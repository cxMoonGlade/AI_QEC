# Claim audit — Manabe, Suzuki, and Darmawan on MPS simulation of repeated-QEC leakage

Date: 2026-08-05

Status: `SOURCE_ONLY_REVIEWED`

Independent admission reviewer: `/root`

Scope: the memory-bearing representation, QEC-facing interface, numerical strategy, demonstrated
repeated-QEC reach, approximation boundary, computational cost, and the extent to which the
simulated leakage-removal comparison can support the B2 intervention question

## Fixed source and reading scope

- Fixed artifact:
  `outputs/reading_packages/simulator_background_top10_2026-07-14/sources/2308.08186v2.pdf`
- Identity: arXiv:2308.08186v2, *Efficient Simulation of Leakage Errors in Quantum Error
  Correcting Codes Using Tensor Network Methods*, Hidetaka Manabe, Yasunari Suzuki, and Andrew S.
  Darmawan; visible arXiv stamp 21 January 2025.
- Artifact verification: PDF 1.5, 15 pages, 773,076 bytes, SHA-256
  `be54fe2ec199878855438bed58b4308172d02744cd8393f86765c151f25137fc`.
- Provenance: the repository provenance record pins arXiv v2, a 15-page PyMuPDF extraction, and a
  retrieval timestamp of 2026-07-15.
- Reading scope: all 15 pages, including Appendix A. All pages were rendered at 180 dpi and
  visually inspected. Equations (1)--(20), (A1)--(A9), Figs. 1--12, code layouts, reset circuits,
  axes, legends, captions, sampling qualifications, and stated scope limitations were checked
  against the rendered source. Text extraction was used for traversal only.
- Independence boundary: older local notes and package summaries for this paper were not used as
  evidence or prose. The admission reviewer independently checked the fixed artifact, all printed
  pages, equations, figures, captions, scope statements and numerical claims against this packet.

## Source question and bounded answer

The paper asks whether a matrix-product-state method can simulate non-Pauli qutrit leakage through
many rounds of quantum error correction at code sizes inaccessible to a full state vector, and
whether such a simulator changes conclusions drawn from simplified leakage channels or different
leakage-removal strategies.

Its bounded answer is positive for the studied one-dimensional repetition code and quasi-one-
dimensional `3 x d` thin surface code. The full data-plus-ancilla qutrit state is carried as a pure-
state MPS through gates and measurements; local dissipative channels and measurements are sampled;
MPO application and SVD truncation update the state. The resulting syndrome and final-data outcomes
are decoded to a logical-error probability. The study reaches distance 99 for the repetition code
with 99 rounds and distance 19 for the thin surface-code results.

This is not a microscopic retained-environment simulation. The thermal bath is eliminated into a
single-qutrit CPTP map applied at the start of each syndrome round. It is also not an
approximation-free calculation: it avoids the generalized twirling approximation in its main arm,
but retains MPS bond truncation and finite trajectory sampling.

## Assigned closure rows

| row | source location | source says | source does not say | status |
|---|---|---|---|---|
| Section 3 — memory-bearing representation | Secs. II--IV, PDF pp. 2--6; Appendix A, pp. 14--15 | Data and ancillary qutrits are represented jointly by a pure-state MPS and updated continuously through repeated syndrome rounds. Coherent leakage amplitude and leaked population present in that system state persist until measurement, relaxation, or a modeled reset/removal operation changes them. | The bath or another external environment is not retained as a dynamical carrier; Eq. (10) is reduced to a local CPTP map applied once per round. | `closed_for_system_qutrit_carrier`; `missing_for_retained_environment` |
| Section 3 — QEC-facing interface | Sec. IV.A, Figs. 2--3, PDF pp. 5--6; Eq. (8)--(9), p. 3 | The simulator exposes repeated syndrome outcomes and final data outcomes for a repetition code and thin surface code, then uses minimum-weight perfect matching and reports decoding-failure probability as logical error rate. | It does not return a detector-error model or a calibrated device-level likelihood model, and the source does not test alternative decoder access to the retained qutrit state. | `closed_for_explicit_circuit_record_and_logical_rate` |
| Section 3 — numerical strategy | Sec. III, Fig. 1, PDF pp. 3--5; Appendix A, Eqs. (A1)--(A9), pp. 14--15 | Gates are applied as local tensors or MPOs, canonical SVD updates truncate the MPS, and CPTP maps and projective measurements are simulated by sampling Kraus/measurement branches in pure-state runs. | It does not contract a process tensor or influence functional, propagate a density matrix, or provide a deterministic sum over all measurement and Kraus branches. | `closed_for_mps_plus_sampled_pure_state_branches` |
| Section 3 — demonstrated repeated-QEC reach | Sec. IV and Figs. 5--12, PDF pp. 5--11 | Demonstrated results include the repetition code through `d = 99` and 99 rounds (`2d-1 = 197` qutrits) and `3 x d` thin-surface-code logical results through `d = 19` (`6d-1 = 113` qutrits). | The source does not demonstrate a full `d x d` surface code, a width-5 or width-7 strip, or a higher-dimensional tensor-network ansatz; the width-5/7 remarks concern anticipated representability and cost, not executed QEC results. | `closed_for_1d_and_width_3_quasi_1d_only` |
| Section 3 — approximation and fidelity | Sec. V.A, Figs. 5--7, PDF pp. 7--8; Appendix A, p. 14 | Each SVD truncation keeps the 2-norm of discarded singular values below `10^-6` for repetition-code runs and `10^-4` for thin-surface-code runs; the source says these settings were confirmed sufficient for logical rates in the studied regions. | No global accumulated state-error bound, record-distribution bound, displayed threshold-convergence study, or independent exact reference is supplied for the largest runs. Finite branch sampling remains separate from bond truncation. | `closed_for_declared_local_truncation_control`; `missing_for_global_certificate` |
| Section 3 — computational cost | Sec. IV.A, PDF p. 6; Sec. V opening and closing paragraphs, pp. 7 and 10 | The runs use one Intel Xeon Platinum 9242 node with 96 threads; nonlocal MPO length and SVD dominate cost, and the source says SVD is a crucial bottleneck for the thin-code simulations at `d >= 5`. | No wall-clock time, peak memory, per-sample scaling fit, GPU result, or matched state-vector resource comparison is reported for the demonstrated workloads. | `partial` |
| B2 — carrier reset/control with logical comparator and cost | Sec. IV.B and Fig. 4, PDF p. 6; Figs. 8--12, pp. 8--11 | Under a common simulated code and leakage model, the study compares no reset, perfect ancilla multilevel reset, and DQLR, and reports logical-error curves showing that the removal choice can strongly change repeated-QEC performance. | The reset and LeakageISWAP operations have no reported physical duration, infidelity, calibration burden, or hardware resource measurement. The thin-surface-code comparison omits DQLR and leakage spreading because of simulation cost. | `partial_not_closed_under_cost_required_B2` |
| Section 5 — evidence level | Complete source scope, PDF pp. 1--15 | The source demonstrates a repeated-QEC effect and an intervention benefit inside declared numerical models and reports a failure of the generalized twirling approximation in one tested regime. | It does not observe temporal structure on hardware, identify a device's microscopic cause, or demonstrate transfer beyond the modeled codes, geometries, noise family, and decoder. | `simulation_evidence_only` |

## Operation replay

| input | transformation | assumption | output | exact source location | replay status |
|---|---|---|---|---|---|
| A superconducting-qubit surrogate with basis `|0>`, `|1>`, `|2>` | Apply the coherent single-qutrit rotations of Eqs. (1)--(5), the leakage-conditioned two-qutrit gate of Eqs. (6)--(7), and the four declared spreading rotations after CZ | The model is phenomenological, not fitted to one experiment; the Rabi processes are separated and the leaked-state CZ phase is fixed to `pi/2` | A circuit-level qutrit state with coherent control leakage, leakage-conditioned phase, and leakage spreading | Sec. II.A--B, Eqs. (1)--(7), PDF pp. 2--3 | complete |
| A qutrit presented for binary measurement | Apply the CP instrument `E_0` or `E_1`; leaked population is assigned to outcome 0 or 1 with probability `p = 1/2` | The readout does not discriminate the leaked state; measurement-induced leakage is neglected | A sampled binary outcome and an outcome-conditioned post-measurement qutrit state | Sec. II.C, Eqs. (8)--(9), PDF p. 3 | complete |
| The harmonic-oscillator thermal master equation at frequency 10 GHz | Truncate higher levels, integrate for `tau = 1 microsecond`, express the reduced dynamics as a Kraus CPTP map, and apply it to every qutrit at the beginning of each syndrome round | Each qubit is represented as a qutrit and the eliminated bath is represented only through the repeated local map | Round-local amplitude damping and thermal excitation acting on the system qutrits | Sec. II.D, Eq. (10), PDF p. 3 | complete |
| A pure-state MPS and a one- or two-qutrit operation | For a nonlocal two-qutrit gate, form an MPO across the intervening sites, move the MPS top tensor, contract the MPO sequentially, perform SVD, and discard small singular values | Accuracy is controlled locally by the declared discarded-singular-value threshold, and practical reach depends on low entanglement in the chosen one-dimensional ordering | An updated canonical MPS with dynamically selected bond dimension | Sec. III and Fig. 1, PDF pp. 4--5; Appendix A, Eqs. (A1)--(A8), p. 14 | complete |
| A single-qutrit CPTP map with Kraus operators `K_i` and current pure-state MPS `|psi>` | Sample branch `i` with `p_i = Tr(K_i |psi><psi| K_i^dagger)` and apply the selected `K_i` as a local update; simulate projective measurements analogously | Independent sampled runs estimate ensemble quantities; the source does not enumerate all branches | One pure-state trajectory through dissipative and measurement events | Appendix A, Eq. (A9), PDF pp. 14--15 | complete |
| An encoded repetition-code logical `|0>` or `|1>` product state with interleaved ancillas | Run the displayed noisy parity-check circuit for `d` rounds, measure data at the end, and decode syndrome plus data outcomes using minimum-weight perfect matching | Decoding failure is the logical-error event; the circuit uses `2d-1` qutrits | A sampled repeated-QEC record and logical-error-rate estimate | Sec. IV.A and Fig. 2, PDF pp. 5--6 | complete |
| A repetition- or thin-surface-code circuit under one leakage model | Choose no reset, perfect ancilla MLR, or DQLR; DQLR performs MLR, a data--ancilla LeakageISWAP printed as acting in the `|11>`--`|20>` subspace, and a second MLR | MLR is the perfect map to `|0>`; no physical duration or error model for the removal operations is reported; the following source sentence inconsistently names `|02>` rather than `|20>` as the state converted to `|11>` | Matched-model logical-error curves for alternative leakage-removal choices | Sec. IV.B, Eq. (12) and Fig. 4, PDF p. 6; Figs. 9--12, pp. 9--11 | complete, with source-local ordering inconsistency and physical-cost row missing |
| A coherent control-leakage channel `U` | Compute leakage and seepage rates, build the GTA channel in Eqs. (16)--(20), Pauli-twirl its computational-subspace action, and compare its decoded logical rate with the unapproximated coherent channel | Leakage spreading is set to zero in the displayed comparison; `d = 19`, `T = 10`, and `theta = 0.1 pi` | Fig. 8 logical-rate curves in which GTA overestimates the MLR result by more than a factor of three in the stated regime | Sec. V.B, Eqs. (13)--(20) and Fig. 8, PDF pp. 8--9 | complete |
| Repeated sampled runs across code distances and noise/removal parameters | Dynamically truncate each SVD, collect end-of-round bond dimensions, decode each sample, and average outcomes | Main prose states 10,000 samples per plotted point, while Fig. 11 separately says several thousand and suppresses points below `3 x 10^-4` | Bond-dimension diagnostics and Monte Carlo logical-error estimates with a source-local sample-count qualification | Sec. V opening and Sec. V.A, Figs. 5--7, PDF pp. 7--8; Fig. 11 caption, p. 10 | complete, with reporting ambiguity preserved |

## Project application

### Section 3 comparison row

This paper is admissible as a concrete computational approach only if the comparison keeps four
objects separate:

- **Representation:** the retained object is the full data-plus-ancilla qutrit system state in an
  MPS. Long-lived leakage is a state component; no external environment is retained.
- **QEC-facing interface:** explicit syndrome-extraction circuits generate binary measurement
  histories and terminal data outcomes, which MWPM converts to a logical-error indicator.
- **Numerical method:** MPO gate application, canonical SVD bond truncation, and sampled Kraus and
  measurement branches.
- **Demonstrated reach:** repetition code to distance/round count 99 and a width-3 thin surface code
  to distance 19, not a full two-dimensional surface-code family.

The row should therefore be named by the concrete implementation, for example “qutrit MPS with
sampled Kraus branches for repetition and thin-surface-code circuits,” rather than by the generic
labels “tensor networks,” “trajectories,” or “microscopic open-system simulation.”

### B2 intervention row

The source gives a strong simulated intervention comparison: the carrier is persistent qutrit
leakage; the interventions are no reset, ancilla-only MLR, and data-plus-ancilla DQLR; and the output
is a multiround logical-error probability over multiple distances. It therefore supplies the
intervention and downstream-QEC portions of B2.

It does not close the cost-required B2 row. MLR is a perfect reset map and DQLR is an added idealized
LeakageISWAP/reset sequence. The paper reports computational cost of simulating these arms, not the
physical duration, error, calibration burden, or hardware overhead of executing the interventions.

### Evidence-status boundary

The source supports a numerical claim about a declared model. It does not support an experimental
observation, microscopic attribution in a device, or transfer claim. Its comparison of exact
coherent leakage with GTA is evidence that matching leakage/seepage summaries need not preserve a
logical result in the tested setup; it is not a universal theorem about every effective model.

## Competing evidence and kill conditions

### Competing or adjacent evidence

- Miao et al., arXiv:2211.04728v1, implements MLR and DQLR on hardware and reports operation-level
  cost diagnostics. It is needed for physical intervention evidence; Manabe et al. is a numerical
  cross-check, not an independent hardware demonstration.
- Exact small-state trajectory calculations can test the MPS truncation and simplified-trajectory
  assumptions at smaller code size. Their smaller reach and different approximations must not be
  collapsed into the same approach row.
- A generic tensor-network, influence-functional, or open-system methods paper that never computes a
  repeated-QEC record or logical output does not duplicate this paper's demonstrated interface.

### Kill conditions

- Kill any claim that the paper performs a microscopic retained-bath or influence-functional
  simulation: the bath is reduced to a local per-round CPTP map.
- Kill any claim that the method is approximation-free: it avoids GTA in the main arm but uses MPS
  truncation and finite branch sampling.
- Kill any claim of full two-dimensional surface-code reach: the executed surface-code geometry is
  `3 x d`, and the authors leave higher-dimensional ansatzes to future work.
- Kill any claim that DQLR has zero or measured physical overhead in this source: no duration,
  infidelity, or calibration cost for the modeled reset operations is reported.
- Kill any claim that a zero observed logical-failure count in Fig. 11 is a zero logical-error rate;
  the caption explicitly identifies a finite-sampling plotting floor.
- Kill any claim that the GTA discrepancy establishes a universal ordering: the more-than-threefold
  result is one declared `d = 19` parameter regime with leakage spreading disabled.
- Kill any claim that the bond-dimension observations are a rigorous global accuracy certificate;
  the source gives local truncation thresholds and empirical sufficiency statements.
- Kill any claim equating persistent leakage in this model with strict quantum non-Markovianity.

## Source-local anomaly

PDF page 6 first defines LeakageISWAP as acting in the `|11>`--`|20>` subspace, but the next
sentence says that it removes data leakage by converting `|02>` to `|11>`. The ket ordering is
therefore internally inconsistent in the prose. This review records the printed definitions and
does not infer which ordering was intended; no conclusion here depends on resolving it.

## Source-local verdict

- `read_status: complete`
- `evidence_status: persisted_source_only_reviewed`
- representation: `closed_for_system_qutrit_mps_carrier`
- QEC-facing interface: `closed_for_explicit_repeated_circuit_record_and_logical_rate`
- numerical strategy: `closed_for_mps_mpo_svd_plus_sampled_kraus_branches`
- demonstrated reach: `closed_for_repetition_d99_99_rounds_and_width3_thin_surface_d19`
- approximation: `closed_for_declared_local_truncation_and_gta_comparison`; global numerical
  certificate `missing`
- computational cost: `partial`; physical intervention cost `missing`
- B2: `partial_not_closed_under_cost_required_definition`
- evidence level: `model-based repeated-QEC demonstration`; hardware observation, device attribution,
  robustness, and transfer `missing`
- admission: `source_only_reviewed_by_/root`
