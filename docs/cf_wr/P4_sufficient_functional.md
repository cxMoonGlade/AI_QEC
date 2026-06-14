# CF-WR P4 (a)-basis — the sufficient-functional composition reframe: composing the decode-/likelihood-sufficient functional, not the full coherent state

> **Theory-only reframe (no code).** Owner object: *the 2D obstruction is stated about the FULL global
> noise state; the operational targets (held-out NLL, do()→ΔLER) are local low-rank FUNCTIONALS of it.
> Does composing the sufficient functional, rather than the full state, give a strictly higher
> composition limit while preserving the coherent slot?*
>
> Derived by opus theory agent, 2026-06-14. Sits **on top of** `P2_derivation.md` (per-seam residual
> φ-expansion, the √-bridge, L-additivity) and `P3_coherent_CMI_prefactor.md` (the perturbative κφ²
> CMI prefactor is local, not exp). P4 changes neither the per-seam law (P2) nor the φ-regime (P3) —
> it changes the **reconstruction TARGET**: from the full Choi J(E) to its decode-/likelihood-sufficient
> projection. Pillars cited, never claimed: KKB [2407.05835] (the exp(Θ(|A|+|C|)) full-state obstruction),
> the full-state trace-distance reconstruction guarantee [2604.01197], windowed/modular decoding
> (Skoric, Tan, Cain), the Pauli TN / dMLE carrier ([2602.19722]), and the project's own
> `decision_pushforward` projection (`METRICS.md`).
>
> **epistemic legend:** (a) exact (theorem/identity/zero-tolerance — the only class admissible as a
> premise/derivation basis); (b) derived prediction band (a miss is a finding, never later citable as
> fact); (c) heuristic/gate (thresholds, eliminative controls — go/no-go only, never a premise).
> Conjectural steps **bold-inline tagged**. Honest verdict throughout: the **strict inequality is
> (a)-structure**; the **gap magnitude is (b)-empirical** (this is exactly what CF-WR's E_do/D_Choi
> co-primary gate measures); **"frozen MWPM is coherent-blind" is (b)/PROVISIONAL** (M4-measured).

---

## 0. Headline claim (read first)

**Composing the decode-/likelihood-SUFFICIENT FUNCTIONAL of the global noise object — not the full
coherent state — gives a STRICTLY HIGHER composition limit, and the likelihood-sufficient variant
PRESERVES the coherent slot.** Precisely:

> **ξ\*_func ≥ ξ\*_full, with strict inequality whenever the per-seam glue error has any component off
> the sufficient subspace `V` (generically true).   (a, structure)**

where `ξ\*_full` is the full-state composition limit (the correlation strength at which composing the
full Choi J(E) from windows breaks, the P2/P3 object) and `ξ\*_func` is the limit for composing only
`P_V(J − J_glue)` — the projection of the glue residual onto the **decoder-sensitive** (`V_do`) and
**syndrome-marginal** (`V_NLL`) directions. The inequality is a **one-line contraction fact** (a
projection is norm-non-increasing); the **magnitude** of the gap is empirical (b) and is *exactly the
quantity CF-WR's E_do/D_Choi co-primary gate measures* (§6). The decisive content is the **choice of
`V`** (§3):

- **`V_NLL` (likelihood-sufficient):** higher limit AND **keeps the coherent slot** — because held-out
  syndrome NLL provably **sees** the bunching/coherent sector (M3: the window twin's +56.21 X /
  +44.28 Z nats/shot/window win over SI1000 **was** the bunching DOF the independent-edges DEM lacks).
- **`V_do` only (ΔLER-sufficient):** higher limit but **forfeits the coherent slot to windowed
  decoding** *if the frozen MWPM is coherent-blind* — which M4 measured (covariation NULL, PROVISIONAL).
  This is the **live trap**: a decode-only sufficient functional collapses into exactly the prior art
  (Skoric/Tan/Cain) that already owns "compose decode decisions."
- **The safe object is `V = V_NLL ∪ V_do`** (likelihood- *and* decode-sufficient): strictly smaller
  than the full Choi ⇒ strictly higher limit; retains the coherent slot via `V_NLL`; supports the
  do()-counterfactual via `V_do`.

**Why this is genuinely novel (§5):** the only published *full-state* trace-distance reconstruction
guarantee [2604.01197] is **strictly stronger** than what decoding/NLL needs; reframe-2 is a
**strictly weaker, sufficient-functional target**, faithful precisely in the regime where full-state
reconstruction is already obstructed (KKB exp prefactor). No prior art owns *"composition limit of a
sufficient functional for a coherent channel field"*: windowed decoding composes *decisions* (no
channel field); TN/dMLE composes the *Pauli* state (no coherent slot — T-B). It sits in the open wedge
of `plan3.md` §1.

**What it does NOT change (§ honest scope):** P3's φ-regime (small φ, strictly below threshold) is
untouched — reframe-2 changes the TARGET, not the φ-regime. The full-state perturbative bound (P3) is
the **CERTIFICATE**; the reduced functional `P_V(J−J_glue)` is the **OPERATIONAL TARGET**; reframe-4's
per-seam reduced Choi blocks (`registration.md` amendment 1) are the **REPRESENTATION**; reframe-1's
local generators (Lindbladian `(h,a)` coords) are the **RECOVERY object** — already escaping the
obstruction by the local-channel literature (Ivashkov 2603.05492; steady-state local-channel
reconstruction; 2604.01197 local-channel-circuit). P4 is the **fourth leg**: the *target reduction*
that makes the other three operationally sufficient.

**Verdict: ESCAPES the full-state obstruction at the level of the sufficient functional — (a) for the
strict inequality and the `V_NLL`-keeps-the-coherent-slot structure; (b) for the gap magnitude and for
the "MWPM coherent-blind" premise of the `V_do` trap (M4-PROVISIONAL).**

---

## 1. The obstruction is about the FULL state — and the operational targets are not

### 1.1 The obstruction, restated (a, cite — not re-derived)
The 2D composition obstruction the project inherits is a statement about the **full global density
operator**:

> KKB [2407.05835]: the conditional-mutual-information clustering bound for a general 2D state carries
> a prefactor `D_AC = exp(Θ(|A|+|C|))`; quantum belief propagation **fails in 2D**; the global Markov
> property is destroyed for macroscopic 2D fragments. (a, the cited obstruction — applied/evaded, never
> claimed; see P3 §3.1.)

> [2604.01197]: the available *positive* reconstruction guarantee is a **full-state trace-distance**
> statement — reconstruct the global state/channel to `½‖·‖₁ ≤ τ`. (a, cited; this is the strong target
> P4 deliberately weakens.) **Scope (binding, governs every [2604.01197] mention below):** that
> guarantee is **trivial-phase / per-window-scoped** — it covers the per-window shallow noise-channel-field
> state, **NOT** the macroscopic below-threshold code state (which is out of its trivial-phase class; see
> `THEORY.md` §8 + P3 §0.1). So the "full-state target P4 weakens" is the *per-window* full state; P4 does
> **not** imply, and must not be read as implying, a macroscopic full-state guarantee.

Both objects of these statements are the **entire** state/channel: KKB marginalizes/reconstructs the
**global density operator**; the [2604.01197] guarantee certifies the **whole** channel in trace
distance. The obstruction is therefore a statement about a **specific, maximal** target. The question
P4 asks is whether the *operational* targets are that maximal.

### 1.2 The operational functionals are local and low-rank (a, structure)
The twin is judged by two functionals of the noise object, neither of which is the full state.

**Decode-sufficient directions `V_do`.** The capability-side score is `do()→ΔLER` under a **frozen**
decoder Φ_dec (the `do()` discipline, `CLAUDE.md`; `registration.md` §6). For MWPM/pymatching, the
decoder consumes `J(E)` **only through the DEM edge-probability vector** `p = {p_e}` (one logit per
matching edge), a **poly(d)-dimensional** read-out — and ΔLER is the change in **logical-class
probability** (a scalar per do() target). Define

> **`V_do := (ker dΦ_dec)^⊥`   (a, definition)** — the Choi directions the frozen decoder's pushforward
> `J ↦ ΔLER(Φ_dec, J)` is first-order **sensitive** to.

`dim V_do` is bounded by the number of decision-relevant DEM coordinates × do() targets — **poly(d),
NOT 4^{#qubits}**. This is not a new object: it is precisely the project's existing
`decision_pushforward` (projection onto the `do()→ΔLER` gradient) and `finite_displacement_regret`
machinery (`METRICS.md` "parameter-grade vs decision-grade"; the `a12i` worked example with **zero**
projection onto the knob gradient is a concrete `V_do^⊥` direction). (a)

**Likelihood-sufficient directions `V_NLL`.** The recover-side score is held-out per-shot **syndrome
NLL**. The syndrome distribution is a function of `J(E)` only through the **syndrome-marginal**
statistics that determine the held-out log-likelihood (the detector-frame marginals + their realized
correlations). Define

> **`V_NLL` := the syndrome-marginal directions that determine held-out NLL   (a, definition)** — the
> directions of `J` to which `−Σ log Pr(syndrome | J)` on the held-out split is first-order sensitive.

Crucially, **`V_NLL` is NOT the diagonal/independent-edges subspace.** The held-out NLL **sees the
bunching/coherent sector**: M3 is the *measured* proof — the window twin beat the shipped SI1000 prior
on held-out syndrome NLL by **+56.21 (X) / +44.28 (Z) nats/shot/window** (paired-bootstrap one-sided
99%; `metric_results.md` P3 gate PASS both), and the **structural** finding was that the
independent-edges DEM **cannot represent** the bunching DOF the NLL win exploited (the measured marginals
are jointly unrealizable by any independent-edges DEM, deficit ≥ 4.1e-3–6.5e-3; per-window bunching
R̂ ∈ [1.0, 17.7]). So `V_NLL` **contains coherent/bunching off-diagonal directions** by measured fact,
not assumption. (a definition / (b) for the magnitude of the NLL sensitivity — M3-measured.)

### 1.3 The reframe target (a, definition)
Set `V := V_do ∪ V_NLL` (the span of both). The **sufficient-functional reconstruction** is: reconstruct

> **`P_V(J − J_glue)` to tolerance τ — NOT all of `J − J_glue`,   (a, definition)**

where `P_V` is the orthogonal projector onto `V` (in the Hilbert–Schmidt / Choi inner product) and
`J_glue` is the composed (windowed-glue) estimate. The full-state target is `‖J − J_glue‖ ≤ τ`; the
sufficient-functional target is `‖P_V(J − J_glue)‖ ≤ τ`. The respective composition limits:

> **ξ\*_full := sup{ ξ : ‖J − J_glue‖ ≤ τ }   (a, def)**
> **ξ\*_func := sup{ ξ : ‖P_V(J − J_glue)‖ ≤ τ }   (a, def)**

(Read `ξ` as the correlation strength — the registered axis is the bunching R̂ and the coherent angle
φ; `ξ` is the per-seam correlation length these induce, the P1/P3 collapse coordinate. "Limit" = the
largest correlation at which composition stays within tolerance.) Both are taken at a **fixed** glue
rule (G1 Petz, the certified anchor) and a fixed seam geometry, so the comparison is **within-run**, the
normalization cancels (the P2.2 stability argument transplanted to the target axis). (a)

---

## 2. The contraction theorem — ξ\*_func ≥ ξ\*_full

### 2.1 The (a)-structure (exact, one line)
`P_V` is an orthogonal projector on the Hilbert–Schmidt space of Choi operators, hence a **contraction**
in every unitarily invariant norm, in particular the trace norm used by D_Choi:

> **‖P_V(J − J_glue)‖ ≤ ‖J − J_glue‖   for all J, J_glue.   (a, exact — projector is norm-non-increasing)**

(For the trace norm `‖·‖₁`: `‖P_V X‖₁ ≤ ‖X‖₁` because an orthogonal projector is a unital completely
positive trace-non-increasing map's Choi-level contraction; equivalently `P_V` has all singular values
in {0,1} and Ky Fan / pinching gives `‖P_V X‖₁ ≤ ‖X‖₁`. The Hilbert–Schmidt case is immediate,
`‖P_V X‖₂² = ⟨X, P_V X⟩ ≤ ‖X‖₂²`; D_Choi is the half-trace-norm, for which the pinching inequality
holds.) Therefore, for **every** correlation strength ξ, if the full residual is within τ the projected
residual is within τ — so the feasible set for `ξ\*_func` **contains** that for `ξ\*_full`:

> **ξ\*_func ≥ ξ\*_full.   (a, structure — the sufficient-functional limit is never lower.)**

### 2.2 Strictness (a-structure / (b)-magnitude)
The inequality `‖P_V(J−J_glue)‖ ≤ ‖J−J_glue‖` is **strict** exactly when `(J − J_glue)` has a nonzero
component in `V^⊥` (the kernel of `P_V`):

> **‖P_V(J−J_glue)‖ < ‖J−J_glue‖   ⟺   P_{V^⊥}(J − J_glue) ≠ 0.   (a)**

This is **generically true**: the full Choi has **coherent off-diagonal directions that no syndrome
marginal reads and no frozen decoder is sensitive to**. Concretely, the glue error of a coherent seam
(P2's un-twirled χ⊥, the O(φ) off-diagonal residual `−i[G, ρ_cl]` of P3 §1.2) has support on
off-diagonal Choi entries; a generic such entry lies **partly outside** `V_do` (the decoder is a fixed
function of the DEM edge logits) and **partly outside** `V_NLL` (only the NLL-determining marginals are
in `V_NLL`). Any residual mass on such a direction makes the inequality strict. Hence

> **ξ\*_func > ξ\*_full, strictly, generically (whenever the per-seam glue error has any `V^⊥`
> component).   (a, structure — the strict direction; the GENERIC qualifier is the load-bearing one.)**

**The magnitude `ξ\*_func − ξ\*_full` is (b), not (a).** Nothing in the contraction fact says **how
much** higher the limit is — that depends on **how much** of the glue residual lives in `V^⊥`, which is
a property of (i) the seam geometry, (ii) the correlation type (bunching R̂ vs coherent φ), and (iii)
the decoder's actual sensitivity map `dΦ_dec`. **This magnitude is precisely the gap CF-WR's E_do /
D_Choi co-primary gate measures**: D_Choi scores `‖J − J_glue‖` (the full residual, including the
decoder-invisible directions), E_do scores the decode-relevant projection `|ΔLER_glue − ΔLER_true|`
(a functional living in `V_do`). The registered statement that *"E_do is a function of D_Choi except
where the decoder is insensitive to the glue-contaminated Choi directions"* (`registration.md` §4) is
**exactly** the statement `P_{V^⊥} ≠ 0` — and M4 is its measured instance (Choi/NLL win, MWPM does not
cash it). So:

> **The contraction gives ξ\*_func ≥ ξ\*_full as a theorem (a); CF-WR's D_Choi (full) vs E_do
> (V_do-projection) co-primary split is the INSTRUMENT that measures the strict gap (b).** (a + (b))

### 2.3 Why this is not a free lunch (a, honest)
The higher limit is **not** something for nothing: it is a **weaker guarantee**. `ξ\*_func` certifies
**only** that the composed object is faithful **on `V`** — it says nothing about the `V^⊥` directions,
which are simply declared **out of operational scope**. The reframe is sound **iff** the operational
question is genuinely a question about `V` (held-out NLL + do()→ΔLER) and **not** about the full Choi.
The danger is **scope creep**: claiming full-state fidelity from a `V`-only certificate. P4 forbids
this — `ξ\*_func` is the limit of the **stated functional**, with the functional named in advance
(theory-first). This is the same discipline as P3's honest boundary (a small-φ theorem is not an
all-φ theorem); here a `V`-functional theorem is not a full-state theorem.

---

## 3. The wedge-preserving variant and the ΔLER trap (decisive)

The choice of `V` is where the reframe earns or loses the coherent slot. Three variants, with sharply
different verdicts.

### 3.1 `V_NLL` — likelihood-sufficient: higher limit AND keeps the coherent slot (a-structure, b-magnitude)
Because held-out syndrome NLL **provably sees the bunching/coherent sector** (§1.2, M3-measured), the
likelihood-sufficient subspace `V_NLL` **contains** the off-diagonal/bunching directions that the
independent-edges DEM cannot represent. Reconstructing `P_{V_NLL}(J − J_glue)` therefore:

- has a **strictly higher** limit than full-state (§2, the marginals are a strict projection of J);
- **retains the coherent slot** — the very DOF (`χ⊥`, bunching R̂>1) that distinguishes the
  density-matrix carrier from a Pauli DEM is **inside** `V_NLL`, by the M3 measurement.

> **`V_NLL` is the wedge-preserving target: strictly weaker than full-state, but still coherent-aware.
> (a, structure — `V_NLL ⊇ {coherent/bunching directions}` by the M3 measurement; (b) for how much of
> the coherent sector NLL resolves at a given window width.)**

This is the variant that keeps P4 inside the project's open wedge (the coherent slot, `plan3.md` §1).

### 3.2 `V_do` only — ΔLER-sufficient: higher limit but FORFEITS the wedge (the live trap)
If `V = V_do` alone (decode-sufficiency only), the limit is **still** strictly higher than full-state
(§2) — but the coherent slot is **forfeited to windowed decoding** **IF the frozen MWPM is
coherent-blind**, i.e. if `dΦ_dec` annihilates the coherent/off-diagonal directions so that
`V_do ∩ {coherent sector} = ∅`. In that case `P_{V_do}(J − J_glue)` is a **purely classical**
(DEM-edge) object, and composing it is **exactly** composing decode decisions — the prior art of
Skoric / Tan / Cain (`plan3.md` §1: "windowed decoding composes *decisions*, not a channel field").
The reframe would then **collapse into the scooped quadrant** and own nothing new.

**Is the frozen MWPM coherent-blind? — (b)/PROVISIONAL, M4-measured.** M4 is the evidence and the
warning:

> M4 (`metric_results.md`): %ΔLER(twin vs naive) = **−40.26% X / −40.73% Z** (CI99, both reversed vs
> the registered +10% bet — a (b) miss = finding); the headline twin-vs-pij was **in band at ≈0**
> (−0.33% / −0.60%); routing **GATE_FAIL_CALIBRATION_DIRECTION + COVARIATION_NULL_STRUCTURAL**, both
> bases. **The M3 syndrome-NLL win and the located bunching certificate did NOT transfer to MWPM
> decoding through the independent-edges DEM.** (PROVISIONAL, no mechanism attribution.)

The **covariation NULL** is the measured statement that, through the independent-edges DEM and the
frozen MWPM, the decode-relevant projection of the bunching knowledge is ≈0 — i.e. the M4-measured
`V_do` **does not contain** the coherent sector that M3's `V_NLL` did. **So the trap is live, not
hypothetical:** the project has *already measured* a regime where `V_do` is coherent-blind. The premise
"frozen MWPM is coherent-blind" is therefore **(b)/PROVISIONAL** — supported by M4, but (i) format- and
decoder-specific (independent-edges DEM + pymatching), (ii) not theorem-grade (M4 carries no mechanism
attribution, and M4's A3c two-pass on high-R̂ windows was a small decode-side **positive**, +1.1% / +0.7%
sig@99%, i.e. `V_do` is **not identically** coherent-blind). It must **not** be cited as fact.

### 3.3 The safe object — `V = V_NLL ∪ V_do` (a, definition; the registered AND-gate is its instrument)
The resolution is to take **both**:

> **Safe sufficient object: `V = V_NLL ∪ V_do` — likelihood- AND decode-sufficient.   (a, definition)**
> - strictly smaller than the full Choi ⇒ **strictly higher** limit than `ξ\*_full` (§2);
> - **retains the coherent slot** via `V_NLL` (§3.1, M3);
> - **supports the do()-counterfactual** via `V_do` (the capability the carrier must deliver).

This is **exactly** why CF-WR's gate is **co-primary D_Choi AND E_do with an AND-gate** (`registration.md`
§4/§6, owner decision ii): D_Choi guards the reconstruction broadly (a full-residual surrogate, upper-bounded
by `√(I_nats)`), while E_do guards the decode-sufficient projection — and the AND forces **both** legs.
The `V = V_NLL ∪ V_do` object is the theoretical content of that AND-gate: passing **only** E_do (a `V_do`
certificate) risks the §3.2 trap (coherent-blind decode); passing **only** D_Choi over the
DEM-representable subspace risks missing the coherent sector. **The registered co-primary gate is the
operational realization of "reconstruct `V_NLL ∪ V_do`, not the full Choi, and not `V_do` alone."** (a)

> **Decisive corollary (a-structure, b-trap):** the sufficient-functional reframe is novel and
> wedge-preserving **only** in the `V_NLL`-inclusive form. Reduced to `V_do` alone it is *strictly higher
> limit but scooped* (collapses to windowed decoding) whenever MWPM is coherent-blind — and M4 says that
> regime is real. **Therefore the registered safe target is `V_NLL ∪ V_do`, and the live empirical
> question is how much coherent mass `V_do` actually carries through the frozen decoder (M4's
> covariation, re-measured at exact truth by CF-WR).**

---

## 4. Novelty vs prior art — the delta table

P4 is a **strictly weaker, sufficient-functional** target for a **coherent channel field**. The delta
against each adjacent body of work (extends `plan3.md` §1 to the *target* axis):

| Prior art | What it owns | Its TARGET | P4's delta (cite, never claim) |
|---|---|---|---|
| **Full-state reconstruction guarantee** [2604.01197] | a trace-distance reconstruction of the global state/channel | **full `J` to `½‖·‖₁ ≤ τ`** | P4 targets `P_V(J − J_glue)` — **strictly weaker** (a projection); **faithful precisely where full-state is obstructed** (KKB exp prefactor). The strong guarantee certifies `V^⊥` too, which decoding/NLL never query. |
| **KKB clustering** [2407.05835] | the 2D quantum-CMI obstruction (`exp(Θ(|A|+|C|))`, quantum-BP-fails-in-2D) | the **global density operator** | the obstruction is a **full-state** statement; P4's target lives in `V ⊊` full Choi, so the worst-case full-state prefactor is **not the relevant constant** for the sufficient functional (the P3 perturbative escape is the companion certificate on `V`). |
| **Windowed / modular decoding** (Skoric, Tan, Cain) | composing **decode decisions** across windows | **decisions** (`ΔLER`-equivalent), no channel field | P4 composes a **coherent channel FIELD**, of which `V_do` is one projection. Reduced to `V_do` alone P4 **degenerates into** this prior art **iff** MWPM is coherent-blind (§3.2, the trap) — which is why `V_NLL` is mandatory. |
| **TN contraction / dMLE carrier** ([2602.19722]) | Pauli windowing by bond dimension | the **Pauli state** (sums probabilities, not amplitudes) | the TN/dMLE target has **no coherent slot** (T-B theorem: Pauli/DEM iid fields pinned at R=1; `ADR 0008`). P4's `V_NLL` **keeps** the coherent/bunching DOF the Pauli TN structurally cannot carry — by the M3 measurement that NLL sees it. |
| **Local-generator reconstruction** (Ivashkov 2603.05492; steady-state local-channel; [2604.01197] local-channel-circuit) | recovering the **local GKSL `(h,a)` generator** in situ | the **local generator** (already low-complexity) | this is reframe-1 (the RECOVERY object) — **already escaping** the global obstruction via locality. P4 is **orthogonal**: it reduces the *composition TARGET* (the functional), not the recovery representation; the two compose (recover local generators → compose their `V`-sufficient functional). |

**The wedge (a):** no prior art owns *"composition limit of a SUFFICIENT FUNCTIONAL for a COHERENT
channel field."* Windowed decoding has the sufficiency (decisions) but no channel field and no coherent
slot; TN/dMLE has a channel object but no coherent slot and targets the full Pauli state; [2604.01197]
has a coherent channel object but targets the **full** state (the strong guarantee P4 weakens). P4
occupies the intersection that is empty in the literature: **a coherent-channel-field target that is
strictly weaker than full-state (hence faithful where full-state is obstructed) yet still
coherent-aware (`V_NLL`).** This is the `plan3.md` §1 open wedge, sharpened to the target.

---

## 5. Relation to P2 / P3 / the registration — certificate vs target vs representation vs recovery-object

P4 is the **fourth leg** of a four-object decomposition; it is consistent with and **changes none** of
the other three. The clean separation (a):

| Leg | Object | Role | Source | What P4 says about it |
|---|---|---|---|---|
| **Certificate** | full-state per-seam residual / CMI bound `D_Choi ≤ √(I_nats) = √κ·φ` | the **upper bound** that the per-seam glue is controlled | **P2** (linear per-seam law, √-bridge), **P3** (κφ² local, no exp prefactor) | unchanged — the full-state certificate is **the** rigorous control; P4 *uses* it as the bound on `‖J − J_glue‖`, which by §2 dominates `‖P_V(J − J_glue)‖`. |
| **Operational target** | `P_V(J − J_glue)`, `V = V_NLL ∪ V_do` | what we **actually need** to reconstruct | **P4 (this file)** | the new content: target the sufficient functional, get `ξ\*_func ≥ ξ\*_full`. |
| **Representation** | per-seam reduced Choi blocks (≤6q support, ≤2¹² dim) | the **feasible carrier** of the computation | `registration.md` amendment 1 | unchanged — P4 targets the same reduced blocks; `V` is a subspace **of** each reduced block, so the reframe is *within* the registered representation, not a new one. |
| **Recovery object** | local GKSL generators `(h,a)` | what the learner **emits** | reframe-1; Ivashkov 2603.05492; 2604.01197 local-channel-circuit | unchanged and **already escaping** — P4 composes the `V`-sufficient functional **of** the recovered local channels; the recovery is orthogonal to the target reduction. |

**The φ-regime is untouched (a, the explicit non-claim).** P3 establishes that the perturbative
escape holds for **small φ, strictly below threshold** (`0 ≤ φ ≲ φ\* ~ exp(−O(ξ))`, independent of
|A|+|C|). **P4 changes the TARGET, not the φ-regime.** Reframe-2 does **not** extend the controlled φ-window;
it says that *within* P3's controlled window, the **operational** reconstruction has a strictly higher
limit than the full-state one. At large φ (≳ φ\*) and at threshold (ξ→∞), P4 **inherits P3's INHERITS
verdict** — a strictly-weaker target does not rescue a regime where even the full-state perturbation
series diverges (the `V^⊥` mass is irrelevant when the `V` mass itself is uncontrolled). **P4 is a
target reduction inside P3's controlled regime, never an extension of it.**

**Consistency with P2.2 (the coefficient ratio).** P2.2's `c = c_{G1}/c_{G0} < 1` (Petz beats
mean-field, (b)) is a statement about the **full** per-seam residual. P4's `ξ\*_func ≥ ξ\*_full` is a
statement about the **projected** residual at a **fixed** glue rule. They are **independent and
compatible**: the projection contraction holds for **each** glue rule separately, so it preserves the
P2.2 ordering — `‖P_V(J − J_{G1})‖ ≤ ‖P_V(J − J_{G0})‖` whenever `‖J − J_{G1}‖ ≤ ‖J − J_{G0}‖` need
**not** hold in general (projection can reorder), so **P4 does not assume P2.2 and P2.2 does not assume
P4**; the within-run E_do comparison measures the projected ordering directly. (a — independence;
flagged because a careless reading would conflate them.)

---

## 6. Honest caveats and the measuring instrument

**(C-1) The strict gap is generic, not universal (a).** `ξ\*_func > ξ\*_full` is strict **iff**
`P_{V^⊥}(J − J_glue) ≠ 0`. If the glue residual happened to lie **entirely** in `V` (e.g. a purely
classical seam whose residual is all DEM-edge marginal shift, the P2 unital/twirled case where χ⊥=0),
the gap is **zero** and reframe-2 buys nothing. The generic case has `V^⊥` mass (coherent off-diagonal);
the **unital/degenerate** case (P2.3, R̂=1, φ=0) is the **null** case — consistent with the registered
zero-control. So the reframe's *value* is **co-extensive with the coherent/bunching content** — exactly
where the project's wedge is. (a)

**(C-2) `V_do` is decoder-specific and possibly coherent-blind ((b)/PROVISIONAL).** `V_do = (ker
dΦ_dec)^⊥` is defined **relative to the frozen decoder**. For frozen MWPM on an independent-edges DEM,
M4 measured the coherent sector to be (nearly) in `ker dΦ_dec` (covariation NULL). A **different**
frozen decoder (correlated-edge, soft, or a windowed-coherent decoder) would have a **different** `V_do`,
possibly coherent-aware. The "`V_do` is coherent-blind" premise is **decoder- and format-specific and
PROVISIONAL** — usable for go/no-go routing, never as a theorem. (b/PROVISIONAL)

**(C-3) `V_NLL` resolution is finite-window ((b)).** `V_NLL` contains the coherent sector *that the
held-out NLL can resolve at a given window width*. Deeper/longer-range coherence may be below the NLL's
resolution at small windows (the M3 finding includes inter-sample drift and long-range tails the window
construction did not fully bind). So `V_NLL` is the **resolvable** coherent sector, not all of it; the
reframe's coherent-slot guarantee is "as much coherence as the held-out NLL resolves," (b)-bounded by
window width. (b)

**(C-4) Sufficiency is a CHOICE, audited at run time.** Whether `V = V_NLL ∪ V_do` is genuinely
sufficient for the operational claim is **not** a theorem — it is the registered functional, and CF-WR
**measures** whether composing it suffices. The honest position: P4 supplies the **strict-inequality
structure and the wedge logic**; CF-WR's E_do/D_Choi co-primary AND-gate supplies the **measurement**.

**The measuring instrument (a, the registered gate).** P4 is **not** self-validating; CF-WR is its
empirical test. The mapping is exact:

> - **D_Choi** = ½‖J_s − J_glue,s‖₁ (per-seam reduced block, `registration.md` amendment 1) is the
>   **full-residual surrogate** — it scores `‖J − J_glue‖` *including the `V^⊥` directions the decoder
>   and NLL never read*. It is the **conservative** leg (upper-bounded by `√(I_nats)`; passing τ_D =
>   0.5·√(I_nats) is **necessary not sufficient**, `registration.md` §6).
> - **E_do** = `knob_dler_error` = |ΔLER_glue − ΔLER_true| is the **`V_do`-projection** — it scores the
>   decode-sufficient functional directly.
> - The **gap** between them — D_Choi small but E_do behavior diverging, or vice versa — is the
>   **measured `P_{V^⊥}` mass**, i.e. the magnitude `ξ\*_func − ξ\*_full` that §2.2 declares (b). **M4 is
>   the prior measured instance** of this gap (NLL/Choi win, MWPM `V_do` null).

So the CF-WR co-primary gate is, read through P4, the **instrument that measures the sufficient-functional
gap and tests whether `V_do` carries the coherent sector** — turning the (b) magnitude and the
(b)/PROVISIONAL coherent-blindness premise into measured numbers against exact 12q truth. (a — the gate
is the registered instrument; the numbers it returns are (b).)

---

## 7. Must-cite

- **The full-state guarantee P4 weakens:** the full-state **trace-distance** reconstruction guarantee,
  **[arXiv:2604.01197]** — the strong (full `½‖·‖₁ ≤ τ`) target; P4's sufficient functional is
  **strictly weaker** and faithful where this is obstructed. **(Also the local-channel-circuit
  reconstruction route cited as a reframe-1 RECOVERY anchor.)** Cite for the strong target — never
  claim it; P4 deliberately does **not** meet it.
- **The full-state obstruction (the prefactor on the strong target):** Kuwahara, Kato, Brandão,
  *Clustering of conditional mutual information and quantum Markov structure at arbitrary temperatures*,
  **[arXiv:2407.05835]** (PRX, [10.1103/9hx7-pzxw](https://link.aps.org/doi/10.1103/9hx7-pzxw)). Cite for
  `D_AC = exp(Θ(|A|+|C|))` worst-case full-state prefactor / quantum-BP-fails-in-2D — applied/evaded,
  never claimed (see P3 §3.1).
- **Windowed / modular decoding (the "composes decisions" quadrant the `V_do` trap collapses into):**
  Skoric, Tan, Cain et al. — windowed/sliding/parallel-window decoding (compose **decode decisions**,
  not a channel field). Cite for the prior art reframe-2 must out-distinguish via `V_NLL`.
- **TN / dMLE carrier (the "Pauli state, no coherent slot" quadrant):** the Pauli-TN / dMLE syndrome-
  likelihood carrier, **[arXiv:2602.19722]**; the **T-B theorem** (`docs/adr/0008-…md`,
  `D_package_derivations.md` §D5: unital-diagonal/Pauli/DEM iid fields pinned at R=1; non-unital CPTP
  expresses R>1 free). Cite for "TN composes the Pauli state, no coherent slot" — the structural reason
  `V_NLL` keeps a DOF the TN cannot.
- **Local-generator recovery (reframe-1, already escaping):** Ivashkov, Romanov, Gong, Gu, Hu, Yelin,
  *Ansatz-Free Learning of Lindbladian Dynamics In Situ*, **[arXiv:2603.05492]** (the local GKSL `(h,a)`
  recovery; "steady states don't identify the generator"); the **steady-state local-channel
  reconstruction** route. Cite for the RECOVERY object that escapes the obstruction by locality —
  **orthogonal** to P4's target reduction.
- **The per-seam certificate (local certificate that P4's target inherits):** **P2** (`P2_derivation.md`
  — linear per-seam residual, the √-bridge `D_Choi ≤ √(I_nats)`, L-additivity) and **P3**
  (`P3_coherent_CMI_prefactor.md` — κφ² CMI prefactor is **local, not exp**; the small-φ controlled
  regime). The full-state certificate that dominates the projected residual (§2, §5).
- **The project's own decision-projection machinery (`V_do` is not a new object):** `docs/METRICS.md`
  ("parameter-grade vs decision-grade"; `decision_pushforward`, `finite_displacement_regret`; the `a12i`
  zero-projection worked example = a concrete `V_do^⊥` direction). The measured M3 (+56.21 X / +44.28 Z
  nats/shot/window NLL win) and M4 (−40.26% X / −40.73% Z reversal; covariation NULL) instances —
  `docs/metric_results.md`. **M4 is the (b)/PROVISIONAL evidence for the `V_do` trap; M3 is the
  (a)-measured proof that `V_NLL` contains the coherent sector.**

---

## 8. FROZEN P4 (the registrable claims)

- **P4.1 (a, structure):** define `V_do := (ker dΦ_dec)^⊥` (decode-sufficient, poly(d), = the project's
  `decision_pushforward` support) and `V_NLL` (the held-out-NLL-determining syndrome-marginal directions,
  which **contain** the bunching/coherent sector by the M3 measurement). The operational target is
  `P_V(J − J_glue)`, `V = V_NLL ∪ V_do`, **strictly smaller than the full Choi**.
- **P4.2 (a, the contraction theorem):** `‖P_V(J − J_glue)‖ ≤ ‖J − J_glue‖` (projector is a
  contraction) ⇒ **`ξ\*_func ≥ ξ\*_full`**, with **strict inequality** iff `P_{V^⊥}(J − J_glue) ≠ 0`
  (generically true — the coherent off-diagonal directions no syndrome marginal reads). **The strict
  direction is (a); the gap magnitude `ξ\*_func − ξ\*_full` is (b)** = exactly what CF-WR's E_do/D_Choi
  co-primary gate measures.
- **P4.3 (a-structure / b-trap, decisive):** the variant choice determines the coherent slot.
  **`V_NLL`** = higher limit **and** keeps the coherent slot (M3: NLL sees bunching). **`V_do` only** =
  higher limit **but forfeits the wedge to windowed decoding IF the frozen MWPM is coherent-blind** —
  which M4 **measured** (covariation NULL, **(b)/PROVISIONAL**). **The safe object is `V = V_NLL ∪
  V_do`**, the theoretical content of the registered co-primary AND-gate.
- **P4.4 (a, novelty):** no prior art owns "composition limit of a sufficient functional for a coherent
  channel field." [2604.01197] is a **full-state** trace-distance target (strictly stronger; P4 weakens
  it); windowed decoding composes **decisions** (no channel field — the `V_do` trap quadrant); TN/dMLE
  composes the **Pauli** state (no coherent slot — T-B). P4 sits in the open wedge.
- **P4.5 (a, non-claim — the φ-regime is untouched):** reframe-2 changes the **TARGET**, not P3's
  φ-regime. The full-state perturbative bound (P3) stays the **CERTIFICATE**; `P_V(J − J_glue)` is the
  **OPERATIONAL TARGET**; reframe-4 reduced Choi blocks are the **REPRESENTATION**; reframe-1 local
  generators are the **RECOVERY object**. P4 inherits P3's INHERITS verdict at large φ / at threshold —
  a weaker target never rescues a regime where the `V` mass itself is uncontrolled.

**Verdict: the sufficient-functional reframe ESCAPES the full-state obstruction at the level of the
operational functional — (a) for the strict inequality `ξ\*_func ≥ ξ\*_full` and the `V_NLL`-keeps-the-
coherent-slot structure; (b) for the gap magnitude (CF-WR's E_do/D_Choi gate measures it) and for the
"frozen MWPM is coherent-blind" premise of the `V_do` trap (M4-PROVISIONAL). Genuinely novel: it is the
strictly-weaker, coherent-aware, channel-field target that the literature's full-state / decision-only /
Pauli-only quadrants each miss.**
