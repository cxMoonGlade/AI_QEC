# Numerical provenance

This is the binding current-state ledger for values, defaults, numerical gates, and run manifests in
`error_coupling_simulator`. It describes what the installed source and current tests may support. A
specified noise process is a model; a default, citation, or passing software check does not make it a
calibrated device model.

## Provenance kinds

Every claim-bearing value has exactly one primary kind.

| Kind | Meaning | Permitted claim |
|---|---|---|
| `paper-measured` | Directly measured value from a named experiment | Only the cited device, protocol, observable, and uncertainty |
| `paper-derived` | Value obtained from a cited equation and cited inputs | Only under the stated derivation assumptions |
| `dataset-measured` | Value read from a named external dataset field | Only that artifact and the declared transform |
| `calibrated-to-paper` | Project parameter fitted to the same observable reported by a paper, with a complete fit/transform chain | Model calibration to that target, never direct device measurement |
| `project-design` | Synthetic mechanism point, sweep, comparator, normalization, or scientific design choice | The declared model calculation only |
| `convenience-default` | API, execution, or routing default | Implementation use only |
| `numerical-only` | Floating tolerance, solver setting, resource cap, or software tripwire | Numerical or implementation decision only |

A `paper-*`, `dataset-measured`, or `calibrated-to-paper` row must carry the exact locator, units,
device/protocol scope, observable identity, and transformation chain. Missing fields fail closed to
`project-design` or `implementation_only`.

Two sources that measure different objects do not validate their Cartesian product. Such a tuple is a
literature-scale composite benchmark, not a calibrated physical cell. Describing a range as broadly
representative additionally requires compatible independent measurements and an explicit uncertainty
or sensitivity analysis.

Runtime metadata does not override this ledger. If a manifest assigns a stronger kind than the
underlying object and transformation support, the artifact is nonconforming and remains
implementation-only.

## Current value and default ledger

### Qutrit leakage and within-cycle execution

| Owner/object | Current values | Kind | Claim boundary |
|---|---|---|---|
| Registered raw-angle preset | `theta=0.30 rad`, `g_seep=0.09`, `g_heat=0`, `b=0.9`, arm `A`, readout `biased_b` | `project-design` | Synthetic strong-angle benchmark; no component tuple is a measured device cell |
| Registered model-rate preset | target `leakage_rate=5e-3`, resolved `theta=0.10244435242990924 rad`, `g_seep=0.09`, `g_heat=0`, `b=0.9`, arm `A`, readout `biased_b` | `project-design` | `theta` is solved in the declared channel. Miao Fig. 3c is only an approximate leakage-population scale anchor, not a direct measurement of this subspace diagnostic or a device calibration |
| Leakage process defaults | `theta=0.07`, `g_seep=0.09`, `g_heat=0` | `project-design` | Convenience center for the declared channel family; not a headline physical point |
| Leakage sweeps | `theta=(0,.045,.07,.10)`, `g_seep=(.05,.09,.10)`, `g_heat=(0,.005)` | `project-design` | Synthetic sensitivity grid |
| Subspace diagnostic target ranges | `leakage_rate=(1e-3,5e-3)`, `seepage_rate=(.05,.10)` | `project-design` with literature-scale context | Target regimes for the declared channel; the endpoints are not jointly measured rate bands |
| Leaked-readout bias | interval `[.5,1]`, grid `(.5,.75,1)`, registered preset point `.9`; bare `RunSpec` default `1` | `project-design` for the sweep; `convenience-default` for bare `RunSpec` | A required nuisance sensitivity. No point value or direction is a calibrated binary readout law |
| Within-cycle channel siting | `WC_LEAK_FRAC=.25`, four applications of `exp(L/4)` | `project-design` | Project normalization and schedule siting; no source establishes it as a physical quarter-CZ law |
| Within-cycle run defaults | logical input `0`, arm `A`, `N=1000`, seed `0`, work chunk `1024`, rounds from schedule, `final -> complex128` | `convenience-default` | A direct `RunSpec` is not a registered scientific run unless a trusted manifest is bound |
| Precision policy | `optimization -> complex64/screening_only`; `final|certification -> complex128/c128_candidate` | `numerical-only` | Only the fused within-cycle executor may use complex64. A candidate still must pass its scientific gates |
| Exact qutrit frontend defaults | `num_qutrits=3`, `cycles=1`, `shots=1024`, seed `0`, process defaults above | `convenience-default` | Bounded implementation surface, not distributional evidence by default |
| Multi-level CZ parameters | `alpha_flux=alpha_stat=-300 MHz`, `J1=15 MHz`, `omega_flux_max=6.7 GHz`, `omega_stat=6.0 GHz`, `t_gate=25 ns`, net-zero pulse, `t_ramp=3 ns`, dissipation off, `T1=Tphi=75 us`, five simulated levels | `project-design` literature-scale composite | Formula/channel fixture. Individual literature scales do not validate the complete tuple or a target device |

`leakage_rate` and `seepage_rate` are evaluator-only subspace-transition diagnostics computed from the
declared channel. `level1_output_leakage_coherence` is the trace norm of the cross-subspace block of
`E(|1><1|)` for that fixed input; it is neither a channel-averaged coherence rate nor an if-and-only-if
classifier of physical cause. None of these values enters the emitted record or proves that two
channels with matching diagnostics have the same record law.

Current preset/runtime metadata classifies the `5e-3` project-channel target and its resolved angle
as `project-design`. The Miao value is retained only as cross-observable scale context; the manifest
records that no identity transform or direct observable match is established. The leaked-readout
manifest likewise classifies the binary map and its direction as `project-design` and records that
the cited literature does not determine that map.

### Classical sources and parameter fan-out

| Owner/object | Current defaults | Kind | Claim boundary |
|---|---|---|---|
| `RTNSource` | amplitude `1e-4 rad/ns`, directional rate `.05/cycle`, cycle `1000 ns` | `project-design` | Controlled symmetric finite-RTN source |
| `OneOverFDriftSource` | total amplitude `1e-4 rad/ns`, eight equal-amplitude modes, geometric rates `.005... .5/cycle`, cycle `1000 ns` | `project-design` | Finite sum of Lorentzian RTNs; a finite-band approximation, not measured `1/f` device noise |
| `PhaseBurstSource` | event probability `0`, peak `-2 MHz`, recovery `1 ms`, `T1` duration `10 us`, phase window/cycle `1000 ns`, echo factor `.05` | `project-design` | Explicit burst comparator; zero probability is the inert default |
| `TemporalStormSPPSource` | `a=.01`, `b=.10`, calm `(0.999,1/3000,1/3000,1/3000)`, storm `(.97,.01,.01,.01)`, global scope | `project-design` | Reduced Pauli HMM comparator, not analog truth |
| Static-ZZ fan-out | `6.0/6.1 GHz`, `alpha=-300 MHz`, gate `25 ns`, base phase `1.6e-4 rad`, with `phi=zeta*t/4` | `project-design` | Declared project Hamiltonian convention; do not compare `phi` directly to a conditional phase using a different coefficient |
| `SourceCouplingConfig` | `z_scale=1e-4 rad/ns`, `Tphi=75 us`, drive `pi/25 rad/ns`, spillover `.001`, readout `.01`, reset `.005`, CZ depolarization `.002`, and declared qubit-process sensitivities | `convenience-default` whose values are `project-design` | Parameter map for controlled source experiments; it has no source-to-qutrit-leakage fan-out, and the class name and formulas do not supply calibration |
| Source-to-Stim Pauli projection | base probability `1e-3`, sensitivity `1`, source scale `1e-4` | `project-design` | Explicit reduced Pauli projection only |

The float64 `RTNSource` sampling domain is the structural point `gamma_per_cycle=0` plus the
discrete interval from `2.775557561562892e-17` through `18.71497387511852` per cycle, where both
`flip_probability` and `autocorr_base` remain representable away from their endpoints. A positive
transition sum for `TemporalStormSPPSource` must likewise yield a finite correlation length; the
first accepted positive binary64 sum is `5.56268464626801e-309`. For
`from_fixed_marginal`, a requested correlation length at or below approximately
`1/(54 ln 2) = 0.0267165748312771` cycles can make the transition sum round to one and is rejected.
These are binary64 representability bounds, not physical cutoffs. Values immediately above the
fixed-marginal lower boundary remain quantized and are not promised to round-trip to the requested
correlation length exactly.

`OneOverFDriftSource` rejects a nonzero total amplitude when division by `sqrt(n_fluctuators)`
would manufacture zero per-mode amplitudes. Its analytic finite-Lorentzian PSD is evaluated as an
exact rational sum over the actual binary64 mode amplitudes and rates and rounded only once at the
public result. A mathematically positive PSD that would underflow to structural zero, or overflow to
a non-finite value, is rejected.

Positive-rate and logit fan-out preserve an exact zero shift by returning the input value directly.
For nonzero shifts, shared scaled-product arithmetic forms `sensitivity * draw / scale` directly
from the three raw binary64 inputs instead of first rounding `draw / scale`. It keeps the ordinary
operation order only when its ratio and final result are safely normal; otherwise an exact rational
`Fraction` fallback rounds the final product/ratio, including half-minimum-subnormal ties-to-even. A
nonzero exact-float product that cannot be represented as a nonzero binary64 shift is rejected rather
than treated as a structural zero.

The positive-rate value path keeps ordinary `base * exp(shift)` only when both the exponential and
final product are safely normal and away from the upper endpoint. Otherwise a 200-digit
exact-binary64-input `Decimal` product/exponential recovers the representable result without a
log-domain sum; subnormal output rounding is classified explicitly on the binary64 lattice. A zero,
subnormal, or overflowing exponential intermediate is never trusted merely because its product
happens to be finite.

Probability fan-out uses the odds-domain value map
`odds * exp(shift) / (1 + odds * exp(shift))`, backed by the same scaled-exponential primitive. It
does not form a rounded `logit(p) + shift` value path and does not cap a logit. Whenever the rounded
odds-domain result reaches an open-interval endpoint, an exact-input `Decimal` log-odds comparison
at 1200-digit precision classifies whether the mathematical result belongs to the binary64
open-probability domain. The precision is required because a minimum-subnormal shift can move an
endpoint probability outside the domain only beyond the 323rd decimal place. This also catches an
outside value whose scaled odds rounded to the adjacent interior ULP. A result outside the domain is
rejected; saturation is never replaced with endpoint probability zero or one.

When a two-dimensional source payload is projected onto several sites, the site mean is formed from
the exact rational values of the binary64 inputs and rounded once. Exact signed cancellation remains
a structural zero shift; a nonzero exact mean that would round to zero is rejected rather than routed
through the zero-shift identity branch.

Static-ZZ evaluation uses the algebraically equivalent stable identity
`zeta = 4 J^2 alpha / ((Delta-alpha)(Delta+alpha))`; exact zero requires `J=0` or `alpha=0`.
Unsafe intermediate products and the top sixteen finite binary64 values use exact rational recovery,
while an unrepresentable nonzero final value is rejected. Inverting `phi=zeta*t/4` rejects every
strictly sign-inconsistent `phi` without a numerical dead zone and uses the raw
`Delta, alpha, phi, t` inputs end-to-end; it never first materializes a possibly subnormal rounded
unit-`J` coefficient. Its fallback forms exact rational `J^2` and takes a 300-digit square root before
binary64 conversion, so a nonrepresentable intermediate `J^2` may still yield a representable
nonzero `J`. The ordinary all-normal inversion path has a fixed independent regression at its
observed 2-ULP worst case; it is not documented as a 1-ULP path. The forward `phi=zeta*t/4` map uses
the shared scaled product/ratio primitive.

`CoupledNoiseParameters` is the public coupling emission boundary: source and normalized draw keys
must each occur exactly once in canonical order; coupling mode must be `shared` or `independent`;
emitted scalar fields must be finite; rates/exchange must be nonnegative; and emitted probabilities
must lie in `[0,1)`. The sole non-finite structural representation is `tphi_ns=+inf` when
`gamma_phi_per_ns` is exactly zero; a positive dephasing rate requires a finite positive reciprocal
lifetime exactly equal to `1/gamma_phi_per_ns`. Config and emitted-bundle numeric scalars are copied
to primitive floats, named draws are copied to canonical tuples, and schema/mode strings are copied
before validation, so mutating a caller-owned list or zero-dimensional array cannot change a later
manifest.

Cross-mechanism Pearson diagnostics reject non-finite selected fields, recognize only exact constant
series as degenerate, and center values after per-field scale normalization. The shared numerical
threshold is not used to turn a small but nonconstant trajectory into zero correlation, and finite
`+/-DBL_MAX` inputs cannot overflow the variance calculation into `NaN`.

The optional record-to-DEM reduction exposes `pair_floor_abs=1e-5` and `pair_floor_sigma=4` as
declared class-(c) edge-selection parameters. Both must be finite and nonnegative and are emitted in
the diagnostics. They select a decoder-facing reduced topology; they do not floor, add, or redefine
physical probability mass. A non-identifiable Spitz pair or standard error remains `NaN` with a
false `pij_identifiable` entry and is excluded from the optional edge reduction; it is never emitted
in diagnostics as structural zero. Every strictly negative boundary residual is recorded as a
`negative_residual` model inconsistency even when its magnitude lies below `pair_floor_abs`; the
decoder edge-selection floor cannot hide it. Exact residual zero alone remains structurally absent.

Validated parameters of `RTNSource`, `OneOverFDriftSource`, `PhaseBurstSource`, and
`TemporalStormSPPSource` are copied to primitive floats/integers/strings or immutable tuples during
construction. A caller-owned zero-dimensional array, event list, or probability list therefore
cannot mutate a validated process into a different or invalid emission domain.

`SourceTimeline` preserves exact payload and evaluator-only latent arrays. A matched-marginal control
preserves each selected row while permuting cycle order; the per-field independent ablation is
explicitly unphysical and must not be called the matched source.

### Execution, carrier, and resource defaults

| Owner/object | Current values | Kind | Claim boundary |
|---|---|---|---|
| Analog duration fallback | 1q `20-30 ns` (nominal `25`), 2q `25-45 ns` (nominal `30`), idle `0-300 ns`, measurement `100-1000 ns`, reset `100-500 ns` | `project-design` | Used only when an explicit duration is absent; all derived channel strengths inherit the bracket |
| Axis-1 joint-channel fixture | `zeta/2pi=370 kHz`, `T1=Tphi=30 us`, drive `pi/25 rad/ns`, declared duration grids and prediction bands | `project-design` | BCH/channel-comparison fixture, not hardware calibration |
| MCWF/MPS execution | one microstep, first-order finite step, one trajectory, leaked-readout `b=1`, no bond cap, probability-mass budget `.1` | `convenience-default` plus `numerical-only` budget | Restricted verification path; one trajectory is not distribution evidence |
| QT/MPS execution | `max_branches=4096`, one microstep, first-order product formula, no bond/discarded-weight gate unless supplied, dense reference requested | `convenience-default` | Restricted verification path, not universal joint-generator evidence. A complete capped run with actual loss is rejected unless both local worst-cut and path-total gates are explicit and pass |
| PEPO solver | complex128; NTU at most 20 sweeps, relative stop and pseudoinverse tolerance `1e-12`; one-site fit at most 64 iterations | `numerical-only` | Solver controls only; they do not certify positivity or record faithfulness |
| PEPO negativity witness default floor | `4.8e-4` | `project-design` numerical witness | Default witness scale, not a physical negativity bound or record certificate |
| PEPS resource guards | pre-cut cap `W_max=160`, abort when a grown bond exceeds `D_abort=40` | `numerical-only` | Orderly resource limits, never a claim that the retained state or record is accurate |
| PEPS environment truncation | current test uses `eps_fid=1e-8`; 20 ALS sweeps; optimization floor `1e-9`; instability guards `1e-12` and `1e-6` | `numerical-only` | Local environment objective only. The current entropy equality is all-noop, so the non-degeneracy gate is RED and blocks scientific acceptance |

## Finite-RTN free-induction diagnostic boundary

For the current `OneOverFDriftSource` defaults, each mode has phase amplitude

```text
a_k = 1e-4 rad/ns * 1000 ns / sqrt(8) = 0.035355339059327376 rad/cycle,
gamma_k = geomspace(0.005, 0.5, 8) per cycle.
```

The first three modes have `a_k/gamma_k > 1`; a Gaussian weak-noise surrogate is therefore not an
exact replacement for the finite-RTN process.

The retained diagnostic defines two separate one-qubit longitudinal free-induction lifts:

1. continuous symmetric-CTMC interpolation between cycle endpoints;
2. a cycle-held phase using the emitted endpoint state.

Each lift compares a factorized result with an independent full-`2^8` state oracle and reports
positive trace-distance excursions for the declared equatorial pair. It tests only the named
free-induction map. It does not test the production source-to-parameter fan-out, scheduled QEC
channel, reset/measurement instrument, syndrome record, or downstream estimator. A source timeline
alone has no CP-divisibility status, and a null means only `NULL_WITHIN_HORIZON`.

The current literature and execution boundaries are:

- `docs/simulator_validation/finite_rtn_free_induction_literature_closure_2026-07-15.md`
- `docs/simulator_validation/finite_rtn_free_induction_diagnostic_contract_2026-07-15.md`

The diagnostic schema is
`error_coupling_simulator.source.finite_rtn_free_induction_diagnostic.v1`. A result is current
evidence only when the script, contract, source owner, environment locks, and Git state are tracked,
clean, and hash-bound. Otherwise a rerun is implementation evidence only.

The mechanism-level RTN transition calculation uses cancellation-safe `expm1`; for example,
`_rtn_flip_probability(1e-20)` is positive instead of a false structural zero. Public
`RTNSource(gamma_per_cycle=1e-20)` is not a positive-probability sampling example: it is rejected at
construction because its one-cycle autocorrelation rounds to the endpoint one. Within the public
sampling domain, ULP-level probability changes can still change an individual seeded RNG comparison,
so trajectories are not promised to remain bit-identical to pre-correction runs. The temporal-storm
correlation and fixed-marginal maps likewise use cancellation-safe `log1p`/`expm1`. Any hash-bound
finite-RTN oracle or diagnostic evidence must be regenerated under the current schema in Phase 6/7;
old artifacts are not compatibility references.

## Numerical gates

All values in this section are software gates, not physical error bars.

| Gate | Current value | Meaning |
|---|---:|---|
| General floating threshold | `NUMERICAL_ZERO=1e-12` | Round-off/conditioning threshold only; never structural probability mass, bits, indices, labels, counts, or exact algebraic zeros |
| Within-cycle leakage CPTP residual | `<1e-12` | Reject an invalid per-slice Kraus table |
| Four-slice composition residual | `<1e-12` | Same-model check that four project slices reproduce the full project channel on the declared input; not a physical-siting validation |
| Within-cycle codestate residual | `1e-10` | Numerical state-preparation check |
| Axis-1 dense channel infidelity | strict `1e-6`; gross `.1` | Strict dense-reference candidate versus restricted-execution no-op/wrong-generator tripwire |
| Axis-1 record TV | strict `1e-6`; gross `.2`; gross ceiling `.45`; confidence `.999` | Project-selected record comparison and finite-shot allowance |
| Axis-1 normalization | `1e-12` | Probability-sum invariant, not distinguishability |
| MCWF/MPS probability residual | `1e-12` | Execution normalization gate |
| MCWF first-order mass preflight | `.1` by default | State-independent fail-closed finite-step budget; disabling is allowed only for a declared convergence study |
| QT/MPS probability residual | `1e-8` | Restricted product-formula execution normalization gate |
| Qutrit leakage independent references | superoperator/unitary `2e-12`; independent route `1e-10` | Implementation comparison only |
| PEPS environment fidelity target | current test `1-1e-8` | Local rank-selection objective, not record accuracy |
| PEPS stabilizer entropy | reference `2.0`, tolerance `1e-4` | Entropy equality alone is insufficient: the strict-target run currently has zero rank-reducing writes, so the independent non-degeneracy gate remains RED |
| Finite-RTN formulation invariance | oracle agreement `1e-10`; monotonic controls `1e-12`; corruptions must differ by `>1e-8` | Diagnostic implementation gates only |

A numerical threshold, denominator guard, clipping operation, or expression equivalent to
`max(NUMERICAL_ZERO, probability)` does not authorize changing a physical probability law.
Structural zeros stay zero. A stable `expm1`, `log1p`, or log-domain computation must be reported as
a numerical operation, never as added probability mass.

## Manifest requirements

Before a claim-bearing run, freeze one row per value:

```text
parameter | semantic object | value | units | provenance kind
source DOI or dataset identifier | exact locator | device/protocol scope
transformation or calibration chain | compatibility assumptions
sweep/uncertainty | allowed claim | forbidden claim
```

The artifact must additionally bind:

- current schema and representability class;
- package distribution/version, package-tree SHA-256, and Git commit when available;
- exact input paths or identifiers plus content hashes;
- source implementation/import origin and relevant environment locks;
- complete run shape, seed, precision purpose/dtype, finite-step and resource settings;
- metric names, gate values, negative controls, and verdict;
- canonical JSON content hash and atomic publication status.

Current schema families include:

- `error_coupling_simulator.frontend.qutrit_leakage.v2`;
- `error_coupling_simulator.frontend.mcwf_qutrit_grover_leakage.v2`;
- `error_coupling_simulator.frontend.experiment_preset_provenance.v2`;
- `error_coupling_simulator.frontend.run_numerical_provenance.v2`;
- `error_coupling_simulator.source.timeline.v1`;
- `error_coupling_simulator.source.coupling_config.v2`;
- `error_coupling_simulator.source.coupled_process_params.v2`;
- `error_coupling_simulator.carrier.package_build_identity.v1`;
- `error_coupling_simulator.source.finite_rtn_free_induction_diagnostic.v1`.

Only the registered preset facade may bind `complete_for_registered_preset`; caller-supplied nested
dictionaries cannot self-promote. Manifests are copied to canonical JSON, value-checked against the
run specification, and digest-bound. Missing or inconsistent provenance fails closed to
`implementation_only`. An optimization artifact remains `screening_only`; a complex128 artifact is
only a candidate until its owning scientific gates pass. Unsupported schema versions are rejected;
there is no compatibility fallback.

## Primary value anchors

- Miao et al., “Overcoming leakage in quantum error correction,” *Nature Physics* 19 (2023),
  DOI `10.1038/s41567-023-02226-w`, Fig. 3c: approximate leakage-population source scale for that
  experiment, not a direct measurement of the declared channel's `leakage_rate`.
- McEwen et al., “Removing leakage-induced correlated errors in superconducting quantum error
  correction,” *Nature Communications* 12 (2021), DOI `10.1038/s41467-021-21982-y`, Supplementary
  Table S1: no-reset seepage scale for that protocol, not a fitted project `g_seep`.
- Wood and Gambetta, “Quantification and characterization of leakage errors,” *Physical Review A*
  97, 032306 (2018), DOI `10.1103/PhysRevA.97.032306`: Eq. (2) supplies the subspace transition-rate
  definitions; Eqs. (30)-(34), (57)-(58), and (61) locate the state/block coherence construction. The
  paper supplies neither the declared exchange/seepage/heating channel nor a current preset tuple.
