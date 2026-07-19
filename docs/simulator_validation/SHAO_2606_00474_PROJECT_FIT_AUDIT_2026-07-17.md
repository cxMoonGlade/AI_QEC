# Project-fit audit — Shao et al. 2606.00474v1

Date: 2026-07-17
Source artifact: `outputs/papers/pepo_survey/2606.00474v1.pdf`
Source SHA-256: `d7722de0513b1aef061a66a43ea766492d4205674a522c72f880e0f497a237f8`
Question: what tensor-network simulability statements follow for noisy density-operator evolution,
and do the absolute/relative Hilbert–Schmidt, whole-trajectory, or higher-dimensional results certify
the project's stochastic trajectories or adaptive detector Record?

## Assigned closure rows

| row | source location | source says | source does not say | status |
|---|---|---|---|---|
| Absolute error definition | Appendix B, Eqs. (B2)–(B5), PDF p. 10 | Ordered operator-Schmidt truncation has exact discarded tail `e_chi = ||rho-rho_hat_chi||_2^2`; fixed absolute accuracy means this squared Hilbert–Schmidt error is at most `epsilon`. If purity `t<=epsilon`, the zero-rank operator already passes. | This is not trace distance, infidelity, relative probability error, or a physical-state guarantee. | closed with exact metric |
| Relative error definition | Appendix B, Eq. (B6), PDF p. 10 | Relative accuracy means `||rho-rho_hat_chi||_2^2 / ||rho||_2^2 <= delta`, the fraction of surviving Hilbert–Schmidt weight in the discarded tail. | It is a ratio of squared norms, not `||error||_2/||rho||_2`, trace distance, or Record TV. | closed with exact metric |
| Entropy-to-rank bridge | Theorems 4–5, Eqs. (B7) and (B13), PDF pp. 10–11 | Unnormalized OEE controls a sufficient rank for fixed absolute squared-HS error, while normalized OEE controls a sufficient rank for fixed relative squared-HS error. | These are upper bounds for an ordered Schmidt truncation across a bipartition, not a local-gate discarded-weight accumulation theorem. | closed |
| Depolarizing thresholds | Main Theorem 1; Appendix D, Theorem 10, PDF pp. 3, 27–28 | For fixed-strength independent single-qubit depolarizing noise after every unitary layer and pure input, unnormalized OEE becomes `O(log n)` after `O(1)` depth and normalized OEE after `O(log n)` depth, for arbitrary gates and any fixed bipartition. | The constants are not calibrated to a device; the statement does not cover correlated, leakage, time-varying, or joint multi-qubit noise. | closed under stated model |
| Relative-depth sharpness | Appendix D, Proposition 3, Eqs. (D56)–(D80), PDF pp. 29–30 | A Bell-pair construction with identity unitary layers keeps normalized OEE super-logarithmic through an initial logarithmic-depth window, proving the uniform relative-OEE crossover cannot be `o(log n)`. | This does not prove every circuit requires logarithmic depth or give a lower bound for a particular project circuit. | closed |
| Whole-trajectory statement | Main Proposition 1; Appendix D, Proposition 4, Eqs. (D81)–(D122), PDF pp. 3, 31–34 | For a one-dimensional bounded-range local circuit, product input, fixed depolarizing strength, one prescribed cut, and fixed relative tolerance, a sequential approximation exists at every depth with polynomial bond dimension across that cut and relative squared-HS error bounded by `epsilon`. | The formal quantifiers do not explicitly construct one tensor train that satisfies all cuts simultaneously, preserve positivity, or expose an a posteriori certificate for an implemented truncation. | closed at prescribed-cut existence level |
| Whole-trajectory construction | Appendix D, Eqs. (D84)–(D122), PDF pp. 31–34 | The proof evolves exactly for `O(log n)` layers, then alternates `O(1)`-length noisy blocks with best-HS-rank truncation and a trace-one identity correction; contraction of trace-zero error closes an induction at all intermediate times. | The discussion states that a certifiably accumulated-error-controlled practical scheme is still missing. | closed as proof mechanism |
| Average-case general noise | Main Theorem 2; Appendix E, Theorem 11, PDF pp. 4, 38–39 | In 1D nearest-neighbor brickwall circuits with independently drawn unitary 2-design two-qubit gates and the same product single-qubit channel after each layer, `c(N)<1/3` yields an `O(1)` unnormalized-OEE plateau at every layer with high probability. | It is an ensemble result, not a worst-case guarantee for a fixed schedule or a relative-error theorem. | closed under ensemble assumptions |
| Worst-case general noise | Main Theorem 3; Appendix E, Theorem 13, PDF pp. 4, 43 | For arbitrary nearest-neighbor gate layers, a single-qubit channel with a unique fixed point and `c(N)<1/48` gives `O(log n)` unnormalized OEE at every depth for product input; arbitrary input obtains the bound only after an `O(log n)` crossover. | It provides fixed-absolute-HS rank control, not normalized relative-HS, trace-distance, or weak-noise guarantees. | closed under strong contraction |
| Higher-dimensional statement | Sec. V; Appendix F, PDF pp. 4, 44–48 | The results induce cutwise polynomial average boundary-bond dimensions for specified errors; the appendix explicitly defines this as a Schmidt-label capacity for a prescribed cut. | It does not construct local PEPO tensors realizing the truncation, satisfy all cuts simultaneously, or imply efficient PEPO contraction. | closed with explicit caveat |
| Adaptive measurement Record | Full-text model and theorem hypotheses, PDF pp. 1–48 | The trajectories are deterministic time sequences of unconditional density operators generated by unitary layers followed by fixed local channels. | No mid-circuit measurement instrument, feedback, branch-conditioned state, classical history register, detector XOR, logical bit, or full Record law appears. | missing |

## Notation ledger

| source symbol | source meaning | domain or scope | fixed/variable |
|---|---|---|---|
| `rho_l` | unconditional density operator after layer `l` and its following noise | noisy circuit trajectory | time-dependent |
| `S_OE` | entropy of unnormalized squared operator-Schmidt coefficients | one prescribed bipartition | state-dependent |
| `S_tilde_OE` | entropy after normalizing squared Schmidt coefficients by purity | one prescribed bipartition | state-dependent |
| `epsilon` | absolute squared-HS tolerance in Theorem 4; relative squared-HS tolerance in Proposition 4 | definition-dependent overload | fixed by task |
| `delta` | relative discarded fraction in Theorem 5 | ordered Schmidt truncation | fixed by task |
| `D_lambda` | single-qubit depolarizing channel `(1-lambda)rho + lambda I/2` | identical product noise after every layer | fixed `lambda` |
| `c(N)` | one-third of the squared displacement and damping parameters in canonical Pauli-transfer form | general single-qubit channel | channel-dependent |
| `chi_bar_partial(A)` | `R^(1/a(A))`, average boundary-bond dimension induced by a target cut rank | prescribed PEPO cut | cut/rank-dependent |

## Operation replay

| input | transformation | assumption | output | exact source location | replay status |
|---|---|---|---|---|---|
| ordered operator-Schmidt spectrum | keep largest `chi` coefficients | Hilbert–Schmidt-orthonormal Schmidt operators | exact squared-HS tail `e_chi` | Eqs. (B1)–(B3), PDF pp. 9–10 | reproduced |
| squared-HS tail and OEE | apply Theorem 4 or 5 | fixed absolute `epsilon` or relative `delta`; one bipartition | sufficient Schmidt rank | Eqs. (B7), (B13), PDF pp. 10–11 | reproduced |
| pure input and repeated product depolarizing layers | use product-channel hypercontractivity and unitary Schatten-norm invariance | identical fixed `lambda`; arbitrary intervening unitaries | purity bound `tr(rho_L^2)<=2^{-n tanh mu}` | Lemma 9, Eqs. (D3)–(D18), PDF pp. 24–25 | reproduced |
| purity bound | apply purity-controlled maximum-OEE bounds | fixed bipartition | separated absolute and relative OEE crossover scales | Theorem 10, Eqs. (D34)–(D55), PDF pp. 27–28 | reproduced |
| 1D local depolarizing trajectory | exact initial segment, block evolution, best-HS truncation, trace correction, and error contraction | product input; bounded gate range; one prescribed cut; fixed `lambda` | all-depth relative squared-HS existence bound | Proposition 4, Eqs. (D81)–(D122), PDF pp. 31–34 | reproduced at theorem level |
| general product single-qubit noise and 1D brickwall layers | replace the distant past by a fixed auxiliary orbit and bound its rank | 2-design ensemble with `c<1/3`, or arbitrary gates with unique fixed point and `c<1/48` | average constant or worst-case logarithmic unnormalized OEE | Theorems 11 and 13, PDF pp. 38–43 | reproduced under separate assumptions |
| one cut Schmidt-rank bound | divide log rank by boundary size | prescribed PEPO cut and target error | average boundary-bond dimension scale | Definition 2 and Propositions 5–7, PDF pp. 45–47 | reproduced as cutwise scale |
| density squared-HS error | reinterpret as adaptive Record total variation | no classical record register or measurement channel is included | no source-supported Record error | full-text boundary, PDF pp. 1–48 | blocked |
| prescribed-cut trajectory | infer one globally certified MPO or PEPO satisfying every cut | simultaneous cut construction is not supplied | no source-supported global certificate | Proposition 4; Appendix F caveat, PDF pp. 31–34, 44–45 | blocked |

## Project application

Shao et al. is theorem-grade evidence for the representability cost of a particular object: an
unconditional density operator propagated by unitary circuit layers and specified product single-qubit
noise. It is not a theorem about the project's restricted pure-state QT/MPS or MCWF/MPS execution laws.
In particular, the paper's word “trajectory” means the time-indexed density sequence `{rho_l}`; it does not
mean a sampled quantum-jump path or a branch carrying measurement outcomes.

The useful project mapping is limited to research diagnostics:

1. For a future density-MPO experiment matching the paper's depolarizing hypotheses, measure both normalized
   and unnormalized operator-Schmidt spectra and keep absolute and relative squared-HS targets separate.
2. Treat the general-noise contraction coefficient as an assumption check, not as a generic “noise helps” rule.
   The project's correlated terms, coherent joint generators, leakage levels, measurements, resets, and
   time-dependent schedules are outside the source model unless separately reduced and proved to preserve its
   hypotheses.
3. Use the exact-initial-window plus noise-contracted-block construction as a theoretical comparison surface.
   It does not replace the project's actual truncation ledger or independent dense/Record oracle.

The error metric is not the product metric. A squared Hilbert–Schmidt density error does not by itself give a
dimension-free trace-distance or complete Record-TV bound. The approximation after Schmidt truncation and trace
correction is not proved positive, and the formal whole-trajectory proposition fixes one cut before constructing the
sequence. These points block promotion to a globally valid MPS state carrier even before adaptive measurement is
introduced.

For higher dimensions, the source is unusually explicit: `chi_bar_partial(A)` is a cutwise average capacity derived
from Schmidt rank. It is not an implemented PEPO, does not produce tensors consistent across all cuts, and does not
imply efficient contraction. It therefore cannot certify the retained PEPO carrier or close its full-record gap.

An adaptive detector Record would require a new model containing the measurement instruments, feedback,
measurement/reset state updates, and a retained classical history register. A new bridge would then have to control
the law of that register in a metric relevant to the complete detector/observable Record. None of those steps is in
the paper.

## Competing evidence and kill conditions

- Werner et al. 1412.5746v2 supplies structural positivity and a trace-norm theorem for a finite
  one-dimensional locally purified density carrier; Shao's best-HS truncation plus trace correction is a
  different representation and certificate.
- Schieffer et al. 2501.15939v1 gives empirical CUDA-Q pure-state MPS performance and one top-four sampling
  check; it neither validates nor contradicts Shao's density-MPO existence bounds.
- Kill any claim using the absolute-error result without stating that the metric is squared Hilbert–Schmidt and
  that the zero operator passes once purity falls below the tolerance.
- Kill any claim using the relative-error result as trace distance, probability-relative error, or norm ratio
  rather than a squared-HS weight ratio.
- Kill the whole-trajectory claim if the circuit is not one-dimensional and bounded range, the input is not the
  stated product state, noise is not fixed product depolarization, or one demands one simultaneous all-cut
  construction.
- Kill the average general-noise claim without i.i.d. two-design gates and `c<1/3`; kill the worst-case claim
  without a unique fixed point and `c<1/48`.
- Kill any PEPO-efficiency or local-tensor-construction claim based only on average boundary-bond dimension.
- Kill any stochastic-trajectory, adaptive Record, or LER certificate unless the complete classical history is
  part of a new proved object.

## Source-local verdict

- read_status: complete
- evidence_status: persisted
- absolute/relative squared-HS rows: closed
- depolarizing OEE thresholds: closed under fixed product-noise assumptions
- whole-trajectory row: closed at all-depth, prescribed-cut density-MPO existence level
- general-noise rows: closed under their separate ensemble/strong-contraction assumptions
- higher-dimensional row: closed only as a cutwise average boundary-dimension scale
- adaptive measurement and detector Record row: missing
- project disposition: `density_MPO_cost_theorem_under_restricted_noise_not_Record_certificate`
- current gate effect: no upgrade to restricted MPS, PEPO, stochastic trajectory, or full-record acceptance
