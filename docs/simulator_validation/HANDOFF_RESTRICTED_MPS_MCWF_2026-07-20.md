# Restricted MPS / MCWF handoff — 2026-07-20

## Purpose and snapshot

This is the current handoff for the restricted Axis-1 MPS/MCWF verification slice. It supersedes
the **current-status, artifact, count, next-step, and terminal-gate** paragraphs in
[`MPS_REPAIR_AND_CONSOLIDATION_PLAN_V3_2026-07-17.md`](MPS_REPAIR_AND_CONSOLIDATION_PLAN_V3_2026-07-17.md).
That plan and its phase packets remain historical implementation evidence.

- Branch: `Dev-F`.
- Code checkpoint: `76c4a2936016f845e7f07fae196ccff9cf8b6c6a`.
- The documentation checkpoint is the commit containing this file.
- Work is local only; nothing in this handoff authorizes a push.
- The user approved the directly related source fixes, semantic mutation gate, and up to four-way
  GPU parallelism. Every command must run in a named `tmux` session; `tmux` itself needs no further
  permission request.

## Read this in authority order

1. [`docs/SIMULATOR.md`](../SIMULATOR.md) — binding product and scientific contract.
2. [`CONTEXT.md`](../../CONTEXT.md) — glossary and claim boundaries.
3. [`docs/ARCHITECTURE.md`](../ARCHITECTURE.md) — current package and flow map.
4. [`docs/service_status.json`](../service_status.json) — machine-readable service contract.
5. [`docs/CODE_MAP.md`](../CODE_MAP.md) — generated inventory; regenerate after catalog/source changes.
6. [`frontend/README.md`](../../src/error_coupling_simulator/frontend/README.md) — owning frontend contract.
7. [`carrier/mps/README.md`](../../src/error_coupling_simulator/carrier/mps/README.md) — MPS mechanics contract.
8. [`tests/CODEBOOK.md`](../../tests/CODEBOOK.md) — test, coverage, and mutation map.
9. [`docs/METRICS.md`](../METRICS.md) — metric definitions and epistemic classes.
10. [`docs/FAITHFULNESS_PROTOCOL.md`](../FAITHFULNESS_PROTOCOL.md) — independent-reference rules.
11. [`docs/NUMERICAL_PROVENANCE.md`](../NUMERICAL_PROVENANCE.md) — value-level evidence rules.

Do not treat the pre-cleanup formula ledger, a dated plan's old counts, or an old output verdict as
current authority. An output is current only if its embedded Git/source identity and cleanliness
scope match the claim being made.

## Executive status

The narrow result is **GREEN at the scoped implementation and focused-test boundary**:

- restricted MCWF supports ordered X and Z measurements, including X reset and non-reset behavior;
- direct, Carrier, auto-to-MCWF, and grouped-Record paths are bound to the same sealed Record law;
- each relevant parent call compiles one Carrier program and reuses the same dictionary through the
  private execution/dynamics path;
- exact schedule, program-content, and backend identities are revalidated before CUDA and at later
  consumption/publication/return checkpoints;
- deterministic finite-step convergence and a public `m=40` GPU sample comparison pass for the one
  frozen two-qubit T1 X/Z fixture;
- canonical grouped Record publication remains fail closed and evaluator truth is not persisted.

The overall result is **not yet scientific- or production-ready**:

- the current QuTiP surface has only one T1 fixture; pure dephasing, thermal excitation, and an
  external neutral-fixture NumPy/SciPy dense worker are missing (the existing certifier-local dense
  joint-law oracle remains in place for its narrower acceptance role);
- the QuTiP baseline environment is not lock-conformant or reproducibly pinned;
- Aer, YASTN, three-leg, benchmark, coverage, aggregate service, and semantic-mutation evidence all
  predate the final source/test freeze or have not been rerun;
- the repository-wide scope-boundary suite has two current contract failures that the focused MCWF
  suites did not exercise;
- the latest aggregate service acceptance is RED because the PEPS/FET non-degeneracy test fails;
- primary-literature/source closure remains OPEN, so the engineering evidence cannot be promoted to
  a complete mechanism, full-QEC-Record, faithfulness, or calibrated production claim.

## S0–S7 progress

These labels match phases 0–7 in the historical plan.

| Stage | Scoped result | Current status | Remaining boundary |
|---|---|---|---|
| S0 | Durable RED/green evidence and owner baseline | GREEN | Old counts/artifacts are historical; regenerate terminal evidence after freeze. |
| S1 | False-green firewall and early resource safety | GREEN | No exemption is allowed in the final coverage/mutation reruns. |
| S2 | Uncapped nonlocal MCWF reference integrity | GREEN | Still restricted mechanics, not a full scientific Carrier. |
| S3 | Schedule-derived Record layout, X/Z semantics, and reset behavior | GREEN | Current external fixture is only one ordered two-qubit T1 schedule. |
| S4 | Probability, configuration, and route-support hygiene | GREEN | The no-measurement sentinel/law executes, but restricted certification/acceptance is unavailable because no input-independent linear-channel metric is registered; bounded support rules stay fail closed. |
| S5 | Consolidated Carrier mechanics | GREEN | Compile-once is Carrier-program scope only; replay may rebuild dynamics artifacts. |
| S6 | Certification ownership and public-interface cleanup | GREEN | Hand-typed implementation oracle is not literature closure or calibration. |
| S7 | Sparse sampled Record algorithm and publication | GREEN | No production scaling claim; current benchmark shows only a small local change. |

“GREEN” in this table means the stage's registered implementation/falsifier boundary passed. It does
not mean the final clean-head coverage, external-baseline, aggregate service, semantic mutation, or
scientific-source gates are green.

## Local commit ledger

The relevant local sequence is:

| Commit | Change |
|---|---|
| `1fd2813` | Fail-closed mutation evidence handling. |
| `2898eb9` | MCWF X/Z end-to-end certification. |
| `4d77d66` | QuTiP X/Z post-validation execution. |
| `d66288a` | Sequential MCWF no-jump residual bound. |
| `a6e2cd96af8000508a4b96dda2e0bb3dfea932c4` | Harden MCWF Record evidence semantics. |
| `c630904e75c5c9a5f613fa0fe10f96a412c8b2fd` | Scope allocator-override contract. |
| `38ae4c3aeec3e6d350a88a5adaf18ba1c319af7b` | Fail-closed MCWF Record publication. |
| `fa5b0d622b48ccd0cbd34a81b132e11d892d28d2` | Consume owned MCWF microstep state. |
| `b2132ea5dcd1ce935abbfd3f80707ca69aaa8702` | Reuse one sealed MCWF Carrier program per parent call. |
| `76c4a2936016f845e7f07fae196ccff9cf8b6c6a` | Persist QuTiP/MCWF X/Z finite-step convergence evidence. |

The branch was 22 commits ahead of `origin/Dev-F` at the code checkpoint. Verify rather than assuming
that count after any later local work.

## What the latest two changes establish

### Carrier compile-once and identity binding

For forced Carrier, auto-to-MCWF, grouped-Record, and public-direct calls:

- the parent compiles exactly one sealed Carrier program;
- the identical dictionary object reaches the private execution/dynamics seam;
- exact schedule-manifest SHA-256, Carrier-program content hash, and backend contract are bound;
- the identities are checked before CUDA and through selector/dynamics, Carrier authority, Record
  materialization, publication, and return checkpoints;
- seeded replay reuses the Carrier program but may independently reconstruct certified dynamics
  artifacts.

Do not widen this claim. It excludes auto-to-dense, does not prove atomic immutability against
concurrent or `mutate -> consume -> restore` changes between checkpoints, and treats the private
precompiled schedule hash as trusted internal sideband rather than an untrusted external API.

### QuTiP project comparison v3

The outer schema is `ai_qec.external_baseline.qutip_project_mcwf_xz_comparison.v3`; the isolated
worker remains v2 and its transport envelope remains v1. The frozen T1 fixture now persists:

- an independent stdlib deterministic finite-step binary recurrence for `m=10,20,40,80`;
- joint/Z TV values `0.023409825026091874`, `0.011859662816100847`,
  `0.005967971464909766`, `0.0029934385472444314`;
- directed X-after TV values `0.010275861041313533`, `0.005088283414417721`,
  `0.002531793804892407`, `0.0012628170724109378`;
- adjacent refinement-ratio gate `[1.85, 2.15]`;
- final joint/Z and X caps `0.0031` and `0.0013`;
- public `m=40`, `n=2048` sample radii `0.0640322086265546` joint and
  `0.039518987893233104` marginal;
- verdict-driving corruptions for no-jump factor `0.5 -> 1.0` and wrong `dt`;
- source/lock hashes, honest project-lock-only scope, atomic publication, and canonical content hash.

The current comparator invokes public direct and Carrier separately and then requires exact Record
equality. It does not claim those two public legs share one compiled object. The project lock does not
pin or attest the isolated QuTiP baseline environment.

## Evidence at handoff

### Revalidated current-code tests

All commands below ran through named `tmux` sessions with `conda run -n ecs python -m pytest` and no
`PYTHONPATH` override.

| Session | Scope | Result |
|---|---|---|
| `handoff_compile_cpu2_0720` | child authentication, Record-output units, Phase-1B firewall | **699 passed** in 5.22 s |
| `handoff_qutip_cpu2_0720` | QuTiP adapter/convergence, excluding public GPU | **33 passed, 2 skipped, 2 deselected** in 1.24 s |
| `handoff_compile_gpu2_0720` | Record-output GPU plus public finite-step fixture law | **4 passed** in 128.18 s |

Earlier focused runs also recorded 349 compile-related passes and 410 Phase-1B passes. Treat the
three table rows as the compact revalidation set; none substitutes for final coverage, service, or
mutation acceptance.

### Repository-wide contract audit: current RED

`handoff_scope_full_0720` ran `tests/test_scope_boundary.py` and
`tests/test_package_release_contract.py`: **21 passed, 2 failed**.

1. `test_current_source_tests_and_configs_have_no_retired_product_narrative` reports 36 uses of
   `staged` in the current MCWF atomic-publication implementation, owner docs, and tests. The scanner
   treats this filesystem-publication term as retired stage/contract vocabulary. Most affected source
   lines arrived with `38ae4c3`; this is a real vocabulary-gate mismatch even if the underlying use of
   a staging directory is intentional.
2. `test_claude_documents_exact_runtime_and_harness_environment_contracts` cannot statically resolve
   the dynamic `name` key in
   `tests/harness/service_acceptance.py`'s `_BOUND_PARENT_ENVIRONMENT` comprehension. That supervisor
   pattern arrived with `2806ac53` and predates the current MCWF checkpoint.

Resolve these without weakening the boundary: use unambiguous filesystem-publication terminology or
a narrowly justified scanner distinction, and make the supervisor's environment access statically
auditable. If the accepted environment contract changes, synchronize `CLAUDE.md`. No fix was folded
into this handoff because it would create a new source/test checkpoint and invalidate the evidence
freeze being handed over.

### Checkpoint-bound QuTiP v3 artifact

`outputs/simulator_validation/qutip_project_mcwf_xz_comparison_76c4a29.json`

- schema: `ai_qec.external_baseline.qutip_project_mcwf_xz_comparison.v3`;
- `all_checks_passed=true`;
- embedded repository commit: `76c4a2936016f845e7f07fae196ccff9cf8b6c6a`;
- embedded selected-source/whole-worktree clean status: true;
- canonical outer `content_hash`:
  `f4615fa1d20a8f76ab369ffdf2f5a0aec82c219f3f204c4c1cd4e4147edbae32`;
- file SHA-256:
  `512ae275d142749d42991f92b7d0d496877ac05f866a3e61d5bca58539abeb82`.

This is valid for the clean `76c4a29` code checkpoint at which it was generated. Relative to the
documentation/catalog checkpoint containing this handoff, it is historical checkpoint evidence, not
a final-head artifact. A later source, test, fixture, adapter, protocol, contract, or environment
change requires regeneration. It remains one-fixture differential evidence.

### Latest aggregate service result: historical RED

The latest retained canonical run is:

`outputs/simulator_validation/service_acceptance/mcwf_record_adapter_final2_20260719/`\
`run-20260720T041215.858983Z-p322562-8b8c948f/summary.json`

- schema `error_coupling_simulator.service_acceptance_run.v3`;
- overall status **FAIL**;
- 102 planned/results, 101 zero exits, one failure;
- summary SHA-256
  `1013568c9772157b09f642a2f48cb8925e108d83e83925a42fc9512db6216e3e`;
- verified snapshot
  `879119c002b8a7c4ccfd7b8775485d7182b58bf6e9e09464a26c30fcd0d554a1`.

The failure is
`tests/test_peps_fet.py::TestFetEnvWiring::test_fet_env_exercises_an_accepted_rank_reducing_writeback`:
all 16 cuts were `noop / fidelity_target_not_met`; best fidelity was `0.9834506556132135` against
strict target `0.99999999`; 108 rank attempts included 81 solver failures. The run predates
`38ae4c3`, `fa5b0d6`, `b2132ea`, and `76c4a29`, so it is neither a current aggregate pass nor a
current-head aggregate verdict.

### Historical baseline and benchmark artifacts

All paths below bind `fa5b0d6` and are diagnostic history, not final-head evidence.

| Surface | Retained artifact | Historical result | Gap before final use |
|---|---|---|---|
| Aer MPS | `outputs/simulator_validation/diagnostics/aer_mps_comparison/fa5b0d6.json` | PASS | Installed Aer-to-source/lock conformance and fuller runtime provenance are not established. |
| YASTN mass | `outputs/simulator_validation/diagnostics/yastn_mcwf_mass_comparison/fa5b0d6.json` | PASS | Missing canonical outer hash, environment/runtime identity, and parent-directory durability evidence. |
| Quimb three-leg | `outputs/simulator_validation/diagnostics/mps_three_leg_comparator/fa5b0d6.json` | PASS | Missing Git/source/transitive/runtime/lock/GPU and atomic-publication provenance. |
| QuTiP X/Z v2 | `outputs/simulator_validation/qutip_project_mcwf_xz_comparison_fa5b0d6.json` | PASS | Superseded by v3 but still only one T1 fixture; baseline lock/cache isolation remains open. |
| Restricted benchmark | `outputs/simulator_validation/benchmarks/restricted_mps/final_fa5b0d6.json` | PASS | No formal hash-bound pre/final block, full transitive source identity, GPU UUID/driver/runtime, or lock conformance. |

The benchmark's pre/post/final semantic payload hashes matched, while the measured local speed change
was only about 2–3%. It supports preservation of the measured semantics, not a significant speedup or
scaling claim.

The retained 2026-07-19 59-unit coverage log is stale after later source/test changes. The expected
current semantic-mutation survivor report does not exist. Old mutation batch/checkpoint schemas are
not reusable for the terminal verdict.

## Gap against scientific and production readiness

| Gate | Current state | Required closure |
|---|---|---|
| X/Z public mechanics | GREEN for one frozen T1 fixture | Preserve while adding mechanism fixtures. |
| Independent numerical oracle | PARTIAL | Add a neutral-fixture NumPy/SciPy dense worker independent of project compilation. |
| Mechanism coverage | RED | Add pure T2 and finite-temperature T1-down/T1-up fixtures. |
| External baseline reproducibility | RED | Pin QuTiP baseline lock/source and isolate cache; improve Aer/YASTN/Quimb provenance. |
| Benchmark provenance | RED | Bind transitive owner sources, runtime/GPU/locks, and formal pre-vs-final comparison. |
| Repository boundary tests | RED | Resolve the `staged` vocabulary collision and dynamic environment-key audit failure. |
| Current clean-head coverage | RED/stale | Rerun only after source/tests/docs/catalog freeze. |
| Aggregate service acceptance | PENDING; latest retained run RED/stale | Repair PEPS/FET non-degeneracy scientifically, then rerun the fresh-process supervisor at the new checkpoint. |
| Semantic mutation | RED/not run | Run last, after every verdict-driving file is frozen. |
| Literature/source closure | OPEN | Inspect primary papers and record exact equation/figure/table locators before claim upgrade. |

## Next work, in order

### 0. Restore the repository boundary gates

Fix and rerun the two failures recorded under “Repository-wide contract audit.” Treat them as
contract/test architecture repairs, not as permission to broadly allow retired product-stage language
or opaque environment access. These fixes change the checkpoint, so regenerate the affected focused
and provenance evidence afterward.

### 1. Close sources and preregister the new fixtures

Before writing F2/F3 experiment or comparator code, run the repository's `theory-first` sequence:
use local RAG/KG for discovery, inspect the primary papers directly, and record exact equation,
figure, or table locators for the pure-dephasing and finite-temperature master equations,
rate/normalization conventions, detailed-balance assumptions, and measurement/reset maps. Freeze a
preregistration covering the neutral fixture schema, independent reference construction, standard
metrics, prediction bands, corruption falsifiers, and bounded claim language. Retrieval hits are
routing aids, not evidence. A literature gap or failed preregistration blocks implementation.

### 2. Add F2: pure dephasing

Use the same ordered `[X, Z, X, Z]` schedule with a pure-T2 neutral fixture. This fixture must fire if
the collapse normalization loses the `sqrt(2 * gamma_phi) * n` convention (the factor-of-two failure).
Do not derive the independent reference from the production compiler or compiled Carrier program.

### 3. Add F3: thermal relaxation/excitation

Add both T1-down and T1-up collapse families. This fixture must fire when `sigma+` is removed,
confused with `sigma-`, assigned the wrong rate/normalization, or applied to the wrong target/support.
It must not require sensitivity to an overall collapse-operator sign or phase because the Lindblad
dissipator is invariant under that gauge change. Unlike the T1-only fixture, F3's final Z bit is not a
structural zero; analytic support checks must be fixture-specific.

### 4. Add an independent dense worker and a registry-driven comparison suite

- Build the dense reference from the neutral fixture with hand-built 4x4 density matrices,
  16x16 Liouvillians, collapse/projector/reset maps, NumPy, and SciPy.
- Never consume the project compiler's sealed program in this worker.
- Let external QuTiP and dense workers both build from the neutral fixture; keep a separate project
  binding gate for active families, rates, schedule identity, and program hash.
- Register five statistics per fixture: QuTiP-dense joint, project-dense joint, QuTiP-project joint,
  and two mechanism-directed marginals. With three fixtures this is 15 tests; derive the Bonferroni
  budget from the registry rather than hard-coding a denominator.
- Verdict-driving corruptions: F1 `sigma- -> sigma+`; F2 missing `sqrt(2)`; F3 removed `sigma+`,
  `sigma+ <-> sigma-`, wrong excitation rate/normalization, or wrong target/support. Do not use a
  global sign/phase mutation as a physical falsifier.

### 5. Close baseline provenance

- QuTiP: create an authoritative baseline lock/source identity, verify conformance, sanitize/cache
  isolation, and keep pristine external sources untouched.
- Three-leg: add Git cleanliness, selected and transitive source hashes, Python/NumPy/Quimb/Torch and
  package identity, honest lock-conformance flags, GPU UUID/driver/runtime status, fixture/canonical
  hashes, and parent-directory `fsync`.
- Benchmark: bind `axis1_ideal_controls.py`, `axis1_selection.py`,
  `axis1_channel_evidence.py`, `axis1_state_evidence.py`, `analog_schedule.py`, and `numerics.py`, plus
  GPU/runtime/lock evidence and a canonical pre-vs-final comparison block.

### 6. Repair PEPS/FET as a separate scientific task

Add an independent real-d3 local QR/SVD feasible-candidate known-answer test while preserving an
analytic feasible candidate. Do not lower the fidelity target, add `xfail`, delete the non-degeneracy
test, or relabel an old pre-gate pass as current. The present all-noop result is evidence of a real
release blocker.

### 7. Freeze and run terminal gates

Freeze source, tests, registries, contracts, docs, service catalog, and package metadata first.
Regenerate `CODE_MAP`, rerun affected baseline artifacts and benchmark, then coverage, then the
fresh-process aggregate service supervisor. Run semantic mutation **last**. Any later verdict-driving
change invalidates the applicable terminal evidence.

## Canonical command templates

Use unique session/output names if a listed one already exists. Do not set `PYTHONPATH`.

```bash
tmux new-session -d -s mps_focused_<stamp> \
  'conda run -n ecs python -m pytest -q \
   tests/test_mps_carrier_child_authentication.py \
   tests/test_mcwf_carrier_record_output_units.py \
   tests/test_mps_phase1b_fail_closed.py; exec bash'

tmux new-session -d -s mps_gpu_<stamp> \
  'CUDA_VISIBLE_DEVICES=0 conda run -n ecs python -m pytest -q \
   tests/test_mcwf_carrier_record_output_gpu.py \
   tests/test_axis1_mcwf_convergence.py::test_public_gpu_xz_records_match_the_finite_step_fixture_law; \
   exec bash'

tmux new-session -d -s qutip_v3_<stamp> \
  'CUDA_VISIBLE_DEVICES=0 conda run -n ecs python \
   scripts/external_baselines/run_qutip_mcwf_xz_comparison.py \
   --fixture scripts/external_baselines/fixtures/qutip_mcwf_xz_two_qubit_t1.json \
   --output outputs/simulator_validation/qutip_project_mcwf_xz_comparison_<commit>.json; \
   exec bash'

tmux new-session -d -s code_map_<stamp> \
  'conda run -n ecs python tools/gen_code_map.py && \
   conda run -n ecs python tools/gen_code_map.py --check; exec bash'

tmux new-session -d -s mps_coverage_<stamp> \
  'conda run -n ecs python tests/harness/gate.py \
   tests/_support/restricted_mps_coverage_targets.json; exec bash'

tmux new-session -d -s service_acceptance_<stamp> \
  'conda run -n ecs python tests/harness/service_acceptance.py \
   --log-dir outputs/simulator_validation/service_acceptance/restricted_mps_final_<stamp>; \
   exec bash'

tmux new-session -d -s mps_mutation_<stamp> \
  'CUDA_VISIBLE_DEVICES=0 conda run -n ecs python tests/harness/mutation.py \
   tests/_support/restricted_mps_mutation_suite.json; exec bash'
```

Operational traps:

- invoke tests as `conda run -n ecs python -m pytest`, not bare `conda run -n ecs pytest`;
- the coverage and mutation harness positional arguments are registries; `--help` is not a supported
  discovery call and is interpreted as a registry path;
- use the fresh-process service supervisor for aggregate acceptance;
- GPU0 is the device verified in this session. Service acceptance remains serial-GPU. The approved
  four-way parallelism is suitable for the mutation harness's registered workers, not overlapping
  independent GPU jobs;
- verify CUDA/NVML inside the process before diagnosing wrapper-level visibility;
- external baseline repositories remain pristine; adapters belong in this repository.

## Stop conditions and claim language

Stop and report RED rather than bypassing a gate if any of these occurs:

- evaluator-only labels or process truth appear in emitted records or persisted downstream evidence;
- a structural zero becomes tolerance-based or a required structural-zero bit gains support;
- a baseline or dense oracle begins consuming the production compiled program;
- a clean/source/lock/runtime identity is unavailable but the artifact claims it;
- a PEPS/FET workaround weakens the strict target or removes the non-degeneracy requirement;
- a semantic mutation survives, the survivor report is missing, or its schema is stale;
- a post-freeze edit occurs after coverage/service/mutation evidence was generated.

Allowed wording now:

> The restricted two-qubit MCWF/MPS verification slice supports ordered X/Z Record mechanics and
> passes its focused compile-once, identity-binding, finite-step, and one-fixture QuTiP differential
> checks at code checkpoint `76c4a29`.

Disallowed wording now includes “production backend,” “complete QEC Record law,” “scientifically
validated noise model,” “QuTiP-reproducible environment,” “aggregate acceptance passed,” or “final
semantic mutation gate passed.”

## Definition of a complete next handoff

The next handoff may upgrade the status only when source closure and preregistration pass and it links
hash-bound artifacts for all three fixtures and the independent dense oracle, current baseline/benchmark provenance, a current
clean-head coverage report, a current fresh-process aggregate result, the PEPS/FET disposition, and
the final semantic-mutation survivor report. The repository boundary and package-release suites must
also pass. It must continue separating scoped engineering evidence, external differential evidence,
source closure, and production acceptance.
