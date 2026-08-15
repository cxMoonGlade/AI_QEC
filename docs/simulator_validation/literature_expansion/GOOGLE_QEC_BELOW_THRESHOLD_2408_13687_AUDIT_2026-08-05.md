# Claim audit — Google Quantum AI on rare error events in repeated QEC

## Fixed source and reading scope

- Fixed artifact: `outputs/papers/2408.13687.pdf`
- Identity: arXiv:2408.13687v1, *Quantum error correction below the surface code threshold*,
  Google Quantum AI and Collaborators; the arXiv record links the work to Nature 638, 920–926
  (2025), DOI `10.1038/s41586-024-08449-y`.
- Artifact verification: PDF 1.5, 27 pages, 3,825,803 bytes, SHA-256
  `9ba05a64dfec13f5d733e0e22484e8f22db2482dc2a5a0d63e6f0766c9c3d368`.
- Version check: a fresh retrieval of `https://arxiv.org/pdf/2408.13687v1` on 2026-08-05
  was byte-identical to the fixed local artifact.
- Reading scope: all 27 artifact pages, comprising the main paper and embedded Supplementary
  Information. The older local notes for this source were not used as evidence.
- Visual verification: artifact pages 1, 4–6, 18, 20, 21, 23, and 27 were rendered and checked at
  220 dpi for the load-bearing formulae, plots, captions, table entries, and numerical statements.

## Assigned closure rows

| row | source location | source says | source does not say | status |
|---|---|---|---|---|
| O1 — observed temporal or rare structure in repeated-QEC data | Main Sec. IV, PDF pp. 4–5; Fig. 3d, PDF p. 5; SI Sec. V.A and Fig. S7, PDF pp. 20–21 | In distance-29 repetition-code data, one event class raises one or two detector probabilities for tens or hundreds of cycles; a second class produces spatially grouped detector bursts with sharp onset and 400–700 microsecond decay over several shots; a single noisy detector can also remain elevated for 1–2 ms. Six large bursts occurred during 2 x 10^10 QEC cycles. | It does not identify a microscopic carrier, establish strict quantum non-Markovianity, or establish that the newly observed events are non-leakage. | closed for record-level cross-cycle/shot structure; the non-leakage mechanism qualifier is missing |
| Q1 — consequence for multicycle or logical QEC performance | Main Sec. IV and Fig. 3a,d, PDF pp. 4–5; SI Sec. V.A, PDF pp. 20–21 | The high-distance logical failures have distinct rare-event signatures: the correlated bursts account for all observed distance-27 errors and half of the distance-21 to distance-25 errors, and the six large bursts are responsible for the highest-distance failures; the paper reports an apparent high-distance logical-error-per-cycle floor near 10^-10. | It does not establish a causal non-leakage mechanism for the logical failures, a surface-code rare-event floor, or transfer beyond this repetition-code/device/decoder setting. | closed for event-associated repetition-code logical consequence; causal mechanism and transfer remain missing |
| A1 — device or microscopic attribution with alternatives or intervention | Main Sec. IV, PDF pp. 4–5; SI Sec. V.A, PDF pp. 20–21 | The less-damaging one- or two-detector events could arise from transient TLS motion or coupler excitation; the larger bursts differ from previously observed high-energy impact events in occurrence rate and decay time; the paper attributes suppression of the older high-energy-impact failures to gap-engineered junctions. | The paper explicitly states that it does not understand the cause of the newly observed large bursts, does not discriminate the proposed causes for the smaller events, and performs no intervention targeted at the new limiting events. | missing for the new rare-event mechanism |

## Operation replay

| input | transformation | assumption | output | exact source location | replay status |
|---|---|---|---|---|---|
| Distance-29 bit- and phase-flip repetition-code circuits | Execute 1,000 QEC cycles over 2 x 10^7 shots, split evenly by basis | The 72-qubit processor and stated repetition-code circuit remain the experimental object throughout the run | Detector records and terminal logical outcomes over 2 x 10^10 QEC cycles and 5.5 hours | Main Sec. IV, PDF p. 4 | complete |
| Terminal logical error probability `p_L` at `t = 1000` cycles | Convert with `epsilon_d = [1 - (1 - 2 p_L)^(1/t)] / 2` and subsample shorter odd-distance codes from the distance-29 data | Logical failures are represented by the source's per-step binomial model for the one-point conversion | Effective logical error per cycle versus code distance | Main Sec. IV, PDF p. 4; SI Sec. VI.B, PDF p. 23 | complete |
| Detector records and decoded outcomes for the high-distance subsamples | Select high-distance logical failures and inspect their time- and detector-resolved detection probabilities | Event classes are defined by their observed detector-probability signatures | A spatially grouped burst class and a one- or two-detector class | Main Sec. IV, PDF pp. 4–5; SI Sec. V.A and Fig. S7, PDF pp. 20–21 | complete |
| Detector events around a large burst | Average detector probabilities in ten-cycle windows and quartiles for Fig. 3d; fit an exponential decay; in Fig. S7 smooth detector traces with a Gaussian filter of sigma 2 | The displayed averaging and smoothing preserve the event-scale signature used for classification | Example decay constant 369 +/- 6 microseconds in Fig. 3d and a reported 400–700 microsecond range across bursts | Fig. 3d and caption, PDF p. 5; SI Sec. V.A and Fig. S7, PDF pp. 20–21 | complete |
| Classified rare events and high-distance decoded failures | Count co-occurrence by code distance and event type | The same decoded dataset supplies both the event signature and logical outcome | Large bursts account for all observed distance-27 errors and half of distance-21 to distance-25 errors; a single-noisy-detector event also causes high-distance errors | Main Sec. IV, PDF p. 5; SI Sec. V.A, PDF pp. 20–21 | complete |
| Newly observed large bursts and previously reported high-energy-impact bursts | Compare occurrence rate and fitted recovery time | The older event class is represented by the cited prior experiment; the present artifact supplies no particle or quasiparticle measurement for the new class | The present bursts are described as different from the older events, and their cause is left unknown | Main Sec. IV, PDF p. 5; SI Sec. V.A, PDF pp. 20–21 | complete |

## Project application

This source supports a Section 5 observation claim and a separate, narrower logical-consequence
claim. It does not support a causal-attribution claim.

- **Observation:** the evidence is hardware data from repeated QEC, not a simulated temporal-noise
  process. The qualifying object is a detector-probability pattern persisting across many cycles and,
  for the large bursts, across shot boundaries. Because the plotted records use smoothing or temporal
  aggregation, the prose should describe an observed event-scale detector signature rather than an
  unsmoothed microscopic trajectory.
- **Logical consequence:** the rare structures are found among decoded high-distance repetition-code
  failures and dominate the observed tail at the largest tested distances. This is stronger than merely
  observing correlation, but it remains an association within one dataset and decoder, not a controlled
  causal intervention.
- **Attribution:** the source-local result is an open cause. The TLS and coupler statements are candidate
  explanations for the smaller event class. The gap-engineering statement concerns suppression of an
  older high-energy-impact class. Neither licenses assigning the new large bursts to quasiparticles,
  leakage, TLSs, coupler excitations, drift, coherent accumulation, or a quantum environment.
- **Concept boundaries:** temporal persistence and spatial localization coexist in the large bursts;
  neither substitutes for the other. The paper separately studies ordinary calibration drift and
  leakage mitigation, but does not identify either as the cause of the new limiting bursts. Coherent
  error injection elsewhere in the paper is a controlled scaling experiment, not an explanation of
  the rare events. No operational non-Markovianity witness or causal-break test is performed.
- **Scope:** the apparent 10^-10 floor is a repetition-code result. The paper's distance-5 and distance-7
  surface-code demonstrations do not establish the same rare-event floor. The one-point per-cycle rate
  uses a binomial conversion, the paper calls the floor apparent, and no distance-29 failures were
  directly observed; these qualifications must accompany any quantitative use.

## Competing evidence and kill conditions

### Competing or adjacent evidence

- Kurilovich et al., arXiv:2506.18228v1, studies a distinct phase-error-burst class with
  interleaved qubit diagnostics and repetition-code data and adds controlled frequency-shift and
  echo-style interventions. That source may support a stronger attribution chain for its own events,
  but it cannot retrospectively identify the unknown bursts in arXiv:2408.13687v1.
- McEwen et al., arXiv:2402.15644v2 / Phys. Rev. Lett. 133, 240601 (2024), compares strongly and
  weakly gap-engineered qubits on one substrate and tests optical quasiparticle poisoning. It grounds
  mitigation of the older high-energy-impact mechanism, not the cause of the new once-per-hour
  repetition-code bursts.
- Kam et al., arXiv:2410.23779v4, uses the reported experimental signature as motivation for
  phenomenological temporal-event models. Its simulated streak construction is not a fitted model of
  these Google records and therefore cannot fill A1 for this source.

### Kill conditions

- Kill any statement that this source identifies the microscopic cause of the new large bursts: main
  PDF p. 5 explicitly states that the cause is not understood.
- Kill any statement that the new large bursts are the previously known high-energy/quasiparticle
  impacts: main PDF p. 5 and SI pp. 20–21 distinguish them by rate and recovery time.
- Kill any statement that O1 proves a non-leakage carrier or strict quantum non-Markovianity: neither
  a carrier measurement nor an operational process-memory test is present.
- Kill any statement that the 10^-10 floor was demonstrated for the surface code: the floor comes
  from high-distance repetition-code subsamples.
- Kill any statement that 10^-10 is an exact stationary floor: the source calls it apparent, reports no
  distance-29 errors, has only six large bursts, and converts terminal `p_L` with a binomial one-point
  model.
- Kill any claim of memory-aware decoder or control benefit: no intervention aimed at the new events
  and no memory-aware-versus-memory-blind decoder comparison is performed.
- Kill transfer claims beyond the tested processor, repetition-code geometry, data-acquisition regime,
  and decoder unless supported by a separate source.

## Source-local verdict

- `read_status`: complete
- `evidence_status`: persisted
- O1: closed for directly observed cross-cycle/shot detector structure; missing for a non-leakage or
  microscopic mechanism qualifier
- Q1: closed for association with high-distance repetition-code logical failures; missing for causal
  physical attribution and transfer
- A1: missing for the new limiting event classes
- downstream status: source-only note requires independent source review before manifest admission
