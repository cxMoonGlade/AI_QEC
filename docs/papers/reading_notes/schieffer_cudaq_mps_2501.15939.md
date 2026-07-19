+++
schema = "error_coupling_simulator.literature.note.v1"
source_id = "arxiv:2501.15939"
source_version = "v1"
source_uri = "https://arxiv.org/abs/2501.15939v1"
source_artifact = "outputs/papers/2501.15939.pdf"
source_sha256 = "37e6238b971a87f3cdc06c098076f911131f9ae3829f7bd6e7f3f6f3858f8316"
title = "Harnessing CUDA-Q's MPS for Tensor Network Simulations of Large-Scale Quantum Circuits"
publication_status = "preprint"
read_status = "complete"
evidence_status = "persisted"
review_scope = "full_text"
operation_replay_status = "complete"
audit_packet = "docs/simulator_validation/SCHIEFFER_2501_15939_PROJECT_FIT_AUDIT_2026-07-17.md"
audit_packet_sha256 = "92f24ccc7975a43bb18fa0b4b658ab64085a7a0a15eed38afde1c7578e69ce49"
admission_status = "source_only_reviewed"
admission_reviewer = "mps_peps_source_rebuild_xhigh_2026_07_17"
admission_date = "2026-07-17"
visually_checked_pages = [1, 2, 3, 4, 5, 6, 7, 8, 9]

[[relations]]
predicate = "defines"
object_id = "cuda-q-mps-configuration"
object_type = "method"
object_label = "CUDA-Q MPS configuration"
fact_id = "schieffer-mps-controls"

[[relations]]
predicate = "measures"
object_id = "cuda-q-mps-runtime-scaling"
object_type = "observable"
object_label = "CUDA-Q MPS runtime scaling"
fact_id = "schieffer-high-qubit-scaling"

[[relations]]
predicate = "measures"
object_id = "cuda-q-mps-phase-profile"
object_type = "observable"
object_label = "CUDA-Q MPS phase profile"
fact_id = "schieffer-profile-phase-share"

[[relations]]
predicate = "measures"
object_id = "qaoa-top-four-set-agreement"
object_type = "observable"
object_label = "QAOA top-four-set agreement"
fact_id = "schieffer-top-four-sweep"

[[relations]]
predicate = "limits"
object_id = "single-instance-accuracy-test"
object_type = "limitation"
object_label = "single-instance accuracy test"
fact_id = "schieffer-accuracy-boundary"
+++
# Full-text review — Schieffer et al., “Harnessing CUDA-Q's MPS for Tensor Network Simulations of Large-Scale Quantum Circuits”

## Source identity [paper_fact]
Fact ID: schieffer-source-identity
Source locator: Title page and arXiv version line
PDF page: 1
Claim: The source is Schieffer, Markidis, and Peng's arXiv:2501.15939v1 preprint “Harnessing CUDA-Q's MPS for Tensor Network Simulations of Large-Scale Quantum Circuits,” posted on 27 January 2025.

All three authors are affiliated with KTH Royal Institute of Technology. The title page labels the
work a pre-print submitted for publication, and this record is pinned to the ten-page v1 artifact.

## Scientific scope [paper_fact]
Fact ID: schieffer-selection-scope
Source locator: Abstract; Sec. I, contributions
PDF page: 1
Claim: The source evaluates CUDA-Q's GPU-backed exact tensor-network and approximate MPS circuit simulators on a Grace Hopper system, compares runtime and scalability with CUDA-Q state-vector simulation, profiles one workload, and tests a source-defined accuracy rule on one QAOA circuit.

The study implements five circuit families and supplies benchmark scripts. Its experiments concern
standalone circuit sampling rather than a general theorem about MPS approximation or GPU performance.

## MPS representation and memory count [paper_fact]
Fact ID: schieffer-mps-representation
Source locator: Sec. II-A–B and Fig. 2
PDF page: 2
Claim: The source describes an exact pure-state MPS as a chain obtained by recursive SVD and reduces memory by truncating singular values to a bond dimension `chi`, giving a parameter count `d n chi^2` and linear dependence on qubit count `n` only when `chi` is fixed.

Here `d=2` for qubits. The source states that the bond dimension is linked to circuit entanglement;
it does not claim that `chi` stays fixed for arbitrary circuit families or depths.

## CUDA-Q MPS controls [paper_fact]
Fact ID: schieffer-mps-controls
Source locator: Sec. III-A and Table I
PDF page: 3
Claim: The evaluated CUDA-Q MPS configuration uses the cuTensorNet-backed `tensornet-mps` backend with default `CUDAQ_MPS_MAX_BOND=64`, absolute cutoff `10^-5`, relative cutoff `10^-5`, and the default QR SVD algorithm.

Table I distinguishes this backend from the cuTensorNet-backed exact `tensornet` backend and the
cuStateVec-backed `nvidia` state-vector backend. These settings fix the evaluated approximation but
are not varied jointly in the accuracy experiment.

## Circuit suite and entanglement ratio [paper_fact]
Fact ID: schieffer-circuit-suite
Source locator: Sec. III-B, Table II, and Fig. 3
PDF page: 3
Claim: The benchmark suite comprises counterfeit coin, GHZ, QFT, Quantum Volume, and QAOA circuits, and the source defines an entanglement ratio `N_2q/N_total` as a loose gate-count-based characterization rather than a measured entanglement entropy.

The stated asymptotic ratio ranges from 0.25 for counterfeit coin to 1 for Quantum Volume. The QFT
gate count depends on its input, so the plotted QFT ratio is explicitly described as a lower bound.

## Execution protocol and platform [paper_fact]
Fact ID: schieffer-execution-protocol
Source locator: Sec. III-D
PDF page: 5
Claim: Runtime experiments use `cudaq.sample` with 1,024 shots on one Grace Hopper Superchip containing a 72-core Arm CPU and a 96 GB H100 GPU, with one warm-up followed by ten measured repetitions that recreate the circuit each time.

The reported runtimes therefore include the source's full sampling protocol on that software and
hardware stack. The profiling experiment later uses a different 10-shot workload.

## Low-qubit runtime comparison [paper_fact]
Fact ID: schieffer-low-qubit-runtime
Source locator: Sec. IV-A and Fig. 4
PDF page: 5
Claim: For every configuration in which the state-vector backend fits, it runs faster than both tensor-network backends; exact TN is faster than MPS below 12 qubits, while MPS is faster than exact TN after the observed 12-to-13-qubit transition.

The authors suggest that SVD overhead explains the TN-to-MPS crossover and that the 12-to-13-qubit
gap may reflect caching or an undocumented simulator behavior. These explanations are presented as
suggestions rather than isolated measurements.

## High-qubit empirical scaling [paper_fact]
Fact ID: schieffer-high-qubit-scaling
Source locator: Sec. IV-B and Fig. 5
PDF page: 5
Claim: The measured CUDA-Q MPS runtime scaling for `n>=35` is fit by `0.0017 n^3.1644` for QAOA and `0.0008 n^3.5786` for Quantum Volume, while QFT and GHZ are fit by `2.11 n - 50.82` and `5.53 n - 155.16`, respectively.

The displayed coefficients of determination are 0.999, 0.9967, 0.98, and 0.99. MPS reaches 60
qubits for all four plotted circuits and 90 qubits for GHZ on the tested single GPU; the fits are
empirical models of those data rather than complexity bounds.

## Profiling phase shares [paper_fact]
Fact ID: schieffer-profile-phase-share
Source locator: Sec. IV-C.1 and Fig. 6
PDF page: 6
Claim: In one Nsight profile of a 20-qubit QFT circuit with 10 shots, the CUDA-Q MPS phase profile assigns 22% of runtime to a CPU-only phase, 70% to GPU SVD, and 8% to CPU+GPU contractions, while average GPU activity during the SVD phase is 33%.

The corresponding exact-TN profile assigns 80% to a CPU-only phase and 20% to a CPU+GPU
contraction phase. The source says the MPS SVD problem may be too small to use the available GPU
resources; it does not profile the other circuit families this way.

## Contraction and transfer observations [paper_fact]
Fact ID: schieffer-contraction-profile
Source locator: Sec. IV-C.2 and Fig. 7
PDF page: 7
Claim: On the same profile, the contraction interval is 225 ms for exact TN and 45 ms for MPS; no MPS kernels run during 60% of that interval while host-to-device transfers of about 128 bytes per operation occur, and whole-execution Tensor Core utilization is below 1% for both methods.

The authors infer that CPU processing is associated with the small transfers and suggest that this
task may be poorly suited to GPU parallelization, but the profile does not isolate the causal cost of
the transfers. The contraction times would grow linearly with shot count under the described method.

## QAOA accuracy protocol [paper_fact]
Fact ID: schieffer-qaoa-accuracy-protocol
Source locator: Sec. V-A–B and Fig. 8
PDF page: 7
Claim: The accuracy study samples one 10-qubit QAOA circuit with random parameters for 100,000 shots, uses state-vector sampling as the reference, and defines the target as the identities of the four most-sampled basis states.

The paper notes that the isolated random-parameter circuit has no problem-specific output meaning and
that choosing four reference states is application-dependent. Figure 8 visually compares the two
histograms but supplies no scalar distribution-distance statistic.

## Bond-cap top-four sweep [paper_fact]
Fact ID: schieffer-top-four-sweep
Source locator: Sec. V-B and Table III
PDF page: 8
Claim: The QAOA top-four-set agreement contains all four reference state identities for `chi_max=64`, `32`, and `16`, whereas every evaluated `chi_max` at or below 15 retains at most two of the four reference identities.

The order within the top-four set changes even in matching columns. The source calls the lower-cap
outputs incorrect under this chosen rule while noting that approximate simulation could still be
useful inside a larger iterative QAOA algorithm.

## Conditional-circuit runtime [paper_fact]
Fact ID: schieffer-conditional-runtime
Source locator: Sec. IV-A, counterfeit-coin paragraph
PDF page: 5
Claim: For the original 12-qubit counterfeit-coin circuit, the source reports 2.8 s for state vector, 4 min for exact TN, and 19 min for MPS and attributes the slowdown to intermediate measurements and measurement-conditioned gates.

The study does not scale this circuit to larger qubit counts because of the observed runtime. The
causal attribution is the authors' interpretation of one circuit structure rather than a controlled
ablation of measurement and conditional operations.

## Accuracy evidence boundary [paper_fact]
Fact ID: schieffer-accuracy-boundary
Source locator: Sec. V-A–B and Sec. VII
PDF page: 7
Claim: The source's single-instance accuracy test reports only sampled top-state identities for one standalone QAOA circuit and leaves evaluation inside a real-world QAOA workflow to future work.

It does not report wavefunction norm error, fidelity, discarded weight, trace distance, total
variation, Hellinger distance, KL divergence, confidence bands, or repeated-seed stability for the
bond-cap sweep.

## Performance evidence boundary [paper_fact]
Fact ID: schieffer-performance-boundary
Source locator: Secs. III-D, IV-C, and VII
PDF page: 5
Claim: The source's performance conclusions are measurements of CUDA-Q backends on one Grace Hopper platform, and the detailed GPU-utilization conclusions come from one small QFT profiling case.

The work does not compare CUDA-Q MPS with another MPS library, run a kernel-fusion intervention, or
separate the effects of numerical precision, host orchestration, circuit construction, and state
update across platforms.

## Source-local unsupported state and distribution certificate [literature_gap]
Fact ID: schieffer-gap-state-certificate
Source locator: Full-text scope of Sec. V and the stated future work in Sec. VII
PDF page: 7
Claim: This source does not establish a state-error or full sampled-distribution certificate for CUDA-Q MPS at any tested bond cap.
Gap scope: source_local

The reported top-four-set match is a discrete application-chosen observable. No theorem or measured
standard distance connects it to the complete state or output distribution.

## Source-local unsupported adaptive Record certificate [literature_gap]
Fact ID: schieffer-gap-adaptive-record
Source locator: Full-text scope; conditional-circuit paragraph in Sec. IV-A
PDF page: 1
Claim: This source does not establish accuracy or performance guarantees for a complete repeated-measurement adaptive record law.
Gap scope: source_local

One counterfeit-coin runtime includes intermediate measurements and conditional gates, but the paper
defines no retained measurement-history object, multi-round record metric, or accuracy comparison for
that circuit.
