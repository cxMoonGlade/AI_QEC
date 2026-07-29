# Numerical provenance

This is the binding current-state ledger for values, defaults, numerical gates, and run manifests in
`error_coupling_simulator`. It describes what the installed source and current tests may support. A
specified noise process is a model; a default, citation, or passing software check does not make it a
calibrated device model.

A final preregistered-pending subsection freezes values and execution policy for work not yet owned by
installed source or current tests. Those rows are not current numerical evidence and cannot be used
as measured results before their explicit activation conditions are met.

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
| MCWF staged artifact integrity | `staged_artifact_set_policy=exact_regular_files_bound_by_st_dev_st_ino_st_mode_st_size_st_mtime_ns_st_ctime_ns_sha256`; `artifact_file_fsync_required_at_each_seal_checkpoint=true`; stage-directory fsync required; exact-set revalidation after stage fsync; published-set rechecks after rename and parent fsync; every corresponding `*_success_attested_in_bundle=false` | `interface-identity` and publication-integrity protocol | At every seal/revalidation checkpoint, required staged files are opened through the sealed stage fd with `O_NOFOLLOW|O_NONBLOCK`, must be regular, and are bound by `st_dev`, `st_ino`, `st_mode`, `st_size`, `st_mtime_ns`, `st_ctime_ns`, and a non-null 64-hex SHA-256; hashing and file fsync use that same open artifact fd. JSON evidence uses independently streamed canonical-payload expected hashes; `.b8` uses chunked expected hashes computed from the in-memory binary Record rows. The manifest is written last, fsynced, sealed, and included in the final exact whitelist. Only the two required evidence JSONs, the manifest, and declared nonzero-width `.b8` files are permitted; a missing file, symlink, substitution, added file, or evaluator-truth file fails closed. The still-open stage fd supports revalidation after stage fsync, immediately before rename, after rename, and after parent fsync. Those events occur after the manifest is sealed, so `artifact_file_fsync_success_attested_in_bundle`, `staging_directory_fsync_success_attested_in_bundle`, `staged_artifact_set_revalidation_success_attested_in_bundle`, `published_artifact_set_recheck_after_rename_success_attested_in_bundle`, and `published_artifact_set_recheck_after_parent_fsync_success_attested_in_bundle` remain false; the bundle does not self-attest them. |
| MCWF grouped Record publication/provenance | absolute lexical `out_dir`; pre-existing parent with a held `st_dev`/`st_ino`-sealed dirfd; actual-target-filesystem collision and success legs for `renameat2(..., RENAME_NOREPLACE)`; destination inode checks after rename and after parent fsync; build scope `disk_package_tree_matches_package_import_time_digest_at_validation_checkpoints`; source scope `disk_source_file_matches_module_import_time_digest_at_validation_checkpoints`; environment-lock scope `lock_hash_bound_only`; loaded CUDA runtime `not_attested` | `interface-identity` and durability protocol, not a scientific metric | Stage creation/removal, final rename, and parent fsync are parent-dirfd anchored; artifact I/O is stage-fd anchored. The checkpoint scopes assert equality to import-time disk digests only at validation checkpoints, not continuous immutability. Source provenance binds the resolved import origin and disk SHA-256 but explicitly does not attest the runtime Python code object or monkeypatches. Git provenance requires a full 40/64-hex `git rev-parse HEAD` and fails closed if unavailable or invalid. Required Torch/Quimb/SciPy distribution versions must be present. `torch.version.cuda` is recorded as the PyTorch build CUDA version; it is not relabeled as the loaded runtime. The manifest is written before the later fsync/revalidation/rename checks, so it remains `prepared_for_atomic_publication`, sets the corresponding success attestations and `claims_offline_durability_confirmation` false, and cannot self-prove those later steps. Successful writer return is the sole durability confirmation. If a no-replace wrapper moves the sealed stage and then raises, or any later post-rename check fails, the published directory is preserved and the exception propagates; only a still-owned unpublished private stage is eligible for identity-safe best-effort cleanup, whose failure cannot turn the publication failure into success. |
| MCWF grouped Record materialization | schema `error_coupling_simulator.frontend.mcwf_mps_record_sample_summary.v1`; `max_record_support_cells` independently caps the static support/layout cell estimate; `max_record_array_payload_bytes` defaults to `AXIS1_MCWF_MPS_RECORD_MAX_ARRAY_PAYLOAD_BYTES == 512 MiB` and caps `4 * N * (D + O)` bytes | `interface-identity` plus two `numerical-only` resource guards | For completed, measured MCWF Carrier evidence accepted for restricted execution, exact histogram counts are expanded once in canonical grouped support order into immutable detector/observable `RecordBatch` arrays and optional little-endian `.b8`; either detector-only or observable-only output is valid, no second sample is drawn, and original trajectory order is not claimed. The 4x quantity is only the incremental NumPy Record-array payload for preallocated `uint8` rows plus current `RecordBatch` validation/freezing temporaries; it excludes the resident Carrier, Python support/layout objects, canonical JSON hashing, array headers/allocator overhead, build/publication provenance, and whole-process RSS. Strict support order, each compiler-sealed X/Z XOR row, and canonical hashes are checked in streaming passes without aggregate projection or support-sized `np.repeat` buffers. A private same-call consistency binding rechecks direct-child, Carrier, policy, and Record-law hashes; it is not cryptographic authenticity or replay protection. The writer requires a fresh destination under a pre-existing parent. Before MCWF it seals the parent's `st_dev`/`st_ino`, environment-lock path/hash, freshly recomputed build/package-tree/Git identity, source hash, and environment/runtime identity; a sacrificial probe on the actual target filesystem must pass both collision-preservation and successful Linux `renameat2(..., RENAME_NOREPLACE)` cases. The complete seal is checked after MCWF and again after staging fsync immediately before the final freshness check and atomic rename. It persists the exact evaluator-truth-free `axis1_mcwf_mps_carrier_execution.json`; its artifact entry binds file SHA-256, schema, internal content hash, `contains_carrier_program_summary=true`, and explicit restricted-policy, Record-execution, and Carrier-program-summary locators. It separately persists the complete sealed, evaluator-truth-free `axis1_mcwf_mps_carrier_program.json`; that artifact entry binds file SHA-256, schema, internal content hash, and `contains_complete_sealed_program=true`, while `metric_and_gate_policy.program_evidence_locator` points to that file. The public standalone bundle supports offline inspection of reported policy metric values, recomputation of gate/confidence-interval and acceptance algebra, and verification of persisted hashes/locators. It omits the evaluator-only declared-basis level law and dense-oracle distribution, so it cannot independently regenerate the multilevel declared-basis TV from raw distributions or fully reproduce the evaluator verdict; the complete direct child must not be persisted. The manifest records run seed/dtypes and the sealed build/source/environment/runtime identities. Files/stage are fsynced and the manifest is written last, but it is only `prepared_for_atomic_publication`: it records the target-FS probe and first post-execution seal revalidation and explicitly does not attest the second pre-rename revalidation, rename, or parent-fsync success. Successful writer return is the sole durability confirmation. A post-rename parent-fsync failure preserves the published directory and raises without path cleanup; only an unpublished stage is removed. Missing parent/lock, failed target-FS probe, sealed-identity drift, no-measurement, blocked, double-zero-width, noncanonical, over-budget, incomplete, or unaccepted input fails closed. Status is preserved; this is not a DEM, decoder, faithfulness, calibration, production, or complete-QEC-Record gate. |
| Uncapped nonlocal MPS mechanics | at most 5 support sites, support Hilbert dimension at most `256`, dense operator at most `65,536` elements; dense-to-MPO and MPS/MPO cutoffs exactly `0.0` | `numerical-only` resource cap and algorithm identity | Fails before dense gate allocation outside the envelope. The caps limit allocation only; they are not accuracy, truncation, state-distance, Record-TV, LER, or faithfulness thresholds |
| QT/MPS execution | `max_branches=4096`, one microstep, first-order product formula, no bond/discarded-weight gate unless supplied, dense reference requested | `convenience-default` | Restricted verification path, not universal joint-generator evidence. A complete capped run with actual loss is rejected unless both local worst-cut and path-total gates are explicit and pass |
| QT/MPS Record materialization cap | `max_record_materialization_outcomes=4096` | `numerical-only` resource cap | Limits explicit construction of the complete Record domain and fails before CUDA acquisition or Record allocation when exceeded. It is not a scientific gate, accuracy threshold, Record-fidelity bound, or truncation claim |
| Restricted MPS Record layout and schemas | `axis1_schedule_record_layout.v1`; direct QT/MPS v6; direct MCWF/MPS v8; MCWF evaluator diagnostics v2 and acceptance policy v7; MCWF frozen-dynamics reference packet v2; QT aggregate/resource manifests v4; Carrier wrapper/auto route v5; routing decision v3 | `interface-identity` | Immutable keys, targets, X/Z bases, per-target reset masks, slices, and XOR columns are parsed from the compiler-sealed schedule before execution. Direct MCWF, Carrier, auto-routing, and certification rebind the ordered Record identity; evaluator-only v2 distinguishes declared-basis eigenlabels from computational local levels. The MCWF hard cut removes the false no-measurement linear-channel identity and names the symmetric-Hamiltonian/first-order-collapse option honestly; the old order name and all earlier schemas are rejected. Current versions also bind sampled support, frozen-dynamics/source/program/artifact provenance, transitive child authentication, exact-shape resource evidence, and fail-closed verdict semantics. These are implementation/schema facts, not sampled values, calibration, or independent oracle truth; no earlier-version fallback is retained |
| MCWF certifier-local operator guard | 51 Hamiltonian families; seven collapse families; `max(abs(O_production-O_reference)) <= NUMERICAL_ZERO == 1e-12` | `numerical-only` floating comparison over an `implementation-definition` reference | The NumPy/Pauli reference module imports no production frontend, Torch, Stim, private family table, grouping helper, or matrix-log path. It constructs leaked-sector padding and forbidden transitions as exact zeros and compares every present term, including zero coefficients, before dense acceptance. Every reference-declared structural-zero entry is required to be exactly zero in the production tensor. Missing family coverage, wrong arity/shape, non-finite values, and disagreement fail closed. The threshold accommodates floating evaluation of analytically equivalent matrices; it is not a physical error tolerance, source-to-coefficient validation, or hardware bound. `CORR_RELAX` uses full declared-dimension identities in its two-site collective-lowering reference, but currently has only internal sealed-Carrier-program support and no public source/schedule compiler lowering. |
| MCWF frozen dynamics artifact gate | term tolerance `NUMERICAL_ZERO == 1e-12`; group-gate tolerance `1000 * NUMERICAL_ZERO == 1e-9`; exact structural zeros; `mcwf_dynamics_artifact_reference_certification.v2` | `numerical-only` cross-backend comparison plus `interface-identity`; non-metric class-(a/c) gate | Production Hamiltonian/collapse tensors are built once, group gates are derived from that same frozen inventory, and the mass preflight and trajectory consume it without rebuilding. The certifier independently reconstructs the connected grouping and uses SciPy `expm`; the larger group tolerance covers the observed Torch-CUDA/SciPy matrix-exponential floor without relaxing term matrices or structural zeros. The packet binds complete substep/term/group coverage, local dimensions, microstep/order controls including the honest symmetric-Hamiltonian/first-order-collapse identity, Carrier-program and artifact hashes, current reference/certifier/carrier-operator hashes, and the transitive `axis1_ideal_controls.py` and `axis1_selection.py` hashes, plus post-execution content integrity. Its artifact hash is independently recomputed from the inspected matrices and metadata, not trusted because a caller supplied 64 hexadecimal characters. Direct policy and Carrier require a current passing packet; an accepted seeded auto route additionally replays direct MCWF from sealed inputs and exact-binds the resulting direct hash, Record summary, and policy. These values are not state/Record error bounds, mechanism literature closure, hardware calibration, or production/scalability evidence; the literature source-closure reset remains OPEN. |
| MCWF finite-step X/Z Record recurrence | frozen `s=0.25` fixture; `m=(10,20,40,80)`; joint/Z TV `(0.0234098250,0.0118596628,0.0059679715,0.0029934385)`; X-after TV `(0.0102758610,0.0050882834,0.0025317938,0.0012628171)`; doubling-ratio band `[1.85,2.15]`; final caps `0.0031` and `0.0013`; public GPU `m=40`, `n=2048`, seed `19073`; one-sample radii joint `0.0640322086`, Z/X `0.0395189879` at `alpha=0.01/3` | `numerical-only` class-(c), fixture-bound Record evidence | A hand-written scalar recurrence imports no production-private execution helper and is checked against the neutral continuous-time law. The deterministic grid must monotonically approach it and approximately halve its bias; the sampled public manifest is compared to the finite-step law, not directly promoted to a continuous channel. Exact final-Z support and ordered `[X,Z,X,Z]` metadata remain structural gates. The `0.5 -> 1` no-jump and `dt/m -> dt` recurrence corruptions demonstrate test power, while the semantic mutation service must independently kill the corresponding production mutants. This row establishes neither global convergence order, a linear Choi/CPTP map, qutrit/leakage behavior, calibration, scalability, nor production readiness. |
| Neutral MCWF X/Z differential fixture family | three byte-pinned two-qubit fixtures F1 T1, F2 number dephasing, and F3 thermal down/up; `n=2048` per sampled leg; overall `alpha=0.01`; 15 registered statistics use `alpha_j=alpha/15`; joint alphabet `k=16`, directed marginal alphabet `k=2`; one-sample radii `0.0670302388436366` and `0.04421175841273293`; two-sample joint radius `0.1365617560712202` | `numerical-only` class-(c) finite-sample external differential plus exact-structure sanity checks | Each fixture fixes ordered bases `[X,Z,X,Z]`, reset mask `[true,true,false,false]`, and reset targets `X -> |+>`, `Z -> |0>`. Per fixture the registry contains project-vs-dense joint and two directed marginals, QuTiP-vs-dense joint, and QuTiP-vs-project joint. The independent dense worker imports no simulator implementation, hand-builds the 4x4 operators and 16x16 Lindblad superoperator, and preserves analytic structural-zero cells exactly; the isolated QuTiP v3 worker binds pristine commit/tree, selected installed-source equality, installed-distribution identity, explicit solver controls, and exact conformance to the 36-package Linux-64 environment lock. The project leg uses public GPU direct and Carrier APIs and requires exact equality between their emitted Record summaries. F1 reversed relaxation, F2 missing number-operator factor, and F3 removed/swapped/doubled/wrong-target jump corruptions must fail; a unit-modulus collapse phase is an inert control. The family does not establish qutrit/leakage behavior, trajectory coupling, a complete multi-round QEC Record, scaling, calibration, or production readiness. |
| MCWF dense binary-readout oracle | explicit binary support at most `4096`; `bonferroni_two_component_per_bin_two_sided_hoeffding_capped_at_gross_tv_ceiling` | `numerical-only` resource cap plus statistical procedure identity | The cap limits certifier-local marginalization of the dense declared-basis label law through the hand-typed leaked-readout kernel and fails closed when exceeded. It is not an accuracy threshold or full-Record claim. The confidence construction covers both label and emitted-binary TV families without assuming their empirical estimates are independent |
| Restricted MPS exact-branch resource bound | `static_branch_count_upper_bound_after_substep`, exactly recomputed from the authenticated program and `max_branches` | `numerical-only` resource bound | Not an observed execution branch count, Record statistic, hidden Kraus-history claim, or faithfulness measurement. The obsolete `branch_count_after_substep` field is rejected |
| Restricted MPS engineering benchmark | smoke: one warmup plus three measured repetitions; full: two warmups plus nine measured repetitions; five fresh, serial CUDA workers | `engineering-performance-only` | Measures complete public-manifest latency. Peak statistics are reset before each invocation, but the reported CUDA value is the absolute allocator peak and includes allocations retained after warmup; it is not an invocation delta. RSS is cumulative process high-water within each fresh workload worker. Catalog-matched `rejected` or `unavailable` diagnostic workloads can pass the instrument; this is not a safe-pruning, production-error-bound, or Record-faithfulness gate |
| PEPO solver | complex128; NTU at most 20 sweeps, relative stop and pseudoinverse tolerance `1e-12`; one-site fit at most 64 iterations | `numerical-only` | Solver controls only; they do not certify positivity or record faithfulness |
| PEPO negativity witness default floor | `4.8e-4` | `project-design` numerical witness | Default witness scale, not a physical negativity bound or record certificate |
| PEPS resource guards | pre-cut cap `W_max=160`, abort when a grown bond exceeds `D_abort=40` | `numerical-only` | Orderly resource limits, never a claim that the retained state or record is accurate |
| PEPS environment truncation | current test uses `eps_fid=1e-8`; 20 ALS sweeps; optimization floor `1e-9`; instability guards `1e-12` and `1e-6`; local rank threshold `NUMERICAL_ZERO=1e-12` | `numerical-only` | Local environment objective only. The B1_3 known-answer cut has stored dimension 12 and independent structural rank 4; production FET preserves the feasible endpoint QR/SVD candidate and accepts rank at most 4 while reconstructing the local map and gamma objective to the registered tolerance. Gauge preparation is regression-gated not to mutate the verdict-driving gamma tensor. Focused owner tests pass, but clean-checkpoint replay, fresh aggregate acceptance, and full-record scientific closure remain pending; no PEPS faithfulness claim follows from this local repair. |


### Preregistered pending GCAPEPS n=8, r=3 differential values

The rows in this subsection are a pre-execution freeze, not a description of current installed
owners or observed output. They activate only after the named scripts and independent tests exist,
are committed and clean, and the target supervisor runs under the frozen identities. No row
registers a canonical Carrier, detector/observable Record, production service, generic PEPS
faithfulness statement, or scalable efficiency result.

| Pending owner/object | Frozen values | Kind | Allowed and forbidden interpretation |
|---|---|---|---|
| Neutral differential fixture and precision | `n=8`, active coherent rank `r=3`, `2x4` open graph, q0-most-significant-bit length-256 vectors; residual weights `(0.8,0.48,0.36)` with the preregistered signed Pauli words; all PEPS/PEPO tensors and complete vectors forced to NumPy `complex128`; `max_bond=None`, `cutoff=0.0`, no compression or truncation | `project-design` | Synthetic one-input state-action stress fixture comparing two candidate implementations. It is not workload representativeness, calibrated noise, a finite-bond approximation, operator equality, or scaling evidence. |
| Candidate and anchor agreement bands | Formula family registered in the pending section of `docs/METRICS.md`; `d_rel <= 2e-11`, `d_norm <= 2e-11`, `1-F <= 1e-12`, and `fidelity_roundoff_correction=max(0,F_raw-1) <= 1e-12`; `d_inf` and `d2` always emitted but report-only | `numerical-only` | Complex128 fixture agreement rule, not a physical error bar or generic correctness certificate. Clamping is allowed only after the explicit roundoff gate passes. |
| NumPy exact-small anchor role | Closed-form four-amplitude residual input, literal bitwise residual and signed-physical Pauli action, and independently written literal complex128 preparation/Clifford replay; forbidden imports are Quimb, Stim, SDIM, and GCAPEPS; the anchor is untimed and contributes no RSS or efficiency sample | `project-design` in an `independent-reference` role | May qualify only the frozen `n=8` one-input state action and localize a candidate mismatch. It is not physical truth, generic PEPS truth, all-input operator equality, a Record-law oracle, or a performance lane. |
| Candidate timing population | A=`plain`, B=`gcapeps`; one discarded fresh-process warmup per lane in order `A,B`; six measured fresh workers per lane in strict serial `A,B,B,A` order repeated three times; every child fully reaped; retain all integer-nanosecond samples and report median/MAD | `convenience-default` engineering protocol | Bounded comparison protocol only. It is not a benchmark standard, statistical confidence interval, portable rate, or asymptotic result. The anchor is excluded from this population and every efficiency ratio. |
| Timed update definitions | `plain_update=physical_clifford+pepo_build+pepo_apply`; `gcapeps_update=tableau_prefix+coherent_ir_build+carrier_apply`; complete-vector materialization and GC literal c128 lift are separate; GC reports `includes_exact_small_internal_dense_and_norm_checks=true` | `numerical-only` instrumentation identity | Compares the frozen end-to-end candidate update paths, not pure kernels. `R_update=median(plain_update)/median(gcapeps_update)` and `R_RSS=median(RSS_plain)/median(RSS_gcapeps)` are interpretable only when candidate differential, anchor qualification, and SDIM-frame corroboration all pass. `R_update>1` is a report-only directional hypothesis, never an acceptance gate. |
| Fresh-worker resource and isolation envelope | exact common CPU is the minimum allowed supervisor affinity; OMP/OpenBLAS/MKL/NumExpr/BLIS threads each `1`; empty `CUDA_VISIBLE_DEVICES`; `PYTHONNOUSERSITE=1`, `PYTHONDONTWRITEBYTECODE=1`, `PYTHONHASHSEED=0`, `TZ=UTC`; systemd 255 user manager plus cgroup v2; `MemoryMax=8 GiB`, `MemorySwapMax=0`, `RuntimeMaxSec=300 s`, `TasksMax=32` | `numerical-only` | Fail-closed execution envelope, not a speed or memory claim. Missing affinity/cgroup capability makes efficiency `INELIGIBLE` rather than relaxing a cap. Logical tensor bytes, `ru_maxrss` with platform units, and cgroup `MemoryPeak` remain distinct. |
| Main Quimb/GCAPEPS source and environment identity | fork `external/forks/quimb-gcapeps`; commit `6fbbf74cd36686ed30a4d8865697ce46e47056c1`; tree `ffdfdf421fbe4d9674c2c88029710042fd18ae14`; Pixi `0.72.2` executable SHA-256 `2f301e44ac4caa9e137d505e5d0606fd029182d4df6f9e3add80bc077effea87`; detached `testpymid` environment, Python 3.13; `pyproject.toml` SHA-256 `c8b48e06ee8595be41cc5dff6d4f8e768a9064d5a0f84efaec5ff12a7e8aa344`; `pixi.lock` SHA-256 `854da99b417c69dbdca4118c2545656470ad4e0f276a606b1b8c3082f795db35`; Stim `1.16.0`; `PYTHONPATH` forbidden | `interface-identity` | The development checkout is not executed; a fresh temporary checkout of this commit must be ignored-inclusive pristine, and `detached-environments` is set to an absolute private path outside it. Binds the exact candidate source/environment scope. It does not by itself attest installed-package conformance or a generally reproducible environment, and it does not make ordinary Quimb ground truth. Both candidates use the same frozen fork commit; the plain worker must not import `quimb.experimental.gcapeps`. |
| SDIM frame-only corroboration identity | environment file `external/forks/quimb-gcapeps/environment-gcapeps-sdim.yml`, SHA-256 `64236e0cb6dc87a90f116dbebb8ee8a73882dc41d00619af8b7d3ccc35de3431`; Python `3.12.13`, Stim `1.16.0`, SDIM `1.3.3`; runtime records installed-distribution state, import origins, source hashes, and environment-file hash | `interface-identity` | Qubit signed-frame corroboration only. The YAML is a bootstrap, not a transitive lock or wheel-byte attestation. SDIM never owns PEPS, complete vectors, fidelity, the pair or anchor verdict, qutrit behavior, or a numeric efficiency ratio. A non-PASS SDIM verdict makes state-action qualification and efficiency interpretation ineligible. |
| Pending worker/comparator/publication surface | planned scripts `emit_gcapeps_n8_r3_fixture.py`, `plain_quimb_n8_r3_worker.py`, `gcapeps_n8_r3_dense_anchor.py`, `gcapeps_n8_r3_worker.py`, `compare_gcapeps_n8_r3_differential.py`, `gcapeps_n8_r3_sdim_worker.py`, `run_gcapeps_n8_r3_controls.py`, and `run_gcapeps_n8_r3_differential.py`; planned test `tests/test_external_gcapeps_n8_r3_differential.py`; terminal schema `error_coupling_simulator.external.gcapeps_n8_r3_candidate_state_action_differential.v1` | `interface-identity` pending activation | These are frozen planned paths, not current owners. A path becomes current only after implementation, independent tests, `tests/CODEBOOK.md`, service-catalog synchronization, committed clean provenance, controls, and publication checks all exist and pass. |
| Runtime timing and memory observations | no preregistered measured value; later payload may contain raw wall nanoseconds, process user/system time, platform-qualified `ru_maxrss`, cgroup `MemoryPeak`, bond/tensor counts, logical bytes, and median/MAD/ratios | `engineering-performance-only` when actually observed | Describes only the frozen fixture, machine, lowering, fork commit, and process envelope. No value is current before a qualifying target run, and no observed resource number proves accuracy, contraction complexity, or general efficiency. |

### Current bounded GCAPEPS bridge forced-truncation values

These values were frozen before implementation in
`docs/simulator_validation/GCAPEPS_NATIVE_FORCED_TRUNCATION_PREREG_2026-07-29.md`.
The held-out run is reported in
`docs/simulator_validation/GCAPEPS_NATIVE_FORCED_TRUNCATION_RESULT_2026-07-29.md`
with verdict `PASS_BOUNDED_BRIDGE_TRANSIENT_TRUNCATION`.

| Object | Registered and observed value | Kind | Boundary |
|---|---|---|---|
| Formal held-out fixture | `n=2`, edge `(0,1)`, input coefficients `(12/13,5/13)`, \(P=ZZ\), \(\theta=\pi/5\), q0-most-significant length-four vectors; executed without substituting the excluded pilot | `project-design` | The earlier `(4/5,3/5,pi/3)` API pilot remains excluded from formal evidence. |
| Numerical execution | NumPy `complex128` states/gates/PEPO tensors, `float64` singular values, `renorm=False`, `gauge_smudge=0.0`, `cutoff_mode=rel`, full SVD, exact contraction optimizer `greedy`; all dtype and finite-value gates passed | `numerical-only` | This is the exact-small registered execution, not a production or scalable contraction environment. |
| Cap-only target | native `CX(0,1), RZ_1(pi/5), CX(0,1)`, `max_bond=1`, `cutoff=0.0`; the first CNOT had the positive discarded squared tail `25/169` | class-(a) finite-dimensional identity plus class-(c) observed local ledger | The ledger localizes this registered cause. It is not a global truncation-error certificate. |
| Cap-only complete-state result | pre-cut singular values `(12/13,5/13)`, gap `7/13`, discarded squared weight `25/169`, raw norm `12/13`, norm squared `144/169`, `d2=d_inf=5/13`, relative norm error `1/13`, normalized squared fidelity `144/169`; every registered value passed its `1e-12` band | class-(a) finite-dimensional identity with class-(c) software observation | Exact only for the registered bridge fixture; not a loopy-PEPS or accumulated-error theorem. |
| No-loss controls | exact-tree, native uncapped `None/0.0`, native high-cap `2/0.0`, and direct literal \(U_{ZZ}\) at `1/0.0` discarded no positive weight and matched the dense anchor within `3.8e-16` over complete vectors; reconstructed full-operator `d_inf=1.25e-16` | `numerical-only` qualification | These controls qualify the bounded comparison; they do not make either Quimb path generic PEPS truth. |
| Cutoff-cause controls | no-cap relative cutoff `0.4` was inert; no-cap relative cutoff `0.5` produced the same complete vector as the cap-only target while naming cutoff rather than cap as the loss cause | class-(a) prediction plus class-(c) ledger gate | Equal final vectors do not establish equal cause; configuration and spectrum are both bound. |
| Exact final-state structure | the exact final state had rank one although the native path passed through the lossy first-CNOT split | class-(a) finite-dimensional identity corroborated numerically | Supports transient path dependence only, not a final-state bond lower bound or a general truncation statement. |
| Source and result identity | parent commit `1e9517af31f83d174bcbdf656c1955f12227b605`, tree `17c17eb549d5f091263e7deaa86476d90420174b`; fork commit `e6cbe016f336843925e01a559db26f209fa9d37b`, tree `854ff4d5ef692497f017a57250cf8f440e47110f`; raw temporary JSON SHA-256 `55d428ceebb38aba91e1fbeb2e2a6d6f1b2f5da944534179ef2f583e4fa65ac7`; canonical content hash `73ca030b410b0bf60f6fc6a1e599064ec21a5c024c8ecfd28955e8f7ad934a58` | `interface-identity` and numerical provenance | Non-formal tests still use only the excluded pilot or synthetic ledgers and do not execute the formal target. Existing n8/d357 artifacts stay pinned to fork commit `6fbbf74cd36686ed30a4d8865697ce46e47056c1` and are not rebound. |
| Claim boundary | no timing was collected; no complete Record, multiround, qutrit/SDIM, leakage, loopy 2x2, generic PEPS, global truncation-error, or general efficiency result was tested | `epistemic-boundary` | The loopy 2x2 extension remains P1. |

For the MCWF grouped writer, "unpublished-stage cleanup" means an ownership-bounded best-effort
attempt, not a success or durability assertion. Cleanup errors are suppressed in favor of the original
publication failure and may leave the private stage behind; a published destination is never path-cleaned.

The final MCWF publication return sequence is also interface identity, not scientific evidence. After
parent fsync and the final full artifact-set recheck, it requires
`sealed_identity_revalidation_required_after_final_artifact_recheck=true`, performs a metadata-only
exact-set recheck, then requires
`published_destination_identity_recheck_after_final_artifact_recheck_required=true` before checking the
path-visible parent. Both corresponding `*_success_attested_in_bundle` fields are false, as is
`sealed_identity_revalidation_success_attested_in_bundle`; the prepared bundle cannot self-attest these
steps or durability.

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
- `error_coupling_simulator.frontend.mcwf_mps_record_sample_summary.v1`;
- `error_coupling_simulator.source.timeline.v1`;
- `error_coupling_simulator.source.coupling_config.v2`;
- `error_coupling_simulator.source.coupled_process_params.v2`;
- `error_coupling_simulator.carrier.package_build_identity.v1`;
- `error_coupling_simulator.source.finite_rtn_free_induction_diagnostic.v1`.
- `error_coupling_simulator.external_baseline.qutip_mcwf_xz_record.v3`;
- `error_coupling_simulator.external_baseline.mcwf_xz_dense_record.v1`;
- `error_coupling_simulator.external_baseline.mcwf_xz_worker_envelope.v1`;
- `error_coupling_simulator.external_baseline.mcwf_xz_fixture_comparison.v1`;
- `error_coupling_simulator.external_baseline.mcwf_xz_fixture_family_comparison.v1`.

The QuTiP worker v3 and dense worker v1 reports are recursively exact-field validated; fixture,
runtime isolation, selected-source identities, solver controls, Record laws, reset residuals, and
verdicts are recomputed by the family comparator. The QuTiP report binds the pristine commit/tree and
installed distribution to `baseline-environment-qutip-linux-64.lock.json`, whose 36 exact conda URLs
carry package hashes; live explicit-package conformance and the source-installed QuTiP identity must
both pass. The worker JSON parser rejects duplicate keys, literal and overflow-derived non-finite
values, and coercible non-integer Record bits/counts. Transport stdout/stderr/return code and a
construction-time raw JSON byte hash/size live in a separate v1 envelope; those exact bytes must
decode to the embedded hash-authenticated worker payload. Worker and family targets use stale-safe
file-plus-directory-`fsync` publication, and a publishable family report requires a clean Git
checkpoint.

The family v1 report binds all three fixture and registry hashes, 15 scored statistics, direct/Carrier
program and Record identities, selected and transitive project sources, environment locks, runtime/GPU
identity, isolated-worker envelopes, corruption contracts, and a canonical outer content hash. F1
also retains the deterministic `m=10,20,40,80` recurrence and public `m=40` sample gate. This is a
reproducible isolated QuTiP-environment claim for the exact pinned Linux-64 lock, not a claim that the
three fixtures cover the full simulator environment or complete QEC behavior.

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
