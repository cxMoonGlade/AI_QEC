# Claim audit — Nayak et al. on latent-QP sensing and iterative decoding

## Fixed source and reading scope

- Fixed artifact: `outputs/overview/literature/final_expansion/sources/2603.18231.pdf`
- Identity: arXiv:2603.18231v1, *Iterative Decoding of Stabilizer Codes under
  Radiation-Induced Correlated Noise*, Anuj K. Nayak and coauthors, dated 18 March 2026.
- Artifact verification: PDF 1.7, 14 pages, 3,867,626 bytes, SHA-256
  `faf25f0c0c253199a5f45c4e5f511dcc2ec97ffad3761769780f1f118e264945`.
- Reading scope: all 14 artifact pages, including Appendices A–F and references. The candidate draft
  and existing audit were not used as evidence.
- Independent admission review rendered and visually traversed pages 1–14. Equations (1)–(2), the
  generative graph, both algorithms, Tables I–II and Figs. 1–14 were checked. Particular attention
  was given to event selection, decoder horizons, Fig. 6 values, absence of uncertainty, parameter
  reuse and inconsistent captions/counts.

## Assigned closure rows

| row | source location | source says | source does not say | status |
|---|---|---|---|---|
| C1 — concrete representation/interface/computation | Secs. III–V, PDF pp. 2–7 | A classical latent QP-density field drives time- and location-dependent Pauli priors; a DEM maps circuit faults to detector events; BP+OSD alternates with either gradient-based field inference or an EKF. | The model excludes other physical noise, Pauli-twirls QP-induced faults, omits recombination from the implemented field dynamics and is not validated on hardware. | closed for the declared model and simulated interface |
| B1 — memory-aware decoder benefit | Main Sec. VI.B and Fig. 6, pp. 7–8; Appendix F.1, pp. 12–13 | For separately selected synthetic events 58 and 53, the online EKF and fixed-uniform configurations share `T_w=2`, `t_s=1`, BP-20 and OSD-10, while the EKF arm obtains lower plotted PLE. | The events were selected from 64 by the largest full-horizon genie/uniform ratio at a 50-microsecond selection horizon; proposed algorithms are not averaged over all 64; Fig. 6 gives no shot count, confidence interval or PLE error bar. | closed only as a selected-event, model-matched synthetic contrast |
| R1 — model-mismatch robustness | Sec. III.B, p. 3; Sec. VII, p. 9 | A deliberately wrong fixed-uniform QP prior is compared with inferred and genie priors. | Mixed noise, an incorrect field law, an incorrect QP-to-Pauli map, calibration error and hardware distribution shift are not tested. | missing beyond one prior-mismatch axis |
| T1 — transfer | Sec. VI.A, p. 7; Appendix E, p. 12 | The procedures are instantiated on a nominal distance-7 rotated surface code and a `[[72,12,6]]` BB qLDPC code. | Parameters are tuned separately for each code, a different event is selected for each headline plot, and no frozen estimator is evaluated on a held-out code, device or mechanism. | missing |
| O1/A1 — experimental observation and attribution | Full source scope | G4CMP muon-event QP fields are used as simulation truth to generate circuit-level Pauli noise and syndrome records. | No hardware syndrome record, measured QP field or external-particle detector is analysed; radiation/QP attribution is an assumed generator, not an experimentally discriminated cause. | not applicable as experimental evidence |

## Operation replay

| input | transformation | assumption | output | exact source location | replay status |
|---|---|---|---|---|---|
| G4CMP muon-event QP trajectory | Sample a one-microsecond field at qubit locations and represent it with linear diffusion and trapping | The quadratic recombination term is neglected; sparse injection is absorbed into stochastic process fluctuations; the field is quasi-static within a 921-nanosecond QEC cycle | Latent field `X_t` and log field `Z_t` | Secs. II.A and III.A, PDF p. 2; Sec. VI.A, p. 7 | complete within declared approximation |
| Instantaneous local QP density | Apply the printed `T1(x)` and `T2(x)` relations and Pauli twirling | Radiation-induced faults are the only physical noise and are conditionally independent given the field | Time- and location-dependent `p_X=p_Y` and `p_Z` | Sec. III.B and Eq. (2), PDF p. 3 | complete |
| Circuit-level Pauli faults | Collapse faults with identical detector signatures into DEM error mechanisms and sum single-fault probabilities | Two or more simultaneous constituent faults are negligible; mechanisms touch no more than two adjacent cycles | Sparse DEM and field-conditioned mechanism priors | Sec. III.C, p. 3; Sec. V, p. 5; Appendix A, p. 10 | complete within printed approximation |
| Detector record and current field estimate | Run BP, feed its soft error-mechanism marginals into gradient updates, repeat, then apply OSD-10 | Bethe and mean-field posteriors plus degeneracy and algorithmic residuals replace exact inference | Offline or sliding-window QP estimate and detector-consistent hard error estimate | Secs. IV–V.A, pp. 4–6; Algorithm 1 | complete within printed approximation |
| Detector record and current field estimate | Reweight BP marginals into QP pseudo-measurements and apply a log-space EKF before BP+OSD output is committed | Single-fault allocation, log-normal dynamics, Gaussian pseudo-measurement noise and first-order dense covariance propagation | Online QP estimate and decoded error mechanisms | Sec. V.B, pp. 6–7; Appendix D, pp. 11–12 | complete within printed approximation |
| Ten G4CMP event trajectories per code | Tune `kappa`, trapping rate and process-noise variance with TPE against average maximum field MSE | Full-horizon Algorithm 1 is the representative tuning case and its code-specific parameters are reused by other algorithm variants | One Table-II parameter set for each code | Appendix E and Table II, p. 12 | complete; not a frozen cross-code calibration |
| All 64 muon events | Under full-horizon `T_w=T=50 microseconds`, compute uniform/genie PLE ratios and select the maximum | Selection targets events most sensitive to prior mismatch, not an unselected event distribution | Surface event 58, ratio 3.424; BB event 53, ratio 4.763 | Appendix F.1, p. 12; Figs. 7–8, p. 13 | complete; selection must accompany headline claims |
| All 64 muon events | Average genie and uniform PLE only | No all-event average is reported for Algorithm 1 or Algorithm 2 | Surface genie/uniform means 0.04202/0.05342 and BB means 0.02180/0.05815 | Appendix F.1, p. 12 | complete; comparator-only aggregate |
| Selected event 58 | At 100 microseconds compare genie and offline Algorithm 1 with sliding Algorithm 1, online EKF and two-cycle uniform decoding | Nominal surface-code model and code-specific tuning; PLE sampling count and uncertainty are unstated | Fig. 6 values 0.09, 0.12, 0.19, 0.23 and 0.28 | Main Sec. VI.B.2 and Fig. 6, pp. 7–8 | complete, selected-event only |
| Selected event 53 | Repeat the five-configuration comparison at 100 microseconds | BB-qLDPC model and separately tuned code parameters; PLE sampling count and uncertainty are unstated | Fig. 6 values 0.12, 0.18, 0.26, 0.52 and 0.76 | Main Sec. VI.B.2 and Fig. 6, pp. 7–8 | complete, selected-event only |
| Selected events under the narrowest printed contrast | Hold event, code, `T_w=2`, `t_s=1`, BP-20 and OSD-10 fixed; replace the uniform prior with BP-derived EKF field updates | Extra EKF inference is the intended intervention; compute and runtime are not equalized | Surface PLE 0.28 to 0.23 and BB PLE 0.76 to 0.52 | Main Sec. VI.A–B and Fig. 6, pp. 7–8 | complete; narrow matched-information contrast |
| Selected events under additional horizons | Add full-horizon uniform and three-cycle EKF configurations | Same event selection; the printed Fig. 13 caption says “using Alg. 1” although its legend includes genie, uniform and Algorithm 2 arms | At 100 microseconds, surface EKF-3 is 0.15 and BB EKF-3 is 0.28; full-horizon uniform is 0.24 and 0.46 | Appendix F.4 and Fig. 13, pp. 13–14 | complete, with caption qualification |

## Project application

This source supplies a concrete Section 3 approach and a highly qualified Section 5 decoder example.

- **Representation:** a classical, spatially distributed QP-density state governed by a Markov
  diffusion/trapping model. It is not a retained quantum environment or a strict quantum
  non-Markovianity model.
- **QEC interface:** the field determines local Pauli probabilities and DEM priors; detector history is
  the estimator input, while G4CMP density remains evaluator-only truth and a genie input.
- **Computation:** the common hard decoder is BP-20 plus OSD-10. Algorithm 1 alternates BP with
  gradient field updates; Algorithm 2 uses approximate pseudo-measurements and an EKF.
- **Demonstrated reach:** the reported QEC result is wholly simulated on two code layouts. The
  surface-code qubit count is internally inconsistent in the source, so the safe public scale labels
  are “nominal distance-7 rotated surface code” and `[[72,12,6]]` BB qLDPC.
- **Benefit:** the online-EKF versus uniform comparison is the narrowest printed contrast because the
  event, code, window, stride, BP count and OSD order are common. It remains selected-event evidence,
  with no PLE uncertainty and no equal-compute or measured-latency control.
- **Population statement:** only genie and uniform have 64-event means. Fig. 6 is not an all-event
  average and the selected events were chosen using a different 50-microsecond full-horizon ratio.
- **Calibration and transfer:** Appendix E says one parameter set is tuned separately for each code
  using full-horizon Algorithm 1 and reused across variants. This is not frozen cross-code transfer.

## Competing evidence and kill conditions

### Competing or adjacent evidence

- Kurilovich et al. provide hardware evidence for QP-associated phase bursts and a physical circuit
  intervention, but do not test this latent-field decoder.
- Miao et al. provide hardware carrier-removal evidence for leakage, not syndrome-only estimation of
  a QP field.
- Learned multiround decoders may use history, but their performance gains do not isolate access to
  the declared QP state unless the comparator and information boundary are matched.

### Kill conditions

- Kill any hardware or experimental-observation claim; all QEC records and QP fields are simulated.
- Kill unique microscopic attribution; the G4CMP/QP mechanism is assumed by the generator.
- Kill any claim that Fig. 6 averages 64 events; its surface and BB bars use selected events 58 and
  53, respectively.
- Kill any claim that the proposed algorithms have a 64-event average benefit; only genie and uniform
  are aggregated across 64 events.
- Kill any precision, confidence or significance claim; no PLE shot count, confidence interval, seed
  variation or Fig. 6 error bar is reported.
- Kill an equal-computation claim. Online EKF and uniform share the printed window, stride and
  BP+OSD backend, but only the former performs EKF state estimation.
- Kill an unqualified full-horizon comparison: event selection uses `T_w=T=50 microseconds`, Fig. 6
  reports 100 microseconds, and Figs. 11–12 extend genie/uniform curves to 150 microseconds.
- Kill a universal estimation-error-to-PLE relationship; the paper states no formal monotone result,
  and the three-cycle EKF can outperform the 20-cycle gradient window in PLE despite worse field MSE.
- Kill robustness beyond the assumed QP/Pauli model; mixed noise and model misspecification are open.
- Kill transfer: parameters are tuned per code and headline events differ.
- Kill strict quantum non-Markovianity: conditional on the classical Markov field, circuit faults are
  independent Pauli variables.

## Source-local anomalies

- Fig. 7's caption calls the Figure 3 layout a `[[72,12,6]] surface code`; the surrounding text and
  Fig. 3 identify event 58 with the distance-7 surface-code layout. Fig. 8 is the BB-qLDPC result.
- Fig. 13's caption ends “using Alg. 1,” while the legend and bars include genie, two uniform horizons,
  Algorithm 1 and two Algorithm 2 horizons.
- For the selected BB-qLDPC event, Fig. 6 reports `0.76` for the two-cycle uniform-prior arm,
  whereas Fig. 13 labels the apparently same `Uniform (T_w=2, t_s=1)` configuration at `0.73`.
  The source does not reconcile this numerical discrepancy.
- The main simulation text says hyperparameters are selected “per algorithm and code,” whereas
  Appendix E says full-horizon Algorithm 1 is tuned separately for each code and those parameters are
  reused across algorithm choices. The audit follows the detailed Appendix-E procedure.
- The source states that the distance-7 rotated surface code has `n=2d^2-1=97` data qubits plus 48
  ancillas, while Fig. 3 visually contains 97 total markers—49 white data markers and 48 check
  markers. The physical-qubit count is therefore internally inconsistent.
- The source uses several non-equivalent horizons/configurations: Fig. 1 illustrates a comparison at
  150 microseconds; Appendix F selects events under full-horizon `T=50 microseconds`; Fig. 6 reports
  the five principal bars at 100 microseconds; Figs. 11–12 extend genie/uniform trajectories to 150
  microseconds while showing proposed-algorithm comparison markers at 100 microseconds. These values
  must not be combined as one matched estimate.
- Appendix E says the 10 tuning samples “does not include both sample 53 and 58.” The intended reading
  appears to exclude the two headline events, but the grammar is ambiguous; the source does not name
  all ten tuning indices.

## Source-local verdict

- `read_status`: complete
- `evidence_status`: persisted
- C1: closed for the declared classical latent-QP/DEM/BP+OSD simulation chain
- B1: closed only for a selected-event, model-matched synthetic online-EKF versus uniform contrast
- R1: missing beyond a deliberately mismatched uniform prior
- T1: missing
- O1/A1: not experimental evidence
- admission review: passed by `/root/expand_observation_attribution` on 2026-08-05; final source-only
  note is written to `docs/papers/reading_notes/nayak_iterative_qp_decoder_2603.18231v1_source_review.md`;
  manifest admission remains a separate corpus-curation step
