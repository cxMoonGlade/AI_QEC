# Independent source rereview, round 2 — Kim, Oh, and Kim, arXiv:2607.03939v1

Date: 2026-07-27

## Verdict

**PASS.** The repaired reading note and source-only audit are semantically
faithful to the reviewed source at their stated, bounded scope. There are no
remaining source-semantic blockers to source-only corpus admission.

Admission is safe after the expected bookkeeping-only finalization:

1. record this round-2 PASS and reviewer identifier in the audit packet;
2. recompute the audit-packet hash in the note;
3. change the note from `draft_pending_review` to `source_only_reviewed` and
   replace the pending reviewer value;
4. rerun artifact-backed note validation; and
5. only then add the resulting note identity to `CURRENT_CORPUS.toml` and
   validate the rebuilt corpus.

This verdict applies only to the exact source, note, and audit revisions hashed
below. Any semantic edit requires renewed review.

## Reviewed revisions

| object | path | SHA-256 |
|---|---|---|
| source PDF | `docs/papers/2607.03939v1.pdf` | `f02ec3815f3776c25b2e4a460eaaea2988b180deaecf9b602d4c0017c903cb9b` |
| candidate note | `docs/papers/reading_notes/kim_qutrit_camps_haldane_2607.03939v1_source_review.md` | `898a0dcad70c353e5a14c5623c0ef9e99d5b8e36cfe9231ebcc11622df202a25` |
| source-only audit | `docs/simulator_validation/KIM_2607_03939V1_SOURCE_ONLY_AUDIT_2026-07-27.md` | `8f82e5524a06e8175413fff64d1247925e82197d6fc52b81e915eaac3e47ce06` |

The source object is a valid, unencrypted 30-page PDF 1.7 file of 1,282,484
bytes with a valid PDF header, cross-reference structure, and EOF marker. Its
title, authors, version, and printed date agree with the note.

## Independence and method

I reopened the complete source and fixed the source-side interpretation before
opening either repaired candidate artifact. The PDF was reread in source order.
Extracted text was used for navigation and bounded terminology scans; rendered
source pages 2--5, 9, 13--14, and 18--21 were inspected directly for the
load-bearing formulas, figures, theorem statement, proof restrictions, and
benchmark captions.

The earlier FAIL was not used as scientific evidence or as a substitute for
this reread. It was used only as a regression target: the repaired artifacts
had to distinguish the paper's active paired update from a passive
fixed-Hamiltonian coordinate pullback without inventing a source ambiguity.

## Regression result: active and passive frames

The repair is correct.

On PDF p. 2, Fig. 1 and the algorithm paragraph, the source says the
disentangler acts on the state while the Hamiltonian is updated simultaneously,
and it prints

\[
  \lvert\psi\rangle\mapsto C\lvert\psi\rangle,\qquad
  H\mapsto CHC^\dagger.
\]

That paired active transformation preserves the expectation value:

\[
  \langle C\psi\rvert CHC^\dagger\lvert C\psi\rangle
  =\langle\psi\rvert H\lvert\psi\rangle.
\]

The distinct passive residual-frame identity, when the physical Hamiltonian is
held fixed and a physical state is parameterized as
\(\lvert\psi_{\rm phys}\rangle=C\lvert\psi_{\rm residual}\rangle\), uses
\(C^\dagger H C\). The repaired audit explicitly separates these conventions,
and the note records only the formula actually printed by the source. Neither
artifact now calls the source's active paired update ambiguous or promotes it
as the passive CAPEPS pullback.

## Claim-by-claim source check

| topic | source finding | candidate treatment | result |
|---|---|---|---|
| qutrit algebra and CAMPS ansatz | PDF pp. 1--2 and SM pp. 8--9 define the qutrit Paulis, Fourier/phase/SUM Clifford generators, qutrit MPS, and sequential Clifford-augmented MPS ansatz. | Records these as source-specific qutrit CAMPS-DMRG ingredients, without promoting them to leakage or PEPS machinery. | PASS |
| 90 candidates | SM p. 9, Eqs. (S6)--(S7), gives \(\lvert\mathrm{Sp}(4,\mathbb F_3)\rvert=51840\), local order \(24^2\), and the printed one-sided count \(51840/24^2=90\). The source calls these left cosets after factoring the local freedom relevant to output bipartite entanglement. | Preserves the source's one-sided statement, does not claim double-sided local equivalence, and records the absence of an executable representative list. | PASS |
| exact theorem | SM pp. 18--19, Lemma 3, Theorem 1, and Eq. (S60), prove the gate choice for the OBC AKLT state with \(L=R=e_\uparrow\), a greedy sequential left-to-right sweep, and the canonical interval \(a_j\in[4/9,2/3]\), with \(a_{j+1}=(2-a_j)/3\). The last bond is checked separately. | States the boundary condition, state, gate class, and greedy schedule, and rejects promotion to global optimization, arbitrary boundaries/schedules, general Haldane states, or non-Clifford circuits. | PASS |
| majorization and post-sweep result | SM pp. 18--21 gives the candidate-polynomial classification, Schmidt-vector majorization, then separately checks that the identity class is locally optimal after the KW sweep, including boundary checks. | Keeps the theorem and post-sweep local-optimum statements separate and bounded. | PASS |
| phase-wide wording | PDF p. 3 and the Discussion combine the specified-AKLT proof with selected numerical observations and state a broader Haldane-phase conclusion; no theorem extends Theorem 1 to every state in the phase. | Records the wording as a paper claim and separately records the missing phase-wide exact proof. | PASS |
| approximately 0.35 entropy gap | SM p. 19, Eq. (S61), computes the minimum gate-type entropy gap over the canonical interval and qualitatively interprets it as robustness to small deviations. It supplies no perturbation norm, radius, or optimizer-preservation bound. | Preserves the exact interval calculation and labels quantitative perturbation robustness as missing. | PASS |
| numerical comparisons | Main Figs. 2--3 and SM Figs. S1--S2 show finite selected workloads, chiefly \(N=128\), displayed bond dimensions, and \(\chi=1000\) DMRG reference values for the energy-error comparisons. | Limits the empirical claim to the shown workloads and does not treat the reference calculation as an independent exact solution. | PASS |
| resource evidence | The source gives no matched runtime, peak-memory, throughput, or asymptotic benchmark; no code/commit identity, convergence tolerances, random seeds, or raw benchmark data are supplied. | Explicitly rejects a matched resource or scaling claim. | PASS |
| absent project bridges | The full source contains no PEPS/CAPEPS construction, measurement--reset--Record instrument, Born-branch accounting, conditional-fidelity or Record-TV observable, or computational-versus-leakage sector/channel model. Its qutrit is the intended spin-1 local Hilbert space. | Records these as source-local gaps and prevents promotion to project implementation evidence. | PASS |

The remaining note facts and gaps were also checked against their cited source
locations. I found no unsupported formula, misplaced epistemic class, or
material overstatement.

## Structural and fail-closed checks

The note's source hash matches the PDF, and its
`audit_packet_sha256` matches the reviewed audit revision.

The on-disk note currently fails the artifact-backed parser at the intended
gate only:

```text
admission_status must be 'source_only_reviewed'
```

A read-only in-memory simulation changed only the pending admission status and
reviewer values. With source and audit verification enabled, the complete note
then parsed successfully as 32 evidence records: 23 `paper_fact` records and 9
`literature_gap` records.

At the validation snapshot, the current manifest had file SHA-256
`ddd1b2caa01ca2aa23579de4946ccafc7a0830c8d4fc1e7e41b3dedc2a51cba4`,
loaded successfully with 38 notes and 473 paper facts, and had corpus identity
SHA-256
`d9ff9d99ed7de88e0d9fefd2e44d20202cb1f5818bf9d8f3b1c1d83fbba4411c`.
The Kim note was absent, as required while review remained pending. The
artifact-verified candidate audit saw 280 candidates, 38 validated and 242
excluded; this note's reported exclusion was the pending admission status.

## Remaining boundaries, not admission blockers

Admission does not close or authorize any of the following:

- a double-sided qutrit Clifford equivalence classification or executable set
  of 90 representatives;
- a global or phase-wide exact optimality theorem;
- a normed quantitative perturbation guarantee;
- matched runtime, memory, throughput, or asymptotic resource advantage;
- a PEPS/CAPEPS residual or two-dimensional algorithm;
- a measurement, reset, branch-mass, trajectory, detector-Record, conditional
  fidelity, or Record-TV mechanism; or
- a qutrit leakage/seepage/return model.

These are correctly retained as gaps or kill conditions. They do not block
admission of the bounded source facts.

## Admission decision

**Safe to admit: yes, for source-only use and only after the mechanical
finalization and fresh artifact-backed validation listed above.**

Recommended reviewer identifier:
`independent_kim_2607_source_rereview_round2_2026_07_27`.
