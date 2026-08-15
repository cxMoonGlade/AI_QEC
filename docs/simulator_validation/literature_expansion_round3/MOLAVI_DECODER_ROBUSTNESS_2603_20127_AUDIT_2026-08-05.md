# Claim audit — Molavi et al. on decoder robustness to physical-rate uncertainty

## Fixed source

- Source: Abtin Molavi, Feras Saad and Aws Albarghouthi, *Analyzing Decoders for Quantum
  Error Correction*, arXiv:2603.20127v1, 20 March 2026.
- Artifact:
  `outputs/overview/literature/coverage_validation/analyzing_decoders/2603.20127v1.pdf`
- Artifact SHA-256:
  `cf38579a83b0b21d2bb9f1bf2ee41249259e68c502589ffec446856eb5aebe90`
- Reading scope: all 29 pages, including formal definitions, algorithms, evaluation, related work,
  conclusions and proofs. Pages 1, 6, 7, 10–13, 15, 17, 18, 20, 21 and 24 were additionally
  rendered; the definitions, independent-event polynomial, Algorithms 1–2, Theorem 7.1, benchmark,
  robustness result and conclusion were visually checked.

## Load-bearing result

The paper gives a formal and computationally demonstrated notion of decoder robustness over
independently bounded **Bernoulli physical error rates**. It does not test robustness to a wrong
temporal-memory model.

| question | source-local result | boundary | status |
|---|---|---|---|
| **R1 — wrong memory model** | A fixed decoder function is evaluated against a symbolic QEC program whose individual Bernoulli channel probabilities vary within a hyperrectangle; worst-case LER is reduced to constrained optimization of an error polynomial (Defs. 3.2, 5.5; pp. 6, 11) | Every error statement remains independent. No carrier, hidden-state transition, temporal kernel, mixed mechanism, memory time or correlation topology is perturbed | **missing for R1; positive adjacent evidence for static rate-interval robustness** |
| **Population comparison** | PyMatching, BP+OSD and Relay-BP are compared on rotated surface-code memory circuits, and the worst-case/nominal gap changes their ordering for one tested instance (Sec. 8.2; Fig. 11; p. 21) | This is synthetic, small-instance formal evaluation, not a memory-aware intervention contrast or a hardware population | **adjacent only** |
| **Uncertainty guarantee** | Enumeration yields sound bounds; the sampling hybrid uses stated Chernoff confidence intervals (Secs. 5–7) | Tight robustness bounds converge only for relatively small programs | **supported within the declared independent-Pauli model** |
| **F1 framework** | The source has a circuit/DEM-facing symbolic error representation, a decoder interface, enumerative plus polynomial-optimization computation and demonstrated QEC reach | It is a method for evaluating a fixed model/decoder pair, not a memory-bearing physical approach bundle | **fits as a computational/evidence boundary; do not add as a Section 3 memory row** |

## Exact interpretation

- The QEC-program language contains probabilistic Pauli error operations parameterized by numerical
  probabilities (Sec. 4; Fig. 3, p. 7), and Sec. 5 treats their event indicators as independent
  Bernoulli variables whose error-bitstring probability factorizes (p. 11).
- The robustness set is a hyperrectangle over those probabilities. In the empirical test each
  parameter is allowed to vary by plus or minus 10% from its nominal value (Sec. 8.2, p. 20).
- The largest robustness circuit reported as meeting the source's finite-resource convergence
  criterion is distance 3 with three rounds and 286 error-channel variables (Sec. 8.2, p. 21).
- Among the configurations summarized in Fig. 11, the authors report largest
  nominal-to-worst-case gaps of 28.6% for Relay-BP, 21.6% for BP+OSD and 21.7% for PyMatching. The
  prose says “6 programs,” while the figure displays seven labelled `(d,r,p)` groups with incomplete
  decoder convergence in several groups; the percentages are retained without resolving that count.
  On the distance-3, three-round, `p=0.001` instance, accuracy and robustness give different
  rankings of Relay-BP and BP+OSD (Sec. 8.2, p. 21).
- The paper explicitly treats constraints beyond hyperrectangles and decoder construction with
  robustness guarantees as future work (Conclusion, p. 24).

## Operation replay

| input | transformation | assumption or resource | output | exact source location | replay status |
|---|---|---|---|---|---|
| Stim-like QEC circuit | Compile the circuit to a detector error model | DEM error events are independent Bernoulli variables with deterministic syndrome/observable effects | Event probabilities and event-to-detector/logical maps | Sec. 8, implementation paragraph, p. 17 | complete; no continuing carrier |
| Error bitstring and fixed decoder | Compute syndrome and observable, apply the decoder and classify success or failure | The decoder is a fixed function of syndrome bits | Decoder-failure set over error strings | Def. 3.1, p. 6; Sec. 5, p. 11 | complete |
| Independent channel variables | Sum failure minterms using the factorized Bernoulli probability | Distinct event indicators are independent | Error polynomial | Theorems 5.4–5.5, p. 11 | complete |
| Explored error strings | Accumulate success/failure mass and bound unseen strings conservatively | Finite enumeration may leave probability mass unexplored | Sound lower and upper polynomial bounds | Sec. 6; Algorithm 1, p. 13 | complete |
| Bound polynomial and hyperrectangle | Use multilinearity, derivative-sign pruning and exhaustive search of remaining vertices | Each finite-circuit rate variable varies independently within its interval | Exact extrema of the explored-set bound polynomial | Sec. 6.2; Algorithm 2 and Theorem 6.7, p. 15 | complete within the declared box model |
| Unexplored mass for Accuracy | Apply conditional rejection sampling and Chernoff inversion | I.i.d. conditional samples | Probabilistic confidence interval | Sec. 7; Theorem 7.1, p. 17 | complete for Accuracy only; robustness bounds are not converted to a wrong-memory test |
| Surface-code task, decoder and ±10% rate box | Run enumeration and optimization until a resource limit or the source's convergence criterion is reached | Synthetic `si1000` DEM is the target family | Fig. 11 robustness comparisons | Sec. 8.2, pp. 20–21 | complete for reported small instances; not exact numerical replay of an unpublished benchmark artifact |

## Non-promotions

- Do not call the tested interval an incorrect memory law. It changes independent channel rates,
  not temporal dependence.
- Do not call this drift tracking. The method computes a worst case over a static uncertainty set;
  no time series or online update is modeled.
- Do not infer hardware robustness. All evaluated tasks are synthetic `si1000` rotated-surface-code
  circuits.
- Do not infer large-code certification. The robustness algorithm converges only on the smaller
  tested circuits.
- Do not promote the source to the Section 3 matrix. It evaluates computations over a declared
  QEC abstraction but supplies no distinct memory-bearing representation.

## Coverage consequence

The previous wording “diagnostic evidence only” is now too coarse. Section 5 can distinguish:

1. formal worst-case robustness to bounded independent rate uncertainty, which has a positive
   small-instance example here;
2. empirical decoder performance under later calibration snapshots or lower scalar rates, addressed
   by Stein and Yan et al.; and
3. robustness to a wrong carrier/history law, mixed temporal mechanisms or stale memory
   calibration, which remains unestablished in the reviewed corpus.

This source therefore **narrows but does not close R1**.
