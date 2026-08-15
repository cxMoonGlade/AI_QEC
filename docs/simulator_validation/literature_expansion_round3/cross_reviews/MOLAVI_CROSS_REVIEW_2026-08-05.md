# Independent cross-review — Molavi et al., arXiv:2603.20127v1

## Decision

**REVISE.** The audit and draft note reach the correct scientific conclusion: this paper provides
positive, small-instance evidence for worst-case decoder analysis under independently bounded
Bernoulli error rates, but it does not test robustness to a wrong temporal-memory law. The reported
decoder ordering change, percentages, circuit sizes and future-work boundary are faithfully
transcribed.

The record is not ready for admission for four reasons:

1. the note's visual-page list omits six pages used by facts and also omits the pages containing
   Algorithms 1--2 and the sampling confidence construction;
2. three locators are mechanically invalid, while the computation fact bundles independently
   locatable enumeration, optimization and sampling operations under the wrong page anchor;
3. all four relations fail the current schema: three labels do not occur in their linked Claims and
   the fourth relation points to a `literature_gap` rather than a `paper_fact`;
4. the audit does not show an operation replay despite `operation_replay_status = "complete"`.
   The operation chain is reconstructible from the paper, but the admission packet should state
   exactly what was replayed and preserve the finite-circuit independent-event boundary.

There is also a source-level reporting ambiguity worth preserving rather than silently resolving:
the prose says "Among the 6 programs in Fig. 11," whereas the figure has seven labelled
`(d, r, p)` groups and incomplete decoder convergence in several groups. The percentages themselves
are printed, but the note should not promote the ambiguous count into "six converged programs."

## Fixed-object verification

- Independently streamed source: `https://arxiv.org/pdf/2603.20127v1`.
- Fixed source: Abtin Molavi, Feras Saad and Aws Albarghouthi, *Analyzing Decoders for Quantum
  Error Correction*, arXiv:2603.20127v1, dated 20 March 2026.
- The official stream and local PDF are byte-identical: PDF 1.7, 29 pages, 1,138,710 bytes,
  SHA-256 `cf38579a83b0b21d2bb9f1bf2ee41249259e68c502589ffec446856eb5aebe90`.
- Audit reviewed:
  `docs/simulator_validation/literature_expansion_round3/MOLAVI_DECODER_ROBUSTNESS_2603_20127_AUDIT_2026-08-05.md`,
  SHA-256 `3a00087c6cd4b7676f98866048c531ead91919c5ca7ee8d116a0cc574d9e7fbb`.
- Draft note reviewed:
  `docs/simulator_validation/literature_expansion_round3/drafts/molavi_decoder_robustness_2603.20127v1_source_review.md`,
  SHA-256 `531ec947f63a44c61bbe9799c495114cdc65c9afd9943fa783572215d2fffb12`.
- The audit hash declared in the draft exactly matches the reviewed audit. The source hash declared
  in the draft exactly matches both the local artifact and official stream.
- Full-text reading covered all 29 pages. Independent visual checks covered pp. 1, 6, 7, 10--13,
  15, 17, 18, 20, 21 and 24, including Definitions 3.1--3.2, the independent-event polynomial,
  Theorems 5.4--5.6, Algorithms 1--2, Theorems 6.2 and 7.1, the benchmark definition, Fig. 11 and
  the conclusion.

## Independent scientific reconstruction

### Representation and QEC interface

The formal QEC program is a straight-line circuit with unitary, reset, measurement and probabilistic
Pauli-error statements, followed by syndrome and logical-observable declarations. For the
implementation, a Stim circuit is compiled to a detector error model. Each resulting error event is
treated as an independent Bernoulli draw with a probability and a deterministic effect on syndrome
and logical-observable bits.

This does not mean that the returned detector record has no multiround structure: one circuit fault
can affect detector outcomes at more than one time location. It does mean that the model has no
stochastic dependence between distinct error-event draws, persistent carrier, hidden transition
law, memory time or correlated temporal generator.

A decoder is a fixed black-box map from syndrome bits to a predicted logical-observable string. Its
logical error rate is the probability that this prediction differs from the program's observable.

### Symbolic uncertainty and computation

The symbolic program replaces the Bernoulli probabilities by variables. In the demonstrated
robustness problem, every variable has its own interval, so the admissible assignments form a
hyperrectangle. An assignment may therefore give different finite-circuit locations different
rates, but it remains one deterministic rate field for a program execution distribution; it is not a
sampled drift trajectory or a misspecified temporal transition law.

For a fixed decoder, the set of error bitstrings on which it fails defines an error polynomial. The
paper proves that pointwise accuracy is polynomial evaluation and worst-case robustness is
maximization over the constraint set. Enumeration classifies explored bitstrings as decoder success
or failure and gives unconditional lower and upper bounds. For hyperrectangles, multilinearity puts
extrema at vertices; partial-derivative pruning fixes certified coordinates and the remaining vertices
are exhaustively searched. The sampling hybrid estimates the unenumerated mass only for the
Accuracy problem and replaces unconditional soundness with a stated Chernoff confidence interval.

### Demonstrated reach

The evaluation uses synthetic rotated-surface-code memory circuits with `d` in `{3,5,7,9}`, odd
round counts up to `d`, the independent `si1000` model at `p` equal to `0.01`, `0.001` or `0.0001`,
and PyMatching, BP+OSD and Relay-BP. Robustness uses the per-variable box
`0.9 v <= x <= 1.1 v`.

The paper reports robustness convergence only for relatively small circuits. It identifies the
largest completed robustness case as `d=3`, `r=3`, with 286 error-channel variables. Fig. 11 uses
the paper's convergence criterion inherited from the accuracy comparison; this is not exact
large-code certification. The paper reports maximum nominal-to-worst-case gaps of 28.6% for
Relay-BP, 21.6% for BP+OSD and 21.7% for PyMatching, and a nominal-versus-robustness ordering
change between Relay-BP and BP+OSD for `d=3`, `r=3`, `p=0.001`.

### R1 boundary

The positive result varies independent event probabilities inside one finite-dimensional
hyperrectangle. It does not vary a carrier lifetime, hidden-state transition, temporal kernel,
correlation topology, mixed mechanism or stale memory calibration. It is therefore adjacent
evidence for static/per-location rate uncertainty, not evidence for robustness under a wrong
temporal-memory model. The audit's R1 classification is correct.

## Operation replay

| input | source operation | assumption | output | cross-review result |
|---|---|---|---|---|
| Stim-like QEC circuit | Compile to a detector error model | DEM error events are independent Bernoulli variables | Event probabilities and deterministic syndrome/observable effects | **complete; no continuing carrier** |
| Error bitstring `e` | Evaluate `synd(e)` and `obs(e)` and run fixed decoder `d` | Program is well-defined; decoder is deterministic for the supplied syndrome | Membership in decoder-failure set `L` | **complete** |
| Independent channel variables | Form each error minterm and sum terms indexed by `L` | Error-event probabilities factor | Error polynomial `p_L(x)` | **complete** |
| Explored error strings `S` | Accumulate `L intersect S` and `S minus L` | Unseen strings can be bounded conservatively | Unconditional lower and upper LER/robustness bounds | **complete** |
| Error polynomial plus hyperrectangle | Vertex theorem, derivative-sign pruning, then exhaustive search of free coordinates | Multilinearity and independent interval constraints | Exact extrema of each explored-set bound polynomial | **complete within the declared box model** |
| Unexplored mass for Accuracy only | Conditional rejection sampling and Chernoff inversion | I.i.d. conditional samples | Probabilistic confidence interval | **complete; not used to make robustness bounds probabilistic** |
| Surface-code task, decoder and plus/minus 10% box | Run enumeration/optimization until resource limit or stated convergence criterion | Synthetic `si1000` DEM is the target distribution family | Fig. 11 convergence and reported robustness comparisons | **complete for reported small instances; not hardware or wrong-memory evidence** |

As an algebraic check, the printed three-qubit repetition-code example gives

`p_L = x1*x2 + x1*x3 + x2*x3 - 2*x1*x2*x3`.

At the nominal point `(0.01,0.01,0.01)`, this is `0.000298`. Each partial derivative is positive on
`[0.009,0.011]^3`, so the maximum is at `(0.011,0.011,0.011)` and equals `0.000360338`. This is an
independent replay diagnostic, not a numerical result claimed by the paper.

## Claim-and-locator cross-check

| draft fact | semantic finding | locator/record finding | result |
|---|---|---|---|
| `molavi-source-identity` | Authors, title, version, date and 29-page extent are correct. | Page 1 is visually and textually adequate. | **pass** |
| `molavi-study-scope` | Formal/synthetic decoder accuracy and rate-uncertainty scope is correct. | Abstract and Sec. 1 support it. | **pass** |
| `molavi-qec-program` | Straight-line representation is correct. The body also asserts Stim-to-DEM compilation. | Fig. 3 on p. 7 supports the representation, but compilation is in Sec. 8 on p. 17 and should be split or separately located. Page 7 is absent from the declared visual list. | **revise locator/atomicity** |
| `molavi-independent-error-scope` | Independent Bernoulli factorization and absence of a persistent carrier are correct. | Sec. 5 on p. 11 is exact; p. 11 is absent from the visual list. | **revise visual record** |
| `molavi-symbolic-program` | Correct. | The named paragraph on p. 10 is exact; p. 10 is absent from the visual list. | **revise visual record** |
| `molavi-accuracy-definition` | Correct. | `Definition 3.1` alone is not an accepted locator and p. 6 is absent from the visual list. | **revise locator/visual record** |
| `molavi-robustness-definition` | Correct for a fixed decoder and constrained parameter assignments; hyperrectangles are the demonstrated sets. | `Definition 3.2` alone is not an accepted locator and p. 6 is absent from the visual list. | **revise locator/visual record** |
| `molavi-polynomial-reduction` | Theorems 5.4--5.5 are transcribed correctly. | Page 11 is correct but absent from the visual list. | **revise visual record** |
| `molavi-computation` | Enumeration, sound bounds, exact box optimizer and Accuracy-only sampling are correctly distinguished. | The claim spans Algorithm 1 on p. 13, Algorithm 2/Theorem 6.7 on p. 15 and Theorem 7.1 on p. 17; `PDF page: 12` does not locate those operations. Split into atomic facts or use exact multi-page locators and add the pages to the visual record. | **revise** |
| `molavi-qec-task` | Distances, rounds, model and three strengths are correct. | Sec. 8 on p. 18 is exact; p. 18 is absent from the visual list. | **revise visual record** |
| `molavi-decoder-set` | Decoder names are correct. | Sec. 8 on p. 18 is exact; p. 18 is absent from the visual list. | **revise visual record** |
| `molavi-robustness-protocol` | Independent plus/minus 10% interval for each nominal variable is correct. | Sec. 8.2 on p. 20 is exact and visually checked. | **pass** |
| `molavi-robustness-result` | All percentages and the ordering change are printed correctly. | Page 21 is exact. Replace "six converged robustness programs": the prose says six, but Fig. 11 visibly labels seven parameter groups and has missing decoder bars. | **revise count wording** |
| `molavi-robustness-reach` | The source identifies `d=3`, `r=3` and 286 variables as its largest robustness case. | Page 21 is exact. Qualify convergence by the paper's finite-resource criterion; do not imply exact large-code certification. | **pass with retained boundary** |
| `molavi-gap-memory-law` | The absence of a carrier/history-law perturbation is correct. | The source-wide negative finding should cover the complete formal and evaluation specification; p. 12 is not in the visual list. | **pass semantics; revise record** |
| `molavi-gap-hardware-transfer` | Correct. | Sec. 8 establishes synthetic-only evaluation; p. 18 is absent from the visual list. | **revise visual record** |
| `molavi-future-scope` | Both future directions are correctly transcribed. | `Conclusion` alone is not an accepted locator; use `Sec. 10, Conclusion` or a page anchor. | **revise locator** |

## Audit-packet cross-check

The audit's central R1 judgment, decoder comparison, uncertainty-guarantee distinction, F1
placement and non-promotions all pass. Three wording/record repairs are needed:

1. Anchor the independent-draw claim to Sec. 5 on p. 11, not only to the QEC syntax on p. 7.
2. Replace "across six converged programs" with wording such as "among the configurations
   summarized in Fig. 11, the authors report ..." and record the source's six-versus-seven
   ambiguity.
3. Add an operation replay or explicitly state that `operation_replay_status = "complete"` covers
   the formal DEM/event-to-polynomial-to-bound chain and small-instance protocol. Preserve that it
   does not reproduce the unpublished benchmark artifact, turn the rate box into a temporal law,
   or extend convergence to larger circuits.

The phrase "tight convergence" is used by the source, but downstream synthesis should say that the
reported cases met the paper's stated finite-resource convergence criterion. It should not be used
as shorthand for exact worst-case LER over large circuits.

## Schema and relation audit

The ordinary artifact-verifying parser first rejects the draft at its intentional status gate because
it declares `evidence_status = "unpersisted"` and `admission_status = "draft_not_admitted"`. A
read-only parse beyond that gate found independent blockers:

- With the current visual list, body parsing stops at `molavi-qec-program`: p. 7 is not declared
  visually checked.
- Even when all pages are hypothetically accepted, body parsing stops at
  `molavi-accuracy-definition` because `Definition 3.1` lacks an accepted section/page/figure/table/
  equation/algorithm anchor. `Definition 3.2` and `Conclusion` have the same defect.
- Relation 1 label `symbolic QEC program with bounded Bernoulli rates` does not occur in the linked
  Claim. `symbolic QEC program` does.
- Relation 2 label `worst-case logical error rate over a rate uncertainty set` does not occur in the
  linked Claim. `maximum logical error rate` does.
- Relation 3 label `error-space enumeration and constrained polynomial optimization` does not
  occur in the linked Claim. `structured enumeration of error bitstrings` does.
- Relation 4 points to `molavi-gap-memory-law`, a `literature_gap`; relations must point to a
  `paper_fact`. It can instead point to `molavi-independent-error-scope` with a label such as
  `independent Bernoulli random variable`, which occurs exactly in that Claim.

With those three locator repairs, visual pages sufficient for the existing facts, and the four
relation repairs applied hypothetically in memory, all 17 sections (15 `paper_fact`, two
`literature_gap`) and all four relations pass the body/relation parser. The computation fact still
requires semantic splitting or broader visual/locator coverage even though that minimal mechanical
repair can satisfy the parser.

## Required revisions before pass

### Audit

1. Add the operation replay and its explicit independent-event, finite-circuit and Accuracy-only
   sampling boundaries.
2. Move the independence anchor to Sec. 5, p. 11 and distinguish a per-location finite-circuit rate
   field from a sampled temporal-memory law.
3. Remove the unqualified "six converged programs" count and retain the source-level Fig. 11
   ambiguity.
4. Describe the largest result as meeting the source's convergence criterion on a small circuit,
   not as large-code or exact hardware robustness certification.

### Draft note

1. Add every fact-bearing visual page at minimum: pp. 6, 7, 10--12 and 18. For the actual
   computation replay, also add pp. 13, 15 and 17.
2. Repair the three mechanically invalid locators: prefix Definitions 3.1--3.2 with Sec. 3 and
   anchor the conclusion to Sec. 10 or p. 24.
3. Split `molavi-computation` into enumeration/sound-bound, hyperrectangle-optimization and
   Accuracy-only sampling facts, or provide exact locators and visual coverage for all three.
4. Split or re-anchor the Stim-to-DEM implementation sentence currently placed under the p. 7
   representation fact; the implementation statement is on p. 17.
5. Repair all four relations as listed above.
6. Replace "six converged robustness programs" with source-faithful wording that does not resolve
   the paper's inconsistent group count.

## Disposition

- `read_status`: complete
- fixed-source identity and PDF hash: **pass**
- audit/source-note hash binding: **pass**
- central scientific classification: **pass**
- operation reconstruction: **complete in this cross-review; revise packet documentation**
- small-instance and wrong-memory-law boundaries: **pass**
- source-note locators/visual coverage/relations: **revise**
- overall cross-review: **REVISE**
- manifest action: none taken

After revision, the defensible use is narrow but useful: Molavi et al. formalize and demonstrate
worst-case evaluation of fixed decoders under independently bounded Bernoulli event probabilities,
and show on small synthetic surface-code circuits that this robustness view can alter a decoder
comparison. The source does not establish robustness to a wrong temporal-memory model, hardware
memory-conditioned decoder benefit, population-level hardware comparison, online drift tracking,
or frozen cross-device/cross-code transfer.

## Final revision verification

**Final decision: PASS for pre-admission review.** This decision supersedes the initial `REVISE`
decision above. The repaired audit and draft note close every required revision without changing
the paper's defensible scientific scope.

| required repair | independent verification | result |
|---|---|---|
| Full operation replay | The audit now separately replays Stim-to-DEM compilation, decoder-failure classification, factorized minterm construction, enumerative bounds, box optimization, Accuracy-only sampling and the finite-resource benchmark comparison. | **pass** |
| Independence anchor | Sec. 5, p. 11 is now the explicit anchor for independent Bernoulli error-channel variables; the audit and note do not infer independence merely from circuit syntax. | **pass** |
| Atomic computation facts | Stim-to-DEM compilation, enumeration, hyperrectangle optimization and Accuracy-only sampling are separate source-located facts. | **pass** |
| Visual and locator record | Declared visual pages are pp. 1, 6, 7, 10--13, 15, 17, 18, 20, 21 and 24. Definitions, algorithms, theorem, implementation, benchmark and conclusion locators now satisfy the current schema and match the rendered pages. | **pass** |
| Relations | All four relations resolve to `paper_fact` records, and each relation label occurs exactly in its linked Claim. | **pass** |
| Fig. 11 ambiguity | The packet preserves that the prose says "6 programs" while the figure visibly contains seven labelled parameter groups and missing decoder bars. It does not manufacture a reconciled count. | **pass** |
| Finite-resource reach | The `d=3`, `r=3`, 286-variable case is described as meeting the source's finite-resource convergence criterion, not as exact large-code certification. | **pass** |

The fixed PDF remains byte-identical to the independently fetched official arXiv v1 artifact:

- PDF SHA-256: `cf38579a83b0b21d2bb9f1bf2ee41249259e68c502589ffec446856eb5aebe90`;
- revised audit SHA-256: `34468763c454d523aac89a1c4e9c4cfcac463e296c70f1e07a1189800d087b24`;
- revised draft-note SHA-256: `7a540f2d2b9ef216fb7e7f304b639239262a192d51c6818943d71febdb7f1c30`.

A read-only prospective parse, changing only the three admission-control values in memory, passes
artifact verification and parses 20 sections: 18 `paper_fact` records, two `literature_gap`
records and four relations. The unmodified draft still fails only at its intentional
`unpersisted`/`draft_not_admitted` gate. The directory-level schema audit reports the same
intentional gate for this note, and `git diff --check` is clean for the audit, note and cross-review.

The scientific boundary has not drifted. This source supports worst-case fixed-decoder analysis
under an independently bounded finite-circuit Bernoulli rate box and a small synthetic comparison
whose ordering changes for one tested configuration. It remains non-evidence for robustness under
a wrong temporal-memory law, hardware memory-conditioned decoder benefit, a hardware population
comparison, online adaptation, or frozen transfer across devices, codes or memory models.

Final disposition: **PASS; ready for the parent-controlled admission step.** No audit, note or
manifest change was made in this final verification.
