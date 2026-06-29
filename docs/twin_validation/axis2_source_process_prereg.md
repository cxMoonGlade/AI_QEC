# Axis-2 SourceProcess preregistration

**Status:** theory-first pre-implementation contract, 2026-06-28.

This prereg covers the next Axis-2 module: explicit source timelines that feed
the existing `Theta(z_t)` fan-out. It does not modify the Axis-1 joint-L
assembler and does not claim record-level novelty by itself.

## Grounding

- `docs/twin_validation/axis2_cross_time_literature_sweep.md`: current
  literature synthesis and build matrix.
- `docs/twin_validation/source_coupling_fanout_prereg.md`: existing
  `Theta(z_t)` fan-out contract.
- `docs/twin_validation/nonmarkovian_coupling_constraint_ledger.md`: C1-C10
  source-layer constraints.
- `docs/papers/reading_notes/kam_nonmarkovian_surface_code_2410.23779.md`:
  Class-1/2 multi-time streak hazard and insufficiency of pairwise-only
  statistics.
- `docs/papers/reading_notes/kam_spatiotemporal_pauli_processes_2603.05474.md`:
  SPP, temporal storm HMM, transfer-operator metrics, matched-marginal reduced
  Pauli comparator.
- `docs/papers/reading_notes/kurilovich_phase_error_bursts_gap_engineered_2506.18228.md`:
  gap-engineered hardware phase-burst source.
- `docs/papers/reading_notes/tan_surface_code_error_bursts_2406.18897.md`:
  elevated-rate burst stress model and syndrome-density observable.
- `docs/papers/reading_notes/bhardwaj_drifting_noise_estimation_2511.09491.md`:
  drifting marginal-rate baseline.
- `docs/papers/reading_notes/gao_nonlocal_nonmarkovian_tls_2605.23385.md`:
  microscopic TLS / 1/f source origin.

## Object

Axis-2 is an explicit source process:

```text
SourceProcess.sample(seed, n_cycles, layout) -> SourceTimeline
SourceTimeline.latent[t]                     -> evaluator-only source state
SourceTimeline.payload[t]                    -> fields consumed by Theta(...)
SourceTimeline.independent_baseline(seed)    -> matched-marginal control
```

The timeline is evaluator-side truth. Learner-visible records see only the
circuit/backend outputs produced downstream.

## First source families

### OneOverFDriftSource / RTNSource

Purpose: analog source payload for the existing frequency-like fan-out. These
reuse the validated RTN/1f source-layer work and `source_coupling.source_to_params`.

Required checks:

- source autocorrelation / PSD has the registered shape;
- each fan-out field has the same marginal under shared and independent
  baseline;
- cross-field same-cycle correlations collapse under independent baseline.

Epistemic class: source formulas and marginal-preservation identities are
**(a)**; physical magnitude constants are **(c)** unless calibrated.

### PhaseBurstSource

Purpose: hardware-inspired burst source that modulates detuning/phase-sensitive
windows and optionally a short T1 component.

Grounded form from Kurilovich et al.:

```text
delta f_i(t) = delta f_i(0) / (1 + (t-t0)/t_rec_i)
```

with event time `t0`, spatial footprint, negative MHz-scale
`delta f_i(0)`, about millisecond recovery, and an initial T1 burst on the
order of 10 us.

Required checks:

- sampled event counts and footprints match configured priors;
- recovery curve follows the registered non-exponential form;
- phase-sensitive schedule windows accumulate phase from the source;
- echo/refocusing windows suppress the phase contribution in a declared control;
- matched independent baseline preserves per-field marginals but breaks shared
  event timing.

Epistemic class: recovery equation and source-to-phase algebra are **(a)** once
parameters are fixed; hardware magnitudes are **(b)/(c)** brackets, not
universal constants.

### TemporalStormSPPSource

Purpose: reduced Pauli / record-level comparator, not analog truth.

Exact HMM:

```text
T = [[1-a, a],
     [b, 1-b]],
lambda_2 = 1-a-b,
xi = -1 / ln(1-a-b),
pbar(x) = (b q_0^(x) + a q_1^(x)) / (a+b).
```

Required checks:

- empirical transition matrix matches `a,b`;
- empirical marginals match `pbar(x)` while `xi` is swept;
- independent baseline preserves `pbar(x)` and collapses temporal correlation;
- reported observables include at least one multi-time statistic, not only a
  pairwise lag covariance.

Epistemic class: HMM equations and matched-marginal identities are **(a)**;
QEC impact bands are **(b)** until run in our carrier.

## Explicit non-goals

- Do not model Axis-2 as independent time-dependent positive Lindblad rates.
  That is a drifting Markovian baseline.
- Do not treat SPP/corrqec as validation of full analog joint-L, coherent
  drive/ZZ, or qutrit leakage.
- Do not make G4/G6 a source-only gate. Record-level faithfulness requires a
  record carrier and independent/reduced comparator appropriate to that carrier.
- Do not start with QCA/PCA. It is a later stress-test source after the generic
  timeline and temporal storm comparator are stable.

## Acceptance gates before downstream records

1. **Source self-audit:** analytic/empirical autocorrelation, PSD or transfer
   spectrum, marginals, and fitted source parameters.
2. **Fan-out audit:** shared-source cross-mechanism correlation vs independent
   matched-marginal baseline.
3. **Serialization audit:** source truth can be stored and replayed exactly
   from a seed or artifact.
4. **Schedule audit:** payload fields are consumed only by declared circuit
   windows / operations; idle and echo handling are explicit.
5. **Reduced-comparator audit:** SPP-style sources report `xi`, `pbar`, and a
   multi-time statistic.

Only after these pass should the source be used for a QEC record-faithfulness
gate.

## Build order

1. Add base `SourceProcess` / `SourceTimeline` under `qec_twin.mechanisms`, not
   under `forward`.
2. Wrap existing 1/f / RTN trajectory generation into the base interface.
3. Add `PhaseBurstSource` with schedule sensitivity hooks.
4. Add `TemporalStormSPPSource` as the first reduced-Pauli comparator.
5. Then connect selected source timelines into the frontend/backend record path.
