+++
schema = "error_coupling_simulator.literature.note.v1"
source_id = "arxiv:2009.07851"
source_version = "v3"
source_uri = "https://arxiv.org/abs/2009.07851v3"
source_artifact = "docs/papers/2009.07851v3.pdf"
source_sha256 = "4b4f244f949b0d1e862ff44e6328f33abab93654cd64a7e5f1ada0467ccaafd7"
title = "The XZZX surface code"
publication_status = "preprint"
read_status = "complete"
evidence_status = "persisted"
review_scope = "full_text"
operation_replay_status = "complete"
audit_packet = "docs/simulator_validation/XZZX_MEASUREMENT_RECORD_SOURCE_AUDIT_2026-07-26.md"
audit_packet_sha256 = "ee557e84655d8abcfebba66d953c9a64fe982c8c9e01e53a3eea0898feedfff3"
admission_status = "source_only_reviewed"
admission_reviewer = "independent_xzzx_primary_second_pass_2026_07_26"
admission_date = "2026-07-26"
visually_checked_pages = [1, 2, 3, 4, 5, 6, 9, 10, 11, 12, 13]

[[relations]]
predicate = "defines"
object_id = "bonilla-xzzx-bulk-face-check"
object_type = "model"
object_label = "XZZX bulk face check"
fact_id = "bonilla-xzzx-bulk-check"

[[relations]]
predicate = "defines"
object_id = "bonilla-consecutive-stabilizer-defect"
object_type = "observable"
object_label = "stabilizer outcome differs from its preceding outcome"
fact_id = "bonilla-xzzx-consecutive-defect"

[[relations]]
predicate = "uses"
object_id = "bonilla-phenomenological-measurement-flip"
object_type = "model"
object_label = "incorrect stabilizer outcome"
fact_id = "bonilla-xzzx-phenomenological-model"
+++
# Source review — Bonilla Ataides et al. on the XZZX surface code

## Source identity [paper_fact]
Fact ID: bonilla-xzzx-source
Source locator: Title page, author block, and arXiv version stamp
PDF page: 1
Claim: The source is the sixteen-page arXiv:2009.07851v3 final-author manuscript on the XZZX surface code by Bonilla Ataides and coauthors.

The manuscript reports code-capacity and phenomenological repeated-measurement studies and links
the associated simulation software and data.

## XZZX bulk face check [paper_fact]
Fact ID: bonilla-xzzx-bulk-check
Source locator: Results, Fig. 1(a) and caption
PDF page: 2
Claim: The XZZX bulk face check is a product of two Pauli-X terms and two Pauli-Z terms on square-lattice vertices, and the same stabilizer form is used at every bulk face.

The figure separately depicts a truncated boundary stabilizer and a rectangular rotated-lattice
choice of boundaries.

## Local Hadamard equivalence [paper_fact]
Fact ID: bonilla-xzzx-local-equivalence
Source locator: Results, opening paragraph below Fig. 1
PDF page: 2
Claim: A Hadamard rotation on alternating data qubits maps the conventional surface code locally to the XZZX surface code without changing its code parameters.

This is a local change of basis on the data register, not a statement about a particular ancilla
schedule.

## Consecutive stabilizer-outcome defect [paper_fact]
Fact ID: bonilla-xzzx-consecutive-defect
Source locator: Fault-tolerant threshold discussion, Fig. 5(a-d) and caption
PDF page: 6
Claim: In the repeated-measurement phenomenological model, a defect is identified when a stabilizer outcome differs from its preceding outcome.

The figure represents data errors as spatial strings and measurement-outcome errors as temporal
strings; one isolated measurement flip produces two sequential defects.

## Phenomenological measurement model [paper_fact]
Fact ID: bonilla-xzzx-phenomenological-model
Source locator: Fault-tolerant threshold model, paragraph below Fig. 5
PDF page: 6
Claim: The fault-tolerant numerical study uses independent data Pauli errors and an independent incorrect stabilizer outcome with probability q equal to the sum of its declared high-rate and low-rate error probabilities.

The threshold calculation operates on this phenomenological outcome-flip model rather than on a
gate-level selective measurement instrument.

## Leading-order ancilla sketch [paper_fact]
Fact ID: bonilla-xzzx-ancilla-sketch
Source locator: Fault-tolerant threshold model, lower-left paragraph below Fig. 5
PDF page: 6
Claim: To leading order, the source motivates its outcome-flip rate by an ancilla prepared in the plus state, coupled to one check by bias-preserving controlled-not and controlled-phase gates, and measured in the Pauli-X basis.

The paragraph supplies neither the order of those gates nor a branch-conditioned state-update
map.

## Circuit-level correlated noise deferred [paper_fact]
Fact ID: bonilla-xzzx-circuit-noise-limit
Source locator: Discussion, final paragraph
PDF page: 10
Claim: The source identifies circuit-level and correlated-noise extensions of the presented phenomenological study as future work.

Its reported repeated-measurement thresholds therefore do not establish a physical ancilla
instrument.

## Complete rotated schedule absent [literature_gap]
Fact ID: bonilla-xzzx-gap-complete-schedule
Source locator: Full-text review, with the code geometry in Fig. 1 and the ancilla sketch on PDF p. 6
PDF page: 6
Claim: The source does not enumerate a complete rotated distance-three or distance-five ancilla schedule with coordinates, gate slots, control-target assignments, and boundary omissions.
Gap scope: source_local

The geometry and leading-order circuit sketch are less specific than a runnable circuit artifact.

## First-round reference absent [literature_gap]
Fact ID: bonilla-xzzx-gap-first-round-reference
Source locator: Fig. 5 and its consecutive-outcome defect definition
PDF page: 6
Claim: The source does not define a first-round detector anchor for an arbitrary initial state.
Gap scope: source_local

Its stated defect rule compares a stabilizer result with a preceding result.

## Ancilla reset map absent [literature_gap]
Fact ID: bonilla-xzzx-gap-reset
Source locator: Full-text review, including the ancilla sketch on PDF p. 6
PDF page: 6
Claim: The source does not define a syndrome-ancilla reset or re-preparation map between repeated extraction rounds.
Gap scope: source_local

The manuscript's logical-patch initialization material is a different operation.

## Full joint Record law absent [literature_gap]
Fact ID: bonilla-xzzx-gap-full-record
Source locator: Methods, tensor-network decoder and minimum-weight matching sections, PDF pp. 11-13
PDF page: 13
Claim: The source does not report the full joint probability law of all detector outcomes and a logical observable.
Gap scope: source_local

Sampled histories are aggregated through a decoder into logical failure rates and thresholds.
