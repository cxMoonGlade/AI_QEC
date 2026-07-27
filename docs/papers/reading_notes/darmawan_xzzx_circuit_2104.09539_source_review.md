+++
schema = "error_coupling_simulator.literature.note.v1"
source_id = "arxiv:2104.09539"
source_version = "v2"
source_uri = "https://arxiv.org/abs/2104.09539v2"
source_artifact = "docs/papers/2104.09539v2.pdf"
source_sha256 = "809149344e94392151a3935a4ec9615930e19d7aee414a9d022a7ac07036e5e5"
title = "Practical quantum error correction with the XZZX code and Kerr-cat qubits"
publication_status = "preprint"
read_status = "complete"
evidence_status = "persisted"
review_scope = "full_text"
operation_replay_status = "complete"
audit_packet = "docs/simulator_validation/XZZX_MEASUREMENT_RECORD_SOURCE_AUDIT_2026-07-26.md"
audit_packet_sha256 = "70ce52221dad7b3be0578b3b8068385017b218af3ddc74d1f510efa66fbfadb3"
admission_status = "source_only_reviewed"
admission_reviewer = "independent_xzzx_primary_second_pass_2026_07_26"
admission_date = "2026-07-26"
visually_checked_pages = [1, 3, 4, 6, 7, 8, 10, 11, 12, 13, 16, 17, 18]

[[relations]]
predicate = "defines"
object_id = "darmawan-xzzx-parity-shell"
object_type = "method"
object_label = "XZZX check"
fact_id = "darmawan-xzzx-check-circuit"

[[relations]]
predicate = "defines"
object_id = "darmawan-consecutive-check-defect"
object_type = "observable"
object_label = "defect"
fact_id = "darmawan-xzzx-defect"

[[relations]]
predicate = "defines"
object_id = "darmawan-conditional-x-repreparation"
object_type = "method"
object_label = "corresponding plus or minus X eigenstate"
fact_id = "darmawan-xzzx-repreparation"

[[relations]]
predicate = "limits"
object_id = "darmawan-residual-leakage-omission"
object_type = "limitation"
object_label = "residual leakage"
fact_id = "darmawan-xzzx-leakage-omission"
+++
# Source review — Darmawan et al. on an XZZX ancilla circuit

## Source identity [paper_fact]
Fact ID: darmawan-xzzx-source
Source locator: Title page, author block, and arXiv version stamp
PDF page: 1
Claim: The source is the twenty-one-page arXiv:2104.09539v2 manuscript by Darmawan and coauthors on an XZZX surface-code architecture built from Kerr-cat qubits.

It combines physical component simulations with circuit-level Pauli simulations and small-code
exact density-matrix calculations.

## XZZX operator orientation [paper_fact]
Fact ID: darmawan-xzzx-operator
Source locator: Sec. II.A, Fig. 2(a) and adjacent text
PDF page: 3
Claim: The source writes each bulk face check as X tensor Z tensor Z tensor X, with the figure placing X on the left and right data sites and Z on the upper and lower data sites.

The standard-layout boundary checks in this figure are distinct from the later rotated nine-data
layout.

## Ordered XZZX check circuit [paper_fact]
Fact ID: darmawan-xzzx-check-circuit
Source locator: Sec. II.A, Fig. 2(a-b), caption, and adjacent circuit description
PDF page: 3
Claim: One XZZX check is measured by preparing a face ancilla in the plus state, applying an ordered CZ, CX, CX, CZ sequence to its four data neighbors, and measuring the ancilla in the Pauli-X basis.

The ancilla is the control of the two CX gates. The spatial arrows in Fig. 2(a) assign the four
interaction slots, and a boundary slot with no neighbor is left idle.

## Rotated nine-data ordering exception [paper_fact]
Fact ID: darmawan-xzzx-rotated-order
Source locator: Sec. II.A, paragraph following the Fig. 2 circuit description
PDF page: 3
Claim: For the rotated nine-data-qubit code, every second face swaps the order of the two CX interactions to mitigate hook-error propagation.

The source contrasts this exception with the common ordering used for its standard-layout checks.

## Consecutive XZZX check defect [paper_fact]
Fact ID: darmawan-xzzx-defect
Source locator: Sec. II.B, opening decoder definition
PDF page: 3
Claim: A defect occurs at face f and time t when the product of the check outcomes at times t minus one and t equals minus one.

The check outcome is denoted by `S_f(t)`.

## Conditional X-basis re-preparation [paper_fact]
Fact ID: darmawan-xzzx-repreparation
Source locator: Sec. III.B.4, Fig. 6 and adjacent paragraph
PDF page: 7
Claim: After projective readout places the measured ancilla in computational state zero or one conditional on the outcome, inverse rotations prepare the corresponding plus or minus X eigenstate for the next syndrome round.

The operation preserves branch information in the sign of the prepared X eigenstate.

## Residual leakage omitted [paper_fact]
Fact ID: darmawan-xzzx-leakage-omission
Source locator: Sec. IV.B, paragraph beginning with leakage suppression at the physical level
PDF page: 10
Claim: After suppressing Kerr-cat leakage at the physical-operation level, the source neglects the residual leakage in its subsequent surface-code simulations.

The manuscript says further work is needed to model and counteract leakage throughout the
architecture.

## Small exact simulation is two-level [paper_fact]
Fact ID: darmawan-xzzx-small-exact-two-level
Source locator: Sec. V, exact-simulation description and leakage qualification
PDF page: 13
Claim: The small-code exact density-matrix simulations use strict two-level qubits and neglect residual leakage.

Their retention of non-Pauli channel terms does not extend the simulated Hilbert space beyond the
qubit subspace.

## Sequential exact check simulation [paper_fact]
Fact ID: darmawan-xzzx-sequential-exact
Source locator: Appendix A.2, exact-simulation implementation paragraph
PDF page: 17
Claim: The small exact simulation completes and measures one check at a time so that it stores one ancilla, unlike the parallel interleaved check schedule used by the Pauli simulation.

The source notes that different ordering changes data--ancilla error propagation and makes the
matched idle-noise exposure only roughly equivalent.

## Complete rotated schedule absent [literature_gap]
Fact ID: darmawan-xzzx-gap-complete-rotated-schedule
Source locator: Sec. II.A circuit description and rotated nine-data ordering exception
PDF page: 3
Claim: The source does not publish a complete coordinate and gate-slot table for all checks of the rotated distance-three or distance-five circuit.
Gap scope: source_local

It specifies the common shell and one ordering exception, not a runnable planar circuit artifact.

## Fixed-state reset absent [literature_gap]
Fact ID: darmawan-xzzx-gap-fixed-reset
Source locator: Sec. III.B.4, Fig. 6 and adjacent re-preparation paragraph
PDF page: 7
Claim: The source does not specify feedback that maps both readout branches to one fixed plus-state ancilla before the next check.
Gap scope: source_local

Its stated re-preparation yields the corresponding plus or minus X eigenstate.

## Retained-leakage Record absent [literature_gap]
Fact ID: darmawan-xzzx-gap-retained-leakage-record
Source locator: Sec. IV.B leakage omission and Sec. V exact-simulation scope
PDF page: 13
Claim: The source does not propagate residual leakage through the full repeated XZZX circuit into a retained detector record.
Gap scope: source_local

Both its large-code and small-code routes remove that degree of freedom before code-level
evaluation.

## Full joint Record law absent [literature_gap]
Fact ID: darmawan-xzzx-gap-full-record
Source locator: Threshold protocol and Appendix A simulation outputs
PDF page: 17
Claim: The source does not report the full joint probability law of all detector outcomes and a logical observable.
Gap scope: source_local

Syndrome histories are consumed by decoders and summarized by logical failure or
syndrome-conditioned logical channels.
