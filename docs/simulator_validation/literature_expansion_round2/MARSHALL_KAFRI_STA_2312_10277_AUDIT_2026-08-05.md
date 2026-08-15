# Claim audit — Marshall and Kafri on trajectory simulation and the STA

## Fixed source and reading scope

- Fixed artifact: `outputs/papers/coherent_leakage_longrange_closure/2312.10277v2.pdf`
- Identity: arXiv:2312.10277v2, *Incoherent Approximation of Leakage in Quantum Error
  Correction*, Jeffrey Marshall and Dvir Kafri, arXiv version dated 5 March 2025; published as
  *Physical Review Applied* 23, 054025 (2025), DOI `10.1103/PhysRevApplied.23.054025`.
- Artifact verification: PDF 1.5, 23 pages, 2,863,313 bytes, SHA-256
  `82ddaa228d8b13e0f55a5fb1c1d18e688698698ffd102823fb0f4e47d10a6ada`.
- Provenance: the repository provenance record fixes the arXiv v2 URL, retrieval date 2026-07-13,
  artifact hash and extraction method.
- Reading scope: all 23 pages, including main text, Appendices A–G and references. The legacy local
  reading note was used only to discover the candidate and not as evidence or prose.
- Visual verification: artifact pages 1–12 and 15–23 were rendered at original detail and checked
  for equations, circuit/model definitions, code-scale comparisons, uncertainty bars, sample counts,
  approximation discrepancies and cost. Pages 13–14 contain references and were text-read but were
  not used as load-bearing visual evidence.

## Assigned closure rows

| row | source location | source says | source does not say | status |
|---|---|---|---|---|
| C1 — concrete computation on persistent-memory repeated QEC | Secs. II–III, Figs. 2–5, PDF pp. 2–12; Appendices C–F, pp. 17–22 | Pure-state Kraus trajectories propagate qutrit leakage across rounds; full-qutrit and STA simulations return leakage, detection and MWPM logical quantities for repetition and surface-code memories. | It does not simulate a general non-Markovian environment. Exact full-qutrit surface-code comparison reaches distance 3; the distance-5 surface-code result uses STA only. | closed for the declared leakage models |
| M4 — exact/approximate representation comparison | Sec. II.D and Sec. III.B, pp. 5–11 | STA twirls channels between computational/leakage subspaces and replaces coherent superpositions by a classical subspace register; exact-versus-STA comparisons expose where this loses coherent structure. | Agreement under selected noise parameters is not a uniform error bound over channels, rounds or codes. | closed as a bounded approximation study |
| Q1 — model-conditioned QEC consequence | Figs. 2–5 and 15–18, pp. 9–12 and 20–22 | Leakage changes detector fractions and logical error; the leakage-conditioned CZ phase and coherent accumulation can change logical outcomes in the tested models. | The source does not estimate prevalence in hardware or establish a universal sign/scale for temporal memory. | closed within models |
| R1 — robustness to approximation/model choice | Figs. 2–4 and 10–18, pp. 9–11 and 19–22 | Thermal leakage is well reproduced by STA; strong coherent leakage produces systematic population and logical discrepancies; a fitted thermal approximation reduces average logical-curve error. | Parameter sweeps are not a certified worst-case bound and the decoder remains fixed/marginal. | partial but strong approximation-boundary evidence |
| T1 — transfer | Full source scope | The same framework is applied to repetition codes at several distances and surface codes at two distances. | Parameters and simulations are separately instantiated, with no fixed calibrated object deployed on a held-out device or code family. | missing |

## Operation replay

| input | transformation | assumption | output | exact source location | replay status |
|---|---|---|---|---|---|
| A composition of local noisy quantum channels | Sample one Kraus operator at each operation with Born probability and update a pure state | Initial state is pure; local Kraus operators have bounded support; sampling replaces complete density-matrix information | One trajectory containing all sampled Kraus indices and measurement outcomes | Sec. II.A, pp. 2–3 | complete |
| A QEC circuit with destructive measurement and creative reset | Build a dependency DAG and topologically reorder commuting operations | Added edges preserve the original partial order; the tested graphs remain acyclic | At most one measure qubit is retained, reducing surface-code memory from `2d^2-1` to `d^2+1` active qubits | Sec. II.B; Appendix B and Fig. 6, pp. 3–4 and 16–17 | complete |
| Hilbert space split into computational and leakage sectors | Apply the subspace twirl `E_STA = <U_-phi o E o U_phi>_phi` | Random relative phases are an acceptable approximation; result is strictly incoherent between sectors | An incoherent channel implemented with quantum state plus classical subspace registers | Sec. II.C–D, Eqs. (8)–(14), pp. 4–6; Appendix A, pp. 15–16 | complete |
| A data qutrit in computational/leakage superposition under repeated stabilizer measurement | Derive syndrome-conditioned Kraus products and Heisenberg evolution of cross-sector coherence observables | Measure-qubit leakage and other noise are omitted in this analytic step | Cross-sector coherence decays exponentially except at special leakage-conditioned phases | Sec. III.A, Eqs. (15)–(17) and Fig. 1, pp. 6–8 | complete |
| Distance-3 surface-code thermal-heating model | Run full-qutrit trajectories and STA trajectories for 50 rounds, at least one million samples, then fixed-MWPM decoding | Markovian Lindblad heating, relaxation and dephasing with stated timescales; leakage-free subtraction defines added LER | Added LER `0.275 +/- 0.012%` exact and `0.266 +/- 0.009%` STA, with similar leakage populations and detector fractions | Sec. III.B.1 prose, p. 9; Fig. 2, p. 10; Fig. 10, p. 20 | complete |
| Deliberately strong coherent CZ leakage | Compare full qutrit, naive STA and a thermal model fitted to exact leakage populations | Coherent transition probability `2.4e-3` exceeds the cited experimental value; no thermal heating is included in this stress case | Added LER `0.384 +/- 0.015%` exact, `0.404 +/- 0.014%` STA and `0.365 +/- 0.010%` fitted thermal STA; mean curve error 11.0% versus 2.9% for naive versus fitted approximation | Sec. III.B.2 and Figs. 3–4, pp. 9–11 | complete |
| Physically motivated mixed coherent/thermal leakage model | Simulate repetition-code memories at distances 3, 5, 7 and 9 with full-qutrit and STA trajectories | Stated `T1`, `T_phi`, leakage lifetime, heating and CZ-transition rates; at least 200,000 samples per point | Exact and STA logical-rate distance trends agree without visible system-size growth of approximation error; distance-9 detector-fraction increase is 1.18% versus 1.13% | Appendix F.1 prose, pp. 20–21; Figs. 15–16, p. 22 | complete |
| The same mixed model on distance-3 surface code | Compare no-leakage qubit, full-qutrit and STA trajectory results | Fixed marginal depolarizing DEM supplies MWPM weights; readout `2` is randomized to `0/1` | Fitted LER 0.0248, 0.0283 and 0.0284; at most roughly 4% intermediate-round relative difference between exact and STA curves | Appendix F.2 prose, p. 21; Figs. 17–18, p. 22 | complete |
| Distance-5 surface-code memory under STA | Use dynamic state size and STA with the physical parameters from Appendix F | No full-qutrit distance-5 comparator; 5,000 samples | Repeated-QEC logical curves through 25 rounds; 49 physical qutrit locations represented with at most 26 active qubits | Fig. 5 and Discussion, p. 11 | complete |
| Distance-5 STA simulation | Time one sample per round on one Intel Xeon Cascade Lake 2.7-GHz core | Reported implementation and hardware; cost remains exponential in active quantum degrees of freedom | Approximately 2.5 minutes per sample per round | Discussion, p. 11 | complete |
| Logical-error probability versus round count | Fit `F_L(k) = A(1-2 epsilon_L)^k` | `A` is ad hoc and leakage transients are not represented in the fit; long-time agreement is emphasized | A scalar fitted LER used in model comparisons | Appendix D, Eqs. (D1)–(D2) and Fig. 9, p. 19 | complete |

## Project application

This source makes Section 3 more concrete by separating four objects that should not be collapsed.

- **Scientific representation:** exact trajectories use a qutrit state whose leakage occupation can
  persist across rounds. STA replaces coherence between computational/leakage sectors by a classical
  sector register while retaining within-sector quantum amplitudes.
- **QEC-facing interface:** the simulation returns qutrit measurement outcomes, detection events and
  logical memory outcomes decoded by MWPM; a measurement result `2` is randomized before decoding.
- **Computation:** Kraus trajectories reduce density-matrix cost to pure-state sampling; dynamic
  creation/destruction of measure qubits reduces peak state-vector size; STA avoids qutrit expansion
  but remains exponential in the active quantum state.
- **Approximation evidence:** exact-versus-STA comparisons show close agreement for thermal and
  physically mixed models, and a clear failure mode for deliberately strong coherent leakage. A
  fitted thermal surrogate improves agreement but requires context-level leakage-population data.
- **Demonstrated reach:** exact comparison reaches distance-9 repetition codes and distance-3 surface
  code; distance-5 surface-code output uses STA only and has a measured high per-sample cost.
- **Evidential boundary:** a successful numerical approximation is not hardware attribution,
  memory-aware decoding benefit, transfer or a formal non-Markovianity result.

## Competing evidence and kill conditions

### Competing or adjacent evidence

- Manabe et al. use qutrit MPS and Kraus trajectories to reach much longer repetition-code chains and
  thin surface-code strips, with bond-dimension/truncation controls. The two approaches should be
  compared by geometry, approximation and returned output, not ranked by raw distance.
- Miao et al. provide hardware leakage-removal evidence. Their measured intervention constrains the
  relevance of leakage models but does not validate every STA channel assumption.
- Generic trajectory and tensor-network papers lack the repeated-QEC interface and should not be
  treated as peer rows merely because they share a numerical method.

### Kill conditions

- Kill any claim that STA is exact for coherent leakage; the strong coherent model shows systematic
  population and logical discrepancies.
- Kill any claim of a uniform approximation bound; the source supplies empirical comparisons and
  analytic coherence decay, not a worst-case error theorem over channels and time.
- Kill any claim that distance-5 surface-code leakage was checked against a full qutrit calculation;
  the distance-5 result uses STA only.
- Kill any claim that the method is polynomial-time or code-scale in general; the active state vector
  remains exponential and the reported distance-5 cost is about 2.5 minutes per sample per round.
- Kill any claim that the decoder exploits temporal leakage information; it uses a fixed marginal
  depolarizing detector model and randomizes a measured `2` outcome.
- Kill any hardware or transfer claim; all results are simulated under declared models.
- Kill any equation of persistent leakage with strict quantum non-Markovianity; the noise channels
  themselves are restricted to Markovian models.

## Source-local anomaly

The prose on PDF page 9 prints the exact strong-coherent added LER as `0.384 +/- 0.0015%`, whereas
the visually checked Fig. 3 caption and the later discussion give `0.384 +/- 0.015%`. This packet
uses the figure-caption value and treats the extra zero in the prose as a source typo. No conclusion
depends on the smaller uncertainty.

## Source-local verdict

- `read_status`: complete
- `evidence_status`: persisted
- C1 and M4: closed for the declared repeated-QEC leakage models and comparisons
- Q1: closed within model
- R1: partial, with explicit approximation success and failure cases
- T1: missing
- independent source-only review: passed on 2026-08-05
- downstream status: eligible for `source_only_reviewed`; manifest admission remains a separate action
