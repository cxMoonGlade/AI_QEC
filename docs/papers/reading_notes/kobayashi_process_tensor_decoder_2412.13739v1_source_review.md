+++
schema = "error_coupling_simulator.literature.note.v1"
source_id = "arxiv:2412.13739"
source_version = "v1"
source_uri = "https://arxiv.org/abs/2412.13739v1"
source_artifact = "outputs/papers/2412.13739.pdf"
source_sha256 = "3d53154051bdc5a331238ba9c573ecff0237e4f52853e6f463e02090617b8ef1"
title = "Tensor-network decoders for process tensor descriptions of non-Markovian noise"
publication_status = "preprint"
read_status = "complete"
evidence_status = "persisted"
review_scope = "full_text"
operation_replay_status = "complete"
audit_packet = "docs/simulator_validation/literature_expansion/KOBAYASHI_PROCESS_TENSOR_DECODER_2412_13739_AUDIT_2026-08-05.md"
audit_packet_sha256 = "a877b5f7d9ac390334fd9a1a531174bb65a44e2af4fce2f547ebadce53902cc9"
admission_status = "source_only_reviewed"
admission_reviewer = "codex-independent-source-review-kobayashi-2026-08-05"
admission_date = "2026-08-05"
visually_checked_pages = [1, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23]

[[relations]]
predicate = "defines"
object_id = "qec-process-tensor"
object_type = "model"
object_label = "process tensor"
fact_id = "kobayashi-process-tensor-definition"

[[relations]]
predicate = "uses"
object_id = "syndrome-conditioned-tester"
object_type = "method"
object_label = "syndrome-conditioned tester"
fact_id = "kobayashi-syndrome-recovery-tester"

[[relations]]
predicate = "defines"
object_id = "process-tensor-ml-decoder"
object_type = "method"
object_label = "maximum-likelihood decoder"
fact_id = "kobayashi-ml-logical-choice"

[[relations]]
predicate = "uses"
object_id = "process-tensor-tester-mps"
object_type = "method"
object_label = "MPS approximation"
fact_id = "kobayashi-mps-computation"
+++
# Full-text review — Kobayashi et al., “Tensor-network decoders for process tensor descriptions of non-Markovian noise”

## Source identity [paper_fact]
Fact ID: kobayashi-source-identity
Source locator: Title page and arXiv version line
PDF page: 1
Claim: The reviewed object is the 27-page arXiv:2412.13739v1 preprint titled “Tensor-network decoders for process tensor descriptions of non-Markovian noise.”

The title page lists Fumiyoshi Kobayashi, Hidetaka Manabe, Gregory A. L. White, Terry
Farrelly, Kavan Modi and Thomas M. Stace, and displays the date 18 December 2024.

## Selection scope [paper_fact]
Fact ID: kobayashi-selection-scope
Source locator: Abstract and Sec. 1
PDF page: 1
Claim: The source constructs a process-tensor-conditioned maximum-likelihood decoder and evaluates exact and approximate tensor-network calculations for the five-qubit and Steane stabilizer codes under a synthetic correlated-noise model.

## Process-tensor definition [paper_fact]
Fact ID: kobayashi-process-tensor-definition
Source locator: Sec. 2.4, Eq. (17)
PDF page: 6
Claim: The source defines a process tensor as the map from a sequence of system-only CP control maps, interleaved with joint system–environment unitaries, to the conditional system output obtained after tracing the environment.

The initial system–environment state may be joint, the control maps act only on the system, and the
interleaved unitaries act on both system and environment.

## Multi-time outcomes and states [paper_fact]
Fact ID: kobayashi-multitime-outcomes
Source locator: Sec. 2.4, Eqs. (18)–(22)
PDF page: 6
Claim: Contracting the selected CP-map Choi states with the process tensor gives the joint instrument-outcome probability and the system state conditioned on the preceding outcomes and instruments.

The source distinguishes the probability, which traces the final output, from the conditional state
that retains that output space.

## Tester memory [paper_fact]
Fact ID: kobayashi-tester-memory
Source locator: Sec. 2.4, Eq. (23), Figs. 3–4 and accompanying text
PDF page: 8
Claim: A tester permits later instrument choices to depend on earlier recorded outcomes and represents the correlated operation as an instrument with common classical or ancillary memory.

## Stabilizer syndrome instruments [paper_fact]
Fact ID: kobayashi-stabilizer-instruments
Source locator: Sec. 3.1, Eqs. (24)–(27)
PDF page: 9
Claim: For an `[[n,k,d]]` stabilizer code, the source models one direct projective instrument for each of the `n-k` stabilizer generators and contracts their ordered binary outcomes with the process tensor to obtain a conditional data state.

Each projector is applied directly to the encoded data space; these equations do not introduce a
syndrome-extraction circuit of measurement ancillas.

## Syndrome-conditioned recovery tester [paper_fact]
Fact ID: kobayashi-syndrome-recovery-tester
Source locator: Sec. 3.1, Eqs. (28)–(30) and Fig. 5
PDF page: 9
Claim: The source combines the ordered syndrome measurements with a syndrome-conditioned recovery into a syndrome-conditioned tester whose classical feed-forward is enforced by Kronecker deltas on the recorded outcomes.

## Pure-error decomposition [paper_fact]
Fact ID: kobayashi-pure-error-decomposition
Source locator: Sec. 3.2, Eqs. (31)–(35)
PDF page: 10
Claim: Errors consistent with a syndrome are decomposed into a pure-error representative, a stabilizer and a logical Pauli, and recovery is reduced to choosing the logical Pauli for that syndrome.

## Maximum-likelihood logical choice [paper_fact]
Fact ID: kobayashi-ml-logical-choice
Source locator: Sec. 3.2, Eqs. (36)–(45)
PDF page: 12
Claim: The source's first maximum-likelihood decoder selects the logical operation that maximizes a Hilbert–Schmidt success objective and defines an aggregate logical-failure quantity by summing the optimized syndrome contributions.

The evaluation appends noiseless syndrome measurement and decoding before comparing the resulting
logical channel with the identity channel.

## Channel-distance objective [paper_fact]
Fact ID: kobayashi-channel-distance-objective
Source locator: Sec. 3.2, Eqs. (46)–(49) and final paragraph
PDF page: 12
Claim: The source also minimizes a logical-channel 2-norm distance for each syndrome and explicitly states that its weighted aggregate in Eq. (49) does not satisfy the strict axioms of probability.

The source names diamond distance and other p-norm distances as possible alternatives.

## Printed depolarising formula [paper_fact]
Fact ID: kobayashi-printed-depolarising-formula
Source locator: Sec. 4.1, item 1, Eq. (50)
PDF page: 14
Claim: The source prints `E_dep(rho,p_err)=(1-p_err)rho+p_err sum_{sigma in {X,Y,Z}} sigma rho sigma-dagger` and describes it as standard iid Markovian depolarising noise.

## Finite-bath interaction [paper_fact]
Fact ID: kobayashi-finite-bath-interaction
Source locator: Sec. 4.1, item 2, Eq. (51) and Fig. 7
PDF page: 14
Claim: The non-Markovian component is a Heisenberg unitary coupling each data qubit to its own local bath qubit through `XX+YY+ZZ` with strength `J_NM`.

The same bath wires continue through the sequential interaction blocks in the source's process-tensor
network.

## Crosstalk interaction [paper_fact]
Fact ID: kobayashi-crosstalk-interaction
Source locator: Sec. 4.1, item 3, Eq. (52) and Fig. 7
PDF page: 14
Claim: The crosstalk component is a nearest-neighbour data-qubit `ZZ` unitary with strength `J_CT` and is distinct from the local system–bath interaction.

## Concrete process-tensor network [paper_fact]
Fact ID: kobayashi-concrete-process-network
Source locator: Sec. 4.1, paragraph after Eq. (52), and Fig. 8(a)
PDF page: 15
Claim: The numerical process tensor is formed by sequentially applying the depolarising, local system–bath and crosstalk blocks and tracing the bath after the sequence.

## Five-qubit demonstrated interface [paper_fact]
Fact ID: kobayashi-five-qubit-interface
Source locator: Sec. 4.2 and Table 1
PDF page: 16
Claim: The first numerical instance is the `[[5,1,3]]` code with four stabilizer generators, four sequential syndrome measurements and a lookup-table logical recovery inside the full process-tensor/tester contraction.

## Exact tensor-network computation [paper_fact]
Fact ID: kobayashi-exact-tn-computation
Source locator: Sec. 4.2, first paragraph
PDF page: 16
Claim: The source implements the full five-qubit process-tensor/tester contraction in quimb, optimizes contraction order with cotengra HyperOptimizer, and reports execution on an AMD EPYC 7532 processor with an NVIDIA A100 40GB GPU.

“Exact” in the later plots and table denotes this tensor-network contraction without the MPS
truncation introduced in Sec. 4.3; the source does not report an independent implementation.

## Five-qubit reported trend [paper_fact]
Fact ID: kobayashi-five-qubit-trend
Source locator: Sec. 4.2 and Fig. 9
PDF page: 17
Claim: Figure 9 reports larger plotted logical-failure quantities as either `J_NM` or `J_CT` increases, while the text warns that a fair comparison must account for noise added by the bath coupling and that concrete statements require careful analysis.

The text also states that the logical-failure quantity is not suppressed even at `J_NM=J_CT=0`
because errors occurring after the stabilizer instrument that could detect them escape that
measurement sequence.

## MPS computation [paper_fact]
Fact ID: kobayashi-mps-computation
Source locator: Sec. 4.3.1, paragraphs following Fig. 10 and Eq. (53)
PDF page: 19
Claim: The MPS approximation orders an auxiliary index, alternating data and local-bath indices, and syndrome-classical indices, then applies MPO representations of noise and stabilizer measurements while truncating the MPS by a maximum bond dimension and a singular-value threshold.

After the sequential updates, the bath qubits are traced to produce the approximated process-tensor
and tester representation.

## MPS applicability boundary [paper_fact]
Fact ID: kobayashi-mps-applicability-boundary
Source locator: Sec. 4.3.1, final paragraphs
PDF page: 20
Claim: The source expects its MPS ordering to be most accurate for one-dimensional codes or relatively weak noise and states that it gives no guarantee for more qubits, more measurements or stronger noise.

The same passage says inaccurate representation of the initial logical Bell pair can substantially
degrade precision.

## Approximate-decoder metrics [paper_fact]
Fact ID: kobayashi-approximate-decoder-metrics
Source locator: Sec. 4.3.2, Eqs. (54)–(56)
PDF page: 20
Claim: The source distinguishes `p_est`, which evaluates the logical-failure quantity using the approximated process, from `p_perf`, which evaluates the logical choice selected from the approximation against the unapproximated process.

## Steane demonstrated scale [paper_fact]
Fact ID: kobayashi-steane-scale
Source locator: Sec. 4.3.2, paragraph after Eq. (56), Fig. 12 and Table 2
PDF page: 20
Claim: The second numerical instance is the `[[7,1,3]]` Steane code with six sequential stabilizer measurements, a singular-value cutoff of `10^-8`, MPS bond caps from 128 through 1024, and unapproximated tensor-network contraction as the source reference.

## Approximation trade-off [paper_fact]
Fact ID: kobayashi-approximation-tradeoff
Source locator: Sec. 4.3.2, Fig. 12, Table 2 and accompanying text
PDF page: 22
Claim: The source reports that moderate MPS bond dimension can approach its unapproximated result faster in low-noise instances, whereas high-noise instances can require larger bond dimensions that take longer than the unapproximated contraction.

The source also reports that low MPS state fidelity does not necessarily imply poor decoder
performance: the plotted strong non-Markovian regime shows a clear performance decrease, while the
plotted strong depolarising and crosstalk regimes do not show the same deterioration.

## Single-round scope [paper_fact]
Fact ID: kobayashi-single-round-scope
Source locator: Sec. 5, third paragraph
PDF page: 23
Claim: The source states that its maximum-likelihood decoder treats only a single round of syndrome measurement and identifies multiple noisy rounds, circuit-based decoding and surface-code decoding as future work.

## PT-MPO non-use [paper_fact]
Fact ID: kobayashi-ptmpo-nonuse
Source locator: Sec. 5, second paragraph
PDF page: 23
Claim: The source discusses PT-MPO as an established open-system approach but says it is unsuitable for the large local memory dimensions in this construction and instead approximates the combined process tensor and tester with MPS.

## Unresolved printed channel normalization [literature_gap]
Fact ID: kobayashi-gap-depolarising-normalization
Source locator: Sec. 4.1, Eq. (50) and adjacent description
PDF page: 14
Claim: The source does not reconcile the coefficients in its printed Eq. (50), whose trace on a trace-one input is `1+2 p_err`, with its description of that expression as a depolarising channel.
Gap scope: source_local

The PDF does not state whether the intended coefficient of the three-Pauli sum is `p_err/3`, whether
`p_err` is a per-Pauli rate, or whether the numerical implementation uses another convention.
This is therefore an ambiguity in the printed source object, not evidence for a silently repaired
channel or for the channel actually executed.

## Unsupported repeated-QEC reach [literature_gap]
Fact ID: kobayashi-gap-repeated-qec
Source locator: Sec. 5, third paragraph
PDF page: 23
Claim: This source does not demonstrate persistent-memory tensor-network computation over repeated syndrome-extraction rounds or return a multicycle detector record or repeated-QEC logical result.
Gap scope: source_local

## Unsupported decoder-benefit claim [literature_gap]
Fact ID: kobayashi-gap-decoder-benefit
Source locator: Numerical comparisons in Secs. 4.2–4.3 and scope statement in Sec. 5
PDF page: 23
Claim: This source does not compare a memory-aware decoder or control against a matched memory-blind alternative and therefore does not establish a benefit attributable to memory-aware intervention.
Gap scope: source_local

## Unsupported hardware and transfer claims [literature_gap]
Fact ID: kobayashi-gap-hardware-transfer
Source locator: Secs. 4–5
PDF page: 23
Claim: This source does not report hardware data, microscopic attribution in a device, threshold scaling, code-distance scaling, or transfer beyond its synthetic five-qubit and Steane instances.
Gap scope: source_local
