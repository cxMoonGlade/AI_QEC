# Claim audit — Takou et al. on syndrome-estimated detector error models

## Fixed source and reading scope

- Fixed artifact: `docs/papers/Logical_error_estimation_from_syndrome_data_of_surface_code_experiments2606.11496v2.pdf`
- Identity: arXiv:2606.11496v2, *Logical error estimation from syndrome data of surface-code
  experiments*, Evangelia Takou and coauthors, version dated 12 June 2026 and manuscript dated
  15 June 2026.
- Artifact verification: 19 pages, 6,078,283 bytes, SHA-256
  `4441789ebbe43aab4cae64bfda047ccd55c66c42acd9aada63fe87294767aaeb`.
- Reading scope: all 19 pages, including Appendices A--H and references. The PDF, not discovery
  metadata or the retained text extraction, is the evidentiary source.
- Visual verification: artifact pages 1--6 and 13 were rendered from the fixed PDF. These checks
  covered source identity, Willow and IBM tasks, Figs. 1--4, the stated limitations, and the
  correlated-MWPM comparison in Fig. 7.

## Assigned coverage rows

| row | source location | source says | source does not say | status |
|---|---|---|---|---|
| D1 — hardware memory-conditioned decoder benefit | Main pp. 1--5; Appendix E, Fig. 7, p. 13 | Syndrome-estimated DEM probabilities reduce decoded logical error probabilities on released Google Willow data and new IBM `ibm_miami` repeated surface-code data relative to declared baseline priors. | The comparison does not isolate access to a continuing carrier, an inferred memory state, a longer history window, or record order. Rates are estimated per detector support and cycle; this is not a fitted temporal transition law. | missing for memory-conditioned benefit; positive adjacent hardware-prior evidence |
| D2 — population-level matched decoder comparison | Figs. 1--4, pp. 2--5; Eq. (1); figure captions | Many device subsystems, bases, distances and cycle counts are evaluated with the same MWPM family. For Willow, the comparisons use common 50,000-shot ensembles and propagate shot-level covariance. The IBM results extend the method to a second device. | For Willow, the same shots are used to estimate the prior and evaluate logical outcomes. No independent calibration/test split is used, and the comparison is not a one-factor memory-access ablation. The IBM shot count is not stated, and its error bars are identified only as standard deviations rather than the Willow covariance-aware construction. | partial/adjacent, not a clean memory-benefit closure |
| R1 — wrong-memory-model robustness | Main pp. 4--5; Appendix B, pp. 9--11; Appendix E, p. 13 | Negative or unresolved detector correlators, missing support and rates above one half expose failure modes; the implementation bootstraps signs, zeroes selected unphysical estimates and regularizes some matching weights. | It does not freeze a decoder or estimator and vary an incorrect carrier law, temporal transition model, mixed mechanism or independent calibration regime. | missing |
| T1 — frozen transfer | Main pp. 1--5 | The same general estimation recipe is applied to Willow and `ibm_miami`, spanning different devices, rotated versus unrotated distance-three instances, Willow distances 3, 5 and 7, and different cycle counts. | Each experimental instance receives newly estimated probabilities from its own syndromes and inherits support/decomposition from a device-appropriate reference DEM. No one frozen inferred model or decoder is deployed across devices or codes. | missing for frozen transfer; positive method-portability evidence |
| A5 — hardware record-to-model approach coverage | Main pp. 1--5; Appendices A--F | The work supplies a broad hardware-record-to-DEM-to-logical-evaluation bundle with cycle-resolved event probabilities, two devices and multiple repeated-QEC instances. | Its estimated object is an independent-event DEM on a supplied support; it does not reproduce the long-lag covariance and signature treatment represented by the Remm row. Neither source defines a continuing carrier-state transition law. | adjacent, not a replacement for the memory-specific Remm row |

## Operation replay

| input | transformation | assumption or resource | output | exact source location | replay status |
|---|---|---|---|---|---|
| Willow rotated-surface-code records | Use detector moments from 50,000 shots for each instance to estimate event probabilities on either SI1000 or RL-derived detector-logical support | The same released shots are subsequently decoded; logical outcomes are not used during probability estimation | `estSI1000` and `estRL` decoder priors | Main pp. 2--4 | complete |
| IBM unrotated distance-three records through 19 cycles, with and without XY4 | Estimate event probabilities on IBM-like support and apply the same graphlike decomposition used by the reference DEM | Ancillas are not unconditionally reset; detector definitions compare readouts two cycles apart | `estIBM` decoder prior and repeated-memory logical outcomes | Main pp. 4--5 and Fig. 4 | complete |
| Detector-event moments for support sets of size at most four | Apply hierarchical strict-superset subtraction; bootstrap unresolved signs; set selected negative estimates to zero | Independent-event representation on the supplied support; omitted mechanisms and hyperedges may remain | Effective DEM probabilities or detector-moment diagnostics | Appendix B, pp. 9--11 | complete |
| Common experimental record and alternative DEM priors | Decode with MWPM and compare finite-memory logical error probability using fractional change in Eq. (1) | The quantum task and shot ensemble are fixed; fitted prior and evaluation data are not independently split | Willow reductions typically in the reported 5--10% range and IBM reductions of similar order, with larger single-cycle IBM cases | Figs. 1--4, pp. 3--5 | complete |
| Paired logical decisions from two priors on the same shots | Propagate binomial variances and the covariance of the two logical-error estimates | This accounts for shot statistics, not common-mode device fluctuations or prior-estimation reuse | Delta-method standard errors for Willow comparisons | Figs. 1--2 captions, p. 3; Appendix H, p. 16 | complete |
| IBM-like or estimated prior | Decode with standard or correlated MWPM | Some estimated rates above one half are capped only for the correlated-MWPM input; the source labels this regularization rather than mechanism estimation | Four-arm comparison showing the estimated prior and correlated decoder can provide complementary gains | Appendix E, Fig. 7, p. 13 | complete |

## Interpretation boundaries

- The source demonstrates that syndrome-derived decoder priors can improve logical performance on
  repeated-QEC hardware records. It does not show that access to a physical memory variable causes
  that gain.
- Allowing event probabilities to vary by cycle captures temporal inhomogeneity. It does not define
  a transition law, persistence time or formal non-Markovian process.
- The record contains correlations and rate trends. A detector firing probability or covariance is
  insufficient for unique microscopic attribution; the paper itself treats coherent ZZ crosstalk
  and leakage accumulation as plausible, setting-dependent interpretations.
- Applying one recipe to two devices establishes methodological portability. Re-estimating the
  model on every instance is adaptation, not frozen cross-device transfer.
- This source is a stronger adjacent comparison than Remm for broad hardware record-to-prior
  logical benefit, but Remm remains the more direct representative of explicitly multicycle
  signature inference. They answer different questions and should not be collapsed into one row.

## Kill conditions

- Kill any claim that the source demonstrates memory-conditioned decoder benefit: no comparator
  removes or randomizes declared history access while holding the rest fixed.
- Kill any claim of held-out prior validation: the Willow event probabilities and logical metrics
  use the same 50,000-shot ensemble for each instance.
- Kill any claim of frozen cross-device transfer: probabilities and reference supports are
  instance-specific.
- Kill any claim that cycle-varying DEM rates identify strict quantum non-Markovianity, leakage or
  another unique microscopic carrier.
- Kill any claim that estimated event support is exhaustive: the paper explicitly retains missing
  hyperedges and correlated mechanisms as limitations.

## Source-local verdict

- `read_status`: complete
- D1: missing for memory-conditioned benefit; adjacent hardware-prior benefit is positive
- D2: partial; Willow has broad common-shot comparisons with covariance-aware uncertainty, whereas
  the IBM shot count and error-bar construction are not reported at the same specificity; neither
  device has a held-out or memory-only arm
- R1: missing for wrong-memory-law robustness
- T1: missing for frozen transfer; method portability across two devices is positive
- A5: adjacent citation-chain bundle; do not replace the memory-specific Remm comparison row
