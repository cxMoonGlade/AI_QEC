+++
schema = "error_coupling_simulator.literature.note.v1"
source_id = "arxiv:1210.7011"
source_version = "v2"
source_uri = "https://arxiv.org/abs/1210.7011v2"
source_artifact = "docs/papers/1210.7011v2.pdf"
source_sha256 = "d0d52308fa0e23e7a8a10eab0291c3d02a9b28cb94893375d36693a602b1543f"
title = "Process verification of two-qubit quantum gates by randomized benchmarking"
publication_status = "published"
read_status = "complete"
evidence_status = "persisted"
review_scope = "full_text"
operation_replay_status = "complete"
audit_packet = "docs/simulator_validation/CORCOLES_1210_7011_SOURCE_ONLY_AUDIT_2026-07-27.md"
audit_packet_sha256 = "355636900305d3f6967bc1e973f441c09a1f3bcce633b4f48cb5a1ae01706088"
admission_status = "source_only_reviewed"
admission_reviewer = "corcoles_independent_source_rereview_2026_07_27"
admission_date = "2026-07-27"
visually_checked_pages = [1, 8, 9]
+++
# Full-text review — Córcoles et al., “Process verification of two-qubit quantum gates by randomized benchmarking”

## Source identity [paper_fact]
Fact ID: corcoles-source-identity
Source locator: PDF p. 1 title page and arXiv footer; official arXiv v2 version history; APS DOI record
PDF page: 1
Claim: The local artifact is the nine-page arXiv:1210.7011v2 version of Córcoles et al.'s paper, whose footer identifies v2 as 2 November 2012 and whose published record is *Physical Review A* 87, 030301(R) (2013).

The title page instead prints “Dated: November 27, 2024.” That line conflicts
with the arXiv footer and the publication chronology, so it is recorded as an
artifact anomaly and is not used as the source date.

## Selection scope [paper_fact]
Fact ID: corcoles-selection-scope
Source locator: Abstract and Introduction, PDF p. 1; supplement section “Decomposition of the two-qubit Clifford operations,” PDF p. 8
PDF page: 1
Claim: The source studies two-qubit randomized benchmarking and supplies a gate decomposition used to sample and implement every operation in the two-qubit Clifford group.

It is a hardware randomized-benchmarking and compilation source, not a
tensor-network or quantum-error-correction simulation paper.

## Single-qubit groups [paper_fact]
Fact ID: corcoles-local-groups
Source locator: Supplement, first paragraph under “Decomposition of the two-qubit Clifford operations,” PDF p. 8
PDF page: 8
Claim: The source defines the single-qubit Clifford group \(\mathcal C_1\) to have 24 elements and introduces the three-element local group \(\mathcal S_1=\{I,R_S,R_S^2\}\), whose nontrivial action cycles Bloch-sphere axes.

These sets appear as local factors in the displayed two-qubit decompositions.

## Four-class decomposition [paper_fact]
Fact ID: corcoles-four-class-decomposition
Source locator: Main-text decomposition paragraph, PDF p. 1; supplement four displayed sequences, PDF p. 8
PDF page: 8
Claim: The source divides the full two-qubit Clifford group into four distinct decomposition classes represented by local, CNOT-like, iSWAP-like, and SWAP circuit cores.

The supplement displays the local gates surrounding each entangling core. It
does not express this classification using a formal quotient symbol.

## Class cardinalities [paper_fact]
Fact ID: corcoles-class-counts
Source locator: Main-text class-count paragraph, PDF p. 1; supplement text adjacent to the four displayed sequences, PDF p. 8
PDF page: 8
Claim: The four source classes contain \(576\), \(5{,}184\), \(5{,}184\), and \(576\) operations, respectively, summing to all \(11{,}520\) two-qubit Clifford operations.

The supplement gives the same counts as \(24^2\), \(24^2 3^2\),
\(24^2 3^2\), and \(24^2\).

## Entangling-gate counts [paper_fact]
Fact ID: corcoles-entangling-counts
Source locator: Main-text class-count paragraph, PDF p. 1; supplement decomposition discussion, PDF p. 8
PDF page: 8
Claim: The local, CNOT-like, iSWAP-like, and SWAP classes use zero, one, two, and three CNOTs, respectively, in the source's optimal CNOT-count decomposition.

The supplement also gives device-specific replacements using the paper's
\(ZX_{-\pi/2}\) gate.

## Average CNOT count [paper_fact]
Fact ID: corcoles-average-cnot
Source locator: Main-text final sentence of class-count paragraph, PDF p. 1; supplement paragraph following the four classes, PDF p. 8
PDF page: 8
Claim: Weighting the four CNOT costs by the source's exhaustive class counts gives an average of 1.5 CNOTs per uniformly selected two-qubit Clifford.

This is a compilation statistic for the full Clifford group, not a PEPS bond
or truncation statistic.

## No fixed-input quotient theorem [literature_gap]
Fact ID: corcoles-gap-fixed-input
Source locator: Full supplement decomposition section, PDF pages 8–9
PDF page: 8
Claim: This source does not prove that local gates before an entangling core may be discarded when optimizing an objective \(f(U\lvert\psi\rangle)\) for a fixed input state.
Gap scope: source_local

It also does not identify its four classes with the one-sided post-local
20-representative search used in a different exact-small construction.

## No tensor-network disentangler objective [literature_gap]
Fact ID: corcoles-gap-tensor-objective
Source locator: Full-text review boundary from Abstract through supplement, PDF pages 1–9
PDF page: 1
Claim: This source does not establish a discarded-weight, purity, Rényi-2, bond-dimension, or whole-network-fidelity objective for tensor-network disentangling.
Gap scope: source_local

## No CAPEPS instrument [literature_gap]
Fact ID: corcoles-gap-capeps-instrument
Source locator: Full-text review boundary from Abstract through supplement, PDF pages 1–9
PDF page: 1
Claim: This source does not establish a PEPS residual, CAPEPS update, selective measurement, Born branch mass, reset, conditional trajectory, syndrome Record, or Record-law fidelity.
Gap scope: source_local
