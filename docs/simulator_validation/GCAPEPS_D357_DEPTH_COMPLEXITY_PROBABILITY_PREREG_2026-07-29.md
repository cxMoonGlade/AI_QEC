# GCAPEPS distance/depth/noise-complexity/probability sweep — preregistration

Status: **FROZEN BEFORE GRID IMPLEMENTATION OR TARGET EXECUTION,
2026-07-29.**

This packet supersedes only the target grid, fixed angle, and six-sample
schedule in
`GCAPEPS_D357_UNITARY_PREFIX_PERFORMANCE_PREREG_2026-07-29.md`.
The earlier fixture algebra, complex128 settings, equal-status lanes,
fresh-process isolation, no-truth boundary, and 8-GiB/300-s censoring remain
binding. No target performance result had been executed or inspected when
this extension was frozen.

## 1. Terminology corrections

The earlier \(K=1\) target at compact sites 6, 22, and 44 is the center
**data** site at coordinates \((d,d)\), not an ancilla. The site is
`RX`-initialized only because the checkerboard local-H XZZX transform changes
that data site's preparation basis. This packet corrects the label without
changing the site, prefix, or signed pullback.

`round_layers=L` means repeated coherent H/CX unitary shells on one persistent
state. It does not mean a complete QEC round because measurement, reset,
branch mass, and Record folding are absent.

`error_probability=p_twirl` means
\(\sin^2(\theta/2)\) for the coherent \(R_Y(\theta)\). It is not an observed or
sampled Bernoulli frequency.

## 2. Frozen error-location complexity

For each distance, rank all graph-degree-four active sites by squared physical
distance to \((d,d)\), then compact id. The first four error locations are:

| \(d\) | ordered compact sites | site kinds | coordinates |
|---:|---|---|---|
| 3 | `(6,5,7,12)` | `(data,check,check,check)` | `(3,3),(2,2),(4,2),(2,4)` |
| 5 | `(22,21,23,30)` | `(data,check,check,check)` | `(5,5),(4,4),(6,4),(4,6)` |
| 7 | `(44,43,45,58)` | `(data,check,check,check)` | `(7,7),(6,6),(8,6),(6,8)` |

Noise complexity \(K\in\{1,2,4\}\) selects the first \(K\) sites. At every
selected site the physical operation is

\[
R_Y(\theta(p))=\exp[-i\theta(p)Y/2],
\qquad
\theta(p)=2\arcsin\sqrt p.
\]

Within each layer, sites are applied in the table order. Both candidates must
consume the same physical site/angle ledger. GCAPEPS computes every signed
pullback from its live accumulated frame; the fixture records expected Stim
pullbacks, and an untimed SDIM-qubit control independently replays them.

## 3. Frozen sparse grid

For each \(d\in\{3,5,7\}\), execute these eight unique cells:

| role | \(L\) | \(K\) | \(p_{\mathrm{twirl}}\) |
|---|---:|---:|---:|
| baseline | 1 | 1 | \(10^{-3}\) |
| depth-2 | 2 | 1 | \(10^{-3}\) |
| depth-\(d\) | \(d\) | 1 | \(10^{-3}\) |
| complexity-2 | 1 | 2 | \(10^{-3}\) |
| complexity-4 | 1 | 4 | \(10^{-3}\) |
| low probability | 1 | 1 | \(10^{-4}\) |
| high probability | 1 | 1 | \(10^{-2}\) |
| stress corner | \(d\) | 4 | \(10^{-2}\) |

This is a one-factor-at-a-time design plus one stress corner, not a complete
Cartesian product. It supports descriptive distance, depth, complexity, and
probability slices but not general interaction or asymptotic inference.

For one cell, start once from the product residual and repeat:

```text
for layer in 1..L:
    apply the frozen H/CX prefix
    for target in first_K_error_locations:
        apply physical RY(theta(p)) at target
```

The plain lane physically updates the persistent Quimb state. The GC lane
updates its live Stim frame once per layer and applies every physical rotation
through `GCAPEPSState.apply_pauli_rotation`. Neither lane may restart between
layers.

## 4. Numerical and resource envelope

The common numerical settings remain:

```text
dtype=complex128
max_bond=None
cutoff=1e-12
renorm=false
gauge_smudge=0
equilibrate_every=None
```

The GC multi-update hard guard is:

```text
max_local_operator_elements = 64
max_total_operator_elements = 64 * n
max_local_candidate_tensor_elements = 4_194_304
max_total_candidate_tensor_elements = 16_777_216
max_predicted_bond_dimension = 64
max_routed_rank_product = 64
max_total_bond_growth_product = 64
```

Refactor products remain one. The guard is a preregistered censoring boundary,
not an efficiency theorem or accuracy cap. The \(L=1,K=1\) cell must still
match its tighter exact construction ledger. Later updates report their actual
route, rank-product, bond, and element ledgers. A guard hit is retained as
`RESOURCE_GUARD_CENSORED`.

The process envelope remains 8 GiB, zero swap allowance, and 300 s per fresh
child. Plain Quimb has no hidden finite bond cap. OOM and timeout are retained
as censored outcomes.

## 5. Sampling and metrics

Each of the 24 cells and two lanes has one discarded fresh-process warmup and
three measured fresh-process samples in alternating AB/BA order. Raw samples,
median, and MAD are retained. A ratio is emitted only when all three measured
samples and the warmup complete for both lanes.

Primary time includes all \(L\) prefix updates and all \(LK\) rotations:

```text
plain_update_ns = sum physical_prefix_apply + sum physical_RY_apply
gcapeps_update_ns = sum tableau_prefix_apply + sum certified_tree_rotation_apply
```

Per-cell outputs also include peak RSS, cgroup `MemoryPeak`, maximum bond,
tensor elements, logical bytes, completed layers/rotations, and censor reason.
No complete vector, norm, fidelity, Born mass, Record, or LER is requested.

## 6. Release gates and allowed interpretation

Before target execution:

1. the original \(L=1,K=1\) fixture/worker/SDIM controls pass;
2. the v2 grid fixture freezes all 24 operation ledgers, angles, accumulated
   Stim pullbacks, site kinds, and hashes;
3. SDIM reproduces every accumulated-frame signed pullback;
4. controls detect mutations of \(L,K,p\), site order, angle mapping, frame
   accumulation, persistent-state reuse, cutoff, and censoring limits;
5. the complete grid implementation and tests are committed in a clean
   parent checkout before any target worker starts.

Allowed conclusion: a bounded current-implementation performance/resource
surface over the 24 registered cells.

Forbidden conclusions: physical multi-round QEC correctness, stochastic
trajectory frequency, Record faithfulness, matched state accuracy, a universal
GCAPEPS speedup, small-bond guarantee, efficient PEPS contraction, interaction
model, threshold, or asymptotic scaling law.
