+++
schema = "error_coupling_simulator.literature.note.v1"
source_id = "arxiv:2606.11496"
source_version = "v2"
source_uri = "https://arxiv.org/abs/2606.11496v2"
source_artifact = "docs/papers/Logical_error_estimation_from_syndrome_data_of_surface_code_experiments2606.11496v2.pdf"
source_sha256 = "4441789ebbe43aab4cae64bfda047ccd55c66c42acd9aada63fe87294767aaeb"
title = "Logical error estimation from syndrome data of surface-code experiments"
publication_status = "preprint"
read_status = "complete"
evidence_status = "persisted"
review_scope = "full_text"
operation_replay_status = "complete"
audit_packet = "docs/simulator_validation/literature_expansion_round3/TAKOU_SYNDROME_DEM_2606_11496_AUDIT_2026-08-05.md"
audit_packet_sha256 = "890e1e6fdbf4a75da109499464e62fb93a35daa7b904a0db88563802dd1cd95e"
admission_status = "source_only_reviewed"
admission_reviewer = "/root/validate_ziad"
admission_date = "2026-08-05"
visually_checked_pages = [1, 2, 3, 4, 5, 6, 9, 13]

[[relations]]
predicate = "derives"
object_id = "takou-syndrome-estimated-dem"
object_type = "model"
object_label = "independent-event probabilities"
fact_id = "takou-dem-estimation"

[[relations]]
predicate = "uses"
object_id = "takou-hierarchical-moment-inversion"
object_type = "method"
object_label = "hierarchical strict-superset subtraction"
fact_id = "takou-dem-estimation"

[[relations]]
predicate = "uses"
object_id = "takou-mwpm-comparison"
object_type = "method"
object_label = "minimum-weight perfect matching family"
fact_id = "takou-decoder-comparison"

[[relations]]
predicate = "supports"
object_id = "takou-hardware-prior-benefit"
object_type = "observable"
object_label = "syndrome-estimated priors"
fact_id = "takou-willow-results"

[[relations]]
predicate = "limits"
object_id = "takou-same-shot-evaluation"
object_type = "limitation"
object_label = "same 50,000 experimental shots"
fact_id = "takou-same-shot-boundary"
+++
# Full-text review — Takou et al., syndrome-estimated detector error models

## Source identity [paper_fact]
Fact ID: takou-source-identity
Source locator: Title page, arXiv version stamp and manuscript date
PDF page: 1
Claim: The fixed source is the 19-page arXiv:2606.11496v2 preprint by Evangelia Takou and coauthors, whose visible version stamp is dated 12 June 2026 and whose title page gives a manuscript date of 15 June 2026.

The artifact includes the main text, Appendices A--H and references.

## Selection scope [paper_fact]
Fact ID: takou-selection-scope
Source locator: Abstract, p. 1; Introduction, pp. 1--2
PDF page: 1
Claim: The source asks whether detector-error-model event probabilities estimated directly from repeated-QEC syndrome records can serve as decoder priors and reduce finite-memory logical error probabilities on Google Willow and IBM `ibm_miami` hardware data.

It estimates an effective detector-level model on supplied support. It does not reconstruct a unique
microscopic noise process.

## Willow task [paper_fact]
Fact ID: takou-willow-task
Source locator: Main text, paragraph beginning "Estimations from Willow processor"
PDF page: 2
Claim: The Willow evaluation uses released rotated-surface-code X- and Z-memory records with 50,000 shots for distances 3, 5 and 7, multiple distance-three subsystems and cycle counts drawn from 1, 10, 13, 30, 50 and 70.

Each instance includes an SI1000 detector error model and an RL-optimized model used as alternative
sources of detector-logical support and hyperedge decomposition.

## IBM task [paper_fact]
Fact ID: takou-ibm-task
Source locator: Main text, paragraph beginning "Estimations from ibm_miami" and Fig. 3
PDF page: 4
Claim: The IBM evaluation runs unrotated distance-three X- and Z-memory circuits through as many as 19 syndrome-extraction cycles, both without dynamical decoupling and with XY4, on `ibm_miami`.

Ancillas are not unconditionally reset, so the detector definition compares the corresponding
measurement outcomes two cycles apart. The manuscript does not state the number of IBM shots.

## Detector-level representation [paper_fact]
Fact ID: takou-dem-representation
Source locator: Main pp. 1--2; Appendix A
PDF page: 2
Claim: The estimated object retains a fixed set of detector and logical-observable signatures from a reference detector error model and replaces their event probabilities using empirical detector moments from the QEC record.

The support and its graphlike decomposition remain inherited from SI1000, RL-optimized or IBM-like
models. The inferred probabilities may vary between cycle-translated detector locations because the
main analysis does not average them over time.

## Moment-inversion computation [paper_fact]
Fact ID: takou-dem-estimation
Source locator: Appendix B, Eqs. (B3), (B4) and (B8)
PDF page: 9
Claim: The estimator uses hierarchical strict-superset subtraction to infer independent-event probabilities on declared detector support sets of size at most four from empirical detector correlators.

When a correlator sign is unresolved the source bootstraps the detector-event records 100 times and
replaces selected unresolved values; selected negative event-probability estimates are set to zero.

## Decoder comparison [paper_fact]
Fact ID: takou-decoder-comparison
Source locator: Main Eq. (1); Figs. 1--4
PDF page: 2
Claim: Alternative reference and syndrome-estimated detector error models are supplied as priors to the same minimum-weight perfect matching family, and their finite-memory logical error probabilities are compared on common experimental shot ensembles.

Appendix E additionally crosses IBM-like versus estimated priors with standard versus correlated
MWPM, while regularizing selected weights that are incompatible with that correlated-MWPM
implementation.

## Willow logical results [paper_fact]
Fact ID: takou-willow-results
Source locator: Main Figs. 1--2 and surrounding text
PDF page: 3
Claim: Across the displayed Willow instances, syndrome-estimated priors usually lower logical error probability relative to SI1000, with reductions reaching about ten percent in selected cases, and perform comparably to the RL-optimized priors with the ordering varying by instance.

The figures report the fractional change relative to SI1000 rather than one pooled field-wide effect.

## IBM logical results [paper_fact]
Fact ID: takou-ibm-results
Source locator: Main Fig. 4 and surrounding text
PDF page: 4
Claim: Across the displayed IBM memory conditions, the syndrome-estimated prior lowers logical error probability relative to the IBM-like prior by roughly five to ten percent in many cases, with reported single-cycle Z-memory reductions of about 37 percent without XY4 and 18 percent with XY4.

The IBM-like prior is not calibrated to the effective idle-noise suppression created by the
dynamical-decoupling sequence.

## Logical uncertainty [paper_fact]
Fact ID: takou-logical-uncertainty
Source locator: Figs. 1--2 captions; Appendix H
PDF page: 3
Claim: Willow fractional-change error bars use a delta-method standard error that propagates binomial variances and the covariance between two logical-error estimates evaluated on the same shots.

The appendix states that propagated errors omit common-mode device fluctuations and some
SPAM-calibration contrasts. Figure 4 labels IBM error bars as standard deviations without providing
the IBM shot count in the manuscript.

## Same-shot evaluation boundary [paper_fact]
Fact ID: takou-same-shot-boundary
Source locator: Main paragraph beginning "For each Willow experimental instance"
PDF page: 2
Claim: For every Willow instance, event probabilities are estimated from the same 50,000 experimental shots that are subsequently decoded, although the final logical success or failure labels are not used in the estimation step.

The source therefore controls the quantum record within a comparison but does not provide an
independent prior-estimation and logical-evaluation split.

## Correlated-MWPM comparison [paper_fact]
Fact ID: takou-correlated-mwpm
Source locator: Appendix E and Fig. 7
PDF page: 13
Claim: On the IBM records, crossing estimated versus IBM-like priors with standard versus correlated MWPM shows that improved prior probabilities and the more refined decoder can provide complementary logical-error reductions.

For this comparison, estimated probabilities above one half are capped for the correlated-MWPM
input; the paper explicitly calls this decoder-input regularization rather than an estimate of the
microscopic mechanism probability.

## Temporal-structure interpretation [paper_fact]
Fact ID: takou-temporal-interpretation
Source locator: Main pp. 2 and 5; Appendix D
PDF page: 5
Claim: The source reports cycle-dependent detector rates, space-time covariances and cycle-resolved effective event probabilities, while cautioning that detector statistics alone do not identify a microscopic error mechanism.

Leakage accumulation is described as plausible for IBM rate growth without leakage removal, and
coherent ZZ crosstalk is one plausible explanation for a dynamical-decoupling-sensitive feature.
Neither is uniquely established by the DEM inversion.

## Memory-benefit boundary [literature_gap]
Fact ID: takou-gap-memory-benefit
Source locator: Main text and Appendices A--H
PDF page: 2
Claim: The source does not compare otherwise-matched decoders with and without access to a continuing physical or latent state, different history windows, or preserved versus randomized cycle order.
Gap scope: source_local

Cycle-resolved probabilities represent temporal inhomogeneity but do not define a carrier-transition
law or show that physical memory access causes the logical benefit.

## Wrong-memory-model boundary [literature_gap]
Fact ID: takou-gap-memory-robustness
Source locator: Main limitations; Appendices B and F
PDF page: 5
Claim: The source does not hold an estimator or decoder frozen while varying an incorrect temporal transition law, carrier dynamics, mixed mechanism or independent calibration regime.
Gap scope: source_local

Its negative-correlator, support-omission and weight-regularization diagnostics are important
estimator failure modes but are not a wrong-memory-model robustness experiment.

## Frozen-transfer boundary [literature_gap]
Fact ID: takou-gap-frozen-transfer
Source locator: Main pp. 1--5
PDF page: 2
Claim: The source does not deploy one fixed inferred detector error model or decoder prior across Willow and IBM, across code distances, or across independent operating regimes without re-estimation.
Gap scope: source_local

The general recipe is portable, but every instance uses its own syndrome-derived probabilities and
a device-appropriate reference support.

## Section-3 comparison boundary [paper_fact]
Fact ID: takou-section-three-boundary
Source locator: Main pp. 1--5
PDF page: 2
Claim: The source is a concrete record-to-effective-model-to-decoder bundle, but its history-bearing object is not a continuing carrier or explicit multicycle transition model.

It is therefore a strong adjacent hardware-prior comparison for an evidence section, not an
automatic replacement for an approach selected specifically to represent persistent multicycle
signature variables.
