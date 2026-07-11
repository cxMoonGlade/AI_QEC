# Full-text review — A.-R. Negari, S. Sahu & T. H. Hsieh, "Measurement-induced phases in the toric code" (arXiv:2307.02292v2, quant-ph, 2023/2024)

> **Provenance: FULL-TEXT read (精读).** Source: `docs/papers/negari_sahu_hsieh_toric_code_loop_measurement_2307.02292.txt`
> (1809 lines, arXiv source dump, includes references + Appendices A–C). Read end-to-end in two passes
> (main text through Discussion + refs, then Appendices A–C). ID/title verified against the header block
> (arXiv:2307.02292v2 [quant-ph] 5 Mar 2024, Perimeter Institute + U. Waterloo). Figures are not
> pixel-extracted — figure facts below are captions + numbers stated in body text only; no numeric phase
> boundary (e.g. a literal `p_c` value) is printed anywhere in the main text — the actual phase diagram
> numerics live in the cited Nahum–Serna–Somoza–Ortuño CPLC paper [28], not here.

## Metadata [paper]

- **Authors / affiliation:** Amir-Reza Negari, Subhayan Sahu, Timothy H. Hsieh — Perimeter Institute for
  Theoretical Physics + Dept. of Physics and Astronomy, University of Waterloo.
- **Venue / status:** arXiv:2307.02292v2 [quant-ph], revised 5 Mar 2024. No journal name given in the
  text itself (preprint as provided).
- **Type:** Analytical theory + exact mapping (parton/Majorana construction), not a numerical simulation
  paper — no tensor-network code, no simulated bond dimensions, no d-scaling benchmark. The "phase
  diagram" results are imported by exact mapping from a classical statistical-mechanics model (the CPLC
  loop model, ref [28]) and from prior free-fermion monitored-circuit papers (refs [21–23]).
- **Key relationship to our work:** THIS is a measurement-induced-*phase* (not literal TN-cost) paper
  about the **toric code specifically** (the closest analytically tractable relative of the rotated
  surface code we care about), analyzed via an exact Majorana-parton map to a classical loop model. It is
  the most on-topic available source for "does a stabilizer-structured resource state, measured almost
  entirely, produce bounded or growing entanglement on what's left" — but it is a **static ground-state
  measurement** paper reframed as an effective circuit, not a genuine multi-round syndrome-extraction
  simulation, and it never touches TN bond dimension, POVMs, ancillas, or leakage.

## Executive summary [paper]

The paper measures a large subset (the "bulk") of qubits in the toric code ground state in random
single-qubit Pauli bases (X, Y, Z with probabilities parametrized by `(p, q)`), leaving either two
distant qubits, two 1D boundaries, or one 1D boundary un-measured, and asks how much entanglement is
induced on what remains. Using an exact free-fermion (Majorana parton) representation, the measured
toric code maps onto the **completely packed loop model with crossings (CPLC)** — a classical loop model
with a known phase diagram (Nahum, Serna, Somoza, Ortuño [28]): a **short-loop phase** (loops have a
finite correlation length ξ) and a **long-loop "Goldstone" phase** (loops proliferate, correlations decay
logarithmically). Measurement-induced entanglement (MIE) on the un-measured region maps exactly onto
loop-model correlators: the short-loop phase gives **area-law** (or exponentially-decaying, for two
points) entanglement; the Goldstone phase gives **logarithmic** entanglement scaling — **never** volume
law is found or predicted anywhere in this paper. Section V shows that the specific case of "measure
everything except a single 1D boundary" maps *exactly* onto a genuine 1+1D monitored hybrid circuit
(alternating unitary gates and projective measurements on the boundary chain, built from Majorana
swaps/parity measurements), giving a first-principles justification for calling this a
"measurement-induced phase transition" in the usual hybrid-circuit sense. Section VII generalizes from
Pauli to arbitrary on-site measurement bases, mapping to Gaussian (free-fermion) tensor networks/circuits,
and the authors argue (by analogy to refs [21–23], not by new proof) that the area-law/log-law dichotomy
survives generically in that broader class. The Discussion explicitly contrasts this capped-at-log result
against the 2D cluster state (a *universal* MBQC resource), where an analogous protocol gives a genuine
area-to-**volume**-law transition [18] — the toric code, not being a universal resource, only ever
reaches log-law, never volume-law, on the unmeasured region.

## Method (deep) [paper]

**Setup (Sec. II):** Toric code ground state `|G>` on a torus/cylinder, built via the Majorana parton
construction: each qubit → 4 Majoranas `γ_{i,1..4}` with the physical constraint `D_j = γ_{j,1}γ_{j,2}γ_{j,3}γ_{j,4} = 1`
(Eq. 3). A subset `M` of qubits is measured in X, Y, or Z with probabilities `(1−q)(1−p)`, `p`,
`q(1−p)` respectively (the "(p, q) measurement protocol", Sec. II.B). The un-measured complement `M^c`
is what's analyzed.

**Stabilizer/Majorana bookkeeping (Sec. II.C):** each single-qubit Pauli measurement is a Majorana
bilinear measurement `iγ_jγ_i`; graphically this re-pairs Majorana "strands." Tiling all these pairings
over the whole lattice produces a global dimer/loop covering.

**The CPLC mapping (Sec. III):** measuring every site produces one of 3 pairing patterns per site
(Fig. 3b); tiling them gives configurations of the completely packed loop model with crossings, with
partition function `Z = Σ_C W_C`, `W_C = p^{Ny}[(1−p)q]^{Nx}[(1−p)(1−q)]^{Nz}` (just below Eq. 4/5). CPLC
is known (ref [28], via a replica limit `n→1` of a Z2 gauge theory coupled to O(n) matter / a sigma-model
continuum limit) to have a **short-loop phase** (massive sigma model, finite loop size ξ) and a
**long-loop "Goldstone" phase** (massless sigma model, loops of size ~ system size). Two load-bearing
loop observables:
  - **Watermelon correlator** `G_k(i,j)` — probability that k strands connect i, j. Goldstone phase:
    `G_k(i,j) ~ C_0 / [k(k−1) ln(d_ij/r_0)]` (Eq. 5, power-law-in-log decay). Short-loop phase:
    `G_k(i,j) ~ e^{−d_ij/ξ}` (exponential decay).
  - **Spanning number** `n_s` (strands crossing a cylinder from one open end to the other). Goldstone
    phase: `n_s ≈ (1/2π)[ln(L/L_0) + ln ln(L/L_0)]` (Eq. 6, i.e. ~log L). Short-loop phase: `n_s → 0`.

**Entanglement ↔ loop-strand counting (Sec. IV, Appendix A):** after projecting onto the physical
qubit Hilbert space and putting the surviving stabilizer generators into canonical form, entanglement
across any bipartition is proportional to the *number of independent canonical stabilizer generators
straddling the cut*, which is in turn an exact linear function of the number of loop strands crossing
that cut (proved combinatorially in Appendix A for both the "one boundary" and "two boundaries" cases:
`n` crossing strands → `n` (one boundary) or `n−2` (two boundaries) independent stabilizers, Eq. 8).
This is the mechanism that turns loop-model statistics into an operator statement about measurement-induced
entanglement — MIE between two qubits = `G_4(i,j)·ln2` (Eq. 7); MIE between two boundaries =
`(n_s − 2) ln2 / 2` for `n_s ≥ 2`, else 0 (Eq. 8, from spanning number).

**The exact 1+1D hybrid-circuit mapping (Sec. V.A, Table I):** for the "one boundary unmeasured" case,
bulk measurements on an `N×N` toric-code cylinder are shown to realize, via Jordan–Wigner transformation,
a literal **depth-N hybrid circuit on the N boundary qubits** alternating two timestep types:
  - odd steps (per neighbor pair): prob `p` → 2-qubit unitary `U1` (from bulk Y-measurement); prob
    `(1−p)q` → identity (bulk X); prob `(1−p)(1−q)` → `M1 = Z_kZ_{k+1}` measurement (bulk Z).
  - even steps (per site): prob `p` → on-site unitary `U2` (bulk Y); prob `(1−p)q` → `M2 = X_k`
    measurement (bulk X); prob `(1−p)(1−q)` → identity (bulk Z).
  This circuit conserves an Ising `Z_2` symmetry (`∏X_i`) and is identified (Sec. VI.A) as belonging to
  the same class as the Sang–Hsieh "measurement-protected phases" hybrid circuit [12] (ZZ + X
  measurements + Ising-symmetric random Clifford unitaries).

**General on-site measurements (Sec. VII):** replacing X/Y/Z with an arbitrary Bloch-sphere direction
`n⃗` maps each measured qubit to a Gaussian (free-fermion) tensor on its 4 virtual Majorana legs
(Eqs. 14–15), and the whole measured-bulk-plus-boundary construction to a **Gaussian tensor network**
(Sec. VII.B) equivalently reformulated as a **Gaussian hybrid circuit** of weak-measurement/parity
operators `K_n⃗` on a Majorana chain (Eq. 16–17, Sec. VII.C) — connecting to the free-fermion monitored
circuit literature [21–23].

**Control parameters:** `p` = probability of the Y-type outcome (→ unitary gate in the boundary-circuit
picture); `q` = split between X and Z among the non-Y outcomes. In the general on-site generalization
(Sec. VII), the control parameter is the *full measurement-basis distribution* `w̃(n⃗)` over the Bloch
sphere (subject only to `w̃(n⃗) = w̃(−n⃗)`), of which `(p,q)` is a special (Pauli-restricted) 2-parameter
slice.

## Results + numbers [paper]

| Quantity | Regime / value | Source |
|---|---|---|
| CPLC phase diagram | short-loop phase (massive, finite ξ) vs long-loop "Goldstone" phase (massless, critical) | Fig. 4; imported from ref [28], no new derivation here |
| Watermelon correlator `G_k(i,j)` | Goldstone: `~ 1/[k(k−1)ln(d/r0)]` (power-law-in-log, i.e. slowly decaying); short-loop: `~ e^{-d/ξ}` | Eq. 5 |
| Spanning number `n_s` (cylinder) | Goldstone: `~(1/2π)[ln(L/L0)+ln ln(L/L0)]` (grows ~log L); short-loop: `→ 0` | Eq. 6 |
| MIE between 2 unmeasured qubits | `⟨S_MIE(i,j)⟩ = G_4(i,j)·ln2` — long-ranged in Goldstone, short-ranged in short-loop | Eq. 7 |
| MIE between 2 boundaries | `(n_s−2)ln2/2` for `n_s≥2`, else 0 — log-scaling in Goldstone, →0 in short-loop | Eq. 8 |
| Entanglement of a contiguous sub-region A of the ONE unmeasured boundary | Goldstone: `S_A ≈ (ln2/2)[ln|A| + (1/4π)(ln|A|)^2]` (Eq. 11, **log-squared correction to a log leading term** — genuinely growing, not saturating); short-loop: **area law** (bounded) | Eq. 11 |
| Spin-glass order (Edwards–Anderson `O`) | short-loop, `q<1/2`: `O ~ L` (extensive / spin-glass ordered); Goldstone / `q>1/2` regime: implied paramagnetic, `O ~ O(1)` | Sec. VI.A |
| Ceiling on entanglement class reached | **Never volume law anywhere in this paper** — max scaling found is `S_A ~ (ln|A|)^2` (Eq. 11); area law is the "good" phase | Secs. V.B, VIII |
| Contrast case: 2D cluster state (universal MBQC resource) | Same-style bulk-measurement protocol DOES give an **area-to-volume-law transition** [ref 18, Liu–Zhou–Chen] | Discussion (Sec. VIII), explicit contrast |
| General on-site (non-Pauli) case | "area law and critical logarithmic scaling separated by phase transitions" — same log ceiling, no volume law reported | Sec. VII.D |
| No explicit `p_c`/`q_c` number | The paper never states a numeric critical value for `p` or `q` in the main text; phase location is stated qualitatively (`q<1/2` ⇒ short-loop is asserted, used only to get the spin-glass sign; the literal 2D `(p,q)` phase boundary curve lives in ref [28]'s own numerics, not reproduced here) | Sec. VI.A, Fig. 4 (schematic only) |

## The regime boundary [paper → the crux]

**What is PROVEN (exact mapping, not conjecture) in this paper:**
1. Entanglement on the un-measured region is an *exact* linear function of loop-strand crossing number
   (Appendix A) — this is a rigorous combinatorial identity for the toric-code parton construction, not
   a numerical fit.
2. The dichotomy is **area law (bounded) vs logarithmic-with-log² correction (a genuinely GROWING but
   sub-volume-law quantity)** — Eq. 11 for the single unmeasured boundary is the load-bearing result:
   `S_A` scales as `ln|A|` at leading order with a `(ln|A|)²` correction in the Goldstone phase. This is
   NOT a bounded/saturating quantity — it is a slow-but-unboundedly-growing entanglement scaling. Do not
   conflate "not volume law" with "bounded/area law": the paper's two possible outcomes are (a) bounded
   (area law) or (b) growing-but-slowly (log/log² scaling), never volume law.
3. **The measurement RATE here is fixed at unity** in the base (p,q) setup — every bulk qubit IS measured
   (this is a static, one-shot measurement of a fixed pure state, not a circuit where a *fraction* p of
   sites are measured per round while others evolve unitarily). The control parameter that produces the
   phase transition is **which bases are measured, in what relative proportion** (the values of p and q,
   i.e. the RELATIVE WEIGHT of X vs Y vs Z measurements), not whether measurement happens at all. Only in
   the *derived* 1+1D boundary-circuit reformulation (Sec. V.A, Table I) does `p` re-acquire a
   measurement-rate-like meaning (fraction of timesteps that are unitary `U1/U2` vs measurement `M1/M2`/
   identity) — but even there, at fixed `p` (fixed unitary-vs-measurement ratio), the phase can still
   switch between area-law and Goldstone-log depending on `q` (the split between the two *measurement
   types*, X vs Z). **This is the single most load-bearing fact for our crux**: at a fixed, arbitrarily
   high measurement rate `1−p→1`, the entanglement phase is NOT automatically area-law — it depends on
   the STRUCTURE (which stabilizer/basis is being measured), not the RATE.
4. **Geometry/structure dependence, explicitly stated by the authors (Discussion, Sec. VIII):** the
   toric code is *not* a universal MBQC resource state, and this is why the boundary entanglement is
   capped at logarithmic — for the 2D cluster state (which IS a universal MBQC resource), the same style
   of bulk-measurement protocol produces a genuine **area-to-volume-law transition** (citing Liu, Zhou,
   Chen [18]). This is a direct, named geometry/structure-class dependence: stabilizer-code ground states
   (toric code, presumably surface-code-like states generally) cap out at log-law; universal
   entanglement-resource states can reach volume law. The paper does not prove this is universal for
   *all* stabilizer codes — it is a single worked example (toric code) contrasted against a single
   counter-example (cluster state) from a different paper.

**What is CONJECTURED / imported by analogy, not proven here:**
- Section VII.D extends the claim to general (non-Pauli) on-site measurement bases by citing prior
  free-fermion monitored-circuit results [21–23] and stating "we infer that the boundary MIE phase
  diagram also behaves similarly" — this is an explicit inference, not a new derivation in this paper.
  It is restricted to the free-fermion/Gaussian universality class (quadratic-in-Majorana operators);
  the authors do not claim this survives for interacting/non-Gaussian circuits.
- The claim that toric-code-like (non-universal-resource) stabilizer states generically cap at log-law
  (vs cluster-state-like universal resources reaching volume law) is stated as a single-example contrast
  in the Discussion, not as a theorem covering the whole class of "structured stabilizer codes."

**Model-class caveats that matter for mapping this onto a real syndrome circuit (all explicit
ANALOGIES, not identities):**
- This is a **Clifford/free-fermion (Gaussian, quadratic-Majorana) circuit class**, exactly solvable
  because the toric code's parton representation is Gaussian. A generic weight-4 POVM injecting leakage
  or non-orthogonal Kraus content (as in our simulator's `√E_s` measurement compilation) is **not**
  a rank-1 projective single-qubit measurement in an arbitrary Bloch direction — it is a genuinely
  higher-rank, multi-qubit, non-Clifford object. The paper's on-site-measurement generalization
  (Sec. VII) only covers single-qubit, rank-1, projective measurements; it does **not** cover multi-qubit
  weight-4 measurements or non-projective (weak/POVM) measurements with leakage.
- The "time" axis in the central Sec. V mapping is the **spatial extent of the toric-code lattice**
  (an `N×N` static ground state reinterpreted as a depth-N circuit via geometry), not literal repeated
  syndrome-extraction ROUNDS over real circuit time. Whether the same phase structure holds for a
  genuinely time-repeated (Floquet-like) syndrome circuit over ~40 rounds is an extrapolation, not
  something this paper directly addresses.
- The underlying code is the **unrotated toric code** (translation-invariant, torus/cylinder boundary
  conditions), not the rotated d=5 XZZX surface code. The paper does briefly discuss how rough/smooth
  surface-code boundary conditions can be generated from the same construction (Sec. V, ln 639–658), but
  does not analyze the rotated/XZZX variant or leakage.
- No numeric critical `p_c`/`q_c` is given in the main text — only qualitative statements (`q<1/2` used
  as sufficient for extensive spin-glass order in the short-loop phase). A quantitative phase boundary
  for "how much X/Z weight would tip a syndrome-extraction-like protocol into Goldstone/log growth" is
  not directly extractable from this paper alone; it requires the cited Nahum et al. CPLC numerics [28].

## Relevance to the d5 PEPS crux [ours]

**Does this support "bond should saturate" or does it identify a genuine growth mechanism?** — **Both,
conditionally.** The paper's clearest and most load-bearing message for us is:

1. **High/maximal measurement rate alone does NOT guarantee area law.** In this paper's base setup, every
   bulk qubit IS measured (rate = 1 in the plain sense), yet the surviving boundary entanglement phase
   still bifurcates between area-law and log-growing depending on *which* stabilizer bases are measured
   and in what proportion. This directly undercuts a naive "p≈1 ⇒ automatically bounded" argument for our
   syndrome-extraction circuit — the fact that ~all ancillas are measured every round is not by itself
   sufficient evidence the PEPS bond must saturate; the STRUCTURE of what's measured (weight-4 stabilizer
   POVMs, X-type vs Z-type, on the rotated lattice) is the thing that actually matters, echoing the
   finding here that `q` (the X/Z split), not just "measurement happens," sets the phase.

2. **Genuine growth in this model class is capped below volume law (log/log²), never volume law**, for a
   *non-universal MBQC resource* like the toric code — and syndrome-extraction Clifford circuits acting
   on stabilizer-code states are exactly the kind of "non-universal resource / highly structured
   stabilizer" setting this paper's toric-code example instantiates (in contrast to the cluster-state
   counter-example, which IS a universal resource and DOES reach volume law). This is modest, genuine
   supporting evidence that our observed fast bond growth (4→18→>40 in 2 rounds) reflects something OTHER
   than "genuine volume-law physics of a structured syndrome circuit" — because this paper's worked
   example of a structured stabilizer resource state never produces volume-law growth, only at-worst
   log-law. **But** log-law growth is still genuine, unbounded (if slow) growth — it is not the same
   claim as "bond saturates to a constant." If our real regime corresponds to something like the
   Goldstone/log phase of this analogy, we would still expect a slowly, persistently growing bond
   (consistent with `chi ~ poly(rounds)`, not `chi ~ e^{rounds}`), which is a much weaker and different
   claim than strict area-law saturation.

3. **What this does NOT rule out as the explanation for our pilot's 4→18→>40 growth:** the observed
   growth rate (roughly ×4.5 per round) is far too fast to be explained by even the Goldstone/log-law
   phase of this paper's model (which predicts entanglement `~ (ln rounds)²`, i.e. bond dimension growing
   at most polynomially in rounds, not near-exponentially). If our bond is genuinely tracking a
   log-law-type physical growth, it should decelerate quickly and look nothing like exponential-looking
   early growth. The mismatch in growth *rate* — not just the bounded-vs-growing binary — is itself
   evidence toward "instrument artifact" (compiled weight-4 √E_s POVM injecting spurious entanglement,
   and/or non-optimal truncation), since neither of this paper's two possible outcomes (area law, or
   `(ln L)²` log-squared growth) produces anything resembling near-exponential early-round growth.

4. **The "which stabilizer, not whether measured" lesson is a concrete design/debugging pointer**: if our
   carrier's bond growth is basis/structure-sensitive the way this paper's `q` parameter is, a natural
   diagnostic is to check whether our weight-4 √E_s POVM is being applied in a way that over-weights one
   Pauli sector relative to the ideal projective syndrome measurement (analogous to drifting q away from
   the "good" side of its transition) — i.e. audit the compiled POVM's basis content against the intended
   ideal stabilizer measurement before concluding the physics itself grows unboundedly.

## How to use / trust + open questions [ours]

- **Trust level:** FULL-TEXT 精读 (1809 lines including references and 3 appendices). This is a rigorous
  analytical-theory paper (exact combinatorial mapping in Appendix A, exact circuit mapping in Sec. V);
  the weakest links are (a) the Sec. VII generalization to non-Pauli measurements, which is stated as an
  inference from other authors' work, not re-derived here, and (b) the total absence of a literal numeric
  phase boundary for `(p,q)` in the main text (the real numbers live in the cited CPLC paper [28], not
  fetched here).

- **What is a genuine finding vs an analogy for us, explicitly:**
  - GENUINE (proven, exact): the loop-strand ↔ stabilizer-generator ↔ entanglement identity (Appendix A);
    the area-law vs log/log²-law dichotomy for the toric code specifically (never volume law in this
    model); the toric-code-vs-cluster-state (non-universal vs universal resource) contrast as the origin
    of the log-vs-volume ceiling.
  - ANALOGY ONLY (do not treat as load-bearing physics for our carrier): mapping "p≈1 syndrome circuit"
    onto this paper's `p`/`1−p` parameters; mapping our weight-4 leaky POVM onto this paper's rank-1
    single-qubit projective on-site measurement; mapping "40 rounds of real circuit time" onto the
    paper's "depth-N circuit from lattice geometry" construction.

- **Open questions for our build:**
  1. Is there a *quantitative* CPLC-style phase-diagram location for a realistic X/Z-stabilizer weighted
     syndrome-extraction protocol (as opposed to this paper's uniform random single-qubit basis choice)?
     This paper doesn't answer that; it would require either re-deriving the loop model for the actual
     rotated-surface-code syndrome circuit or finding a more targeted follow-up (e.g. Sang & Hsieh [12] or
     Behrends–Venn–Béri [32], the latter explicitly cited here as mapping toric-code error correction
     under coherent+incoherent errors to 1+1D free-fermion circuits — closer to our actual setting and
     worth a follow-up close-read).
  2. Does the log/log² (not area-law) Goldstone phase of this paper's toric-code example, if it turns out
     to be the operative regime for a real syndrome circuit, still translate into a *tractable* (if
     slowly-growing) PEPS bond over ~40 rounds, or does even polynomial-in-rounds growth break our
     feasibility budget at d=5?
  3. Given point 3 above (growth-rate mismatch), the most actionable next step is NOT more literature
     reading but a direct audit of the compiled weight-4 √E_s POVM's structure/truncation in the pilot
     run, since this paper's model class caps genuine physics-driven growth well below what the pilot
     showed.
