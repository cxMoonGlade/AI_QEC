# Full-text review — Hines, Ostrove, Rudinger, Seritan, Young, Blume-Kohout & Proctor, "Simulating Quantum Error Correction beyond Pauli Stochastic Errors" (arXiv:2603.18457)

> **Provenance (2026-06-19): HTML full-text read.** The downloaded PDF
> (`docs/papers/qec_beyond_pauli_stochastic_sim_2603.18457.pdf`) is **broken — only 1 page renders**, so
> it was NOT used. This note is built from the **arXiv HTML full text at
> `https://arxiv.org/html/2603.18457v1`** (Introduction, Results §2.1–2.4, Discussion, Methods §4.1–4.5,
> Appendices A–D incl. theorem/lemma statements, simulation-detail subsections, and figure/table
> captions), fetched via WebFetch. The HTML summariser declined verbatim reproduction, so equations and
> wording below are close technical paraphrases of the stated content rather than character-for-character
> quotes; where a number is the summariser's paraphrase rather than a figure I could read pixel-for-pixel,
> it is flagged. **Figure curves are not pixel-extracted** — figure-level facts are the captions plus the
> numbers stated in the running text. Epistemic tags: **[paper]** = stated/derived in the paper;
> **[twin]** = our application/inference for `qec_twin` (not the paper's claim).

## Metadata [paper]
- **Authors / affiliation.** Jordan Hines, Corey Ostrove, Kenneth Rudinger, Stefan Seritan, Kevin Young,
  Robin Blume-Kohout, Timothy Proctor — all **Quantum Performance Laboratory, Sandia National
  Laboratories** (Albuquerque, NM 87185 / Livermore, CA 94550). This is the Sandia GST / error-generator
  group (the `pyGSTi` authors).
- **Venue / status.** arXiv:2603.18457v1 [quant-ph], dated **19 Mar 2026**; year 2026; no journal yet.
- **Type.** Classical **forward-simulation method** + applications: a perturbative algorithm that maps an
  arbitrary small-rate Markovian *circuit-level* error model onto a **detector error model (DEM)** for an
  FTQC circuit, then uses that DEM for Monte-Carlo logical-error estimation, noise-adapted decoding, and
  approximate strong simulation.
- **Lineage.** Builds directly on the **elementary error generator (EEG)** taxonomy of Blume-Kohout,
  Hines et al. ("error generators" / Lindbladian H–S–C–A basis used in GST) and on Stim/`pyGSTi` DEM
  tooling. It is the *coherent/non-Pauli* counterpart to Stim's Pauli-only DEM pipeline.

## Executive summary [paper]
QEC is designed and validated against **Pauli stochastic** error models, but real hardware has **coherent
and non-Pauli** errors whose circuit-level effects differ sharply from stochastic Paulis, and whose impact
on QEC/FTQC has been "largely unpredictable" because exact simulation costs exponential resources. The
paper's central technical result is a method to **map any sufficiently-small-rate Markovian circuit-level
error model onto a DEM** for an FTQC circuit. The trick: represent every error channel as
`E = exp(G)` with the generator `G` expanded in the **EEG basis** (Hamiltonian `H`, stochastic `S`,
Pauli-correlation `C`, active `A`); **propagate generators through the Clifford circuit** by conjugating
their Pauli indices (efficient, Gottesman–Knill-style); **compose** the propagated layer generators into a
single circuit generator `G_c` via a **Baker–Campbell–Hausdorff (BCH)** expansion; **partition** `G_c` by
**DEM event class** (the set of detectors a generator flips); and **factorise** `exp(G_c)` into independent
single-DEM-event channels via a **Zassenhaus** expansion. Each resulting single-event channel's flip
probability is read off from a trace `p_D = ½(1 − Tr(P · exp(G_D)[|ψ⟩⟨ψ|]))`. The output is a standard
(Stim-compatible) DEM whose event rates are **analytic functions of the physical noise parameters**,
enabling approximate strong simulation and hardware-tailored decoding.

Applied to surface-code syndrome extraction, the bivariate-bicycle **Gross code** `[[144,12,12]]`, and
**magic-state cultivation**, the headline empirical claims are: (1) for `d=3` rotated-surface syndrome
extraction the coherent-error DEM predicts detection-history distributions **~100× more accurately (in
total variation distance, TVD) than a Pauli-twirled DEM**, with leading-order prediction error scaling as
`TVD ∝ ε_gen^{1.5} = O(ε_h^3)`; (2) **coherent error shifts the fault-tolerance threshold** — a 75%-coherent
model has threshold CNOT-infidelity ≈ **0.006** vs ≈ **0.012** for the stochastic equivalent of identical
generator infidelity (a ~2× shift), with >0.002 threshold spread across 10 random sparse CPTP models;
(3) coherent error can **increase logical error rates by an order of magnitude** vs the equivalent
stochastic model; (4) in the Gross code, coherent errors can **cancel constructively/destructively**, so
Pauli-twirling **over-estimates** the logical error rate by **up to 24%** in some regimes; and (5) in
**magic-state cultivation**, raising the coherent fraction of Z-type error from 0% to 35% **reduces the
discard probability ~10× and increases the logical-error probability ~10×**, traced via a sensitivity
matrix to the circuit being **~15–28% more sensitive to coherent than stochastic Z-type errors**.

**Crucial scope caveat for us:** the method models **CPTP errors on the computational subspace only**. It
**explicitly cannot model leakage** (population leaving the qubit subspace), and **amplitude damping**
produces **anticorrelated detection events** that need **negative DEM event rates** (Appendix B.2) — exactly
the two non-Pauli channels at the center of our teacher program.

## Contributions (claim → evidence → strength) [paper]
- **C1 — EEG→DEM mapping for arbitrary small Markovian errors (Methods §4.1–4.4, App. A).** Any
  small-rate CPTP circuit error model becomes a DEM. *Evidence:* the five-step algorithm
  (defer-measurements → propagate → BCH-compose → partition by DEM event class → Zassenhaus-factorise →
  trace each event), with **Theorem 1** (a generator made only of EEGs of a single DEM-event class produces
  a single-event DEM, exactly). *Strength: strong — the enabling result; this is the paper.*
- **C2 — Leading-order correctness + a CPTP-positivity guarantee (App. B.1, Theorem 6).** At leading order
  (first order in `S,C,A`; second order in `H`) **CPTP error models cannot produce negative DEM event
  rates** — so the leading-order DEM is a *valid* probability model. *Evidence:* Theorem 6 via Lemmas 7–8
  (sign-consistency of correlation generators). *Strength: strong (settles when the construction is a
  legitimate sampler).*
- **C3 — Validated accuracy: ~100× over Pauli twirl (Results §2.2, Fig. 1).** On `d=3` surface, 2 rounds,
  TVD vs exact statevector is 1–2 orders of magnitude smaller than Pauli-twirled; dominant detection
  histories to ~1% relative precision (many to 0.1%); error scales `ε_gen^{1.5}`. *Strength: strong (the
  cleanest quantitative validation, against exact ground truth).*
- **C4 — Coherent error shifts thresholds and amplifies LER (Results §2.3, Fig. 2).** ~2× threshold shift
  (0.012→0.006) at 75% coherent; >0.002 spread over 10 random CPTP models; order-of-magnitude LER increase
  vs stochastic. *Strength: strong as a demonstration; the specific magnitudes are model-dependent.*
- **C5 — Constructive/destructive coherent interference (Results §2.3, Fig. 3, Gross code).** Logical error
  minimised at **nonzero** `H_{XX}` CNOT coherent rate (~−0.013); Pauli-twirl over-estimates LER by up to
  24%. *Strength: strong (qualitatively new behaviour Pauli models cannot show).*
- **C6 — Magic-state cultivation cost amplification (Results §2.4, Fig. 4).** 0%→35% coherent Z-error
  fraction ⇒ ~10× discard reduction and ~10× logical-error increase; sensitivity matrix shows ~15–28%
  greater sensitivity to coherent vs stochastic Z errors. *Strength: strong (a resource-cost consequence,
  with a mechanistic sensitivity-matrix explanation).*
- **C7 — Analytic physical-parameter→DEM-rate relations (Methods §4.5, Discussion).** DEM event rates are
  explicit (low-order-polynomial) functions of physical error parameters `θ`, enabling **approximate strong
  simulation** and **hardware-tailored DEM decoding**. *Strength: medium-strong (powerful for calibration;
  decoder gains shown to be modest sub-threshold).*

---

## Method (deep) [paper]

### 1. Error-generator (EEG) representation
Every imperfect operation is `Ê = exp(G) ∘ U` where `U` is the ideal Clifford layer and `G` is the **error
generator**, expanded over the four **elementary-error-generator** superoperator classes acting on
`n`-qubit Paulis `P, Q` (Methods §4.1; App. A.1):

- **Hamiltonian:** `H_P[ρ] = −i[P, ρ]` (coherent over-/under-rotation).
- **Stochastic:** `S_P[ρ] = PρP − ρ` (Pauli-stochastic error).
- **Pauli-correlation:** `C_{P,Q}[ρ] = PρQ + QρP − ½{ {P,Q}, ρ }` (correlates two Paulis).
- **Active:** `A_{P,Q}[ρ] = i( PρQ − QρP + ½{[P,Q], ρ} )` (mixes coherence and correlation).

So `G = Σ_P ε_{h_P} H_P + Σ_P ε_{s_P} S_P + Σ_{P,Q} ε_{C_{P,Q}} C_{P,Q} + Σ_{P,Q} ε_{A_{P,Q}} A_{P,Q}`.
Two facts make this tractable: **(a) sparsity** — real hardware generators have ≪ `16^n` nonzero EEG
coefficients; and **(b) a perturbative hierarchy** — Hamiltonian (coherent) rates are taken `O(ε)` while
`S, C, A` rates are `O(ε²)`, reflecting that calibration-error coherent terms dominate, with
stochastic/correlation effects appearing at second order.

### 2. Propagating generators through Clifford circuits
EEGs conjugate through a Clifford `U` by simply conjugating their **Pauli indices** (with `±1` sign factors
`s_{U,P}`): e.g. `U† S_P U = s_{U,P} S_{U†PU}`, `U† H_P U = s_{U,P} H_{U†PU}`,
`U† C_{P,Q} U = s_{U,P} s_{U,Q} C_{U†PU, U†QU}`, and likewise for `A`. Because Clifford conjugation of a
Pauli is `poly(n)` (Gottesman–Knill), **propagating the whole error model to the end of the circuit is
efficient**, and sparsity is preserved. **Mid-circuit measurements (MCMs)** cannot be conjugated unitarily;
the fix (App. A.2) is an **expanded circuit** with **auxiliary virtual qubits** that **defers all
measurements to the end**, exactly preserving the detection-history distribution, so all pre-measurement
errors can be propagated past the (now-deferred) measurements.

### 3. Composing the propagated errors — BCH
After propagation the total circuit error is a product
`E_c = E'_k E'_{k−1} ⋯ E'_1 = exp(G_c)`, where `E'_j = U_k⋯U_{j+1} E_j U_{j+1}^{-1}⋯U_k^{-1}` is layer `j`'s
error pushed to the end. Composing exactly is intractable, so `G_c` is approximated by the **Baker–
Campbell–Hausdorff** expansion: `G_c ≈ Σ_i G'_i + Σ_i B_i`, where `G'_i` are the propagated layer
generators and `B_i` are the BCH commutator corrections. **If layers are EEG-sparse the BCH result stays
sparse** to polynomial order — the necessary tractability condition. The BCH truncation at order `j`
carries error `O(ε^{j+1})`.

### 4. Detector error models, DEM event classes (the core mapping)
A **detector** `P` is a Pauli observable with definite ideal eigenvalue, `⟨ψ|P|ψ⟩ = ±1` (normalised to
`+1`); a **detection history** is the bit-string of detector outcomes; a **DEM** is a set of independent
**events** `D_i ⊆ 𝔻` (subsets of detectors that flip together) each with a Bernoulli probability `p_i`. For
a **Pauli** error `Q`, the event it triggers is `Δ(Q) = { P ∈ 𝔻 : [P, Q] ≠ 0 }` (the detectors that
anticommute with it). The paper extends this to **non-Pauli** generators by partitioning `G_c` into **DEM
event classes**: `𝔾_D` is the maximal set of EEGs all of whose Pauli indices satisfy `Δ(·) = D` for a fixed
detector-set `D`, giving `G_c = G_1 + G_2 + ⋯ + G_k` with `G_i` collecting all EEGs of event class `D_i`.

**Theorem 1 (App. A.4, via Lemmas 3–4).** If a generator `G` consists *entirely* of EEGs from a single DEM
event class `D`, then `E_D = exp(G)` is **perfectly** modelled by a single-event DEM with
`p_D = ½(1 − Tr(P · E_D[|ψ⟩⟨ψ|]))` for any `P ∈ D`. The proofs evaluate `β(ψ,G,P) ≡ Tr(P G[|ψ⟩⟨ψ|])` for
each EEG type and show each flips detectors in exactly one event class (or none).

### 5. Factorising into single-event channels — Zassenhaus
With `G_c = Σ_i G_i` partitioned by event class, the **Zassenhaus** formula factorises the exponential into
a product of single-event channels plus correction terms:
`E_c ≈ exp(Σ_{g∈𝔾_1} ε_g g) · exp(Σ_{g∈𝔾_2} ε_g g) ⋯ · ∏_{i≥2} W_i`, where the `W_i` are Zassenhaus
commutator terms (e.g. `W_2 = exp(½ Σ_{g1∈G1,g2∈G2}[g2,g1] + …)`). **All simulations use first order
(`j=1`)**, dropping `W_2` and higher; the truncation error is `O(ε^{3/2})` and, combined with the
second-order BCH terms, yields the empirical detection-statistics error scaling `TVD ∝ ε_gen^{1.5}`.

### 6. Computing event probabilities
Each single-event channel's rate comes from the trace formula. **For S-only event classes it is exact:**
`p_i = ½(1 − exp(Σ_{S_j∈G_i} 2 ε_j))` (App. A.5). For mixed `S/C/A` a low-order Taylor expansion of
`exp(Σ ε_g g)` is used. **Coherent (`H`) errors contribute only at `O(ε²)`**, through quadratic
cross-terms, e.g. `p ≈ −½ Σ_{Q,Q'} b_{P,Q,Q'} s_{Q'} s_Q^T ε_{h_Q} ε_{h_{Q'}}` — i.e. coherent errors
*do* flip detectors, but quadratically in the coherent rate (the source of the `O(ε_h^3)` TVD).

### 7. Positivity, higher orders, and the amplitude-damping obstruction
**Theorem 6 (App. B.1)** guarantees no negative leading-order rates for CPTP models (so the leading-order
DEM is a legitimate sampler). **Theorem 2 (App. C)** characterises which DEM events appear at order `k`:
all symmetric differences of ≤`k` leading-order events; each must be decomposed iteratively (cost grows
with the number of compositions). **Beyond leading order, correlated non-Pauli errors — amplitude damping
being the worked example (App. B.2) — produce *anticorrelated* detection events that require *negative* DEM
event probabilities**, which a standard stochastic DEM cannot sample without allowing negative rates.

### 8. Sensitivity analysis (Methods §4.5)
To relate physical parameters `θ` to observables, detector expectations are written as a quadratic form
`⟨P⟩ ≈ 1 + θᵀ M_P θ` with a **sensitivity matrix** `M_P` (truncation error `O(ε^3)`). For cultivation,
explicit `M_P` matrices show which coherent parameters most strongly drive the logical observable and the
postselection (discard) rate — the mechanism behind the cultivation result.

### Cost / complexity [paper]
The paper gives **no closed-form scaling in code distance `d` or qubit count `n`**, but the algorithm is
`poly(n)` provided the generator is EEG-sparse: Clifford propagation is `poly(n)` per Pauli; BCH/Zassenhaus
to order `j` produce `O(j·s)` terms in the sparsity `s`; partitioning by event class is an `O(s log s)`
sort; the expanded (deferred-measurement) circuit adds `O(n)` virtual qubits. Each event-rate trace is
exact for `S`-only and a low-order Taylor expansion otherwise. **Approximation error:** BCH order-`j` and
Zassenhaus order-`j` each `O(ε^{j+1})`; the empirically reported detection-statistics error is
`TVD ∝ ε_gen^{1.5} = O(ε_h^3)` with `ε_gen = Σ_{P∈𝔾_H} ε_{h_P}^2`. **Validity window:** "sufficiently
small" rates, in practice `ε_gen < O(10^{-2})` (gate infidelities `≲ 10^{-3}`); accuracy degrades beyond.

---

## Key results, figures and tables [paper]

- **Figure 1 — "Efficient prediction of QEC circuits with non-Pauli errors"** (Results §2.2). Validation on
  **2 rounds of `d=3` rotated surface-code syndrome extraction** with sparse coherent error models, against
  **exact statevector** ground truth. Plots TVD between predicted and true detection-history distributions
  for the coherent-error DEM vs a **Pauli-twirled** DEM, and the scaling of TVD with error rate. **Headline:
  the coherent DEM's TVD is 1–2 orders of magnitude (≈100×) smaller** than Pauli-twirled; dominant
  detection histories predicted to **~1% relative precision** (many to 0.1%); **error scales `ε_gen^{1.5}`**.
- **Figure 2 — "Surface code logical performance with coherent and Pauli stochastic error"** (Results §2.3),
  `d = 3, 5, 7`, **MWPM** decoder. (a) Threshold CNOT-infidelity spread **> 0.002 across 10 random sparse
  CPTP models** (lowest ≈0.006). (b) At **fixed generator infidelity**, a **75%-coherent** model has
  threshold ≈ **0.006** vs ≈ **0.012** for the stochastic equivalent — a **~2× shift**. (c) Hardware-tailored
  DEM weighting helps the decoder slightly above threshold (`d=3`) but gives **no significant logical-error
  improvement sub-threshold** at high distance.
- **Figure 3 — "Scaling of Gross code logical error probability with coherent error"** (Results §2.3),
  **Gross / bivariate-bicycle `[[144,12,12]]`**, 2 rounds, **Beam decoder (belief-propagation-based)**, with
  coherent idle `H_X` and coherent CNOT `H_{XX}` parameters. **Logical error is minimised at a *nonzero*
  `H_{XX}` ≈ −0.013** (coherent cancellation), and **Pauli-twirled models over-estimate the logical error
  rate by up to 24%** in that regime — qualitatively impossible for a Pauli model.
- **Figure 4 — "Magic State Cultivation with Coherent Error"** (Results §2.4), `d=3` color code, SS-state
  injection (proxy for T gates) + double logical-H check. (a) Raising coherent contribution **0%→35% of
  Z-type CZ error** drives discard probability down and **logical-error probability up ~10×**. (b)
  Sensitivity matrix: the logical observable is **~15% more sensitive to coherent `Z⊗Z` than stochastic**,
  and **~28% more sensitive to coherent `I⊗Z`**; postselection is ~4.8% more sensitive to coherent `Z⊗Z`,
  but *under*-sensitive (≈14%/25%) to coherent `I⊗Z`/`Z⊗I` (a partly-counteracting, subdominant effect).
  CZ infidelity fixed at **0.00165**. *(The 15%/28%/4.8%/14%/25% figures are the HTML summariser's read of
  the sensitivity-matrix panel, not a pixel-extracted plot — treat as approximate.)*
- **Codes / decoders studied.** Rotated surface code (`d=3` validation; `d=3,5,7` thresholds, MWPM);
  **Gross `[[144,12,12]]`** (Beam/BP decoder); `d=3` color code (cultivation, no decoder — observable
  statistics); **Steane `[[7,1,3]]`** as an additional general-CPTP example in App. D.2. Pauli-twirled
  baselines are built with the standard Stim DEM pipeline (App. D.3).
- **Abstract-level headline numbers.** "coherent error can shift fault-tolerance thresholds, increase the
  space-time cost of magic state cultivation, and can increase logical error rates **by an order of
  magnitude** compared to equivalent stochastic errors." *(An "≈8×" figure appeared in one WebFetch
  paraphrase; the text I could verify states "order of magnitude" / ~10× for cultivation — prefer the
  order-of-magnitude framing.)*

---

## USEFUL FOR OUR PROJECT [twin]

**Direct relevance: this is a candidate scalable engine for the non-Pauli SIM-ONLY teacher.** Our program
(memory: *decoder-gate-and-frontier*, *coherence-not-identifiable-syndrome-only*) needs a teacher that emits
realistic-noise surface-code **syndrome** data whose non-Pauli structure is **decoding headroom above Pauli
decoders**, and whose simulation **scales beyond the ~15-qubit density-matrix ceiling** of
`forward/exact`. This paper supplies exactly such an engine for the *coherent/correlated* slice — and,
importantly, draws the precise line where it stops, which maps onto our axis split.

1. **The EEG→DEM construction is the scalable non-Pauli teacher for the *coherent/correlated* axis.**
   For coherent (`H`) + correlated (`C/A`) + stochastic (`S`) errors, the method produces a **standard
   Stim-compatible DEM** whose event rates are analytic in the physical parameters, in `poly(n)`, with a
   **certified error bound `TVD ∝ ε_gen^{1.5} = O(ε_h^3)`** (Fig. 1) inside `ε_gen < ~10^{-2}`. This is
   exactly the "scalable non-Pauli simulation with bounded error" our brief calls for. **Concrete adoption:**
   use it to generate teacher detection-history / syndrome streams at `d=5,7` under coherent CNOT/CZ
   over-rotation, then train/score our decoder and measure `%ΔLER` of a coherence-aware decoder vs the
   Pauli-DEM baseline — the surface-code analogue of our `do()`/headroom loop. The **DEM-construction code
   is shipped in `pyGSTi`** [paper] (simulation code promised in "PRAQTICE", unreleased at submission), so
   the engine is partly available off-the-shelf rather than a from-scratch build.

2. **It cleanly separates "what we can already simulate scalably" from "what still needs a multi-level
   sim."** The paper's hard boundary is **CPTP-on-the-computational-subspace**, and it states **leakage is
   explicitly out of framework** and **amplitude damping needs negative DEM rates** (App. B.2,
   Discussion). This is decisive for our axis planning:
   - **Coherent over-rotation / Pauli-correlated crosstalk → use THIS method** (scalable DEM, bounded error).
   - **T1/T2 amplitude-damping → this method is only a *leading-order* DEM and breaks at the
     anticorrelation order** — consistent with our note that T1/T2 has canonical Kraus channels but its
     *detection-level* signature includes anticorrelations a Pauli/leading-order DEM misses. The
     amplitude-damping anticorrelation (App. B.2) is *itself* a concrete piece of "non-Pauli signal =
     decoding headroom": a coherence/relaxation-aware teacher exposes anticorrelated detector events that
     no Pauli DEM (and no Pauli-twirled decoder) can represent.
   - **Leakage `|1>→|2>` + seepage → NOT covered**; the paper confirms (by exclusion) our standing
     conclusion that **true leakage needs a multi-level simulator** outside the EEG/DEM picture. So this
     paper is the teacher for the coherent/correlated rung, **not** the leakage rung.

3. **The error-bounding mechanism we can reuse, stated precisely.** The bound is *not* a generic
   Trotter/Lindblad bound — it comes from (i) the **EEG-sparsity + perturbative hierarchy** (`H` at `O(ε)`,
   `S/C/A` at `O(ε²)`), (ii) **first-order BCH** composition (`O(ε²)` correction), and (iii)
   **first-order Zassenhaus** factorisation into single-event channels (`O(ε^{3/2})`), giving the net
   detection-statistics error `O(ε_h^3)`. **Theorem 6** (no negative leading-order rates for CPTP) is the
   guarantee the teacher DEM is a *valid sampler*; **Theorem 2** is the recipe for systematically going to
   higher order if a teacher needs tighter fidelity. For us this is a ready-made, citable
   **"bounded-error non-Pauli simulation"** recipe with an explicit validity window (`gate infidelity
   ≲ 10^{-3}`), and a built-in tripwire: if a coherent rate is too large, the bound degrades and negative
   rates appear — a clean go/no-go on whether the perturbative teacher is trustworthy at a given noise level.

4. **It validates our central program thesis against exact ground truth.** Fig. 1's **~100× TVD advantage
   over Pauli-twirling** and Fig. 3's **24% Pauli-twirl LER misestimate** are independent, exact-statevector-
   checked evidence that **Pauli-twirled (moment-matched) models are not a sufficient statistic for
   detection statistics or LER** — i.e. there is genuine non-Pauli headroom in the *syndrome distribution*,
   not just the logical channel. This is the surface-code, circuit-level confirmation of our
   *coherence-not-identifiable-syndrome-only* finding's flip side: coherence *is* present in detection
   statistics; whether it is *learnable from binary syndromes alone* is our separate (harder) question, but
   the teacher can now *inject* it controllably and at scale.

5. **Sensitivity matrices `⟨P⟩ ≈ 1 + θᵀ M_P θ` are a recover/identifiability tool.** The Methods §4.5
   construction gives, per detector/observable, an explicit **quadratic map from physical noise parameters
   to expectation values**. For our `recover`/`understand` capabilities this is a direct
   **Fisher-information-style identifiability object**: `M_P` tells us which coherent parameters a given
   detector set is sensitive to (and which it is blind to), informing context/probe-richness design exactly
   as our `audit/gating` does. *(Use as a design heuristic — class (c) — not a premise.)*

6. **Baseline/comparison hygiene.** This paper's **Pauli-twirled-DEM** construction is precisely the
   "weak/standard Pauli baseline" our *decoder-gate-and-frontier* memo warns is too easy to beat; its
   **noise-adapted (hardware-tailored) DEM decoder** result is sobering — the decoder gain is **modest
   sub-threshold** even with the *correct* coherent DEM. **[twin]** This is independent corroboration that
   beating a Pauli baseline is necessary but not sufficient; the contribution bar remains the shipped
   frontier, and the coherent-DEM headroom is largest **near/above threshold and at small distance**, not
   deep sub-threshold — i.e. our coherent-teacher experiments should be sited where the signal lives.

---

## What does NOT apply / limitations [paper + twin]

- **[paper] No leakage / seepage / `|2>`.** Errors are CPTP on the qubit subspace; **leakage is explicitly
  excluded** ("Errors outside of our method's framework, such as leakage errors, can also cause
  anticorrelations, and are often highly detrimental to QEC"). **[twin]** Our leakage rung (`|1>→|2>` +
  seepage) **cannot** use this engine — it still requires a scalable multi-level simulator; this paper does
  not solve that and in fact marks it as out of scope.
- **[paper] Amplitude damping ⇒ negative DEM rates beyond leading order (App. B.2).** Correlated/relaxation
  errors create **anticorrelated detection events** the standard stochastic DEM cannot represent without
  permitting **negative event probabilities**; the paper's only "workaround" is to allow negative rates
  (breaking the clean sampler interpretation), or to go to higher composite-event order at extra cost.
  **[twin]** For T1/T2 teachers this means the DEM is a *leading-order approximation*; the genuinely
  hard-to-fake part of the relaxation signal is precisely the anticorrelation order — useful as *headroom*,
  but the teacher must either accept the leading-order truncation or escalate beyond DEMs.
- **[paper] Small-rate only.** Valid for `ε_gen ≲ 10^{-2}` (gate infidelity `≲ 10^{-3}`); accuracy degrades
  as `O(ε_h^3)` grows and the BCH/Zassenhaus truncations break. **[twin]** Real-hardware regimes near
  threshold can exceed this; a teacher run must check it sits inside the validity window (the paper's own
  tripwire: emergence of negative leading-order rates / large `ε_gen`).
- **[paper] Clifford circuits + stabilizer prep + computational-basis measurement only** (plus MCMs via the
  deferred-measurement expansion). **Non-Clifford gates** are handled "at the expense of increased
  computational cost"; **active-feedback** FTQC primitives are **future work**.
- **[paper] Decoder gains are modest sub-threshold.** Even the *correct* coherent DEM gives no significant
  logical-error improvement at high distance / sub-threshold (Fig. 2c). **[twin]** Tempers any claim that a
  coherence-aware decoder trained on this teacher yields large `%ΔLER` deep sub-threshold; the win is
  near-threshold / small-`d` / high-postselection settings (matching the cultivation result).
- **[paper] Validation is small-scale.** Exact-statevector ground truth only reaches `d=3`, 2 rounds; larger
  claims rest on the method's internal consistency and the bound, not direct exact comparison.
- **[twin] No identifiability/learnability claim.** The paper *injects and forward-simulates* known coherent
  noise; it does **not** address recovering coherent parameters from binary syndrome data — our
  *coherence-not-identifiable-syndrome-only* caveat stands. This is a **teacher/forward** tool, not a
  learner.

## How to use / trust + open questions [twin]
- **Trust:** high as a **bounded-error, scalable forward teacher for coherent + Pauli-correlated +
  stochastic surface-code noise**; carry the hard caveats (no leakage; amplitude-damping only to
  leading order; `gate infidelity ≲ 10^{-3}`). `pyGSTi` ships the DEM construction.
- **Adopt for us:** (i) stand up the EEG→DEM pipeline (or wrap `pyGSTi`) as the **coherent-axis teacher**;
  emit `d=5,7` detection histories under coherent CNOT/CZ over-rotation + correlated crosstalk; (ii)
  measure `%ΔLER` of a coherence-aware decoder vs the Pauli-DEM baseline, sited **near threshold / small-`d`**
  where Fig. 2c says the signal survives; (iii) reuse the **`ε_gen^{1.5}` bound + Theorem 6 positivity**
  as the teacher's certified-error statement; (iv) **keep leakage on the separate multi-level-sim rung** —
  this engine confirms, by exclusion, that leakage is not reducible to a DEM.
- **Open questions:** is the coherent detection-statistics headroom (Fig. 1's ~100×, Fig. 3's 24%)
  *learnable from binary syndromes alone* at `d=5,7`, or only injectable? Where exactly does the
  leading-order DEM's amplitude-damping anticorrelation gap become the dominant missing signal for a T1/T2
  teacher? Can the sensitivity matrices `M_P` quantify the *information* a syndrome set carries about
  coherent vs stochastic parameters (our identifiability axis)?
