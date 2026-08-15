# Full-text review - Kurilovich, Roberts, Martin et al., "Correlated Error Bursts in a Gap-Engineered Superconducting Qubit Array" (arXiv:2506.18228)

> **Provenance (2026-06-28): FULL-TEXT read (Jingdu).** PDF `outputs/papers/2506.18228.pdf` -> txt
> `outputs/papers/2506.18228.txt` (PyMuPDF, 26 pp). All equation / figure references are from that
> extracted text. Figures not pixel-extracted; figure facts below come from captions and numeric values
> stated in the text. Tags: **[paper]** = stated by the paper; **[ours]** = project application/inference.

## Metadata [paper]
- **Authors / affiliation.** Vladislav D. Kurilovich, Gabrielle Roberts, Leigh S. Martin, Matt McEwen,
  Alec Eickbusch, Lara Faoro, Lev B. Ioffe, Juan Atalaya, Alexander Bilmes, John Mark Kreikebaum,
  Andreas Bengtsson, Paul Klimov, Matthew Neeley, Wojciech Mruczkiewicz, Kevin Miao, Igor L. Aleiner,
  Julian Kelly, Yu Chen, Kevin Satzinger, Alex Opremcak; Google Quantum AI.
- **Status.** arXiv:2506.18228v1 [quant-ph], 23/24 Jun 2025.
- **Type.** Hardware experiment + QP frequency-shift model + repetition-code correlation experiment.

## Executive summary [paper]
Gap engineering suppresses the long catastrophic T1 bursts associated with quasiparticle tunneling, but
the paper identifies a residual burst mechanism: impact-induced quasiparticles shift qubit frequencies,
causing correlated phase errors. The shifts are systematically negative, reach MHz scale (up to about
3 MHz, median about 2 MHz in detected bursts), and recover over about 1 ms. A 1 MHz shift over a 1 us QEC
cycle accumulates about `2*pi` phase, so this is directly QEC-relevant. Interleaved repetition-code and
coherence-monitor experiments show QEC detection bursts align with Ramsey/phase bursts, not the short
T1 burst. Echo-style circuit modifications suppress the phase-burst susceptibility and move the residual
detection burst closer to the T1-like short-burst signature.

## Method (deep) [paper]

### Coherence monitoring
The device is a 72-qubit Willow processor subset of 60 qubits. The monitoring sequence repeats Ramsey
`R`, spin-echo `E`, and relaxation `T1` measurements across all qubits. The total `R + E + T1` cycle is
`Delta t = 5 us`; each dataset has `N = 8e5` repeats (`4 s`), with 1800 datasets (`2 h`).

Burst detection uses the total number of errors across the array, a moving average subtraction, and an
exponential matched filter. Appendix B defines the template

```text
Template(t) = (2 / tau_MF) exp(-t/tau_MF) Theta(t),
tau_MF = 1.5 ms,
threshold MF[delta Sigma(t)] = 4.
```

The authors report false positives below about 2% at threshold 4, and more than 15% at threshold 3.

### Frequency-shift tomography
The tomography sequence repeats `T1`, `R_X`, and `R_Y` every `4.9 us`. Ramsey outcomes estimate phase
`phi = 2*pi*delta f_q*tau` with `tau = 750 ns`, using

```text
<M(R_X)> = (1 - cos(phi)) / 2,
<M(R_Y)> = (1 - sin(phi)) / 2,
delta f_q = phi / (2*pi*tau).
```

The extraction averages ten subsequent measurements, justified because `delta f_q` changes on about
`1 ms` timescales, far longer than the roughly `50 us` averaging window.

### QP frequency-shift model
The paper connects frequency shift to elevated quasiparticle density near Josephson junctions:

```text
delta f_q / f_q = -a x_qp,    a ~= 0.77 for their parameters.
```

QP recombination is modeled by

```text
dx_qp(t)/dt = -r x_qp(t)^2.
```

Combining these yields the non-exponential recovery

```text
delta f_q(t) = delta f_q(0) / (1 + t/t_rec),
t_rec = (1/r) * (a f_q / delta f_q(0)).
```

They fit `r = 1/(88 +- 12 ns)`.

## The MECHANISM (for implementation) [paper -> ours]

The Axis-2 hardware source is not a generic "burst rate". It should be split into:

1. **PhaseBurstSource.** A rare event with spatial footprint and per-qubit frequency-shift amplitudes
   `delta f_q,i(0)`, typically negative, MHz-scale, recovering roughly as
   `delta f_i(t)=delta f_i(0)/(1+t/t_rec_i)`. It fans out to detuning, phase accumulation during idle and
   gate windows, readout/syndrome sensitivity through circuit placement, and echo-removable controls.
2. **T1BurstSource.** A short transient relaxation burst at the beginning of the impact, with duration on
   the order of `10 us` (Appendix D reports reliable large-burst fits around `35 +- 15 us` for T1 bursts).
3. **Matched filter / detector source observable.** Bursts are identifiable from aggregate record spikes,
   but the matching observable depends on circuit sensitivity; phase-sensitive circuits see long phase
   bursts, echo-protected circuits see residual T1-like bursts.

The same event should generate both phase and T1 components, but they have different timescales and should
not be collapsed into one elevated depolarizing probability.

## The OBSERVABLE / metric [paper]
- Coherence monitor: total Ramsey/echo/T1 error counts across qubits, matched-filtered over time.
- Frequency shift: per-qubit `delta f_q(t)` reconstructed from `R_X/R_Y` tomography.
- QEC record: repetition-code detection events per cycle, matched-filtered and correlated with monitor
  bursts.
- Circuit sensitivity: mean repetition-code detection probability vs injected uniform `delta f_q`.

## Findings + numbers [paper]
- Frequency shifts are systematically negative, MHz-scale, and last about `1 ms`; an example reaches
  `2.7 MHz` at an epicenter.
- Detected burst statistics over 5.2 h: 265 bursts; measured rate about `1/(71 s)`; median burst size
  15 qubits (defined by `|delta f_q(0)| > 3 sigma_f ~= 200 kHz`); events affecting more than half the
  array occur at about `1/(22 min)`; median peak frequency shift about `2 MHz`.
- Phase errors persist about `1 ms`. The initial T1 burst lasts on the order of `10 us`; it is more than
  two orders of magnitude shorter than T1 bursts on non-gap-engineered devices, but still exceeds a
  typical `1 us` QEC cycle.
- In interleaved experiments, repetition-code detection bursts align closely with Ramsey phase bursts and
  not with the T1 burst duration.
- Controlled injection: a spatially uniform `2 MHz` shift increases detection probability by about `35%`
  in the original repetition-code circuit; after echo-style modification, the response to `2 MHz` falls to
  about `5%`.

## Limitations [paper]
- The hardware is a specific gap-engineered Willow-generation device; rates and amplitudes are not universal.
- The repetition-code circuits are diagnostic; this is not a full surface-code threshold paper.
- The matched-filter threshold misses small or differently shaped bursts by construction.
- Echo mitigation makes phase bursts partially removable at the circuit level; residual T1 bursts remain.

## Relevance to AI_QEC [ours]
1. **This is a concrete Axis-2 source class.** The latent event persists across many QEC cycles and drives
   multiple mechanism parameters from one source: detuning/phase, T1, SPAM/measurement sensitivity, and
   possibly gate errors.
2. **It corrects the burst taxonomy.** Tan et al. gives a useful elevated-depolarizing stress model, but
   this Google hardware paper says residual gap-engineered bursts are phase/frequency-shift dominated.
   A simulator that only implements uniform depolarizing burst would miss the deployed hardware mechanism.
3. **It supplies a real circuit-level removal control.** Echo/dynamical-decoupling can suppress the phase
   part. Therefore PhaseBurstSource belongs in the "material / circuit removable" audit: it is a real
   physical source, but some record imprint is removable by schedule design.
4. **It is not Axis-1.** The source is cross-time and shared/spatially extended. Axis-1 joint-L may be used
   inside each substep to apply detuning/dephasing/leakage/T1 jointly, but the burst identity and decay live
   in Axis-2.
5. **First simulator hook:** implement a `PhaseBurstSource` timeline with per-shot latent event times,
   per-qubit amplitudes, non-exponential recovery, matched independent baseline, and an echo/sensitivity
   flag in the circuit schedule.

## How to use / trust + open questions [ours]
- **Trust:** high for hardware phenomenology and order-of-magnitude parameters; full text read. The direct
  QEC result is on a repetition-code diagnostic, not a full XZZX surface-code simulator.
- **Open implementation choice:** use the paper's non-exponential recovery exactly for phase shift; choose
  a bracketed spatial footprint model (uniform, radial, clustered) because the paper reports footprint
  statistics but not a single universal spatial kernel.
- **Acceptance implication:** G4/G6 record faithfulness for this source should include a phase-sensitive
  circuit and an echo-protected negative/control circuit, not only a marginal error-rate comparison.
