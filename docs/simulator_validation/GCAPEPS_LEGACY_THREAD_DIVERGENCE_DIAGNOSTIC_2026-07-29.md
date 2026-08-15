# GCAPEPS legacy capped-tree thread-divergence diagnostic

Date: 2026-07-29

Status: **post-result bug-localization input; not formal evidence, not a
held-out result, and not a replacement for the committed repair regression.**

## Scope and source identity

The diagnostic used parent commit
`6d37d9b6753279bdfc26227ad6812f9647085031`, parent tree
`7f40ba760ff182ec625b164dcf6ec99a6895722b`, Quimb-fork commit
`d90bb5ea210e666cbd7ecf8a8b7fa02390519baf`, and fork tree
`f7cd3496c48ec69f1800d41eabcaa8d53cab3b5b`. The parent worktree already
contained unrelated uncommitted finite-memory scale-balance work. The
observations below were obtained during interactive diagnosis and the raw
vectors were not persisted as a sealed artifact. They can localize a program
defect and register a future regression, but cannot qualify a scientific
claim.

The common cell was:

```text
width = 7
n_qubits = 14
rounds = 4
axis_family = 3
p_event = 3/4
seed = 2
gamma_index = 2
input_id = 2
max_bond = 32
cutoff = 0
dtype = complex128
strategy = exact_tree_then_native_compress
```

Fresh processes set all of `OMP_NUM_THREADS`, `OPENBLAS_NUM_THREADS`,
`MKL_NUM_THREADS`, `NUMEXPR_NUM_THREADS`, and `BLIS_NUM_THREADS` uniformly to
one or four. CUDA was disabled and `PYTHONHASHSEED=0`.

## Observed localization

The following values are a transcription of interactive diagnostic output.
They are deliberately not labelled as current metrics because no raw-vector
artifact survives:

| Comparison | Observation |
|---|---:|
| ordinary Quimb, one versus four threads, normalized fidelity | `0.9999999999999996` |
| ordinary Quimb, phase-aligned relative L2 diagnostic | `4.8594e-14` |
| ordinary Quimb, phase-aligned L-infinity diagnostic | `1.72495e-15` |
| legacy GC capped tree, one versus four threads, normalized fidelity | `0.5233640835918022` |
| legacy GC capped tree, phase-aligned relative L2 diagnostic | `0.7437216321291179` |
| legacy GC capped tree, phase-aligned L-infinity diagnostic | `0.055567614357418124` |
| legacy GC capped tree, raw norm ratio | `1.13704734` |
| immediately after operation 99, cross-thread phase-aligned L2 diagnostic | `2.07e-14` |
| immediately after operation 100, cross-thread phase-aligned L2 diagnostic | `0.0640457` |
| operation-100 cross-thread infidelity | `0.00410` |
| operation-100 cross-thread relative norm diagnostic | `0.000451` |

The operation-100 pulled word was transcribed as
`+YXXZIZYIXXYZII`. Its registered legacy route was

```text
(0,1), (1,2), (1,8), (2,3), (2,9), (3,4),
(3,10), (4,5), (4,11), (5,6)
```

The first large split divergence occurred at split index three on edge
`(2,3)`, with exact pre-compression dimension 64 and kept dimension 32:

```text
one-thread  s[30:36] =
0.06009836, 0.05752434, 0.05581595, 0.05384161, 0.04941039, 0.04282414
one-thread  s32/s33 = 1.036669
one-thread  discarded_fraction = 0.00639537

four-thread s[30:36] =
0.06249813, 0.05483622, 0.05150589, 0.04793997, 0.04707771, 0.04188256
four-thread s32/s33 = 1.074383
four-thread discarded_fraction = 0.00332342
```

## Program-level inference

The exact tree lowerer extends routed gauges as
\(g'_e=g_e\otimes\mathbf 1_r\). That operation is an exact representation
rule. The legacy path then passes the resulting representation-only gauges to
Quimb simple update as local environment weights. The observed pattern is
consistent with the following project inference:

1. uncapped, nearly degenerate identity splits choose different internal
   bases under different BLAS reductions while preserving the physical state;
2. the finite cap subsequently chooses a representation-dependent subspace;
3. later splits amplify the first physical discrepancy.

This is `[ours]` bug localization, not a theorem from Evenbly or Quimb. A
committed fresh-process regression must reproduce the legacy failure under
the same envelope and then test the repaired native path. That regression
must use the repository's registered no-phase-fit raw metrics; the
phase-aligned values above remain non-claim-bearing historical diagnostics.

## Required replacement evidence

The repair is not accepted from this note. The committed regression must:

- materialize raw complete vectors after operations 99 and 100;
- apply the registered finite/nonzero/raw-norm gates and symmetric
  `d_rel`, `d_norm`, `F_raw`, clipping-order semantics;
- require the legacy lane to violate at least one registered cross-thread
  band at operation 100;
- compare the repaired native lane under the same fresh-process envelope;
- retain independent dense comparisons as report-only development evidence;
- persist environment, source, fixture, raw-vector, and result hashes.

