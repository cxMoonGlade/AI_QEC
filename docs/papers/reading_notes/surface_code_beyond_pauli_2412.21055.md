# Full-text review — Behrends & Béri, "The surface code beyond Pauli channels: Logical noise coherence, information-theoretic measures, and errorfield-double phenomenology" (arXiv:2412.21055 / PRX Quantum 6, 040350 (2025))

> **Provenance (2026-07-06): HTML full-text read (ar5iv).** Built from the ar5iv HTML
> full text at `https://ar5iv.labs.arxiv.org/html/2412.21055` (abstract, Secs. I–VII,
> Eqs. 1/3/16–17/24/46, Figs. 1–3) and the arXiv abstract page
> `https://arxiv.org/abs/2412.21055` (metadata, journal-ref, verbatim abstract), fetched
> via WebFetch. Load-bearing sentences in "Decisive verbatim quotes" were re-fetched and
> confirmed against the ar5iv HTML (verbatim, character-level, section-tagged); the
> statistical-mechanics / field-theory equations are the summariser's LaTeX transcription
> of the stated content and are close technical transcriptions rather than pixel-verified
> — flagged where used. Figure curves are NOT pixel-extracted; figure-level numbers are the
> captions plus numbers stated in running text. **Correction to the acquisition brief:** the
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

## Executive summary [paper]
The surface code is analysed under the **most general single-qubit X-error channel** [Eq. 1],
`E_j[ρ] = (1−p_j) ρ + p_j X_j ρ X_j + i γ_j √(p(1−p)) [X_j, ρ]`, which interpolates between a
purely **incoherent** bit-flip (`γ_j = 0`) and a **fully coherent** rotation
`U_j = exp(±i ϑ_j X_j)` (`γ_j = ±1`). This is a **beyond-Pauli** channel: for `γ_j ≠ 0` it has a
commutator (Hamiltonian/coherent) piece that a Pauli (stochastic) channel cannot represent. The
central result is that **for any nonzero incoherent component, the coherence of the *logical*
noise channel is exponentially suppressed in the code distance `d`** — the logical channel that
survives syndrome extraction + recovery becomes increasingly **incoherent (effectively Pauli)**
as `d` grows. Consequently, information-theoretic performance measures (coherent information `I_C`,
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
  `γ_j² ≤ 1`; the `i γ_j √(p(1−p)) [X_j, ρ]` term is the coherent (commutator) piece a Pauli
  channel omits. Scope: **X-only** — this is coherent/incoherent **bit-flip**, not amplitude
  damping or a general non-unital channel.
- **F2 — Logical noise becomes incoherent with distance (the load-bearing result).** For any
  `γ < 1`, the mean logical coherence
  `⟨|γ_L^(s)|⟩_s = ⟨| Z_{10,s} / √(Z_{00,s} Z_{11,s}) |⟩_s` **decreases exponentially to zero
  with `d`** [Fig. 3(b)]; "The logical noise thus becomes increasingly incoherent with `d`"
  [Sec. VI]. So even nearly coherent physical noise (`γ = 0.995`) yields an **effectively Pauli
  logical channel** at large distance.
- **F3 — Effective logical channel is a Pauli/`X_L` channel after syndrome projection.** After
  syndrome measurement and projection, the logical-space channel is
  `D_s[ρ] = Z_{00,s} ρ + Z_{11,s} X_L ρ X_L + Z_{01,s} ρ X_L + Z_{10,s} X_L ρ` [Eq. 3], with
  `Re Z_{01,s} = 0` for the lattice studied (even-weight stabilizers, odd-weight logicals). In the
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
  `γ = 1`" [Fig. 1(d), Sec. VI]: `p_th = 0.109(1)` at `γ = 0.05` and `0.50`, `0.108(2)` at `0.95`,
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
  incoherent and fully coherent limits.

## Relevance to project [ours]

**This is a strong, independent, *published* (PRX Quantum) anchor for a "protocol-boundary"
closure argument: standard surface-code syndrome extraction drives the logical channel to an
effectively Pauli/stochastic form, so a passive syndrome record carries essentially classical
Pauli structure — the beyond-Pauli coherent piece is exponentially suppressed by the code, not
sitting in the record.** It reinforces (from a completely different method — stat-mech / MPS, not
error-generator DEMs like 2603.18457, and not our own machinery) the memory line that the *right*
observable is not the coherent structure of the passive syndrome record.

1. **[paper→ours] Direct support for the closure argument.** F2/F3 are the load-bearing facts:
   for any nonzero incoherent component the **logical** noise coherence
   `⟨|γ_L|⟩ → 0 exponentially in d`, and the post-syndrome effective channel is an `X_L` (Pauli)
   channel [Eq. 3]. **[ours]** This is a physics-grounded, distance-scaling reason a passive
   syndrome record of a real (coherent+incoherent) surface code looks classical-Pauli at usable
   `d`: the code itself Pauli-fies the logical noise. It complements the "syndrome extraction
   Pauli-twirls the gate noise" framing with a *decoding-side* statement — the surviving logical
   channel is incoherent — reached without invoking twirling as an assumption.

2. **[paper→ours] The coherent structure is NOT freely accessible from the passive record.** F5:
   the passive-ensemble information-theoretic measures **cannot detect the threshold for fully
   coherent errors** and need increasingly large `d` as coherence grows; the coherent piece is
   pushed to the singular `γ = 1` corner (F3) and is finite-size-fragile there (F7). **[ours]**
   Maps onto our standing conclusion (`lessons-leakage-and-coherence-observability`,
   `coherence-not-identifiable-syndrome-only`): coherent/beyond-Pauli structure is not a
   sufficient-statistic feature of the passive syndrome record — accessing it needs the coherent
   corner (`γ→1`) and/or extra non-syndrome probing, not more passive syndromes.

3. **[paper→ours] Honest scope boundary — X-only bit-flip, not the amplitude-damping/non-unital
   axis.** The brief motivated this acquisition partly by "non-unital (amplitude-damping)"
   structure; this paper's beyond-Pauli content is a **coherent X (bit-flip) channel**, unital,
   not amplitude damping. **[ours]** So it anchors the *coherent-error* half of the closure
   argument rigorously, but it does **not** speak to non-unital/relaxation anticorrelations — that
   axis is covered by 2603.18457 (App. B.2, amplitude damping ⇒ anticorrelated detectors ⇒ needs
   negative DEM rates) and by our leakage/relaxation notes. Cite the two together; do not let this
   paper carry a non-unital claim it does not make.

4. **[paper→ours] "Recoverable ≠ Pauli-string-correctable" is a useful precision (F4).** The
   coherent logical rotation is unitarily correctable in principle even where the standard
   (Pauli-string) threshold criterion sees a failure. **[ours]** Guards against a sloppy
   equivalence in our own writing: "the record is Pauli" and "coherence is uncorrectable" are
   different statements; the closure argument is about what the *passive syndrome record under
   standard extraction* carries, not about ultimate correctability with a coherence-aware recovery.

5. **[paper→ours] Method reuse / baseline.** The stat-mech→MPS transfer-matrix syndrome sampler
   (F8) is an independent, area-law-justified route to large-scale non-Pauli (coherent-X)
   surface-code syndrome statistics and maximum-likelihood thresholds — a candidate
   cross-check/baseline for any coherent-teacher record we generate, and an independent-oracle
   family distinct from our DM/carrier engines (relevant to the anti-circular / independent-GT
   discipline). *(Use as method/baseline, class (c); the MPS is an approximation with its own
   truncation, not an exact oracle.)*

## Decisive verbatim quotes [paper]
Re-fetched and confirmed against the ar5iv HTML `https://ar5iv.labs.arxiv.org/html/2412.21055`
(section tags as printed there); the abstract is from `arxiv.org/abs/2412.21055`.

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
- **[Sec. VI, Fig. 3(b)]** "`⟨|γ_L^(s)|⟩_s` decreases exponentially to zero with `d`, which holds
  for all `γ < 1`."
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

## Equations recorded (transcribed, not pixel-verified) [paper]
- **Eq. 1 (general single-qubit X channel):**
  `E_j[ρ] = (1−p_j) ρ + p_j X_j ρ X_j + i γ_j √((1−p)p) [X_j, ρ]`.
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
- **[ours] Not an identifiability/learnability result.** The paper characterises the *logical*
  channel and *ensemble* information measures; it does not claim to recover coherent parameters from
  binary syndromes, and its "closure" support is about what the record *carries*, consistent with —
  but not a proof of — our passive-record legitimacy line. Use it as an anchor for the
  protocol-boundary argument, not as a stand-alone identifiability theorem.
