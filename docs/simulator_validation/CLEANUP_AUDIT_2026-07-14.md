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

## Phase-4 corrective reopening — 2026-07-15

Four negative gates were added before changing product source or current authority prose. Their
pre-fix run is intentionally red and proves that the new checks detect the actual escaped defects:
the cross-line `ADR 0011` reference and three unresolved backticked Markdown paths; five missing
level-one/two owner READMEs; the separately derived four-variable runtime/test-surface and
eight-variable harness-only environment contracts absent from `CLAUDE.md`; and three still-importable
numerical-floor symbols. The two historical snapshots
`docs/SCIENTIFIC_FORMULA_PROVENANCE.md` and this cleanup ledger are explicitly outside the closed
current-authority path set; placeholder and glob examples are not treated as concrete file claims.

No `src/**` file or current authority statement was changed before these RED results were recorded.
Phase 4 is reopened until the reviewed source/document diff turns all four gates green. Phase 5B
admission remains paused; the Miao note is still a draft and is not in the current corpus.

Independent gate review then found that the first numerical gate proved only that three old names
remained importable; it did not prove that the forbidden operation was absent under another name or
inline. Before any product fix, the gate was strengthened with an AST probability-threshold check and a
source-owner endpoint falsifier. The final pre-fix run is therefore six expected failures, while the
full scope file is `6 failed, 10 passed`: the original four defect groups plus active structural-zero
pollution in source probabilities/rates/stationary mass. This is a new P0 and enlarges the reviewed
`src/**` phase; it is not silently folded into the dead-helper deletion.

### Dated inventory reconciliation — 2026-07-15

Earlier phase rows remain visible as execution history. Their corrected top-level test-file chain is
`128 @ 844d211` (intake) -> `99 @ 4e04435` (47 removals and 18 additions, including the later-deleted
duplicate interop test) -> `98 @ ed351fd` (47 removals and 17 additions) -> `99 @ HEAD` (one current
literature test added). Thus the earlier “46 removed tests” text is corrected to **47** as of this
dated reconciliation; the Phase-4 `98` and current `99` rows describe different commits rather than
conflicting counts.

The acceptance count likewise changed by one at a real registration boundary: `70` was the
intermediate surface before the connected-cluster owner was registered; adding
`tests/test_axis1_connected_cluster_channels.py` produced the current `71`. Renames do not explain
or alter that count.

## Phase ledger

| phase | status | required outcome |
|---|---|---|
| 1 — boundary freeze | complete | intake inventory and trust boundary recorded |
| 2 — P0 repair | complete; 5B1 reopening closed | retired dispatcher deleted; retained record, packed bridge, Born probability, PTM, certification, coupled-process, and corrected qutrit-leakage owners pass independent falsifiers |
| 3 — Twin-only implementation hard cut | complete | retired implementation removed; all 128 intake tests reconciled; retained tests use current owners; static/subprocess/schema/package gates prove no retired runtime dependency |
| 4 — authority reset | reopened 2026-07-15 | corrective negative gates are proven red before the reviewed source/document repair |
| 5 — literature reset | paused at Phase 5B review | Phase 5A isolation and the first DOI/VOR note remain; Miao admission is blocked on source-only review and the reopened Phase-4 gate |
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
| 2026-07-14 | 3 | initial ownerless-test removal | PARTIAL/SUPERSEDED | initial estimate removed 27 ownerless scripts; corrected 2026-07-15 against the commit-anchored chain: 47 removed tests, 18 additions at `4e04435`, and five removed registries; see the dated inventory reconciliation above |
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
| 2026-07-15 | 4 corrective RED | current-authority ADR/backticked-path negative gate | FAIL/EXPECTED RED | caught cross-line `ADR 0011`; caught missing `frontend/nonmarkovian_memory_carrier_scope.md`; also caught two bare finite-RTN reading-note paths that do not resolve from their authority document; historical snapshots and placeholder/glob examples were outside the concrete-path check |
| 2026-07-15 | 4 corrective RED | derived owner-README existence gate | FAIL/EXPECTED RED | package structure derived exactly five missing contracts: `carrier/`, `carrier/exact/`, `mechanisms/`, `noise_processes/`, and `source/`; private `certify/anchors` remains parent-owned by an explicit semantic exemption |
| 2026-07-15 | 4 corrective RED | AST/config-derived environment documentation gate | FAIL/EXPECTED RED | actual runtime/test-surface set contained 4 keys and harness-only set contained 8 keys; both dedicated `CLAUDE.md` sections were absent; no bare token grep was used |
| 2026-07-15 | 2/4 corrective RED | shared-numerics negative API gate | FAIL/EXPECTED RED | caught importable `NUMERICAL_FLOOR`, `positive_floor`, and `probability_floor`; repository scan found no consumer outside the pre-cleanup formula snapshot and the current provenance sentence that rejects their use |
| 2026-07-15 | 4 corrective gate review | RED-gate anti-false-green hardening | PARTIAL/SUPERSEDED | the first synthetic set covered dynamic local aliases, ordinary-dictionary writes, ambiguous key reassignment, absolute local paths, and `00110` versus `ADR 0011`, but the later implementation review found an untested module-alias shadow and weaknesses in the compressed probability matcher; retained as the pre-correction result |
| 2026-07-15 | 2/4 corrective RED v2 | AST probability-threshold pattern gate | FAIL/EXPECTED RED | caught the shared positive-floor implementation; active probability zeroing, two-sided clamp, and rate/logit caps in `source/coupling.py`; the frontend source-projection logit cap; and tiny-positive boundary-probability deletion in `frontend/interop.py`; synthetic renamed/inlined corruptions are detected, while the separate delta-method gradient, NTU denominator, and SVD-rank guards remain unflagged |
| 2026-07-15 | 2/4 corrective RED v2 | source structural-zero endpoint falsifier | FAIL/EXPECTED RED | caught tiny positive rate/probability collapse, near-one probability clamp, finite rate/logit values replaced by `[-60,60]` caps in both source coupling and frontend source projection, tiny nonzero sensitivity treated as zero, finite tiny dephasing rate reported as infinite Tphi, and tiny-positive transition rates replaced by degenerate stationary mass; no `src/**` fix had been applied |
| 2026-07-15 | 2/4 corrective RED v3 | source cancellation-neighbour falsifier | FAIL/EXPECTED RED | before source repair, added stable `expm1`/`log1p` reference probes caught three same-cause neighbours in `source/process.py`: a positive `1e-20` RTN rate produced zero flip probability, positive transition rates produced infinite correlation length, and a finite `1e17` requested correlation length produced exactly zero transition rates; the endpoint falsifier now exposes 12 failures in total |
| 2026-07-15 | 2/4 corrective RED v4 | nonrepresentable-map fail-closed falsifier | FAIL/EXPECTED RED | before source repair, added lower/upper representability probes: positive-rate underflow and overflow did not raise, source logit underflow manufactured positive mass, source logit overflow returned endpoint probability one, and frontend logit underflow manufactured positive mass; the endpoint falsifier now exposes 17 failures, while the already-fail-closed frontend upper endpoint remains a passing control |
| 2026-07-15 | 2/4 corrective RED v5 | stable-map boundary completion | FAIL/EXPECTED RED | added five final neighbour probes before source repair: a mathematically representable rate lost to intermediate exponential overflow, reciprocal overflow in `Tphi`, RTN flip probability rounded to endpoint `0.5`, positive-rate autocorrelation rounded to endpoint `1`, and fixed-marginal transition underflow; the endpoint falsifier now exposes 22 failures and defines the required fail-closed boundary |
| 2026-07-15 | 4 corrective RED final | full scope-boundary pre-fix run | FAIL/EXPECTED RED | `6 failed, 10 passed`; every helper/self-falsifier passed and exactly the six declared product/document gates remained red |
| 2026-07-15 | 4 corrective gate review v2 | compressed-gate adversarial review | FAIL/CORRECTED | review reproduced a module constant hidden by a same-named function parameter, probability alias propagation that escaped the matcher, a `marginal_cost` false positive, and unrelated lower/upper bounds incorrectly combined into one clamp; all four cases were added as corruption or negative probes before source repair |
| 2026-07-15 | 4 corrective gate review v3 | compressed-gate adversarial rerun | PASS | same-named function/lambda bindings now fail closed, harness discovery is recursive, probability assignments propagate to a fixed point, and clamp/cap recognition requires one nested value chain; targeted probes `2 passed`, the complete pre-fix scope remained `6 failed, 10 passed`, the whole-source list remained exactly seven real findings, and `git diff --check` was clean |
| 2026-07-15 | 4 corrective RED fragment extension | current-authority local-link fragment falsifier | FAIL/EXPECTED RED | the synthetic probe accepted an existing heading and rejected a missing fragment before document repair; the product gate remained red on the same four real defects: ADR 0011, the missing frontend memory document, and two finite-RTN reading-note paths |
| 2026-07-15 | 2/4 corrective RED v6 | asymmetric endpoint and rate-recovery completion | FAIL/EXPECTED RED | before source repair, the endpoint falsifier separately pinned the float64 open-probability lower and upper bounds, used independent exact-float `mpmath` references, and added both representable rate-recovery directions (`1e-300, +710` and `1e300, -1000`); the aggregate remained exactly 22 failures |
| 2026-07-15 | 2 pre-implementation domain audit | current preset and acceptance parameter domain | PASS WITH TEST-CONTRACT MIGRATION | no current default preset or fixed positive acceptance configuration enters the new fail-closed domain; old clamp-expecting tests and the existing RTN property-test generator do intersect it and must assert rejection at unrepresentable endpoints. Public arbitrary finite inputs can enter the domain by design. No physical parameter was adjusted |
| 2026-07-15 | 2 corrective RED v7 | subnormal-exponential and constructor-domain review | FAIL/EXPECTED RED | five minimal owner regressions failed before repair: a subnormal `exp(shift)` poisoned a normal positive-rate product by 52.185%; low/high RTN, high finite-RTN-sum, and tiny positive storm inputs constructed successfully but failed only on later derived use; fixed-marginal unit transition mass surfaced a misleading generic `a+b` error |
| 2026-07-15 | 4 corrective RED path follow-up | current-authority path gate after first document repair | FAIL/EXPECTED RED | formal scope run was `1 failed, 15 passed`; exactly four finite-RTN reading-note labels remained parseable as unresolved backticked paths, including two otherwise-correct Markdown targets; no extractor exception was added |
| 2026-07-15 | 2 corrective regression | B1/B2/S1 minimal owner regressions | PASS | the same five pre-fix regressions passed after routing subnormal exponential intermediates through split-`ln(2)` recovery and validating all emit-consumed derived domains at construction; exact invalid/valid float neighbors and successful boundary-valid `sample()` calls are pinned |
| 2026-07-15 | 4 corrective path regression | current-authority path gate | PASS | `tests/test_scope_boundary.py`: `16 passed`; all four note references use descriptive link labels and repository-resolving targets, with no gate allowlist or exemption |
| 2026-07-15 | 2/4 corrective focused gate, first run | focused source/scope/interop suite | FAIL/TEST-ORACLE | `317 passed, 3 skipped, 1 failed`; the only failure was a newly added DEM-text assertion that incorrectly expected two lines and omitted the valid pair edge already emitted alongside two boundary edges. Source behavior was conforming; the failed test expectation remains visible rather than being promoted as a product failure |
| 2026-07-15 | 2/4 corrective focused gate, rerun | focused source/scope/interop suite | PASS | `318 passed, 3 skipped`; all B1--B3 and S1/S2 regressions, 22 endpoint falsifiers, 7 static source findings, adversarial negative controls, and the complete current scope suite (`16/16`) passed after correcting only the DEM-text oracle |
| 2026-07-15 | 2/4 corrective isolated release gate | sdist-to-wheel and package contracts | PASS | `10 passed`; a real sdist was rebuilt into a wheel, installed and exercised outside the repository, while package ownership, release metadata, generated inventory, fresh-process acceptance topology, and retired-tree absence remained valid |
| 2026-07-15 | 2/4 corrective final-diff RED v8 | cancellation, bundle, and reduction-domain falsifiers | FAIL/EXPECTED RED | `12 failed`; exact-float counterexamples caught 199-ULP logit cancellation, one exact-domain false rejection and one false acceptance in both logit owners, a recoverable frontend normalization overflow, finite coupling inputs emitting `inf`, and six negative/non-finite decoder-floor inputs silently altering DEM topology |
| 2026-07-15 | 2/4 full engineering regression attempt | repository `pytest tests/` | ABORTED/SUPERSEDED | the buffered run was stopped without a promoted test summary after final-diff review exposed the v8 RED counterexamples; its process group and GPU children were verified absent after interruption. The full gate must restart from the repaired checkout and is not inferred from this partial run |
| 2026-07-16 | 2/4 corrective RED v8 oracle correction | exact open-probability boundary classification | FAIL/TEST-ORACLE CORRECTED | the recorded 12 test failures contained two duplicated false-outside expectations, one in each logit owner. Exact-float high-precision evaluation proves both `(p_min,+0x1.8696a3c1fe543p+9)` and `(p_max,-0x1.8696a3c1fe543p+9)` are inside; `nextafter` toward larger shift puts both outside. The v8 product count was therefore 10 real failures plus 2 test-oracle failures; the historical v8 row is retained unchanged |
| 2026-07-16 | 2 corrective shared-numerics first focused run | source/scope/interop/numerics suite | FAIL/EXPECTED RED | `1 failed, 329 passed, 3 skipped`; Hypothesis found that a mathematically nonzero sensitivity product below half the minimum subnormal was rounded to shift zero and silently treated as identity. The shared product-ratio primitive was extended to reject that nonrepresentable nonzero shift |
| 2026-07-16 | 2 corrective numerics coverage first run | shared numerics owner registry | FAIL/EXPECTED RED | `scaled_product_ratio` had statement `29/29` but branch `11/12`; the missing route was a normal ratio intermediate whose final multiplication overflowed or rounded to zero. Both endpoint counterexamples were added before promotion |
| 2026-07-16 | 2 corrective source coverage first run | source coupling owner registry | FAIL/EXPECTED RED | `drift_to_t2` had statement `10/11` and branch `3/4`; a positive minimum-subnormal rate made `1/gamma` non-finite. The exact rejection and message were added before promotion |
| 2026-07-16 | 2 corrective subnormal-exponential rerun | B1 311-point regression | PASS | every `exp(shift)` point from the first positive exponential through the last subnormal exponential was routed through shared split-`ln(2)` recovery; all 311 representable normal final products agreed with the 200-digit exact-float oracle within 1 ULP |
| 2026-07-16 | 2 corrective owner coverage rerun | shared numerics and source coupling registries | PASS | numerics: 3/3 public units at statement/branch 100%; source coupling: 20/20 public units at statement/branch 100%, including public bundle emission invariants and finite reciprocal lifetime |
| 2026-07-16 | 2/4 corrective focused GREEN | affected source, projection, DEM, scope, numerics, and coupled-cycle owners | PASS | `377 passed, 3 skipped`; all exact-float endpoint, scaled-product, finite-emission, decoder-floor, RTN/process, current-authority path, adversarial static, and helper-regression tests passed. The standalone scope gate was `16 passed`; the expected interop population-cube warnings remained 28 |
| 2026-07-16 | 4/7 regenerated code/service inventory | current checkout after shared-numerics registration | PASS | 104 installed Python modules, 4 native sources, 100 top-level test modules, 27 services, 72 unique acceptance files (`30 cpu_light`, `7 cpu_exclusive`, `35 gpu_serial`), and 29 coverage registries; all 104 modules are classified and `CODE_MAP --check` is clean |
| 2026-07-16 | 2 corrective final-review RED v9 | adjacent-ULP, scaled-exp, and public emission-boundary falsifiers | FAIL/EXPECTED RED | `10 failed`: an exact-domain-outside probability rounded to the odds ULP adjacent to the upper boundary and was accepted; one representable `DBL_MAX` scaled exponential was rejected and a second fallback missed by 2 ULP; a finite static-ZZ input emitted infinite exchange; and public coupling bundles accepted six invalid physical fields plus invalid mode/draw-key structures. The preceding 377-test GREEN is retained but superseded for phase promotion |
| 2026-07-16 | 2 corrective final-review RED v10 | strict structural-zero and DEM-identifiability falsifiers | FAIL/EXPECTED RED | two focused tests independently proved red: a strictly negative `J^2=-5e-13` was thresholded and returned as structural `J=0`, while an undefined Spitz `0/0` pair was omitted and its diagnostic `p_ij/SE` overwritten with zero instead of remaining explicitly unidentifiable |
| 2026-07-16 | 2 corrective final-review probes | stable static-ZZ and inversion boundary | FAIL/EXPECTED RED | independent 200-digit probes found `static_zz_zeta(1e16,1,1e8)` returned false zero instead of the representable `4e-16`; finite `phi=t_gate=DBL_MAX` produced `inf/inf -> NaN -> J=0` although `J≈1.2944` is representable; and minimum-subnormal `phi` lost an unrepresentable intermediate `J^2` although final `J≈5.75e-163` is representable |
| 2026-07-16 | 2 corrective owner regressions after v9/v10 | numerics, source coupling, and interop | PASS | targeted new counterexamples `15 passed`; complete three owner files `94 passed, 3 skipped`; numerics 3/3, source coupling 20/20, and interop 5/5 public units each reached statement/branch 100% |
| 2026-07-16 | 2 corrective post-refactor subnormal rerun | shared Decimal scaled-exponential recovery | PASS | the 311-point subnormal-exponential window plus the correctly-rounded `DBL_MAX` and former 2-ULP fallback probes passed; every checked final product remained within 1 ULP of the 200-digit exact-float oracle |
| 2026-07-16 | 2 corrective final-review RED v11 | global rounding, immutable emission, reciprocal, and correlation falsifiers | FAIL/EXPECTED RED | `7 failed, 1 passed`: scaled exponential rejected a globally recoverable minimum subnormal; finite `zeta*t/4` overflowed in an intermediate; tiny and `DBL_MAX` trajectories produced false-zero/`NaN` Pearson results; mutable arrays/lists could change validated configs or manifests; and positive `gamma/Tphi` pairs were not checked for reciprocal consistency |
| 2026-07-16 | 2 corrective endpoint and snapshot counterexamples | final semantic owner targets | PASS | `11 passed`: global half-minimum-subnormal/overflow classification, static-ZZ overflow midpoint, raw-input exchange inversion, representable `phi`, direct three-factor fan-out, scale-stable Pearson, primitive-float/tuple snapshots, schema/mode snapshots, and exact `gamma/Tphi` consistency |
| 2026-07-16 | 2 corrective static-ZZ upper-bound RED | independent representable upper-endpoint oracle | FAIL/EXPECTED RED | a finite point 11 ULP below `DBL_MAX` differed from the 200-digit oracle by 3 ULP, exceeding the current <=2 ULP owner convention; the top exact-rational guard was expanded only after this fixed counterexample failed |
| 2026-07-16 | 2 corrective final high-precision sweep | shared arithmetic, odds, static-ZZ, and exchange | PASS | scaled exponential 78,008 points (0 false accepts/rejects, max 1 ULP); scaled ratio 65,413 (0/0, max 1 ULP, half-subnormal ties-to-even); odds endpoints 22,000 (0/0); static-ZZ upper 35,000 (18,371 accepts, 16,629 rejects, 0/0, max 0 ULP); exchange 135,536 (0/0, no crash, max 2 ULP) |
| 2026-07-16 | 2 corrective DEM negative-residual audit | real Spitz and controlled tiny-negative counterexamples | FAIL/EXPECTED RED -> PASS | a declared edge floor hid negative residuals inside its magnitude; the decoder selection parameter was removed from the consistency decision, and both `p_raw=-0.1324555` with floor `.15` and controlled `p_raw≈-5e-13` now remain in `clamped_boundaries` |
| 2026-07-16 | 2 corrective owner and coverage gates | numerics, source coupling, and interop | PASS | owner files `107 passed, 3 skipped`; numerics 3/3, source coupling 20/20, and interop 5/5 public units each reached statement/branch 100%; corruption falsifiers cover defensive non-finite Pearson routes |
| 2026-07-16 | 2/4 corrective focused GREEN v2 | affected source, projection, DEM, scope, numerics, and coupled-cycle owners | PASS | `400 passed, 3 skipped`; standalone scope remained `16 passed`; the expected 28 Spitz population-cube warnings remained visible |
| 2026-07-16 | 2 corrective final-review RED v12 | cross-scale endpoint and site-aggregation falsifiers | FAIL/EXPECTED RED | a 200-digit endpoint classifier accepted `p_max` shifted outward by the minimum subnormal and `p_min` shifted outward by its negative because the distinction occurs beyond the 323rd decimal place; a two-site payload `[min_subnormal, 0]` rounded its nonzero exact mean to zero and incorrectly invoked the structural identity branch |
| 2026-07-16 | 2 corrective final-review RED v13 | finite-RTN-sum amplitude and PSD endpoint falsifiers | FAIL/EXPECTED RED | `2 failed`: `OneOverFDriftSource(amplitude=min_subnormal,n=4)` constructed but emitted four false-zero modes, while a representable endpoint PSD evaluated as `0/0 -> NaN` instead of the correctly rounded value one |
| 2026-07-16 | 2 corrective owner-coverage RED | new PSD and projection rejection branches | FAIL/EXPECTED RED | source-process coverage found `OneOverFDriftSource.analytic_psd` at statement `15/18`, branch `5/6`; noise-spec coverage found `SourceStimPauliRule.probability_for` at statement `12/13`, branch `7/8`. Public overflow/underflow PSD and post-construction non-finite carrier corruptions were added before promotion |
| 2026-07-16 | 2 corrective final-review RED v14 | shallow-frozen source constructor corruption | FAIL/EXPECTED RED | a caller-owned zero-dimensional RTN amplitude/rate/cycle array changed after validation (`1 failed` immediately); equivalent probes showed OneOverF could be mutated into false-zero modes, PhaseBurst retained a mutable event list/scalar, and Storm could be mutated past `a+b<1` into a late math-domain failure |
| 2026-07-16 | 2 corrective endpoint, aggregation, PSD, and snapshot regressions | final semantic owner targets | PASS | the 1200-digit endpoint classifier rejects `p_max+min_subnormal` and `p_min-min_subnormal`; exact-input site averaging preserves only true cancellation; OneOverF rejects false-zero modes and computes its finite PSD as an exact rational sum with final underflow/overflow rejection; all four source classes snapshot validated mutable inputs. The source-process owner is `71 passed`; numerics plus noise-spec owners are `142 passed` |
| 2026-07-16 | 2 corrective owner-coverage rerun | numerics, noise projection, and source process | PASS | numerics 3/3, noise spec 25/25, and source process 33/33 public units each reached statement/branch 100%; no coverage exemption or allowlist was added |
| 2026-07-16 | 2 corrective exchange direct-path bound | fixed exact-float 2-ULP regression | PASS | the all-normal tuple `delta=-0x1.a837c88962923p+191`, `alpha=-0x1.2b0db576e809ep+185`, `phi=-0x1.82cdc8fe2d8c7p-243`, `t=0x1.c9eada0d47998p+783` returns `0x1.fe1f81ed61c15p-415` against exact-input oracle `0x1.fe1f81ed61c17p-415`; the test pins the honest direct-path distance at exactly 2 ULP rather than claiming 1 ULP |

## Corrective numerical behavior ledger

This table declares the intended behavior changes in the reviewed Phase-2 source patch. The patch is
not marked green until its focused owner, static, adversarial, and scope gates run after human diff
review.

| Behavior class | Owner | Concrete counterexample | Old behavior | Current contract |
|---|---|---|---|---|
| Cancellation error and false structural zero removed | `source/process.py` mechanism helper | `_rtn_flip_probability(1e-20)` | the helper rounded a finite positive flip probability to exact zero | return the cancellation-safe positive mechanism value; public `RTNSource(1e-20)` is separately rejected at construction because `autocorr_base` rounds to one |
| False structural zero removed | `frontend/interop.py` | controlled residual `p_raw=5e-13` | boundary edge silently omitted by the shared threshold | emit every strictly positive residual; exact zero remains absent |
| Saturation replaced by rejection | `source/coupling.py`, `frontend/noise_spec.py` | `nextafter` immediately outside each asymmetric float64 logit bound | finite logit was silently capped or rounded to a probability endpoint | reject the nonrepresentable open-interval result |
| Tiny positive and exact identity preserved | `source/coupling.py`, `frontend/noise_spec.py` | positive input with `shift == 0` | thresholding or logit round-trip changed the input | return the original float exactly through a structural zero-shift branch |
| Representable endpoint recovery | `numerics.py`, `source/coupling.py` | `(base, shift)=(1e-300,710)` and `(1e300,-1000)` | the intermediate exponential overflowed or underflowed | recover the correctly rounded positive product from exact binary64 inputs with the high-precision shared fallback; reject only an unrepresentable final result |
| Poisoned subnormal intermediate removed | `numerics.py`, `source/coupling.py` | `base=1.67e260`, `shift=-744.86` | a subnormal exponential intermediate yielded a finite normal result with `52.185%` relative error | route every zero, subnormal, or overflowing exponential intermediate through high-precision exact-input recovery before trusting a finite product |
| Late emit failure moved to owner boundary | `source/process.py` | RTN below/above its float64 domain; storm `0<a+b<=1/DBL_MAX`; fixed-marginal unit transition sum | constructors accepted values that later failed while emitting metadata or sampling | validate every emit-consumed derived quantity in `__post_init__` or the named constructor and report the input parameter domain |
| Cancellation-sensitive logit value repaired | `numerics.py`, `source/coupling.py`, `frontend/noise_spec.py` | `p=0x0.0000000000001p-1022`, `shift=0x1.74385446d71c3p+9` | rounded `logit(p)+shift` lost up to 199 ULP | apply the shift in odds space through the shared scaled exponential; use exact-input classification only at an ambiguous open-domain endpoint |
| Recoverable scaled ratio preserved | `numerics.py`, `source/coupling.py`, `frontend/noise_spec.py` | `sensitivity=min_subnormal`, `value=1`, `z_scale=min_subnormal`; raw `draw=min_subnormal`, `scale=1.15`, `sensitivity=DBL_MAX` | forming `value/z_scale` first overflowed or rounded a subnormal coordinate before the remaining factor could recover the finite shift | form the three-factor shift directly; use an exact-rational fallback with binary64 ties-to-even and feed the shared odds map |
| False zero shift replaced by rejection | `numerics.py`, `source/coupling.py`, `frontend/noise_spec.py` | nonzero finite factors whose exact product magnitude is below half the minimum subnormal | the product rounded to zero and invoked the structural identity branch | exact factor zero alone is identity; an unrepresentable nonzero shift is rejected |
| Non-finite, mutable, or invalid coupling bundle blocked | `source/coupling.py` | `detuning_base=DBL_MAX`, finite detuning draw `DBL_MAX`; invalid mode/draw keys; negative rate/exchange; endpoint probability; inconsistent `gamma/Tphi`; caller mutates a zero-dimensional array or draw list after construction | a public parameter bundle could carry non-finite/physically invalid values or change after its validation | the public dataclass is the single immutable emission snapshot; structures and scalar domains are validated, positive `gamma` requires exact reciprocal `Tphi`, and only structural zero gamma permits `Tphi=+inf` |
| Invalid DEM reduction floor rejected | `frontend/interop.py` | each pair-floor parameter set to `-1`, `NaN`, or `+inf` | comparisons silently changed or erased the optional DEM topology | require both declared class-(c) parameters to be finite and nonnegative; do not reinterpret them as probability floors |
| Static-ZZ cancellation, endpoint, and inversion corruption removed | `source/coupling.py` | `(Delta,alpha,J)=(1e16,1,1e8)`; `J^2=-5e-13`; overflow midpoint returning `DBL_MAX-1`; `phi=t=DBL_MAX`; subnormal unit-`J` coefficient with representable final `J` | subtraction, threshold, coefficient materialization, and unsafe intermediate arithmetic returned structural zero, a wrong finite endpoint, or a non-finite manifest | use the stable ZZ identity, top-16-ULP exact-rational fallback, strict sign rejection, and raw-input end-to-end inversion; only exact physical zero returns zero |
| Unidentifiable DEM pair preserved | `frontend/interop.py` | independent half-marginal pair with Spitz denominator/covariance `0/0` | the pair was dropped and diagnostics rewrote `NaN` `p_ij/SE` as zero | keep `NaN` values plus `pij_identifiable=False`; exclude the pair from the optional reduction without claiming structural zero |
| Negative DEM model residual remains visible | `frontend/interop.py` | real Spitz population cube with `p_raw=-0.1324555` and `pair_floor_abs=0.15`; controlled `p_raw=-5e-13` | a negative residual disappeared whenever its magnitude lay inside the declared edge-selection floor | record every strictly negative residual as `negative_residual`; decoder selection parameters never redefine model consistency or structural zero |
| Scale-stable correlation preserved | `source/coupling.py` | perfect correlation on `(0,5e-13)` and on `(-DBL_MAX,+DBL_MAX)` | the shared threshold returned false zero for the first trajectory and raw variance overflow returned `NaN` for the second | reject non-finite fields, treat only exact constants as degenerate, and compute centered Pearson correlation after independent scale normalization |
| Cross-scale endpoint classification | `numerics.py`, `source/coupling.py`, `frontend/noise_spec.py` | `p_max` with `+min_subnormal` shift and `p_min` with `-min_subnormal` shift | insufficient Decimal precision classified a mathematically outside value as the unchanged endpoint ULP | use 1200-digit exact-input log-odds comparison whenever the odds result lands on an open-domain endpoint |
| Nonzero site mean cannot become identity | `numerics.py`, `frontend/noise_spec.py` | two-site payload `[min_subnormal,0]`; cancellation control `[min_subnormal,-min_subnormal]` | ordinary averaging rounded both cases to zero | average exact binary64 inputs as rationals, preserve exact cancellation, and reject a nonzero mean that cannot be represented |
| Finite-RTN-sum false modes and false PSD endpoints removed | `source/process.py` | total amplitude `min_subnormal` over four modes; `amplitude=sqrt(min_subnormal), gamma=min_subnormal, omega=0` | per-mode division manufactured zero sources and direct PSD arithmetic produced `NaN` | reject an unrepresentable nonzero per-mode amplitude; sum the analytic PSD exactly over binary64 mode values and round only the final result |
| Mutable source parameters cannot bypass construction gates | `source/process.py` | caller mutates 0-D RTN/OneOverF/Storm scalars or a PhaseBurst event list after construction | shallow-frozen dataclasses changed after validation and failed late or emitted different physics | normalize every validated source field to a primitive scalar or immutable tuple in `__post_init__` |

The RTN `expm1` correction is a physical process repair, not a precision-only optimization: at the
mechanism level the previous cancellation could manufacture a zero transition probability. The
public `RTNSource` now rejects positive rates when either the flip probability or one-cycle
autocorrelation reaches a float64 endpoint; `gamma_per_cycle=1e-20` is therefore a mechanism-helper
counterexample, not a successful public sampling run. Within the accepted domain, ULP-level changes
can flip individual seeded RNG comparisons, so pre-correction finite-RTN trajectories are not
bit-level reference artifacts. Hash-bound finite-RTN oracle and diagnostic evidence is scheduled for
Phase 6/7 regeneration under the current schema, with no compatibility comparison to old artifacts.

## Phase-4 close boundary

Phase 4 closes the tracked authority and vocabulary reset. It does not claim that Phase 5 or Phase 6
is complete. Existing paper notes, RAG/KG outputs, ignored local workflows, and old generated
artifacts remain quarantined discovery material until their explicit reset/purge phases close.

The finite-RTN diagnostic is the first targeted clean-room exception: its two load-bearing primary
papers were reread in full, formula pages visually checked, project inference removed from their
reading notes, and a post-result (not preregistered) current contract created. Its new implementation
tests pass, but a signed JSON artifact must wait for a clean tracked checkpoint and belongs to the
Phase-6/7 regeneration gate.
