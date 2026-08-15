# Claim audit — Markov and Shi, circuit tensor contraction and treewidth

## Status and decision

This packet audits the arXiv v4 preprint quant-ph/0511069 only for the
definition and interpretation of the treewidth meter in the no-cutoff
structure census. The fixed source artifact is
`docs/papers/quant-ph_0511069v4.pdf`, SHA-256
`a1c7089d9f2059ea57c17a90a07e458ea90dc37f49f2d8c3db7e2019caddb371`.
All 21 pages were read; PDF pages 1, 5–12, and 14–16 were visually checked.
Independent round-two source-only review passed under reviewer ID
`independent-markov-shi-0511069v4-source-review-2026-08-03`.

The source closes the graph-theoretic definitions and the fixed-output
tensor-contraction bridge. Treewidth is the minimum, over tree decompositions,
of maximum bag size minus one, equivalently the minimum elimination width. For
a tensor-network multigraph `G`, the source's edge-at-a-time contraction
complexity is exactly the treewidth of its line graph `G*`. For a bounded-degree
quantum-circuit graph, the source relates these widths within constant factors
and derives fixed-scenario probability computation in circuit-size polynomial
time multiplied by an exponential in width.

The source is not limited to scalars. It says that a network with `k` open wires
can contract to a rank-`k` tensor, and Sec. 6 samples adaptive measurement
sequences by repeated fixed-scenario contractions. What remains source-locally
missing is the particular graph that simultaneously retains the complete
multi-round detector/observable joint law, and the graph augmentation for one
persistent coherent latent variable connected across repeated error locations.

## Assigned closure rows

| row | exact source location | source says | source does not say | status |
|---|---|---|---|---|
| Treewidth | Sec. 2, "Treewidth of a graph", conditions T1–T3, PDF p. 5 | Treewidth is the minimum over tree decompositions of maximum bag size minus one. | No heuristic decomposition is identified with exact treewidth. | closed |
| Elimination form | Sec. 2, paragraph after Fig. 1, PDF p. 6 | Minimum induced/elimination width equals treewidth. | One chosen elimination order supplies only an upper bound unless optimality is established. | closed |
| Circuit graph | Sec. 2, final paragraph, PDF p. 7 | Gates are vertices, input/output endpoints are vertices, and wire segments are graph edges. | The graph does not include a retained classical output or persistent-latent construction unless one is explicitly represented. | closed |
| Tensor index domain and open output | Sec. 3, Defs. 3.1–3.3 and paragraph after Eq. (1), PDF pp. 7–8 | Qubit density-operator/superoperator wire indices use a fixed four-element operator basis; a network with `k` open wires can contract to a rank-`k` tensor. | An open tensor is not automatically the requested folded detector/observable PMF. | closed |
| Fixed-output tensor scalar | Sec. 3, Defs. 3.3–3.4 and Prop. 3.5, PDF pp. 8–9 | Attaching a fixed input and measurement scenario yields a closed tensor network whose complete contraction is that scenario's probability. | The proposition computes one selected scenario, not a materialized complete joint Record PMF. | closed |
| Parallel numerical contraction | Sec. 3, Eq. (1), PDF p. 8 | All parallel shared indices between two tensors are summed in one numerical contraction. | This numerical operation is not identical to the edge-at-a-time graph convention later used to define `cc(G)`. | closed |
| Contraction complexity | Sec. 4, Def. 4.1 and Prop. 4.2, PDF pp. 10–11 | The edge-at-a-time graph process retains loops, and its minimum peak merged-vertex degree satisfies `cc(G)=tw(G*)`. | The equality is not a statement that `tw(G*)` is the exact peak rank of the parallel numerical contraction. | closed |
| Parallel-to-edge bridge | Sec. 4, paragraph before Def. 4.1, PDF p. 10 | Edge-at-a-time contraction can emulate the parallel contraction while increasing the maximum observed vertex degree by no more than a factor of two. | The bridge supports asymptotic exponential-width cost, not numerical equality of the two peak quantities. | closed |
| Simulation cost | Sec. 3, Prop. 3.6, PDF p. 10; Sec. 4, Thm. 4.6 and proof, PDF pp. 11–12 | A fixed scenario probability can be computed in circuit-size polynomial time times an exponential in contraction complexity, equivalently exponential in circuit-graph treewidth for bounded degree. | It proves no small-width result for the requested QEC family. | closed |
| Adaptive measurement sequence | Sec. 6, Lemmas 6.1–6.2, PDF pp. 14–16 | Repeated fixed-scenario probabilities and the ratio `p_t^0/p_{t-1}` sample each next adaptive outcome with the correct distribution. | The algorithm does not construct one retained graph or materialized table for the complete multi-time outcome law. | closed |
| Full retained Record graph | Full-text review boundary PDF pp. 1–21, especially Secs. 3–4 and 6, PDF pp. 8–16 | The source permits open tensors, fixed-scenario probabilities, and adaptive sequential sampling. | It does not define the constrained graph for a complete multi-round detector/observable Record law. | missing source-locally |
| Persistent-latent graph | Full-text review boundary PDF pp. 1–21, especially Secs. 1–2, PDF pp. 2 and 6–7 | The circuit formalism supports bounded-arity quantum operations and general circuit wiring. | It does not define one coherent latent error variable reused across QEC rounds or report the augmented graph width. | missing source-locally |

## Operation replay

| input | transformation | assumption | output | exact source location | replay status |
|---|---|---|---|---|---|
| Quantum circuit, fixed computational-basis input, and fixed measurement scenario | Replace states, gates, and measurement elements by tensors and join each qubit wire segment through an index | Gate arity is bounded; each qubit density-operator/superoperator wire index has the fixed four-element operator basis of Defs. 3.1–3.2 | Closed tensor network whose scalar is the specified scenario probability | Sec. 3, Defs. 3.1–3.4 and Prop. 3.5, PDF pp. 7–9 | complete |
| Tensor network with `k` deliberately open wires | Contract all internal wires while retaining the open indices | Each index occurs in one tensor (open) or two tensors (internal) | One rank-`k` tensor independent of contraction order | Sec. 3, paragraph following Eq. (1), PDF p. 8 | complete |
| Two tensors joined by multiple shared indices | Sum all parallel shared indices together according to Eq. (1) | Parallel numerical contraction removes all shared edges in one operation | Merged tensor used by Prop. 3.6's rank-cost process | Sec. 3, Eq. (1) and Prop. 3.6, PDF pp. 8–10 | complete |
| Tensor-network multigraph `G` | Instead contract one edge at a time, retain resulting loops, form `G*`, and use the edge/elimination correspondence | The edge-at-a-time convention can emulate parallel contraction with at most a factor-two increase in observed degree | Exact graph identity `cc(G)=tw(G*)` for the edge-at-a-time process; a width-bounded contraction order follows from a tree decomposition | Sec. 4, paragraph before Def. 4.1 and Prop. 4.2 with proof, PDF pp. 10–11 | complete |
| Width-controlled graph contraction and tensor network | Translate the graph order back to numerical contractions | Parallel and edge-at-a-time peaks are related only up to the stated constant-factor bridge | Fixed-scenario scalar in polynomial-size times exponential-width time, not an exact equality between width and numerical peak rank | Sec. 3, Prop. 3.6, and Sec. 4, Thm. 4.6, PDF pp. 10–12 | complete |
| Previously realized adaptive measurement prefix with probability `p_(t-1)` | Build the fixed-scenario extension for outcome zero, compute `p_t^0`, and sample the next outcome using `p_t^0/p_(t-1)` | The measurement description is efficiently determined from earlier outcomes | One additional correctly distributed adaptive outcome and updated prefix probability | Sec. 6, Lemmas 6.1–6.2, PDF pp. 14–16 | complete |

## Project application

The following graph and certification rules are project choices, not results
stated by Markov and Shi.

1. Freeze one exact retained-Record tensor-network multigraph `G_record` whose
   open classical legs are every detector and logical observable in chronological
   order, and whose factors include resets, measurements, XOR folds, coherent
   error operations, and one persistent latent sign connected to every declared
   error location. Hash the complete factor incidence and labelled multigraph.
2. The headline contraction-width meter is
   `tw_line_record_network(graph_hash) = tw(G_record*) = cc(G_record)` under the
   source's edge-at-a-time convention. A primal-factor-graph width, physical
   qubit interaction width, or different line graph must use a separate name.
3. Claim `EXACT` only with a machine-checkable width-`k` decomposition of
   `G_record*` and an independently checkable lower-bound certificate of `k`.
   A deterministic elimination order or NetworkX min-fill/min-degree result is
   an upper bound only.
4. The route burden is `2^tw`, reflecting the source's polynomial-times-
   exponential width law up to constants. It is a finite-grid architecture
   burden, not an exact byte or runtime prediction.
5. Until the graph construction and matching certificates exist, emit
   `UNAVAILABLE/NO_EXACT_TREEWIDTH_OWNER`; do not serialize a heuristic width as
   zero or exact. The tensor route remains `CODE_BLOCKED`.

## Competing evidence and kill conditions

- The open-wire statement prevents the overclaim that the source can only
  produce scalars. Kill any rationale for retained-Record impossibility that
  rests on that false premise.
- Sec. 6 is a constructive rival to materializing the full joint table: it can
  sample an adaptive sequence through conditional fixed-scenario calls. Kill
  any claim that this already gives the requested exact full-law census; it
  provides samples, not the retained joint tensor and its certified TV.
- The physical circuit graph `G_C`, the retained tensor-network graph
  `G_record`, its line graph, and a constrained primal graph are distinct
  objects. Kill any result whose graph hash and convention do not identify
  which width was computed.
- A tree decomposition proves an upper bound. Kill `EXACT` if the independent
  lower certificate is absent, invalid, or refers to a different graph hash.
- Kill a bare `tw` populated by NetworkX min-fill/min-degree, by one elimination
  order, or by an implementation's peak rank. These are useful diagnostics but
  not the source definition's minimum.
- Kill the route on the preregistered finite grid only from certified burden
  intervals that prove the growth condition; resource exhaustion or an
  unmatched bound is `INDETERMINATE`, not a numerical cutoff or exact count.

## Source-local verdict

- `read_status`: complete
- `evidence_status`: persisted and independently source-only reviewed
- treewidth, elimination width, circuit/tensor graph definitions,
  fixed-scenario contraction, adaptive sequential sampling, and
  `cc(G)=tw(G*)` under the edge-at-a-time convention: `closed`
- constrained complete retained-Record tensor graph: `missing source-locally`
- persistent coherent latent graph and its treewidth: `missing source-locally`
- project graph identity, exact-certificate policy, and census disposition:
  project applications, not source claims
- downstream permission: source-note re-review and preregistration design only;
  no solver implementation or scalability claim
