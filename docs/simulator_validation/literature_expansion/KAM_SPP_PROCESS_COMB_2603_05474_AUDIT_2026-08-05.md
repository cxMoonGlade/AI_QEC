# Claim audit — Kam et al. on spatiotemporal Pauli processes

## Assigned closure rows

| row | source location | source says | source does not say | status |
|---|---|---|---|---|
| M1 — concrete latent/effective model | Secs. 6.1–6.2, pp. 29–31 | A two-state calm/storm hidden Markov process emits round-level Pauli faults and permits its temporal correlation length to vary while its single-round marginal is held fixed. | The model is prescribed, not fitted to a device or derived from a microscopic bath. | closed for a concrete QEC-level effective model |
| M2 — microscopic representation | Secs. 7.1–7.2, pp. 34–37; Appendix C, pp. 49–54 | A local system–bath quantum cellular automaton, under the declared system twirl and controlled-unitary assumptions, maps to a nonlinear probabilistic-cellular-automaton hidden Markov model with conditional Pauli emissions. | This is a constructed microscopic model, not an attribution of a measured device process. | closed within the stated model and twirling assumptions |
| M3 — multi-time operational representation | Secs. 2.4, 3–5, pp. 8–28; Theorem 4.3, pp. 16 and 48–49 | A process tensor carries intervention-conditioned multi-time dynamics; multi-time Pauli twirling yields a process-separable comb and joint distribution over Pauli trajectories, with tensor-network and conditional HMM forms under stated conditions. | Process separability is not temporal independence, and an HMM form of the same bond dimension is not guaranteed without a suitable nonnegative row-stochastic representation. | closed for the formal representation and its boundaries |
| C1 — computation on repeated QEC | Secs. 6.3–6.4, pp. 31–33; Sec. 7.4, pp. 39–40 | The paper samples SPP faults, composes them with 0.1% circuit-level noise in Stim, and decodes rotated-surface-code memory/stability circuits with marginalized, correlation-blind MWPM. | It does not contract a general two-dimensional process tensor at the demonstrated code scales or certify approximation error for such a contraction. | closed for sampled stabilizer simulation only |
| Q1 — logical consequence | Figs. 9–10, pp. 32–33; Fig. 12, pp. 39–40 | In the tested storm model, longer temporal correlation at fixed single-round marginals worsens logical performance; in the QCA-derived model, distance scaling reverses in the finite-size pseudo-critical window. | These are model-conditioned finite-size results, not a universal threshold theorem or hardware finding; the correlation-blind decoder also prevents the QEC results from isolating intrinsic code sensitivity from decoder mismatch. | closed within the tested simulations |
| N1 — limitations/null controls | Secs. 3.2, 4.1, 5.4, 6.4, 7.3–7.4, pp. 14, 17, 27–28, 32–33, 37–40 | The source states that two-dimensional networks are not generally both exact and efficient, that twirling is operational rather than a literal microscopic transformation, that the HMM equivalence has positivity/stochastic-gauge conditions, and that the decoder ignores correlations. | It does not demonstrate a general scalable physical-model-to-decoder pipeline. | closed as explicit boundary evidence |
| B1 — decoder or control benefit | Secs. 6.3 and 7.4, pp. 31 and 39–40; Sec. 8, pp. 40–46 | The demonstrated decoder uses a marginalised detector-error model; correlation-aware decoding and learning are future directions. | No memory-aware decoder, reset, or control is benchmarked against a matched baseline. | missing |
| O1/A1 — observation and attribution | Complete study design; Sec. 8, pp. 40–46 | The paper constructs and simulates formal and microscopic models and relates their patterns qualitatively to experimental literature. | It neither observes temporal structure in new hardware records nor fits the QCA or storm model to identify a microscopic cause in a device. | missing |
| R1/T1 — reset/schedule intervention and transfer | Complete study design | The benchmarks use fixed surface-code memory or stability schedules and one correlation-blind decoder family. | There is no matched reset or schedule intervention, and no demonstrated transfer across a device, code family, decoder family, or calibrated physical model. | missing |

## Operation replay

| input | transformation | assumption | output | exact source location | replay status |
|---|---|---|---|---|---|
| System–environment process with interventions at ordered times | Contract the process-tensor Choi object with the chosen interventions | The process satisfies the causal trace constraints | Conditional output state and joint multi-time statistics | Sec. 2.4, Eqs. (8)–(16), pp. 8–10 | complete |
| Finite-dimensional Stinespring process tensor | Re-index the system–environment unitaries as an MPO and, for composite systems, spatially factorise them by SVD | Temporal bond dimension is bounded by the environment Liouville dimension; spatial truncation controls the spatial bonds | One-dimensional temporal MPO or higher-dimensional spatiotemporal tensor network | Secs. 3.1–3.2, Eqs. (24)–(30), pp. 11–14 | complete with 2D contraction caveat |
| General process tensor | Apply an independent Pauli twirl to every input–output time pair | The declared Pauli-frame randomisation protocol defines the effective operational process | Process-separable Pauli comb and joint Pauli-trajectory distribution | Sec. 4.1, Eqs. (32)–(37), pp. 15–17; Appendix B, pp. 48–49 | complete |
| Twirled process tensor network | Contract fixed Pauli tensors into the physical legs while retaining the virtual environmental bonds | The supplied tensor-network representation is available | SPP MPS/PEPS tensors with temporal bond dimension no larger than the corresponding process bond | Sec. 4.2, Eqs. (38)–(48), pp. 17–20 | complete |
| Time-homogeneous one-dimensional SPP MPS | Form transfer and emission operators and inspect their spectrum; convert to an edge-emitting HMM when a nonnegative row-stochastic gauge exists | Stationarity/ergodicity and diagonalizability are invoked for the simplest exponential-correlation statements | Correlation functions, spectral correlation length, and conditional latent-state representation | Secs. 5.1–5.4, Eqs. (53)–(75), pp. 23–28 | complete with stated conditions |
| Two-state storm parameters and fixed target single-round marginal | Use the stationary distribution in Eq. (80) and solve Eqs. (79) and (81) for transition rates a and b so the correlation length changes while the stationary one-round marginal remains fixed | The solved rates satisfy 0 ≤ a,b ≤ 1 and a+b<1, and the model begins in stationarity | Sampled round-level Pauli trajectories with adjustable temporal correlation length | Sec. 6.2, Eqs. (76)–(81), pp. 29–31 | complete |
| Storm trajectories plus baseline circuit-level noise | Inject an SPP Pauli fault at the start of each round, propagate with Stim, and decode with a marginalised PyMatching detector model | Correlation-blind MWPM and the declared circuit/noise composition | Logical error per round for memory circuits and logical failure for stability circuits | Secs. 6.3–6.4, pp. 31–33; Figs. 9–10 | complete |
| Local QCA bath, stochastic injection/relaxation, and controlled system–bath interaction | Apply the operational system twirl; derive bath dephasing, bipartite PCA updates with flip probability sin²(kθ), and conditional Pauli emissions | The conditional system unitaries satisfy the Hilbert–Schmidt orthogonality condition and the bipartite update assumptions | Exact PCA hidden Markov representation of the twirled constructed model | Secs. 7.1–7.2, pp. 34–37; Appendix C, Eqs. (C3)–(C36), pp. 50–54 | complete |
| QCA-derived PCA trajectories | Estimate bath statistics after burn-in and inject sampled Pauli faults into repeated surface-code memory circuits | Finite lattices, single-exponential correlation-time fit, bath reset to all zeros for each QEC shot, and marginalised MWPM model | Finite-size bath diagnostics and logical error versus θ and distance | Secs. 7.3–7.4, pp. 37–40; Figs. 11–12 | complete with finite-size and decoder-mismatch caveats |

## Project application

This source is suitable for Section 3 only when four layers remain visibly separate:

- memory-bearing representation: a process tensor, its twirled SPP trajectory distribution, a
  two-state storm HMM, or the QCA bath/PCA latent process;
- QEC-facing abstraction: round-level Pauli strings, detector-error-model marginals, syndrome
  records, and logical memory or stability outcomes;
- computation: formal tensor contractions or spectral analysis for the representation, versus
  Monte Carlo sampling, Stim propagation, and MWPM for the demonstrated QEC benchmarks;
- demonstrated reach: finite rotated-surface-code memory/stability circuits, up to the stated
  distances and round counts, not a generic exact contraction of an arbitrary microscopic model.

For Section 5, the fixed-marginal storm comparison supports a model-conditioned statement that
joint temporal structure can change multicycle logical performance beyond what one-round marginals
predict. The QCA study supports a constructed mechanism-to-logical calculation under an operational
twirl. Neither result is a hardware observation, a device-level microscopic attribution, a
memory-aware intervention benefit, or a transfer demonstration.

## Competing evidence and kill conditions

- Process separability after twirling does not imply a Markov process; classical temporal
  correlations remain in the joint trajectory distribution.
- The operational twirl does not establish that the untwirled microscopic bath has physically
  become classical. A literal-mechanism interpretation is killed by the caveat in Sec. 4.1.
- A same-bond-dimension HMM interpretation requires a suitable nonnegative row-stochastic
  representation; Sec. 5.4 presents this as a sufficient construction, not a general minimal-realisation
  theorem.
- The 2D tensor-network representation does not itself establish efficient exact contraction at code
  scale; Sec. 3.2 explicitly states the general obstruction.
- The logical results use correlation-blind MWPM. Any decoder-benefit claim is killed by the absence
  of a matched correlation-aware decoder arm.
- The QCA transition is called pseudo-critical and is studied at finite lattice sizes. A thermodynamic
  critical-point or universal-threshold claim is not licensed.
- The paper is a 2026 preprint and contains no hardware calibration, new observation, or cross-platform
  replication. Device attribution and transfer therefore remain open.

## Source-local verdict

- read_status: complete
- evidence_status: persisted
- assigned-row status: M1, M2, M3, C1, Q1, and N1 closed within declared formal or simulation
  boundaries; B1, O1, A1, R1, and T1 missing
