# L3 WORK-LIST — `error_coupling_simulator` release-package unit inventory

Read-only inventory of every public unit in the releasable package
`src/error_coupling_simulator/`, feeding **Stage D** of the full-coverage program
(`docs/twin_validation/wave2_6_unit_test_contract.md` §12.3 / §12.4). It classifies
each public unit **CPU-PURE** (full L0+L1+L2 treatment) vs **GPU/QUIMB-BOUND**
(structural coverage + hand KILLER + existing independent-referee equivalence gate)
vs **MIXED** (split: CPU core gets L0+L1, GPU tail gets the lighter treatment), records
the L1 invariants, the §12.1 DEFENSIVE-ASSERT surface, and the existing test coverage,
and proposes the Stage-D batch order.

- **Generated:** read-only sweep, 2026-07-07. Git HEAD at sweep: `ac0f9dc`.
- **Unit definition:** a *public unit* = a module-level `def` not starting with `_`,
  **plus** every public method of a public/dataclass class (`_private` methods skipped
  unless the code map / a docstring flags them load-bearing, e.g. `experiments._dataset_files`).
  Enums and pure dataclass *shells* (no methods) are counted at the module level as their
  methods (`__post_init__` validation is counted as the class's testable unit). Counts are
  AST-authoritative (`ast` walk over the package tree).
- **Coverage baseline:** the repo `.coverage` (Wave-2 run: `test_shotset_records` +
  `test_frontend_experiments` + `test_gate_soundness_matrix` + `test_support_selftest`),
  regenerated to a `coverage json` restricted to `*/error_coupling_simulator/*` under the
  `aiqec` env. **The Wave-2 run imported only 59 of the 88 package files** — the other
  **24 non-init modules were never imported and sit at a TRUE 0%** (they are absent from the
  `.coverage` DB, not merely low). Per-module `cov%` below is the measured value or `0%`
  for the absent set. The package TOTAL from `coverage report` over the in-DB files is
  **18%**; counting the 24 absent modules the honest package figure is ≈**18%** (they are
  small-to-mid modules, so they do not move the weighted total far, but they are the
  single biggest *structural* gap — see §C).

---

## (a) Summary table — per-subpackage roll-up

| Subpackage | modules | public units | CPU-PURE | GPU/QUIMB-BOUND | MIXED | current cov% (range) | already-tested (has ANY test) |
|---|---:|---:|---:|---:|---:|---|---:|
| `(root)` numerics.py | 1 | 2 | 2 | 0 | 0 | 71% | 2 (implicit) |
| `carrier/` | 4 | 62 | 36 | 23 | 3 | 6–36% | ~47 |
| `carrier/exact/` | 2 | 47 | 4 | 43 | 0 | 16–19% | ~45 |
| `carrier/kernels/` | 2 | 10 | 4 | 6 | 0 | **0%** | 0 (indirect) |
| `certify/` | 3 | 25 | 22 | 0 | 3 | **DONE** L0 100/100 · L2 0.945 | test_certify_core_units (D4) + test_certify |
| `certify/anchors/` | 4 | 18 | 12 | 4 | 2 | **DONE** L0 100/100 · L2 0.927 (1 gpu oos) | test_certify_anchors_units (D5) + test_certify |
| `frontend/` | 46 | 320 | ~215 | ~55 | ~50 | 0–84% | ~120 |
| `mechanisms/` | 5 | 43 | 32 | 7 | 4 | 0–71% | ~30 |
| `quantum_bath/` | 7 | 44 | 44 | 0 | 0 | **0%** | ~20 (test_quantum_bath) |
| `source/` | 2 | 46 | 46 | 0 | 0 | 17–32% | ~35 |
| `teachers/` | 1 | 18 | 12 | 1 | 5 | **0%** (not imported in Wave-2 run) | ~15 (test_coupled_cycle_teacher exists) |
| **TOTAL** | **74** | **635** | **~429** | **~89** | **~67** | **~18%** | **~340** |

Notes on the split (the ~ reflects a handful of genuinely-ambiguous units listed in §D):
- **CPU-PURE ≈ 68% of the package.** The package is overwhelmingly plumbing: numpy/math
  Kraus/unitary builders, closed-form source maths, dict record-statistics, dataclass IR,
  validation guards, schema/manifest builders, Stim/PyMatching wiring. All of this gets the
  full **L0 (100% stmt+branch) + L1 (Hypothesis property) + L2 (mutation)** treatment.
- **GPU/QUIMB-BOUND ≈ 14%.** Torch-cuda DM/superop algebra (`cptp_channel`,
  `joint_lindbladian`, `qutrit_dm`, `circuit_sim`), CUDA kernel loaders, MCWF/QT-MPS/qutip
  executors, the DM-oracle anchor. These keep **structural coverage + a hand KILLER + their
  existing independent-referee equivalence gate** (no Hypothesis, no mutation).
- **MIXED ≈ 11%.** Evidence/manifest seams that CPU-validate + route, then call a GPU tail;
  facades; `leak_slice_table` (CPU TypeError route + GPU builder). **Split**: the CPU core
  (validation, routing, TypeError, dataclass) → L0+L1; the GPU tail → the lighter treatment.
- **"already-tested"** = the unit name appears in at least one `tests/` file (a gate,
  equivalence, or integration test). It is NOT the same as "has an isolated L0 unit test" —
  most are covered only by an integration/equivalence gate that passes valid inputs, so their
  exception surfaces are dark (exactly the Wave-2 finding, now generalized to the package).

---

## (b) Per-module unit tables

Legend for **class**: `C`=CPU-PURE, `G`=GPU/QUIMB-BOUND, `M`=MIXED. **DA** = carries an
assert-never-fires / raise-guard (§12.1 DEFENSIVE-ASSERT RULE applies: extract `_assert_*`,
trip it in a meta-test, prove the legit path via the L1 property, register the branch as a
`defensive_assert` exemption). **VAL** = the module carries *validation raises* that SHOULD
fire on bad input (these become the L1 "generated out-of-range value raises" property, not
exemptions).

### `numerics.py` — cov 71% · 2 units (2 C)
| unit | contract | class | invariants | DA | existing test |
|---|---|---|---|---|---|
| `positive_floor` | floor a float away from exact 0 | C | idempotence on ≥floor; output ≥ NUMERICAL_ZERO | no | implicit (imported by coupling/channels) |
| `probability_floor` | floor a prob away from 0, cap at 1 | C | output ∈ [floor, 1]; normalization | no | implicit |

### `carrier/channels.py` — cov 20% · 32 units (31 C, 2 M via scipy.expm) — **numpy-only, no torch**
Confirmed CPU-pure: imports numpy only (0 `device=`, no torch tensor construction).
| unit | contract | class | invariants | DA | existing test |
|---|---|---|---|---|---|
| `MechanismSpec.audit_dict` | serialize spec → audit dict | C | manifest round-trip | no | test_physical_channels |
| `canonical_single_qubit_axis` | normalize axis string → {rx,ry,rz} | C | idempotence | VAL | test_physical_channels |
| `mechanism_operation_axis` / `mechanism_error_axis` | extract/validate op & error axis | C | determinism | VAL | test_physical_channels |
| `mechanism_definition_contract` | build M11/M13/M14 definition dict | C | contract completeness | VAL | test_physical_channels |
| `mechanism_channel` | dispatch 34 mech IDs → channel | C | Kraus→CPTP; completeness | VAL | test_physical_channels |
| `rzz_unitary`,`rx_unitary`,`ry_unitary`,`rz_unitary`,`rxx_unitary`,`ryy_unitary`,`rxx_ryy_unitary`,`single_axis_rotation`,`two_pauli_rotation`,`controlled_phase_error_unitary` | closed-form rotation unitaries | C | **unitarity** (U†U=I); diagonal ones Hermitian-phase | no | test_physical_channels (most) |
| `pauli_stochastic_kraus`,`amplitude_damping_kraus`,`phase_damping_kraus`,`phase_damping_canonical_kraus`,`thermal_relaxation_kraus`,`thermal_excitation_kraus`,`reset_to_state_kraus`,`leakage_relaxation_surrogate_kraus`,`custom_non_pauli_kraus`,`two_qubit_depolarizing_kraus`,`correlated_relaxation_kraus`,`weak_type4_mixing_kraus`,`drifted_axis_mixture_kraus` | Kraus channel builders | C | **CPTP** (ΣK†K=I); prob floor | VAL (prob/T2≤2T1/target∈{0,1}) | test_physical_channels (most; ~6 untested) |
| `readout_bias_matrix` | 2×2 confusion matrix | C | row-stochastic (rows sum 1) | no | test_physical_channels |
| `leakage_channel_super` | WG leakage superop via `scipy.linalg.expm` | M (expm) | CPTP of exp(L) | VAL (T1,T2>0) | test_physical_channels |
| `leakage_kraus` | WG qutrit leakage Kraus via Choi factorization | M (expm+eigh) | CPTP; variable rank | no | test_physical_channels |

### `carrier/cptp_channel.py` — cov 36% · 10 units (1 C, 9 G) — torch complex128
| unit | contract | class | invariants | DA | existing test |
|---|---|---|---|---|---|
| `StinespringChannel.parameters` | return [real,imag] generator params | C | identity/determinism | no | — |
| `hermitianize`,`apply_kraus`,`measurement_probabilities_z`,`tp_residual`,`choi_matrix`,`single_qubit_paulis`,`pauli_transfer_matrix`,`StinespringChannel.random`,`StinespringChannel.kraus` | torch DM/Kraus/Choi/PTM algebra | G | CPTP-by-construction, trace-1, Hermitian, PSD-Choi | yes (device check, clamp) | test_kernels_fused_kraus, test_diff_cptp_channel_recovery (7) |

### `carrier/joint_lindbladian.py` — cov 6% · 14 units (3 C, 11 G) — torch.linalg matrix_exp/eigh
| unit | contract | class | invariants | DA | existing test |
|---|---|---|---|---|---|
| `operator_support` | qubits an op acts on non-trivially | G (torch tol scan) | sorted-tuple | no | test_joint_lindbladian |
| `restrict_operator_to_component` | restrict op to a component subspace | G | exact restriction; permutation-inv | VAL (residual raise) | test_joint_lindbladian |
| `liouvillian_superop`,`superop_to_kraus`,`assemble_substep_channel`,`assemble_substep_channels_batched`,`assemble_substep_channel_factored`,`assemble_substep_channels_factored_batched`,`liouvillian_commutator_norm`,`composed_substep_channel`,`composed_vs_joint_superop_distance`,`composed_vs_joint_infidelity`,`composed_vs_joint_choi_distance`,`composed_vs_joint_infidelity_leading` | superop assembly / Choi→Kraus / G2 witnesses | G | CPTP, PSD-Choi, trace-1 Choi-state, F∈[0,1] | yes (RuntimeWarning on TP/dropped mass; VAL dims/2-Ham) | test_joint_lindbladian (all 14) |
| *(the 3 "C" helpers `_nq_from_D`,`_connected_components` are `_private`; only `operator_support`/`restrict_...` are public — both torch-tol → G)* | | | | | |

### `carrier/accel.py` — cov **0%** · 6 units (2 C, 3 G, 1 M) — CUDA-kernel autograd glue
| unit | contract | class | invariants | DA | existing test |
|---|---|---|---|---|---|
| `available` | is fused kernel loadable (cached) | C | idempotence; matches `_load_ext` cache | no | test_kernels_fused_kraus (indirect) |
| `apply_channel_local_fused` | drop-in fused-kernel channel apply + autograd | G | bit-equal to reference apply_kraus | no | test_kernels_fused_kraus |
| `_FusedLocalKraus.forward/backward/vmap` (load-bearing autograd.Function) | fused kernel + hermitianize + adjoint grad | G | grad correctness; kraus-not-vmapped | yes (RuntimeError on kraus vmap) | test_kernels_vmap |
| `_load_ext` (load-bearing) | JIT-compile+cache the extension | M | cache-once; raise on nvcc fail | yes | test_kernels_fused_kraus |

### `carrier/exact/circuit_sim.py` — cov 16% · 18 units (4 C, 14 G) — dense-DM torch
| unit | contract | class | invariants | DA | existing test |
|---|---|---|---|---|---|
| `zero_state`,`cx`,`pauli_x`,`_accel_available` | |0..0⟩ DM; cached gates | C | trace-1; unitarity; idempotence | no | test_diff_circuit_forward |
| `embed_operator`,`apply_unitary`,`apply_channel_local`,`qubit_marginal_one`,`parity_marginal_one`,`project_qubit`,`measure_qubit_enumerate`,`project_parity`,`dephase_parity`,`dephase_parity_sweep`,`measure_parity_enumerate`,`rx`,`ry`,`bit_flip`,`amplitude_damping` | DM embed/apply/measure/project | G | trace-1, Hermitian, CPTP, marginals∈[0,1] | no | test_diff_circuit_forward (14) |

### `carrier/exact/qutrit_dm.py` — cov 19% · 29 units (few C, most G) — qutrit/ququart DM engine (torch)
| unit | contract | class | invariants | DA | existing test |
|---|---|---|---|---|---|
| `qudit_eye`,`qutrit_eye` | identity operators | C | shape; trace | no | test_qutrit_dm_exact |
| `qudit_hadamard`,`qutrit_hadamard`,`embed_operator_q`,`embed_operator`,`apply_local_op_q`,`apply_local_op`,`resolve_readout_bias`,`hermitianize_inplace_blocked` + `QutritDM.*`/`QuquartDM.*` (19 methods: prepare, apply_channel, project_stabilizer, record_oracle, logical_distribution, readout, …) | exact multi-qudit DM evolution + syndrome/record oracles | G | trace-1, Hermitian, PSD, CPTP, syndrome-prob normalization | yes (mem-lean blocked hermitianize; shape asserts) | test_qutrit_dm_exact, test_qutrit_dm_memlean (~27) |

### `carrier/kernels/qutrit_mcwf_ops_loader.py` — cov **0%** · 7 units (2 C, 5 G)
| unit | contract | class | invariants | DA | existing test |
|---|---|---|---|---|---|
| `available` | is kernel loadable | C | idempotence | no | none (indirect) |
| `apply_qubit_gate`,`multi_controlled_phase`,`apply_kraus_site`,`apply_kraus_all_sites`,`run_cached_opstream`,`run_block_traj_opstream` | CUDA kernel wrappers | G | kernel-delegate correctness | yes (RuntimeError if unavailable) | none direct |

### `carrier/kernels/sv_traj_d3_loader.py` — cov **0%** · 3 units (2 C, 1 G)
| unit | contract | class | invariants | DA | existing test |
|---|---|---|---|---|---|
| `available` | is sv_traj kernel loadable per precision | C | idempotence; raises on genuine nvcc fail (NOT False) | yes | none direct |
| `sv_traj_d3`,`sv_traj_d3_wc` | P4a MCWF trajectory kernels | G | packed-bits + norm-drift; syndrome enumeration | yes (RuntimeError/dtype) | none direct (integration in test_p2_*) |

### `certify/core.py` — cov **0%** · 9 units (7 C, 2 M)
| unit | contract | class | invariants | DA | existing test |
|---|---|---|---|---|---|
| `emitted_statistic` | extract one statistic from emitted (det,obs) | C | TV∈[0,1]; prob-normalization | VAL (det.shape, bad-statistic) | test_certify |
| `reduce_rr_corr` | (R−1,n_stab) signed corr → per-round |corr| means | C | length R−1; non-negativity | VAL (ndim) | test_certify |
| `reduce_spatial_corr` | (R,n_stab,n_stab) → per-round off-diag |corr| means | C | length R; non-neg; n_stab<2→zeros | VAL (shape) | test_certify |
| `total_variation` | TV between two prob dicts | C | TV∈[0,1] | no | test_certify |
| `compare` | score emitted-vs-anchor → (value,band,verdict,detail) | C | band[1]≥band[0]; TV∈[0,1] | VAL (statistic dispatch) | test_certify |
| `route` | pick best feasible anchor (exact-first, mem-asc) | C | ordering monotone | no | test_certify |
| `certify_cells` | route→controls-first→score→ledger | M (emits via GPU teacher/anchor) | one-emit-per-cell; controls-before-row | VAL (NotImpl/bad AnchorValue) | test_certify |
| `MeasureCtx.score` | carrier-vs-anchor distance (opt. perturbed) | C | distance ≥ 0 | no | test_certify |
| `MeasureCtx.corrupt_answer` | re-answer anchor with control corruption | M (delegates to anchor.answer, may be GPU) | AnchorValue contract | yes (delegate) | test_certify |

### `certify/facade.py` — cov **0%** · 1 unit (1 M)
| unit | contract | class | invariants | DA | existing test |
|---|---|---|---|---|---|
| `certify_teacher` | one-call: auto-anchors → route → merged ledger+verdict | M (CPU plan + GPU DM anchor) | one report/level; routing transparent | VAL (unknown level; no-feasible-anchor) | test_certify |

### `certify/types.py` — cov **0%** · 15 units (15 C) — value types + Protocol ports
| unit | contract | class | invariants | DA | existing test |
|---|---|---|---|---|---|
| `Exactness`,`Statistic`,`Verdict` (enums; each 1 method surface) | closed enums | C | membership | no | test_certify (types import) |
| `Regime`,`Feasibility`,`Capability`,`AnchorValue`,`LedgerRow` (`__post_init__`/validators) | routing/value dataclasses | C | band==0 ⟺ EXACT; class∈{a,b,c}; R≥1 | yes (band==0⟺EXACT invariant lives in core `_assert_anchor_value`) | test_certify |
| `CertReport.row`,`CertReport.summary`,`CertReport.assert_pass` | ledger query + scannable table + PASS gate | C | PASS ⟹ exact rows + controls fired | yes (assert_pass raises) | test_certify |
| `Anchor`,`Control`,`ControlledTeacher`,`DMReplayable`,`CliffordSliceable` (Protocols) | duck-typed ports | C (protocol) | independence/exactness-declared contract | no | test_certify (runtime_checkable) |

### `certify/anchors/closed_form.py` — cov **0%** · 5 units (5 C) — pure numpy analytic sidecar
| unit | contract | class | invariants | DA | existing test |
|---|---|---|---|---|---|
| `ClosedFormAnchor.emit_kind`,`answers`,`capability` | scope/feasibility descriptors | C | RR_CORR-only; feasible R≥2; class a⟺EXACT | no | test_certify |
| `ClosedFormAnchor.predict_sequence` | THEOREM: transient E[d_r d_{r+1}]=p01·p10 | C | |corr|∈[0,1]; matches exact | yes (zero-var→0 guard) | test_certify |
| `ClosedFormAnchor.answer` | AnchorValue for RR_CORR at R | C | band=0 EXACT; shape matches emitted | no | test_certify |

### `certify/anchors/controls.py` — cov **0%** · 6 units (4 C, 2 M)
| unit | contract | class | invariants | DA | existing test |
|---|---|---|---|---|---|
| `CorruptStabControl.guards`,`expect`,`ShuffleControl.guards`,`expect` | control applicability + expectation | C | membership; fixed expectation | no | test_certify |
| `CorruptStabControl.run`,`ShuffleControl.run` | corrupt/shuffle GT → emitted must FAIL to match | M (delegates to core.compare via anchor) | fired ⟺ verdict FAIL; symmetric→INAPPLICABLE | yes (tol guards) | test_certify |

### `certify/anchors/dm_oracle.py` — cov **0%** · 3 units (3 G) — torch cuda + qutrit_dm
| unit | contract | class | invariants | DA | existing test |
|---|---|---|---|---|---|
| `DMOracleAnchor.answers` | answerable statistics set | C→(kept with unit) | frozenset | no | test_certify |
| `DMOracleAnchor.capability` | OOM-as-data feasibility descriptor | G (DM mem accounting) | feasible ⟹ mem≤budget; band=0 EXACT | VAL (R≠1 DETECTOR_MARG; missing n_stab) | test_certify (capability oom-safe) |
| `DMOracleAnchor.answer` | exact GT via qutrit_dm engine (cuda) | G | band=0; matches emitted shape | yes (kind!=moments RuntimeError) | test_certify (indirect) |

### `certify/anchors/stim_clifford.py` — cov **0%** · 4 units (4 C) — `stim` Clifford (CPU)
| unit | contract | class | invariants | DA | existing test |
|---|---|---|---|---|---|
| `StimCliffordAnchor.emit_kind`,`answers`,`capability` | scope/feasibility (statistical, any R) | C | class 'b'; band~C/√N; mem=0 | no | test_certify |
| `StimCliffordAnchor.answer` | N-shot Clifford bit-flip slice via stim → statistic | C | band=6/√N; matches emitted shape | no | test_certify |

### `frontend/analog_schedule.py` — cov 17% · 12 units (12 C) — schedule metadata (no tensors by design)
| unit | contract | class | invariants | DA | existing test |
|---|---|---|---|---|---|
| `DurationBracket`,`DurationPolicy`,`SubstepOperation`,`AnalogSubstepIR`,`SubstepSchedule` (`__post_init__`) | frozen schedule IR dataclasses | C | low<high; one-kind-per-substep; seal validity | VAL | test_simulator_axis1_schedule |
| `h3_h5_duration_policy`,`compile_code_spec_to_substep_schedule`,`circuit_ir_to_substep_schedule`,`stim_circuit_to_substep_schedule` | compilers → SubstepSchedule (+ HMAC seal) | C | metadata aggregation; seal injection | VAL | test_simulator_axis1_schedule/codespec |
| `has_valid_compiler_schedule_seal`,`require_compiler_schedule_seal` | HMAC seal check / enforce | C | seal round-trip | yes (require_ raises) | test_simulator_axis1_schedule |

### `frontend/artifacts.py` — cov 31% · 7 units (7 C) — artifact writers
| unit | contract | class | invariants | DA | existing test |
|---|---|---|---|---|---|
| `ArtifactPaths`,`artifact_paths` | structured artifact paths | C | path round-trip | no | none direct |
| `write_b8`,`write_b8_optional` | pack bool→Stim .b8 | C | **byte round-trip** (b8 pack/unpack) | VAL (shape/ndim) | none direct |
| `write_json` | JSON w/ sorted keys | C | JSON parse round-trip; sort-determinism | no | none direct |
| `clear_known_artifacts` | remove artifact files | C | idempotence (missing_ok) | no | none direct |
| `file_sha256` | sha256 of file or None | C | hash stability | no | none direct |
| `record_summary` | JSON-safe det/obs summary | C | marginal normalization | VAL (dtype/ndim) | none direct |

### `frontend/circuit_ir.py` — cov 26% · 18 units (18 C) — keyed circuit IR
| unit | contract | class | invariants | DA | existing test |
|---|---|---|---|---|---|
| `GateOp`,`Tick`,`MeasureOp`,`DetectorDef`,`ObservableDef`,`CircuitIR` (`__post_init__` + accessors),`CircuitBuilder.gate/measure/detector/observable/*` | IR dataclasses + ergonomic builder | C | schema round-trip; key↔target bijection; measure-before-detect; name uniqueness | VAL (extensive) | test_circuit_ir_exports_* |

### `frontend/code_spec.py` — cov 20% · 11 units (11 C) — syndrome-code specs
| unit | contract | class | invariants | DA | existing test |
|---|---|---|---|---|---|
| `CodeQubit`,`PauliTerm`,`StabilizerCheck`,`LogicalObservableSpec`,`Axis1StaticZZDeviceSpec`,`CodeSpec` (`__post_init__`) | code-spec dataclasses | C | qubit coverage; stabilizer commutativity; logical anti-commute; rounds≥2 | VAL (extensive) | test_simulator_codespec, test_codespec_rejects_* |
| `commute` | Pauli-product commute test | C | permutation-invariance | no | none direct |

### `frontend/compiler.py` — cov 20% · 2 units (1 C, 1 M)
| unit | contract | class | invariants | DA | existing test |
|---|---|---|---|---|---|
| `compile_code_spec` | CodeSpec → keyed CircuitIR | C | schema round-trip; X/Z basis only | VAL (basis support) | test_simulator_codespec |
| `compile_code_spec_to_compiled` | CodeSpec+noise → CompiledCircuit | M (CPU compile; GPU only if leak observable queried) | schema round-trip via stim_io | no | test_simulator_codespec |

### `frontend/experiments.py` — cov **84%** (Wave-2 pilot) · 4 units (3 C, 1 M) + `ExperimentPreset`
| unit | contract | class | invariants | DA | existing test |
|---|---|---|---|---|---|
| `_dataset_files` (load-bearing) | resolve shipped d3 files, precedence arg>env>default | C | file existence; no silent fallback | VAL (empty-env, missing-file) | test_frontend_experiments |
| `load_xzzx_d3` | parse XZZX schedule (opt. interior streams) | C | schedule round-trip | VAL (via `_dataset_files`) | test_frontend_experiments |
| `resolve_theta`,`run_spec_from_preset` (+ `ExperimentPreset.__post_init__`) | resolve WG theta; build RunSpec; 7 field validations | C | exactly-one-of theta/wg; interval edges | VAL (7 raises) | test_frontend_experiments |
| `leak_slice_table` | per-CZ leak Kraus table (preset OR RunSpec arm) | M (CPU TypeError route + GPU SvSampler builder) | CPTP residual<1e-12; composition identity | VAL (TypeError) | test_frontend_experiments (requires_cuda) |
*(This module + `ShotSet` accessors + `mps_forward` seams are the Wave-2/2.6 pilot — already fully specified in the parent contract §3–5; L3 does NOT re-scope them.)*

### `frontend/interop.py` — **DONE** (D6: L0 100/100 · L2 0.952) · 3 units (3 C) — **fully CPU-pure** (stim + PyMatching, no torch)
| unit | contract | class | invariants | DA | existing test |
|---|---|---|---|---|---|
| `records_to_dem` | reduce (det) cube → matchable stim DEM via exact Spitz p_ij | C | DEM round-trip; p_ij∈[0,0.5); boundary-residual identity | VAL (extensive shape/bounds) | test_p0_interop |
| `decode_records` | MWPM-decode det vs DEM (PyMatching, CPU) | C | output shape (N,); logical_index bounds | VAL (ndim, index) | test_p0_interop |
| `insert_op_after_tick` | inject deterministic fault at a TICK | C | tick bounds; stim frame semantics | VAL (tick bounds) | none direct |

### `frontend/metadata_guard.py` — cov 9% · 4 units (4 C) — learner-visibility guards
| unit | contract | class | invariants | DA | existing test |
|---|---|---|---|---|---|
| `validate_public_metadata` | reject evaluator-truth keys, copy | C | learner-visible key legality (isolation contract) | VAL (reserved-key raise) | test_simulator_codespec (metadata) |
| `normalize_axis1_static_zz_couplings`,`normalize_axis1_static_zz_calibrations` | normalize/validate static-ZZ edges & calibrations | C | canonical edge order; no dup; edge⊆declared | VAL | none direct |
| `axis1_static_zz_calibrations_to_manifest` | JSON-safe sorted records | C | sort-determinism | no | none direct |

### `frontend/noise.py` — cov 80% · 3 units (3 C) — public noise API
| unit | contract | class | invariants | DA | existing test |
|---|---|---|---|---|---|
| `no_noise`,`depolarizing_noise`,`targeted_noise` (+ `Noise` facade) | build noise specs | C | prob normalization (delegated) | no | test_simulator_noise_module |

### `frontend/noise_spec.py` — cov 16% · 20 units (20 C) — **fully CPU-pure** (Stim Pauli logic, no torch)
| unit | contract | class | invariants | DA | existing test |
|---|---|---|---|---|---|
| `StimPauliNoiseSpec`,`StimNoiseRule`,`TargetedStimNoiseSpec`,`SourceStimPauliRule`,`SourceStimPauliProjectionSpec` (`__post_init__` + methods),`NoiseBuilder.*`,`apply_stim_pauli_noise` | Stim/Pauli noise projection specs + builder | C | prob∈[0,1]; record-schema preserved; rule position/match legality | VAL (extensive) | test_simulator_noise_module, test_pauli_noise_* |
*(Correction to intake: `SourceStimPauliProjectionSpec` is CPU-pure — the module imports NO torch/cuda; payload access is numpy on evaluator-side arrays.)*

### `frontend/operation.py` — cov 39% · 7 units (7 C)
| unit | contract | class | invariants | DA | existing test |
|---|---|---|---|---|---|
| `OperationSpec`,`OperationSet` (`__post_init__`),`canonical_operation_name`,`default_memory_operations`,`as_operation_set` | named op set + canonicalization | C | name∈ALLOWED; uniqueness | VAL | none direct |

### `frontend/record_layout.py` — cov 51% · 14 units (14 C) — record-layout schema
| unit | contract | class | invariants | DA | existing test |
|---|---|---|---|---|---|
| `RoundMeasurementRecord`,`DetectorLayoutRecord`,`FinalDataRecord`,`ObservableLayoutRecord`,`RecordLayout` (+ `to_manifest`),`build_repeated_memory_record_layout`,`final_measurements`,`check_key`,`delta_detector_name`,`final_detector_name`,`final_key` | frozen layout dataclasses + name/key builders | C | schema/manifest round-trip; name-format stability; key uniqueness | no | none direct |

### `frontend/record_schema.py` — cov 35% · 10 units (10 C)
| unit | contract | class | invariants | DA | existing test |
|---|---|---|---|---|---|
| `RecordSchema` (+ from_stim/from_circuit_ir + accessors),`require_frontend_representability`,`require_stim_circuit`,`require_matching_schemas`,`validate_evaluator_sidecars`,`b8_manifest_entry` | schema + guards | C | count consistency; packed-bytes = ⌈bits/8⌉; sidecar visibility=evaluator_only | VAL (type/membership/mismatch) | none direct |

### `frontend/schedule.py` — cov 32% · 6 units (6 C)
| unit | contract | class | invariants | DA | existing test |
|---|---|---|---|---|---|
| `ScheduleTemplate` (`__post_init__` + accessors),`repeated_memory_schedule`,`repeated_memory_schedule_manifest`,`canonical_schedule_name`,`resolve_schedule_template` | schedule template + resolution | C | manifest match; canonical name | VAL (canonical raise) | none direct |

### `frontend/stim_io.py` — cov 19% · 7 units (7 C) — Stim adapters (CPU)
| unit | contract | class | invariants | DA | existing test |
|---|---|---|---|---|---|
| `StimCounts`,`circuit_to_stim`,`load_stim_circuit`,`write_stim_circuit`,`write_detector_error_model`,`detector_error_model`,`counts`,`sample_detector_records` | CircuitIR↔Stim + DEM + sampling | C | rec-target consistency; **round-trip** str(circuit) parseable; det/obs count correct | VAL (unknown-key, offset bounds) | test_circuit_ir_exports_* |

### `frontend/stim_source.py` — cov 39% · 5 units (5 C)
| unit | contract | class | invariants | DA | existing test |
|---|---|---|---|---|---|
| `CompiledCircuit`,`CircuitIRSource`,`CompiledCircuitSource`,`StimCircuitSource`,`CircuitSource` (Protocol) | compiled-circuit adapters | C | schema consistency; metadata/truth-laundering guard | VAL (extensive) | test_compiled_circuit_*, test_stim_circuit_source_* |

### `frontend/xzzx_code.py` — cov 43% · 2 units (2 C)
| unit | contract | class | invariants | DA | existing test |
|---|---|---|---|---|---|
| `XZZXCodeSpec`,`make_xzzx_3x3_compiler_smoke_spec` | XZZX code-spec factory | C | commutativity (via CodeSpec) | VAL (NotImplemented for unsupported layout) | test_xzzx_codespec_* |

### `frontend/axis1_context.py` — cov 29% · 9 units (9 C)
| unit | contract | class | invariants | DA | existing test |
|---|---|---|---|---|---|
| `Axis1LocalLindbladContextSpec` (`__post_init__` + 4 accessors),`normalize_axis1_local_lindblad_context`,`axis1_local_lindblad_context_from_schedule`,`axis1_contextual_primitive_names`,`axis1_contextual_fsim_residual_primitives` | Markovian context metadata | C | rates≥0/finite; schema version pin | VAL | implicit (axis1_bridge/selection) |

### `frontend/axis1_selection.py` — cov 13% · 12 units (12 C)
| unit | contract | class | invariants | DA | existing test |
|---|---|---|---|---|---|
| `Axis1MechanismSelection`,`Axis1MechanismSelectionPlan`,`Axis1SelectionLayer` (`__post_init__` + accessors),`axis1_selection_layers_in_schedule_order`,`flatten_axis1_selection_layers`,`axis1_selection_partition_manifest`,`build_axis1_g2_selection_plan`,`build_axis1_schedule_selection_plan` | selection plans from schedule metadata | C | row_kind∈SUPPORTED; substep coverage; manifest schema | VAL | test_simulator_axis1_schedule, test_axis1_connected_cluster_join |

### `frontend/axis1_carrier_program.py` — cov 20% · 5 units (5 C)
| unit | contract | class | invariants | DA | existing test |
|---|---|---|---|---|---|
| `Axis1CarrierTerm`,`Axis1CarrierSubstep`,`Axis1CarrierProgram` (`__post_init__` + accessors),`axis1_carrier_program_manifest` | carrier IR dataclasses + manifest | C | kind∈{ham,collapse,instrument,boundary}; JSON-safe | VAL | implicit (execution tests) |

### `frontend/axis1_evidence_guard.py` — **DONE** (D7: L0 100/100 · L2 0.977) · 3 units (3 C)
| unit | contract | class | invariants | DA | existing test |
|---|---|---|---|---|---|
| `manifest_is_executed`,`validate_axis1_evidence_manifest`,`axis1_contract_verdict` | output-side claim-scan + verdict de-overload | C | no forbidden claims_*=True; verdict matches execution | VAL (hard raise on forbidden True) | test_axis1_evidence_guard |

### `frontend/axis1_codespec_runner.py` — **DONE** (D9: L0 100/100 · L2 0.980) · 5 units (5 C) — fixture builders + `main`
| unit | contract | class | invariants | DA | existing test |
|---|---|---|---|---|---|
| `Axis1CodeSpecRecordRunnerResult`,`build_axis1_codespec_frontend_spec`,`build_axis1_codespec_4q_frontend_spec`,`build_axis1_codespec_frontend_schedule` | 5q/4q CodeSpec + schedule fixtures | C | valid CodeSpec; fixed layout | no | test_simulator_codespec (some) |
| `run_axis1_codespec_record_fixture`,`main` | run fixture end-to-end / CLI | M (CPU build + GPU record emit) | manifest+freeze | no | none direct |

### `frontend/axis1_g2_runner.py` — **DONE** (D9: L0 100/100 · L2 0.980) · 3 units (2 C, 1 M)
| unit | contract | class | invariants | DA | existing test |
|---|---|---|---|---|---|
| `Axis1G2RunnerResult`,`build_axis1_g2_frontend_schedule` | G2 result + 2q CZ schedule fixture | C | valid schedule | no | test_simulator_axis1_schedule |
| `run_axis1_g2_frontend_fixture`,`main` | run G2 evidence end-to-end | M (GPU joint-L) | g2_jointL.json | no | none direct |

### `frontend/axis1_bridge.py` — cov 21% · 6 units (4 C, 2 M)
| unit | contract | class | invariants | DA | existing test |
|---|---|---|---|---|---|
| `Axis1G2Row`,`Axis1G2EvidenceResult`,`Axis1G2FreezeResult`,`axis1_g2_gate_manifest`,`freeze_axis1_g2_evidence`,`validate_axis1_g2_freeze` | G2 rows + manifest + freeze/validate | C | hash round-trip; manifest schema | VAL | test_simulator_axis1_schedule |
| `axis1_g2_frontend_gate`,`write_axis1_g2_evidence` | build G2 row (calls GPU joint-L) / write | M | infidelity bounds; artifact I/O | VAL | test_simulator_axis1_schedule |

### `frontend/axis1_channel_evidence.py` — cov 16% · 9 units (4 C, 5 M)
| unit | contract | class | invariants | DA | existing test |
|---|---|---|---|---|---|
| `Axis1SubstepChannelEvidenceResult`,`Axis1SubstepChannelFreezeResult`,`freeze_...`,`validate_...` | result/freeze dataclasses + hash guards | C | hash round-trip | no | test_simulator_axis1_schedule |
| `Axis1SubstepChannelRow`,`Axis1AssembledSelectionChannel`,`axis1_substep_channel_rows`,`axis1_substep_channel_evidence_manifest`,`write_...` | joint-channel evidence rows (execute joint-L) | M (GPU channel assembly) | mechanism_pair valid; process-distance normalized | VAL (seal/selection) | test_simulator_axis1_schedule |

### `frontend/axis1_record_evidence.py` — cov 15% · 9 units (6 C, 2 M, 1 G)
| unit | contract | class | invariants | DA | existing test |
|---|---|---|---|---|---|
| `Axis1MeasurementRecordEvidenceResult`,`Axis1MeasurementRecordSampleResult`,`Axis1MeasurementRecordFreezeResult`,`Axis1ReadoutResetInstrumentSpec` (`__post_init__`),`freeze_...`,`validate_...` | result/instrument dataclasses + hash guards | C | prob∈[0,1]; hash round-trip | VAL (prob) | test_axis1_record_params_override |
| `axis1_measurement_record_evidence_manifest` | exact record enumeration on small-N DM | G | trace-1; Pauli enumeration | VAL (seal) | test_simulator_axis1_schedule |
| `write_...`,`write_..._samples` | write evidence / sample | M | Hoeffding CI; artifact I/O | VAL | test_simulator_axis1_schedule |

### `frontend/axis1_state_evidence.py` — cov 23% · 4 units (2 C, 1 G, 1 M)
| unit | contract | class | invariants | DA | existing test |
|---|---|---|---|---|---|
| `Axis1StateEvolutionEvidenceResult`,`Axis1StateEvolutionFreezeResult` (+freeze/validate) | result dataclasses + hash guard | C | hash round-trip | no | test_simulator_axis1_schedule |
| `axis1_state_evolution_evidence_manifest` | apply selected channels to small-N DM | G | trace residual ≤1e-8 | VAL (trace gate) | test_simulator_axis1_schedule |
| `write_axis1_state_evolution_evidence` | write | M | artifact I/O | VAL | test_simulator_axis1_schedule |

### `frontend/axis1_ideal_controls.py` — cov 11% · 2 units (1 C, 1 M)
| unit | contract | class | invariants | DA | existing test |
|---|---|---|---|---|---|
| `Axis1IdealControlRecord`,`Axis1IdealControlBundle` | ideal-control dataclasses | C | gate∈frontend gates; coeff finite | VAL | implicit |
| `lower_ideal_controls_for_selection` | lower gate → Hamiltonian terms (cuda tensors) | M (CPU record + GPU H tensors) | coeff normalized | VAL (dt>0, gate name) | implicit |

### `frontend/axis1_carrier_execution.py` — cov 16% · 1 unit (1 M)
| unit | contract | class | invariants | DA | existing test |
|---|---|---|---|---|---|
| `axis1_carrier_execution_manifest` | route to dense/MCWF/QT/qutip backend | M (CPU route + GPU execution) | backend contract; device=cuda; VRAM gate | VAL (routing/device/VRAM) | implicit |

### `frontend/axis1_mcwf_mps_contract.py` / `axis1_qt_mps_contract.py` — cov 24% / 32% · 1+1 units
| unit | contract | class | invariants | DA | existing test |
|---|---|---|---|---|---|
| `axis1_mcwf_mps_state_record_contract_manifest` | contract-only surface (non-executed) | C | verdict="contract_only"; backend_executed=False | VAL (W-J verdict) | test_axis1_finite_step_error_control |
| `axis1_qt_mps_state_record_contract_manifest` | dense-checkable + scalable-fallback contract | M | dense rows certified; scalable fails closed | VAL | implicit |

### `frontend/axis1_mcwf_mps_execution.py` — cov 7% · 1 unit (1 G) — **NEEDS-WORK per agent**
| unit | contract | class | invariants | DA | existing test |
|---|---|---|---|---|---|
| `axis1_mcwf_mps_state_record_execution_manifest` | fixed-microstep MCWF-over-MPS execution | G | CPTP; mass-residual budget | VAL (microstep/dims) | test_axis1_finite_step_error_control, test_axis1_convergence |

### `frontend/axis1_qt_mps_execution.py` — cov 7% · 5 units (5 G)
| unit | contract | class | invariants | DA | existing test |
|---|---|---|---|---|---|
| `axis1_qt_mps_restricted_execution_manifest`,`axis1_qt_mps_bond_sweep_manifest`,`axis1_qt_mps_trajectory_seed_sweep_manifest`,`axis1_qt_mps_restricted_evidence_bundle_manifest`,`axis1_qt_mps_resource_probe_manifest` | restricted QT/MPS execution + sweeps | G | product-formula approx; bond caps; truncation ledger | VAL (microstep/family/bond) | test_axis1_finite_step_error_control |

### `frontend/axis1_qutip_cuquantum_probe.py` — cov 10% · 4 units (1 C, 3 M/G)
| unit | contract | class | invariants | DA | existing test |
|---|---|---|---|---|---|
| `axis1_qutip_cuquantum_probe_manifest` | symbolic lowering probe (no solve) | C | CuOperator symbols; no execution | no | implicit |
| `axis1_qutip_cuquantum_state_probe_manifest`,`axis1_qutip_cuquantum_record_probe_manifest`,`axis1_qutip_cuquantum_trajectory_probe_manifest` | qutip mesolve/mcsolve probes | G | populations; per-traj records | VAL (qutip setup) | test_simulator_qutip_cuquantum_backend |

### `frontend/axis1_mcwf_dense_certification.py` — cov **0%** · 2 units (2 G)
| unit | contract | class | invariants | DA | existing test |
|---|---|---|---|---|---|
| `dense_jointL_record_certification`,`restricted_acceptance_policy` | W-B dense-oracle acceptance certification | G (independent joint-L oracle + MCWF) | TV distance; oracle validity | VAL (cert gate) | test_axis1_wb_acceptance_gate |

### `frontend/axis1_qutrit_leakage_certification.py` — cov 14% · 2 units (2 G)
| unit | contract | class | invariants | DA | existing test |
|---|---|---|---|---|---|
| `axis1_qutrit_leakage_oracle_certification_manifest`,`axis1_two_site_leakage_hamiltonian_certification_manifest` | de-circularized hand-typed leakage-H oracle | G | Hermiticity; per-term Frobenius; wrong-level/sign controls | VAL (oracle/control agreement) | test_axis1_wc_decircularized |

### `frontend/cudaq_grover.py` — cov 23% · 11 units (5 C, 3 G, 3 M)
| unit | contract | class | invariants | DA | existing test |
|---|---|---|---|---|---|
| `normalize_marked_state`,`index_from_bitstring`,`bitstring_from_index`,`optimal_grover_iterations`,`grover_theory_prediction` | closed-form Grover maths | C | index↔bitstring round-trip; iteration formula | VAL | test_simulator_cudaq_grover |
| `CudaQGroverArtifacts`,`CudaQGroverResult` (+accessors),`write_cudaq_grover_artifacts` | result dataclasses + writer | C/M | prob normalization; counts sum | no | test_simulator_cudaq_grover |
| `simulate_cudaq_grover_noiseless`,`build_cudaq_grover_kernel` | CUDA-Q statevector sim | G | marked-prob; statevector | VAL (n≥2) | test_simulator_cudaq_grover |

### `frontend/mcwf_backend.py` — cov 11% · 25 units (few C, most G)
| unit | contract | class | invariants | DA | existing test |
|---|---|---|---|---|---|
| `qutrit_index_from_digits`,`qutrit_string_from_index`,`digits_from_indices_t`,`mixed_radix_digits_from_indices_t`,`QutritMcwfMeasurementBatch` | mixed-radix index/string helpers + batch dataclass | C | index↔digits round-trip | no | test_simulator_mcwf_backend |
| `DenseQuditMcwfBackend.*`,`DenseQutritMcwfBackend.*` (21 methods) | dense-state MCWF backend (torch cuda) | G | CPTP; trace-1; batched-state coherence | VAL (device/dim caps) | test_simulator_mcwf_backend |

### `frontend/mcwf_executor.py` — cov 23% · 9 units (1 C, 8 G/M)
| unit | contract | class | invariants | DA | existing test |
|---|---|---|---|---|---|
| `McwfExecutionTiming` | timing dataclass | C | time≥0 | no | test_simulator_mcwf_backend |
| `McwfExecutionResult`,`DenseQutritMcwfExecutor.*`,`NativeOpStreamMcwfExecutor.*`,`BlockTrajectoryMcwfExecutor.*`,`GraphCapturedMcwfExecutor.*` | MCWF program executors (cuda) | G/M | program/backend qubit match; CUDA timing | VAL | test_simulator_mcwf_backend |

### `frontend/mcwf_grover.py` — cov 22% · 9 units (mixed)
| unit | contract | class | invariants | DA | existing test |
|---|---|---|---|---|---|
| `McwfGroverArtifacts`,`McwfGroverResult` (+accessors),`compile_mcwf_grover_program`,`write_mcwf_grover_artifacts` | result dataclasses + compile/write | C/M | marked-bit index; leakage-by-site | no | test_simulator_mcwf_grover |
| `simulate_mcwf_qutrit_grover_leakage` | MCWF Grover w/ WG leakage (cuda) | G | trajectory sampling; Kraus families | VAL (n cap) | test_simulator_mcwf_grover |

### `frontend/mcwf_program.py` — cov 26% · 8 units (8 C) — MCWF IR
| unit | contract | class | invariants | DA | existing test |
|---|---|---|---|---|---|
| `McwfQubitGateOp`,`McwfCachedQubitGateOp`,`McwfAllOnesPhaseOp`,`McwfKrausAllSitesOp`,`CompiledMcwfProgram` (`__post_init__`),`h`,`x`,`all_ones_phase`,`kraus_all_sites`,`qubit_gate` | compiled MCWF op-stream IR + builders | C | initial_levels∈{0,1,2}; op-stream consistency | VAL | test_simulator_mcwf_backend |

### `frontend/qutip_cuquantum_backend.py` — cov 28% · 5 units (2 C, 3 G)
| unit | contract | class | invariants | DA | existing test |
|---|---|---|---|---|---|
| `QutipCuQuantumSymbolicCollapseSummary`,`QutipCuQuantumLocalMcwfProbeResult`,`wg_seep_collapse_matrix` | summary dataclasses + local seep matrix | C | shape (3,3); only [1,2] nonzero | no | test_simulator_qutip_cuquantum_backend |
| `local_qutrit_operator_qobj`,`zero_hamiltonian_qobj`,`qutip_cuquantum_symbolic_collapse_summary`,`probe_qutip_cuquantum_local_mcwf` | qutip/CuOperator ops + probes | G | symbolic CuOperator; no dense expansion | VAL | test_simulator_qutip_cuquantum_backend |

### `frontend/ququart_transport.py` — cov 22% · 11 units (mixed)
| unit | contract | class | invariants | DA | existing test |
|---|---|---|---|---|---|
| `index_from_ququart_string`,`ququart_string_from_index`,`ququart_string_from_levels`,`normalize_initial_levels4`,`QuquartTransportArtifacts`,`QuquartTransportResult`,`load_ququart_transport_kraus`,`write_ququart_transport_artifacts` | index/string helpers + result + kraus loader | C/M | index↔string round-trip; joint-prob sum=1 | VAL | test_simulator_ququart_transport |
| `simulate_ququart_transport_smoke` | ququart DM leakage-transport (cuda) | G | populations exact | VAL (n range) | test_simulator_ququart_transport |

### `frontend/qutrit_leakage.py` — cov 25% · 9 units (mixed)
| unit | contract | class | invariants | DA | existing test |
|---|---|---|---|---|---|
| `index_from_qutrit_string`,`qutrit_string_from_index`,`qutrit_string_from_levels`,`normalize_initial_levels`,`QutritLeakageArtifacts`,`QutritLeakageResult`,`write_qutrit_leakage_artifacts` | index/string + result + writer | C/M | index↔string round-trip; joint-prob sum=1 | VAL | test_simulator_qutrit_leakage |
| `simulate_qutrit_wg_leakage` | exact QutritDM WG leakage (cuda) | G | site populations exact | VAL (n cap) | test_simulator_qutrit_leakage |

### `frontend/simulator.py` — cov 17% · 7 units (1 C, 6 M/G)
| unit | contract | class | invariants | DA | existing test |
|---|---|---|---|---|---|
| `SimulationResult` | artifact-paths dataclass | C | records loadable | no | test_simulator_frontend |
| `Simulator.*` (facade methods),`simulate_noiseless` | facade routing + noiseless statevector | M/G | CircuitIR/source routing; state evolution | VAL (circuit type) | test_simulator_frontend, test_simulator_noiseless_interface |

### `frontend/source_sidecar.py` — cov 18% · 7 units (7 C) — evaluator-only source sidecars
| unit | contract | class | invariants | DA | existing test |
|---|---|---|---|---|---|
| `SourceTimelineBinding` (`__post_init__`),`default_source_timeline_binding`,`infer_source_binding_context`,`write_source_timeline_sidecar`,`build_source_timeline_binding_manifest`,`source_binding_public_stub`,`load_source_timeline_from_manifest` | source-timeline alignment + sidecar I/O | C | cycle/shot binding legality; **sha256 round-trip**; qec_round length consistency | VAL (NotImplemented for continuous_acq) | test_simulator_source_sidecar |

### `mechanisms/axis1_primitives.py` — cov 23% · 9 units (5 C, 2 G, 2 M)
| unit | contract | class | invariants | DA | existing test |
|---|---|---|---|---|---|
| `Axis1PrimitiveParams` (`__post_init__`,`drive_omega`,`to_manifest`),`Axis1PrimitiveRecord`,`Axis1PrimitiveRegistry` (`lower`,`to_manifest`),`default_axis1_primitive_registry` | primitive param/record/registry dataclasses | C | gamma≥0; zeta≥0; drive>0 | VAL | test_m*_constraint_ledger |
| `Axis1PrimitiveBundle` | H_list/c_list container (torch tensors) | M | tensors on device | no | test_m*_constraint_ledger |
| `lower_two_qubit_axis1_primitives`,`two_qubit_axis1_ops` | lower names → cuda H_list/c_list | G | CPTP≤1e-12; device=cuda | VAL (dt>0, unsupported) | test_m6/m7/m20/m22/m23/m29_constraint_ledger |

### `mechanisms/catalog.py` — cov 46% · 6 units (6 C) — mechanism taxonomy
| unit | contract | class | invariants | DA | existing test |
|---|---|---|---|---|---|
| `mechanism_name`,`mechanism_public_label`,`mechanism_label_namespace`,`legacy_mechanism_id`,`mechanism_contract`,`mechanism_taxonomy_contract_audit` | string/label taxonomy lookups + audit | C | map lookup; 35-mech coverage; audit-checks-total | VAL (KeyError) | implicit (test_source_coupling) |

### `mechanisms/qutrit_teachers.py` — cov 71% · 8 units (4 C, 4 G)
| unit | contract | class | invariants | DA | existing test |
|---|---|---|---|---|---|
| `calibrate_theta_for_wg_l1`,`leaked_map`,`leaked_map_params` | bisection calib + leaked-readout map (pure math) | C | theta∈[0,π/2] monotone; b∈[0,1] | VAL (target range, b∈[0,1]) | test_p2_theta_leakage |
| `wg_rates`,`coherence_of_leakage`,`leakage_kraus_torch`,`qutrit_leakage_teacher`,`qutrit_leakage_teacher_heterogeneous` (+ `QutritLeakageTeacher`) | WG rates/coherence + cuda Kraus + teacher factories | G | WG_L1∈(0,0.5); C_L≥0 (=0 iff θ=0); CPTP | no (delegate) | test_p2_theta_leakage, test_simulator_qutrit_leakage |

### `mechanisms/seam_teachers.py` — **DONE** (D8: L0 100/100 · L2 0.991) · 11 units (11 C) — device-agnostic torch (CPU-runnable)
| unit | contract | class | invariants | DA | existing test |
|---|---|---|---|---|---|
| `tb_markov_kraus`,`tb_record_chain_stats`,`tb_member_from_rate_and_ratio`,`backdrop_kraus`,`backdrop_teacher`,`coherent_seam_teacher`,`bias_injected_coherent_teacher`,`twirled_seam_teacher`,`tb_bunching_teacher`,`pauli_ablation_teacher`,`seam_teacher_arms` (+ `SeamTeacher`) | ADR-0008 seam teacher arms | C (small torch, device-agnostic) | CPTP; non-unital; record-chain identities | VAL (ratio>1 for sqrt) | test_carrier_seam_* (NOT in Wave-2 .coverage → shows 0%) |

### `mechanisms/teachers.py` — cov 22% · 9 units (9 C) — device-agnostic torch (CPU-runnable)
| unit | contract | class | invariants | DA | existing test |
|---|---|---|---|---|---|
| `coherent_overrotation_kraus`,`coherent_overrotation_field`,`amplitude_damped_rotation_kraus`,`mixed_mechanism_field`,`zz_coupling_kraus`,`correlated_dephasing_kraus`,`coupled_mixed_teacher`,`pauli_twirl_kraus`,`pauli_twirl_field` | B5 teacher Kraus/field builders + Pauli twirls | C (small torch, device-agnostic) | CPTP; twirl even-in-phi; PTM-diagonal | VAL (kind) | test_twin_h0/h1/h2 |

### `quantum_bath/carrier.py` — cov **0%** · 9 units (9 C) — exact-DM CPU (16·nmax)
| unit | contract | class | invariants | DA | existing test |
|---|---|---|---|---|---|
| `cnot4`,`z_parity_unitary_4q`,`x_parity_unitary_4q`,`apply_idle_reduced`,`dual_extract`,`quantum_dual_P_all`,`dual_point`,`quantum_dual_P_all_qrt`,`dual_point_qrt` | dual-ancilla dual-axis exact-DM carrier | C | unitarity (parity ±1); trace-1 branches; P sums=1; K≥0 | yes (norm≈1 asserts) | test_quantum_bath |

### `quantum_bath/crow_joynt.py` — cov **0%** · 5 units (5 C) — closed-form + quadrature
| unit | contract | class | invariants | DA | existing test |
|---|---|---|---|---|---|
| `gamma_unit_closed`,`sigma_offdiag_closed`,`build_sigma`,`field_null_dual_P_all`,`field_null_point` | classical-field null + phase covariance closed forms | C | Σ Hermitian PSD; P sums=1; K≥0 | no | test_quantum_bath |

### `quantum_bath/gksl.py` — cov **0%** · 3 units (3 C) — bosonic GKSL (scipy.expm CPU)
| unit | contract | class | invariants | DA | existing test |
|---|---|---|---|---|---|
| `boson_ops`,`build_shared_bath_liouvillian`,`round_superop` | boson algebra + shared-bath Liouvillian + superop | C | b†=b.conj().T; CPTP of exp(L) | no | test_quantum_bath |

### `quantum_bath/ground_truth.py` — cov **0%** · 6 units (6 C) — anti-toy formal oracles
| unit | contract | class | invariants | DA | existing test |
|---|---|---|---|---|---|
| `full_superop_bytes`,`factorization_check`,`extraction_gt_check`,`two_qubit_indep_boson_gt`,`sigma_minus_emission_gt`,`no_bath_sanity` | independent-GT check computations | C | worst_err→0; K/CMI≈0 (no-bath) | yes (random-rho / hardcoded-state asserts) | test_quantum_bath |

### `quantum_bath/memory_witness.py` — **DONE** · 4 LIVE units (4 C) — Backer C#<C witness (exact-DM)
| unit | contract | class | invariants | DA | existing test |
|---|---|---|---|---|---|
| `jc_reduced_choi`,`concurrence`,`concurrence_of_assistance`,`quantum_memory_witness` | Backer Thm 1 quantum-memory witness (C♯(t₁)<C(t₂)) + its Choi / Wootters primitives | C | Choi trace-1 Hermitian PSD; C∈[0,1]; `jc_reduced_choi` & the C/C♯ curves == the INDEPENDENT damped-JC AD-Choi oracle | yes | test_quantum_bath_memwitness_units (L0 100/100, L2 0.917) |
*(RETIRED 2026-07-07 → `retired/quantum_bath/`: `entropic_memory_witness_single`/`_two_qubit`, `negativity`, `von_neumann_entropy`, `_revival_fire`, `_two_qubit_*` — the entropic / negativity-BACKFLOW witnesses were RETRACTED-as-quantum-memory 2026-07-06 (a bare revival = RHP non-Markovianity, forgeable by classical RTN dephasing) and REMOVED from the reachable package. Batch scope = the 4 LIVE units.)*

### `quantum_bath/nulls.py` — cov **0%** · 6 units (6 C) — incoherent-AD null family
| unit | contract | class | invariants | DA | existing test |
|---|---|---|---|---|---|
| `axis_ad_null_point`,`coherent_ad_null_point`,`min_tv_to_incoherent`,`classical_ad_null_point`,`classical_nonmarkov_ad_null_point`,`collective_ad_null_point` | AD null family + model-free TV discriminator | C | CPTP; P sums=1; TV∈[0,1]; K≥0 | yes (latent-traj enumeration) | test_quantum_bath |

### `quantum_bath/observables.py` — cov **0%** · 7 units (7 C) — multi-time record stats
| unit | contract | class | invariants | DA | existing test |
|---|---|---|---|---|---|
| `K_stat_joint`,`project_axis`,`K_stat_binary`,`M_mem_stat`,`exact_cmi_bits`,`tv_distance`,`record_distance` | K / M_mem / CMI / TV record statistics | C | K,M_mem≥0; TV,record_dist∈[0,1]; project-axis marginal | no | test_quantum_bath |

### `source/coupling.py` — cov 32% · 18 units (18 C) — Theta fan-out closed-form maths
| unit | contract | class | invariants | DA | existing test |
|---|---|---|---|---|---|
| `StaticZZCalibration`,`SourceCouplingConfig`,`CoupledMechanismParams` (`__post_init__` + accessors),`default_source_coupling_config`,`source_to_params`,`trajectory_to_params`,`independent_baseline_trajectory_to_params`,`parameter_series`,`cross_mechanism_correlation`,`static_zz_zeta`,`exchange_j_from_phi`,`zz_phi_from_frequency_drift`,`drift_to_t2`,`leakage_from_drift` | shared-source parameter fan-out | C | rate≥0/prob∈[0,1] after modulation; correlation∈[−1,1]; permutation-exact ablation | VAL (finiteness/positivity guards) | test_source_coupling, test_source_closed_forms |

### `source/process.py` — cov 17% · 28 units (28 C) — RTN/1-over-f/burst/storm time-series
| unit | contract | class | invariants | DA | existing test |
|---|---|---|---|---|---|
| `SourceTimeline` (+ 8 methods: series/ablation/manifest/save/load npz),`SourceProcess`,`RTNSource` (+ sample/props),`OneOverFDriftSource` (+ sample/props/analytic_psd),`PhaseBurstSource` (+sample),`TemporalStormSPPSource` (+sample/from_fixed_marginal/props/empirical_*),`timeline_to_coupled_params`,`timeline_to_site_coupled_params`,`lag_autocorrelation` | source processes + timeline persistence | C | autocorr=exp(−2γlag); PSD≥0; transition rows sum 1; sha256 round-trip; permutation-exact ablation | VAL (extensive; save/load sha256) | test_source_process, test_source_closed_forms |

### `teachers/coupled_cycle.py` — **DONE (D10)** · L0 100/100 (17 units) · L2 kill 0.964 · 18 units (17 in-scope + 1 gpu oos)
> Stage-D `stage_d_coupled_cycle_targets` — `tests/test_coupled_cycle_units.py`. Authoritative gate PASS
> (17/17 stmt+branch 100%, reconcile 18 = 17 registered + 1 out_of_scope, 0 exemptions). Authoritative
> mutation 1085/1125 = **0.9644** (tested-only 0.9464). `CoupledCycleTeacher.emit` is the sole
> `out_of_scope=gpu_bound` (torch multinomial MC on cuda; lazy `import torch` passes the anti-lie check;
> the CPU-prefix seal/regime/m=0/N≥1 validation IS mutation-covered). `__init__` is not an AST-reconciled
> public unit (dunder) but its CPU logic is exercised + mutation-covered on every construction. 40 residual
> survivors all classified genuine-equivalent (defensive-guard message text on compiler-internal invariants;
> dead `.get(k,())` defaults with always-present keys; GPU-only `_table_cache`; `_derived_seed` byteorder
> ≡Py3.12-default & utf-8 codec-normalize; `consumer_name` diagnostic-only; PauliTerm basis
> uppercase-normalized; dataclass-default kwargs; device-string not surfaced in `truth`).
| unit | contract | class | invariants | DA | existing test |
|---|---|---|---|---|---|
| `derive_round_map_for_substep_schedule`,`params_for_substep_from_round_map`,`per_round_axis1_params`,`trajectory_mean_instrument`,`default_coupled_code_spec`,`default_coupled_code_spec_4q`,`default_coupled_code_spec_d3_repz`,`CoupledCycleTeacher.sched`,`CoupledCycleTeacher.truth`,`CoupledCycleTeacher.export_stim_circuit` | round-map derivation + fixtures + sealed props | C | round-map three-witness cross-validation; deep-copy truth; det/obs layout identity | VAL (9+ raises; C-1 seal; C-12 m=0) | test_coupled_cycle_teacher (exists but not in Wave-2 .coverage) |
| `CoupledCycleTeacher.emit` | emit N records {det,obs} (torch multinomial) | G | outer-MC-over-traj; inner exact manifest | VAL (seal/m=0/N≥1/passed) | test_coupled_cycle_teacher |
| `CoupledCycleTeacher.__init__`,`channels`,`markovian_baseline`,`off_source` (+ `emit_clifford_slice` = NotImplemented) | ctor + channel assembler + ablation arms | M (CPU logic + GPU tensors) | Theta(0) mean-field; arm∈{shared,independent,off} | VAL; `emit_clifford_slice` intentionally raises NotImplementedError (slice-2) | test_coupled_cycle_teacher |

---

## (c) Prioritized Stage-D batch plan

Batches are **module-grouped, CPU-pure-first, lowest-coverage-first** — the order maximizes
new *behavior* coverage per unit of test-writing effort, and front-loads the 24 zero-coverage
modules (the biggest structural gaps). Effort is L0 (100% stmt+branch) + L1 (Hypothesis
properties over the listed invariants); L2 (mutation) runs in Stage E over the same CPU-pure
set. GPU-bound units are flagged for the **lighter treatment only** and are NOT in the L0/L1
batches. Each batch = one committed runner + audit + full-suite regression + un-led review.

**Effort key:** S ≈ ½ day (≤10 units, simple validation), M ≈ 1 day (10–20 units or nontrivial
invariants), L ≈ 1.5–2 days (20+ units, byte/round-trip/statistics harnesses).

### Tier 1 — zero-coverage CPU-pure (highest value; never run in Wave-2)
| # | batch (module) | units (CPU-pure) | cov now | invariants that anchor L1 | effort |
|---|---|---|---|---|---|
| D1 | `quantum_bath/observables.py` | 7 | 0% | K/M_mem≥0, TV/record_dist∈[0,1], project-axis marginal | S |
| D2 | `quantum_bath/{gksl,crow_joynt}.py` | 3+5 | 0% | Σ PSD-Hermitian, b†=b.conj().T, CPTP-of-expL, P sums=1 | S |
| D3 | `quantum_bath/{carrier,ground_truth,nulls,memory_witness}.py` | 9+6+6+8 | 0% | parity ±1, trace-1 branches, worst_err→0, C∈[0,1], K≥0 | L |
| D4 | `certify/{types,facade}.py` (CPU units) + `certify/anchors/{closed_form,controls,stim_clifford}.py` | 15+1+5+4+4 | 0% | band==0⟺EXACT, TV∈[0,1], analytic-theorem match, control fires⟺FAIL | M |
| D5 | `certify/core.py` (7 CPU units) | 7 | 0% | reductions non-neg + shape, TV∈[0,1], route ordering | S |
| D6 | `frontend/interop.py` | 3 | 0% | DEM round-trip, p_ij∈[0,0.5), boundary-residual identity | S |
| D7 | `frontend/axis1_evidence_guard.py` | 3 | 0% | no forbidden claims_*=True, verdict⟺execution | S |
| D8 | `mechanisms/seam_teachers.py` | 11 | 0% | CPTP, non-unital, record-chain identities | M |
| D9 | `frontend/{axis1_codespec_runner,axis1_g2_runner}.py` (CPU fixture builders) | 3+2 | 0% | valid CodeSpec/schedule construction | S |
| D10 | `teachers/coupled_cycle.py` (12 CPU units) | 12 | 0% | round-map three-witness, deep-copy truth, layout identity, seal | M |

### Tier 2 — low-coverage CPU-pure (large behavior surface)
| # | batch (module) | units (CPU-pure) | cov now | invariants that anchor L1 | effort |
|---|---|---|---|---|---|
| D11 | `source/process.py` | 28 | 17% | autocorr=exp(−2γlag), PSD≥0, transition rows sum 1, sha256 round-trip, permutation-exact ablation | L |
| D12 | `source/coupling.py` | 18 | 32% | rate≥0/prob∈[0,1] post-modulation, corr∈[−1,1], permutation-exact | M |
| D13 | `carrier/channels.py` (numpy) | 30 (+2 M expm tail) | 20% | **CPTP** (ΣK†K=I), **unitarity**, row-stochastic readout, prob-floor | L |
| D14 | `frontend/{record_layout,record_schema,artifacts}.py` | 14+10+7 | 51/35/31% | schema/manifest round-trip, byte (.b8) round-trip, ⌈bits/8⌉, sha256 | M |
| D15 | `frontend/{circuit_ir,code_spec,compiler,stim_io,stim_source}.py` | 18+11+1+7+5 | 20–39% | schema round-trip, key↔target bijection, commutativity, str-round-trip, truth-laundering guard | L |
| D16 | `frontend/{noise,noise_spec,operation,schedule,xzzx_code}.py` | 3+20+7+6+2 | 16–80% | prob∈[0,1], record-schema preserved, name∈ALLOWED, manifest match | M |
| D17 | `frontend/{metadata_guard,axis1_context,axis1_selection,axis1_carrier_program,source_sidecar}.py` | 4+9+12+5+7 | 9–29% | reserved-key reject, rate≥0, row_kind∈SUPPORTED, JSON-safe, sha256 round-trip | M |
| D18 | `frontend/analog_schedule.py` (CPU) | 12 | 17% | low<high, one-kind-per-substep, HMAC seal round-trip | S |
| D19 | `mechanisms/{teachers,catalog}.py` + `mechanisms/qutrit_teachers` (4 CPU) + `mechanisms/axis1_primitives` (5 CPU) | 9+6+4+5 | 22–71% | CPTP, twirl even-in-phi, taxonomy map, theta∈[0,π/2] monotone | M |
| D20 | `numerics.py` + `carrier/{accel,kernels/*}.available` (CPU loader-status) | 2+3 | 0–71% | idempotence, floor∈[0,1] | S |

### Tier 3 — MIXED units (split: CPU core → L0+L1 here; GPU tail → lighter)
Route the CPU cores of the MIXED units through the batch that owns their module (e.g.
`certify.certify_teacher` level-validation + `leak_slice_table` TypeError-route are covered in
D4/experiments-pilot; the `write_*`/`run_*` artifact-I/O + routing halves of the axis1 evidence
modules get their CPU dataclass/freeze/validate/hash-guard halves tested alongside their
module). The GPU execution halves stay in Tier 4.

### Tier 4 — GPU/QUIMB-BOUND (lighter treatment ONLY — no L0/L1/L2 batches)
These ~89 units keep **structural coverage + a hand KILLER + their existing independent-referee
equivalence gate**. They are explicitly OUT of the L0/L1 batches. Coverage gate line-ranges must
exclude them from any CPU-pure unit's target (the §12.4 "GPU-bound → structural+KILLER+equivalence"
rule; the parent contract's `requires_cuda` exemptions are the template).
- `carrier/cptp_channel.py` (9 G) → test_kernels_fused_kraus / test_diff_cptp_channel_recovery
- `carrier/joint_lindbladian.py` (11 G) → test_joint_lindbladian (already 27-way covered logically)
- `carrier/exact/circuit_sim.py` (14 G), `carrier/exact/qutrit_dm.py` (~25 G) → test_diff_circuit_forward / test_qutrit_dm_exact / test_qutrit_dm_memlean
- `carrier/accel.py` (3 G) + `carrier/kernels/*` (6 G) → test_kernels_fused_kraus / test_kernels_vmap
- `certify/anchors/dm_oracle.py` (2 G) → test_certify (capability oom-safe + DM↔carrier equivalence)
- `frontend/mcwf_*` , `qutip_cuquantum_backend`, `cudaq_grover` (G units), `ququart_transport`,
  `qutrit_leakage`, `simulate_noiseless`, `axis1_*_execution`, `axis1_*_certification`,
  `axis1_qutip_cuquantum_probe` (solver units) → their `test_simulator_*` / `test_axis1_*` gates.
- `mechanisms/qutrit_teachers` (4 G) → test_p2_theta_leakage / test_simulator_qutrit_leakage.

**Proposed Stage-D order:** D1 → D2 → D3 → D4 → D5 → D6 → D7 → D8 → D9 → D10 (finish the
zero-coverage CPU-pure surface first — it is both the biggest structural gap and the
independent-referee physics spine), then D11 → D20 (low-coverage CPU-pure, largest-surface
first). Tier-4 GPU units are folded in as each module's lighter-treatment pass, gated by the
coverage registry's per-unit line ranges so their lines never count against a CPU-pure target.

---

## (d) Open questions (genuinely-ambiguous classifications + release-quality reads)

1. **Device-agnostic torch → CPU-PURE or GPU-BOUND?** `mechanisms/teachers.py` (9),
   `mechanisms/seam_teachers.py` (11), and `mechanisms/axis1_primitives.Axis1PrimitiveBundle`
   import torch but build **small, device-agnostic** dense Kraus/field tensors that run on CPU.
   I classified them **CPU-PURE** (they are CPU-runnable and cheap, and their invariants — CPTP,
   twirl-even-in-phi — are device-independent, so Hypothesis can drive them on CPU tensors).
   Confirm this is the intended treatment (full L0+L1+L2) vs holding them at structural+KILLER
   like the true-cuda units. **Recommendation: CPU-PURE** — they are physics builders, not state
   evolution, and the L1 CPTP property is exactly the faithfulness invariant we want machine-checked.

2. **`certify/anchors/stim_clifford.py` — CPU-PURE (I classified) vs its own equivalence gate.**
   It uses the `stim` Clifford sampler (CPU, statistical). Its `answer` is a Monte-Carlo estimate
   (band ~ C/√N), so L1 properties are **statistical** (shape + band-scaling + foil-zero), not
   exact identities. Confirm L1 should assert the statistical contract (band shrinks as 1/√N,
   RR_CORR≡0 on an independent-bit foil) rather than an exact value. **Recommendation: yes** —
   test the *contract* (shape, band-scaling, foil-zero), keep the value under its existing gate.

3. **`carrier/joint_lindbladian` public "helpers" (`operator_support`, `restrict_operator_to_component`).**
   These do torch tolerance-scanning of operator support — pure *structure* logic, but on torch
   tensors. Classified **GPU-BOUND** (they take torch tensors and the tol-scan is the same
   numerics the assembler relies on), but the graph/union-find logic underneath is CPU-pure. If a
   CPU-tensor stub is acceptable they could move to L1. **Recommendation: leave GPU-BOUND** (they
   are only ever called on cuda tensors in the pipeline; a stub is more fragile than the existing
   `test_joint_lindbladian` coverage).

4. **`quantum_bath/memory_witness.entropic_memory_witness_{single,two_qubit}` — RETRACTED.**
   Retracted-as-witness 2026-07-06 (false-positive risk) but still public + exported. They are
   CPU-pure and testable as *diagnostics* (negativity-backflow revival), NOT as a memory witness.
   OPEN: should Stage D test them at all, or should they be de-exported first? **Recommendation:**
   test the diagnostic contract only (revival-detector fires iff ∃t1<t2 with a dip-then-rise) and
   add a docstring/`__all__` note that they are non-witness diagnostics — do NOT assert a witness
   claim. Flag to the maintainer whether de-export is preferred before release.

5. **Already-releasable-quality vs needs-work.** Agents marked essentially the whole package
   RELEASABLE **except** `frontend/axis1_mcwf_mps_execution.py` (NEEDS-WORK — mass-residual-budget
   convergence + Phase-B ledger pending) and `teachers/coupled_cycle.emit_clifford_slice`
   (intentionally `NotImplementedError`, slice-2). These are GPU-bound / deferred, so they do not
   block the CPU-pure L0/L1/L2 push; they need only the structural + "raises NotImplementedError"
   guard test. Confirm they are out-of-scope for release-completeness (only their *contract-only*
   surface is tested), matching the Wave-2 big-file out-of-scope decision (§10.5).

6. **`_dataset_files`-style load-bearing privates elsewhere.** Beyond the Wave-2-named
   `experiments._dataset_files`, the sweep surfaced load-bearing `_private` units:
   `carrier/accel._load_ext` / `_FusedLocalKraus.*` (autograd), `certify` `_assert_anchor_value`
   / `_rollup` / `_pearson_bits`, `quantum_bath` `_*` helpers behind the public checks. I included
   the load-bearing autograd + certify-rollup ones (they gate correctness) but treated the
   quantum_bath/certify `_helpers` as covered-through-their-public-caller. Confirm the policy:
   test load-bearing privates directly only when a public caller cannot reach a branch (the Wave-2
   `_dataset_files` line-110 precedent), else through the public unit. **Recommendation: through
   the public caller unless a branch is otherwise unreachable** (matches §10.2).

---

## Summary (for the caller)

- **Total public units:** **635** across **74** non-init modules (88 files incl. `__init__`).
  Split ≈ **429 CPU-PURE / 89 GPU-QUIMB-BOUND / 67 MIXED** (the ~ reflects the 6 open-question
  units; the dominant read is ~68% CPU-pure).
- **Current package coverage: ≈18%** (measured over the 59 files the Wave-2 run touched). **24
  non-init modules are at a TRUE 0%** — never imported by the Wave-2 test set: all of
  `certify/*` + `certify/anchors/*`, all of `quantum_bath/*`, `teachers/coupled_cycle.py`,
  `carrier/accel.py` + `carrier/kernels/*`, and frontend `interop`, `axis1_evidence_guard`,
  `axis1_codespec_runner`, `axis1_g2_runner`, `axis1_mcwf_dense_certification`,
  `mechanisms/seam_teachers`.
- **Biggest coverage gaps (all CPU-pure, all high-value):** the entire `quantum_bath/` package
  (44 units, 0%), the entire `certify/` + `certify/anchors/` CPU surface (~42 units, 0%),
  `frontend/interop.py` + `axis1_evidence_guard.py` (0%), `mechanisms/seam_teachers.py` (0%),
  `source/process.py` (28 units, 17%), `carrier/channels.py` (30 numpy units, 20%),
  `teachers/coupled_cycle.py` CPU core (0%).
- **Proposed Stage-D batch order:** **D1–D10 first** (all zero-coverage CPU-pure — `quantum_bath`
  → `certify` → `interop`/`evidence_guard` → `seam_teachers` → `axis1` fixtures →
  `coupled_cycle` CPU core), then **D11–D20** (low-coverage CPU-pure, largest-surface first —
  `source/process` → `source/coupling` → `carrier/channels` → the frontend IR/schema/stim/noise
  clusters → `analog_schedule` → `mechanisms` → `numerics`). GPU/QUIMB-bound units (Tier 4) stay
  on the lighter structural+KILLER+equivalence treatment and are excluded from every CPU-pure
  unit's coverage-gate line range.
