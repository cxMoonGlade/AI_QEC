+++
schema = "error_coupling_simulator.literature.note.v1"
source_id = "arxiv:quant-ph/0511069"
source_version = "v4"
source_uri = "https://arxiv.org/abs/quant-ph/0511069v4"
source_artifact = "docs/papers/quant-ph_0511069v4.pdf"
source_sha256 = "a1c7089d9f2059ea57c17a90a07e458ea90dc37f49f2d8c3db7e2019caddb371"
title = "Simulating quantum computation by contracting tensor networks"
publication_status = "preprint"
read_status = "complete"
evidence_status = "persisted"
review_scope = "full_text"
operation_replay_status = "complete"
audit_packet = "docs/simulator_validation/MARKOV_SHI_QUANT_PH_0511069V4_TREEWIDTH_AUDIT_2026-08-03.md"
audit_packet_sha256 = "99cd0172d2040a0a4ce0ed3b9ba7cf30b328029470fe7db6da8e162040de0cc0"
admission_status = "source_only_reviewed"
admission_reviewer = "independent-markov-shi-0511069v4-source-review-2026-08-03"
admission_date = "2026-08-03"
visually_checked_pages = [1, 5, 6, 7, 8, 9, 10, 11, 12, 14, 15, 16]

[[relations]]
predicate = "defines"
object_id = "markov-shi-treewidth"
object_type = "concept"
object_label = "treewidth"
fact_id = "markov-shi-treewidth-definition"

[[relations]]
predicate = "defines"
object_id = "markov-shi-circuit-graph"
object_type = "model"
object_label = "graph of a quantum circuit"
fact_id = "markov-shi-circuit-graph-definition"

[[relations]]
predicate = "derives"
object_id = "markov-shi-contraction-complexity"
object_type = "concept"
object_label = "contraction complexity"
fact_id = "markov-shi-line-graph-equivalence"

[[relations]]
predicate = "derives"
object_id = "markov-shi-width-cost-law"
object_type = "theorem"
object_label = "computed deterministically"
fact_id = "markov-shi-simulation-cost"
+++
# Full-text review — Markov and Shi, tensor contraction and treewidth

## Source identity [paper_fact]
Fact ID: markov-shi-source-identity
Source locator: Title page, author block, abstract, and arXiv version line
PDF page: 1
Claim: The reviewed source is the arXiv v4 preprint quant-ph/0511069v4 by Igor Markov and Yaoyun Shi, dated 19 June 2007, titled "Simulating quantum computation by contracting tensor networks".

The fixed artifact contains 21 PDF pages.  It studies classical simulation of
bounded-arity quantum circuits through tensor-network contraction and relates
the cost to graph width parameters.

## Tree-decomposition definition [paper_fact]
Fact ID: markov-shi-treewidth-definition
Source locator: Sec. 2, paragraph "Treewidth of a graph", conditions T1–T3 and the following width definition
PDF page: 5
Claim: A tree decomposition assigns graph-vertex bags to nodes of a tree so that every graph vertex occurs, every graph edge has both endpoints in a bag, and the bags containing any fixed graph vertex form a connected subtree; its width is maximum bag size minus one and graph treewidth is the minimum such width.

The paper gives trees as treewidth-one examples and cycles of length at least
three as treewidth-two examples.  These examples are illustrative, not a
replacement for the minimization in the definition.

## Elimination width equals treewidth [paper_fact]
Fact ID: markov-shi-elimination-width
Source locator: Sec. 2, paragraph after Fig. 1 defining elimination ordering and induced width
PDF page: 6
Claim: In the elimination process, each removed vertex first has its remaining neighbors connected; the width of an ordering is the maximum remaining-neighbor count at removal, and the minimum induced width over orderings is precisely the graph's treewidth.

A width obtained from one chosen order is therefore an upper bound on the
minimum unless optimality is established independently.

## Quantum-circuit graph [paper_fact]
Fact ID: markov-shi-circuit-graph-definition
Source locator: Sec. 2, final paragraph before Sec. 3
PDF page: 7
Claim: The graph of a quantum circuit (C), denoted (G_C), is obtained by treating each gate as a vertex, adding a vertex at every open input/output wire endpoint, and representing every wire segment as a graph edge.

The source assumes a constant bound on gate arity.  Input and output endpoint
vertices later carry the initial states and terminal measurement or trace-out
operators.

## Tensor-network definition and contraction [paper_fact]
Fact ID: markov-shi-tensor-network
Source locator: Sec. 3, Definition 3.3 and Eq. (1), PDF pp. 8–9
PDF page: 8
Claim: A tensor network is a collection of tensors whose indices are each used by one or two tensors, and contracting shared indices replaces two incident tensors by the tensor obtained by summing their product over those shared indices.

An index used once is an open wire and an index used twice is an edge.  Complete
contraction of a closed network produces a rank-zero tensor, namely a scalar.

## Open-wire contraction retains a tensor [paper_fact]
Fact ID: markov-shi-open-wire-tensor
Source locator: Sec. 3, paragraph following Eq. (1), PDF p. 8
PDF page: 8
Claim: A tensor network with (k) open wires can be contracted to a single tensor of rank (k), and the result is independent of contraction order.

Thus the formalism is not intrinsically limited to closed scalar networks.
Closing all input and measurement wires is a choice made for the
fixed-scenario probability construction below.

## Fixed measurement-scenario probability [paper_fact]
Fact ID: markov-shi-fixed-scenario-probability
Source locator: Sec. 3, Definition 3.4 and Proposition 3.5
PDF page: 9
Claim: Attaching tensors for a fixed computational-basis input and a fixed terminal measurement scenario to the circuit tensor network yields a closed network whose complete contraction is the probability that the specified measurement scenario occurs.

The measurement scenario assigns a single-qubit POVM element to each output
qubit, with the identity used for an unmeasured qubit.  The proposition concerns
one specified scenario rather than an explicitly materialized joint table of
all scenarios.

## Intermediate-rank contraction cost [paper_fact]
Fact ID: markov-shi-rank-cost
Source locator: Sec. 3, Proposition 3.6
PDF page: 10
Claim: For a size-(T) circuit tensor network and a specified wire-contraction order, if (d) is the maximum rank of any intermediate tensor, the contraction takes (O(T\exp[O(d)])) time.

The result makes the contraction order load-bearing: different orders leave
the final scalar invariant but may produce different maximum intermediate
ranks.

## Contraction complexity and line-graph treewidth [paper_fact]
Fact ID: markov-shi-line-graph-equivalence
Source locator: Sec. 4, Definition 4.1 and Proposition 4.2
PDF page: 10
Claim: The contraction complexity (cc(G)) is the minimum, over edge-contraction orders, of the maximum degree of a merged vertex, and Proposition 4.2 states (cc(G)=tw(G^*)) for the line graph (G^*).

PDF page 11 proves the correspondence between contracting an edge of (G) and
eliminating the corresponding vertex of its line graph.  A tree decomposition
of (G^*) can be converted to a contraction order whose complexity is no
larger than the decomposition width.

## Bounded-degree comparison of width parameters [paper_fact]
Fact ID: markov-shi-bounded-degree-width
Source locator: Sec. 4, Lemma 4.4 and Theorem 4.5
PDF page: 11
Claim: For graph maximum degree (Δ(G)), the source bounds line-graph treewidth by ((tw(G)-1)/2\le tw(G^*)\le Δ(G)(tw(G)+1)-1), so circuit-graph treewidth and contraction complexity are within constant factors for bounded-degree graph families.

The bound does not make the two quantities numerically identical.  Direct
contraction complexity remains the exact line-graph treewidth in Proposition
4.2.

## Width-dependent deterministic simulation [paper_fact]
Fact ID: markov-shi-simulation-cost
Source locator: Sec. 4, Theorem 4.6 and its four-step proof
PDF page: 12
Claim: Given a bounded-arity quantum circuit, fixed computational-basis input, and fixed terminal measurement scenario, the scenario probability can be computed deterministically in circuit-size polynomial time multiplied by an exponential in contraction complexity, equivalently by an exponential in circuit-graph treewidth up to the bounded-degree relation.

The proof constructs the closed tensor network, obtains a tree decomposition of
its line graph, derives a contraction order, and contracts to the scalar
probability.  It provides a cost upper bound and no claim that every circuit
family has small width.

## Adaptive sequential measurement sampling [paper_fact]
Fact ID: markov-shi-adaptive-sequential-sampling
Source locator: Sec. 6, Lemmas 6.1–6.2 and the three-step simulation procedure, PDF pp. 14–16
PDF page: 15
Claim: For a one-way computation, the randomized simulation maintains the probability of the realized measurement prefix, recomputes a fixed-scenario extension probability, and samples the next bit with conditional probability (p_t^0/p_{t-1}), producing the correct adaptive measurement-outcome distribution with width-dependent cost.

This algorithm repeatedly calls fixed-scenario contractions instead of
materializing a joint table.  In the oblivious case, the source gives a
deterministic ratio construction for the final output probability.

## No retained full-Record graph [literature_gap]
Fact ID: markov-shi-gap-retained-record-graph
Source locator: Full-text review boundary PDF pp. 1–21; positive open-wire, fixed-scenario, and adaptive-sampling scopes in Sec. 3, PDF pp. 8–10, and Sec. 6, Lemmas 6.1–6.2, PDF pp. 14–16
PDF page: 15
Claim: This source does not define a constrained tensor or primal graph that retains every multi-round detector and logical-observable output simultaneously as a complete Record-law object.
Gap scope: source_local

The source explicitly allows open wires to remain as a rank-(k) tensor and can
sample adaptive sequences by repeated fixed-scenario probability evaluations.
The narrower missing item is a specific graph construction that simultaneously
retains the complete multi-time detector/observable joint law; the paper is not
limited to one scalar contraction in all uses.

## No persistent declared-error graph [literature_gap]
Fact ID: markov-shi-gap-persistent-error
Source locator: Full-text review boundary PDF pp. 1–21; operation and circuit-model scopes in Secs. 1–2, PDF pp. 2 and 6–7
PDF page: 7
Claim: This source does not define a caller-declared coherent latent error variable that persists across QEC rounds, nor does it report treewidth for such a model.
Gap scope: source_local

The general gate formalism can represent bounded-arity quantum operations, but
the particular persistent-memory factor and its connection to every repeated
error location are not a source construction.
