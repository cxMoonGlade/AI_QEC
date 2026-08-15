# Section 3 approach comparison review — round 2

Date: 2026-08-05
Scope: read-only assessment of current admitted, source-only-reviewed, and pending round-2 notes;
`CURRENT_CORPUS.toml` is not changed here.

## Recommendation

Figure 2 should be a comparison matrix of concrete, source-instantiated approach bundles. A row is
eligible when one source-local implementation makes it possible to name all of the following without
filling gaps by analogy:

1. the representation in which temporal dependence persists;
2. the variables exposed to the QEC calculation or decoder;
3. the numerical or inferential method actually used;
4. the physical resolution retained and discarded;
5. the simulated or measured temporal horizon;
6. how parameters were prescribed, estimated, or calibrated; and
7. the repeated-QEC result actually demonstrated.

This criterion yields **six ready main rows** and **one visually separated boundary row**. The rows
are not mutually exclusive model families and are not stages of a common
pipeline. In particular, an MPS, a trajectory sampler, Monte Carlo, an HMM, a detector error model
and MWPM are not rows by themselves.

Recommended public title:

> **Comparison of concrete approaches to temporal dependence in repeated QEC**

Recommended caption boundary:

> Rows denote implemented source-local combinations of representation, QEC interface and
> computation, not a universal taxonomy or ranking. “Demonstrated reach” reports only the QEC
> outputs and scales actually calculated or measured; formal applicability and proposed extensions
> are not counted as demonstrations.

## Source readiness

| Candidate | Current local status | Figure decision |
|---|---|---|
| Kam et al., arXiv:2410.23779v4 | admitted current-schema note | main row |
| Kam et al., arXiv:2603.05474v2 | admitted current-schema note | main row for the QCA-to-PCA construction; the storm HMM is an adjacent example, not another full row |
| Manabe, Suzuki and Darmawan, arXiv:2308.08186v2 | independently source-only reviewed; manifest admission separate | main row |
| Marshall and Kafri, arXiv:2312.10277v2 | independently source-only reviewed; manifest admission separate | main row |
| Remm et al., arXiv:2502.17722v1 | independently source-only reviewed; manifest admission separate | main row |
| Nayak et al., arXiv:2603.18231v1 | independently source-only reviewed; manifest admission separate | main row, using the nominal code labels rather than the source's inconsistent surface-code qubit count |
| Kobayashi et al., arXiv:2412.13739v1 | admitted current-schema note | separated boundary row, because the implemented QEC example contains one syndrome-measurement round rather than repeated cycles |

Public artwork should not display these repository-status labels.

## Proposed Figure 2 matrix

### Main rows

| Concrete approach | Memory-bearing representation | QEC-facing variables | Computation actually used | Physical resolution | Temporal horizon | Parameter setting or calibration | Demonstrated repeated-QEC reach |
|---|---|---|---|---|---|---|---|
| **Circuit-location pair/streak Pauli event masks** — Kam et al., 2410.23779v4 | Sampled events join two rounds or cover an interval at a declared circuit location; power-law or exponential separation/length distributions carry the dependence. There is no inferred latent bath. | Class-0/1/2 circuit locations, dynamic Pauli masks, detector parities, a marginal detector error model and logical-memory outcome. | Custom event-mask Monte Carlo, Stim `FlipSimulator`, then the same correlation-blind PyMatching decoder for correlated and matched-independent arms. | Circuit-level Pauli errors with location and error-class resolution; no microscopic carrier, coherent dynamics or device fit. | Events occupy the tested `2d`-round memory block; the largest simulated case is `d=15`, hence 30 syndrome rounds. | Event rate and decay law are prescribed. One-location, time-resolved marginals are matched analytically between correlated and independent arms; parameters are not calibrated to hardware. | Rotated-surface-code memory through `d=15`, `2d` rounds and 10 million trials in the main series, with logical error per round and confidence intervals. |
| **Operationally twirled QCA bath mapped to a PCA/HMM Pauli process** — Kam et al., 2603.05474v2 | The microscopic construction has local system and bath qubits; under the declared system twirl, the continuing bath becomes an exactly mapped probabilistic-cellular-automaton hidden state with conditional Pauli emissions. | One round-level Pauli string, detector events, numerically marginalised detector-model weights and logical-memory outcome. | Analytic QCA-to-PCA mapping under the stated controlled-unitary/twirl assumptions; long classical bath sampling; Pauli injection into Stim; correlation-blind MWPM. The general 2D process tensor is not contracted at code scale. | A constructed local system–bath mechanism is retained before twirling; the demonstrated QEC calculation uses its classical PCA/HMM image. It is not a device-derived microscopic model. | Bath diagnostics use one million cycles, discard a 200,000-cycle burn-in and give a fitted correlation time of about 140 cycles for the plotted `d=9` case. QEC memories use `3d` rounds for `d=5`–17. Each shot starts the bath in the all-zero state. | Bath injection, relaxation and interaction angle are prescribed; single-round marginals are estimated numerically for the decoder. No hardware fitting or held-out calibration is performed. | Rotated-surface-code memory at `d=5`–17 for `3d` rounds, returning detector and logical curves. This is sampled PCA/HMM reach, not exact contraction of a generic quantum bath. |
| **Full-system qutrit MPS with sampled Kraus branches** — Manabe, Suzuki and Darmawan, 2308.08186v2 | The joint data-plus-ancilla qutrit pure state is retained as an MPS across rounds. Leakage amplitude and occupation persist in the system state; the thermal bath itself is reduced to a local CPTP map and is not retained. | Binary syndrome history, terminal data outcomes and MWPM decoding-failure indicator; no detector-error model or decoder access to the hidden qutrit state. | Local tensor and nonlocal MPO gate updates, canonical SVD bond truncation, and sampled Kraus and projective-measurement branches. Local discarded-singular-value norms are bounded by `10^-6` for repetition and `10^-4` for thin-code runs. | Phenomenological transmon-qutrit circuit with coherent control leakage, leakage-conditioned phases/spreading and a reduced thermal channel; no explicit environment or device likelihood model. | Repetition-code calculations explicitly reach 99 rounds. A displayed `3 x 7` resource study uses seven rounds; thin-code logical curves extend through `d=19`. | Leakage angles, thermal parameters and idealised removal maps are prescribed rather than fitted to hardware. Main prose reports 10,000 samples per point, with a separate “several thousand” qualification for one figure. | Repetition code through `d=99`, 99 rounds and 197 qutrits; quasi-1D `3 x d` thin surface code through `d=19` and 113 qutrits. No full `d x d` surface-code result. |
| **Full-qutrit state-vector trajectories with a subspace-twirled surrogate** — Marshall and Kafri, 2312.10277v2 | The full arm carries a pure qutrit state across rounds; STA removes coherence between computational and leakage sectors and stores sector occupancy in a classical register while retaining within-sector quantum amplitudes. | Qutrit measurement outcomes, leakage population, detector-event fraction and MWPM logical-memory outcome. Outcome `2` is randomised to binary `0/1`; the decoder receives no leakage trajectory. | Pure-state Kraus trajectories, dynamic destruction/creation of measured/reset qubits and circuit reordering; full-qutrit versus STA comparisons. The active state remains exponential even after reordering. | Markovian qutrit channel models for heating, relaxation, dephasing and coherent CZ leakage; no retained environment. STA is an approximation to these declared channels, not a claim that leakage is physically incoherent. | Distance-3 surface-code comparisons run for 50 rounds; a distance-9 repetition-code detector series reaches 100 rounds; the distance-5 STA-only surface-code example runs for 25 rounds. | Rates and transition probabilities are declared and partly experiment-motivated but not fitted to a device record. MWPM uses a fixed depolarising detector model with probability `0.001`. | The full-qutrit no-STA comparator reaches repetition distance 9 and surface-code distance 3. STA-only reach is a distance-5 rotated surface code with 49 locations, at most 26 active systems and 5,000 samples; no full-qutrit `d=5` comparator. |
| **Hardware-record syndrome-signature inversion and graph reweighting** — Remm et al., 2502.17722v1 | Temporal dependence is represented operationally by selected multi-cycle error-signature indicators and their inferred probabilities. This is a record-level generative abstraction, not a physical memory carrier. | Syndrome elements, space-time covariance, selected signature probabilities, MWPM edge weights and fitted logical error per cycle. | Closed-form moment inversion with recursive subtraction of strict supersets, a tractable selected signature catalogue, standard MWPM and one conditional cross-type reweighting iteration. | Experimental detector-record resolution. Distinct physical processes with the same signature are aggregated; leakage, drift and quasiparticle mechanisms are not uniquely identified. | Sixteen stabilizer cycles. The measured same-auxiliary covariance is plotted through separation 11; the selected long C-signatures span at most separation 8. | Default analysis retains about 54,000 runs per logical preparation after selection from 500,000 acquisitions. The same dataset supplies signature weights, interpolation choice and logical evaluation; there is no held-out calibration. | One 17-qubit distance-3 surface-code device, four logical preparations and 16 cycles. The correlated-MWPM difference is not statistically significant and does not establish benefit from long-history access. |
| **Latent quasiparticle-field estimation coupled to DEM/BP+OSD** — Nayak et al., 2603.18231v1 | A classical spatial QP-density field diffuses and decays by trapping across cycles; Pauli faults are conditionally independent given the field. | Field-conditioned Pauli rates and DEM mechanism priors, detector trajectory, inferred field, hard error estimate and logical-error probability. Evaluator-only true fields appear only in synthetic/oracle comparisons. | BP-20 plus OSD-10 alternated with full/sliding-window gradient estimation, or an EKF built from approximate QP pseudo-measurements. The EKF has a dense `O(n^3)` covariance term. | Chip-scale classical diffusion/trapping field mapped through declared `T1/T2` relations and Pauli twirling; no retained quantum coherence and no hardware-identified radiation event. | One-microsecond field discretisation, 921-ns QEC cycle and a 100-microsecond main endpoint. Online EKF uses two-cycle windows; the gradient sliding method uses 20-cycle windows. | Diffusion, trapping and process-noise parameters are tuned separately for each code on ten G4CMP events. Headline algorithm comparisons use one impact-selected event per code; no QEC hardware calibration or held-out transfer. | Synthetic source-labelled distance-7 rotated surface code and a `[[72,12,6]]` BB qLDPC code. Logical results for the proposed estimators are selected-event results without reported uncertainty. |

For the Nayak row, retain the nominal code labels rather than quoting a surface-code qubit total. The
independent review confirms that the source prints `n=97` “data qubits” plus `n_a=48` ancillas while
Fig. 3 contains 97 total markers, comprising 49 data and 48 measurement markers.

### Visually separated boundary row

| Concrete approach | Memory-bearing representation | QEC-facing variables | Computation actually used | Physical resolution | Temporal horizon | Parameter setting or calibration | Demonstrated repeated-QEC reach |
|---|---|---|---|---|---|---|---|
| **Finite-bath process tensor contracted with a stabilizer-QEC tester** — Kobayashi et al., 2412.13739v1 | A process tensor generated by sequential system–environment interactions retains one local bath qubit per data qubit until the end of the sequence. | Ordered ideal stabilizer outcomes, syndrome-conditioned logical Pauli recovery, recovered logical channel and source-defined decoder objectives. | Exact tensor-network contraction for small instances; MPS/MPO approximation of the combined process tensor and tester with bond caps and SVD truncation. | Explicit finite qubit baths plus declared crosstalk/depolarising terms, but ideal direct stabilizer projectors rather than a noisy ancilla/readout/reset circuit. | One syndrome-measurement round containing four sequential stabilizer measurements for the five-qubit code or six for Steane. These are not four or six repeated QEC cycles. | Synthetic couplings and error parameters; no device calibration. Quantitative reuse is additionally restricted by the printed non-trace-preserving Eq. (50) ambiguity. | Five-qubit and Steane-code single-round calculations only. Repeated syndrome-extraction cycles, surface-code reach and multicycle detector records are explicitly absent. |

The row should be shaded or separated by a rule and labelled **formal/small-instance boundary**. It
is useful because the absence of repeated-cycle reach is itself an important conclusion. It should
not be placed among the main rows without that visual separation.

## How Section 3 should use the matrix

- Treat the two qutrit rows as a controlled comparison: the memory-bearing physical representation
  is similar, but MPS truncation and geometry produce different reach from state-vector trajectories,
  circuit reordering and STA. This directly demonstrates why a scientific model and a numerical
  method cannot be collapsed.
- Contrast the circuit-event row with the QCA-to-PCA row: both return sampled Pauli trajectories to
  a stabilizer simulator, but only the latter begins from a constructed local bath, and even there
  code-scale prediction follows an operational twirl and classical mapping rather than direct 2D
  quantum-process contraction.
- Use the Remm row to mark the opposite inference direction: a QEC-facing signature model can be
  calibrated from Records without identifying a microscopic carrier.
- Use the Nayak row to show a continuing latent physical field coupled to online inference; retain
  its synthetic, selected-event, printed qubit-count inconsistency and per-code-tuning limits.
- Mention the Kobayashi construction in the multitime-description discussion, but use its boundary
  row to prevent formal process-tensor expressivity from being reported as demonstrated repeated-QEC
  scale.
- Keep detailed logical effects out of Section 3 except where needed to define demonstrated reach or
  an approximation boundary. Section 4 should explain consequences; Section 5 should judge evidence,
  calibration, benefit and transfer.

## Old rows to delete or downgrade

| Old or tempting row label | Action | Reason and replacement |
|---|---|---|
| `Phenomenological`, `microscopic`, `multi-time`, `QEC-level effective` | downgrade to prose grouping or a small side label | These are descriptive levels, not concrete approaches. Populate the matrix with the named implementations above. |
| `Exact propagation` | remove as a row; retain in the computation column | Exactness is relative to a declared model and finite task. The current corpus has no generic exact retained-environment repeated-QEC solver row. |
| `Stochastic trajectories` | remove as a row | Trajectories are a computation. Use the Manabe and Marshall rows, which state what is propagated, sampled, approximated and returned. |
| `Tensor networks` or `MPS` | remove as generic rows | Tensor networks are numerical representations/contractions with geometry- and bond-dependent meaning. Use the qutrit-MPS row and the separated process-tensor/tester boundary row. |
| `Influence-functional`, `TEMPO` or `PT-MPO` | delete from the Figure 2 matrix for now | The current source-only corpus does not demonstrate one of these routes returning a repeated-QEC Record or logical result. Generic open-system capability is not a peer row. |
| `Process tensor` | downgrade from a peer main row to the Kobayashi boundary row and Section 3 prose | Formal intervention slots are established, but the concrete QEC computation is single-round and small-code. Kam's code-scale QCA result uses the twirled PCA/HMM image rather than general process-tensor contraction. |
| `Monte Carlo and sampling` | remove as a row | It is a computation used by several scientifically different approaches and belongs in the computation column. |
| `HMM` or `latent-state model` | remove as generic rows | The storm state, a local leakage state and a diffusing QP field have different physical meaning, calibration and outputs. Name only the instantiated model used in a row. |
| `Circuit-level`, `syndrome-level`, `decoder model` or `DEM` | remove as model-family rows | These denote QEC-facing resolution or interface. Place them in the QEC-facing-variable and physical-resolution columns. |
| `Joint system–environment propagation` | downgrade to a scientific question, not a row | Use the QCA-to-PCA row for a constructed mechanism-to-effective mapping and the Kobayashi row for the current explicit finite-bath small-instance boundary. Do not imply code-scale direct bath propagation. |
| `Reduced dynamics` | retain only as connecting prose | No current concrete reduced-dynamics source closes all matrix fields with a repeated-QEC output. A local CPTP channel inside Manabe or Marshall is a component of those rows, not a separate approach. |
| Kam's two-state calm/storm HMM | keep as an in-text or caption example, not a second Kam main row | It is a strong fixed-marginal phenomenological example but overlaps the circuit-level effective-process role already occupied by the pair/streak row; giving both full rows would overweight one descriptive level and one source group. |
| Bultink or Varbanov leakage HMMs | retain as short examples of leakage inference; omit as full Figure 2 rows | They clarify that a posterior leakage label is a QEC-facing estimator rather than hidden truth. Bultink has no logical-qubit demonstration, while Varbanov is limited to Surface-17 and would create a third leakage-heavy row beside Manabe and Marshall. |
| Bhardwaj's drifting DEM estimator | use as a grey contrast note, not a memory-bearing row | Its error events are explicitly time-dependent, Markovian and statistically independent. It is useful precisely to show that history used for estimation does not make drift a memory state. |
| Miao DQLR, Kurilovich echo/recentering and Google below-threshold hardware | move to Sections 4–5 | Their principal role is mechanism, observation, intervention or evidence maturity, not a distinct Section 3 representation/computation approach. |
| Generic open-system, tensor-network or decoder method papers without repeated-QEC output | omit | Shared mathematics or software does not establish the QEC-facing variables, horizon, calibration or demonstrated reach required for a peer row. |

## Display constraints

- Use a matrix, not arrows or a carrier-to-decoder architecture.
- Keep **representation**, **QEC-facing variables** and **computation** in separate columns even when
  the source couples them tightly.
- Keep **physical resolution**, **temporal horizon** and **demonstrated reach** textual; checkmarks or
  a single high/medium/low score would erase important asymmetries.
- Use subtle row bands only to distinguish model-to-prediction rows from record-to-inference rows;
  the bands must not imply a maturity ladder.
- Put “not demonstrated” explicitly in the boundary row rather than leaving a blank cell.
- Do not show corpus state, audit terminology, source counts, hashes or local paths in the public
  artwork.
- Do not include logical-effect magnitudes merely to fill cells. Consequence and evidence claims
  belong in Sections 4 and 5 unless a number is required to define computational reach or an
  approximation comparison.

## Evidence basis

- Kam 2410: `docs/papers/reading_notes/kam_nonmarkovian_surface_code_2410.23779v4_source_review.md`;
  Secs. II.B and III, Appendix A, Figs. 3–8.
- Kam 2603: `docs/papers/reading_notes/kam_spatiotemporal_pauli_processes_2603.05474v2_source_review.md`;
  Secs. 3–7, especially Secs. 7.1–7.4 and Figs. 11–12.
- Manabe: `docs/papers/reading_notes/manabe_suzuki_darmawan_leakage_mps_2308.08186v2_source_review.md`;
  Secs. II–V, Appendix A and Figs. 2–12.
- Marshall and Kafri: `docs/papers/reading_notes/marshall_kafri_sta_2312.10277v2_source_review.md`;
  Secs. II–III, Appendices C–F and Figs. 2–5, 15–18.
- Remm: `docs/papers/reading_notes/remm_syndrome_correlations_2502.17722v1_source_review.md`;
  Secs. III–V, Appendices C, E, F and I.
- Nayak: `docs/papers/reading_notes/nayak_iterative_qp_decoder_2603.18231v1_source_review.md`;
  Secs. III–VI and Appendices D–F.
- Kobayashi boundary: `docs/papers/reading_notes/kobayashi_process_tensor_decoder_2412.13739v1_source_review.md`;
  Secs. 2.4, 3 and 4.
