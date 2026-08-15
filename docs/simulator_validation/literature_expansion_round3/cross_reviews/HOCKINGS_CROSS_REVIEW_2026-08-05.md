# Independent cross-review — Hockings et al., arXiv:2502.21044v2

## Decision

**PASS.** The fixed audit and draft source note are faithful to the official v2 artifact on all
load-bearing points assigned for this cross-review. No source-note, audit or manifest change is
required.

Two wording constraints remain important for downstream use but are already present in the audit:

1. call the under-four-second laptop value a **reported local processing time**, not a fully
   benchmarked end-to-end calibration latency;
2. call the about-two-second hardware acquisition value and all distance-61/63 values
   **projections**, not demonstrations.

## Fixed-object verification

- Independently downloaded official source:
  `https://arxiv.org/pdf/2502.21044v2`.
- Official record: arXiv:2502.21044v2, revised 1 April 2025; the record lists v1 and v2 and no
  journal reference or separate Supplementary Information.
- Official and local PDF match: 10 pages, 483,968 bytes, SHA-256
  `9477f3e1a195c59e92681ce7e026dc859323790fbeb62b66de63169915af3b46`.
- Audit reviewed:
  `docs/simulator_validation/literature_expansion_round3/HOCKINGS_NOISE_AWARE_DECODING_2502_21044_AUDIT_2026-08-05.md`,
  SHA-256 `cbad77c756b43dfa0635c7dc8cbb591c1bdabb1e73c61605f4e98d2509de1b6f`.
- Draft note reviewed:
  `docs/simulator_validation/literature_expansion_round3/drafts/hockings_noise_aware_decoding_2502.21044v2_source_review.md`,
  SHA-256 `b21682402d0e0ee473ff92d2273d676a3a2355d772d4a5a80dd182e7391a0703`.
- The draft note passes `parse_note(..., verify_artifact=True)` with 24 evidence records and six
  relations; its source and audit hashes validate.
- Independent full-text reading covered all ten pages. Equations (1)--(2), Fig. 2, Table I,
  the distance-25 and distance-61/63 paragraphs, the timing paragraph and Appendix-A
  Eqs. (A1)--(A5) were visually checked against rendered pages 1--5 and 9--10.

## Independent scientific reconstruction

The source's noise object is a circuit-level Pauli channel attached to each gate in the specific
context of its syndrome-extraction layer. A synthetic instance draws gate Pauli probabilities
independently from a log-normal distribution, after which those probabilities are treated as the
fixed model for that instance. Layer/schedule context and multiqubit Pauli correlations do not add
a cross-round state or history law. No carrier lifetime, latent transition, stale-state variable,
round-indexed parameter or history-conditioned decoder prior is defined.

ACES measures Pauli observables on rearrangements of the circuit, decomposes circuit eigenvalues
into products of gate eigenvalues, solves the full-rank logarithmic linear system in Eq. (2), and
converts gate eigenvalues to Pauli probabilities through the inverse Walsh--Hadamard relation. A
stabiliser calculation then maps those circuit-level probabilities to priors over detector-flip
mechanisms for the same correlated-MWPM decoder.

The comparison therefore changes **static prior calibration**:

- the true simulated Pauli prior;
- finite-shot ACES estimates from `10^6` or `10^7` simulated calibration shots;
- tuned depolarising priors that retain correct operation-class average rates but remove gate-level
  heterogeneity.

It does not change access to a memory-bearing state or a longer record. “Memory experiment” is the
standard X/Z logical-storage task label. Device drift appears only in the proposal to combine ACES
with separately cited online updating methods in future work.

## Point-by-point cross-check

| issue | independent source finding | audit/note treatment | result |
|---|---|---|---|
| Static heterogeneous Pauli calibration versus temporal memory | Eqs. (1)--(2) and the numerical model define fixed gate/layer-context Pauli probabilities for each sampled instance. No temporal state or transition law is present; drift handling is prospective on p. 5. | Both documents explicitly classify the source as static noise-aware calibration and keep it outside temporal-memory evidence. | **pass** |
| Population design | At distances 3, 5, 7, 9, 11 and 13, logical decay is estimated over rounds `{3,5,9,17,33}` and `10^5` shots, with 1,500, 300, 100, 80, 60 and 50 log-normal instances, respectively, averaged over X and Z memories. The same correlated-MWPM decoder type is supplied four different priors. | Counts, distances, round set, priors and common decoder type are reproduced correctly. | **pass** |
| Population uncertainty and matching | Fig. 2 identifies its error bars as one standard deviation. The common `±0.0025` on the four suppression-factor fits is not assigned a confidence-level meaning. Per-record reuse is not explicitly stated for every population point. | The audit preserves all three qualifications and does not call the fitted `±` values confidence intervals. | **pass** |
| Distance-25 paired comparison | Table I applies all four priors to the same `10^7` shots, evenly divided between X and Z memories, for one fixed-seed log-normal instance. Its diagonal and off-diagonal counts are a genuinely shot-paired decoder comparison. | The note transcribes the four diagonal counts and the 3,005 versus 1,314 true/depolarising discordant counts correctly and limits the result to one instance. | **pass** |
| ACES calibration acquisition | The study numerically simulates ACES calibration for each declared setting; the design is informed by tuned-depolarising parameters optimised on a distance-3 circuit. Finite-shot ACES probes estimator precision within the assumed Pauli family, not a held-out mechanism. | Correctly reconstructed and not promoted to device calibration or wrong-memory-model robustness. | **pass** |
| Tuned-depolarising comparator | It retains accurate operation-class mean rates while discarding gate-level heterogeneity. It is a deliberately informed coarse static prior, not an uninformed decoder and not a changed temporal law. | Correctly qualified in both audit and note. | **pass** |
| Distance-25 logical rates | The four printed per-round rates come from one distance-25 instance and fits over the stated round set; agreement with the low-distance population trend is attributed to self-averaging by the authors. | Correctly reported as a single-instance check, not population validation at distance 25. | **pass** |
| Distance 61/63 | No distance-61 or distance-63 circuit is simulated. The paper extends the distance-3--13 population fit, using the single distance-25 agreement as motivation, to predict the four distance-63 rates and the distance-61 ACES-`10^6` rate/qubit comparison. | Audit and note explicitly label these values extrapolations and correctly report the 496-qubit comparison. | **pass** |
| About-two-second acquisition | The source combines gate, measurement and reset times from cited experiment [25] with its ACES design to estimate that `10^6` shots could be collected in about two seconds, conditional on an appropriate control stack. | Correctly labelled as an estimate based on another experiment, not a measurement in this study. | **pass** |
| Under-four-second processing | The authors report that laptop-based classical ACES processing for the simulated distance-25 circuit can be performed in under four seconds. No timing protocol, repetition count, variance or end-to-end integration is given. | Substantively correct. Downstream prose should prefer “reported under-four-second processing” over “benchmarked latency.” | **pass** |
| WLS reduction | Appendix A says generalised least squares becomes impractical at large scale; distance-25 ACES therefore uses weighted least squares and retains only the diagonal of the circuit log-eigenvalue covariance `Omega'`. | Correctly located, scoped to the large/distance-25 computation and marked as lacking a formal error bound. | **pass** |
| Gatewise simplex projection | A global Mahalanobis projection becomes intractable, so the probability estimate is projected separately for each gate with the corresponding diagonal block of the inverse probability covariance. The source calls the impact minor but gives no dedicated numerical ablation or quantitative bound in this letter. | Correctly reported and appropriately limited. | **pass** |
| Robustness | `10^6` versus `10^7` probes calibration-shot precision; tuned depolarising versus heterogeneous priors probes loss of static detail inside the Pauli representation. No stale calibration, non-Pauli residual, drift during acquisition, mixed carrier mechanism or wrong temporal law is tested. | Correctly classified as finite-data/static-prior diagnostics rather than wrong-memory-model robustness. | **pass** |
| Transfer | Each synthetic instance receives a corresponding calibration/prior; all codes are in the same XZZX surface-code family. No fixed prior is evaluated across an independent device, code family or operating regime. | Correctly rejects frozen-transfer promotion. | **pass** |

## Operation-replay check

| input | transformation | source-critical assumption | output | status |
|---|---|---|---|---|
| Pauli-frame-randomised Clifford circuit | Attach a gate/layer-context Pauli channel | Pauli-channel representation is adequate; no non-Pauli residual is evaluated | Static circuit-level Pauli model | complete and correctly bounded |
| Rearranged-circuit Pauli measurements | Estimate circuit eigenvalues, factor into gate eigenvalues and solve the log-linear system | Full-rank ACES design and estimable circuit eigenvalues | Gate-eigenvalue estimates | complete |
| Gate-eigenvalue estimates | Inverse Walsh--Hadamard conversion and covariance-aware simplex projection | Estimated covariance is adequate; identity coordinates are omitted consistently | Gate Pauli probabilities | complete within printed method |
| Gate Pauli model | Stabiliser conversion to detector-error priors | Circuit-level Pauli model captures the simulated mechanisms | Correlated-MWPM prior | complete |
| Same declared task under four priors | Decode and compare per-round logical failure | Population fits and same-instance pairings are interpreted only at their stated scope | Suppression factors, Fig. 2 and Table I | complete; population record pairing remains unstated outside Table I |
| Low-distance fitted trend | Extend to distances 61/63 | Scaling and asserted self-averaging persist far outside the population-fit range | Predicted logical rates/qubit saving | complete only as extrapolation |
| Distance-25 ACES estimation | Drop off-diagonal `Omega'` terms and perform per-gate projection | Source assertion that reductions suffice/minorly affect performance | Scalable approximate calibration | implemented, but no certified approximation error |

## Disposition

- `read_status`: complete
- cross-review result: **pass**
- audit semantic fidelity: pass
- source-note semantic fidelity: pass
- provenance/schema integrity: pass
- manifest action: none taken; admission decision remains with the parent reviewer

The strongest defensible use of this source is as an adjacent control showing a population-level,
partly shot-paired benefit from accurate **static** decoder-prior calibration. It cannot support a
claim of temporal-memory observation, memory-conditioned decoder benefit, wrong-memory-model
robustness, frozen transfer, hardware-demonstrated calibration, directly simulated distance-61/63
performance or certified large-scale ACES approximations.
