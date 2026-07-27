# Source-only claim audit — Córcoles et al., arXiv:1210.7011v2

Date: 2026-07-27

Source artifact: `docs/papers/1210.7011v2.pdf`

Source SHA-256:
`d0d52308fa0e23e7a8a10eab0291c3d02a9b28cb94893375d36693a602b1543f`

Read status: `complete`

Evidence status: `persisted`

Independent review status: `passed`

Review basis:
`docs/simulator_validation/CORCOLES_1210_7011_INDEPENDENT_SOURCE_REREVIEW_2026-07-27.md`

Admission reviewer: `corcoles_independent_source_rereview_2026_07_27`

The nine-page source, including its four-page supplement, was traversed in
full. PDF pages 1, 8, and 9 were rendered and visually inspected for source
identity, the four two-qubit-Clifford decomposition classes, their
cardinalities, the local factors, and the entangling-gate counts. Text
extraction was used only for navigation.

## Source-identity anomaly

The PDF footer identifies the artifact as `arXiv:1210.7011v2 [quant-ph]
2 Nov 2012`, while the title page and repeated supplement title page contain
the incompatible line `Dated: November 27, 2024`. The official
[arXiv v2 version history](https://arxiv.org/abs/1210.7011v2) identifies v2 as
2 November 2012. The official
[APS DOI record](https://journals.aps.org/pra/abstract/10.1103/PhysRevA.87.030301)
identifies the published paper as *Physical Review A* 87, 030301(R), received
24 October 2012 and published 19 March 2013. The 2024 date is therefore
retained as an unexplained artifact-level anomaly and is not used as
bibliographic evidence. The scientific claims below are bound to the exact PDF
hash above and to visually checked content.

## Assigned closure rows

| row | source location | source says | source does not say | status |
|---|---|---|---|---|
| two-qubit Clifford partition | main text, PDF p. 1; supplement, PDF p. 8 | The 11,520 two-qubit Clifford operations are divided into four decomposition classes with cardinalities 576, 5,184, 5,184, and 576. | The paper does not formulate the partition using explicit left-, right-, or double-coset notation. | `closed` for the stated four-class decomposition |
| canonical class forms | supplement, PDF p. 8 | The classes have local, CNOT-like, iSWAP-like, and SWAP canonical cores, with arbitrary single-qubit Clifford factors before the core and the displayed restricted post-rotations where applicable. | It does not establish that an arbitrary quotient convention used by this project preserves a fixed-input objective. | `closed` for the displayed source decomposition; `missing` for project quotient equivalence |
| class counts | supplement, PDF p. 8 | With \(\lvert\mathcal C_1\rvert=24\) and \(\lvert\mathcal S_1\rvert=3\), the class counts are \(24^2\), \(24^2 3^2\), \(24^2 3^2\), and \(24^2\). | It does not give a 20-element one-sided post-local representative catalogue. | `closed` |
| entangling-gate cost | main text, PDF p. 1; supplement, PDF pp. 8--9 | The four classes use zero, one, two, and three CNOTs respectively, producing an average of 1.5 CNOTs over the complete group. | This hardware compilation cost is not a tensor-network truncation, purity, or disentangling objective. | `closed` |
| fixed-input disentangler quotient | full source scope, especially supplement decomposition | The source supplies a hardware-oriented partition of the entire two-qubit Clifford group. | It does not prove that pre-local gates can be removed when optimizing \(f(U\lvert\psi\rangle)\) for a fixed input, nor that double-sided local equivalence is interchangeable with a one-sided post-local quotient. | `missing` |
| CAPEPS and measurement--reset--Record | full source scope | The source studies randomized benchmarking and Clifford compilation for two superconducting qubits. | It does not define a PEPS residual, CAPEPS update, selective Born branch, reset, raw-history mass, detector Record, or Record-law metric. | `missing` |

## Notation ledger

| symbol | source meaning | type / range | fixed or variable | exact source location |
|---|---|---|---|---|
| \(\mathcal C\) | Clifford group, defined as the normalizer of the Pauli group | unitary group modulo the source's phase convention | fixed gate family | main text, PDF p. 1 |
| \(\mathcal C_1\) | single-qubit Clifford group | 24 elements | fixed local group | supplement, PDF p. 8 |
| \(\mathcal S_1=\{I,R_S,R_S^2\}\) | three-element group cycling the Bloch-sphere axes | 3 local operations | fixed restricted post-rotation set | supplement, PDF p. 8 |
| local class | independent \(\mathcal C_1\) gates on the two qubits | \(24^2=576\) elements | class | supplement, PDF p. 8 |
| CNOT-like class | displayed local--CNOT--\(\mathcal S_1\) sequence | \(24^2 3^2=5{,}184\) elements | class | supplement, PDF p. 8 |
| iSWAP-like class | displayed local--iSWAP-like--\(\mathcal S_1\) sequence | \(24^2 3^2=5{,}184\) elements | class | supplement, PDF p. 8 |
| SWAP class | displayed local--SWAP sequence | \(24^2=576\) elements | class | supplement, PDF pp. 8--9 |

## Operation replay

| input | transformation | assumption | output | exact source location | replay status |
|---|---|---|---|---|---|
| two independent \(\mathcal C_1\) choices | Apply only the local gates. | \(\lvert\mathcal C_1\rvert=24\). | \(24^2=576\) local-class operations | supplement, PDF p. 8 | `closed` |
| two \(\mathcal C_1\) choices, a CNOT core, and two \(\mathcal S_1\) choices | Compose the displayed sequence. | The displayed choices enumerate the CNOT-like class without additional multiplicity. | \(24^2 3^2=5{,}184\) CNOT-like operations | supplement, PDF p. 8 | `closed` |
| two \(\mathcal C_1\) choices, the paper's iSWAP-like core, and two \(\mathcal S_1\) choices | Compose the displayed sequence. | The displayed choices enumerate the iSWAP-like class without additional multiplicity. | \(24^2 3^2=5{,}184\) iSWAP-like operations | supplement, PDF p. 8 | `closed` |
| two \(\mathcal C_1\) choices and a SWAP core | Compose the displayed sequence. | The displayed choices enumerate the SWAP class. | \(24^2=576\) SWAP-class operations | supplement, PDF p. 8 | `closed` |
| the four class counts | Sum the cardinalities. | The four source classes are disjoint and exhaustive as stated. | \(576+5{,}184+5{,}184+576=11{,}520\) operations | main text, PDF p. 1; supplement, PDF p. 8 | `closed` |
| the four class counts and CNOT costs \(0,1,2,3\) | Compute the uniform-group average. | Every group element is weighted once. | \((0\cdot576+1\cdot5{,}184+2\cdot5{,}184+3\cdot576)/11{,}520=1.5\) CNOTs | main text, PDF p. 1; supplement, PDF p. 8 | `closed` |

## Paper claim versus project inference

The paper directly supports a four-class decomposition of all two-qubit
Cliffords and gives concrete pre-\(\mathcal C_1\)/core circuit forms, with
restricted post-\(\mathcal S_1\) factors for the CNOT-like and iSWAP-like
classes. Because all displayed decorations around each core are single-qubit
operations, the decomposition is relevant background for local-equivalence
classification.
However, the source never defines a quotient symbol or proves equality to the
project's fixed-input search space. Calling these four classes *the project's
double quotient*, or using them to replace a one-sided 20-representative
post-local search, is a project inference and is not admitted from this source.

In particular, a fixed input \(\lvert\psi\rangle\) need not be invariant under
arbitrary local Cliffords placed before the entangling core. Córcoles et al.
do not address that objective. The source therefore supports a warning about
quotient conventions, not the project's exact-small candidate reduction by
itself.

## Competing evidence and kill conditions

- Chang et al. supply the separate one-sided post-local 20-representative
  construction used by the exact-small qubit lane; that result cannot be
  replaced by the four Córcoles classes.
- Masot-Llima and Garcia-Saez, arXiv:2602.15942v2, must be read independently
  before using a double-sided local-equivalence statement as a no-go or
  falsifier.
- A project sentence asserting “Córcoles proves the exact fixed-input search
  has four candidates” is killed by the source's lack of a fixed-input
  objective and explicit quotient convention.
- Any transfer from the reported 1.5-CNOT compilation average to PEPS bond,
  runtime, memory, or Record-law efficiency is killed unless a separate
  target experiment makes and validates that bridge.

## Source-local verdict

- `read_status: complete`
- `evidence_status: persisted`
- `independent_source_review: passed`
- `review_basis: CORCOLES_1210_7011_INDEPENDENT_SOURCE_REREVIEW_2026-07-27.md`
- four-class full-group decomposition: `closed`
- class cardinalities and 11,520 total: `closed`
- 1.5-CNOT compilation average: `closed`
- explicit double-coset theorem: `missing`
- equality to a fixed-input or one-sided quotient search: `missing`
- CAPEPS or measurement--reset--Record evidence: `missing`
- title-page 2024 date: `anomalous_not_used`
