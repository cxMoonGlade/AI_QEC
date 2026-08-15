+++
schema = "error_coupling_simulator.literature.note.v1"
source_id = "arxiv:2607.28422"
source_version = "v1"
source_uri = "https://arxiv.org/abs/2607.28422v1"
source_artifact = "outputs/overview/literature/final_expansion/sources/2607.28422.pdf"
source_sha256 = "2c8f6fec9a1dd0a76f041d76cdd4b76be74ee466a7cbb9719f15637f13144c7c"
title = "QAdapt: A Noise-Adaptive Neural Pre-Decoding Framework for Quantum Error Correction"
publication_status = "preprint"
read_status = "complete"
evidence_status = "persisted"
review_scope = "full_text"
operation_replay_status = "complete"
audit_packet = "docs/simulator_validation/literature_expansion_round3/QADAPT_2607_28422_AUDIT_2026-08-05.md"
audit_packet_sha256 = "99bec4adbd88848246a4dee164e82d459c55f2e206fd1ee5315f139ef6027fdc"
admission_status = "source_only_reviewed"
admission_reviewer = "/root/validate_hockings"
admission_date = "2026-08-05"
visually_checked_pages = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]

[[relations]]
predicate = "defines"
object_id = "qadapt-residual-syndrome"
object_type = "observable"
object_label = "residual detector tensor"
fact_id = "qadapt-residual-interface"

[[relations]]
predicate = "uses"
object_id = "qadapt-htnet"
object_type = "method"
object_label = "HTNet"
fact_id = "qadapt-spatiotemporal-branches"

[[relations]]
predicate = "uses"
object_id = "qadapt-q-ewc"
object_type = "method"
object_label = "Q-EWC"
fact_id = "qadapt-ewc-schedule"

[[relations]]
predicate = "supports"
object_id = "qadapt-willow-zero-shot-result"
object_type = "observable"
object_label = "On Willow"
fact_id = "qadapt-willow-result"

[[relations]]
predicate = "limits"
object_id = "qadapt-backend-latency-boundary"
object_type = "limitation"
object_label = "PyMatching on the residual syndrome"
fact_id = "qadapt-latency-boundary"
+++
# Full-text review — Miao et al., "QAdapt: A Noise-Adaptive Neural Pre-Decoding Framework for Quantum Error Correction"

## Source identity [paper_fact]
Fact ID: qadapt-source-identity
Source locator: Title page, arXiv margin stamp and official version metadata
PDF page: 1
Claim: The fixed source is the 11-page arXiv:2607.28422v1 preprint by Ran Miao, Rui Luo, Xiaohan Shan and Xiaoming Sun, submitted on 30 July 2026.

The artifact contains the main text, Appendices A–D, six figures, six tables and references. The
official arXiv version history contained only v1 at the time of review.

## Selection scope [paper_fact]
Fact ID: qadapt-selection-scope
Source locator: Abstract; Sec. 1
PDF page: 1
Claim: The source develops a neural pre-decoding pipeline for rotated-surface-code memory data that is trained across predefined noise tasks and evaluated under synthetic distribution shifts and on an external Willow dataset.

The learned local-correction stage passes a residual syndrome to PyMatching rather than replacing
the global decoder.

## Syndrome-density observable [paper_fact]
Fact ID: qadapt-syndrome-density
Source locator: Sec. 3.1; Eq. (1)
PDF page: 3
Claim: Input syndrome density is the mean of the binary detector observations at fixed distance, logical basis and number of rounds, and the source states that it is not a complete noise characterization because different correlated processes can have similar density.

The paper uses density as a decoder-workload indicator and as the threshold variable for its
hardware-anchored high-load subset.

## Residual-syndrome interface [paper_fact]
Fact ID: qadapt-residual-interface
Source locator: Sec. 3.1; Eq. (2); Sec. 4.5
PDF page: 3
Claim: QAdapt maps predicted local corrections through a detector–correction incidence map to form the residual detector tensor `s_res = s XOR H e_hat`, which is then decoded by PyMatching.

The final logical decision remains the output of the global matching problem.

## Detector-tensor representation [paper_fact]
Fact ID: qadapt-detector-tensor
Source locator: Sec. 4.2
PDF page: 3
Claim: HTNet takes a four-channel binary detector tensor indexed over syndrome rounds and two spatial lattice dimensions and gives its three blocks an effective receptive field of nine rounds or lattice positions along each convolved dimension.

The source denotes the input as `x` in `{0,1}^{4 x T x D x D}` before the batch dimension shown in
Fig. 3.

## Spatiotemporal feature branches [paper_fact]
Fact ID: qadapt-spatiotemporal-branches
Source locator: Sec. 4.2; Eqs. (3)–(7); Fig. 3
PDF page: 3
Claim: HTNet applies separate spatial, temporal and joint convolution branches and fuses them with per-sample, per-channel weights before further feature mixing and gating.

The printed kernels are `1 x 3 x 3`, `3 x 1 x 1` and grouped `3 x 3 x 3`, respectively. The source
interprets them as within-round, cross-round and coupled local space–time feature extractors.

## Axis–channel calibration [paper_fact]
Fact ID: qadapt-axis-channel-gate
Source locator: Sec. 4.3; Eq. (8)
PDF page: 4
Claim: HTNet adds channel, temporal and spatial logits before a sigmoid gate so that evidence on one axis can compensate for weaker evidence on another.

A raw-evidence skip concatenates the original detector channels before the output head.

## Q-EWC sequential schedule [paper_fact]
Fact ID: qadapt-ewc-schedule
Source locator: Sec. 4.4; Eq. (9); Sec. 5.2; Appendix B and Table 6
PDF page: 4
Claim: Q-EWC trains sequentially on base, measurement-enhanced, CNOT-enhanced, idle-enhanced and Z-bias-enhanced tasks, using 20 epochs per stage, lambda 100 and diagonal Fisher estimates from 65,536 samples.

Fisher states are captured after T0–T3 and loaded for later tasks. Each active task parameter is
multiplied by 1.5 relative to T0, while unlisted parameters remain at their T0 values.

## Offline–online boundary [paper_fact]
Fact ID: qadapt-offline-online-boundary
Source locator: Sec. 4.1; Fig. 2; Sec. 4.5
PDF page: 3
Claim: The source places sequential task generation, HTNet training and Q-EWC in the offline stage, while its online stage applies a fixed local pre-decoder, constructs a residual tensor and invokes PyMatching.

Online Fisher updates and drift detection are named as future extensions in Sec. 7.4 rather than as
operations evaluated in the paper.

## T0 circuit-level Pauli environment [paper_fact]
Fact ID: qadapt-t0-noise-model
Source locator: Sec. 5.1; Appendix A and Table 5
PDF page: 5
Claim: T0 is a 25-parameter circuit-level Pauli environment in which fixed preparation, measurement, idle and nonidentity CNOT-channel probabilities are applied per occurrence in repeated rotated-surface-code memory circuits sampled with Stim.

The Appendix-A table specifies two preparation, two measurement, six idle and fifteen two-qubit
Pauli-channel probabilities.

## Comparator configuration [paper_fact]
Fact ID: qadapt-comparator
Source locator: Sec. 5.2
PDF page: 5
Claim: Ising-fast is trained under the same T0 environment and input representation and uses the same PyMatching backend as HTNet, but the two networks have 912,772 and 650,374 parameters, respectively.

The printed T1–T4 continual schedule is assigned to QAdapt; the source describes Ising-fast as trained
under T0. It does not print Ising-fast's epoch or sample budget or identify the exact checkpoint used
for each reported comparison.

## Synthetic OOD grid [paper_fact]
Fact ID: qadapt-ood-grid
Source locator: Sec. 5.3; Appendix C
PDF page: 5
Claim: The synthetic OOD grid activates every two-, three- and four-axis combination of measurement, CNOT, idle and Z-bias perturbations at multipliers 1.2, 1.5, 2.0, 2.5 and 3.0 for distances 7 and 9, yielding 110 configurations.

All evaluation settings remain within the circuit-level Pauli parameterization listed in Appendix A.
The 110 cells exhaust this constructed design grid; they are not a sampled population of devices or
noise processes.

## High-load subset definition [paper_fact]
Fact ID: qadapt-high-load-subset
Source locator: Sec. 5.3; Sec. 6.3
PDF page: 6
Claim: The source defines its high-load subset before method comparison as the 74 synthetic configurations whose input syndrome density is at least 0.13106, the mean density measured in five batches on an anonymized cloud platform.

The anchor is measured at distance 3, logical Z and nine rounds, then applied to distance-7 and
distance-9 synthetic configurations. The paper states that it is not an end-to-end decoding result
on that platform and does not establish distributional equivalence.

## Willow no-target-update protocol [paper_fact]
Fact ID: qadapt-willow-protocol
Source locator: Sec. 5.4
PDF page: 6
Claim: The Willow evaluation uses ten-round open surface-code data without target-domain fine-tuning, parameter updates or target-domain calibration, comprising 400,000 shots at distance 5 and 100,000 shots at distance 7.

The source treats Willow as an external distribution rather than as a matched-noise benchmark.
It does not identify the hardware source of T0, document whether Willow informed architecture,
hyperparameter or checkpoint selection, bind exact checkpoints to the two distances, or state that
the reported cohorts exhaust the public release.

## Metric and timing definitions [paper_fact]
Fact ID: qadapt-metrics
Source locator: Sec. 5.5; Eq. (10)
PDF page: 6
Claim: The reported evaluation metrics are logical error rate, input detector-event fraction and PyMatching time per round after neural pre-decoding, with relative reduction defined against Ising-fast.

The timing value is explicitly characterized as backend load rather than end-to-end deployment
latency.

## Mapped-T0 result [paper_fact]
Fact ID: qadapt-t0-result
Source locator: Sec. 6.1; Table 2 and Fig. 4
PDF page: 7
Claim: Under T0, HTNet's reported LER is 0.04280 versus 0.05071 for Ising-fast at distance 7 and 0.03286 versus 0.04037 at distance 9.

The corresponding relative reductions are 15.59% and 18.61%. The figure also reports residual
PyMatching latency reductions of 7.34% and 12.04%.

## Synthetic OOD result [paper_fact]
Fact ID: qadapt-ood-result
Source locator: Sec. 6.2; Table 3 and Fig. 5
PDF page: 7
Claim: QAdapt has a lower point-estimate LER than Ising-fast in all 110 retained OOD configurations, with mean LER 0.22701 versus 0.23447 at distance 7 and 0.23653 versus 0.24444 at distance 9.

The reported mean relative LER reductions are 3.18% and 3.23%, and the residual PyMatching latency
reductions are 5.72% and 5.65%.

## High-load result [paper_fact]
Fact ID: qadapt-high-load-result
Source locator: Sec. 6.3; Fig. 5c
PDF page: 7
Claim: QAdapt has lower plotted LER than Ising-fast in all 74 synthetic configurations at or above the hardware-density anchor, with mean absolute LER difference minus 0.00788.

The source limits this to synthetic-load robustness and not a logical-decoding result on the
anonymized platform.

## Willow no-target-update result [paper_fact]
Fact ID: qadapt-willow-result
Source locator: Sec. 6.4; Table 4 and Fig. 6
PDF page: 7
Claim: On Willow, QAdapt's reported LER is 0.09386 versus 0.09963 for Ising-fast at distance 5 and 0.08201 versus 0.08412 at distance 7, corresponding to relative reductions of 5.79% and 2.51%.

Residual PyMatching time decreases from 0.704 to 0.694 microseconds per round at distance 5 and from
1.405 to 1.274 microseconds per round at distance 7, reported as 1.43% and 9.32% reductions.

## Architecture-attribution limitation [paper_fact]
Fact ID: qadapt-architecture-limitation
Source locator: Sec. 7.1
PDF page: 9
Claim: The source states that its data establish a gain for the complete architecture but do not isolate the causal contribution of individual HTNet components because no module-by-module ablation is reported.

This limitation includes the spatial, temporal and joint branches, fusion, gating and raw-evidence
skip presented in Fig. 3.

## Density-to-LER limitation [paper_fact]
Fact ID: qadapt-density-limitation
Source locator: Sec. 7.2
PDF page: 9
Claim: The source states that lower residual-syndrome density does not by itself explain the LER improvement because residual topology and matching-edge weights also affect decoding difficulty.

Co-occurring reductions in LER and backend time are therefore reported as an association rather than
a causal density bridge.

## Residual-backend latency boundary [paper_fact]
Fact ID: qadapt-latency-boundary
Source locator: Secs. 4.5 and 5.5; Sec. 7.2
PDF page: 6
Claim: The source's latency measurements include only PyMatching on the residual syndrome and exclude neural inference, host–device transfer and residual-tensor construction.

The paper states that an end-to-end claim requires joint measurement of all four components.

## OOD interpretation boundary [paper_fact]
Fact ID: qadapt-ood-boundary
Source locator: Sec. 7.3
PDF page: 9
Claim: The source interprets its synthetic grid and Willow evaluation as probing changes in noise intensity and hardware origin while explicitly stating that they do not exhaust all forms of distribution shift.

Willow's matched detector load is lower than T0, whereas the synthetic grid includes higher-density
settings.

## Stated evidence limitations [paper_fact]
Fact ID: qadapt-evidence-limitations
Source locator: Sec. 7.4
PDF page: 9
Claim: The source explicitly reports that its evidence lacks LER confidence intervals, a controlled Q-EWC-versus-unregularized-fine-tuning comparison and per-component end-to-end latency.

The same passage lists seed variation, paired-shot analysis, replay and joint mixed-noise
comparators, and component ablations as follow-up reporting or experiments.

## Demonstrated QEC reach [paper_fact]
Fact ID: qadapt-qec-reach
Source locator: Secs. 5.3–5.4 and 7.4
PDF page: 9
Claim: The reported QEC reach is rotated-surface-code memory data at synthetic distances 7 and 9 and ten-round Willow distances 5 and 7.

Longer windows, larger distances, logical operations, leakage- and crosstalk-dominated noise,
additional processors, other QEC codes and other decoding backends are listed as future extensions.

## Data availability [paper_fact]
Fact ID: qadapt-data-availability
Source locator: PDF p. 9, Data Availability section
PDF page: 9
Claim: The third-party Willow data are available through the associated Google release, while the study's synthetic and device-mapped simulation records are not publicly available at submission.

The source says editorial material will be supplied confidentially and other access requests will be
considered subject to institutional and commercial restrictions.

## Reproducibility-checklist status [paper_fact]
Fact ID: qadapt-reproducibility-checklist
Source locator: Appendix D
PDF page: 10
Claim: Appendix D prospectively instructs the authors to record code revision, configuration, checkpoint and seed, preserve disaggregated counts, separate latency components and regenerate figures from retained records.

The checklist does not itself provide those revision, checkpoint, seed or retained-record values.

## Explicit temporal-generator boundary [literature_gap]
Fact ID: qadapt-gap-temporal-generator
Source locator: Sec. 5.1 and Appendix A–C full generator specification
PDF page: 10
Claim: The source does not evaluate a noise generator with a continuing physical or latent state, a carrier lifetime or a parameterized history-dependent transition law.
Gap scope: source_local

Its fixed and perturbed environments use per-occurrence circuit-level Pauli probabilities.

## Temporal-access ablation boundary [literature_gap]
Fact ID: qadapt-gap-temporal-ablation
Source locator: Sec. 7.1 architecture limitation and full comparison scope
PDF page: 9
Claim: The source does not compare an otherwise identical decoder with and without the temporal branch, a multiround history window or access to a declared memory state.
Gap scope: source_local

The printed comparison changes the architecture and training sequence together.

## Continual-learning attribution boundary [literature_gap]
Fact ID: qadapt-gap-ewc-ablation
Source locator: Sec. 7.4
PDF page: 9
Claim: The source does not report controlled comparisons of Q-EWC with unregularized sequential fine-tuning, replay or joint mixed-noise training.
Gap scope: source_local

The reported OOD advantage therefore belongs to the complete QAdapt package rather than to an
isolated continual-learning operation.

## Wrong-history-model robustness boundary [literature_gap]
Fact ID: qadapt-gap-wrong-history-model
Source locator: Secs. 5.1–5.3 and Appendix A–C full evaluation boundary
PDF page: 10
Claim: The source does not test robustness to an incorrect temporal kernel, hidden-state transition, carrier lifetime, mixed memory mechanism or history-model calibration.
Gap scope: source_local

The OOD grid changes static error-type probabilities within the same circuit-level Pauli family.

## LER uncertainty boundary [literature_gap]
Fact ID: qadapt-gap-ler-uncertainty
Source locator: Sec. 7.4
PDF page: 9
Claim: The source does not report LER confidence intervals, seed variation or a paired-shot statistical comparison for its synthetic or Willow decoder results.
Gap scope: source_local

Willow shot counts are given, but no uncertainty is attached to the LER differences.

## Synthetic data-split boundary [literature_gap]
Fact ID: qadapt-gap-synthetic-splits
Source locator: Secs. 5.1–5.3, Appendix B–D and Data Availability
PDF page: 10
Claim: The source does not state synthetic training and evaluation shot counts, train/validation/test splits, evaluation round counts, random seeds or checkpoint-selection rules.
Gap scope: source_local

The task environments, epoch counts and Fisher-sample count are specified, but those fields are not.

## Code-availability boundary [literature_gap]
Fact ID: qadapt-gap-code-availability
Source locator: Data Availability, Appendix D and full-text availability-statement boundary
PDF page: 10
Claim: The source does not provide a code-availability statement, public source-code link, exact code revision or model checkpoint.
Gap scope: source_local

Appendix D lists revision and checkpoint recording as prospective reproducibility steps.

## End-to-end latency boundary [literature_gap]
Fact ID: qadapt-gap-end-to-end-latency
Source locator: Secs. 5.5, 7.2 and 7.4
PDF page: 9
Claim: The source does not report end-to-end decoding latency, neural inference time, transfer time, residual-construction time, execution hardware, timing repetitions or timing dispersion.
Gap scope: source_local

Only the residual PyMatching component is measured.

## Cross-code and cross-device transfer boundary [literature_gap]
Fact ID: qadapt-gap-cross-setting-transfer
Source locator: Secs. 5.4 and 7.4
PDF page: 9
Claim: The source does not evaluate a fixed model across different QEC code families, decoder backends or multiple independent hardware devices.
Gap scope: source_local

Its external result is a source-reported no-target-update evaluation on one Willow release within
the rotated-surface-code memory setting; strict target-unseen selection is not auditable.

## Checkpoint-to-distance boundary [literature_gap]
Fact ID: qadapt-gap-checkpoint-distance
Source locator: Secs. 5.2–5.4 and full model/evaluation protocol
PDF page: 6
Claim: The source does not state whether one identical trained checkpoint is reused across distances 5, 7 and 9 or whether separate distance-specific checkpoints are frozen for evaluation.
Gap scope: source_local

No cross-distance parameter-sharing claim can be reconstructed from the printed protocol.

## Target-exposure and cohort boundary [literature_gap]
Fact ID: qadapt-gap-target-exposure
Source locator: Secs. 3.2, 5.1–5.4 and complete model-selection protocol
PDF page: 6
Claim: The source does not identify T0's source hardware, state whether Willow records or summaries were excluded from architecture, hyperparameter, threshold and checkpoint selection, identify the exact evaluated checkpoints, or document Willow cohort filtering and paired record reuse.
Gap scope: source_local

The reported absence of target-domain fine-tuning, parameter updates and calibration during
evaluation remains a valid source statement, but a strict target-unseen frozen-transfer protocol
cannot be reconstructed.
