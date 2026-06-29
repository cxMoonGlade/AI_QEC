# Axis-2 cross-time error-coupling literature synthesis

**Status:** theory-first web sweep + local-note audit + close-read synthesis,
2026-06-28.

This file routes the next Axis-2 build. It is not a substitute for the committed
reading notes, but records which literature objects are now safe to build from
and which are only claim-boundary context.

## Topline

The current implementation has a valid `Theta(z_t)` fan-out layer, but that is
only the map from one source draw to mechanism parameters. A real cross-time
coupling simulator also needs explicit source processes, source timelines,
matched-marginal controls, and multi-time observables.

Therefore the next Axis-2 layer should be:

```text
SourceProcess.sample(seed, n_cycles, layout) -> SourceTimeline
SourceTimeline.latent[t]                     -> evaluator-only latent state
SourceTimeline.payload[t]                    -> source fields exposed to Theta
Theta(payload[t])                            -> CoupledMechanismParams[t]
SourceTimeline.independent_baseline(seed)    -> matched-marginal control
```

The core anti-toy rule is unchanged: **a time index on independent positive
Lindblad rates is a Markovian drifting-rate baseline, not owned cross-time
coupling.** The owned object is the explicit source carrying memory across
cycles.

## Newly closed load-bearing notes

- `docs/papers/reading_notes/kam_spatiotemporal_pauli_processes_2603.05474.md`
  now grounds the reduced Pauli / record-level Axis-2 comparator:
  multi-time Pauli twirl, SPPs, transfer operators, HMM equivalence, temporal
  storm model, and QCA/PCA stress test.
- `docs/papers/reading_notes/kurilovich_phase_error_bursts_gap_engineered_2506.18228.md`
  now grounds a hardware `PhaseBurstSource`: MHz-scale, millisecond-recovery
  frequency-shift bursts in gap-engineered superconducting qubit arrays, with
  repetition-code detection impact and echo/removal controls.

## Literature decision matrix

| Source / framework | Build role | What it gives | Boundary |
|---|---|---|---|
| Kam et al. 2024, non-Markovian surface-code memory (`2410.23779`) | Record-level hazard taxonomy | Class-1/2 streaky multi-time correlations are harmful; pairwise statistics are insufficient | QEC Pauli/circuit-level, not analog bath truth |
| Kam et al. 2026, SPP (`2603.05474`) | Reduced Pauli comparator and HMM source | Multi-time Pauli twirl -> SPP; transfer `T`, emission `E_f`, `xi`; two-state temporal storm with fixed marginals | Comparator / reduced carrier only; not coherent/leakage/joint-L validation |
| Kurilovich et al. 2025, gap-engineered bursts (`2506.18228`) | Hardware `PhaseBurstSource` | Shared frequency-shift event: `delta f_q(t)`, phase errors, QEC detections, echo suppression | Repetition-code diagnostic; device-specific magnitudes |
| McEwen et al. 2021 (`2104.05219`) | Hardware `T1BurstSource` / cosmic-ray baseline | Chip-wide quasiparticle T1 bursts, event rate and long recovery | Older non-gap-engineered regime; mostly T1, not phase |
| Tan et al. 2024/2025 (`2406.18897`) | Elevated-rate burst stress model | Single-round burst thresholds, syndrome-density observable, teraquop footprint | Idealized elevated depolarizing burst; not phase-source physics |
| Bhardwaj et al. 2025 (`2511.09491`) | Drifting marginal-rate baseline | Time-varying marginal rates and adaptive decoder-weight utility | Drift is not sufficient for multi-time contribution |
| Gao et al. 2026 TLS (`2605.23385`) | Microscopic TLS / 1/f source origin | Shared TLS, nonlocal coupling, 1/f dephasing, RTN-like jumps | Device-physics source; QEC record imprint still needs interface |
| Fowler leakage (`1308.6642`) | Persistent leakage memory | Leakage persists across rounds and needs reset/repumping semantics | Not a Pauli source; needs qutrit carrier |
| Terhal-Burkard + AKP (`0402104`, `0510231`) | Claim boundary | Non-Markovian / long-range correlated noise can be threshold-compatible if local/weak enough | Not simulator recipes |
| Process tensor / memory-kernel papers (`2012.01894`, `2004.11038`, `2007.03234`) | Formal boundary | Multi-time process object, Markov order, MPO/bond-memory view, transfer tensors | General formalism; SPP is the QEC-facing specialization |

## Operable equations and models

### 1. Temporal storm SPP source

From `2603.05474`, a two-state latent environment has transition matrix

```text
T = [[1-a, a],
     [b, 1-b]],
lambda_2 = 1-a-b,
Delta = a+b,
xi = -1 / ln(1-a-b).
```

Emissions are Pauli channels conditioned on the updated latent state:

```text
E_s[rho] = sum_x q_s^(x) sigma_x rho sigma_x,
pbar(x) = (b q_0^(x) + a q_1^(x)) / (a+b).
```

This is the first reduced-Pauli comparator to build because it can sweep
correlation length while fixing single-round marginals. It directly supports a
matched independent baseline.

### 2. SPP transfer / multi-time observables

For SPP matrices `A_x`:

```text
T   = sum_x A_x,
E_f = sum_x f(x) A_x,
Etilde_f = E_f - <f> T,
C_f,g(tau) = <l1| Etilde_f T^(tau-1) Etilde_g |r1>.
```

The multi-point observable is

```text
C_{f1,...,fm}
  = <l1| Etilde_f1 T^Delta_t1 Etilde_f2 ... T^Delta_t{m-1} Etilde_fm |r1>.
```

This is the correct anti-pairwise record statistic for SPP-style Axis-2. A
2-point lag statistic may be reported, but it cannot be the only gate.

### 3. Phase-burst source

From `2506.18228`, the hardware frequency-shift source is

```text
delta f_q / f_q = -a x_qp,
dx_qp/dt = -r x_qp^2,
delta f_q(t) = delta f_q(0) / (1 + t/t_rec),
t_rec = (1/r) * (a f_q / delta f_q(0)).
```

Grounded magnitudes:

- frequency shifts are negative and MHz-scale; detected bursts have median peak
  about `2 MHz`, with examples around `2.7 MHz` and up to about `3 MHz`;
- recovery is about `1 ms`;
- initial T1 burst is on the order of `10 us`;
- a `1 MHz` shift over a `1 us` QEC cycle accumulates about `2*pi` phase;
- a uniform `2 MHz` injected shift increases repetition-code detection
  probability by about `35%` in the original circuit and about `5%` after
  echo-style modification.

This source must fan out through detuning/phase-sensitive circuit windows, not
only through a depolarizing probability.

## Source taxonomy for the simulator

### Go first

1. `SourceProcess` / `SourceTimeline` base objects with evaluator-only latent
   storage, payload fields, marginal statistics, and matched-independent control.
2. `OneOverFDriftSource` and `RTNSource` feeding the existing
   `source_coupling.source_to_params` fan-out.
3. `PhaseBurstSource` with event time, spatial footprint, per-qubit
   `delta_fq0`, non-exponential recovery, and optional short `T1` companion.
4. `TemporalStormSPPSource` as a reduced Pauli comparator with exact `xi`,
   `pbar(x)`, and HMM sampling.

### Defer but keep in design

1. `QCAPCASource`: a 2D spatiotemporal SPP stress test. It is valuable but
   heavier: lattice geometry, burn-in, density statistics, pseudo-critical
   tuning, and distance-scaling benchmarks.
2. `LeakagePersistenceSource`: leakage is not a scalar source draw. It needs a
   qutrit carrier state and reset/repumping semantics, then can be connected to
   cross-time coupling.
3. Full process-tensor / MPO learning: formal background only for now.

## Required controls and observables

Every source family needs:

- **latent diagnostics:** autocorrelation, PSD or transfer-spectrum / `xi`, and
  source parameter summary;
- **fan-out diagnostics:** same-cycle cross-mechanism correlation under shared
  source, collapsed under independent-per-field baseline;
- **matched marginal control:** preserve per-field marginals while breaking the
  shared latent timeline;
- **record-level faithfulness when a record carrier exists:** timelike string,
  excess entropy / multi-point statistic, or decoder-facing LER under a frozen
  marginal comparator;
- **removal/sensitivity control when applicable:** phase-burst echo protection,
  burst-aware vs burst-blind decoder, leakage reset/repump.

## Axis separation

- **Axis-1:** instantaneous joint channel inside a substep. This remains
  `joint_lindbladian.py` / G2 and channel-oracle validation.
- **Axis-2:** source timeline across cycles. A source may feed Axis-1 parameters
  at each substep, but its contribution is the cross-time latent path and the
  matched-marginal ablation.
- **SPP/corrqec scope:** SPP-like sources validate reduced Pauli temporal-mask
  behaviour and record-level comparators. They do not validate analog coherent
  joint-L, qutrit leakage, or full master-equation fidelity.

## Go / no-go

- **Go now:** implement `SourceProcess` / `SourceTimeline`, then wire
  `OneOverFDriftSource`, `RTNSource`, and `PhaseBurstSource` into the existing
  `Theta(z_t)` fan-out.
- **Go next:** implement `TemporalStormSPPSource` as a reduced-Pauli comparator
  and negative-control harness.
- **Do not do:** implement Axis-2 as independent per-mechanism time-dependent
  positive Lindblad rates; that is the Markovian drifting-rate baseline.
- **Do not do:** use SPP/corrqec as an "independent validator" for full analog
  joint-L/leakage/coherent physics.

## Remaining build-time choices

1. **Timeline schema.** Decide whether latent state is stored as arrays, dataclass
   rows, or a compact typed payload object. Recommendation: typed dataclass plus
   array views for GPU kernels.
2. **Spatial footprint.** Phase bursts need uniform, radial, and clustered
   footprint modes. The first implementation can use uniform/clustered brackets
   and record that hardware spatial kernels are device-specific.
3. **Circuit sensitivity hooks.** PhaseBurstSource must know which schedule
   windows accumulate phase and whether echo/refocusing cancels it.
4. **SPP granularity.** Temporal storm can be per-register shared, per-qubit
   independent, or clustered. First build should support `scope={global,
   cluster, per_site}` because the science depends on this distinction.

## Sources used

- https://arxiv.org/abs/2603.05474
- https://arxiv.org/abs/2506.18228
- https://arxiv.org/abs/2410.23779
- https://arxiv.org/abs/2511.09491
- https://arxiv.org/abs/2406.18897
- https://arxiv.org/abs/2104.05219
- https://arxiv.org/abs/1308.6642
- https://arxiv.org/abs/2605.23385
- https://arxiv.org/abs/2502.18929
- https://arxiv.org/abs/quant-ph/0402104
- https://arxiv.org/abs/quant-ph/0510231
- https://arxiv.org/abs/2012.01894
- https://arxiv.org/abs/2004.11038
- https://arxiv.org/abs/2007.03234
