# Simulator current-core cleanup audit — 2026-07-14

This is the working ledger for the approved current-core cleanup. It is not a scientific
authority and it does not preserve retired product history. Each phase is closed only after its
listed gate passes. Git history is the archive.

## Frozen pre-cleanup boundary

- repository: `/home/cx/AI_QEC/AI_QEC`
- branch: `Dev-F`
- HEAD: `844d211a6fba28784b890c1638884a1efa4377be`
- pre-existing worktree item preserved: `docs/SCIENTIFIC_FORMULA_PROVENANCE.md` (untracked at
  cleanup start)
- installed Python modules: 109
- native sources: 4
- canonical acceptance files: 52
- tracked legacy implementation files: 101, plus the tracked `src/qec_twin` symlink
- tracked test modules: 128
- tracked validation/working/literature-note files at intake:
  - `docs/twin_validation/`: 159
  - `docs/nonpauli_teacher/`: 30
  - `docs/papers/reading_notes/`: 246
- files matching at least one retired namespace/taxonomy/API marker across source, tests,
  configuration, and active documentation: 420

The module/native/acceptance counts are an intake snapshot, not preservation targets.

## Current Phase-4 implementation snapshot

- cleanup checkpoint: `4e04435` (`clean up`), based on intake commit `844d211`;
- current installed Python modules: 104;
- current native sources: 4;
- current worktree top-level test modules: 98;
- current service catalog: 27 services and 71 unique acceptance files;
- acceptance lanes: 29 `cpu_light`, 7 `cpu_exclusive`, and 35 `gpu_serial` files;
- current coverage/mutation configuration: 28 neutral `*_coverage_targets.json`
  registries; no stage-numbered registry remains.

These are an authority-reset checkpoint, not the final Phase-7 inventory. The service catalog now
uses `classical_finite_rtn_source_chain`; the retained finite-RTN research diagnostic is a separate
free-induction object and does not assign CP-divisibility to the production source, channel, or
record. The temporary file-level test-disposition document has been removed after its count and
decision summary were folded into this ledger; Git remains the only old-script archive.

## Authority and trust boundary during cleanup

- Runtime truth is established from the directly reachable
  `src/error_coupling_simulator/` implementation and its current consumers.
- `docs/SCIENTIFIC_FORMULA_PROVENANCE.md` is pre-cleanup evidence. Its source hashes and reverse
  coverage become stale whenever an audited source changes.
- Existing RAG, KG, project-synthesis reading-note sections, historical output artifacts, and
  retired validation documents are discovery material only until rebuilt from current
  paper-fact records.
- A retained scientific object must have all four: a current runtime consumer, a current owner,
  primary-source or complete project derivation provenance, and a current acceptance test.
- No compatibility shim, alias, dual reader, frozen old schema, or in-repository archive is an
  accepted retention reason.

## Scope correction — retain PEPO, rebuild tests from current owners

The user narrowed the cleanup boundary after the initial Phase 3 pass: this operation targets the
retired Twin product line only. PEPO is a retained scientific implementation. The attempted PEPO
excision and subsequent PEPS/FET diagnosis were stopped and restored from the intake HEAD; no
PEPS/FET scientific fix from that interrupted out-of-scope diagnosis is retained.

The later test-evidence clarification distinguishes implementation, executable tests, and run
records:

- all 128 tracked `tests/test_*.py` intake files are executable pytest scripts, not test results;
- `tests/_support/*.json` files are executable coverage/allowlist registries, not results;
- Git commit `844d211a6fba28784b890c1638884a1efa4377be` is the exact joint snapshot of the
  old scripts, the 101-file retired implementation, and the `src/qec_twin` symlink, so Git is the
  only required archive;
- old scripts with no current owner may be deleted; tests that protect a retained PEPO/PEPS or
  current simulator invariant must first be rewritten against current owners and current physical
  names;
- old PASS records do not prove the renovated source. The renovated source and renovated tests
  must be rerun, and their new records must bind the complete source/test/data/environment state.

The first `27 / 17 / 3 / 2` script classification was an intake estimate without a member list and
could not close against the actual diff. It is superseded by a complete file-level manifest:

```text
128 intake tests = 19 byte-identical + 62 same-path/current-owner edits
                 + 27 deleted ownerless + 20 deleted/replaced
98 current tests = 19 + 62 + 17 newly named current-owner tests
```

Five retired support JSON registries were deleted, not four. PEPO remains retained: its monolithic
test was split into current owner groups and fresh-process helpers. The two host-seam files remain as
negative retired-namespace gates. PEPS/FET tests were migrated off the retired API without accepting
or masking the known entropy failure. Static, AST, subprocess-import, old-schema-rejection, package,
and service-plan gates now prove that the renovated source and tests do not depend on a retired API.

## Phase 3 working findings — execution isolation and retained carriers

The earlier exit-139 execution-layer repair has **not** been reverted. Against intake HEAD
`844d211`, `tests/harness/proc.py`, `tests/harness/gpu_pool.py`, and
`tests/harness_config.json` remain byte-identical. The only intentional change in
`tests/harness/service_acceptance.py` before the current catalog edits was the log root migration
from the retired output tree to `outputs/simulator_validation/`. The following properties remain
enforced:

- the supervisor imports no Torch/CUDA runtime;
- each acceptance file is a fresh exec process;
- `cpu_light` is bounded by four workers and `MemAvailable`, `cpu_exclusive` is serial, and
  `gpu_serial` alone holds the cross-process `flock` lease;
- CUDA-Q remains routed to the `aiqec` environment;
- task/environment plans are immutable and the single parent writer publishes `summary.json`
  atomically;
- child process groups, signal handling, registration cleanup, and orphan detection remain active.

The execution-layer regression tests passed (`14 passed`), and the process self-test passed all
three cases with no orphan. Git history identifies intake HEAD `844d211` as the 881-line execution
repair itself; `proc.py`, `gpu_pool.py`, and `harness_config.json` remain byte-identical to that
commit. The repair was not reverted.

The first retained-carrier run appeared to expose a PEPO allocator omission. The historical runner
used PyTorch expandable segments, while the generic service-acceptance catalog had not encoded that
child-process setting. Three split high-memory cases run from an otherwise idle GPU passed with
`PYTORCH_ALLOC_CONF=expandable_segments:True` in 528.12 s, 121.75 s, and 60.70 s, while nearby runs
without it exited 139 in 4--7 s. The catalog therefore recorded the setting on the eight GPU PEPO
owner files and kept it private to each child.

Later controlled repetitions **falsified allocator choice as either the root cause or an accepted
remedy**. Native, expandable-segment, and `cudaMallocAsync` configurations have all produced the
same exit 139; each has also produced clean passes. The setting remains visible in the current
catalog only as the tested historical execution condition, not as evidence that the fault is fixed.
The completed R580 gate below does not change that interpretation: its reference-only and full A/B
stages passed with `PYTORCH_ALLOC_CONF` unset, while the catalog-driven PEPO owner lane passed under
its recorded expandable-segment child setting. Allocator policy remains an independent execution
contract, not the exit-139 repair.

A catalog-driven run recorded the
main 47-case carrier file passing, followed by three fresh processes exiting 139 after 66.20 s,
15.06 s, and 6.31 s. A dedicated follow-up proved that the main process completed 47 tests plus an
explicit `torch.cuda.synchronize()` / `empty_cache()` epilogue; its process group and CUDA compute
PID disappeared, the GPU had an approximately 1.4 s no-compute interval, and only then did the
successor create a context. The successor still exited 139. Normal conda process overlap, a missing
end-of-session synchronize, fixed sleeps, and a simple GPU-idle threshold are therefore rejected as
causes or remedies. Older PEPO logs already contain `CUDA driver error: device not ready` on the
same product line, so a historical single 50-pass run is not evidence that the old runner was
stable.

The renovated tests revealed avoidable execution pollution: the compressed-cap and NTU
pre-cut cases constructed and evolved a roughly 5.77-GiB exact density matrix and immediately
deleted it without using it in any assertion. They now build the identical deterministic PEPO
state/token program without that unused mirror. The nonselective-round case now retains its
independent exact reference without overlapping CUDA lifetimes: child A builds and publishes the
`19683 x 19683` complex128 reference plus a source/input/configuration-bound manifest; child A
exits; child B reconstructs PEPO, executes the unchanged two rounds at `D_cap=8`, and compares in
256-row blocks. The 6,198,727,952-byte array is deleted after each run, while the small manifest and
result can remain as evidence. No physical map, assertion, tolerance, or corruption falsifier
changed. A completed comparison recorded 22 binding NTU entries and
`max_abs_difference=0.0011016668648880863 <= 0.01`.

The process launcher hardening is complete. Process-group cleanup is now explicitly verified
before unregistering; `Ran.ok` and service results require that proof; summary schema v2 records
`group_cleanup_verified`; and timeout, unverifiable cleanup, SIGABRT, or SIGSEGV stops further GPU
admission even in the default mode. Ordinary safely reaped pytest failures still continue unless
`--stop-on-failure` is selected. Focused harness tests pass. This contains a native failure but is
not presented as its root-cause repair.

The same canonical run found a separate current PEPS/FET scientific failure: five tests passed,
but `test_fet_env_round_preserves_stabilizer_entropy` produced
`S_A=0.10860941571062639` against the independent GF(2) reference `2.0` with tolerance `1e-4`.
This is not an execution-layer exit 139 and is outside the Twin API cleanup. No tolerance, FET
formula, or entropy expectation is weakened here; the failure remains a visible PEPS scientific
blocker.

### P0 native-crash diagnosis — R580 A/B stress gate passed

The exit-139 feedback loop is now smaller than PEPO. The same source-hashed current
`tests/_support/pepo_nonselective_worker.py reference` command alone reproduces the fault before a
PEPO state, NTU update, SVD, or repository custom CUDA extension is created. The most recent Python
frames drift among the 3-by-3 qutrit Hadamard construction, POVM diagonal construction, and
measurement rotate-forward/rotate-back sites in `carrier/exact/qutrit_dm.py`. A deterministic
source and input can pass and then fail in a later fresh process; the Python frame is therefore an
asynchronous exposure point, not a demonstrated faulty formula.

The controlled runtime matrix used the same RTX 5090, driver 595.71.05, source hashes, four input
hashes, configuration hash, and output hash. Every successful reference published array SHA256
`241f4c3b810100bf69659da68b5bb16f3454fcd708b78cc46ddf902bef793129`:

| PyTorch build | user CUDA | reference-only fresh execs | result |
|---|---:|---:|---|
| 2.12.0, git `7661cd9` (canonical `ecs`) | 13.0 | 3 PASS, then 1 SIGSEGV | FAIL |
| 2.11.0, git `70d99e9` | 13.0 | first exec SIGSEGV | FAIL |
| 2.12.0, git `7661cd9` | 13.2 | 4 PASS, then 1 SIGSEGV | FAIL |
| 2.11.0, git `70d99e9` | 12.8 | 6 PASS, then 1 SIGSEGV | FAIL |

The CUDA 12.8 environment also completed one full fresh-reference -> fresh-PEPO comparison, but its
later reference-only SIGSEGV proves that run was an intermittent PASS, not a remedy. Switching
PyTorch, CUDA minor version, allocator backend, launch blocking, or fresh-process topology does not
close the fault.

Live `/proc/<pid>/maps` checks show one internally consistent user-space CUDA library tree in each
environment and only the required system `libcuda.so.595.71.05`; no process mixed cu12 and cu13
libraries. The active kernel module, user driver, and GSP firmware are all 595.71.05. A retained
580-series firmware package is inactive (`GSP Firmware Version: 595.71.05`) and is not a dependency
conflict. `pip check` passes in canonical `ecs` and `aiqec`, which contain the same Torch/CUDA build.

Two kernel-recorded crashes resolve to the identical stripped
`libcuda.so.595.71.05 + 0x415c48` instruction; later events are confirmed SIGSEGV by Apport but lack
kernel PCs. Core limit zero plus Apport's rejection of Conda Python means no core was persisted. A
live GDB run passed once and therefore did not capture the intermittent fault. No run has emitted an
NVRM Xid, PCIe/AER error, recovery action, or hardware-temperature warning. Compute Sanitizer found
zero device memory errors through a full reference/PEPO round when the incompatible
expandable-segment instrumentation path was disabled.

NVIDIA's own 595.71.05 release notes document a Blackwell driver defect that can sporadically
misconfigure TMA descriptors for certain backing allocations below 128 KiB and cause illegal memory
accesses or Xid 13. The repository path has not been proved to call the affected API, so this is
corroborating driver evidence, not an exact causal identification. The latest R580 maintenance
release available to this host, 580.173.02, supports CUDA 13.x and does not list that TMA defect;
absence from its known-issues list is likewise not proof. A package-manager dry run shows that a
580.173.02 A/B requires replacing the complete 595 open-driver user/kernel stack and rebooting. The
user authorized and performed that replacement and reboot on 2026-07-15.

The post-reboot execution stack was internally consistent before GPU admission: RTX 5090 driver,
open kernel modules, system `libcuda`, NVML, and GSP firmware all reported 580.173.02; the active
module vermagic matched kernel `6.17.0-40-generic`, its signer matched the enrolled Secure Boot MOK,
and the current boot contained no Xid, GSP/MMU/UVM fault, AER error, recovery, or signature failure.
The canonical `ecs` environment mapped PyTorch 2.12.0+cu130 and all CUDA 13 user libraries from the
locked environment plus only system `libcuda.so.580.173.02`. `pip check` and the core-environment
contract passed after re-synchronizing the current checkout's editable-package metadata; no source
or dependency version changed.

Two post-reboot observations are recorded but do not block this gate. Versioned inactive 580/595
firmware directories and NVIDIA's unversioned 610-series utility packages remain installed, but
neither appears in the active kernel/`libcuda`/GSP execution chain. The RTX 5090 currently negotiates
PCIe 16.0 GT/s x4 although the device can support 32.0 GT/s x16; with all AER counters at zero this
was a separate performance/platform observation, not evidence for the exit-139 cause. After the user
corrected the physical slot on 2026-07-15, sysfs reports current width x16, maximum width x16, and a
maximum 32.0 GT/s link. The idle link downshifts to 2.5 GT/s (Gen1) while retaining x16 width. The x4
performance follow-up is resolved and remains unrelated to the native crash.

The predeclared driver-candidate gate then passed without changing a scientific tolerance or source
formula:

1. **Reference-only:** 20/20 consecutive fresh execs passed with the default allocator. Every
   6,198,727,952-byte exact-reference array had SHA256
   `241f4c3b810100bf69659da68b5bb16f3454fcd708b78cc46ddf902bef793129`; elapsed time was 23--24 s
   per process. The large arrays were deleted after their source-bound manifests were recorded.
2. **Full two-child A/B:** 3/3 consecutive fresh-reference -> fresh-PEPO comparisons passed at the
   unchanged two rounds, `D_cap=8`, and `max_abs_limit=0.01`. All three produced 22 binding NTU
   entries and the identical `max_abs_difference=0.0029731254318278552`; each pair took 137--138 s.
3. **Current PEPO service:** all ten catalog acceptance files passed as fresh processes: two CPU
   boundary files and eight GPU-serial owner files. Every result recorded return code zero,
   `timed_out=false`, and `group_cleanup_verified=true`; the high-memory compressed-cap file ran
   528.12 s and the independent nonselective comparison ran 137.85 s.

After all three stages, there was no compute process, no new Xid/native-fault/kernel-recovery log,
and PCIe AER correctable, nonfatal, and fatal totals remained zero. R580.173.02 therefore **passes
the defined stress gate and removes the Phase-3 P0 execution blocker**. Because the failure was
intermittent and the repository path was never tied to NVIDIA's documented TMA condition, this is
strong causal A/B evidence against the 595.71.05 execution stack, not proof of one exact driver
defect and not a claim of unlimited future stability. The fresh-exec, fail-closed admission, process
cleanup, and GPU-flock protections remain required.

Current evidence records:

- `outputs/simulator_validation/logs/service_acceptance/pepo_peps_current/`
  `run-20260715T032939.224991Z-p2072177-1e92849c/summary.json`
- `outputs/simulator_validation/logs/service_acceptance/pepo_139_minimal/`
  `run-20260715T034001.115857Z-p2084296-16cc4dad/summary.json`
- `outputs/simulator_validation/logs/service_acceptance/pepo_expandable_segments_ab/`
  `run-20260715T043220.452789Z-p2124028-bfd875f7/summary.json`
- `outputs/simulator_validation/logs/service_acceptance/pepo_catalog_contract/`
  `run-20260715T044615.101300Z-p2131185-ee9893de/summary.json`
- `outputs/simulator_validation/logs/service_acceptance/pepo_main_then_lean_ntu/`
  `run-20260715T050835.366456Z-p2149606-6223d397/summary.json`
- `outputs/simulator_validation/logs/service_acceptance/pepo_nonselective_cuda_malloc_async_repeat/`
  `run-20260715T060812.515032Z-p2189677-70f490fe/summary.json`
- `outputs/simulator_validation/diagnostics/cu128_t211_full_ab_01/reference.json`
- `outputs/simulator_validation/diagnostics/cu128_t211_full_ab_01/result.json`
- `outputs/simulator_validation/diagnostics/cu130_live_gdb_01/gdb.log`
- `outputs/simulator_validation/diagnostics/r580_173_02_reference_gate/gate.txt`
- `outputs/simulator_validation/diagnostics/r580_173_02_reference_gate/summary.tsv`
- `outputs/simulator_validation/diagnostics/r580_173_02_full_ab_gate/gate.txt`
- `outputs/simulator_validation/diagnostics/r580_173_02_full_ab_gate/summary.tsv`
- `outputs/simulator_validation/diagnostics/r580_173_02_pepo_service_gate/`
  `run-20260715T145925.497231Z-p14250-8ff67cd0/summary.json`

## Phase 4 authority reset

The tracked current authority has been rebuilt from current owners rather than renamed from the
retired documentation. The binding surface is now `docs/SIMULATOR.md`, `CLAUDE.md`, `CONTEXT.md`,
`docs/ARCHITECTURE.md`, `docs/METRICS.md`, `docs/FAITHFULNESS_PROTOCOL.md`,
`docs/NUMERICAL_PROVENANCE.md`, `docs/service_status.json`, generated `docs/CODE_MAP.md`,
`tests/CODEBOOK.md`, and the current module/validation READMEs named by the scope gate.

The retired documentation surface was removed rather than archived in the repository:

- 159 files under the old product-validation tree;
- 30 files under the old role-named carrier tree;
- 9 white-box files, 8 CF-WR files, and 8 repository archive files;
- four historical ADRs, the old migration guide, and one tracked build skill whose only contract
  target was the deleted validation tree.

The retained source/test surface was then made current-only:

- certification no longer exposes injectable private reference probabilities, level
  distributions, Kraus stacks, or superoperators; it always constructs the current independent
  reference and requires the explicit `passed_gross` field;
- `RunSpec` defaults to final/c128, while c64 requires explicit
  `run_purpose="optimization"`; no implicit precision compatibility remains;
- the duration policy is `DEFAULT_DURATION_POLICY_ID` /
  `default_duration_policy()` with schema
  `error_coupling_simulator.frontend.duration_policy.v1`; the old names do not resolve;
- 28 coverage registries use physical/current owner names and the mutation-only environment key is
  `ECS_MUTATION_SKIP_SLOW`;
- the PEPO negativity diagnostics, PEPS carrier tests, Axis-1 dense-reference tests, and transient
  Markov closed-form reference use descriptive names; retired numbered/stage labels are absent;
- the zero-consumer PEPS one-site alias, the zero-consumer schedule helper, the unowned PEPS
  diagnostic environment branch, and an exact duplicate interop test were deleted without a
  compatibility fallback;
- qutrit subspace-rate targets and leaked-readout bias are recorded as project-design coordinates
  with cross-protocol scale context only. The two-site leakage level-map source-to-row audit remains
  explicitly pending; its implementation test is not promoted into a physical-mechanism claim.

The source semantic-diff audit found no added numeric literal in any changed Python source. Removed
numeric literals occur only inside the deleted unowned PEPS diagnostic branch, deleted private
certification injection paths, and a deleted no-consumer acceptance helper. The native CUDA diff is
comment-only. No physical formula, threshold, tolerance, or retained PEPO/PEPS execution operation
was changed by the authority reset. The existing PEPS/FET entropy failure remains visible at
`0.10860941571062639` versus `2.0` with tolerance `1e-4`.

Phase 4 closes only the tracked current authority and current source/test vocabulary. Existing
reading notes, local RAG/KG material, and ignored local old-product skills/workflows remain
quarantined and untrusted. In particular, the ignored local project-engine skill/workflow and old
retrieval commands are not current authority and must appear in the Phase-6 dry-run deletion
manifest; literature commands are rebuilt in Phase 5 before use. This explicit quarantine is not a
claim that those later phases are complete.

## Phase 5B1 feedback into P0 — qutrit leakage hard cut

The first clean-room DOI/VOR read reopened one supposedly closed P0 item. The implementation had
attached an author name and channel-level coherence interpretation to a project-declared
exchange/seepage/heating channel. Its `coherence_of_leakage` value was actually the trace norm of the
cross-subspace block of `E(|1><1|)` for one fixed input, not the paper's Haar-averaged channel
coherent-leakage rate. A pure exchange at `theta=pi/2` is the decisive counterexample: this fixed-input
quantity is zero even though the exchange generator remains nonzero. The old if-and-only-if causal
wording and `C_L` manifest field were therefore withdrawn.

The correction is a hard cut, with no aliases or readers for the old surface:

- the retained operations are `leakage_seepage_rates`,
  `level1_output_leakage_coherence`, and
  `solve_exchange_angle_for_leakage_rate`;
- qutrit frontend, MCWF, preset, and run-provenance schemas moved to their current neutral `v2`
  families;
- the solver now scans for a bracket before direction-independent bisection, preserves an exact zero
  target, rejects invalid controls and unreachable targets, and never returns an unverified midpoint;
- the source-coupling `v2` contract deletes the zero-consumer source-to-qutrit fan-out rather than
  renaming it. Source processes and qutrit leakage remain separate current owners;
- service metadata, package exports, current authority documents, native comments, retained
  PEPO/PEPS fixtures, and generated `CODE_MAP.md` use descriptive physical-operation names.

The scoped hard-cut evidence is green: 192 focused CPU tests passed; the qutrit owner registry covers
all 10 canonical units at 100% statement and branch coverage; 2,228 tests collect; the scope/import,
old-schema, old-symbol, M0--M34, package, service, and code-map checks pass. A targeted nine-file
fresh-GPU run passed eight current owners and reproduced only the pre-existing PEPS/FET entropy
failure.

The complete 71-file service surface was then exercised in two disjoint parts. The first supervisor
run completed 49 files, including the 527.85-second compressed-cap PEPO owner, before interactive
steering terminated the supervisor as it admitted file 50; it produced no aggregate summary and is
not represented as a complete canonical run. A new supervisor run covered the remaining 22 files and
atomically recorded 21 passes plus the same PEPS/FET failure, with every process group verified
clean. Across the two parts, 70 files passed, no process exited 139, and no Xid/native fault or orphan
was observed. The global service gate remains red solely because the retained out-of-scope PEPS/FET
entropy check remains red; no skip, allowlist, tolerance change, or compatibility layer was added.

Current execution records:

- `outputs/simulator_validation/logs/service_acceptance/qutrit_hardcut_targeted/`
  `run-20260715T225920.098557Z-p201968-51210bc4/summary.json`;
- interrupted, no-summary prefix:
  `outputs/simulator_validation/logs/service_acceptance/qutrit_hardcut_full/`
  `run-20260715T230135.672845Z-p203678-fa3800a3/`;
- atomic remainder:
  `outputs/simulator_validation/logs/service_acceptance/qutrit_hardcut_full_remainder/`
  `run-20260715T233556.319047Z-p6697-43c86417/summary.json`.

## Phase ledger

| phase | status | required outcome |
|---|---|---|
| 1 — boundary freeze | complete | intake inventory and trust boundary recorded |
| 2 — P0 repair | complete; 5B1 reopening closed | retired dispatcher deleted; retained record, packed bridge, Born probability, PTM, certification, coupled-process, and corrected qutrit-leakage owners pass independent falsifiers |
| 3 — Twin-only implementation hard cut | complete | retired implementation removed; all 128 intake tests reconciled; retained tests use current owners; static/subprocess/schema/package gates prove no retired runtime dependency |
| 4 — authority reset | complete | current-only tracked authority; unsupported scientific claims withdrawn or explicitly pending |
| 5 — literature reset | in progress | Phase 5A fail-closed cut complete; Phase 5B1 admits the first DOI/VOR clean-room note; remaining load-bearing sources remain |
| 6 — output cleanup | pending | dry-run manifest, targeted purge, current artifact regeneration |
| 7 — inventory and acceptance | pending | zero-reference scans, rebuilt catalogs, full engineering gates |
| 8 — formula audit restart | pending | current manifest frozen and sequential audit resumed |

## Phase 2 P0 dispositions

| finding | completed disposition | gate result |
|---|---|---|
| Record arrays were narrowed before binary validation and remained writable | validate original integer/bool values before conversion; make copied arrays contiguous and read-only | PASS: wide, fractional, non-finite, mutation, and ownership falsifiers |
| Packed carrier records accepted non-byte/fractional payloads and under-specified their layout | require the current schema, exact byte layout, all-zero detector prior, binary logical byte, zero padding, and immutable payload | PASS: adversarial layout/payload tests and producer-consumer round trip |
| Z-basis Born probabilities used a per-outcome numerical floor | preserve structural zeros; reject non-finite, non-Hermitian, non-PSD, and non-positive-trace inputs | PASS: exact-zero and invalid-state falsifiers |
| PTM off-diagonal structure was described as a general coherent-error certificate | restrict interpretation to basis-specific non-Pauli structure | PASS: hand-typed amplitude-damping counterexample |
| Retired numbered mechanism dispatcher was certified by the channel-algebra gate | delete dispatcher/catalog, compatibility adapters, fixtures, registries, and their tests | PASS: active-source retired-symbol scan is empty; physical primitives retain named owner tests |
| Retired scientific names remained attached to certification, coupled-process, and qutrit-leakage owners | expose only neutral process/fixture APIs and descriptively named qutrit leakage operations | PASS: defining APIs plus 100% statement/branch owner gates |

## Phase-gate log

Append one dated row per completed gate. A failed gate remains visible until repaired.

| UTC timestamp | phase | command/check | result | evidence |
|---|---|---|---|---|
| 2026-07-14 | 1 | repository safety preflight and tracked inventory | PASS | clean tracked worktree; one preserved untracked provenance ledger |
| 2026-07-14 | 2 | focused P0 test batch | PASS | 191 passed |
| 2026-07-14 | 2 | qutrit-leakage owner gate | PASS | 10/10 public units; 100% statement and branch coverage |
| 2026-07-14 | 2 | certification owner gate | PASS | 25/25 public units; 100% statement and branch coverage |
| 2026-07-14 | 2 | coupled-process owner gate | PASS | 17/17 registered units; 100% statement and branch coverage |
| 2026-07-14 | 2 | active-source retired API/import scan | PASS | no MechanismSpec, mechanism_channel, old aliases, or deleted module imports |
| 2026-07-14 | 3 | legacy implementation and symlink removal | PASS | 101 tracked legacy files and the tracked compatibility symlink deleted; no repository archive retained |
| 2026-07-14 | 3 | attempted historical-test retirement | REVOKED | all deleted historical tests and support registries restored; tracked top-level test inventory is again 128 |
| 2026-07-14 | 3 | attempted PEPO retirement | REVOKED | PEPO source, PEPS integration, and PEPO/PEPS tests restored exactly from intake HEAD |
| 2026-07-14 | 3 | out-of-scope PEPS/FET diagnosis | STOPPED | temporary instrumentation and attempted FET algorithm/tolerance change removed; later PEPS/FET diffs are terminology/API migrations only |
| 2026-07-14 | 3 | historical test/record classification | PASS | all tracked tests are scripts; old source+script snapshot is recoverable from `844d211`; support JSON files are registries, not results |
| 2026-07-14 | 3 | initial ownerless-test removal | PARTIAL/SUPERSEDED | initial estimate removed 27 ownerless scripts; the final manifest records 46 removed tests, 18 current additions relative to intake, and five removed registries |
| 2026-07-14 | 3 | native-crash runtime matrix | FAIL | exact-reference-only SIGSEGV reproduced under CUDA 12.8, 13.0, and 13.2; dependency mixing, PEPO NTU/SVD, custom kernels, and allocator choice rejected as sufficient explanations |
| 2026-07-14 | 3 | R580.173.02 package dry run | PENDING AUTHORIZATION | compatible CUDA 13.x driver candidate identified; no package or running driver changed; reboot plus post-change stress gate required |
| 2026-07-15 | 3 | R580.173.02 post-reboot stack audit | PASS | active kernel modules, `libcuda`, NVML, and GSP all 580.173.02; Secure Boot signature valid; canonical PyTorch 2.12.0+cu130 map and core-environment contract clean |
| 2026-07-15 | 3 | R580 reference-only stress gate | PASS | 20/20 fresh execs; identical exact-array SHA256; 23--24 s each; default allocator; no kernel fault |
| 2026-07-15 | 3 | R580 full reference-to-PEPO A/B gate | PASS | 3/3 fresh two-child comparisons; identical max-absolute difference 0.0029731254318278552 <= 0.01; 22 binding NTU entries |
| 2026-07-15 | 3 | current PEPO service acceptance | PASS | 10/10 fresh files, including 8/8 gpu_serial owners; all process groups verified cleaned; no SIGSEGV/native CUDA/kernel fault |
| 2026-07-15 | 3 | R580.173.02 driver-candidate stress gate | PASS | all predeclared stages passed; strong A/B evidence against the 595.71.05 execution stack, without claiming an exact driver defect |
| 2026-07-15 | 3 | PCIe slot correction | PASS | RTX 5090 now negotiates x16 width with 32.0 GT/s maximum; idle 2.5 GT/s is link power management, not a width loss |
| 2026-07-15 | 3 | complete intake-test disposition | PASS | 128 = 19 byte-identical + 62 same-path migrations + 27 ownerless deletions + 20 replacements; current 99 = 19 + 62 + 18; five support registries deleted |
| 2026-07-15 | 3 | renamed-owner CPU batch | PASS | 127 passed: coherent Pauli, source coupling, coupled-process units, and qutrit parser corruption |
| 2026-07-15 | 3 | finite-RTN neutral diagnostic migration | PASS | old over-broad script/test/path removed; 14 current contract/schema/oracle/corruption/hash/atomic-output tests passed; registered as CPU-exclusive source-owner acceptance |
| 2026-07-15 | 3 | retired API static and subprocess gate | PASS | direct source/test/config/tool token and tree scans empty; current-module import blocker plus PEPO/PEPS host gates: 8 passed; seven old-schema rejection falsifiers passed |
| 2026-07-15 | 3 | package and generated inventory gates | PASS | scope boundary 5 passed; package release 7 passed; code map current at 104 installed modules, 27 services, and 70 unique acceptance files |
| 2026-07-15 | 4 | retired documentation and tracked-tool removal | PASS | 214 files removed from five retired documentation trees, plus four historical ADRs, the migration guide, and the obsolete tracked build skill; no repository archive created |
| 2026-07-15 | 4 | retained source/test API hard cuts | PASS | private certification injection seams, implicit c64 purpose, retired duration policy, zero-consumer helpers/aliases, duplicate interop test, and unowned PEPS diagnostic branch removed with no shims |
| 2026-07-15 | 4 | current vocabulary and authority gate | PASS | 8 passed; tracked/unignored source, tests, native code, scripts, tools, configs, current authority links, runtime imports, retired exports, and package trees checked |
| 2026-07-15 | 4 | current source/test focused CPU gates | PASS | duration/registry batch 417 passed, 1 optional skip; certification/current schedule batch 255 passed, 1 optional skip; narrative/support batches 123 passed, 3 deselected |
| 2026-07-15 | 4 | Axis-1 fresh GPU owner gates | PASS | connected-cluster 6 passed, convergence 5 passed, dense certification 5 passed; each file ran fresh under the cross-process GPU lock |
| 2026-07-15 | 4 | full test collection | PASS | 2,140 tests collected from the renovated current checkout in canonical `ecs`; no deleted test path is required |
| 2026-07-15 | 4 | regenerated code/service inventory | PASS | 104 installed Python modules, 4 native sources, 98 top-level test modules, 27 services, 71 unique acceptance files (29 cpu_light, 7 cpu_exclusive, 35 gpu_serial), 28 valid coverage registries; CODE_MAP check clean |
| 2026-07-15 | 4 | retained PEPS/FET scientific blocker | OPEN/UNCHANGED SCOPE | the original run was 0.10860941571062639 versus GF(2) 2.0; current fresh repeats were 0.12493899691635187 and 0.047288649590463, all at the unchanged 1e-4 tolerance; the value variation is not diagnosed in this Twin-only phase and the gate is neither skipped nor weakened |
| 2026-07-15 | 4 | ignored local old-product tooling/retrieval surfaces | QUARANTINED | excluded from current authority; exact dry-run deletion/rebuild belongs to Phases 5–6 and remains pending |
| 2026-07-15 | 5A | literature corpus inventory and current-corpus cut | PASS | 248 candidate content-note artifacts inspected; 0 current-schema notes; every legacy candidate excluded from current retrieval; original source objects preserved |
| 2026-07-15 | 5A | neutral RAG/KG tools and corruption tests | PASS | 64 passed; manifest-only paper-fact retrieval, source/note/section/chunk hashes, exact-locator edges, unsupported-schema rejection, generated-index freshness, and dangling-edge falsifiers |
| 2026-07-15 | 5A | current retrieval publication | ISOLATED/BOOTSTRAP EMPTY | 0 admitted notes, 0 RAG chunks, 0 KG edges, 0 dangling; no quarantined cache was read or migrated; empty publication is not literature completion |
| 2026-07-15 | 5A | quantum-bath public-contract correction | PASS | result key hard-cut to `inequality_violated` with no alias; `False` is inconclusive; citation corrected to Bäcker et al., PRL 132, 060402 (2024), arXiv:2310.01205; formula/numerical/tolerance path unchanged; owner suites 12 + 14 passed and scope suite 8 passed |
| 2026-07-15 | 5A | literature skill command/schema reset | PASS | `.agents` and `.claude` copies use neutral tools and source-only notes; paired skill/template copies are byte-identical |
| 2026-07-15 | 5A | regenerated developer-tool inventory and collection | PASS | CODE_MAP check clean; 104 installed modules and 27 services unchanged; 2,204 tests collected including the 64 literature-tool gates |
| 2026-07-15 | 5B1 | Wood--Gambetta DOI/VOR clean-room closure | PASS | APS VOR read in full and visually checked; four review rounds ended in dual independent PASS; 38 paper facts, 2 source-local gaps, 13 relations; 12 load-bearing source conflicts isolated; no project inference admitted |
| 2026-07-15 | 5B1 | current-corpus admission and retrieval rebuild | PASS | artifact-verified manifest contains 1 VOR note; RAG has 38 paper-fact-only chunks; KG has 13 source-located edges and 0 dangling; concept index regenerated |
| 2026-07-15 | 5B1 | literature and scope gates | PASS | canonical `python -m pytest` launcher: 72 passed; direct `conda run pytest` collection attempt was invalid because that entrypoint omitted the repository import root |
| 2026-07-15 | 5B1/P0 | qutrit scientific/API hard cut | PASS | fixed-input coherence is no longer a channel-cause label; nonmonotone solver is bracketed and fail-closed; fake source fan-out deleted; neutral v2 schemas and exports only; no compatibility aliases |
| 2026-07-15 | 5B1/P0 | qutrit owner and current-boundary gates | PASS | 192 focused CPU tests; 10/10 owner units at 100% statement/branch; scope suite 8 passed; 2,228 tests collected; old API/schema/M0--M34 scans empty; CODE_MAP current at 104 installed modules and 27 services |
| 2026-07-15 | 5B1/P0 | isolated sdist-to-wheel hard cut | PASS | 10 distribution/package tests; installed binding-spec bytes are hash-bound; neutral qutrit APIs and v2 source schemas resolve; retired qutrit/frontend aliases are absent from the isolated wheel |
| 2026-07-15 | 5B1/P0 | affected fresh-GPU owners | PASS WITH EXTERNAL BLOCKER | qutrit hard-cut owners, Axis-1, MCWF, QuTiP/cuQuantum, PEPO, and PEPS trajectory passed; only the unchanged-scope PEPS/FET entropy gate failed |
| 2026-07-15 | 7 pre-gate | 71-file service acceptance surface | GLOBAL BLOCKED | 70 files passed across a 49-file interrupted run and an atomic 22-file remainder; no 139/Xid/orphan; sole failure `tests/test_peps_fet.py`; the interrupted first run has no aggregate summary and is not promoted to a complete canonical gate |

## Phase-4 close boundary

Phase 4 closes the tracked authority and vocabulary reset. It does not claim that Phase 5 or Phase 6
is complete. Existing paper notes, RAG/KG outputs, ignored local workflows, and old generated
artifacts remain quarantined discovery material until their explicit reset/purge phases close.

The finite-RTN diagnostic is the first targeted clean-room exception: its two load-bearing primary
papers were reread in full, formula pages visually checked, project inference removed from their
reading notes, and a post-result (not preregistered) current contract created. Its new implementation
tests pass, but a signed JSON artifact must wait for a clean tracked checkpoint and belongs to the
Phase-6/7 regeneration gate.
