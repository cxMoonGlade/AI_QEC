# Full-text review — Behrends & Béri, "The surface code beyond Pauli channels: Logical noise coherence, information-theoretic measures, and errorfield-double phenomenology" (arXiv:2412.21055 / PRX Quantum 6, 040350 (2025))

> **Provenance (2026-07-13 re-audit): FULL-TEXT PDF read (精读).** Refetched the pinned
> `arXiv:2412.21055v3` PDF from `https://arxiv.org/pdf/2412.21055v3`; 21 pages,
> SHA-256 `3ead96c98a6055b2e9ad3109932444f4bacd1bc088c6f89f90eff5dbea3207a9`.
> PyMuPDF extraction was used only for navigation. PDF pp. 1–3, 7, 9, and 15 were rendered and
> visually inspected for Eqs. (1)–(6), Eq. (29), Eq. (59), Fig. 1(d), the Sec. VI statement,
> and the field-theory interpretation. The full 21-page text, including appendices and
> references, was traversed. The earlier 2026-07-06 ar5iv/HTML read remains a secondary
> navigation record, not the formula/figure ground truth. Figure curves were not digitized.
> **Correction to the acquisition brief:** the
> venue is **PRX Quantum 6, 040350 (2025)** (DOI 10.1103/psf5-b6j2), NOT PRL; and the paper's
> beyond-Pauli scope is the general single-qubit **X-error channel** (coherent + incoherent
> bit-flip), NOT amplitude damping / general non-unital noise — recorded honestly below.
> Epistemic tags: **[paper]** = stated/derived in the paper; **[ours]** = our application /
> inference for the project (not the paper's claim).

## Metadata [paper]
- **Authors / affiliation.** Jan Behrends, Benjamin Béri — T.C.M. Group, Cavendish
  Laboratory, University of Cambridge.
- **Venue / status.** arXiv:2412.21055; v1 30 Dec 2024, v2 24 Apr 2025, v3 23 Oct 2025.
  **Published: PRX Quantum 6, 040350 (2025)**, DOI 10.1103/psf5-b6j2. Categories: quant-ph;
  cond-mat.stat-mech.
- **Type.** Theory + large-scale numerics: a **statistical-mechanics mapping** of the
  surface-code decoding problem under a general single-qubit **X-error channel with a
  coherent component**, expressed as a **(1+1)D hybrid transfer-matrix / quantum circuit**
  simulated with **matrix product states (MPS)** for approximate syndrome sampling, plus a
  **phenomenological field theory** for the coherent limit. Focus: how the **coherence of the
  logical noise channel** scales with code distance, and what **information-theoretic measures**
  (coherent information, quantum relative entropy) can detect.
- **Lineage.** The stat-mech / RBIM mapping of surface-code decoding (Dennis–Kitaev–Landahl–
  Preskill) extended to coherent errors; the coherent-limit "errorfield double" / logarithmic-
  entanglement phenomenology connects to prior coherent-error stat-mech work (Venn–Vala–Béri,
  etc.). It is the *coherent-error* stat-mech counterpart to the Pauli-only RBIM decoding picture.

## Selection + coverage [ours]

This source was re-audited for one narrow claim: whether increasing code distance `d` makes a
project-relevant "long-range entanglement tail" exponentially negligible. It directly addresses the
scaling of a **syndrome-conditioned logical-channel coherence** under a local product X-error channel.
It does **not** address physical qutrit leakage, a circuit-level multi-round record, or PEPS truncation.

| assigned row | exact source location | source-local status |
|---|---|---|
| local physical model | PDF p. 1, Eq. (1) | `closed`: independent single-qubit X channels |
| logical observable | PDF p. 3, Eqs. (2)–(4), definition of `γ_L^(s)` | `closed` |
| scaling with code distance | PDF p. 2, Fig. 1(d); p. 9, Sec. VI; p. 15, Sec. VII.D | `closed`, numerical + phenomenological only |
| physical long-range entanglement | no such object in the paper | `missing` |
| PEPS truncation → full-record / rare-LER error | no PEPS, record-distance, or truncation theorem | `missing` |

## Executive summary [paper]
The surface code is analysed under the **most general single-qubit X-error channel** [Eq. (1)],
`E_j[ρ] = (1−p_j) ρ + p_j X_j ρ X_j + i γ_j √(p_j(1−p_j)) [X_j, ρ]`, which interpolates between a
purely **incoherent** bit-flip (`γ_j = 0`) and a **fully coherent** rotation
`U_j = exp(±i ϑ_j X_j)` (`γ_j = ±1`). This is a **beyond-Pauli** channel: for `γ_j ≠ 0` it has a
commutator (Hamiltonian/coherent) piece that a Pauli (stochastic) channel cannot represent. The
authors' central scaling claim is that **for any nonzero incoherent component, the coherence of the
*logical* noise channel is exponentially suppressed in code distance `d`**. The direct numerical
plot contains two near-coherent subthreshold points; Sec. VII supplies a qualitative phenomenological
field-theory account. This is not a numbered theorem, a fitted all-parameter law, or a rigorous
`A exp(−d/ξ)` bound. Consequently, information-theoretic performance measures (coherent information `I_C`,
quantum relative entropy) **require that suppression to detect the Pauli-recovery threshold**: they
work at large `d` whenever there is any incoherent component, need **increasingly large distances
as coherence increases**, and **break down entirely for fully coherent errors** (where `I_C` is
constant, `= ln 2`, independent of `p`, and cannot locate a threshold). The exotic power-law /
logarithmic-entanglement above-threshold phase of the *purely coherent* code is shown (via the
field theory, Eq. 46) to be **fragile — unstable to any small incoherent perturbation**, giving
way to a conventional area-law / Pauli-recoverable phase. Methodologically the paper supplies a
**stat-mech mapping + MPS transfer-matrix syndrome sampler** that scales these non-Pauli
simulations (maximum-likelihood thresholds) well beyond the small sizes previous exact methods reach.

## Key findings [paper]
- **F1 — The channel is genuinely beyond-Pauli (coherent bit-flip).** Eq. 1 is
  "the most general single-qubit channel one can build using `X_j`" [Sec. I]; CPTP for
  `γ_j² ≤ 1`; the `i γ_j √(p_j(1−p_j)) [X_j, ρ]` term is the coherent (commutator) piece a Pauli
  channel omits. Scope: **X-only** — this is coherent/incoherent **bit-flip**, not amplitude
  damping or a general non-unital channel.
- **F2 — Logical noise becomes incoherent with distance (the load-bearing result).** The authors
  state that for any `γ < 1` the mean logical coherence
  `⟨|γ_L^(s)|⟩_s = ⟨| Z_{10,s} / √(Z_{00,s} Z_{11,s}) |⟩_s` **decreases exponentially to zero
  with `d`** [Fig. 1(d), PDF p. 2; Sec. VI, p. 9]. Fig. 1(d) directly plots only
  `(p,γ)=(0.1,0.995)` and `(0.105,0.99)`, both subthreshold. Sec. VI says this held for every
  `γ<1` they examined; Sec. VII.D gives a qualitative kink-correlator explanation. **Evidence
  strength: numerical + phenomenological, not theorem-grade.**
- **F3 — Effective logical channel lies in the `{I,X_L}` operator span after syndrome projection.** After
  syndrome measurement and projection, the logical-space channel is
  `D_s[ρ] = Z_{00,s} ρ + Z_{11,s} X_L ρ X_L + Z_{01,s} ρ X_L + Z_{10,s} X_L ρ` [Eq. 3], with
  `Re Z_{01,s} = 0` for the lattice studied (even-weight stabilizers, odd-weight logicals). The
  off-diagonal terms are precisely the non-Pauli coherence; this becomes a stochastic Pauli channel
  only when they vanish. In the
  **fully coherent** limit the effective channel `D_s^(coh)[ρ] = e^{i X_L ϑ_s} ρ e^{−i X_L ϑ_s}`
  acts **unitarily** on `ρ` [Sec. III.2] — coherence is *preserved* only at the singular `γ = 1`
  point; away from it, F2 drives it to zero.
- **F4 — Recoverable ≠ Pauli-string correctable.** For coherent errors `I_C^(coh)|_even = ln 2`,
  which "indicates perfect recoverability" because the unitary logical rotation is in-principle
  correctable — "However, this does not necessarily imply that the channel is Pauli-string
  correctable" [Sec. III.2]. The standard (MWPM / stat-mech) threshold is a **Pauli-string**
  recoverability criterion, distinct from unitary recoverability.
- **F5 — Info-theoretic measures need the incoherence to see the threshold.** "For coherent
  errors, however, measures like the coherent information cannot detect a conventional QEC error
  threshold" [Sec. VI]; near the coherent limit "`γ ≳ 0.95` … both coherent information and
  quantum relative entropy suffer from finite-size effects and are thus unsuited to determine the
  threshold" [Sec. VI], but "can … detect the threshold for large system sizes, provided the error
  has nonzero incoherent component."
- **F6 — Thresholds barely move until the coherent limit.** Maximum-likelihood `p_th ≈ 0.109`
  is "largely independent of the coherent contribution `γ` until it is close to the coherent limit
  `γ = 1`" [Fig. 1(a)–(b); Fig. 3; Sec. VI]: `p_th = 0.109(1)` at `γ = 0.05` and `0.50`, `0.108(2)` at `0.95`,
  rising to `0.119(2)` at `0.99` and `0.127(3)` at `0.995`. **MWPM** thresholds instead *decrease*
  toward coherence: `0.102(3)` (`γ=0.05`) → `0.086(3)` (`γ=0.995`).
- **F7 — Coherent above-threshold phase is fragile.** The logarithmic-entanglement /
  power-law phase of the purely coherent code is "a special property of the coherent limit,
  unstable to a small incoherent noise component" [Sec. I]; the field theory (Eq. 46) shows the
  logarithmic entanglement "gives way to an area law (from the gapped phase) upon introducing
  incoherent noise even as perturbation" [Sec. VII.2].
- **F8 — Method: stat-mech + MPS transfer matrix (the scalability lever).** Decoding is mapped to
  a two-species random-bond Ising partition function [Eqs. 18/24], written as a transfer matrix
  `Z = ⟨φ_0| M |φ_0⟩` [Eq. 25] = a (1+1)D hybrid quantum circuit; the evolved 1D state obeys an
  **area law**, so it is simulated efficiently with **MPS** [Sec. I], enabling an iterative
  MPS syndrome sampler [Sec. V.2] and large-scale non-Pauli threshold estimation away from the
  incoherent and fully coherent limits. This is the entanglement of an auxiliary `(1+1)D`
  transfer-matrix state, not the physical 2D QEC PEPS.

## Relevance to project [ours]

1. **Bounded adjacent evidence, not a project closure theorem.** The paper supports one restricted
   statement: after one local X-error product channel, ideal stabilizer projection, and a
   syndrome-dependent Pauli recovery, the authors' `γ_L` decreases with `d` when an incoherent
   component is present. It is useful context for logical-channel Pauli-fication, but it cannot be
   promoted into a statement about a real circuit-level passive record.

2. **The record bridge remains open.** `γ_L` is an off-diagonal parameter of the conditioned
   logical channel `D_s/P(s)`. The paper does not prove that the multi-round distribution
   `P(detectors, observable flips)` is Pauli, that coherent parameters are unidentifiable from it,
   or that a leakage/coherent contribution is record-null. The prior note's stronger
   "passive record is essentially classical Pauli" inference is therefore retracted.

3. **The truncation/long-range bridge is absent.** The auxiliary transfer-MPS area law does not say
   that physical 2D PEPS entanglement vanishes with `d`; an area law bounds scaling across a cut, not
   the operational error caused by truncating it. The paper contains no discarded-weight bound,
   PEPS/FET/WTG analysis, full-record TV/KL guarantee, or rare-LER error bound. It cannot authorize
   deleting the d5/d7 coherent leakage tail. For that project use the evidence row is
   `REOPEN_EVIDENCE`.

4. **[paper→ours] "Recoverable ≠ Pauli-string-correctable" is a useful precision (F4).** The
   coherent logical rotation is unitarily correctable in principle even where the standard
   (Pauli-string) threshold criterion sees a failure. **[ours]** Guards against a sloppy
   equivalence in our own writing: "the record is Pauli" and "coherence is uncorrectable" are
   different statements. The project's passive-record closure asks a separate question that this
   logical-channel paper does not answer; ultimate correctability with a coherence-aware recovery
   is different again.

5. **[paper→ours] Method reuse / baseline.** The stat-mech→MPS transfer-matrix syndrome sampler
   (F8) is an independent, area-law-justified route to large-scale non-Pauli (coherent-X)
   surface-code syndrome statistics and maximum-likelihood thresholds — a candidate
   approximate cross-check/baseline for a matching coherent-X object, implemented independently
   from our DM/carrier engines. *(Use as method/baseline, class (c); the MPS is an approximation
   with its own truncation and is not an exact oracle or independent ground truth.)*

## Decisive source locations [paper]
Rechecked against the pinned v3 PDF; short excerpts below are navigational, while the PDF is the
evidence object.

- **Abstract (verbatim, arXiv abstract page):** "We consider the surface code under errors
  featuring both coherent and incoherent components and study the coherence of the corresponding
  logical noise channel and how this impacts information-theoretic measures of code performance,
  namely coherent information and quantum relative entropy. Using numerical simulations and
  developing a phenomenological field theory, focusing on the most general single-qubit X-error
  channel, we show that, for any nonzero incoherent noise component, the coherence of the logical
  noise is exponentially suppressed with the code distance. We also find that the
  information-theoretic measures require this suppression to detect optimal thresholds for Pauli
  recovery; for this they thus require increasingly large distances for increasing error coherence
  and ultimately break down for fully coherent errors. To obtain our results, we develop a
  statistical mechanics mapping and a corresponding matrix-product-state algorithm for approximate
  syndrome sampling. These methods enable the large scale simulation of these non-Pauli errors,
  including their maximum-likelihood thresholds, away from the limits captured by previous
  approaches."
- **[Sec. VI]** "The logical noise thus becomes increasingly incoherent with `d`."
- **[Sec. VI, PDF p. 9; Fig. 1(d), p. 2]** The text states that `γ_L` decreases exponentially to
  zero with `d` for every `γ<1` considered; the figure directly shows two near-coherent points.
- **[Sec. VI]** "For coherent errors, however, measures like the coherent information cannot detect
  a conventional QEC error threshold."
- **[Sec. VI]** "close to the coherent limit, both coherent information and quantum relative
  entropy suffer from finite-size effects" (full: "For `γ ≳ 0.95` close to the coherent limit,
  however, both coherent information and quantum relative entropy suffer from finite-size effects").
- **[Sec. III.2]** "Since the effective error channel `D_s^(coh)[ρ] = e^{i X_L ϑ_s} ρ e^{−i X_L ϑ_s}`
  acts unitarily on `ρ`."
- **[Sec. III.2]** "However, this does not necessarily imply that the channel is Pauli-string
  correctable."
- **[Sec. I]** "The entanglement entropy of a 1D state evolved by the quantum circuit exhibits an
  area law, and we can thus efficiently simulate the evolution numerically using matrix product
  states."
- **[Sec. I]** "this above-threshold behavior is however a special property of the coherent limit,
  unstable to a small incoherent noise component."
- **[Sec. VII.2]** the logarithmic entanglement "gives way to an area law (from the gapped phase)
  upon introducing incoherent noise even as perturbation."

## Equations recorded (visually checked on pinned v3 PDF) [paper]
- **Eq. 1 (general single-qubit X channel):**
  `E_j[ρ] = (1−p_j) ρ + p_j X_j ρ X_j + i γ_j √((1−p_j)p_j) [X_j, ρ]`.
- **Eq. 3 (effective logical channel after syndrome projection):**
  `D_s[ρ] = Z_{00,s} ρ + Z_{11,s} X_L ρ X_L + Z_{01,s} ρ X_L + Z_{10,s} X_L ρ`, with
  `Re Z_{01,s} = 0` for the studied lattice.
- **Logical coherence order parameter (Sec. VI):**
  `⟨|γ_L^(s)|⟩_s = ⟨| Z_{10,s} / √(Z_{00,s} Z_{11,s}) |⟩_s → 0` exponentially in `d` for `γ < 1`.
- **Coherent-limit coherent information (Eq. 16–17):** `I_C^(coh)|_even = ln 2` (constant in `p`).

## What does NOT apply / limitations [paper + ours]
- **[paper] Beyond-Pauli scope = coherent X (bit-flip) only.** No amplitude damping, no general
  non-unital channel, no leakage; the "beyond-Pauli" content is the unital coherent commutator term.
- **[paper] The unitary-logical-channel statement is the singular `γ = 1` limit.** Away from it, F2
  drives logical coherence to zero; the "coherence preserved" reading holds *only* at the coherent
  point and is finite-size-fragile there (F5/F7).
- **[paper] Thresholds are stat-mech / maximum-likelihood (and MWPM), on the X-error RBIM.** The
  ~`0.109` numbers are for this X-channel family and lattice; not directly a circuit-level
  (measurement-error, `d`-round) threshold.
- **[paper] Scaling evidence is not a rigorous uniform theorem.** There is no numbered theorem,
  fitted `ξ`, confidence band over `ξ`, or bound `γ_L(d)≤A exp(−d/ξ)` uniform over all `p,γ`.
  Fig. 1(d) directly plots two parameter pairs; the wider statement combines the authors' additional
  numerics with qualitative field-theory phenomenology.
- **[paper] No circuit-level repeated-round instrument.** Stabilizer measurement is ideal and the
  model is one product error channel followed by syndrome projection and Pauli recovery. There are no
  measurement errors, explicit ancillas, resets, RTN, spatial correlations, or leakage levels.
- **[ours] Not an identifiability/learnability or record-faithfulness result.** The paper
  characterises a conditioned logical channel and ensemble information measures. It neither recovers
  coherent parameters from binary syndromes nor bounds a full multi-time record.
- **[ours] Auxiliary area law is not physical-tail decay.** The MPS entanglement belongs to the
  transfer-matrix calculation. It cannot be substituted for a 2D PEPS truncation certificate.

## Project kill conditions [ours]

- If a downstream claim changes the observable from `γ_L` to full-record TV/KL or frozen-decoder
  `ΔLER` without a separate bridge, this paper cannot support that claim.
- If the physical model includes leakage, non-unital relaxation, correlated noise, circuit-level
  measurement faults, or repeated rounds, Eq. (1)'s source-local closure no longer applies.
- If "area law" is used to infer exponentially vanishing PEPS truncation error, the inference is
  unsupported and must be removed.

## Operation replay ledger [ours; source-checked]

| input | transformation | assumption | output | exact source location | replay status |
|---|---|---|---|---|---|
| product X-error channel `⊗_j E_j` | ideal syndrome projection + Pauli recovery `C_s` | surface-code geometry; for input-independent `P(s)`, even-weight stabilizers and odd-weight logical | conditioned logical channel `D_s/P(s)` | pp. 1, 3; Eqs. (1)–(4) | `matched` |
| coefficients `Z_{00,s},Z_{11,s},Z_{10,s}` | form `abs(γ_L^(s))=abs(Z_{10,s})/√(Z_{00,s}Z_{11,s})`, then syndrome average | sampled syndrome ensemble | logical-noise coherence `γ_L` | p. 3 after Eq. (4) | `matched` |
| near-coherent `γ<1` samples | MPS syndrome sampling and evaluation versus square-code distance `d=L=M` | approximate MPS sampling; 1,000–10,000 syndromes | approximately linear `ln γ_L` versus `d` for two plotted points | p. 2, Fig. 1(d); pp. 8–9, Sec. VI | `matched` |
| incoherent perturbation of coherent field theory | relevant `λ_2,λ_4` terms open gaps; kink-correlator ratio | phenomenological description of typical partition functions | qualitative exponential decay of typical `γ_L^(s)` | p. 15, Eq. (59) and following text | `matched`, qualitative |
| local/auxiliary TN diagnostic | infer full multi-round record or rare-LER error | no such bridge supplied | project record-faithfulness certificate | absent | `unsupported` |

## How to use / trust + open questions [ours]

- **Trust:** published paper; pinned v3 full text; PDF hash/page count captured; load-bearing formulas,
  figure identity, axes, and limitations visually checked. The logical-coherence claim is credible as
  published numerical + phenomenological evidence, not theorem-grade evidence.
- **Source-local outcome:** physical-model, logical-observable, and studied scaling rows are `closed`;
  physical long-range-entanglement and PEPS/full-record/rare-LER bridge rows are `missing`.
- **Project action:** `REPAIR` the overbroad propagation; retain the bounded result as adjacent
  evidence only. The project-wide literature closure still controls whether the missing bridge is a
  confirmed literature gap.
