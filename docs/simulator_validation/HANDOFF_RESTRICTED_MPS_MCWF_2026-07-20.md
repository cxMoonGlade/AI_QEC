# Restricted MPS / MCWF execution ledger — 2026-07-20

## Authority and claim boundary

This file records the current restricted Axis-1 MPS/MCWF closure run on branch `Dev-F`. It
supersedes the status, gap, next-step, and terminal-gate sections of the earlier version of this
handoff and of
[`MPS_REPAIR_AND_CONSOLIDATION_PLAN_V3_2026-07-17.md`](MPS_REPAIR_AND_CONSOLIDATION_PLAN_V3_2026-07-17.md).
Git history remains the audit trail for the intake snapshot.

Read [`docs/SIMULATOR.md`](../SIMULATOR.md) first. Then use
[`CONTEXT.md`](../../CONTEXT.md), [`docs/service_status.json`](../service_status.json), the owning
frontend/MPS/PEPS READMEs, [`tests/CODEBOOK.md`](../../tests/CODEBOOK.md),
[`docs/METRICS.md`](../METRICS.md), [`docs/FAITHFULNESS_PROTOCOL.md`](../FAITHFULNESS_PROTOCOL.md),
and [`docs/NUMERICAL_PROVENANCE.md`](../NUMERICAL_PROVENANCE.md).

The restricted slice is engineering and class-(c) differential evidence for three frozen two-qubit
fixtures. It is not a complete QEC Record law, a calibrated device model, a PEPS full-record
faithfulness result, a scalability result, or a production backend. No work in this ledger
authorizes a push.

## Current phase status

| Phase | Status at source/test freeze | Evidence boundary |
|---|---|---|
| Repository boundary repairs | **GREEN** | The publication vocabulary is `prepublication artifact`; supervisor parent-environment access is statically auditable. The scope and package-release contract tests passed after the repair. |
| F2/F3 source closure and preregistration | **GREEN for implementation admission** | Primary-source notes, exact locators, project-fit audit, literature-closure packet, and preregistration exist. This admits the frozen fixtures; it does not validate a full simulator mechanism. |
| Neutral fixture family | **GREEN focused** | F1 T1, F2 number dephasing, and F3 thermal down/up are byte pinned. Exact analytic marginals are F1 `(0.5,0.25,0.75,0)`, F2 `(0.5,1,0.625,0)`, and F3 `(0.5,0.4,0.75,0.15)` in `[mx_before,mz_before,mx_after,mz_after]` order. |
| Independent dense oracle | **GREEN focused** | A simulator-independent worker hand-builds the 4x4 operators, 16x16 Lindblad superoperator, selective measurement, and reset maps. It imports no project implementation and preserves registered structural zeros exactly. |
| Registered statistical family | **GREEN focused** | A byte-pinned registry contains five statistics per fixture, 15 total, with family `alpha=0.01` and `alpha/15` allocation. One-sample joint/marginal radii are `0.0670302388436366` and `0.04421175841273293`; the two-sample joint radius is `0.1365617560712202`. |
| QuTiP baseline reproducibility | **GREEN focused** | Worker v3 binds pristine QuTiP commit/tree, installed-source/distribution identity, exact 36-package Linux-64 conda URLs with hashes, live conformance, sanitized launch, and a mode-`0700` private cache. |
| Project direct/Carrier family | **GREEN focused** | Public GPU direct and Carrier paths bind the fixture/program and emit exactly equal Record summaries. The three fixture comparisons and registered corruptions passed in pre-freeze diagnostic runs. |
| Three-leg provenance | **GREEN unit/focused** | The publishable report requires clean Git, selected/transitive sources, lock hashes, selected NumPy/Quimb/Torch conformance, runtime/project/GPU identity, and atomic file-plus-parent-`fsync` publication. Full environment lock conformance is explicitly not claimed. |
| Restricted benchmark provenance | **GREEN unit/focused** | The report binds all production owners and transitive sources, parent/worker runtime and GPU identity, selected locks, canonical atomic publication, and a same-mode hash-valid pre-vs-final comparison against the retained historical baseline. Benchmark pass remains engineering-only. |
| PEPS/FET implementation blocker | **GREEN focused; scientific gate still open** | Gauge preparation no longer mutates the verdict-driving gamma tensor. The B1_3 known-answer cut reduces stored bond dimension 12 to independent structural rank 4, reconstructs the local map, and meets the unchanged `eps_fid=1e-8` target. Focused PEPS owner tests pass. This does not establish finite-truncation full-record faithfulness. |
| Clean-head external artifacts | **PENDING until the freeze commit** | Family, three-leg, and benchmark reports require a clean worktree and must embed the freeze commit/source/lock/runtime identities. |
| Coverage | **PENDING terminal gate** | Run after artifact replay and before aggregate service. |
| Fresh-process aggregate service | **PENDING terminal gate** | The catalog now schedules the full F1/F2/F3 family as a serial-GPU external test in addition to the retained external baselines. |
| Semantic mutation | **PENDING; must run last** | Any verdict-driving edit after mutation invalidates the terminal verdict. |

“GREEN focused” means the registered implementation and falsifier boundary passed. It does not mean
that the pending clean-head artifact, coverage, service, mutation, or full scientific claim is green.

## Frozen scientific inputs

### Fixture and registry hashes

| Input | SHA-256 |
|---|---|
| F1 T1 | `72d46d517d2e880327f22148e94611aa3b3c503a4a62d8ee18cf12b2d610257b` |
| F2 number dephasing | `90604ed353b2334810d6b0af89d82da04e42f4523d47ca846652c21d0c13ca72` |
| F3 thermal down/up | `6f1691b833036201fdfcf524e3ddd52d845fc4359fac1cc9d0a0230c74621de1` |
| 15-entry registry | `3cd654e798a4c45d3bbebf51665ecffbc109f89ccb3a9eb776904236b5525d62` |
| QuTiP Linux-64 lock | `ea45011e3b8f13299cc37fb1dbed25fb988ff19963658a479a80eb787454a355` |
| QuTiP Linux-aarch64 lock (Spark) | `62506552aaa05221d88a326b0a801314556dec3732219482e9a82ea966ca0f2e` |

Platform-parallel lock supplement (2026-07-20, late): terminal execution moved to the aarch64
GB10 Spark host after the local x86_64 host's unresolved hard-reset fault (see
`outputs/simulator_validation/runtime_reset_watch/DIAGNOSTIC_LEDGER_20260720.md`). The Linux-64
explicit conda lock is unsatisfiable on aarch64 by construction, so a platform-parallel
37-package Linux-aarch64 lock was generated from the live conformant environment and registered
as the machine-selected authority in `run_qutip_mcwf_xz_comparison.py`. The QuTiP VCS identity
(pristine `external/baselines/qutip` at commit `f343ee3c…`, tree `f09c4126…`, version
`5.4.0.dev0+f343ee3`) is unchanged and identical in both locks; the exact ordered-URL
conformance gate is unchanged; unregistered machines fail closed. The Linux-64 lock remains the
authority for x86_64 execution.

All fixtures use two qubits, `n=2048`, project microstep count 40, ordered
`[X,Z,X,Z]` measurement keys `[mx_before,mz_before,mx_after,mz_after]`, and reset mask
`[true,true,false,false]`. F3 final Z is not a structural zero.

### Registered falsifiers

- F1: `sigma_minus -> sigma_plus`.
- F2: remove the required number-dephasing `sqrt(2)` normalization.
- F3: remove excitation, swap excitation/relaxation, double excitation rate, or move the target-1
  pair to target 0.
- Gauge-invariant control: a unit-modulus collapse-operator phase must remain inert.
- F1 retains the separate deterministic `m=10,20,40,80` recurrence and its wrong-no-jump-factor
  and wrong-`dt` corruptions.

The dense and QuTiP workers build from the neutral fixture, never from the production compiled
Carrier program. Project family/rate/support/schedule/program binding is a separate gate.

## Focused evidence before the freeze commit

All commands used named `tmux` sessions, `conda run -n ecs python -m pytest`, and no
`PYTHONPATH` override.

| Scope | Result |
|---|---|
| Boundary migrations | **48 passed, 3 skipped** |
| Fixture/registry/dense/provenance migrations | **targeted suites passed** |
| Dense-vs-analytic maximum cell difference | F1 `5.55e-17`; F2 `2.78e-17`; F3 `8.33e-17` |
| Diagnostic QuTiP family | all registered fixture checks passed; real-jump counts were nonzero |
| Diagnostic project family | direct and Carrier binding/Record equality passed for F1/F2/F3 |
| PEPS FET owner file | **38 passed** |
| PEPS owner trio | **69 passed** |
| Freeze-contract bundle | **144 passed, 1 skipped**; the skip is the clean-head full family replay |

Pre-freeze diagnostic report values are not final artifacts because the worktree was not yet at the
freeze commit. The terminal artifacts below are authoritative only if their embedded cleanliness,
commit, sources, locks, runtime, and content hashes validate.

## Terminal execution order and artifact locations

Do not reorder the terminal sequence:

1. Freeze source, tests, fixtures, registry, contracts, service catalog, package metadata, and docs.
2. Regenerate and check [`docs/CODE_MAP.md`](../CODE_MAP.md).
3. Commit the freeze checkpoint; verify a completely clean worktree including untracked files.
4. Generate the full family artifact:
   `outputs/simulator_validation/mcwf_xz_fixture_family/final_20260720.json`.
5. Generate the publishable three-leg artifact:
   `outputs/simulator_validation/diagnostics/mps_three_leg_comparator/final_20260720.json`.
6. Generate the full benchmark artifact with
   `outputs/simulator_validation/benchmarks/restricted_mps/final_fa5b0d6.json` as the formal
   historical baseline:
   `outputs/simulator_validation/benchmarks/restricted_mps/final_20260720.json`.
7. Run `tests/_support/restricted_mps_coverage_targets.json`.
8. Run the fresh-process service supervisor into
   `outputs/simulator_validation/service_acceptance/restricted_mps_final_20260720/`.
9. Run `tests/_support/restricted_mps_mutation_suite.json` last.

Every report must be read from its schema and embedded identities; filename presence is not a pass.
Outputs remain local unless separately authorized.

## Canonical commands

```bash
tmux new-session -d -s ecs_code_map_final +  'conda run -n ecs python tools/gen_code_map.py && +   conda run -n ecs python tools/gen_code_map.py --check'

tmux new-session -d -s ecs_mcwf_family_final +  'CUDA_VISIBLE_DEVICES=0 conda run -n ecs python +   scripts/external_baselines/run_mcwf_xz_fixture_family_comparison.py +   --output outputs/simulator_validation/mcwf_xz_fixture_family/final_20260720.json'

tmux new-session -d -s ecs_three_leg_final +  'CUDA_VISIBLE_DEVICES=0 conda run -n ecs python +   scripts/mps_three_leg_comparator.py +   --output outputs/simulator_validation/diagnostics/mps_three_leg_comparator/final_20260720.json'

tmux new-session -d -s ecs_benchmark_final +  'CUDA_VISIBLE_DEVICES=0 conda run -n ecs python +   scripts/benchmarks/run_restricted_mps_benchmark.py --mode full +   --baseline-report outputs/simulator_validation/benchmarks/restricted_mps/final_fa5b0d6.json +   --output outputs/simulator_validation/benchmarks/restricted_mps/final_20260720.json'

tmux new-session -d -s ecs_coverage_final +  'conda run -n ecs python tests/harness/gate.py +   tests/_support/restricted_mps_coverage_targets.json'

tmux new-session -d -s ecs_service_final +  'conda run -n ecs python tests/harness/service_acceptance.py +   --log-dir outputs/simulator_validation/service_acceptance/restricted_mps_final_20260720'

tmux new-session -d -s ecs_mutation_final +  'CUDA_VISIBLE_DEVICES=0 conda run -n ecs python tests/harness/mutation.py +   tests/_support/restricted_mps_mutation_suite.json'
```

The three CUDA-bearing commands before service must run serially. The service owns its serial GPU
lane. Mutation concurrency is controlled only by its registered harness.

## Stop conditions

Stop and report RED rather than bypassing a gate if:

- evaluator-only labels or process truth appear in emitted or persisted downstream records;
- a structural zero becomes tolerance-based;
- an external oracle consumes a production compiled program;
- clean/source/lock/runtime identity is missing or disagrees with the report;
- direct and Carrier Record summaries disagree;
- any of the 15 registered statistics or corruption falsifiers fails;
- the PEPS repair requires a weaker target, an `xfail`, or removal of non-degeneracy;
- coverage or aggregate service is not green;
- a semantic mutant survives, the survivor report is missing, or its schema is stale;
- any verdict-driving source/test/fixture/registry/contract edit occurs after terminal evidence.

## Permitted completion language

Only after all terminal gates above pass:

> At the embedded clean `Dev-F` checkpoint, the restricted two-qubit Axis-1 MCWF/MPS verification
> slice passes its registered F1 T1, F2 number-dephasing, and F3 thermal down/up dense/QuTiP/project
> differential family, provenance, coverage, fresh-process service, and semantic-mutation gates.
> The PEPS B1_3 implementation blocker is repaired at its focused local FET boundary.

Even then, do not claim a production backend, complete QEC Record law, calibrated hardware model,
general trajectory coupling, scalable finite-bond accuracy, or PEPS full-record faithfulness.
