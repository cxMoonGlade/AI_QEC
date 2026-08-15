+++
schema = "error_coupling_simulator.literature.note.v1"
source_id = "arxiv:2511.09491"
source_version = "v1"
source_uri = "https://arxiv.org/abs/2511.09491v1"
source_artifact = "outputs/papers/2511.09491.pdf"
source_sha256 = "cb2a52cb135c08d92118a672b9574c94aa53051280bc7d53993aebf83d7d3191"
title = "Adaptive Estimation of Drifting Noise in Quantum Error Correction"
publication_status = "preprint"
read_status = "complete"
evidence_status = "persisted"
review_scope = "full_text"
operation_replay_status = "complete"
audit_packet = "docs/simulator_validation/literature_expansion/BHARDWAJ_ADAPTIVE_DRIFT_2511_09491_AUDIT_2026-08-05.md"
audit_packet_sha256 = "59d58780a0ce91b03dcbd7f359e8fdc74e2ebc979383bcb16ed78a8de6f5cae7"
admission_status = "source_only_reviewed"
admission_reviewer = "codex-independent-source-review-bhardwaj-2026-08-05"
admission_date = "2026-08-05"
visually_checked_pages = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18]

[[relations]]
predicate = "defines"
object_id = "detector-error-model-edge-probability"
object_type = "model"
object_label = "detector-error-model edge probability"
fact_id = "bhardwaj-dem-representation"

[[relations]]
predicate = "defines"
object_id = "sinusoidal-time-dependent-pauli-drift"
object_type = "model"
object_label = "sinusoidal time-dependent Pauli drift"
fact_id = "bhardwaj-drift-model"

[[relations]]
predicate = "limits"
object_id = "markovian-independent-event-scope"
object_type = "limitation"
object_label = "Markovian time-dependent noise"
fact_id = "bhardwaj-markovian-scope"

[[relations]]
predicate = "derives"
object_id = "sliding-window-temporal-average"
object_type = "observable"
object_label = "sliding-window temporal average"
fact_id = "bhardwaj-window-average"

[[relations]]
predicate = "derives"
object_id = "rectangular-window-frequency-response"
object_type = "observable"
object_label = "rectangular-window frequency response"
fact_id = "bhardwaj-frequency-response"

[[relations]]
predicate = "uses"
object_id = "relative-window-instantaneous-estimator"
object_type = "method"
object_label = "relative-window instantaneous estimator"
fact_id = "bhardwaj-relative-method"

[[relations]]
predicate = "supports"
object_id = "drift-adapted-logical-error-comparison"
object_type = "observable"
object_label = "drift-adapted logical-error comparison"
fact_id = "bhardwaj-repetition-benefit"

[[relations]]
predicate = "limits"
object_id = "high-frequency-circuit-edge-resolution"
object_type = "limitation"
object_label = "high-frequency structure"
fact_id = "bhardwaj-circuit-estimation-limit"
+++
# Full-text review — Bhardwaj et al., “Adaptive Estimation of Drifting Noise in Quantum Error Correction”

## Source identity [paper_fact]
Fact ID: bhardwaj-source-identity
Source locator: Title page, arXiv version line, and embedded PDF metadata
PDF page: 1
Claim: The source is Bhardwaj, Takou, Lin, and Brown’s preprint “Adaptive Estimation of Drifting Noise in Quantum Error Correction,” arXiv:2511.09491v1.

The arXiv footer records v1 on 12 November 2025, while the manuscript title page is dated 13
November 2025. The artifact contains 20 PDF pages, including two appendices and the complete
reference list; no journal publication is identified in the artifact.

## Selection scope [paper_fact]
Fact ID: bhardwaj-selection-scope
Source locator: Abstract and Sec. I
PDF page: 1
Claim: The source asks whether time-dependent Pauli error rates can be estimated from repeated-QEC syndrome histories and used to improve decoding under nonstationary drift.

It develops sliding-window, iterative sliding-window, and overlapping relative-window estimators.
The worked evidence consists of numerical memory experiments under prescribed phenomenological and
circuit-level Pauli noise.

## Detector-error-model representation [paper_fact]
Fact ID: bhardwaj-dem-representation
Source locator: Sec. II, first three paragraphs
PDF page: 2
Claim: A detector-error-model edge probability is the QEC-facing quantity estimated by the source from single-detector firing rates and two-detector coincidence rates.

The paper restricts its developed representation to a decoding graph: detectors are vertices,
independent error mechanisms are bulk or boundary edges, and an edge of probability `p` has weight
`w = ln((1-p)/p)`. It states that hypergraph error mechanisms would require higher-order detector
correlators and leaves that extension outside the demonstrated calculations.

## Time and window notation [paper_fact]
Fact ID: bhardwaj-window-indexing
Source locator: Sec. III.A, paragraph before Eq. (3)
PDF page: 3
Claim: The source indexes syndrome-extraction times by `t_n = n Delta t`, uses `N` for the total number of cycles, and estimates an endpoint value at `t_l` from a trailing window of `W` cycles.

The selected interval is `[t_l-W Delta t, t_l)`. The endpoint convention matters because the
rectangular window produces both attenuation and a phase shift in the later frequency-domain
analysis.

## Prescribed drift model [paper_fact]
Fact ID: bhardwaj-drift-model
Source locator: Sec. IV.A, Eqs. (12)–(13)
PDF page: 6
Claim: The phenomenological simulations use sinusoidal time-dependent Pauli drift by applying a depolarizing channel with prescribed probability `g(t) = g_0 + sum_(m in M) g_m sin(omega_m t)` at each syndrome-extraction cycle.

The amplitudes and frequencies are injected simulation parameters. A static channel is recovered
when all frequency components vanish. Later circuit-level simulations give distinct prescribed
parameters to data qubits, ancilla qubits, and CNOT groups.

## Markovian independent-event scope [paper_fact]
Fact ID: bhardwaj-markovian-scope
Source locator: Sec. III.A immediately after Eq. (3), and Appendix A immediately before Eqs. (A10)–(A12)
PDF page: 3
Claim: The derived sliding-window relation is restricted by the source to Markovian time-dependent noise with statistically independent error events across the sampled times.

Appendix A factorizes the probability of a window bitstring into a product of instantaneous
Bernoulli probabilities. No latent state, retained environment, history-conditioned transition, or
multi-time non-Markovian object appears in this derivation.

## Sliding-window temporal average [paper_fact]
Fact ID: bhardwaj-window-average
Source locator: Sec. III.A, Eq. (3), and Appendix A, Eq. (A13)
PDF page: 3
Claim: Under the stated independent-event assumption, the sliding-window temporal average satisfies `p_est_ij(t_l) = W^-1 sum_(k=0)^(W-1) p_ij(t_l-W Delta t+k Delta t)`.

The estimated value is therefore a trailing average of the prescribed instantaneous edge
probabilities, not an unfiltered instantaneous rate. Appendix A reconstructs this result from the
expected number of edge occurrences in all length-`W` Bernoulli bitstrings.

## Sliding-window statistical uncertainty [paper_fact]
Fact ID: bhardwaj-window-variance
Source locator: Sec. III.A, Eq. (4), and Appendix B, Eqs. (B7)–(B8)
PDF page: 3
Claim: The source gives the windowed estimator variance as `W^-2` times the sum of the independent Bernoulli variances `p_ij(t)(1-p_ij(t))` over the window.

The resulting standard deviation decreases with window length but depends on the instantaneous
probabilities. The numerical discussion uses this relation to explain why smaller windows and local
rate extrema show larger uncertainty.

## Rectangular-window frequency response [paper_fact]
Fact ID: bhardwaj-frequency-response
Source locator: Sec. III.A, Eqs. (5)–(7), and Fig. 2
PDF page: 4
Claim: The DFT of the sliding-window estimate equals the true probability spectrum multiplied by a normalized rectangular-window frequency response with a frequency-dependent phase.

As printed in Eq. (7), the magnitude factor is
`W^-1 |sin(pi m W/N)/sin(pi m/N)|` and the phase is `pi m(W-1)/N`. The paper interprets this as
low-pass attenuation plus time lag, rather than as recovery of every drift frequency.

## Printed cutoff-normalization ambiguity [paper_fact]
Fact ID: bhardwaj-frequency-rule-ambiguity
Source locator: Sec. III.A, Eqs. (7)–(9), and Sec. IV.E discussion of Fig. 9(a)
PDF page: 5
Claim: The printed cutoff equation in Eq. (8) omits the `W^-1` normalization present in Eq. (7), while Eq. (9) and the reported optimum behave as though a normalized response were intended.

Equation (8) prints only the sine ratio on its left-hand side. The subsequent text gives
`c(0.05) approximately 0.12`, and the simulation reports `W_opt = 1228 +/- 42`; the paper does not
reconcile these expressions. This record therefore preserves the printed ambiguity.

## Iterative sliding-window method [paper_fact]
Fact ID: bhardwaj-iterative-method
Source locator: Sec. III.B, Eq. (10)
PDF page: 6
Claim: The iterative method decreases the window size, uses a response threshold to assign a frequency cutoff, and solves discrete sine and cosine coefficients by least squares while retaining previously resolved components.

The paper starts from a window of order `N`, then moves to smaller windows to admit higher
frequencies. It reports that the iteration normally stops at windows of 500–1000 syndrome cycles
because smaller windows have excessive statistical uncertainty.

## Relative-window instantaneous estimator [paper_fact]
Fact ID: bhardwaj-relative-method
Source locator: Sec. III.C, Eq. (11)
PDF page: 6
Claim: The relative-window instantaneous estimator subtracts two overlapping trailing averages of widths `W` and `W+1` to isolate the new endpoint probability.

The stated identity is
`p_ij(t_l) = (W+1) p_est_ij,W+1(t_l+Delta t) - W p_est_ij,W(t_l)`. The method is a
single-pass algebraic reconstruction and does not resolve individual frequency components.

## Relative-window smoothing assumption [paper_fact]
Fact ID: bhardwaj-relative-smoothing
Source locator: Sec. IV.C, Eq. (14) and the following paragraph
PDF page: 9
Claim: The numerical relative-window procedure applies Savitzky–Golay polynomial smoothing before evaluating the amplified discrete difference between the two noisy window estimates.

The paper states that the sampled estimates have local statistical peaks and describes them as
non-differentiable before smoothing. The polynomial order, filter width, and sensitivity to those
choices are not reported in the main text.

## Demonstrated simulation reach [paper_fact]
Fact ID: bhardwaj-simulation-reach
Source locator: Sec. IV opening and Secs. IV.A–D
PDF page: 6
Claim: The demonstrated reach is limited to Stim simulations of distance-3 repetition-code and distance-3 rotated-surface-code memory experiments under prescribed phenomenological noise, plus a distance-3 repetition-code circuit-level example.

The circuit-level example assigns nonuniform single-frequency depolarizing rates to data qubits,
ancillas, and CNOT groups. The rotated-surface-code calculation measures only the X stabilizers and
decodes the X-DEM.

## Window-size trade-off [paper_fact]
Fact ID: bhardwaj-window-tradeoff
Source locator: Figs. 3–6 and accompanying text
PDF page: 7
Claim: In the tested sinusoidal drift simulations, larger windows reduce sampling spread but attenuate and phase-shift faster components, whereas smaller windows retain faster structure with greater statistical uncertainty.

For the single-frequency repetition-code example, the stated response factors are 0.964, 0.636,
and 0.156 for `W = 1500`, `5000`, and `12000`, respectively. Figure 5 shows that a fixed window can
fail to isolate the faster component cleanly in a two-frequency signal.

## Rapid-drift relative-window result [paper_fact]
Fact ID: bhardwaj-relative-fast-drift
Source locator: Fig. 7 and Sec. IV.C results
PDF page: 10
Claim: With overlapping windows of 2000 and 2001 cycles, the relative-window simulations track prescribed multi-frequency drift down to periods of 500 and 700 cycles, but their uncertainty grows at local extrema.

Each displayed estimate averages five independent estimation trials. The source describes agreement
at most time instances for the fastest case rather than exact recovery at every time.

## Circuit-level high-frequency limitation [paper_fact]
Fact ID: bhardwaj-circuit-estimation-limit
Source locator: Fig. 8, Table I, and Sec. IV.D final paragraph
PDF page: 12
Claim: In the circuit-level repetition-code example, propagated uncertainty is larger for boundary edges and the diagonal-edge estimate fails to reproduce all high-frequency structure in the prescribed ground-truth signal.

The source attributes the diagonal signal’s decaying multi-frequency envelope to independently
drifting qubit and gate parameters. The relative-window estimate follows the broad trend but retains
visible mismatch.

## Logical-error comparison metric [paper_fact]
Fact ID: bhardwaj-logical-metric
Source locator: Sec. IV.E, Eq. (15)
PDF page: 12
Claim: The source defines relative logical-error mismatch as `Delta = epsilon_L_est/epsilon_L_stim - 1` and compares estimated and ground-truth DEMs using the same detection events.

`epsilon_L_est` is the logical error rate per cycle obtained from the estimated DEM, while
`epsilon_L_stim` is obtained by decoding the ground-truth DEM. The paper does not identify the
decoder algorithm used to produce these logical-error values.

## Logical optimum for one drift frequency [paper_fact]
Fact ID: bhardwaj-logical-window-optimum
Source locator: Fig. 9(a) and Sec. IV.E first numerical example
PDF page: 13
Claim: For the tested distance-3 repetition code with one prescribed drift frequency, the relative logical-error mismatch has a numerical minimum at `W = 1250`, compared with the paper’s prediction `W_opt = 1228 +/- 42`.

This simulation uses 1000 syndrome cycles and 50,000 shots for the logical-error calculation. Large
windows incur damping and lag, while very small windows incur sampling error.

## Repetition-code drift-adapted logical comparison [paper_fact]
Fact ID: bhardwaj-repetition-benefit
Source locator: Fig. 10 and Sec. IV.E discussion
PDF page: 13
Claim: In the tested distance-3 repetition-code simulations, the drift-adapted logical-error comparison shows lower logical error for a syndrome-estimated time-dependent DEM than for a static DEM, with the estimated curve close to the ground-truth DEM curve.

The phenomenological calculation uses 100 cycles and 500,000 shots per physical-error setting. The
circuit-level calculation shows larger deviations between the estimated and ground-truth curves,
which the source associates with uncertain boundary and diagonal edge estimates. The plot reports
direction and uncertainty bars but no tabulated improvement ratio.

## Rotated-surface-code drift-adapted logical comparison [paper_fact]
Fact ID: bhardwaj-surface-benefit
Source locator: Table II, Fig. 11, and the final paragraphs of Sec. IV.E
PDF page: 15
Claim: In the tested distance-3 rotated-surface-code X-memory simulation, the estimated time-dependent X-DEM gives lower logical error than the static X-DEM and closely follows the ground-truth X-DEM across the plotted physical-error range.

The calculation uses 50 cycles and one million shots. Each data and ancilla qubit is assigned a
prescribed sinusoidal drift frequency, and no circuit-level surface-code example is reported.

## Printed second-moment ambiguity [paper_fact]
Fact ID: bhardwaj-appendix-variance-ambiguity
Source locator: Appendix B, Eqs. (B6)–(B8)
PDF page: 17
Claim: Equation (B6) prints the second-moment cross term with the same time index in both probability factors, whereas Eqs. (B7)–(B8) state the independent-Bernoulli variance with one contribution per time index.

The appendix does not introduce a second summation index or otherwise reconcile the displayed
second moment with the next line. This record does not silently replace the printed expression.

## Explicit future scope [paper_fact]
Fact ID: bhardwaj-explicit-future-scope
Source locator: Sec. V, final paragraph
PDF page: 14
Claim: Experimental validation, hypergraph detector-error models, and extension to non-Markovian noise are explicitly identified as future directions rather than demonstrated results.

The source also suggests applying backward-moving windows to early cycles and extending the method
to drift across consecutive experimental runs, but those variants are not evaluated in Sec. IV.

## Memory-bearing-model gap [literature_gap]
Fact ID: bhardwaj-gap-memory-bearing-model
Source locator: Sec. III.A after Eq. (3), Appendix A before Eq. (A10), and Sec. V final paragraph
PDF page: 3
Claim: This source does not define or simulate a history-bearing physical or latent memory state and does not establish a non-Markovian repeated-QEC model.
Gap scope: source_local

Its time dependence is an externally prescribed variation of statistically independent Pauli event
rates. Nonstationary drift is therefore the modeled temporal structure; physical memory is not.

## Experimental observation and attribution gap [literature_gap]
Fact ID: bhardwaj-gap-observation-attribution
Source locator: Sec. IV opening and Sec. V final paragraph
PDF page: 6
Claim: This source does not observe temporal drift in hardware data and does not identify a microscopic cause for the prescribed drift frequencies used in its QEC simulations.
Gap scope: source_local

Every displayed QEC record is generated by Stim from author-selected error-rate functions.
Experimental validation is stated as future work.

## Model-mismatch robustness gap [literature_gap]
Fact ID: bhardwaj-gap-model-mismatch
Source locator: Full-text simulation scope in Sec. IV and limitations in Sec. V
PDF page: 14
Claim: This source does not test the adaptive estimator under a misspecified Pauli family, correlated event model, incorrect detector graph, or perturbed calibration prior.
Gap scope: source_local

Its robustness statements concern variation of physical error rate, drift frequency, frequency count,
and window size inside the assumed synthetic families. The deliberately static comparator omits the
drift term but is not used to test robustness of the adaptive estimator to model misspecification.

## Transfer gap [literature_gap]
Fact ID: bhardwaj-gap-transfer
Source locator: Sec. IV opening, Sec. IV.E, and Sec. V final paragraph
PDF page: 6
Claim: This source does not demonstrate transfer of one calibrated estimator or decoder across devices, platforms, code distances, decoders, or independently generated operating regimes.
Gap scope: source_local

The repetition-code and surface-code cases are separately instantiated distance-3 simulations.
Breadth across those examples does not establish transfer of a fixed learned or calibrated object.

## Decoder and resource-reporting gap [literature_gap]
Fact ID: bhardwaj-gap-decoder-resources
Source locator: Sec. IV.E and Sec. VI
PDF page: 12
Claim: This source does not identify the decoder algorithm used for the logical-error figures and does not report runtime, memory, or latency measurements for the claimed low computational-resource requirement.
Gap scope: source_local

Stim is named as the circuit simulator. The paper specifies cycles and shots for the logical plots,
but it gives no decoder configuration or online wall-clock benchmark.
