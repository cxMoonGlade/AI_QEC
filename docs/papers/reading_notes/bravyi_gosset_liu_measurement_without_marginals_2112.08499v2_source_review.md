+++
schema = "error_coupling_simulator.literature.note.v1"
source_id = "arxiv:2112.08499"
source_version = "v2"
source_uri = "https://arxiv.org/abs/2112.08499v2"
source_artifact = "docs/papers/2112.08499v2.pdf"
source_sha256 = "4743d2f0ed7de44f0da83ca875fb69dd15378cecfb54ef368da93d81580c68c6"
title = "How to simulate quantum measurement without computing marginals"
publication_status = "preprint"
read_status = "complete"
evidence_status = "persisted"
review_scope = "full_text"
operation_replay_status = "complete"
audit_packet = "docs/simulator_validation/BRAVYI_GOSSET_LIU_2112_08499V2_SOURCE_ONLY_AUDIT_2026-07-27.md"
audit_packet_sha256 = "b909593a3c3f24d7ecefcfc5ea2f1c2aa572ee354517afcd007c1e3da0c38049"
admission_status = "draft_pending_review"
admission_reviewer = "pending_fresh_independent_source_only_review"
admission_date = "2026-07-27"
visually_checked_pages = [1, 2, 3, 4, 5, 10, 11, 12, 16, 17]

[[relations]]
predicate = "defines"
object_id = "gate-by-gate-born-sampler"
object_type = "method"
object_label = "gate-by-gate sampler"
fact_id = "bgl2112-gate-by-gate"

[[relations]]
predicate = "supports"
object_id = "prefix-distribution-invariant"
object_type = "theorem"
object_label = "sampler distribution"
fact_id = "bgl2112-prefix-invariant"

[[relations]]
predicate = "supports"
object_id = "adaptive-circuit-output-sampling"
object_type = "method"
object_label = "adaptive quantum-circuit output sampling"
fact_id = "bgl2112-adaptive-circuits"

[[relations]]
predicate = "uses"
object_id = "tensor-network-amplitude-computation"
object_type = "method"
object_label = "tensor-network amplitude computation"
fact_id = "bgl2112-tn-cost-estimate"

[[relations]]
predicate = "uses"
object_id = "low-rank-stabilizer-amplitudes"
object_type = "method"
object_label = "low-rank stabilizer amplitudes"
fact_id = "bgl2112-stabilizer-rank"

[[relations]]
predicate = "supports"
object_id = "surface-code-mbqc-sampling"
object_type = "method"
object_label = "surface-code MBQC sampling"
fact_id = "bgl2112-mbqc-algorithm"

[[relations]]
predicate = "limits"
object_id = "surface-code-marginal-computation"
object_type = "limitation"
object_label = "surface-code marginal computation"
fact_id = "bgl2112-marginal-hardness"

[[relations]]
predicate = "supports"
object_id = "gapped-ground-state-sampling"
object_type = "method"
object_label = "gapped-ground-state sampling"
fact_id = "bgl2112-ground-state-mixing"
+++
# Full-text review — Bravyi, Gosset, and Liu, arXiv:2112.08499v2

## Source identity [paper_fact]
Fact ID: bgl2112-source-identity
Source locator: PDF page 1, title, author block, abstract, and arXiv version line
PDF page: 1
Claim: The reviewed source is the 17-page arXiv:2112.08499v2 preprint “How to simulate quantum measurement without computing marginals” by Sergey Bravyi, David Gosset, and Yinchen Liu, with a visible version stamp of 6 January 2022 and Supplemental Material included in the same PDF.

## Computational-basis sampling target [paper_fact]
Fact ID: bgl2112-sampling-target
Source locator: PDF page 1, Abstract and Introduction
PDF page: 1
Claim: The source assumes a normalized \(n\)-qubit state and targets a classical sample \(x\in\{0,1\}^n\) from the standard-basis law \(|\langle x|\psi\rangle|^2\).

## Standard marginal sampler [paper_fact]
Fact ID: bgl2112-marginal-chain-rule
Source locator: PDF pages 1--2, Eq. (1) and Algorithm 1
PDF page: 1
Claim: The standard qubit-by-qubit algorithm samples sequential conditional probabilities obtained from the growing marginals \(\pi_j(x_1\ldots x_j)\), requiring up to one marginal computation per output bit.

## Gate-by-gate sampler [paper_fact]
Fact ID: bgl2112-gate-by-gate
Source locator: PDF page 2, Algorithm 2 and Eq. (2)
PDF page: 2
Claim: The gate-by-gate sampler starts at \(x=0^n\) and, after each circuit gate, resamples only the gate-support bits using probabilities of the corresponding prefix-circuit output while holding the complementary bits fixed.

## Prefix distribution invariant [paper_fact]
Fact ID: bgl2112-prefix-invariant
Source locator: PDF page 2, proof following Algorithm 2
PDF page: 2
Claim: If exact prefix probabilities are used, the source proves by induction that the sampler distribution \(Q_t\) after iteration \(t\) equals the prefix output distribution \(P_t\), so the returned bit string has the exact final Born law.

## Probability-call count [paper_fact]
Fact ID: bgl2112-call-count
Source locator: PDF page 2, paragraphs following the Algorithm 2 proof
PDF page: 2
Claim: For gates acting on at most \(k\) qubits, Algorithm 2 evaluates at most \(m2^k\) prefix probabilities; its denominator is a normalization over at most \(2^k\) locally differing strings rather than a growing Algorithm-1 marginal.

## CNOT and diagonal-gate specializations [paper_fact]
Fact ID: bgl2112-special-gates
Source locator: PDF page 2, final paragraph before the adaptive-circuit statement
PDF page: 2
Claim: For CNOT plus arbitrary single-qubit gates, the sampled bits are updated deterministically at each CNOT and at most \(2m\) output probabilities are needed, while a diagonal gate can be skipped because it leaves \(P_t(x)\) unchanged.

## Adaptive-circuit output sampling [paper_fact]
Fact ID: bgl2112-adaptive-circuits
Source locator: PDF page 2, final paragraph, together with footnote 28 on PDF page 6
PDF page: 2
Claim: The source extends Algorithm 2 to adaptive quantum-circuit output sampling when later gates may be classically controlled by earlier measurement outcomes and every measured qubit is left untouched by all subsequent gates.

This convention does not define reset or a general outcome-resolved quantum
channel.

## Tensor-network depth comparison [paper_fact]
Fact ID: bgl2112-tn-depth-heuristic
Source locator: PDF page 3, first two columns before Table I
PDF page: 3
Claim: The source argues that a marginal probability can require a doubled-depth bra-ket contraction whereas the gate-by-gate method uses prefix amplitudes, so an advantage is expected only when the chosen amplitude method has a large cost ratio between depths \(2d\) and \(d\).

## Tensor-network cost estimate [paper_fact]
Fact ID: bgl2112-tn-cost-estimate
Source locator: PDF page 3, Table I and surrounding text; Supplemental PDF page 10, Table II and numerical details
PDF page: 3
Claim: For tensor-network amplitude computation on a displayed 49-qubit depth-16 \(7\times7\) circuit, CoTenGra optimizer estimates under matched slicing constraints report much lower aggregate FLOP counts for gate-by-gate than qubit-by-qubit sampling; the contractions themselves were not executed.

## Stabilizer-rank application [paper_fact]
Fact ID: bgl2112-stabilizer-rank
Source locator: PDF page 3, stabilizer-rank paragraphs
PDF page: 3
Claim: Using low-rank stabilizer amplitudes, the source gives an exact Clifford-plus-\(T\) sampler with runtime linear in the stabilizer rank of the magic resource up to polynomial factors, improving the cited qubit-by-qubit rank dependence from quadratic to linear.

## Prefix-state robustness bound [paper_fact]
Fact ID: bgl2112-robustness
Source locator: PDF page 4, Lemma 1 and Eq. (3), with proof in Supplemental PDF pages 7--8
PDF page: 4
Claim: If every approximate prefix state has global vector-norm error at most \(\epsilon_t\), the modified sampler obeys the printed bound \(\|Q-P_m\|_1\leq16\sum_{t=1}^{m-1}\epsilon_t\).

## Distance convention [paper_fact]
Fact ID: bgl2112-distance-convention
Source locator: PDF page 4, Eq. (3)
PDF page: 4
Claim: Equation (3) explicitly defines \(\|Q-P_m\|_1\) as the sum of absolute probability differences; under the common convention, total variation is one half of this printed quantity.

## Ground-state input conditions [paper_fact]
Fact ID: bgl2112-ground-state-conditions
Source locator: PDF page 4, Eqs. (4)--(6) and surrounding text
PDF page: 4
Claim: The ground-state sampler assumes a unique ground state, a Hamiltonian connecting computational-basis strings only within fixed Hamming distance \(k=O(1)\), a nonzero spectral gap \(\gamma\), a supported initial string of non-negligible probability, amplitude-ratio access, and controlled sensitivity parameter \(s\).

## Gapped-ground-state sampling bound [paper_fact]
Fact ID: bgl2112-ground-state-mixing
Source locator: PDF pages 4--5, Eqs. (5)--(14)
PDF page: 5
Claim: Under the stated conditions, the source bounds the calls needed for gapped-ground-state sampling by a quantity scaling as \((n^k s/\gamma)\log[1/(\pi(x_{\mathrm{in}})\epsilon)]\), using a local Metropolis--Hastings chain and a spectral-gap argument.

## Surface-code resource state [paper_fact]
Fact ID: bgl2112-surface-resource
Source locator: Supplemental PDF page 10, Eq. (31) and following paragraph
PDF page: 10
Claim: For a planar graph \(G\), the source defines the surface-code resource state \(|\psi_G\rangle\) as the uniform superposition of graph cycles and notes that its direct standard-basis measurement can be sampled in \(O(n)\) time from a face-boundary basis.

## Surface-code MBQC algorithm [paper_fact]
Fact ID: bgl2112-mbqc-algorithm
Source locator: Supplemental PDF page 11, Eq. (33), Algorithm 3, and Problem 1
PDF page: 11
Claim: The source gives surface-code MBQC sampling on any planar graph by initializing from \(|\psi_G\rangle\), applying the gate-by-gate update to adaptive one-qubit bases, and evaluating product-state overlaps with the resource state.

## Surface-code MBQC runtime [paper_fact]
Fact ID: bgl2112-mbqc-runtime
Source locator: Supplemental PDF page 11, paragraphs following Problem 1
PDF page: 11
Claim: The stated runtime is \(O(n^4T)\) for a general planar graph and \(O(n^3T)\) for the square-lattice specialization, where \(T\) is the maximum cost of evaluating an adaptive basis-choice function.

## Surface-code marginal hardness [paper_fact]
Fact ID: bgl2112-marginal-hardness
Source locator: Supplemental PDF page 12, Problem 2 discussion and Theorems 1--2
PDF page: 12
Claim: Without the connectivity restriction used by the cited earlier method, the source proves that exact surface-code marginal computation is \(\#P\)-hard by reducing exact perfect-matching counting in 3-regular graphs to Problem 2.

## Measurement-order qualification [paper_fact]
Fact ID: bgl2112-order-qualification
Source locator: Supplemental PDF page 12, paragraphs before Theorem 1
PDF page: 12
Claim: The marginal-hardness obstruction is tied to an enforced adaptive measurement order; for regular non-adaptive measurement on connected \(G\), qubits can be reordered to satisfy the connectivity condition and both sampling routes remain efficient.

## Stoquastic sensitivity bound [paper_fact]
Fact ID: bgl2112-stoquastic-sensitivity
Source locator: Supplemental PDF page 16, “Ground state sensitivity for stoquastic Hamiltonians”
PDF page: 16
Claim: For a stoquastic Hamiltonian and a nonnegative ground-state representative, the source proves \(s\leq\max_y\langle y|H|y\rangle-E_0\).

## Magic-ratio Hamiltonian family [paper_fact]
Fact ID: bgl2112-magic-ratio
Source locator: Supplemental PDF pages 16--17, Lemma 4 and final sensitivity argument
PDF page: 17
Claim: For the defined frustration-free magic-ratio Hamiltonian family with disjoint projector supports, the source reduces required amplitude ratios to local projector data and obtains the sensitivity bound \(s\leq m\).

## No post-measurement conditional state [literature_gap]
Fact ID: bgl2112-gap-conditional-state
Source locator: PDF pages 1--4, complete circuit-sampling construction
PDF page: 2
Claim: This source samples a classical output law but does not represent, compare, or certify outcome-conditioned post-measurement quantum states.
Gap scope: source_local

## No reset transaction [literature_gap]
Fact ID: bgl2112-gap-reset
Source locator: PDF page 2 and footnote 28 on PDF page 6
PDF page: 2
Claim: This source does not define measurement followed by reset or re-preparation; its adaptive convention instead leaves a measured qubit untouched thereafter.
Gap scope: source_local

## No QEC raw-history or Record fold [literature_gap]
Fact ID: bgl2112-gap-qec-record
Source locator: PDF pages 3--4 and Supplemental PDF pages 10--12, complete surface-code-MBQC scope
PDF page: 11
Claim: This source does not define repeated syndrome rounds, raw measurement-history or prefix branch masses for a QEC instrument, detector/observable Record folds, or decoder records.
Gap scope: source_local

## No XZZX noise experiment [literature_gap]
Fact ID: bgl2112-gap-xzzx
Source locator: Supplemental PDF pages 10--12, surface-code resource-state construction
PDF page: 10
Claim: The surface-code result is an MBQC resource-state sampler, not a noisy XZZX syndrome circuit, coherent-error model, memory experiment, or logical-error benchmark.
Gap scope: source_local

## No Clifford-frame residual [literature_gap]
Fact ID: bgl2112-gap-clifford-residual
Source locator: PDF page 3, stabilizer-rank application and complete source scope
PDF page: 3
Claim: This source does not provide a tableau-carried Clifford frame, \(C|\mathrm{MPS}\rangle\), \(C|\mathrm{PEPS}\rangle\), or a non-stabilizer PEPS residual.
Gap scope: source_local

## No finite-bond error derivation [literature_gap]
Fact ID: bgl2112-gap-finite-bond
Source locator: PDF page 4, Lemma 1 and Eq. (3)
PDF page: 4
Claim: This source assumes global prefix-state errors \(\epsilon_t\) and does not derive them from PEPS virtual-bond truncation, finite contraction environments, or branchwise compression.
Gap scope: source_local

## No matched full-PEPS comparison [literature_gap]
Fact ID: bgl2112-gap-matched-peps
Source locator: PDF page 3, Table I and Supplemental PDF page 10, Table II
PDF page: 3
Claim: This source does not compare CAPEPS with a matched full-PEPS simulation or a Pauli-twirled tableau on the same channel and Record estimand.
Gap scope: source_local

## No conditional fidelity or Record-TV [literature_gap]
Fact ID: bgl2112-gap-record-metrics
Source locator: PDF page 4, Lemma 1 and complete source scope
PDF page: 4
Claim: This source does not report conditional-state fidelity, detector Record total variation, raw-history equality, or reset correctness.
Gap scope: source_local

## No measured peak-memory benchmark [literature_gap]
Fact ID: bgl2112-gap-peak-memory
Source locator: PDF page 3, Table I and surrounding benchmark qualification; Supplemental PDF page 10
PDF page: 3
Claim: The displayed tensor-network study constrains intermediate tensor size and estimates FLOPs but does not report measured contraction runtime, peak host/device memory, or output-law accuracy.
Gap scope: source_local

## No universal tensor-network advantage [literature_gap]
Fact ID: bgl2112-gap-universal-tn-speedup
Source locator: PDF page 3, depth-cost discussion and Table I
PDF page: 3
Claim: This source does not prove that gate-by-gate sampling is faster than qubit-by-qubit sampling for every tensor-network geometry, contraction optimizer, or memory regime.
Gap scope: source_local
