# Full-text review — Masot-Llima & Garcia-Saez, "Stabilizer Tensor Networks: universal quantum simulator on a basis of stabilizer states" (arXiv:2403.08724)

> **Provenance (2026-07-12): FULL-TEXT read (精读).** PDF downloaded fresh from
> `https://arxiv.org/pdf/2403.08724` → `outputs/papers/peps_foundation/2403.08724.pdf`
> → text via PyMuPDF (`fitz`) to `outputs/papers/peps_foundation/2403.08724.txt`
> (**13 pages / 1432 lines**, including the full Annex A–D). I read the ORIGINAL extracted
> text end-to-end (main text lines 1–486; Annex A Lemmas 1–3 + proofs lines 681–1199;
> Annex B entangling-power bound lines 1201–1274; Annex C worked example lines 1276–1317;
> Annex D tableau rules lines 1319–1432), not a second-hand summary. All §/Eq/Lemma/Fig
> refs below are transcribed from that text.
>
> **Verbatim load-bearing passages confirmed from the PDF text:** the basis decomposition
> `|ψ⟩ = Σ_i ν_i d̂_i |ψ_S⟩` (Eq. 2, lines 170–175); "**forgoes the correspondence between
> qubits and tensors … entanglement is transferred … into the basis**" (lines 274–278);
> the `|T⟩_n` example collapsing to a **χ = 1 MPS** while pseudo-rank ξ̃ = 2^n (Eqs. 11–12,
> lines 327–348); the non-Clifford rotation on |ν⟩ (Eq. 6, lines 208–210) and its Lemma-2
> proof (lines 768–855); the measurement projection + non-unitary rotation on |ν⟩ (Eqs. 8–9,
> lines 226–248; Lemma 3 lines 909–1184); the **χ′ ≤ 2⁴χ = 16χ worst case / ~2^2.46 average**
> single-rotation bound (Annex B, lines 1268–1274, main text lines 425–429); "**We focus on a
> 1D MPS structure**" (line 74).
>
> **ID/title verified from the PDF front matter (lines 1–6).** arXiv:2403.08724v2 IS the paper:
> Sergi Masot-Llima & Artur Garcia-Saez, "Stabilizer Tensor Networks: universal quantum
> simulator on a basis of stabilizer states," dated April 10 2024. Published as **PRL 133,
> 230601 (2024)** (venue confirmed via our repo's GCAMPS note ref [23], not from this PDF's
> own front matter — flagged as cross-ref).

## Metadata [paper]
- **Authors / affiliation:** Sergi Masot-Llima (Barcelona Supercomputing Center; Univ. de Barcelona) and Artur Garcia-Saez (BSC; Qilimanjaro Quantum Tech), Barcelona.
- **Venue / status:** arXiv:2403.08724v2 [quant-ph], 9 Apr 2024; published PRL 133, 230601 (2024) [venue via cross-ref].
- **Type:** Method / formalism paper (a *generalization of the tableau formalism* to a stabilizer BASIS whose amplitudes are stored in a tensor network) + small numerical demonstration (single-T-gate χ-growth statistics, Fig. 2). ~4-page Letter + Annex A–D.
- **Code:** Python implementation at `https://github.com/bsc-quantic/stabilizer-TN` (ref [42]); authors flag STIM (ref [43]) integration as the obvious speedup.

## Executive summary [paper]
The paper fuses the **stabilizer tableau formalism** (Aaronson–Gottesman, ref [37]) with a **tensor
network**. An arbitrary n-qubit state is written in a *stabilizer basis* `B(S,D)` — the stabilizer
state `|ψ_S⟩` plus all products of destabilizer generators `d̂_i` acting on it (Lemma 1, Yoder's
generalized stabilizer formalism [19]):

    |ψ⟩ = Σ_{i=0}^{2^n} ν_i d̂_i |ψ_S⟩     (Eq. 2)

The `2^n` amplitudes `|ν⟩ = Σ_i ν_i |i⟩` are stored **in an MPS** (Eq. 1). The whole point: the MPS
bond dimension **χ tracks NON-Clifford (magic) content, not stabilizer entanglement.** Update rules
are proven for all three primitives:

1. **Clifford gate G** — conjugate the tableau `B(S,D) → B(S̃,D̃)`; `|ν⟩` is **unchanged**, `χ`
   **preserved** (Eqs. 3–4). Stabilizer entanglement is absorbed into the basis "for free."
2. **Non-Clifford gate U** (single-qubit rotation, 2-term Pauli-basis decomposition) — a change of
   basis by a Clifford `δσ` followed by a **multi-qubit rotation on |ν⟩** (Eq. 6, Lemma 2). This is
   the *only* operation that can grow `χ`.
3. **Measurement of O = α δ_n̂ σ_m̂** — compute `⟨O⟩ = α⟨ν|X_n̂ Z_m̂|ν⟩` (Eq. 7), sample outcome `m`
   with **Born probability** `p± = (1±⟨O⟩)/2`, then apply a **projection `P_k = |0⟩⟨0|_k` + a
   non-unitary rotation `R̃` on |ν⟩** (Eqs. 8–9, Lemma 3), and update the tableau. Measurement
   **halves the number of non-zero coefficients** whenever the measured Pauli has an anticommuting
   part (n̂ ≠ 0) — so it can *reduce* χ.

Headline demonstrations: (i) `|T⟩_n` (n T-gates on |+⟩^n) is a **χ = 1 MPS** in the right basis even
though its pseudo-stabilizer-rank is maximal ξ̃ = 2^n (Eqs. 11–12) — magic that is trivial here is
exponential for a naive stabilizer-rank decomposition; (ii) a maximally-entangled *stabilizer* state
is a single basis element ξ = χ = 1, though it needs χ = 2^{n/2} as a plain MPS; (iii) one
non-Clifford single-qubit rotation grows the MPS bond by at most **χ′ ≤ 16χ** (worst case, far-apart
CNOTs forcing SWAPs), ~2^{2.46} on average, and the bound is **independent of n** (Fig. 2, Annex B).

## Method (deep) [paper]

**The stabilizer basis (Lemma 1, Annex A lines 687–710).** Given a stabilizer group `S` (generators
`s_i`) and its destabilizers `D` (generators `d_i`, with `{d_i,s_i}=0`, `[d_i,d_j]=0`, `[d_i,s_j]=0`
for i≠j), the `2^n` states `{d̂_i |ψ_S⟩}` (with `d̂_i = d_1^{i_1}…d_n^{i_n}`) are **orthonormal and
span H_n** — a complete orthonormal basis. So *any* |ψ⟩ has the expansion Eq. 2. The tableau (Fig. 1
b1) is the `n × (2n+1)` boolean array storing S and D generators; the amplitudes ν_i live in the
green MPS (Fig. 1 b2). The qubit↔tensor correspondence of a normal MPS is **abandoned**: the MPS
index runs over the destabilizer-power label `î`, not over physical qubits.

**Clifford update (Eqs. 3–4).** `G d̂_i |ψ_S⟩ = (G d̂_i G†) G|ψ_S⟩ = d̃_i |ψ_S̃⟩`, i.e. only the basis
labels change; `G|ν⟩ = |ν⟩`. Efficient O(n²) tableau update via Aaronson–Gottesman (Annex D
transcribes the CNOT/H/phase/measure/rowsum rules verbatim). **χ untouched.**

**Non-Clifford update (Eq. 6, Lemma 2, lines 768–855).** Decompose `U = Σ_i φ_i δ_d̂i σ_ŝi` in the
basis (Eq. A5). For the physically relevant 2-term case `U = φ_1 δ_1σ_1 + φ_2 δ_2σ_2`, Lemma 2 proves
`U` = (Clifford `δ_1σ_1`, applied to the tableau) ∘ (a single **multi-qubit rotation** on |ν⟩):

    R(2θ) = cos θ · I − i sin θ · X^{Ix} Y^{Iy} Z^{Iz},   θ = arccos(Re φ_1)   (Eq. A7)

with the axis-support vectors `Iy = (d̂_1+d̂_2)∘_h(ŝ_1+ŝ_2)`, `Ix = (d̂_1+d̂_2)+Iy`,
`Iz = (ŝ_1+ŝ_2)+Iy` (Eq. A8; ∘_h = elementwise product). Implemented as a **CNOT cascade + one
central single-qubit rotation** (Fig. 4). Standard {CNOT, RX, RY, RZ} compilation puts *every*
non-Clifford single-qubit gate in this form (main text lines 249–257).

**Measurement update (Eqs. 8–9, Lemma 3, lines 909–1184).** For `O = α δ_n̂ σ_m̂`:
`⟨O⟩ = α⟨ν|X_n̂ Z_m̂|ν⟩` (Eq. A17). Sample `m∈{+,−}` with `p± = (1±⟨O⟩)/2`. Then

    |ν′⟩ = P_k · [ (1/√2) I ± α(−i)^{|Iy|}/√2 · X^{Ix} Y^{Iy} Z^{Iz} ] |ν⟩   (Eqs. 9 / A20)

`k` = position of the first 1 in n̂; `P_k = |0⟩⟨0|_k` collapses the qubit. Lemma 3 proves the
renormalization is exactly `N = √((1±⟨O⟩)/2)` — i.e. a **faithful Born-rule projective
measurement**. When n̂ = 0 (measuring a stabilizer) the basis is untouched; when n̂ ≠ 0 the tableau
gets the usual Aaronson–Gottesman measurement update, and **the number of non-zero coefficients is
halved** (lines 985–987) — measurement can *shrink* the |ν⟩ support.

**Free operations / resource (Corollary 2.1, lines 857–864).** The free operations are all Clifford
gates plus any non-Clifford `U` whose Eq.-6 rotation is a *local* single-qubit rotation on |ν⟩ (which
does not grow χ). `χ` of the |ν⟩ MPS is the resource. Because Clifford gates never touch |ν⟩, **any
state simulable by a plain MPS is also simulable here**, and one can "move freely in the space of
states with fixed stabilizer rank."

**The χ-growth bound (Annex B, Eqs. B2–B4, lines 1201–1274).** Using the Schmidt/operator
decomposition of the applied gate (`U = Σ_k s_k A_k⊗B_k`, Schmidt number k), a rank-k gate takes
χ → at most kχ (Eq. B4). A CNOT has Schmidt number 2, so the two CNOTs crossing a bond give
`χ′ ≤ 4χ` for **adjacent** qubits. For **far-apart** qubits on a 1D MPS the CNOT must be routed with
SWAPs (Schmidt rank 4), giving the **worst case `χ′ ≤ 16χ`** (matches Fig. 2 simulations, avg
~2^{2.46}, n-independent). Crucially (lines 1272–1274): "**TN geometries other than MPS that adapt to
the connectivity … can reduce the bound to 4χ; this entails a bigger complexity in the TN
contraction, as is the case in general for higher dimensional networks.**"

## The MECHANISM (for implementation) [ours, distilled from the paper]

State = `(tableau B(S,D), MPS |ν⟩)`. Loop over the circuit:
- **Clifford / reset-Clifford** → tableau update only (Annex D); |ν⟩ and χ untouched. *All the
  surface-code syndrome-extraction backbone (H, CZ/CNOT, S, resets, Pauli corrections) is Clifford →
  it is FREE and carried EXACTLY in the tableau.*
- **Non-Clifford insertion** (a leakage-induced coherent rotation, a T-like magic gate) → decompose
  into Eq.-6 form, do the Clifford part on the tableau, apply the multi-qubit rotation (CNOT cascade
  + central RX) to |ν⟩. This is the *only* χ-growing step; bounded by 4χ (adjacent) / 16χ (routed).
- **Stabilizer measurement** (syndrome bit) → Born-sample the outcome from `⟨O⟩`, project |ν⟩ with
  `P_k R̃` (Eqs. 8–9), update the tableau; halves |ν⟩ support when the measured Pauli anticommutes.
- **Truncation** = a plain SVD on the |ν⟩ MPS bond, discard smallest singular values (the paper does
  *not* elaborate a bespoke scheme — it inherits ordinary MPS SVD truncation; GCAMPS's Eq. 8 makes
  this explicit with χ_max=32).

**The exactness that matters for us:** the physical bipartition entropy of the *stabilizer part*
(our S_A) is carried **losslessly in the tableau** — it is *not* represented in, and *cannot be
truncated by*, the χ bond. The χ bond only ever carries the **magic amplitudes** |ν⟩. This is the
structural inversion of our PEPS problem.

## Answering the four commissioned questions [ours]

### (1) Does it extend to 2D / a surface-code geometry, or is it 1D/MPS-only?
**Implemented: 1D/MPS-only.** The paper explicitly "focus[es] on a 1D MPS structure" (line 74) for
|ν⟩ and demonstrates only MPS. **BUT the |ν⟩ index is NOT physical geometry** — the qubit↔tensor
map is abandoned (lines 274–278); |ν⟩ is a 1D chain over the *destabilizer-power / magic-amplitude*
label. So "2D surface-code geometry" is a category question, not a blocker: the 2D surface-code
*stabilizer* structure lives entirely in the tableau (Clifford, free, exact), and the |ν⟩ MPS only
needs to carry the (sparse, weak) non-Clifford content. A PEPS/higher-connectivity |ν⟩ is *mentioned
as possible* and would cut the routing bound 16χ→4χ (lines 1272–1274), but is **not developed**.
Verdict: MPS-only in this paper; a 2D |ν⟩ is future work but is over the *magic* space, at far
smaller effective bond than our physical PEPS.

### (2) Projective measurement (syndrome extraction) + reset + repeated rounds?
**YES — directly and rigorously.** Lemma 3 (Eqs. 8–9) is a genuine Born-rule projective stabilizer
measurement: `⟨O⟩` computed on |ν⟩, outcome sampled at `p±=(1±⟨O⟩)/2`, |ν⟩ projected + tableau
updated, renormalization proven `=√((1±⟨O⟩)/2)`. Reset = measure + conditional Clifford, both native.
**Repeated rounds are unobstructed** and *favorable*: measuring an anticommuting Pauli **halves the
|ν⟩ support** (lines 985–987), so multi-round syndrome extraction tends to *contract* χ rather than
grow it — the opposite of our PEPS bond blow-up. This is the single strongest match to our
"FINITE, MEASURED, multi-round" requirement. (GCAMPS 2605.29514 is the paper that actually *runs*
this on the rotated surface code d3–d9; see cross-check.)

### (3) Weak non-Clifford leakage (qutrit) as bounded magic — and cost vs leakage strength?
**Partial / not native.** The formalism is strictly **qubit** stabilizer (Pauli group `P_n`, `Z_2`
tableau). A qutrit leakage level `|2⟩` is **not representable** — there is no third computational
level in the tableau. Carrying qutrit leakage as bounded magic would require a **qudit (Z_3)
stabilizer / Clifford extension**, which the paper does not provide = substantial new work.
*However*, the abstract mechanism is exactly right IF leakage is modeled as a weak non-Clifford
*rotation within a qubit subspace*: it enters |ν⟩ as bounded-χ magic (≤4χ/16χ per event), and — the
critical point — it does **NOT touch the stabilizer entanglement S_A** (that stays in the tableau).
**Cost vs leakage strength:** the χ-bound (16χ) is θ-*independent* (worst case), but in practice a
weak rotation (small θ, far from π/4) is dominated by its identity term, so after SVD truncation its
*effective* χ growth is small — and the true cost driver is the **number `t` of non-Clifford events**
(× rounds), not their amplitude. Weak + sparse leakage ⇒ small χ_ν (cf. GCAMPS's χ_max=32 to d=9).

### (4) Real path to a bounded-bond carrier for our measured leaky surface-code trajectory?
**Conceptually YES; concretely SUBSTANTIAL new work.** The primitives (Clifford-free tableau, Born
measurement, non-Clifford-as-bounded-χ-magic, stabilizer entanglement carried exactly for free) are
*precisely* the FORK-B design: a carrier whose bond tracks **only** leakage magic while our S_A
(2 ebits d3 / 4 ebits d5) sits exact in the tableau and can never be over-counted or truncated. But
to reach *our* target from *this paper* needs: (a) a **qutrit/qudit stabilizer extension** for
genuine leakage (the biggest lift); (b) a **multi-round QEC demonstration** (this paper has none —
GCAMPS supplies it, but only for coherent *qubit* crosstalk, still no qutrit); (c) reordering the
|ν⟩ chain / possibly a 2D |ν⟩ to control routing bonds. So: this is the **FORK-B foundation stone**,
not a drop-in carrier.

## Cross-check vs the GCAMPS note (`harper_nonclifford_crosstalk_surface_2605.29514.md`) [ours]

- **Is 2403.08724 the PARENT of GCAMPS? YES.** The GCAMPS note lists **ref [23] = Masot-Llima &
  Garcia-Saez PRL 133, 230601 (2024)** as its stabilizer-TN lineage (alongside Nakhl PRL 134 [22]).
  GCAMPS's representation `|ψ⟩ = C|MPS⟩` (Eq. 7 there: Clifford operator C + MPS) **IS this paper's
  construction** — Harper's `C` = our basis-change Clifford / tableau `B(S,D)`; Harper's `MPS` = our
  `|ν⟩`. Harper's "non-Clifford error commuted through C, collapses to Pauli in the tableau at
  measurement" is exactly Lemma 2 + Lemma 3 here. **2403.08724 is the clean foundational statement of
  WHY GCAMPS works** (bond tracks magic not stabilizer entanglement; free-operation/resource theory).

- **Does GCAMPS already cover our need?** *More of it than this paper does, but not all.* GCAMPS ADDS
  what 2403.08724 lacks for us: the **actual rotated surface code d3–d9 under multi-round syndrome
  extraction**, coherent-noise-during-extraction, and a measured **χ_max=32-suffices-to-d9** envelope
  (Schmidt decay, Fig. 2/3 there). So for a *qubit-coherent* surface-code carrier, **GCAMPS is the
  more directly reusable engine and this paper is the theory underneath it.** BUT **neither covers
  qutrit LEAKAGE** — GCAMPS's own L3 lists leakage/amplitude-damping as future work, and this paper is
  qubit-only. For FORK B we would build on the *pair*: this paper for the formalism/resource guarantee,
  GCAMPS for the QEC-scale forward machinery — and still add the qudit-leakage extension ourselves.

## Relevance to qec_twin [ours]

**Why this is the FORK-B foundation.** Our PEPS FET-ALS pathology is that a *single* per-edge bond is
forced to carry **both** stabilizer entanglement (bounded, exact — our independent GF(2) S_A = 2/4
ebits) **and** whatever the truncator over-counts, and the ALS metric (non-Hermitian/non-PSD,
unregularized pinv) then blows the bond up non-monotonically. This stabilizer-TN formalism
**structurally removes the confound**: stabilizer entanglement is stored in the tableau **exactly and
for free** (Clifford gates never touch |ν⟩, χ preserved), so the bond χ can only ever track magic.
There is **no scenario in this formalism where S_A gets corrupted by truncation** — S_A is not in the
truncated object. That is the decisive contrast with FORK A (fix the PEPS ALS): FORK B moves S_A out
of the bond entirely, rather than fighting to truncate it correctly.

**Reliability vs our ALS.** Deterministic and monotone where ours is not. No ALS, no environment
metric, no pseudo-inverse. Clifford is an *exact* tableau conjugation. The only lossy step is an
ordinary SVD on the |ν⟩ bond (Eckart–Young-optimal per bond, monotone in retained χ) — it cannot
exhibit our non-monotone-fidelity / pinv-divergence failure mode, because there is no environment
metric to be non-PSD and no over-parameterized linear solve.

**Cost at d3/d5 on one RTX 5090.** Clifford bulk = O(n²) tableau (17 qubits d3 / 49 qubits d5,
negligible). The MPS |ν⟩ is over the qubits carrying magic; for weak, sparse leakage χ_ν stays small
(GCAMPS: χ_max=32 to d=9). An MPS of ≤49 sites at χ≤32 in complex128 is **trivial** on a 5090 —
orders of magnitude cheaper than our physical PEPS ALS. Real cost = #non-Clifford leakage events ×
rounds; measurement *halves* support each round, so multi-round is self-limiting.

## Limitations [paper]
- **Qubit-only.** No qudit/qutrit stabilizer formalism — the biggest blocker for genuine leakage.
- **1D MPS for |ν⟩** demonstrated; the 16χ routing penalty for far-apart CNOTs is real (mitigable to
  4χ only by a higher-connectivity |ν⟩ they do not build).
- **Non-Clifford handling is proven only for the 2-term (single-qubit-rotation) decomposition**
  (Lemma 2); arbitrary multi-term unitaries "left for future work" (lines 1316–1317). Fine for
  compiled {CNOT, RX, RY, RZ} circuits, but a general 2-qubit non-Clifford gate is not covered.
- **No QEC / surface-code demonstration in THIS paper** — only single-T-gate χ-growth statistics
  (Fig. 2) and the |T⟩_n / max-entangled-stabilizer analytic examples. (GCAMPS supplies the QEC run.)
- **Resource R is conjectural.** The paper's own headline open question: the metric R that captures
  "efficiently representable" (low-entanglement OR low-stabilizer-rank ⇒ low R) is *not* identified;
  ξ̃ (non-zero |ν⟩ coefficients) only upper-bounds the true stabilizer rank ξ.
- **Optimal basis allocation unsolved** (Conclusions): choosing *when* to apply a Clifford to the
  tableau vs directly to |ν⟩ to minimize χ is "left for future work."

## Epistemic-status declaration [ours]
- **(a) exact / theorem-grade:** the basis completeness (Lemma 1), the Clifford-invariance of |ν⟩
  (Eqs. 3–4), the Born-rule measurement projection + renormalization (Lemma 3), and the per-event
  χ′ ≤ 16χ / 4χ bound (Annex B) — these are proved in the paper and are the load-bearing facts we
  rely on. **That S_A cannot be corrupted by |ν⟩-truncation** follows *exactly* from Clifford-
  invariance of |ν⟩ (a), and is the one theorem-grade guarantee we take from this paper.
- **(b) prediction band:** "χ_ν stays small (≲32) for weak sparse leakage at d3/d5" — a registered
  bet extrapolated from GCAMPS's measured d9/χ32 envelope; a miss is a finding, not a fact.
- **(c) heuristic / decision gate:** "FORK B is preferable to FORK A" — a routing decision this note
  informs, not a premise anything is derived from.
- **Undeclared ⇒ (c).** No conclusion here is a premise for further derivation until we have *built*
  and *measured* a qudit-extended, multi-round leaky-surface-code |ν⟩ carrier against our exact d3
  bayes-floor / DM oracle.

## How to use / trust + open questions [ours]
- **Trust level:** FULL-TEXT 精读 of a **published PRL** (higher baseline than a preprint), 13 pp
  incl. all proofs. Equations transcribed from PyMuPDF text. The core claims are *proved* (Lemmas
  1–3), not benchmarked-away.
- **Independent-verification potential:** high — the |T⟩_n χ=1 claim and the max-entangled-stabilizer
  ξ=1 claim are analytic and checkable by hand; the single-T-gate χ-growth (Fig. 2) is reproducible
  from the open code (ref [42]).
- **Open questions for our FORK-B decision:**
  1. **Qudit extension.** Is there a qutrit (Z_3) stabilizer-TN in the literature we can inherit
     (generalized Clifford + tableau), or do we build it? This is the gating unknown for genuine
     leakage. (Search Nakhl PRL 134 [22] and its citations; check whether GCAMPS's future-work
     leakage plan names a construction.)
  2. **Leakage-as-magic encoding.** Can weak qutrit leakage be *faithfully* projected to a
     within-qubit-subspace non-Clifford rotation (bounded magic) without an unbounded simplification
     error (FAITHFULNESS_PROTOCOL rule III)? If not, (1) is mandatory.
  3. **|ν⟩ ordering / 2D.** For our d3/d5 lattice, what qubit ordering of the |ν⟩ chain minimizes the
     routing (16χ vs 4χ) — and is a 2D |ν⟩ ever worth its contraction cost at χ≤32?
  4. **Reuse vs rebuild.** Reuse the BSC `stabilizer-TN` code [42] and/or GCAMPS as the engine, add a
     differentiable / qudit layer — vs implement from scratch (Stim tableau + torch |ν⟩ MPS). Cross-
     check against the GCAMPS note's open question (i).
  5. **S_A audit.** Because S_A is carried in the tableau, we should be able to read it off the
     tableau *independently* (GF(2) rank) and confirm it equals our 2/4-ebit oracle at *every* round —
     a free, exact, per-round check the PEPS carrier could never give us cheaply.

## Key equations (implementation reference)
- **Eq. 2** — stabilizer-basis expansion `|ψ⟩ = Σ_i ν_i d̂_i |ψ_S⟩` (the whole representation).
- **Eqs. 3–4** — Clifford: tableau conjugation, `G|ν⟩ = |ν⟩` (χ preserved).
- **Eq. 6 / Lemma 2 (A7–A15)** — non-Clifford single-qubit rotation → multi-qubit rotation on |ν⟩.
- **Eqs. 7–9 / Lemma 3 (A16–A32)** — Born measurement: ⟨O⟩, sample p±, project P_k R̃, renormalize.
- **Eqs. 11–12** — `|T⟩_n` = χ=1 MPS (magic-free-in-the-right-basis demonstration).
- **Annex B (B2–B4)** — χ′ ≤ kχ per gate; CNOT k=2 ⇒ 4χ adjacent, SWAP k=4 ⇒ 16χ routed.
- **Annex D (D2–D6)** — Aaronson–Gottesman CNOT/H/phase/measure/rowsum tableau rules (verbatim).
