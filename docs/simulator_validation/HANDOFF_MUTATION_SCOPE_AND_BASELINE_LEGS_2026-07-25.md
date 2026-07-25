# Mutation scope and external baseline legs — 2026-07-25

## Authority and claim boundary

This file records one session's work on branch `mutation-x86-a875395` (branched from `a875395`,
four commits, worktree clean). It changes the mutation gate's execution contract and the external
baseline surface. It does not change any scientific claim: no carrier gained faithfulness, no
metric was added, and no `src/**` file was modified.

Read [`docs/SIMULATOR.md`](../SIMULATOR.md) first, then [`CLAUDE.md`](../../CLAUDE.md),
[`CONTEXT.md`](../../CONTEXT.md), [`docs/service_status.json`](../service_status.json),
[`tests/CODEBOOK.md`](../../tests/CODEBOOK.md), and
[`docs/external_baselines/BASELINE_ENVIRONMENTS.md`](../external_baselines/BASELINE_ENVIRONMENTS.md).

The `project-engine-ecs` skill (now mirrored into `.claude/skills/`) is the routing engine for this
kind of work. Use it before touching mechanisms, Carrier/Record evidence, or baselines.

## What landed

| Commit | Change |
|---|---|
| `4abff32` | Mutation suite scope + per-host worker counts |
| `3cceb11` | Aer/YASTN environment repair + ITensorMPS third MPS leg |
| `352fca6` | pinv/svd replay reproducers retained; CODE_MAP regenerated |
| `1e719f3` | Downstream documentation for the baseline environments and the narrowed scope |

### Mutation gate: two contract changes

**Per-host worker counts.** The `gpu_serial` ceiling of four was hardcoded in four places; those
collapse into `mutation._GPU_MAX_FRESH_WORKERS = 16`, and each batch declares the count for the host
that runs it (8 aarch64, 16 x86, cpu batch unchanged at 4). A same-shard A/B on `gpu_03` measured
0.71 wall-seconds per mutant against a 1.84 baseline — 2.59x, cutting that shard from 4.74 h to
1.98 h. Classification does not depend on the choice: the per-mutant timeout scales by the same
in-shard concurrency, and a real timeout or resource exhaustion aborts the shard instead of being
scored.

Two sizing results worth not rediscovering. 24 workers is **slower** than 16, because the mutant
loop is a lockstep barrier-wave scheduler (`for wave_start in range(0, len(remaining), jobs)`) and
SMT siblings create a mixed-speed wave whose cost is the slowest worker's. 32 exhausts device memory
during clean-control admission: measured at 16 workers, admission uses 735 MiB of VRAM per CUDA
context, 13.9 GB total, and 41 GB of host RAM.

**Scope.** Each batch now declares `default_scope` and a mandatory `scope_rationale` (>= 40 chars),
and only in-scope batches run by default. The default scope is the `certify` shard alone. Batches
stay declared, because the loader requires the union of batch modules to equal the coverage
registry's thirteen modules — deleting a batch would break the L0/L1 coverage gate as well. Each
suite run publishes its executed and deferred batches with reasons, so a narrowed score never reads
as a complete one. Default cost fell from 22,167 mutants to 7,027.

The rationale, recorded in the suite JSON: the evaluator judges every external comparison, so no
baseline leg can validate it; and its fail-closed guards are invisible to green tests because a
guard that never fires looks like one that cannot fire.

### External baselines: three legs restored, one added

`docs/service_status.json` had long declared `ecs-baseline-aer` and `ecs-baseline-yastn` while
neither environment existed on this host and neither had a committed lock. Two of the three wired
MPS legs silently could not run. Both are rebuilt and locked; all four legs now pass (43 tests).

ITensorMPS is wired as a third MPS leg because the truncated-MPS canonical split, Schmidt spectrum
and discarded weight had **no external independent comparator at all**: the Aer leg never compares
against this project's carrier, the YASTN leg is a bond-dimension-one product-MPS mass check that
performs no SVD, and two of the three legs in `scripts/mps_three_leg_comparator.py` run the same
quimb that implements this project's splits.

Verified end to end: three frozen fixtures across full_rank/cap_2/cap_1, all full-rank rows
reproducing an independent numpy dense reference at fidelity `1.000000000000`, and a deliberate
rotation corruption caught. `status=passed`.

## Measured results retained

| Shard | Mutants | Raw kill rate | Semantic | Survivors |
|---|---|---|---|---|
| cpu | 3,681 | 0.8289 | 0.9373 | 204 |
| gpu_01 (Spark) | 5,717 | 0.7186 | 0.7410 | 1,131 |
| gpu_02 (Spark) | 12,648 | 0.7532 | 0.7828 | 3,108 |
| gpu_03 | 10,042 | 0.6638 | 0.7257 | 3,366 |
| gpu_04 | 1,417 | 0.7332 | 0.7348 | 378 |
| gpu_05 | 7,027 | 0.7423 | 0.8054 | 1,811 |

x86 shards ran 18,486 mutants in 6.06 h with zero crashes and zero timeouts. The gap map tool is
`scripts/mutation_survivor_gap_map.py`; the newest map is under
`outputs/simulator_validation/mutation_gap_maps/`.

Note the asymmetry: the 204 reviewed semantic dispositions apply **only** to the cpu batch. All
three GPU shards report `dispositions_applied = 0`, so their kill rates carry no equivalence credit
and roughly 95% of their survivors have never been reviewed.

## Survivor mechanism: what the census actually found

A full census of `_certify_record_path` (331 mutants, every one diffed against the original) found
the discriminator is **assertion surface, not coverage**. Every mutant in a function shares the
identical covering test set and line coverage is complete; what separates killed from survived is
whether the mutated expression is pinned by an assertion. That function's eleven covering tests
include ten bare `pytest.raises` with no `match=`, and the single test that inspects the returned
dict asserts four of its twenty-five keys.

Two cheaper hypotheses were tested and **rejected**: manifest-style functions are not systematically
blind (their survival rates match the shard mean), and covering-test count explains little
(Pearson r = -0.316 over 66 functions; a 1-test function survives at 17.6% while a 267-test function
survives at 35.3%).

The remedy is mostly `write_test` — only 4 of 213 survivors in that function are true equivalences.
But 14 of 30 fields in its certification payload are **written and read by nothing in `src/`**, so
adding assertions for those would pin decoration rather than behaviour. Those need a source
decision: wire up the guard that should read them, or record them as non-load-bearing.

One finding deserves separate attention: `oracle_independent_of_carrier_grouping` can be flipped to
`False` on the success path with no test noticing. That is a core evaluator guarantee currently
without a falsifier.

## Open items

1. **Read `.scratch/mutation-gate-adjudication/`** — three issues (gate-green definition, equivalent
   mutant denominator, registry/execution snapshot coupling) that bear directly on this session's
   scope change and kill-rate semantics. They were recovered from Spark this session and have not
   been read. Check the scope narrowing against them before propagating it.
2. **Spark merge** — `mutation-x86-a875395` is pushed to Spark but not merged; its `Dev-F` is still
   at `a875395` and its fixture-family job has been running since 2026-07-24. Before merging, delete
   Spark's three untracked copies of `scripts/run_pinv_170_test.py`, `scripts/run_svd_170_test.py`
   and `test_170` (verified byte-identical to the committed versions), or git will refuse.
3. **Spark's cpu/01/02 mutation batches have never run at `a875395`** with the repaired harness.
4. **4,105 unreviewed survivors** across the x86 shards. The `adversarial-reachability` skill is
   built for exactly this; the GPU is free.
5. **The 14 unread certification fields** need the source decision described above.
6. **Static IP** — recommended as a router DHCP reservation by MAC (`34:5a:60:bd:b8:07` wired,
   `ac:f2:3c:cb:1b:a1` WiFi, gateway `192.168.1.254`) rather than a netplan static, because this
   host's interface names have already changed twice across hardware swaps. Not done.
7. **RTC offset** — `/proc/uptime` and the journal disagree by about eight hours on this boot, and
   the cause is not established. Timestamps within a boot that cross an NTP step are not comparable;
   `boot_id` and the monotonic clock are the reliable identities.

## Traps already paid for

- `git status --porcelain` **hides gitignored files**, so a clone polluted by a directory install
  (`build/`, `*.egg-info/`, a generated `_version.py`) reports clean while a leg later fails with an
  opaque source-tree mismatch. Use `--ignored`.
- Bind a source install with `git+file://<clone>@<commit>`. A bare directory path records `dir_info`
  and binds nothing; this cost two debugging rounds on QuTiP and again on YASTN. Aer is the
  deliberate exception: its orchestrator requires `direct_url` to be **absent**.
- Julia: `JSON.parse` returns `JSON.Object`, not `Dict`; `String(::Vector{UInt8})` takes ownership
  and empties the source array; `svd`/`noprime`/`eigs`/`truncerror` are defined in `ITensorMPS` but
  not exported. Do not reimplement Python's canonical JSON in Julia — hash the raw request bytes.
- An SVD at cutoff 0 returns numerically-zero singular values, so its length is not the bond
  dimension. Report the state's own `linkdims`.
- `mutation.py` exits 1 both for a below-bar gate and for a crash. Distinguish them by whether the
  `MUTATION tag=... PASS|FAIL` summary line was published; `scripts/run_mutation_shard_chain.py`
  does this.
- Never write anywhere under `tests/` while a mutation shard is running: `_batch_snapshot_paths`
  hashes the entire tree and the batch aborts at publish.

## Tooling added this session

`scripts/external_baselines/`: `itensor_mps_protocol.py`, `itensor_mps_worker.jl`,
`run_itensor_mps_comparison.py`, `build_itensor_baseline_environment.py`,
`build_mps_baseline_environment_locks.py`.

`scripts/`: `mutation_survivor_gap_map.py`, `run_mutation_shard_chain.py`,
`mutation_shard_autotune.py`, `mutation_gpu_shard_resource_probe.py`.

Agent memory carrying the durable facts: `mutation-gate-gpu-worker-sizing`,
`itensormps-third-baseline-leg`, `ubt5090-hard-reset-diagnosis`.
