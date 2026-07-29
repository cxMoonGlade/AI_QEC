+++
schema = "error_coupling_simulator.literature.note.v1"
source_id = "arxiv:1805.09626"
source_version = "v2"
source_uri = "https://arxiv.org/abs/1805.09626v2"
source_artifact = "docs/papers/1805.09626v2.pdf"
source_sha256 = "619f3a5fe047481ef1fc434255e63e0ca3428ca594805a34d9897ec0e9fb4fd5"
title = "System-environment correlations and Markovian embedding of quantum non-Markovian dynamics"
publication_status = "preprint"
read_status = "complete"
evidence_status = "persisted"
review_scope = "full_text"
operation_replay_status = "complete"
audit_packet = "docs/simulator_validation/CAMPBELL_1805_09626V2_MEMORY_DEPTH_AUDIT_2026-07-29.md"
audit_packet_sha256 = "364ca4438a1d8ddabb06c87cf54e36499cc93c3414afdc11a438a7b3016e1916"
admission_status = "source_only_reviewed"
admission_reviewer = "campbell-round2-independent-source-review"
admission_date = "2026-07-29"
visually_checked_pages = [1, 2, 3, 5, 6, 7, 9]

[[relations]]
predicate = "defines"
object_id = "collision-memory-depth"
object_type = "model"
object_label = "memory depth"
fact_id = "campbell-memory-depth-definition"

[[relations]]
predicate = "defines"
object_id = "xyz-collision-hamiltonian"
object_type = "model"
object_label = "collision Hamiltonian"
fact_id = "campbell-collision-hamiltonian"

[[relations]]
predicate = "supports"
object_id = "finite-memory-markovian-embedding"
object_type = "method"
object_label = "Markovian embedding"
fact_id = "campbell-first-order-embedding"
+++
# Full-text review — Campbell et al., “System-environment correlations and Markovian embedding of quantum non-Markovian dynamics”

## Source identity [paper_fact]
Fact ID: campbell-source-identity
Source locator: Title page and arXiv version line
PDF page: 1
Claim: The reviewed object is the eleven-page arXiv:1805.09626v2 preprint titled “System-environment correlations and Markovian embedding of quantum non-Markovian dynamics.”

The PDF displays arXiv:1805.09626v2 [quant-ph] 10 Jul 2018 and is dated July 11, 2018.

## Selection scope [paper_fact]
Fact ID: campbell-selection-scope
Source locator: Abstract and Sec. I
PDF page: 1
Claim: The source relates finite-range ancilla–ancilla collision memory to a finite Markovian embedding of the reduced system dynamics.

## Factorized initial state [paper_fact]
Fact ID: campbell-factorized-input
Source locator: Sec. II, Eq. (1)
PDF page: 2
Claim: The collision model starts from a tensor product of the system state and all ancilla states, with no initial system–environment or ancilla–ancilla correlations.

## Collision Hamiltonian [paper_fact]
Fact ID: campbell-collision-hamiltonian
Source locator: Sec. II, Eq. (2)
PDF page: 2
Claim: The source defines a pairwise collision Hamiltonian \(-\frac12(J_xXX+J_yYY+J_zZZ)\) for either a system–ancilla pair or an ancilla–ancilla pair.

## Isotropic partial-SWAP case [paper_fact]
Fact ID: campbell-isotropic-partial-swap
Source locator: Sec. II, paragraph following Eq. (4)
PDF page: 2
Claim: When \(J_x=J_y=J_z=J\), the source identifies the collision unitary as \(\cos(J\tau)I-i\sin(J\tau)\hat S\), a partial SWAP.

## System-collision block indices [paper_fact]
Fact ID: campbell-system-collision-blocks
Source locator: Sec. II, Eqs. (3)–(4)
PDF page: 2
Claim: The source's first step collides \(S\) with \(E_1,\ldots,E_d\), while the system-collision block at step \(n>1\) is \(E_{(n-1)d+1},\ldots,E_{nd}\).

## Ancilla-collision block and order [paper_fact]
Fact ID: campbell-aa-collision-block
Source locator: Sec. II, Eq. (4) and following paragraph
PDF page: 2
Claim: At step \(n>1\), the printed ancilla–ancilla block uses pairs \(l<m\) with indices from \((n-2)d+1\) through \((n-1)d+1\), and the source permits arbitrary ordering among those pairwise interactions.

## Memoryless limit [paper_fact]
Fact ID: campbell-memoryless-limit
Source locator: Sec. II, paragraph spanning PDF pp. 2–3 after Eq. (4)
PDF page: 2
Claim: Removing ancilla–ancilla collisions gives the source's fresh-ancilla memoryless collision model.

## Perfect-AA-SWAP limit [paper_fact]
Fact ID: campbell-perfect-aa-swap-limit
Source locator: Sec. II, paragraph at the top of PDF p. 3
PDF page: 3
Claim: In the perfect ancilla–ancilla SWAP limit, the source says that \(S\) behaves as if it interacts with the same ancilla at all times.

## Trace-distance diagnostic [paper_fact]
Fact ID: campbell-trace-distance
Source locator: Sec. III, Eq. (5) and following paragraphs
PDF page: 3
Claim: A nonmonotonic trace-distance trajectory for at least one initial pair is sufficient for the source's BLP non-Markovian diagnosis, while monotonic decay for one selected pair is inconclusive.

## Memory-depth definition [paper_fact]
Fact ID: campbell-memory-depth-definition
Source locator: Sec. V opening paragraph
PDF page: 5
Claim: The source reinterprets the ancilla–ancilla interaction range \(d\) as the memory depth.

## Enlarged-system size [paper_fact]
Fact ID: campbell-embedding-size
Source locator: Sec. I final paragraph continuing on PDF p. 2
PDF page: 2
Claim: For the source's collision model, the composite enlarged system contains \(S\) plus as many ancillas as the memory depth \(d\).

## First-order Markovian embedding [paper_fact]
Fact ID: campbell-first-order-embedding
Source locator: Sec. V, Eqs. (7)–(10)
PDF page: 5
Claim: For \(d=1\), the joint state of \(S\) and the advancing last-collided ancilla evolves through a composition of CPTP maps that is a Markovian embedding of the generally non-Markovian reduced \(S\) map.

The retained label changes from \(E_{n-1}\) to \(E_n\) at each step.

## Explicit second-order embedding [paper_fact]
Fact ID: campbell-second-order-embedding
Source locator: Sec. V, unnumbered second-order step maps, Eq. (11), and the reduced-map equation immediately following it
PDF page: 5
Claim: For \(d=2\), the source explicitly constructs a CPTP evolution of \(S\) plus two advancing ancillas and obtains the reduced map by tracing the last two collided ancillas.

## Arbitrary-depth enlarged-state extension [paper_fact]
Fact ID: campbell-arbitrary-depth-extension
Source locator: Sec. V, paragraph following Eq. (11)
PDF page: 5
Claim: The source states that the memory-depth construction naturally extends to arbitrary \(d\).

The source does not print a general numbered \(\Phi^{(d)}\) or \(\Lambda^{(d)}\) equation.

## Swap identities for fixed memory [paper_fact]
Fact ID: campbell-fixed-memory-swap-identities
Source locator: Sec. V, Eqs. (15)–(16)
PDF page: 6
Claim: The source uses partial-trace invariance under a swap and a swap–collision commutation identity to relabel a moving ancilla interaction onto a fixed memory ancilla.

## Fixed-memory first-order equivalence [paper_fact]
Fact ID: campbell-fixed-memory-first-order
Source locator: Sec. V, Eq. (17) and its reduction to Eq. (14) at the top of the following page
PDF page: 6
Claim: For \(d=1\), the source derives a reduced-dynamics representation in which \(S\) repeatedly interacts with fixed memory ancilla \(E_1\), and proves it equivalent to the original nearest-neighbor stream.

Fresh ancillas, memory–fresh-ancilla collisions, swaps, index relabelling, and partial traces are
parts of this representation.

## Fixed-memory second-order equivalence [paper_fact]
Fact ID: campbell-fixed-memory-second-order
Source locator: Sec. V, Eq. (18) and following paragraph
PDF page: 7
Claim: For \(d=2\), the source states that a representation using two fixed memory ancillas is equivalent to the original second-order reduced dynamics in Eq. (13).

## Arbitrary-depth fixed-memory analogue [paper_fact]
Fact ID: campbell-fixed-memory-arbitrary-depth
Source locator: Sec. V, paragraph following Eq. (18)
PDF page: 7
Claim: The source states that a similar fixed-memory approach can be used for arbitrary \(d\).

This is an analogous-extension statement rather than a separately printed general equation.

## Fixed-memory scheduling qualification [paper_fact]
Fact ID: campbell-fixed-memory-scheduling
Source locator: Sec. V, final paragraph
PDF page: 7
Claim: The same-fixed-ancilla SWAP construction requires \(S\) to interact with the whole memory before intra-environment collisions occur.

If AA collisions instead occur after each individual \(S\)-ancilla collision, the source says that
the last \(d\) ancillas still contain the relevant correlations but that the SWAP construction no
longer ensures interaction with the same ancillas throughout.

## Generality limitation [paper_fact]
Fact ID: campbell-generality-limit
Source locator: Sec. VII, final two paragraphs
PDF page: 9
Claim: The source states that it is not known whether arbitrary non-Markovian dynamics admit the same collision-model construction.

## Unsupported PEPS contraction guarantee [literature_gap]
Fact ID: campbell-gap-peps-contraction
Source locator: Scientific body, PDF pp. 1–9
PDF page: 1
Claim: This source does not establish a PEPS contraction guarantee.
Gap scope: source_local

## Unsupported tensor-network truncation guarantee [literature_gap]
Fact ID: campbell-gap-tensor-network-truncation
Source locator: Scientific body, PDF pp. 1–9
PDF page: 1
Claim: This source does not establish a tensor-network truncation guarantee.
Gap scope: source_local

## Unsupported runtime guarantee [literature_gap]
Fact ID: campbell-gap-runtime
Source locator: Scientific body, PDF pp. 1–9
PDF page: 1
Claim: This source does not establish a runtime guarantee for a tensor-network simulation.
Gap scope: source_local

## Unsupported bond-dimension guarantee [literature_gap]
Fact ID: campbell-gap-bond-dimension
Source locator: Scientific body, PDF pp. 1–9
PDF page: 1
Claim: This source does not establish a tensor-network bond-dimension guarantee.
Gap scope: source_local

## Unsupported monotonic-entanglement guarantee [literature_gap]
Fact ID: campbell-gap-monotonic-entanglement
Source locator: Scientific body, PDF pp. 1–9
PDF page: 1
Claim: This source does not establish that entanglement increases monotonically with collision step or round.
Gap scope: source_local
