+++
schema = "error_coupling_simulator.literature.note.v1"
source_id = "arxiv:2607.28600"
source_version = "v1"
source_uri = "https://arxiv.org/abs/2607.28600v1"
source_artifact = "docs/papers/2607.28600v1.pdf"
source_sha256 = "37c2e5b4276d4c348ee951b0c3fb8b72b5f1ac9893b707fecd3cad10ebc5af29"
title = "SymFT: Universal Fault-Tolerant Quantum Circuit Simulation via Symbolic Clifford–Pauli Frames and Stabilizer Coordinates"
publication_status = "preprint"
read_status = "complete"
evidence_status = "persisted"
review_scope = "full_text"
operation_replay_status = "complete"
audit_packet = "docs/simulator_validation/FANG_LOU_LI_2607_28600V1_SYMFT_STRUCTURE_AUDIT_2026-08-03.md"
audit_packet_sha256 = "0d3045d9cd871fe727e9aee871e1414b1679988e6937e6c228e95f73d4dc5913"
admission_status = "source_only_reviewed"
admission_reviewer = "independent_symft_2607_source_rereview_round2_2026_08_03"
admission_date = "2026-08-03"
visually_checked_pages = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24]

[[relations]]
predicate = "defines"
object_id = "symft-symbolic-frame-factorization"
object_type = "method"
object_label = "symbolic Clifford–Pauli frame factorization"
fact_id = "symft-branch-factorization"

[[relations]]
predicate = "defines"
object_id = "symft-active-coordinate-state"
object_type = "model"
object_label = "dense active-state vector"
fact_id = "symft-active-state"

[[relations]]
predicate = "defines"
object_id = "symft-peak-active-width"
object_type = "observable"
object_label = "peak active width"
fact_id = "symft-sampling-complexity"

[[relations]]
predicate = "supports"
object_id = "symft-coherent-surface-width"
object_type = "observable"
object_label = "coherent-noise surface-code family"
fact_id = "symft-coherent-benchmark"

[[relations]]
predicate = "supports"
object_id = "symft-clifft-width-conditional-equivalence"
object_type = "method"
object_label = "same residual Pauli sequence"
fact_id = "symft-clifft-comparison"

[[relations]]
predicate = "defines"
object_id = "symft-soft-sparse-support"
object_type = "observable"
object_label = "peak sparse support"
fact_id = "symft-soft-comparison"
+++
# Full-text review — Fang, Lou, and Li, "SymFT"

## Source identity [paper_fact]
Fact ID: symft-source-identity
Source locator: Title page, author block, abstract, arXiv version line, and title-page repository footnote
PDF page: 1
Claim: The reviewed source is arXiv:2607.28600v1 by Wang Fang, Huazhe Lou, and Riling Li, dated 30 July 2026, and it identifies SymFT as the second-generation successor to SOFT at `https://github.com/haoliri0/SOFT`.

The fixed artifact contains 28 PDF pages.  The source presents SymFT as an exact
simulator for noisy adaptive Clifford-dominated circuits and reports both CPU
and CUDA implementations.  The repository URL is a source statement, not a
commit binding; repository facts require a separately pinned code audit.

## Exact Pauli operation surface [paper_fact]
Fact ID: symft-operation-surface
Source locator: Sec. 2, operation-family bullets and displayed rotation/projector definitions
PDF page: 4
Claim: SymFT's circuit model includes exact Hermitian-Pauli rotations (R_P(\theta)=\exp(-i\theta P/2)=\cos(\theta/2)I-i\sin(\theta/2)P), projective Pauli measurements with projectors ((I\pm P)/2), stochastic Pauli noise, and measurement-record-controlled Pauli feedback.

The source requires (P^2=I) for a Pauli used as a rotation generator,
measurement observable, or stochastic noise operator.  The feedback control in
the defined model is the parity of a specified subset of earlier measurement
outcomes.  More general Boolean or non-Pauli feedback is described as a
possible but generally less efficient extension.

## Symbolic frame factorization and branch probability [paper_fact]
Fact ID: symft-branch-factorization
Source locator: Sec. 1.1, displayed factorization and branch-probability equation, PDF p. 2; Sec. 3, Eqs. (2)–(4), PDF pp. 5–6
PDF page: 2
Claim: Symbolic Clifford–Pauli frame factorization writes a measurement branch operator, up to global phase, as (K(s,m)\doteq C E(s,m)O(s,m)), where the residual Clifford and Pauli frames are unitary, so the conditional measurement-branch probability is (Pr(m\mid s)=\lVert O(s,m)|0^n\rangle\rVert^2).

Here (s) denotes stochastic Pauli-noise choices and (m) the measurement
record.  The ordered residual (O(s,m)) consists of pulled-back Pauli
rotations and Pauli measurement projectors.  Clifford operations have already
been incorporated into the pulled-back Paulis, while noise and feedback enter
the residual operations through symbolic signs.

## Dense active-coordinate state [paper_fact]
Fact ID: symft-active-state
Source locator: Sec. 1.1, displayed active-basis expansion and following two paragraphs
PDF page: 3
Claim: A canonical stabilizer–destabilizer tableau defines (n) stabilizer coordinates, the first (k) of which are active, and the semantic representation writes the active-basis coefficients as one dense active-state vector (|\alpha\rangle_A\in\mathbb C^{2^k}) while the remaining (n-k) coordinates are dormant.

The tableau trajectory and basis changes are planned once and shared across
shots.  A pulled-back operation is decomposed into active and dormant
components; dormant components are handled by tableau changes and symbolic
Pauli corrections, while active components compile to direct dense-vector
instructions.  This semantic monolithic vector is not a statement that every
current backend materializes the full tensor product; the CPU product-component
lowering described in Sec. 6 can retain exact factorization.

## Rotation promotion rule [paper_fact]
Fact ID: symft-rotation-promotion
Source locator: Sec. 4.1, "Dormant-nondiagonal rotations", coordinate update and emitted instruction
PDF page: 8
Claim: When a pulled-back non-Clifford Pauli rotation has dormant coordinate (d\ne0), so that it anticommutes with at least one dormant stabilizer, the planner selects one dormant pivot, updates the stabilizer coordinates, moves that pivot into the active block, and emits a promoted-rotation instruction, increasing active width by one.

The coordinate change preserves the canonical stabilizer–destabilizer
commutation relations.  The source treats diagonal dormant rotations without
promoting an active coordinate and treats rotations with only active support
by direct dense-vector updates.

## Active-measurement compaction rule [paper_fact]
Fact ID: symft-measurement-compaction
Source locator: Sec. 4.2, "Active-diagonal measurements" and "Active-nondiagonal measurements", Eqs. (12)–(13), PDF pp. 11–13
PDF page: 13
Claim: When (d=0) and the active component satisfies ((a,b)\ne(0,0)), both active-measurement cases sample or determine the branch, project and normalize the dense active-state vector, move one pivot coordinate to the dormant block, and compact the vector from dimension (2^k) to (2^{k-1}).

PDF pages 11–13 derive the active-diagonal and paired-amplitude
active-nondiagonal cases separately.  Dormant random or deterministic
measurements do not traverse the active vector and do not reduce (k).

## Per-shot cost and peak active width [paper_fact]
Fact ID: symft-sampling-complexity
Source locator: Sec. 5, paragraph "Sampling complexity" and the two displayed cost formulas
PDF page: 15
Claim: If (k^S_{\max}) is SymFT's peak active width, the general monolithic state-vector bound for per-shot dense-state work is (O((n_t+n^S_{m,\mathrm{active}})2^{k^S_{\max}})), and total per-shot cost adds symbolic-expression evaluation and stochastic-noise sampling terms.

The source defines (n_t) as the number of non-Clifford Pauli rotations and
(n^S_{m,\mathrm{active}}) as the number of Pauli measurements that emit an
active dense-vector instruction.  It states a worst-case bound for evaluating
symbolic signs, while noting that those signs are typically sparse in local
fault-tolerant circuits.

## Exact product-component CPU lowering [paper_fact]
Fact ID: symft-product-component-backend
Source locator: Sec. 6, paragraph "Adaptive product-component representation", PDF p. 16
PDF page: 16
Claim: The current CPU product-component backend uses a deterministic lowering pass to identify exact product structure, stores one small dense vector per independent component without materializing the full tensor product, and exactly merges only components coupled by an operation.

Promotion creates a new one-coordinate component.  Operations internal to one
component update only that component, while cross-component operations first
use an exact Kronecker product for the affected components.  A conservative
cost model decides whether to select this representation.  Thus
`2^(k_max^S)` remains a valid general or monolithic burden but is not a
complete prediction of the current CPU backend's realized work or memory.

## Coherent surface-code active-width observations [paper_fact]
Fact ID: symft-coherent-benchmark
Source locator: Sec. 7.1, paragraph "Coherent noise and distillation", Tables 3–4
PDF page: 20
Claim: On the reported coherent-noise surface-code family, SymFT has (k^S_{\max}=4,7,12,22) for ((d,r)=(3,1),(3,3),(5,1),(5,5)), and the FP64 CUDA execution for (d=5,r=5) is marked as exceeding the RTX 4090 per-block shared-memory limit.

The preceding paragraph on PDF page 19 defines the family as a small
`R_Z(0.02)` over-rotation together with circuit-level noise on distance-(d)
surface-code circuits.  The table contains four observations and no fit or
asymptotic extrapolation.

## Explicit unvalidated full-distribution workload [paper_fact]
Fact ID: symft-unvalidated-msc-d7
Source locator: Sec. 7.1, paragraph immediately before "Coherent noise and distillation", PDF p. 19
PDF page: 19
Claim: For the exploratory MSC distance-seven workload, the source says that too few shots were generated to validate the full output distribution or rare logical-error behavior and therefore makes no correctness claim for that workload.

The workload is included as a performance stress test for a larger active
subspace.  This explicit limitation separates attempted-shot throughput from
full-distribution validation.

## Conditional comparison with Clifft active width [paper_fact]
Fact ID: symft-clifft-comparison
Source locator: Sec. 8, bullet "Clifft", comparison paragraph after the two cost formulas
PDF page: 22
Claim: SymFT keeps (k^S_{\max}) distinct from Clifft's (k^C_{\max}); the source gives the same residual Pauli sequence plus maximum-rank dormant stabilizer subgroups after every prefix as a sufficient condition under which the widths coincide at every step, while reordering, fusion, or different coordinate updates can change the compiled trajectories.

Both methods use an active-width parameter and a dense active vector, but their
direct update mechanics and symbolic work differ.  The comparison does not
identify either reported width as a representation-independent lower bound.

## Sparse SOFT support is a distinct cost parameter [paper_fact]
Fact ID: symft-soft-comparison
Source locator: Sec. 8, bullet "SOFT", final paragraph and displayed worst-case update bound
PDF page: 22
Claim: SOFT stores a sparse generalized-stabilizer coefficient map with peak sparse support (r_{\max}); the source gives the worst-case relation (r_{\max}\le 2^{k^S_{\max}}) while stating that code constraints can make the sparse support much smaller.

The source treats `r_max` as SOFT's number of nonzero coefficients, not as a
Pauli-pair state count, a decision-diagram node count, or a treewidth.  It
therefore cannot be substituted for those census quantities without a new
definition and implementation.

## Multiple structural costs remain relevant [paper_fact]
Fact ID: symft-multi-cost-outlook
Source locator: Sec. 9, second paragraph
PDF page: 24
Claim: The source says that reducing non-Clifford count alone does not guarantee a lower peak active width and proposes that future optimizers jointly consider (k^S_{\max}), symbolic-evaluation cost, and total dense-vector work along the planned trajectory.

The current product-component backend already exploits exact separability but
does not split a component again after merging.  Future directions are to
detect new exact factorizations, use richer structured representations, and
adaptively choose among monolithic dense, exact product-component, sparse, and
tensor-network representations.  The source does not claim that one
structural parameter dominates every circuit family.

## No persistent coherent latent process [literature_gap]
Fact ID: symft-gap-persistent-coherent-memory
Source locator: Full-text review boundary, body PDF pp. 1–24 and full artifact PDF pp. 1–28; positive model scopes in Sec. 2, PDF p. 4, Sec. 3, PDF pp. 5–6, and Sec. 7.1, PDF p. 19
PDF page: 19
Claim: This source does not define or benchmark a single coherent latent variable whose value persists across QEC rounds and jointly controls all repeated coherent rotations.
Gap scope: source_local

The source's stochastic variables (s) encode independent choices at individual
Pauli-noise locations; it separately uses measurement symbols (m).  The
reported coherent circuit applies a fixed `R_Z(0.02)` over-rotation.  Neither
construction defines the single cross-round coherent latent variable named in
the gap.

## No complete non-Markovian Record scaling certificate [literature_gap]
Fact ID: symft-gap-complete-record-scaling
Source locator: Full-text review boundary, body PDF pp. 1–24 and full artifact PDF pp. 1–28; positive sampling, benchmark, comparison, and outlook scopes in Secs. 5–9, PDF pp. 15–24
PDF page: 24
Claim: This source does not prove that SymFT scales for a complete detector/observable Record law generated by a persistent non-Markovian declared-error process, and it supplies no independent full-law total-variation certificate over increasing code distance and rounds.
Gap scope: source_local

The paper defines exact shot generation for its supported circuit model and
reports attempted-shot throughput.  It explicitly withholds a full-output
correctness claim for the exploratory MSC distance-seven workload on PDF p. 19.
Neither item is a strong-simulation table of the entire folded Record support
or an independent Record-law certification result.

## No Pauli-pair, decision-diagram, or treewidth metric [literature_gap]
Fact ID: symft-gap-other-structure-meters
Source locator: Full-text review boundary, body PDF pp. 1–24 and full artifact PDF pp. 1–28; related-work and outlook scopes in Secs. 8–9, PDF pp. 21–24
PDF page: 24
Claim: This source does not define a Pauli-pair reachable-state count, a reduced ordered decision-diagram node count for the folded Record law, or an exact treewidth of a declared Record-law factor graph.
Gap scope: source_local

The related-work and outlook sections discuss sparse coefficients, ZX
decompositions, stabilizer tensor networks, and possible tensor-network
backends.  Those discussions do not supply the three requested census meters.
