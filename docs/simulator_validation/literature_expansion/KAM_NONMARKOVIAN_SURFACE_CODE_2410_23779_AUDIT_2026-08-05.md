# Claim audit — Kam et al. on temporally correlated surface-code memory noise

## Assigned closure rows

| row | source location | source says | source does not say | status |
|---|---|---|---|---|
| M1 — concrete non-leakage latent/effective model | Sec. III.A, pp. 5–7; Appendix A, pp. 17–18 | Pairwise and multi-time streak events are defined at circuit locations, with polynomial or exponential duration/separation laws and an explicit matched-marginal construction. | The event process is not inferred from a device and is not derived from a microscopic bath. | closed for a concrete QEC-level effective model |
| C1 — computation on persistent-memory repeated QEC | Sec. III.B–C, pp. 7–8; Table I, p. 20 | Custom error-mask sampling drives Stim surface-code memory circuits for 2d rounds, distances through 15, with 10 million shots and MWPM decoding. | It does not demonstrate exact propagation, process-tensor contraction, or a target-scale numerical-error certificate. | closed for Monte Carlo/stabilizer simulation only |
| Q1 — non-leakage logical consequence | Figs. 3–6, pp. 5–11; Appendix B, pp. 18–19; Table I, p. 20 | At fixed one-location marginals, tested streaky Class 1/2 structures degrade logical-error scaling, whereas the tested pairwise structures and Class 0 streaks remain comparatively benign. | It does not establish a universal consequence of temporal correlation, a device-independent threshold, or asymptotic behavior beyond the simulated distances. | closed within the tested models |
| N1 — null/limitation | Sec. IV.C, pp. 10–11; Figs. 7–8, pp. 12–13 | Pairwise detector autocorrelation magnitude does not rank the logical severity of the tested temporal structures. | It does not prove that every two-time statistic is insufficient for every model or device. | closed within the tested comparison |
| B1 — decoder benefit | Sec. III.B, p. 7; Sec. V.B, p. 13 | Both correlated and matched-independent samples are decoded with the same marginalized-independent MWPM model; memory-aware decoding is discussed only as a possible mitigation. | No memory-aware decoder is implemented or benchmarked. | missing |
| O1/A1 — observation and attribution | Sec. V.A, pp. 12–13 | The paper relates its simulated streaks to a previously reported experimental event pattern. | This work performs no hardware observation and identifies no microscopic cause for its simulated event process. | missing |

## Operation replay

| input | transformation | assumption | output | exact source location | replay status |
|---|---|---|---|---|---|
| Rotated surface-code memory circuit with Class 0, 1, and 2 circuit locations | Define a detector as the parity of consecutive syndrome measurements and associate circuit errors with space-, time-, or spacetime-like detector edges | Clifford circuit and the paper's boundary conventions | Detector record and logical-memory outcome used by the decoder | Sec. II.A–B, Eqs. (1)–(2), pp. 2–3 | complete |
| Event probabilities indexed by qubit/location and two round endpoints | Sample event matrix O and map it through T into a per-location, per-time error mask M; pair events mark endpoints, streak events mark the interval | Events in the declared model are sampled independently; error-class-specific composition rules apply | Dynamic Pauli injections for Stim FlipSimulator | Sec. III.A–B, Eqs. (3)–(4), pp. 6–7 | complete |
| Correlated event model | Reparameterize channels as maximal mixing and multiply the probabilities that no covering event occurs | The maximal-mixing channel is idempotent; the paper's event family and uniform conditional Pauli distribution apply | One-location marginal error probability p(s,t) | Appendix A, Eqs. (A1)–(A10), pp. 17–18 | complete |
| Correlated samples and matched independent samples | Decode both with the same detector error model constructed from the marginalized independent model | MWPM/PyMatching is deliberately correlation-blind in this comparison | Logical error per round versus distance | Sec. III.B–C, pp. 7–8 | complete |
| Logical-error samples through d = 15 | Fit exponential or power-law curves and extrapolate the distance needed for 10^-12 logical error per round | The chosen fit form continues outside the simulated distance range | Teraquop-distance projections or “no realistic projection” | Sec. III.C–IV.B, pp. 7–11; Table I, p. 20 | complete with extrapolation caveat |
| Detector records from a 10-round, distance-5 memory experiment | Compute Pearson detector correlations and average over equal spatial coordinates | Pairwise correlation is the selected summary | Mean autocorrelation versus round separation | Sec. IV.C, Eq. (5), pp. 10–11; Figs. 7–8, pp. 12–13 | complete |

## Project application

For the technical overview, this source can instantiate a concrete Section 3 comparison row only if
the four layers remain separate:

- memory-bearing representation: sampled pair or interval events with prescribed decay;
- QEC-facing abstraction: Class 0/1/2 circuit locations, detector parities, and logical-memory failure;
- numerical method: custom Monte Carlo masks plus Clifford propagation and MWPM;
- demonstrated reach: rotated surface-code memory, 2d rounds, d <= 15, 10 million trials per reported experiment.

For Section 5 it closes a model-conditioned logical-consequence row, not an observation or attribution
row. The matched-marginal contrast permits the report to say that temporal joint structure, rather
than one-location error rates alone, changes logical performance in these simulations. It does not
permit the report to call the streak model a measured device mechanism, to generalize the fitted
scaling beyond its simulated regime, or to claim a benefit from memory-aware decoding.

## Competing evidence and kill conditions

- The same paper supplies a null contrast: tested pairwise structures and Class 0 streaks do not show
  the severe degradation seen for Class 1/2 streaks. Any synthesis saying “temporal correlation is
  detrimental” without structure and location qualifiers is invalidated by these controls.
- The pending Gravier et al. silicon-spin candidate reports a different logical response to a
  physically motivated temporally structured noise model. Until independently admitted, it is a
  competing lead rather than evidence in the current corpus.
- The causal explanation in Sec. V is topological interpretation of simulated patterns. A claim of
  microscopic attribution is killed by the absence of a fitted or independently measured bath model.
- A decoder-benefit claim is killed by Sec. III.B: the decoder is held fixed and correlation-blind.
- A true-threshold claim is killed by the paper's own “apparent threshold” caveat and finite-distance,
  fit-dependent analysis.

## Source-local verdict

- read_status: complete
- evidence_status: persisted
- assigned-row status: M1, C1, Q1, and N1 closed within the declared simulation; B1, O1, and A1 missing
