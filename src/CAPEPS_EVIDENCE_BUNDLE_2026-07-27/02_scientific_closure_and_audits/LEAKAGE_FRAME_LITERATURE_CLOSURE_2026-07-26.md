# Leakage-conditioned frame literature closure

Date: 2026-07-26. Status: **CLOSED FOR DOCUMENTATION; EXACT FRAME IDENTIFIABILITY
REMAINS PROJECT INFERENCE**.

This packet answers the current d3 leakage-conditioned frame question without expanding the product
claim. Source statements live in the four current-schema reading notes named below. This file
contains source selection, operation replay, cross-source comparison, project application, and the
closure decision. Search hits, repository implementations, extracted text, and RAG/KG chunks are
discovery surfaces; none substitutes for the versioned PDFs and exact locators.

## Frozen claim

| field | frozen value |
|---|---|
| decision / consequence | Decide whether the residual left after dividing out the deterministic leakage-free transversal-echo sign is physical Record content, an observationally redundant relabeling, or a trajectory-conditioned term requiring a hidden leakage history. The consequence is the defensible semantics of the d3 analog detector/observable Record. |
| mechanism | Each non-terminal round applies a declared single-qutrit echo. Its computational block anticommutes with the supported logical Pauli, while its leaked level is inert. Leakage and return can therefore change which support sites experience the computational action. Separately, a leaked support site can reduce a stabilizer to an effective lower-weight check. |
| observable / Record object | The product object is the emitted temporal detector bits and logical-observable flip, including joint and temporal structure. Leakage population, exact trajectory labels, density-matrix blocks, and HMM posterior are not product fields. A raw parity outcome, a folded defect, a supercheck product, a time series, and a direct heralded leakage flag are different observables. |
| mechanism-to-observable bridge | Qutrit gate and CZ dynamics determine effective check operators; the measurement instrument generates raw outcomes; schedule-specific post-processing generates defects; the deterministic leakage-free frame sign is removed from the logical readout. The question is what remains after only that reference sign is removed. |
| favorable prediction | None. The packet must retain nulls and counterexamples: paralysis, one-half marginals, generic-phase supercheck corruption, non-unique leakage patterns, short-event misses, direct-measurement back-action, and lack of an exact frame theorem. |
| alternatives | Explicit leaked-block phase convention; effective gauge checks and their supercheck; physical echo; Pauli-frame correction; HMM inference; direct heralded leakage measurement; decoder-side located flag. These are not interchangeable. |
| possible no-go | A deterministic bit relabeling is invisible in an exactly uniform one-bit marginal. An exact trajectory-conditioned correction is unavailable if two hidden histories produce the same public Record but require different corrections. The first is elementary algebra and the second is a conditional identifiability statement; neither is promoted here to a sourced field-wide theorem. |
| implementation target | Documentation and retrieval only. No `src/**` change, HMM, new experiment, d5 claim, decoder promotion, or hardware-calibration claim is authorized. |

## Selected load-bearing sources

| source | fixed artifact | role | publication check |
|---|---|---|---|
| Ghosh et al., arXiv:1306.0925v2 | `docs/papers/1306.0925v2.pdf`, SHA-256 `d2b630d8cee32a4e1ab5302fda3e4f7cee15849577565dff9eb63a10dd10f076` | Original single-check phase-to-paralysis operation chain | Work later published as Phys. Rev. A 88, 062329, DOI `10.1103/PhysRevA.88.062329`; Crossref metadata checked 2026-07-26 and exposes no update relation. |
| Bultink et al., arXiv:1905.12731v1 | `docs/papers/1905.12731v1.pdf`, SHA-256 `b7f831dc66b329d583c892483160c937b773dec1cc2f52edf33b32e15d1b563d` | Physical data echo, raw parity pattern, temporal syndrome, HMM, and effective-check argument | Work later published under a reordered title in Science Advances 6, eaay3050, DOI `10.1126/sciadv.aay3050`; Crossref relation is empty and no correction/retraction notice was found in the checked DOI/PubMed surfaces. This is not an absolute absence claim. |
| Varbanov et al., arXiv:2002.07119v1 | `docs/papers/2002.07119v1.pdf`, SHA-256 `e5e3f4756bcedac10a4016aaac957af41a7a560501033a7f43a993a7b22abbe9` | Surface-17 effective checks, individual defects, superchecks, HMM emissions, and ancilla pi-pulse proposal | Work later published in npj Quantum Information 6, 102, DOI `10.1038/s41534-020-00330-w`; Crossmark was checked 2026-07-26 and displayed the document as current without a correction notice. The version of record contains numerical updates, so no value or locator from it is mixed into the v1 note. |
| Miyamura et al., arXiv:2607.17204v1 | `docs/papers/2607.17204v1.pdf`, SHA-256 `cb33dbc5eaddb400c0e04b63dfc9be199adfef2797e3133996b6aea32b0ed889` | Adjacent direct binary leakage measurement and its back-action boundary | Preprint submitted in July 2026; no journal version is claimed. |

The source-only notes are:

- `docs/papers/reading_notes/ghosh_leakage_paralysis_1306.0925v2.md`
- `docs/papers/reading_notes/bultink_repetitive_parity_leakage_1905.12731v1.md`
- `docs/papers/reading_notes/varbanov_leakage_detection_surface17_2002.07119.md`
- `docs/papers/reading_notes/miyamura_heralded_leakage_2607.17204v1.md`

All locators in those notes refer to the declared arXiv artifact, not a later version of record.

## Coverage ledger

| row | evidence and exact locator | status | project implication |
|---|---|---|---|
| M1 — action on computational and leaked sectors | Ghosh Eq. (2), p. 2 embeds `H` as `H_qubit direct-sum 1`; Varbanov Sec. I.A, p. 2 declares single-qubit gates identity on leakage and Appendix D Eqs. (D3)-(D5), p. 16 uses that convention; Bultink Fig. 1A, p. 2 shows a physical data `Rx(pi)` echo but does not specify its complete leaked-subspace action. | **closed for a declared leaked-inert convention; missing for X-to-Y equivalence and a device error bound** | Once the leaked entry is fixed to `+1`, a global phase chosen for the computational-block representative becomes a relative computational/leakage phase. The current `Y direct-sum 1` representative is a declared model choice, not a hardware-certified equivalence to `(-iY) direct-sum 1`; cross-sector coherence can distinguish them. |
| M2 — leakage paralysis and echo removal | Ghosh Eqs. (20)-(24), pp. 5-6 derives phase-dependent randomization/paralysis; Bultink Supplemental Sec. II.B, p. 11 states that the repeated-ZZ data echo flips the effective stabilizer each round and breaks paralysis. | **contradicted** as a novelty claim; **closed** as prior mechanism | Echo-breaking of leakage paralysis is direct prior art. |
| O1 — individual defect distribution | Varbanov Appendix D Eq. (D13), p. 16 gives fully randomized outcomes at phase `0` or `pi`; the general-phase paragraph, pp. 16-17, says branch operators are not projectors but simulated individual defects remain near one half for fixed or randomized phases because `d[n]=m[n] XOR m[n-2]`. | **closed, qualified** | A one-half individual defect does not imply each raw outcome is uniform or the joint Record is uninformative. |
| O2 — joint, supercheck, and temporal information | Varbanov Fig. 10 and Appendix D, pp. 15-17: same-type gauge products define a weight-six supercheck only under the schedule condition, and generic conditional phase can raise its defect rate to one half. Bultink main p. 3 plus Supplemental p. 10: the repeated-ZZ raw pattern maps to a persistent temporal syndrome. | **closed** | Never lift a one-bit marginal null to the supercheck or full time series. At favorable phases the supercheck retains parity; at generic phases it can be corrupted. |
| B1 — qutrit dynamics to parity Record | Ghosh Eqs. (19)-(22) and the following probability sentence, pp. 5-6 map leaked-block CZ phase to an ancilla rotation and outcome probability. Bultink pp. 3, 10-11 maps physical echo to an effective-check flip, raw `...++--...` outcomes, then `s_D[m]=M_A[m]M_A[m-2]`. Varbanov Appendix D supplies the Surface-17 check operators. | **closed for the cited circuits, not universalized to the current Y schedule** | The literature proves that leakage-conditioned intended-gate effects can remain physical parity-record content. |
| B2 — parity string to leakage estimate | Bultink p. 3 and Supplemental pp. 9-12: patterns are non-unique, HMM output is a posterior, ancilla leakage is confounded, and short leakage can be missed. Varbanov Appendix E/F, pp. 17-18: two-state local HMMs use approximate independent emissions and suffer crosstalk. | **closed** | An HMM is a downstream estimator, not direct truth and not an exact trajectory reconstruction. |
| B3 — intended layer plus readout bookkeeping | Varbanov Appendix G, pp. 18-19 proposes an ancilla pi pulse every other cycle plus a predetermined outcome relabeling, so a leaked ancilla assumed inert under the pulse would emit a defect every cycle. The evaluation flips outcomes only inside density-matrix-identified leakage windows and does not circuit-simulate the layer. | **closed as an ancilla-only analog; missing for the data-transversal logical frame** | Intended-gate bookkeeping can be reconciled with a detector convention, but this source does not recover an exact frame from the public Record. |
| A1 — direct heralded flag | Miyamura Fig. 3 and Eq. (5), pp. 3-4; Fig. 4, pp. 4-5; Supplemental Fig. S7, pp. 14-15. It directly measures `ge/f`, gives balanced assignment fidelity `97.1(3)%`, preserves the computational block only approximately, and suppresses cross-sector coherence. | **closed** | A direct flag is a new measurement outcome with back-action, not frame information recovered from the existing parity Record. |
| N1 — uniform-marginal relabeling | No selected source states the elementary identity `Bernoulli(1/2) XOR c = Bernoulli(1/2)` as a leakage result. Varbanov supplies the regime in which the premise can approximately occur. | **ours-inference-only** | Use only as a local marginal symmetry; it cannot prove full-Record nullity. |
| N2 — trajectory-conditioned frame identifiability | Bultink establishes non-unique parity patterns and probabilistic rather than exact inference, but no selected source proves that the current logical-frame correction is identifiable or non-identifiable. Targeted searches found no direct theorem. | **ours-inference-only** | Exact reconstruction must not be claimed. A counterexample would have to be established under the current declared instrument and public Record. |
| I1 — defensible documentation semantics | Cross-source synthesis plus the binding product boundary: subtract only the known leakage-free deterministic reference sign; retain the residual in the physical Record; do not call it a calibrated leakage-frame bit or expose hidden truth. | **closed for documentation** | No code change follows from literature alone. |

## Operation replay

### Ghosh: phase to paralysis

| input | operation | assumption | output | locator |
|---|---|---|---|---|
| data qutrit leaked in `|2>`; ancilla reset in `|0>` | Restrict CZ to joint states `|02>` and `|12>` | leaked state remains occupied over the cycle | diagonal phases `xi1, xi2` | Eqs. (19)-(20), p. 5 |
| phase difference `theta=xi2-xi1` | Surround the CZ by ancilla Hadamards | qutrit Hadamard is `H_qubit direct-sum 1` | ancilla x rotation and unambiguous probability `P(0)=cos^2(theta/2)` | Eqs. (2), (21)-(22), pp. 2, 5-6 |
| ancilla measurement | Born rule | analytic special case | equiprobable outcomes at `theta mod pi=pi/2`; deterministic paralysis at integer multiples of `pi` | Eqs. (23)-(24), p. 6 |

Eq. (21) produces a `-i` relative amplitude under the standard Pauli convention, whereas Eq. (22)
prints a real positive amplitude. Also, the probability formula gives all-zero output only at
`theta=0 mod 2pi` and all-one at odd multiples of `pi`, while Eq. (24) calls all
`theta=0 mod pi` all-zero. These source-internal inconsistencies do not change the outcome
probability or the deterministic-paralysis conclusion. This circuit contains no data echo,
neighboring check product, logical operator, or HMM.

### Bultink: physical echo to temporal syndrome

| input | operation | assumption | output | locator |
|---|---|---|---|---|
| two data transmons and one ancilla | Apply a physical `Rx(pi)` echo to both data qubits halfway through ancilla measurement | computational transition is driven; complete leaked-block unitary is not printed | ordinary echo/refocusing | Fig. 1A, p. 2; Supplemental Sec. I.C, p. 6; Fig. S3, p. 9 |
| one data qubit leaked | The echo acts only on the remaining computational data qubit | repeated-ZZ circuit | effective stabilizer flips each round and raw outcomes follow `...,+1,+1,-1,-1,...` | main p. 3; Supplemental Sec. II.B, p. 11 |
| raw outcomes | Multiply outcomes two rounds apart | repeated-ZZ definition | persistent negative data syndrome | Supplemental Sec. II.A, p. 10 |
| syndrome string | Markov prediction and Bayesian measurement update | trained model and non-unique observation model | computational-subspace posterior used for thresholding/post-selection | main pp. 3-4; Supplemental pp. 9-10 |

PFU is separate: in the first projection step, outcome `M_A=-1` records a fixed `X` on the
high-frequency data qubit for later tomography. It is not the physical echo and not a
leakage-trajectory frame.

### Varbanov: effective gauges, individual defects, and superchecks

| input | operation | assumption | output | locator |
|---|---|---|---|---|
| one high-frequency data qutrit leaked | Restrict the extended X/Z check operators to that leaked sector | `L1` and `Lm` tend to zero, no decoherence, exactly one high-frequency data site is leaked, all other sites are computational, no simultaneous neighboring ancilla leakage, and the single-qubit Hadamard acts trivially on leakage | the restricted extended X/Z operators anticommute independent of conditional phase | Eqs. (D1)-(D12), pp. 15-16 |
| conditional phase `0` or `pi` | Rephase the branch-global minus sign and interpret branch operators as projectors | one leaked site; at `pi` the outcome labels interchange | fully randomized individual gauge outcomes and exactly one-half neighboring defects in the ideal analytic model | Eq. (D13) and following paragraph, p. 16 |
| two same-type gauges | Multiply their outcomes | conditional phase `0` or `pi`, and both same-type gauges are measured before the opposite type | weight-six supercheck parity | Fig. 10a and Appendix D, pp. 15-16 |
| generic conditional phase | Apply each nonprojective gauge measurement | simulated Surface-17 schedule | individual defects remain near one half, but supercheck extraction is corrupted and its defect can rise toward one half | Fig. 10b-c and Appendix D, pp. 15-17 |
| alternating ancilla pi proposal | Apply every other cycle and relabel in post-processing | leaked ancilla unaffected by pi pulse | leaked interval would create a defect each cycle | Appendix G, pp. 18-19 |

The last row was evaluated only by flipping outcomes inside density-matrix-identified leakage
windows; it was not a physical-circuit simulation and worsened data-HMM crosstalk.

Direct replay found three printed algebra defects that do not change the normalized projector-regime
conclusion: Eq. (D11) writes a zero anticommutator for the four-overlap checks where the commutator
is zero; Eq. (D12) prints `exp(-i phi)` where direct multiplication gives `exp(-2 i phi)`; and Eq.
(D13) drops a branch-global minus sign. At `phi=pi`, the plus/minus branch labels also interchange.

### Miyamura: direct leakage flag

| input | operation | assumption | output | locator |
|---|---|---|---|---|
| fixed-frequency transmon and readout resonator | Apply near-resonant `g-e` drive during dispersive probe | `f` is not resonantly driven | merged `g/e` response and distinct `f` response | Fig. 1, p. 2 |
| integrated readout | Threshold into `ge` or `f` | calibration on prepared `g,e,f` | false flag `2.3(3)%`, missed leakage `3.5(2)%`, balanced fidelity `97.1(3)%` | Fig. 3 and Eq. (5), pp. 3-4 |
| mixed computational/leakage input | Apply detection and an unconditional calibrated recovery, then retain shots declared `ge` | approximate computational-block inverse | six-state conditional fidelity `92.9(5)%` at target `p_f=0.5` | Fig. 4, pp. 4-5 |
| coherent three-level input | Measure without and with conditioning | intended binary projector | retain much of `g-e` coherence and strongly suppress cross-sector coherence | Supplemental Fig. S7, pp. 14-15 |

This is an additional measurement instrument. It does not derive a flag or frame from a stabilizer
Record and does not execute a decoder.

## Contrary and anomaly ledger

| anomaly / contrary fact | exact evidence | consequence |
|---|---|---|
| Earlier notes treated Fig. 10b-c as an individual-check phase scan. | Varbanov Fig. 10 caption and Appendix D, pp. 15-17. | The curves are **supercheck** defect probability. Simulated individual defects stay near one half across fixed phases even though generic-phase branch operators are not projectors. |
| Earlier notes said the source had no deterministic inserted layer. | Varbanov Appendix G, pp. 18-19. | The source proposes an alternating **ancilla** pi layer with deterministic post-processing. It is not a transversal data echo and was not physically simulated. |
| Varbanov Appendix D contains printed algebra errors. | Eqs. (D11)-(D13), p. 16, independently replayed. | The four-overlap relation needs a commutator, the D12 phase prefactor is squared, and D13 omits a branch-global minus sign. The intended one-leaked-site anticommutation and normalized projector conclusions survive. |
| Fully randomized individual gauges coexist with an informative product only in a qualified regime. | Varbanov Eq. (D13), schedule paragraph, and generic-phase paragraph, pp. 16-17. | At phase `0` or `pi`, the supercheck product can retain parity; generic phase can undermine that extraction. |
| Repeated-ZZ and interleaved ZZ/XX leakage records are not the same random process. | Bultink pp. 3-4 and Supplemental pp. 10-11. | Repeated ZZ has the echo-induced `++--` temporal pattern; interleaved checks reduce to random noncommuting X/Z measurements. |
| HMM patterns are non-unique and lack direct per-shot data-leakage truth. | Bultink pp. 3-4, 10, 12; Varbanov Appendix E/F. | Posterior leakage likelihood cannot be silently promoted to exact trajectory truth or a frame bit. |
| Varbanov's production schedule suppresses a coherence/phase sensitivity that is possible in a general embedding. | Appendix B, Eqs. (B7)-(B9) and final paragraph, pp. 13-14. | Varying the exchange phase and zeroing computational-leakage coherences do not change the reported schedule-level results; the logical-rate coherence null is qualified to a Z-basis preparation. The production simulation uses the incoherent leakage model. This is a schedule-scoped counterexample to generalizing the project's relative-phase concern. |
| Bultink v1 and the published article have different title ordering and locator surfaces. | arXiv v1 title page versus DOI metadata. | The note remains pinned to v1; no v2/version-of-record page or formula locator is imported. |
| `97.1(3)%` is not a leakage true-positive rate. | Miyamura Eq. (5), p. 4. | It is balanced binary assignment fidelity; the measured `f` true-positive rate is `96.5%`. |
| Direct heralding deliberately suppresses computational-leakage coherence. | Miyamura Supplemental Fig. S7, p. 15. | “Preserved coherence” is restricted to the computational block and remains imperfect. |
| Ghosh Eqs. (21)-(22) disagree on the coherent relative phase, and Eq. (24)'s modulo statement overstates all-zero output. | Ghosh pp. 5-6. | Use the probability and deterministic-paralysis result; do not cite Eq. (22) as an exact coherent state or equate every integer multiple of `pi` with bit zero. |
| The current leaked-inert gate convention is not hardware-certified by these sources. | Ghosh Eq. (2); Varbanov Sec. I.A and Appendix D; Bultink lacks a complete multilevel/leaked-subspace echo action. | The declared matrix convention must remain explicit, especially when cross-sector coherence is retained. |

## External acquisition ledger

Search date for all rows: 2026-07-26. Backend: AnySearch `academic.search`; physics category
except the marginal/identifiability query, which also requested mathematics. Official arXiv,
publisher, Crossref, and PubMed surfaces were then used for version/publication checks. Snippets did
not close evidence rows.

| exact query | leading relevant result(s) | disposition |
|---|---|---|
| `data qubit echo leakage paralysis stabilizer` | Ghosh leakage/paralysis work; Bultink Science Advances article; `Incoherent Approximation of Leakage in Quantum Error Correction` | Ghosh and Bultink selected. The incoherent-approximation paper is adjacent to coherence decay and efficient simulation but does not supply the echo-to-frame operation chain. |
| `leakage paralysis echo pulse effective stabilizer` | No relevant academic result in the returned set | Negative search; not treated as gap proof because the lexical query was weak and the Bultink hit appeared under neighboring formulations. |
| `transmon leakage effective weight-3 gauge supercheck conditional phase` | Varbanov article/preprint; leakage-reduction work | Varbanov selected for the exact gauge/supercheck derivation. Leakage-reduction sources were rejected for this claim because removal is not frame reconstruction. |
| `qutrit echo leaked level relative phase stabilizer` | Varbanov; flux-activated leakage reduction; qudit gate synthesis | Varbanov selected for the declared leaked-inert convention. Other hits do not bridge the current stabilizer Record. |
| `transmon leakage hidden Markov parity outcomes` | Bultink and Varbanov; hardware-efficient leakage reduction | Bultink and Varbanov selected. |
| `surface code leakage supercheck conditional phase` | Varbanov | Selected; no competing source displaced the exact Appendix-D result. |
| `heralded leakage detection preserved computational coherence transmon` | Dual-rail erasure-qubit work and unrelated parity/readout results | The already acquired Miyamura preprint was read directly because the index had not surfaced this six-day-old source. Dual-rail work was rejected as a different encoding and observable. |
| `uniform marginal deterministic bit flip identifiability parity record` | Returned results were unrelated | Keep N1 as elementary local derivation; do not declare a field-wide literature gap. |
| `leakage trajectory Pauli frame reconstruction stabilizer measurement` | Returned results were unrelated | No exact theorem selected; keep N2 as project inference. |
| `logical frame leakage trajectory quantum error correction` | Returned bosonic/error-correction and general superconducting results, none matching the operation chain | No exact theorem selected; keep N2 as project inference. |

## Search-exhaustion statement

No row is labeled `confirmed-literature-gap`. The targeted searches were sufficient to find the
direct prior mechanism, the original paralysis model, the Surface-17 effective-check derivation,
and the direct-measurement alternative. They were not sufficient to prove that no trajectory-frame
identifiability theorem exists anywhere in the field. N1 and N2 therefore remain explicitly
`ours-inference-only`.

## Closure decision

The three original alternatives do not survive unchanged:

1. **Physical Record content:** supported in the narrow, relevant sense. Bultink demonstrates that
   asymmetric echo action during data leakage changes the physical parity-outcome time series.
   Varbanov shows that effective-check leakage drives simulated individual defects near one half
   across phases, while conditional phase changes the raw nonprojective branch behavior and
   supercheck extraction/statistics. After removing only the known leakage-free reference sign,
   such a residual must not be erased merely because it resembles frame bookkeeping.
2. **Observationally redundant:** rejected as a general statement. A deterministic relabeling is
   invisible in an exactly uniform single-bit marginal, but Bultink's repeated-ZZ temporal pattern
   and Varbanov's phase-qualified supercheck show why the complete Record cannot be reduced to that
   marginal.
3. **Exact trajectory-conditioned frame:** not established by the literature. Non-unique patterns,
   HMM posteriors, crosstalk, and short-event misses show that probabilistic leakage inference is
   different from exact reconstruction. They do not, by themselves, prove a no-go theorem for the
   current public Record.

The documentation-safe rule is therefore:

> Divide out only the deterministic leakage-free transversal-echo reference sign. Preserve the
> remaining detector/logical-observable residual as physical Record content under the declared
> qutrit model. Do not label it an exact leakage-frame correction, do not reconstruct it from hidden
> trajectory truth, and do not promote HMM or directly heralded flags into the product interface.

This rule is consistent with the current `uncertified` product boundary. It does not certify the
leaked-block phase convention, bound the residual, or authorize source changes.

## Admission review

The four source-only notes were written from fresh full-text reads with visual checks of every
load-bearing equation, figure, and table page. On 2026-07-26, independent source-only reviewers
returned `ADMIT-CONTENT` for Ghosh, Bultink, Varbanov, and Miyamura after the required revisions.
The review explicitly checked the echo/PFU distinction, the Ghosh phase inconsistencies, individual
defects versus the Fig. 10 supercheck, the Appendix-D printed algebra defects, the Appendix-G
truth-assisted evaluation boundary, the direct-measurement chronology, and every atomic locator.

Admission is complete only when each note carries the SHA-256 of this frozen packet and the full
corpus audit verifies the source artifact, note schema, reviewer metadata, and packet binding.
