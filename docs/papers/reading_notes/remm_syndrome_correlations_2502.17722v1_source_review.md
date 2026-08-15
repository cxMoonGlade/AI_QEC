+++
schema = "error_coupling_simulator.literature.note.v1"
source_id = "arxiv:2502.17722"
source_version = "v1"
source_uri = "https://arxiv.org/abs/2502.17722v1"
source_artifact = "outputs/papers/2502.17722.pdf"
source_sha256 = "e2c6f6261c134e510f00d9083cf87a6e98f1e79b414fdb7b6b259a64ba6054e2"
title = "Experimentally Informed Decoding of Stabilizer Codes Based on Syndrome Correlations"
publication_status = "preprint"
read_status = "complete"
evidence_status = "persisted"
review_scope = "full_text"
operation_replay_status = "complete"
audit_packet = "docs/simulator_validation/literature_expansion_round2/REMM_SYNDROME_CORRELATIONS_2502_17722_AUDIT_2026-08-05.md"
audit_packet_sha256 = "0aec1130453ae7e8aade36fa8dd2b9fce762ad9e87d13707ef21558c4f6dfbd2"
admission_status = "source_only_reviewed"
admission_reviewer = "/root/expand_decoder_benefit"
admission_date = "2026-08-05"
visually_checked_pages = [1, 2, 4, 5, 6, 7, 8, 9, 10, 11, 13, 14, 15, 16, 17, 18, 19]

[[relations]]
predicate = "measures"
object_id = "remm-multicycle-syndrome-covariance"
object_type = "observable"
object_label = "same-auxiliary syndrome covariance"
fact_id = "remm-long-time-covariance"

[[relations]]
predicate = "derives"
object_id = "remm-signature-probability-model"
object_type = "model"
object_label = "error-signature probability model"
fact_id = "remm-general-inversion"

[[relations]]
predicate = "uses"
object_id = "remm-correlated-mwpm"
object_type = "method"
object_label = "correlated minimum-weight perfect matching procedure"
fact_id = "remm-correlated-decoder-operation"

[[relations]]
predicate = "limits"
object_id = "remm-nonstationarity-confounder"
object_type = "limitation"
object_label = "nonstationarity-induced apparent correlation"
fact_id = "remm-drift-confounder"

[[relations]]
predicate = "limits"
object_id = "remm-decoder-benefit-boundary"
object_type = "limitation"
object_label = "difference is not statistically significant"
fact_id = "remm-decoder-result"
+++
# Full-text review — Remm et al., "Experimentally Informed Decoding of Stabilizer Codes Based on Syndrome Correlations"

## Source identity [paper_fact]
Fact ID: remm-source-identity
Source locator: Title page and arXiv identifier in page margin
PDF page: 1
Claim: The fixed source is the 23-page arXiv:2502.17722v1 manuscript by Ants Remm and coauthors, dated 26 February 2025 on its title page.

The source is treated as a preprint. The repository artifact includes the main text, Appendices A–I
and references.

## Selection scope [paper_fact]
Fact ID: remm-selection-scope
Source locator: Abstract; Introduction; Secs. III–V
PDF page: 1
Claim: The source infers probabilities for selected error signatures from experimental syndrome correlations in a 16-cycle distance-3 surface-code experiment, uses those probabilities to calibrate matching weights, and investigates device diagnostics and a correlated-MWPM modification.

## Experimental task and selection [paper_fact]
Fact ID: remm-experimental-task
Source locator: Sec. IV, paragraph beginning "Using the device"
PDF page: 6
Claim: The experiment prepares `|0>_L`, `|1>_L`, `|+>_L` or `|->_L` on a 17-qubit distance-3 surface-code device, acquires 16 stabilizer cycles and a final readout, and starts from 500,000 runs per state.

For the default analysis, runs with any non-computational readout or failed ground-state
initialization are removed, leaving about 54,000 runs per logical state. Figure 5 separately
recomputes selected quantities with and without final data-qubit leakage rejection and labels the
former series as having no postselection.

## Syndrome convention [paper_fact]
Fact ID: remm-syndrome-convention
Source locator: Sec. II, paragraph beginning "The stabilizers are repeatedly measured"
PDF page: 2
Claim: Because the auxiliary qubits are not reset between error-correction cycles, the source infers `s_m = M_(m-1) M_m` from consecutive readouts and defines the syndrome element as `sigma_m = (1 - s_(m-1) s_m)/2`.

The pipelined circuit measures X- and Z-type stabilizers at half-cycle offsets. Boundary syndrome
elements additionally use preparation or final data readout and are excluded from the
bulk-correlation average in Eq. (9).

## QEC-facing error classes [paper_fact]
Fact ID: remm-error-classes
Source locator: Sec. II and Fig. 1f
PDF page: 4
Claim: The source organizes circuit errors by their observed syndrome signatures into boundary, time-like, readout-misclassification, space, space-time, hook and two-qubit-gate classes.

## Standard matching abstraction [paper_fact]
Fact ID: remm-standard-mwpm
Source locator: Sec. III, Eqs. (3)–(8)
PDF page: 4
Claim: Selected pair-signature probabilities are converted into syndrome-graph weights and supplied to minimum-weight perfect matching, with X- and Z-type syndromes decoded separately.

The construction uses a bulk time-translation approximation and a finite maximum temporal
separation.

## Signature identifiability [paper_fact]
Fact ID: remm-signature-identifiability
Source locator: Sec. III, paragraph beginning "Next, we will discuss"
PDF page: 5
Claim: Distinct physical errors that produce the same syndrome signature are observationally indistinguishable in this analysis and are represented as one effective error process on the auxiliary-qubit graph.

This aggregation is separate from the later assumption that distinct effective error-process
indicators are statistically independent.

## Experimental covariance structure [paper_fact]
Fact ID: remm-covariance-structure
Source locator: Sec. IV, Eq. (9) and Fig. 3a
PDF page: 7
Claim: The 16-cycle data resolve distinct covariance structures at integer and half-integer cycle separation, including nearest-neighbour space correlations, same-auxiliary consecutive-cycle correlations and smaller two-cycle diagonal correlations.

The authors connect several short signatures to standard circuit-level Pauli and readout processes.

## General correlation-to-probability inversion [paper_fact]
Fact ID: remm-general-inversion
Source locator: Sec. IV, Eq. (10); Appendices E–F
PDF page: 7
Claim: Equation (10) defines an error-signature probability model that assigns a closed-form probability to a selected arbitrary-weight signature from measured syndrome moments and probabilities assigned to strict supersets of that signature.

Numerical validation in Fig. 12 uses 83 artificial error channels with signatures on as many as 12
nodes, 100,000 shots and about 30 minutes of laptop computation. This tests the inversion under its
declared artificial-data assumptions.

## Independent-process assumption [paper_fact]
Fact ID: remm-independent-process-assumption
Source locator: Appendix E, Eq. (E3) and paragraph defining `F`
PDF page: 18
Claim: The derivation of Eq. (10) assumes that the random indicators for every two distinct effective error processes factorize, even when their syndrome-signature sets overlap.

The assumption concerns the latent process indicators `F`; it does not assert that measured
syndrome elements are independent. Each `F` is indexed by an unordered set of distinct syndrome
nodes and has probability `(1 - <F>)/2`.

## Truncated signature catalogue [paper_fact]
Fact ID: remm-signature-selection
Source locator: Sec. IV, paragraphs following Eq. (10)
PDF page: 8
Claim: Because one 16-cycle run yields 124 syndrome elements and exhaustive treatment of `2^124` signatures is infeasible, the experimental analysis retains 116 signatures generated by selected circuit-level Pauli errors and 4,360 high-correlation signatures.

The added C class includes subsets on one auxiliary qubit over nine consecutive syndrome-cycle
positions, corresponding to maximum separation `Delta-m_max = 8`, and subsets around one data
qubit separated by at most two cycles. The maximum separation is limited by exponential growth of
the subset catalogue.

## Omitted-signature bias [paper_fact]
Fact ID: remm-omitted-signature-bias
Source locator: Sec. IV; Appendix F and Table III
PDF page: 18
Claim: If important high-weight signatures are omitted, the renormalized inversion can overestimate lower-weight pair processes, underestimate single-node processes and even produce negative inferred probabilities.

Appendix F demonstrates the bias with `p_1 = 3%`, `p_12 = 2.5%` and `p_123 = 1%`: omitting the
three-node process gives `p_check_2 = p_check_3 = -1%` and `p_check_12 = 3.4%`.

## Circuit-Pauli comparison [paper_fact]
Fact ID: remm-pauli-simulation-comparison
Source locator: Sec. IV and Fig. 3b; Appendix G
PDF page: 8
Claim: A uniform circuit-level Pauli simulation calibrated from independent average gate and readout quantities reproduces broad experimental error-class totals, with a notable discrepancy for correlated bit flips associated with CZ gates.

The source states that this simulation omits leakage and readout-misclassification processes and
that those omissions could explain part of the residual difference from experiment.

## Long-time covariance [paper_fact]
Fact ID: remm-long-time-covariance
Source locator: Sec. V and Fig. 5a
PDF page: 9
Claim: The average same-auxiliary syndrome covariance displays a positive tail beyond the idealized two-cycle range and is fitted for `Delta-m > 2` as proportional to `0.89^Delta-m` through the plotted separation `Delta-m = 11`.

The Fig. 5a points are averaged over the eight auxiliary qubits and their error bars are one standard
deviation across those qubits.

## Leakage-consistency evidence [paper_fact]
Fact ID: remm-leakage-consistency
Source locator: Sec. V and Fig. 5b–c
PDF page: 9
Claim: Final-readout leakage rejection and inclusion of long high-correlation signatures change the extracted readout-misclassification probabilities in a pattern that the source finds consistent with undetected data-qubit leakage that seeps back before final readout.

## Competing causes for the long tail [paper_fact]
Fact ID: remm-competing-attribution
Source locator: Sec. V, paragraphs discussing Fig. 5
PDF page: 9
Claim: The paper retains time-varying bit-flip rates and quasiparticle-related processes as alternative explanations for the long-time syndrome covariance, alongside undetected leakage.

Energy-relaxation asymmetry alone is argued not to explain the leakage-rejection dependence.

## Control-error diagnostic [paper_fact]
Fact ID: remm-control-diagnostic
Source locator: Sec. V and Fig. 4b
PDF page: 8
Claim: Error-signature pairs expected to have equal X and Y probabilities reveal one data-qubit circuit location with approximately `p_X = 2 p_Y`, which the source interprets as consistent with a control miscalibration while retaining microwave crosstalk as an alternative.

## Correlated decoder operation [paper_fact]
Fact ID: remm-correlated-decoder-operation
Source locator: Appendix C.1–C.3, Eqs. (C1)–(C3)
PDF page: 11
Claim: The correlated minimum-weight perfect matching procedure first decodes one syndrome type, uses inferred Pauli-Y-compatible signatures to replace complementary-graph probabilities by leading-order conditional probabilities, interpolates the update with strength `gamma`, and repeats decoding once.

The method targets cross-type X/Z correlation produced by Pauli-Y errors; the propagated Y-error
signatures used for the update can occupy one or two consecutive stabilizer-readout rounds.

## Experimental decoder result [paper_fact]
Fact ID: remm-decoder-result
Source locator: Appendix C and Fig. 8
PDF page: 13
Claim: At the selected interpolation strength `gamma = 0.09`, the reported experimental error per cycle is `3.873 +/- 0.203%` for standard MWPM and `3.869 +/- 0.201%` for correlated MWPM, and the source states that the difference is not statistically significant.

The fitted difference is 0.004 percentage points. Figure 8 scales its displayed fidelity error bars by
a factor of ten for visibility, and its caption states that the weights and fidelities are calculated
from the same dataset.

## Finite-sample sensitivity [paper_fact]
Fact ID: remm-finite-sample-sensitivity
Source locator: Appendix C.3–C.4 and Fig. 9
PDF page: 15
Claim: In the experimental data, update strengths only slightly above `gamma = 0.09` worsen decoding for several cycle counts, whereas a homogeneous simulated dataset with about 12 times more syndrome readouts sustains improvement until the breakdown reported for `gamma > 0.8`.

The source presents this as a qualitative investigation and conjectures that the contrast arises from
larger statistical fluctuations in the experimentally inferred conditional probabilities.

## Heterogeneity sensitivity [paper_fact]
Fact ID: remm-heterogeneity-sensitivity
Source locator: Appendix C.4 and Fig. 10
PDF page: 15
Claim: In illustrative surface-17 simulations, changing the spread of heterogeneous gate error rates changes which correlated-decoder update strengths improve or degrade fidelity.

The source explicitly says these simple simulations are not intended to fully reproduce the device.

## Drift confounder [paper_fact]
Fact ID: remm-drift-confounder
Source locator: Appendix I, Eqs. (I1)–(I4)
PDF page: 19
Claim: The Appendix I example is a nonstationarity-induced apparent correlation: pooling two acquisition periods with different but internally independent error rates produces a nonzero inferred pair-error probability that is absent at the same stationary mean rate.

For a smaller fractional rate change `epsilon`, the apparent pair probability scales as
`epsilon^2 p^2` in the stated example.

## Strict-memory-formalism boundary [literature_gap]
Fact ID: remm-gap-nonmarkovianity
Source locator: Abstract; Secs. I–VI; Appendices A–I
PDF page: 1
Claim: The source does not test CP divisibility, information backflow, process-tensor conditional independence or another criterion for strict quantum non-Markovianity.
Gap scope: source_local

Its empirical covariance and error-signature model are compatible with several stationary and
nonstationary explanations.

## Microscopic-attribution boundary [literature_gap]
Fact ID: remm-gap-attribution
Source locator: Secs. V–VI and Fig. 5
PDF page: 9
Claim: The source does not uniquely identify the microscopic process responsible for the long-time covariance tail.
Gap scope: source_local

Leakage, changing rates and quasiparticle-related processes remain in play, and no single candidate
carrier is manipulated while the repeated-QEC task is held fixed.

## Memory-aware-benefit boundary [literature_gap]
Fact ID: remm-gap-memory-aware-benefit
Source locator: Sec. III; Appendix C
PDF page: 11
Claim: The source does not compare a decoder with and without access to the long-time record or an explicit inferred memory state under otherwise matched conditions.
Gap scope: source_local

The tested correlated update uses cross-type Pauli-Y information, and its experimental difference is
not statistically significant.

## Transfer boundary [literature_gap]
Fact ID: remm-gap-transfer
Source locator: Secs. IV–VI; Appendices C–I
PDF page: 10
Claim: The source does not test deployment of a fixed inferred model or decoder on a held-out device, code family or independently calibrated operating regime.
Gap scope: source_local

The illustrative simulations diagnose uncertainty and heterogeneity effects; they are not a transfer
experiment.

