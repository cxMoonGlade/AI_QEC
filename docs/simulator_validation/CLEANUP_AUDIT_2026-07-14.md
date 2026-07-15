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

The first script classification found 27 tests with no current source owner, 17 tests whose
invariants require a current-owner coverage reconciliation, three PEPO/PEPS mixed tests that must
be migrated off the retired host API, two clean PEPO/PEPS ownership tests, and 81 tests already on
the current import graph. The 27 ownerless scripts and four retired test registries are now deleted;
the 17-file reconciliation and PEPO/PEPS migration remain gated work.

Before more deletion, every outstanding worktree change must be classified as Twin-only or
out-of-scope. Out-of-scope changes are reverted; the broader current-core cleanup interpretation is
withdrawn. Retained source and tests must additionally pass a static and subprocess-enforced
retired-API dependency gate.

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
is a separate performance/platform follow-up, not evidence for the exit-139 cause.

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

## Phase ledger

| phase | status | required outcome |
|---|---|---|
| 1 — boundary freeze | complete | intake inventory and trust boundary recorded |
| 2 — P0 repair | complete | retired dispatcher deleted; retained record, packed bridge, Born probability, PTM, certification, coupled-process, and qutrit-leakage owners pass independent falsifiers |
| 3 — Twin-only implementation hard cut | in progress | remove retired implementation and ownerless scripts; migrate retained tests to current APIs; prove no retired dependency |
| 4 — authority reset | pending | current-only binding docs and source-closed retained claims |
| 5 — literature reset | pending | paper-fact-only notes/RAG/KG with no dangling evidence |
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
| Retired scientific names remained attached to certification, coupled-process, and qutrit-leakage owners | expose only neutral process/fixture APIs and physically named qutrit leakage operations | PASS: defining APIs plus 100% statement/branch owner gates |

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
| 2026-07-14 | 3 | out-of-scope PEPS/FET diagnosis | STOPPED | temporary instrumentation and attempted FET change removed; no PEPS/FET source or test diff remains |
| 2026-07-14 | 3 | historical test/record classification | PASS | all tracked tests are scripts; old source+script snapshot is recoverable from `844d211`; support JSON files are registries, not results |
| 2026-07-14 | 3 | ownerless legacy test removal | PASS | 27 scripts without a current implementation owner and four retired registries deleted; PEPO/PEPS tests excluded |
| 2026-07-14 | 3 | native-crash runtime matrix | FAIL | exact-reference-only SIGSEGV reproduced under CUDA 12.8, 13.0, and 13.2; dependency mixing, PEPO NTU/SVD, custom kernels, and allocator choice rejected as sufficient explanations |
| 2026-07-14 | 3 | R580.173.02 package dry run | PENDING AUTHORIZATION | compatible CUDA 13.x driver candidate identified; no package or running driver changed; reboot plus post-change stress gate required |
| 2026-07-15 | 3 | R580.173.02 post-reboot stack audit | PASS | active kernel modules, `libcuda`, NVML, and GSP all 580.173.02; Secure Boot signature valid; canonical PyTorch 2.12.0+cu130 map and core-environment contract clean |
| 2026-07-15 | 3 | R580 reference-only stress gate | PASS | 20/20 fresh execs; identical exact-array SHA256; 23--24 s each; default allocator; no kernel fault |
| 2026-07-15 | 3 | R580 full reference-to-PEPO A/B gate | PASS | 3/3 fresh two-child comparisons; identical max-absolute difference 0.0029731254318278552 <= 0.01; 22 binding NTU entries |
| 2026-07-15 | 3 | current PEPO service acceptance | PASS | 10/10 fresh files, including 8/8 gpu_serial owners; all process groups verified cleaned; no SIGSEGV/native CUDA/kernel fault |
| 2026-07-15 | 3 | R580.173.02 driver-candidate stress gate | PASS | all predeclared stages passed; strong A/B evidence against the 595.71.05 execution stack, without claiming an exact driver defect |
