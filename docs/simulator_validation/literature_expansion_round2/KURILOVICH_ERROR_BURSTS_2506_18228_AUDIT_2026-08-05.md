# Claim audit — Kurilovich et al. on correlated phase-error bursts in repeated QEC

## Fixed source and reading scope

- Fixed artifact: `outputs/papers/2506.18228.pdf`
- Identity: arXiv:2506.18228v1, *Correlated Error Bursts in a Gap-Engineered Superconducting
  Qubit Array*, Vladislav D. Kurilovich and coauthors, manuscript dated 24 June 2025. The work was
  subsequently published in *Physical Review X* 16, 021025 (2026), DOI
  `10.1103/1bl4-b2f7`.
- Artifact verification: PDF 1.7, 26 pages, 3,273,746 bytes, SHA-256
  `278f6adb6a48313d1ea21fb6f8775b106996ef373639b6c2e5078c8e9d10826c`.
- Reading scope: all 26 artifact pages, including the main text, Appendices A–H, references and the
  embedded five-page Supplementary Materials. The candidate draft and earlier notes were not used
  as evidence.
- Independent admission review rendered and visually traversed artifact pages 1–26. The title and
  source identity, circuit layouts, monitor/QEC spatial separation, burst traces and spatial maps,
  tomography and kinetic fits, matched-filter boundaries, injected-shift comparisons, excluded
  box-like events, trajectory model and supplementary examples were checked against the fixed PDF.

## Assigned closure rows

| row | source location | source says | source does not say | status |
|---|---|---|---|---|
| O1 — observation of multicycle temporal structure in repeated QEC | Main Sec. V.A and Fig. 5, PDF pp. 5–6; SI Figs. S3–S4, artifact pp. 25–26 | In an eight-hour interleaved experiment, cycle-resolved repetition-code detection bursts generally co-occur with slowly decaying Ramsey-error bursts recorded simultaneously on an adjacent monitor region. | The monitor and QEC qubits are disjoint, events are selected when either matched-filter trace peaks, and the source does not report a burst-conditioned logical-error time series or a formal non-Markovianity witness. | closed for a repeated-QEC detector record; not for a logical or formal-memory observable |
| A1 — physical attribution | Main Secs. III–IV and Figs. 2–4, PDF pp. 2–5; Appendices D–G, pp. 10–17 | Systematically negative MHz-scale shifts, Ramsey-versus-echo discrimination, reciprocal recovery consistent with QP recombination, and the excitation/relaxation energy-threshold hierarchy jointly support QP-associated, quasi-static frequency shifts near the junctions in the selected burst class. | QP density is inferred rather than measured directly, no synchronized external particle detector tags individual events, and the consistency chain does not uniquely identify the initiating particle species or prove that every detector burst has the same cause. | closed, qualified, for QP-associated frequency-shift attribution within the selected class; the external-radiation initiator remains untagged |
| Q1 — effect on repeated-QEC observables | Main Sec. V and Figs. 5–6, PDF pp. 5–7 | Natural Ramsey and repetition-code detection bursts align in time, while a controlled spatially uniform `-1 MHz` step for 15 cycles raises the original circuit's mean detection probability by 17 percentage points. | The injected step does not recreate the natural event's initiating carrier or spatial nonuniformity; detection probability is not logical error rate, and the source calls the link to an earlier repetition-code LER floor plausible. | closed for a detector-level repeated-QEC consequence; not for logical performance or full natural-event reproduction |
| B2 — control/intervention benefit | Main Sec. V.B–C and Fig. 6, PDF pp. 6–7; SI Fig. S3, artifact p. 25 | Recentring dynamical decoupling and adding an echo reduce excess detection under a controlled `-1 MHz` shift from 17 percentage points to 2; separately sampled natural bursts shown for the modified circuit have shorter detector tails that align more closely with residual T1 errors. | The intervention changes schedule and gate content, the natural events are not event-matched across circuits, the outputs are detector-level, and no cost-normalized logical benefit or transfer to another code is measured. | closed, qualified, for detector-level mitigation of controlled uniform-shift susceptibility; natural-event and logical benefit remain limited |
| R1 — robustness | Main Sec. V, Appendix B and Appendix H, PDF pp. 5–9 and 17–19 | The source sweeps injected-shift amplitude, states matched-filter miss and false-positive boundaries, excludes a distinct box-like event class, checks X- and Z-basis repetition-code variants, and compares injection curves with a small trajectory model. | It does not systematically vary natural-event spatial profiles, event-selection bias, calibration drift, background-model choice or higher-level transmon effects. | partial |
| T1 — transfer | Appendix H.2 and Fig. 13, PDF pp. 17–18 | Phase-associated detector bursts and echo suppression of injected-shift sensitivity are shown in X- and Z-basis repetition-code variants on the same Willow device. | There is no held-out processor, independent device, surface-code test or fixed-policy transfer, and the authors caution that the decoupling strategy may not apply directly to other codes. | missing beyond a same-device repetition-code basis variant |

## Operation replay

| input | transformation | assumption | output | exact source location | replay status |
|---|---|---|---|---|---|
| Sixty gap-engineered Willow transmons | Repeatedly execute Ramsey, spin-echo and T1 measurements, reset after each measurement and aggregate errors across the array | Ramsey/echo outcomes probe phase accumulation and T1 outcomes probe relaxation on the declared sequence timescales | A sudden spatially correlated burst with a roughly millisecond Ramsey tail and much shorter echo/T1 components | Main Sec. III and Fig. 2, PDF pp. 2–3 | complete |
| Repeated `T1 + R_X + R_Y` tomography | Average ten consecutive Ramsey-pair outcomes to estimate phase and convert it to `delta-f_q` | The shift varies slowly relative to the approximately 50-microsecond averaging window | Spatially nonuniform, systematically negative shifts in the MHz range with roughly millisecond recovery | Main Sec. IV.A and Fig. 3, PDF pp. 3–4 | complete |
| Measured frequency-shift recovery | Use `delta-f_q/f_q = -a x_qp` and fit the reciprocal curve derived from `dx_qp/dt = -r x_qp^2` | Cold QPs near the low-gap side dominate after the initial transient; the stated junction parameters set `a approximately 0.77` | Aggregate recombination rate `r = 1/(88 +/- 12 ns)` and a better fit than the displayed exponential comparator | Main Sec. IV.B, Eqs. (1)–(3) and Fig. 3c, PDF p. 4; SI Fig. S2, artifact p. 24 | complete |
| Faster T1 sampling and a ground-state dwell measurement | Ramsey-herald events, fit large relaxation bursts and compare excitation with relaxation traces | QPs above different energy thresholds drive excitation and relaxation before cooling by phonon emission | Median T1 burst size nine qubits, large-burst duration `35 +/- 15 microseconds`, and excitation bursts shorter than about five microseconds | Appendices D–F, PDF pp. 10–14 | complete |
| Adjacent, disjoint monitor and repetition-code regions | Synchronize one Ramsey and two T1 measurements with each 944-nanosecond X-basis repetition-code cycle; matched-filter Ramsey errors and measure-qubit detection changes | A spatially extended event can affect both regions, but the two records do not sample identical qubits | In eight hours, 105 selected events; Ramsey-error and QEC-detection matched-filter signals generally co-occur | Main Sec. V.A and Fig. 5, PDF pp. 5–6; Appendix H.1, p. 17 | complete, with spatial-separation boundary |
| Original X-basis repetition-code circuit | Apply a spatially uniform `-1 MHz` flux-induced frequency step to all code qubits for 15 cycles | The imposed shift tests circuit response to a shift of the observed scale but not the natural carrier or spatial field | Mean detection probability rises by 17 percentage points for approximately the injection duration | Main Sec. V.B and Fig. 6b–c, PDF p. 6 | complete, as a susceptibility intervention |
| Original, recentered-DD and recentered-DD-plus-echo circuits | Repeat the controlled uniform-shift sweep after schedule and gate changes | Recentring accounts for DQLR duration; echo between Hadamards cancels coherent phase accumulation through the CZ interval | At `-1 MHz`, excess detection falls from 17 points in circuit (i) to 2 points in circuit (iii); the conclusion reports about 35 versus 5 points at `-2 MHz` | Main Sec. V.B and Fig. 6a–c, PDF pp. 6–7 | complete, for detector response |
| Separately selected natural events under circuit (iii) | Repeat the simultaneous monitor/QEC experiment after the schedule change | Comparison is across separately sampled event populations, not the same impact replayed under two circuits | Displayed modified-circuit detector bursts no longer follow the millisecond Ramsey tail and align more closely with T1 | Main Sec. V.C and Fig. 6d, PDF p. 7; SI Fig. S3, artifact p. 25 | complete, with unmatched-natural-event boundary |
| Uniform-shift response curves | Sample quantum trajectories for 3- and 5-data-qubit circuit models with phase accumulation and detuned one-qubit gates | The model neglects higher transmon levels; a heuristic background bit-flip probability is chosen to reproduce the zero-shift detection count; the shift during two-qubit gates is adjusted for flux sensitivity | Curves agree with the three measured detector-response curves over the plotted shift range | Appendix H.3 and Fig. 14, PDF pp. 18–19 | complete, with baseline-calibration qualification |
| Initially matched-filtered QEC events | Identify near-unit, 50–250-microsecond box-like responses on two adjacent measure qubits and remove affected time sections | Near-unit detection differs from the coherent burst response; TLS interaction and data-qubit leakage are proposed, not established, alternatives | A distinct excluded temporal-anomaly class outside the QP-associated impact set | Appendix H.1 and Fig. 12, PDF p. 17 | complete |
| X-basis repetition-code result | Repeat interleaved monitoring and injected-shift echo comparison in a Z-basis repetition code | This changes the protected basis while retaining the same device and repetition-code family | Similar Ramsey-associated detection bursts and reduced injected-shift sensitivity with echo | Appendix H.2 and Fig. 13, PDF pp. 17–18 | complete as a same-device basis variant |

## Project application

This source is a strong but bounded mechanism-to-QEC case study. Its evidential layers must remain
separate.

- **Observation:** the repeated-QEC object is a cycle-resolved stabilizer-detection record. The
  simultaneous Ramsey/T1 monitors occupy an adjacent, disjoint region, so correlation across the two
  records is spatially informative but not a same-qubit measurement.
- **Attribution:** the negative sign, Ramsey/echo contrast, reciprocal recovery, QP-consistent rate and
  excitation/relaxation hierarchy support QP-associated quasi-static frequency shifts. They are
  convergent model-and-observation evidence, not a direct QP-density measurement or a synchronized
  tag of the initiating radiation particle.
- **QEC consequence:** natural-event co-occurrence and controlled injection support a detector-level
  consequence. The earlier LER-floor connection remains a cross-study plausible explanation rather
  than a logical-performance measurement in this source.
- **Intervention:** recentered dynamical decoupling and echo are physical schedule/control changes,
  not decoder changes. The strongest causal benefit is the reduction of detector response to a
  controlled spatially uniform shift; the natural-event comparison uses separately sampled bursts.
- **Computation:** the small trajectory model explains the injected-shift response under declared
  approximations. The source's “no free parameters” wording coexists with a heuristic background
  probability fixed to the measured zero-shift detector count, so it should not be recast as an
  uncalibrated prediction of natural bursts.
- **Transfer:** the Z-basis variant broadens the result only within one device and one code family.
- **Concept boundary:** a persistent physical condition and a multicycle detector record are not by
  themselves a process-tensor witness or another test of strict quantum non-Markovianity.

## Competing evidence and kill conditions

### Competing or adjacent evidence

- The earlier Willow below-threshold experiment reports rare repetition-code bursts but leaves their
  causes open. Kurilovich et al. provide a plausible QP-associated pathway for a class of such events;
  this does not prove that all earlier large bursts share it.
- Harrington et al. and Li et al. use external particle detectors in non-QEC monitoring. They sharpen
  standards for radiation attribution but cannot be fused with this repeated-QEC record as if it were
  one synchronized experiment.
- Miao et al. directly prepare and remove leakage. Kurilovich et al. instead exclude a 50–250-
  microsecond box-like class for which TLS interaction or leakage is only proposed; the classes must
  not be merged.

### Kill conditions

- Kill any claim that individual selected events were synchronously tagged by a cosmic-ray, gamma-ray
  or other external particle detector.
- Kill any claim that the paper directly measures QP density or uniquely proves the initiating
  radiation species; its QP attribution is a convergent consistency argument.
- Kill any claim that monitor and QEC traces come from the same qubits; the regions are adjacent and
  disjoint.
- Kill any claim that detector probability is logical error rate or that this source directly proves a
  logical-error benefit.
- Kill any claim that the uniform injected step reproduces the natural event's carrier or spatially
  nonuniform field.
- Kill any claim that the echo comparison is a decoder-aware intervention; it changes the physical
  circuit schedule and gate content.
- Kill any claim of surface-code or device-independent transfer; the source explicitly cautions that
  the decoupling strategy may not apply directly to other QEC codes.
- Kill any established attribution of the excluded box-like events to QPs, radiation, TLS or leakage;
  TLS interaction and leakage are proposed possibilities.
- Kill any unqualified statement that the response model is an uncalibrated natural-burst prediction;
  its scope is the uniform-shift response and its zero-shift background is matched heuristically.
- Kill any statement equating burst persistence with strict quantum non-Markovianity.

## Source-local verdict

- `read_status`: complete
- `evidence_status`: persisted
- O1: closed for cycle-resolved repeated-QEC detection bursts, with adjacent-region qualification
- A1: closed, qualified, for a QP-associated quasi-static-frequency-shift pathway in the selected
  burst class; direct external-radiation tagging is missing
- Q1: closed for detector-level consequence, not logical performance
- B2: closed, qualified, for detector-level mitigation under a controlled uniform shift; the natural
  comparison is not event-matched and no logical/cost-normalized benefit is shown
- R1: partial
- T1: missing beyond same-device repetition-code basis variants
- admission review: passed by `/root/expand_observation_attribution` on 2026-08-05; final source-only
  note is written to `docs/papers/reading_notes/kurilovich_error_bursts_2506.18228v1_source_review.md`;
  manifest admission remains a separate corpus-curation step
