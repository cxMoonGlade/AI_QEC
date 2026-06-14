# The small-window composition limit — consolidated theory spine (Paper-2 framework)

> **What this file is.** The single, end-to-end theoretical argument behind the small-window
> twin and its composition limit. P2/P3/P4 (same directory) carry the full derivations; **this
> file is the SPINE** — it states each theorem with its conditions, tags every quantitative
> claim, and chains §1→§10 into one argument a paper referee follows without leaving the page.
> It does **not** reproduce the per-step algebra (the P-docs do); it states the result and cites
> the doc. Companion: `registration.md` (the CF-WR experiment that adjudicates the (b) bets),
> `plan3.md` §3 (the one-paragraph summary this file expands), `docs/METRICS.md` (the D_Choi
> metric). Consolidated by the opus theory agent, 2026-06-14.
>
> **Epistemic legend (binding, `CLAUDE.md` / `METRICS.md`).** Every quantitative claim is tagged:
> **(a) exact** — theorem / identity / zero-tolerance check; the **only** class admissible as a
> premise or derivation basis. **(b) prediction band** — a registered falsifiable bet; a miss is
> a **finding**, never later citable as fact. **(c) heuristic / gate** — thresholds, significance
> conventions, eliminative controls; go/no-go tripwires **only**, never a premise. Undeclared ⇒
> defaults to (c). Conjectural steps are **bold-inline tagged**. A conclusion without
> theorem-grade justification is **PROVISIONAL**: reportable and go/no-go-usable, but nothing is
> built on it.
>
> **Cite-don't-claim (HARD).** Every borrowed theorem (Brown–Poulin, Fawzi–Renner, JRSWW,
> Fuchs–van de Graaf, Kuwahara–Kato–Brandão, Sang–Hsieh, Zhang–Gopalakrishnan, Hu et al.
> 2604.01197, Ivashkov, Lieb–Ruskai, Petz/KMB) is **applied or evaded, never claimed as ours**.
> Our genuine deltas are flagged **[OURS]** at the point of use and tabulated in §10. The honest
> one-line positioning is at the end of §10.

---

## 0. The claim in one sentence (the spine)

**For a shallow-depth, geometrically-local noisy QEC channel field below the decodability
threshold, the small-window composition limit equals the decodability threshold itself — for the
diagonal/classical sector exactly, and for the coherent sector perturbatively — with the required
window width growing at most logarithmically in system size; and the operational reconstruction
target is the decode-/likelihood-*sufficient functional*, not the full state, which raises the
limit strictly and keeps the coherent slot.**

Unpacked into its five load-bearing pieces, with their epistemic class:

1. **(a)** Diagonal noise reduces to a classical Markov network; its conditional mutual
   information (CMI) is **strictly zero past the interaction range**, so windows reconstruct the
   global state **exactly with a constant bulk buffer** `w ≥ R₀` — the limit *is* the
   decodability threshold (§3).
2. **(a)-core / (b)-macroscopic** A weak coherent edge on that classical-Markov bulk keeps
   `I(A:C|B) = κφ² + O(φ³)` with a **local, not `exp(Θ(|A|+|C|))`, prefactor** — the leading
   coefficient κ is exact; the macroscopic escape is a (b) bet with two named gaps (§5).
3. **(a)-structure / (b)-magnitude** Composing the **sufficient functional** `V = V_NLL ∪ V_do`
   rather than the full state gives `ξ*_func ≥ ξ*_full` and **keeps the coherent slot** — the
   genuine new contribution (§6).
4. **(a)** Window width scales as `w ≳ 2ξ·log(L/ε)` (a `+2ξ·log(1/φ)` coherent surcharge),
   i.e. **at most logarithmic** in `L`; in the classical bulk away from criticality it is
   **constant** (§3, §5).
5. **(a)** The wall is the decodability transition (`ξ→∞`): there **all** controlled bounds
   collapse together, and the limit "= the threshold" is the *maximum attainable*, not a rule
   deficiency (§8).

Whether the **hardware** sits in the controlled regime is **empirical** and is settled by a
single cheap diagnostic on existing data (§9), which converts the (b) bets into a verdict.

---

## 1. The object and the question

**The object (a).** The twin's noise model is a **channel field** `E` — a geometrically-local,
shallow-depth completely-positive trace-preserving (CPTP) map acting on a 2D nearest-neighbour
QEC lattice. Its faithful linear representation is the **Choi–Jamiołkowski state**

> `J(E) = (I ⊗ E)|Ω⟩⟨Ω|`,  `|Ω⟩` the unnormalized maximally-entangled vector (Choi 1975;
> Jamiołkowski 1972).  **(a, definition)**

`J(E)` carries the **full** channel, including its coherent (off-diagonal) content. Per-window the
state is exactly representable: a window of ≤15 physical qubits has a density-matrix backend that
holds `J` and all reduced spectra to machine precision (`forward/exact`; the feasibility wall is
~15q, `CLAUDE.md` backend boundary). The macroscopic `J(E)` is **never materialized** — the
global figure is the **seam aggregate** of per-seam reduced blocks (≤6q support, ≤2¹² dimension;
`registration.md` amendment 1, `METRICS.md` D_Choi line).

**The question (a).** *Composition.* Given exact small-window twins and their measured marginals
`{ρ_AB, ρ_BC}` on overlapping windows, can a principled glue rule reconstruct the global `J(E)`
from those marginals, and **where** (in correlation strength) does it break? This is the one open
problem of `plan3.md`; CF-WR is its controlled adjudicator against exact 12q truth.

**Why this is NOT an arbitrary 2D Gibbs state (a — the load-bearing scope restriction).** The
worst-case 2D-reconstruction obstruction (§4) is proved over **all** 2D states, including those
arbitrarily far from any Markov state. Our object is **not** generic: it is the Choi state of a
**shallow-depth, geometrically-local channel field**, so it inherits a **light-cone / finite-depth
causal structure** — correlations it can build are bounded by the circuit depth, and below
threshold the induced correlation length ξ is finite. This is precisely the regime in which the
shallow-circuit clustering guarantee of **Hu et al. (2604.01197)** applies (its **trivial-phase**
result, Thm 11/13, Fact 3 — cited, never claimed; see the scope caveat in §8 and the citation
note in §10). The whole argument is **conditioned on this shallow / below-threshold structure**;
remove it and the worst-case obstruction returns. The scope is stated once here and enforced
throughout: **trivial-phase, per-window, below-threshold.**

---

## 2. The per-seam bound (P2) — the certificate is local and linear

The atomic object is a single seam, tripartitioned **A — B — C** with `B` the overlap/buffer; the
glue is a function only of the measured marginals `{ρ_AB, ρ_BC}`. Two glue rules are studied:
**G0** (mean-field / conditional-product, the suspected-artifact baseline) and **G1** (the Petz
rotated universal recovery map, the certified anchor). The reconstruction residual is the Choi
trace distance `D_Choi^G(λ) = ½‖ρ(λ) − glue_G(ρ_AB, ρ_BC)‖₁`, with `λ` the cross-seam correlation
amplitude (the registered non-unital-CPTP T-B coordinate; the signed asymmetry `δ′ = p10 − p01`
is the two-sided perturbation coordinate). Full derivation: `P2_derivation.md`.

> **Theorem P2-bound (a; Fawzi–Renner 1410.0664 + JRSWW PMC4841654 + Fuchs–van de Graaf).** The
> Petz rotated recovery `R_{B→BC}` depends **only on `ρ_BC`**, and
> `½‖J_s − R(J_s, AB)‖₁ ≤ √(I_nats(A:C|B))`,  where `I_nats = ln2 · I_bits`.
> *(Constant provenance: Fuchs–van de Graaf `F² ≥ e^{−I_nats}` ⇒ `T² ≤ 1 − F² ≤ I_nats` ⇒
> `D_Choi^{G1} ≤ √(I_nats)`. The constant is `√(I_nats)`, **not** `√(2·I_nats)` — the working
> draft's √2 is void; `P2_derivation.md` §0 [B-5].)*

This is the **certificate**: the per-seam Petz residual is **upper-bounded by the square root of
the conditional mutual information**, a fully-quantum bound that holds regardless of the 2D
obstruction. Its leading-order behaviour separates the two glue rules:

> **Theorem P2.1 (a — G0 leading order).** `D_Choi^{G0}(λ) = c_{G0}·λ + O(λ²)`, **slope 1**, with
> `c_{G0} = ½‖χ⁽¹⁾_uncaptured‖₁ > 0`. The mean-field/product glue cannot represent the **first-order
> connected A:C cumulant** `χ⁽¹⁾`, which is **nonzero for the non-unital (un-twirled) knob** (it
> breaks the parity/twirl symmetry that would force `χ⁽¹⁾ = 0`). *(The K1 seam-test measured the
> exponent 0.973 ≈ 1, retro-confirming slope 1 and falsifying the earlier quadratic ansatz — which
> had mistaken the dropped first-order connected term for an `O(λ²)` self-consistency error.)*
> **Exception (a):** the unital/twirled coupling has `χ⁽¹⁾ = 0` ⇒ **slope 2**. The order is set by
> the **parity of the leading connected correlation**.

> **Discriminator P2.2 (b — the registered bet; G1 vs G0).** `D_Choi^{G1}(λ) = c_{G1}·λ + O(λ²)`
> with the **coefficient ratio** `c ≡ c_{G1}/c_{G0}` the registered object. The bet is `c < 1`
> (direction `c ≤ 0.5`); `c ≥ 1` is a **finding** (Petz does not beat mean-field), `c ≈ 0`
> (G1 slope ≈ 2) is a **bonus**. **Why a ratio, not a slope:** a clean G1 `O(λ²)` would require
> `χ⁽¹⁾` to be *exactly* Petz-recoverable at first order, which a non-unital interface **cannot
> prove** (the rotated-Petz integral can over-rotate; `‖χ − Petz(χ)‖₁ < ‖χ‖₁` is **not** a general
> trace-norm identity — `P2_derivation.md` §0 [B-1]). So `c < 1` is **(b), decoupled from the GO
> gate**, and a within-run ratio (same teacher/functional/grid) is more stable than either slope
> alone.

> **Pin P2.3 (a).** At the unital point `p01 = p10`, both `c_{G0}` and `c_{G1}` vanish at first
> order ⇒ residual `O(λ²)`. A violation is a build bug, not physics.

**2D aggregation over `L` seams (a — at-most-linear, sub-additive).** Local fields make each
interface cell's `χ⁽¹⁾_ℓ` seam-supported; for **disjoint** supports the trace norm is additive
(`∝L`), but **adjacent 2×2 windows share a corner qubit**, so supports intersect and the trace
norm is only **sub-additive** (`‖Σ A_ℓ‖₁ ≤ Σ‖A_ℓ‖₁`). Hence the per-seam residual is **monotone
non-decreasing with an `O(L)` upper bound (a)**; strict linearity is the **(b) centre** (exponent
band `[0.85, 1.15]`). The `√L` fluctuation law does **not** apply — `D_Choi` is an `L₁` norm,
contributions add by **magnitude**, not in quadrature (`P2_derivation.md` §0 [B-3], §5). The exact
density-matrix oracle reaches only `L ∈ {1,2,3}`, so the L-exponent is **direction-only**; the
**coefficient ratio `c` (P2.2) is L-independent at first order**, hence the robust 2D-transferable
discriminator.

---

## 3. The classical limit (P-spine) — (a)-exact, limit = decodability threshold

Restrict to **diagonal** (Pauli/incoherent) noise. Then `J(E)` is diagonal in the stabilizer/Bell
basis and is equivalent to a **classical Gibbs distribution / Markov random field (MRF)** over the
syndrome configuration.

> **Theorem CL (a; Brown–Poulin 1206.0755; Hammersley–Clifford).** For a classical Gibbs/MRF state
> with finite interaction range, the conditional mutual information is **strictly zero past the
> interaction range**: `I(A:C|B) = 0` whenever the buffer `B` separates `A` from `C` by more than
> the interaction range `R₀`. Equivalently, the conditional-independence log-ratio
> `log ρ_AB + log ρ_BC − log ρ_B − log ρ_ABC` **vanishes identically on the support**
> (Hammersley–Clifford).

Two exact consequences follow, and they are the backbone of the whole composition argument:

1. **Exact reconstruction with a CONSTANT bulk buffer (a).** Because `I(A:C|B) = 0` *exactly* once
   `B` exceeds `R₀`, the Petz bound P2-bound gives `D_Choi^{G1} ≤ √(I_nats) = 0`: the windowed-glue
   reconstruction is **exact** with a buffer `w ≥ R₀` that is **independent of system size `L`** in
   the bulk. The `2ξ·log(L/ε)` width is needed **only in the thin critical window** near the
   threshold `p_c`, where ξ diverges. In the bulk the cost is **constant**.
2. **The limit equals the decodability threshold (a).** The correlation length ξ that sets the
   buffer is the **same** ξ that governs decodability. Composition is faithful exactly while ξ is
   finite — i.e. **below threshold** — and the buffer required is the decodability buffer. The
   composition limit **is** the decodability threshold; there is no separate, lower wall.

**Aggregation (a, from §2).** Summing over the `O(L)` seams is **at-most-linear and sub-additive**
(corner-sharing supports). The global classical reconstruction error is therefore bounded by an
`O(L)·e^{−w/ξ}` term that the buffer width `w ≳ 2ξ·log(L/ε)` drives below ε — **logarithmic** in
`L`. This is the proven classical sector; it is **cited as the premise** the coherent sector
builds on (§5), never re-derived there.

---

## 4. The coherent obstruction (the naive stop signal)

Turn on **off-diagonal** (coherent) noise. Now `J(E)` has coherences no classical MRF can carry,
and the classical clustering theorem CL no longer applies. The relevant worst-case 2D bound is the
**only** available general quantum-CMI clustering result, and it carries a fatal prefactor:

> **Obstruction KKB (a; Kuwahara–Kato–Brandão 2407.05835, PRX; precursor 1910.09425 / PRL 124,
> 220601).** For a **general** 2D state the conditional-mutual-information clustering bound has a
> prefactor `D_AC = exp(Θ(|A| + |C|))` — **exponential in the fragment volume**. Consequently the
> global Markov property is **destroyed for macroscopic 2D fragments**, and **quantum belief
> propagation degrades / fails on 2D boundaries**.

Stated precisely as the thing to escape: the exp prefactor is a **non-perturbative, worst-case**
constant — the cost of finding the Markov reference **from scratch** for an arbitrary 2D state. If
it bound our object, small-window composition of a coherent channel field would be hopeless at
macroscopic scale. The next two sections show it **does not** bind — first perturbatively at the
level of the full state (§5), then structurally at the level of the operational target (§6).

---

## 5. The coherent escape (P3) — prior art + the [OURS] κ delta

The escape rides on the §3 premise: the coherent noise is a **weak perturbation φ on a
classical-Markov bulk** `ρ_cl` (the proven poly-prefactor object). The seam-crossing coherent knob
is `U_φ = exp(−iφ G)`, `G = Σ_{e∈seam} Z_e ⊗ Z_{e'}` an **inter-cell** generator supported on the
`O(L)` seam edge-pairs (`registration.md` §2). The first-order perturbation is the off-diagonal
coherence `χ⊥ = −i[G, ρ_cl]`, `(χ⊥)_{ab} = −i G_{ab}(p_a − p_b)`, seam-supported. (The
non-commutation is **inter-cell**: a single-cell `Z⊗Z` commutes with the non-unital Choi cell —
its coherence lives in the `{|00⟩,|11⟩}` block where `Z⊗Z = +1` — so the connected coherence is
injected only across two seam cells; `P3_coherent_CMI_prefactor.md` §1.1, R2-2.) Full derivation:
`P3_coherent_CMI_prefactor.md`.

> **Theorem P3.1 (a — leading order, exact by symmetry).** `I(A:C|B)[ρ(φ)] = κ φ² + O(φ³)`. The
> leading order is `O(φ²)` **exactly**, because `I` is **even in φ**: in the real basis
> `ρ(φ)ᵀ = ρ(−φ)` blockwise, and every entropy depends only on eigenvalues, so `I[ρ(−φ)] = I[ρ(φ)]`
> ⇒ every odd coefficient vanishes (cleaner than P2's one-sided coordinate — parity does the work
> stationarity alone could not guarantee at a boundary; `P3` §2.1, F2′).

> **Theorem P3.2 (a — the leading coefficient is LOCAL, no exp prefactor).** The φ² coefficient is
> the **Kubo–Mori–Bogoliubov (KMB) entropy-Hessian** of `ρ_cl` contracted on `χ⊥`:
> `κ = ½ ⟨χ⊥, K_cl χ⊥⟩_KMB ≥ 0`, in closed divided-difference form
> `κ = ½ Σ_{a≠b} |G_{ab}|² σ̃(p_a, p_b)`, `σ̃ ≥ 0`, with kernel
> `k(p_a,p_b) = (log p_a − log p_b)/(p_a − p_b) > 0` (Petz, the BKM metric as relative-entropy
> Hessian). Every factor is **local or `O(L)`**: `G` runs over `O(L)` seam edges; the kernel is a
> fixed function of the **finite-ξ classical bulk weights**; the CMI's connected cancellation
> screens any seam pair buried `> ξ` deep in `B` by `e^{−w/2ξ}` (the **classical** Markov screening
> of `ρ_cl`, the poly-prefactor one). Hence
> `κ ≤ O(L · log(1/p_min^{local})) · e^{−w/2ξ}` — **NOT `exp(Θ(|A|+|C|))`**.
> *Mechanism:* KKB's exp is the cost of finding the Markov reference from scratch; the perturbation
> is **handed** the reference (`ρ_cl`) and pays only its **local KMB curvature** (`P3` §2–§3).

> **★ [OURS] — the narrow, explicit delta.** The **conclusion** of P3.2 (a weak coherent
> perturbation of a classical-Markov state keeps CMI controlled with a local-not-volume prefactor
> below threshold, collapsing at threshold) is **PRIOR ART**: **Sang–Hsieh 2404.07251** (PRL 134,
> 070403) and **Zhang–Gopalakrishnan 2511.01976** establish finite-Markov-length stability below an
> `O(1)` threshold (via cluster expansion, for **incoherent** perturbations). **We cite both and do
> not re-claim the conclusion.** P3's own contribution is exactly the piece they do not supply: the
> **explicit closed-form Kubo–Mori coefficient κ for a COHERENT off-diagonal (unitary) edge**. The
> stability papers prove *finiteness*; we extract the *coefficient* — and the sharp constant at
> macroscopic scale **remains open** (the two gaps below).

**Honest status — (a)-core, (b)-macroscopic, two named gaps.** The escape splits cleanly:

- **(a) — the leading coefficient κ.** Exact via the KMB route (P3.2). This is theorem-grade.
- **(b)-conditional — the macroscopic escape.** That `I(A:C|B)[ρ(φ)]` *stays* local (no exp) at
  **fixed φ** as `|A|+|C| → macroscopic` is a **(b) bet with TWO exact gaps**:
  - **C1** — the **uniform higher-order remainder**: the `n ≥ 3` Fréchet remainder of `−S` must be
    controlled by the *same* local seam kernel, uniformly in `N` and fragment size. The structure
    holds (every order is seam-local — `n` generators all on the seam), and the leading floor
    `φ ≲ exp(−O(ξ))` is derived; the **uniform N-bound** (the standard hard DOI/Kato step) is not
    closed (`P3` §3.3).
  - **C2** — the **wrong-direction information bound**: defeating KKB needs an **UPPER** bound on
    `I(A:C|B)` at fixed φ for macroscopic regions. The Fawzi–Renner recovery route `I ≥ −2 log F`
    is a **LOWER** bound on `I` — the wrong direction — so the Petz route **cannot rescue the
    macroscopic escape to (a)**. It corroborates only the *order and locality of the coefficient*,
    which is anyway (a) by KMB (`P3` §3.4, R2-3).

> **Theorem-conditional P3.3 (the coherent composition limit, (b) granting §5).** The coherent edge
> shifts the required window width by an **additive** term:
> `w ≳ 2ξ · [ log(L/ε) + log(√κ · φ) ]`. Since `√κ · φ ≤ 1` in the regime of interest, the
> surcharge is `≤ 0` for small φ (**no extra width**) and grows only **logarithmically** as φ
> increases — at most a `2ξ·log(1/φ)` penalty. The φ-regime of validity is
> `0 ≤ φ ≲ φ* := c · exp(−O(ξ))`, **set by the correlation length, independent of `|A|+|C|`**:
> for any code size `L` there is a φ-window `[0, φ*(ξ)]`, fixed by ξ alone, in which coherent
> small-window composition is faithful with a poly·L (not exp) prefactor.

**The P2↔P3 reconciliation (a — same physics, two metrics).** P2's per-seam residual is **O(φ)
linear** (a *trace-distance reconstruction residual*, odd-sensitive); P3's CMI is **O(φ²)
quadratic** (a *relative-entropy information*, Markov-stationary/even). They are **not** the same
statement and **not** contradictory: the √-bridge `D_Choi^{G1} ≤ √(I_nats) = √κ · φ + O(φ²)`
reconciles them exactly — both **linear in φ**, both **L-additive with a local prefactor**. The
CMI route thereby **certifies that P2's linear per-seam law carries no exp prefactor** — the
coherent generalization of the classical limit (P2 gives the per-seam law; **P3 is the global
statement** that the KKB obstruction does not bind perturbatively).

**Limit = decodability threshold, extended.** As in §3, the controlling ξ is the decodability ξ;
the coherent escape is **parasitic on the classical Markov screening** of `ρ_cl`. So the coherent
composition limit is again **= the decodability threshold**, now for coherent-perturbative noise,
with the additive φ-logarithmic window surcharge. At `ξ → ∞` (threshold) `φ* → 0` and the screening
is lost — the controlled window collapses (§8).

---

## 6. The sufficient-functional reframe (P4) — the genuine new contribution

The obstruction of §4 is a statement about the **FULL** state. The twin is judged by two
**functionals** of `J(E)`, neither of which is the full state:

- **Decode-sufficient directions `V_do := (ker dΦ_dec)^⊥`** — the Choi directions the **frozen**
  decoder's pushforward `J ↦ ΔLER(Φ_dec, J)` is first-order sensitive to. For MWPM/pymatching the
  decoder reads `J` **only through the DEM edge-logit vector** — `dim V_do = poly(d)`, **not**
  `4^{#qubits}`. This is the project's existing `decision_pushforward` support (`METRICS.md`).
- **Likelihood-sufficient directions `V_NLL`** — the syndrome-marginal directions that determine
  held-out per-shot syndrome NLL. Crucially `V_NLL` is **NOT** the diagonal/independent-edges
  subspace: held-out NLL **provably sees the bunching/coherent sector** (M3 measured it — the
  window twin beat SI1000 by +56.21 X / +44.28 Z nats/shot/window, exploiting a bunching DOF the
  independent-edges DEM **cannot represent**). So `V_NLL` **contains coherent/bunching directions
  by measured fact** (`P4` §1.2).

Set `V := V_NLL ∪ V_do` and target `P_V(J − J_glue)` — the projection of the glue residual onto
the sufficient subspace — **not** all of `J − J_glue`. Full derivation: `P4_sufficient_functional.md`.

> **Theorem P4-contract (a — structure).** `P_V` is an orthogonal projector on the Hilbert–Schmidt
> space of Choi operators, hence a **contraction in every unitarily invariant norm** (in particular
> the trace norm of D_Choi): `‖P_V(J − J_glue)‖ ≤ ‖J − J_glue‖` for **all** `J, J_glue`. Therefore,
> writing `ξ*_full`, `ξ*_func` for the correlation strengths at which full-state vs sufficient-
> functional composition breaks at fixed glue rule and geometry,
> **`ξ*_func ≥ ξ*_full`**, with **strict inequality iff `P_{V^⊥}(J − J_glue) ≠ 0`** — **generically
> true**, since the full Choi has coherent off-diagonal directions **no syndrome marginal reads and
> no frozen decoder is sensitive to** (`P4` §2).

This is **(a)-structure** (a one-line projection-contraction fact). Its **(b)-magnitude** —
*how much* higher the limit is — is exactly the `E_do`/`D_Choi` gap: `D_Choi` scores the full
residual `‖J − J_glue‖` (including the decoder-invisible `V^⊥` directions), `E_do = knob_dler_error`
scores the decode-relevant `V_do`-projection. M4 is the **prior measured instance** of a nonzero
`P_{V^⊥}` (NLL/Choi win, MWPM does not cash it). Not a free lunch: `ξ*_func` is a **weaker
guarantee** — faithful only on `V`, `V^⊥` declared out of operational scope. The reframe is sound
**iff** the operational question is genuinely about `V` (held-out NLL + do()→ΔLER), the functional
named in advance (theory-first); `ξ*_func` is **not** a full-state certificate (`P4` §2.3).

**The wedge-preserving variant vs the ΔLER trap (the decisive choice).** The value lives in the
choice of `V`:

- **`V_NLL` (likelihood-sufficient) — keeps the coherent slot (a-structure / b-magnitude).** Held-out
  NLL **sees** bunching (M3), so `V_NLL` **contains** the off-diagonal/bunching DOF that
  distinguishes the density-matrix carrier from a Pauli DEM. Strictly higher limit **and**
  coherent-aware (`P4` §3.1).
- **`V_do` only (ΔLER-sufficient) — the live trap ((b)/PROVISIONAL).** Still a strictly higher
  limit, but **forfeits the coherent slot to windowed decoding IF the frozen MWPM is
  coherent-blind** (`dΦ_dec` annihilates the coherent directions). Then `P_{V_do}(J − J_glue)` is a
  purely classical DEM-edge object and composing it is **exactly** the prior art (Skoric/Tan/Cain
  compose *decisions*). **M4 measured this regime real:** %ΔLER twin-vs-naive −40.26% X / −40.73% Z
  (both reversed vs the +10% bet — a finding), headline twin-vs-pij in band at ≈0, routing
  GATE_FAIL_CALIBRATION_DIRECTION + COVARIATION_NULL_STRUCTURAL — **the M3 NLL win and the bunching
  certificate did NOT transfer to MWPM through the independent-edges DEM**. So "frozen MWPM is
  coherent-blind" is **(b)/PROVISIONAL** — supported by M4, but format- and decoder-specific, no
  mechanism attribution, and **not** identically true (M4's A3c two-pass was a small decode-side
  **positive**, +1.1% / +0.7% on high-R̂ windows, sig@99%). It must **not** be cited as fact (`P4`
  §3.2).

> **Theorem P4-safe (a — definition; the registered AND-gate is its instrument).** The safe
> sufficient object is **`V = V_NLL ∪ V_do`** — likelihood- **and** decode-sufficient: strictly
> smaller than the full Choi (⇒ strictly higher limit), retains the coherent slot via `V_NLL`
> (M3), supports the do()-counterfactual via `V_do`. This is the theoretical content of CF-WR's
> **co-primary D_Choi AND E_do gate**: passing only `E_do` risks the coherent-blind trap; passing
> only `D_Choi` over the DEM-representable subspace risks missing the coherent sector. The AND
> forces both (`P4` §3.3, `registration.md` §4/§6).

> **★ [OURS].** No prior art owns *"composition limit of a SUFFICIENT FUNCTIONAL for a COHERENT
> channel field."* The strict-inequality structure and the wedge logic are P4's genuine new
> contribution. The full-state guarantee (2604.01197) is **strictly stronger** (P4 deliberately
> weakens it); windowed decoding has sufficiency but no channel field and no coherent slot;
> TN/dMLE has a channel object but no coherent slot (T-B). P4 occupies the empty intersection.

---

## 7. The four-leg architecture

The full theory is a **four-object decomposition**; P4 changes the *target* and **none** of the
other three. Each leg owns one role (`P4` §0, §5; `plan3.md` §3):

- **Certificate — the full-state per-seam residual / CMI bound `D_Choi ≤ √(I_nats) = √κ·φ`.** The
  rigorous **upper bound** that the per-seam glue is controlled. Owned by **P2** (linear per-seam
  law, the √-bridge, L-additivity) and **P3** (κφ² local, no exp prefactor). It is *the* rigorous
  control; the operational target inherits it because, by P4-contract, the full residual **dominates**
  the projected residual. Unchanged by P4.
- **Target — the reduced functional `P_V(J − J_glue)`, `V = V_NLL ∪ V_do`.** What the twin
  **actually needs** to reconstruct. Owned by **P4** (this is the new content): target the
  sufficient functional, get `ξ*_func ≥ ξ*_full`, keep the coherent slot.
- **Representation — the per-seam reduced Choi blocks (≤6q support, ≤2¹² dimension).** The
  **feasible carrier** of the computation (`registration.md` amendment 1, `METRICS.md`). `V` is a
  subspace **of** each reduced block, so the reframe lives *within* the registered representation,
  not a new one. Unchanged by P4.
- **Recovery object — the local GKSL generators `(h, a)`.** What the learner **emits**. This is
  **already escaping** the obstruction by locality (steady-state local-channel reconstruction;
  **Ivashkov 2603.05492**, ansatz-free Lindbladian learning in situ — cited, never claimed). P4 is
  **orthogonal**: it reduces the *composition target*, not the recovery representation; the two
  compose (recover local generators → compose their `V`-sufficient functional). Unchanged by P4.

The legs fit as: **recover** local generators (already-escaping) → carry them in the **reduced-block
representation** → **compose** their **sufficient-functional target** (P4) → **certify** the
composition with the full-state CMI bound (P2/P3). One sentence per leg; one continuous object.

---

## 8. Scope and the wall

**Scope (STRICT, stated once, enforced throughout).** Every result here is **trivial-phase,
per-window, below-threshold**. The shallow-circuit clustering guarantee (Hu et al., 2604.01197)
covers the **trivial phase only** — the escape applies to the **per-window shallow
noise-channel-field state**, NOT the macroscopic below-threshold code state (citation note, §10).
P3's coherent escape is a **small-φ, strictly-below-threshold** theorem at the coefficient level,
(b)-conditional at macroscopic scale. P4's `ξ*_func ≥ ξ*_full` is a **target reduction inside P3's
controlled regime, never an extension of it**: at large φ or at threshold P4 **inherits** P3's
INHERITS verdict — a weaker target never rescues a regime where the `V` mass itself is uncontrolled
(`P4` §5).

**The wall is the decodability transition (a).** As `ξ → ∞` (approaching threshold):

- the classical buffer `2ξ·log(L/ε) → ∞` (CL, §3);
- the coherent radius `φ* ~ exp(−O(ξ)) → 0` and the screening `e^{−w/2ξ} → 1` (P3.2/P3.3, §5);
- the KKB worst-case exp prefactor (§4) becomes the relevant constant again — there is no longer a
  good Markov reference to be handed.

So **all controlled bounds collapse together at the transition** — the predicted **R̂ ∈ {5–8}
crash** (the registered (b) CF-WR will resolve). The limit being "= the threshold" is therefore the
**maximum attainable**: above it the state is **physically unreconstructable from small windows**
(no finite correlation length to screen the seam), **not** a deficiency of the glue rule. The
ceiling is physical, and the honest statement is *a below-threshold theorem, not an all-regime one.*

---

## 9. The empirical bridge (ξ̂) — converting the (b) to a verdict

The theory's hypothesis is "**finite/small ξ, below threshold**." Whether the **hardware** satisfies
it is **empirical**, and is settled **cheaply, before any build**, on data already in hand:

> **The ξ̂ gate (do FIRST; decoder-independent).** Measure the hardware **spacetime Markov length
> `ξ̂`** from the M3 d=29 repeated-syndrome record via the spacetime-Markov-length diagnostic
> (**Negari–Ellison–Hsieh 2412.00193**). A finite / `O(1)` `ξ̂` with a clean `e^{−w/ξ̂}` collapse ⇒ the
> hardware sits in the **controlled regime** ⇒ the whole direction is validated on real data; **no
> collapse** ⇒ near threshold ⇒ **stop**.

This is the step that converts the §5/§6 **(b)** bets into a **verdict on existing data**: the
theory says "controlled iff ξ finite"; `ξ̂` measures whether ξ is finite for *this* hardware. It is
the cheapest decisive gate in the program (`plan3.md` §7, item 0).

---

## 10. Honest novelty map + cite-don't-claim ledger

**Borrowed theorems — what each owns, all cited-not-claimed:**

| Source | What it owns | Used here as |
|---|---|---|
| **Brown–Poulin 1206.0755** (+ Hammersley–Clifford) | classical Gibbs/MRF CMI **strictly zero past interaction range** | §3 Theorem CL — the (a)-exact classical limit; the premise the coherent escape rides on |
| **Fawzi–Renner 1410.0664** | quantum-CMI ↔ recovery: `½‖ρ − R(ρ)‖₁ ≤ √(I_nats)`, `R` depends only on `ρ_BC` | §2 P2-bound — the per-seam certificate that survives the 2D obstruction |
| **JRSWW / Sutter–Fawzi–Renner PMC4841654** | the **explicit rotated** universal recovery map | §2 — the constructive Petz form for G1 |
| **Fuchs–van de Graaf** | fidelity↔trace-distance: `F² ≥ e^{−I_nats}` | §2 — the `√(I_nats)` (not `√2·I_nats`) constant |
| **Kuwahara–Kato–Brandão 2407.05835** (PRX; precursor 1910.09425) | the 2D quantum-CMI **`exp(Θ(|A|+|C|))`** obstruction; quantum BP fails in 2D | §4 Obstruction KKB — the worst-case constant **evaded**, never claimed |
| **Sang–Hsieh 2404.07251** (PRL 134.070403) | finite conditional-Markov-length **stability** below threshold (incoherent) | §5 — **prior art for the CONCLUSION** of the coherent escape |
| **Zhang–Gopalakrishnan 2511.01976** | weak-decoherence Markov-length stability of classical/commuting-Pauli states below an `O(1)` threshold | §5 — **prior art for the CONCLUSION**; not re-claimed |
| **Hu et al. 2604.01197** | shallow-circuit **trivial-phase** clustering (**Thm 11/13, Fact 3**); a full-state trace-distance reconstruction guarantee | §1/§8 scope; §6 the strong full-state target P4 **weakens**. **TRIVIAL PHASE ONLY** — macroscopic below-threshold code state OUT of scope |
| **Ivashkov 2603.05492** | ansatz-free local **GKSL `(h,a)` generator** recovery in situ | §7 — the RECOVERY leg, already-escaping by locality |
| **Lieb–Ruskai (SSA)** | `I(A:C|B) ≥ 0` | §5 — the non-negativity/stationarity premise (F2) |
| **Petz (BKM/KMB metric)** | KMB inner product = relative-entropy Hessian, kernel `(log a−log b)/(a−b)` | §5 P3.2 — the local integral kernel that replaces the exp prefactor |
| **Skoric / Tan / Cain** (windowed/modular decoding) | composing **decode decisions** across windows | §6 — the quadrant the `V_do`-only trap collapses into |
| **2602.19722** (Pauli-TN / dMLE) + T-B theorem (ADR 0008) | Pauli windowing by bond dimension; iid Pauli/DEM fields pinned at `R=1` | §6 — the "Pauli state, no coherent slot" quadrant |
| **Negari–Ellison–Hsieh 2412.00193** (Spacetime Markov length; mixed-state-phase fault-tolerance diagnostic) | decoder-independent **spacetime Markov-length** diagnostic (classical CMI of repeated syndromes) | §9 — the ξ̂ empirical bridge |

**Our genuine deltas — flagged [OURS]:**

| Delta | Where | Class |
|---|---|---|
| The **explicit Kubo–Mori coefficient κ** for a **coherent off-diagonal unitary edge** (closed divided-difference form `½Σ\|G_{ab}\|²σ̃`) | §5 P3.2 | (a) leading coefficient; the macroscopic escape is (b)/C1+C2 |
| The **sufficient-functional reframe**: `ξ*_func ≥ ξ*_full` for a coherent channel field, with `V_NLL` keeping the coherent slot — the empty intersection no prior art occupies | §6 P4 | (a)-structure; (b)-magnitude (the E_do/D_Choi gate) |
| The **application to a QEC noise twin** — real-hardware characterization (M3 NLL win, M4 transfer-null, the bunching certificate) + the validated **do()-counterfactual** | §6–§7, §9 | measured: M3 (a)-grade; M4 (b)/PROVISIONAL |

**Citation hygiene (binding).** When 2604.01197's clustering is invoked it is **Thm 11/13 (NOT
12/14)**, **Fact 3 (NOT "Fact 5")**, and **TRIVIAL PHASE ONLY**; do **not** stretch it to the
macroscopic code state. The CMI-quadratic-in-φ corollary (§5 P3.1) is a **derived corollary** of
Fawzi–Renner/JRSWW (non-negativity + analyticity + Markov-stationarity / φ-parity), **not** their
stated words — cite as such. The constant in the Petz bound is **`√(I_nats)`**, never `√(2·I_nats)`.

**The honest positioning (one line).** This is a **characterization + narrow-theory** contribution
— the classical limit is borrowed-and-applied (a), the coherent conclusion is **prior art** with an
**explicit-coefficient delta [OURS]** (a-core, b-macroscopic), and the **sufficient-functional
reframe [OURS]** is the genuine new structural result; the whole is **theoretically de-risked and
measured against exact truth and real hardware, NOT a general breakthrough.**
