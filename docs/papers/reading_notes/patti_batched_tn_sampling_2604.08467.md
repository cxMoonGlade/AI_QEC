# Reading note (精读): Patti et al., "Accelerating Quantum Tensor Network Simulations with Unified Path Variations and Non-Degenerate Batched Sampling" (arXiv:2604.08467)

> **Provenance (2026-07-06): FULL-TEXT read (精读).** PDF → txt `outputs/papers/2604.08467.txt`
> (11 pages). All §/Eq refs from that text. NVIDIA-authored paper extending Pre-Trajectory
> Sampling with Batched Execution (PTSBE) to tensor networks.
> Adjudication target: does this paper's batched contraction framework (UPV + NBS) provide
> the blueprint for batching our 70-90 independent small operator calls per syndrome round,
> and what are the optimal batch sizes? **Verdict: YES — UPV eliminates repeated contraction
> path finding (our per-operator overhead), NBS batches over shots eliminating serial shot
> collection, and flexible batch sizing shows b=10 is optimal for 282 qubits/s vs b=24 at
> 11 qubits/s (25× improvement). This precisely addresses our "many independent small
> contractions → batch to approach peak" problem.**

## Metadata [paper]
- **Authors:** Taylor Lee Patti, Paavai Pari, Yang Gao, Azzam Haidar, Thien Nguyen, Tom Lubowe,
  Daniel Lowell, Brucek Khailany (NVIDIA)
- **Venue / status:** arXiv:2604.08467v1 [quant-ph], 9 Apr 2026
- **Type:** algorithm / systems (batched tensor network trajectory sampling)

## Executive summary [paper]
Three innovations dramatically accelerate tensor network trajectory simulations, building on
PTSBE (Pre-Trajectory Sampling with Batched Execution):

1. **Unified Path Variations (UPV):** Error operators are fused into neighboring gate tensors
   (a lightweight tensor merge), preserving the tensor network topology. This means a single
   contraction path P^j suffices for ALL error patterns, eliminating the CPU-dominant path
   finding overhead. **One path find, E×m reuses.**
2. **Non-Degenerate Batched Sampling (NBS):** Instead of 1 shot per contraction loop, collect
   multiple bitstrings per batch. Two modes: proportional (preserves quantum statistics) and
   non-proportional (max data for ML). The final batch B_f is exhaustively sampled from the
   2^{b_f} population vector.
3. **Flexible batch size optimization:** Exposes all b_j as tunable hyperparameters. The default
   CUDA-Q batch size b=24 is shown to be 25× less efficient than the optimal b=10.

Results: **non-proportional: up to 10⁸× data collection speedup; proportional: up to 10³×.**
These are vs the CUDA-Q `tensornet` baseline on identical H100 GPUs.

## Key equations / methods [paper]

### Standard trajectory TN sampling (§II.B, Fig. 1)
For m shots, an n-qubit circuit with g gates:
1. For each shot k=1..m: sample error operators → build TN T^D_i → CPU path finding for
   each error set → per-batch contraction → sample 1 bitstring per batch → repeat
2. Contraction paths P^j_i must be found independently for each error set K_i (different
   TN topology due to different error insertion locations)
3. Fixed batch size b (CUDA-Q default: b=24)
4. **One shot per full contraction loop**

Cost per shot: O(path_finding + f×contraction), where f = ceil(n/b) batches.
Path finding is CPU-dominant (tens to hundreds of seconds, Fig. 6 center panel).

### Unified Path Variations (UPV) (§III.A, Fig. 2)
Key insight: if errors are modeled as single- or two-qubit channels adjacent to gates of
the same size, the error tensors can be **fused (contracted) into the neighboring gate
tensor** before path finding:
```
T_fused[d_l, k_p] = contract(T_gate[d_l], T_error[k_p])
```
After fusion:
- Same tensor network structure (same operand number, shape, topology, rank) as the
  error-free network
- One contraction path P^j suffices for ALL error sets
- Error fusion is a lightweight local contraction: "Values change, topology preserved"

**Path finding cost: O(1) instead of O(E).** For large E (thousands of error sets), this
is effectively zero amortized cost.

### Non-Degenerate Batched Sampling (NBS) (§III.B)

For each error set K_i with m_i assigned shots:

**Proportional NBS (preserves quantum statistics):**
- Batch B_1: one contraction → sample m_i bitstrings from resulting 2^{b_1} probability vector
- Batches B_j (j>1): for each unique prefix (s_1,...,s_{j-1}), contract once → sample conditional
- Total contractions = 1 + Σ_j (number unique prefixes at j-1)
- Strict improvement over traditional: never repeat identical prefixes

**Non-proportional NBS (max data for ML):**
- Same as proportional for batches B_1..B_{f-1}
- Final batch B_f: **exhaustive sampling** — gather all population entries above user-specified
  threshold from the 2^{b_f} population vector
- Can collect orders of magnitude more shots from B_f at near-zero marginal cost
- Exhaustive sampling used for all non-proportional benchmarks in this paper

### Flexible batch size optimization (§III, Fig. 7)
Measured per-batch contraction + sampling times for varying b (n=100, g=600 circuit):

| Batch size b | Time (ms) | Qubits/s |
|-------------|-----------|----------|
| 2 | 22.9 | 87 |
| 5 | 37.4 | 134 |
| **10** | **35.4** | **282** |
| 15 | 71.3 | 210 |
| 20 | 368.6 | 54 |
| 24 (CUDA-Q default) | 2176.8 | 11 |
| 28 | 24996.1 | 1.1 |

**Optimal b=10: 282 contracted qubits/s vs CUDA-Q default b=24: 11 qubits/s — 25× improvement.**
"The default CUDA-Q value of b_j=24 is actually an expensive batch-size selection."

For non-proportional sampling with final batch B_f: b_f=28 is the practical maximum on a
single H100 80GB (2^{28} complex128 population vector). Larger b_f requires multi-GPU.

### Contraction path finding vs contraction time (§V, Fig. 6)
For all tested regimes (n=50-200, g=200-1000):
```
path_finding_time ≈ 10-1000 seconds
contraction_time_per_shot ≈ 10^{-5}-10^{-1} seconds
ratio (path_finding / contraction) ≈ 10²-10⁷
```
"This consistently high ratio indicates that repeated path finding fundamentally limits
the acceleration of unoptimized tensor network trajectory simulations." → UPV makes this
ratio irrelevant.

### Performance results (§V)

#### Non-proportional (Fig. 3, 4)
| n (qubits) | g (gates) | Speedup vs CUDA-Q |
|-----------|----------|-------------------|
| 50 | 400 | ~10⁴× |
| 100 | 600 | ~10⁶× |
| 200 | 1000 | ~10⁸× |
| All converge to ~10⁸× | for deep enough circuits |

Speedup grows with circuit depth (g/n): deeper circuits populate more states, giving
exhaustive final-batch sampling more shots to extract.

Final batch size scaling (n=200):
```
b_f=24: ~10⁶× speedup
b_f=26: ~10⁷× speedup (≈4× over b_f=24)
b_f=28: ~10⁸× speedup (≈4× over b_f=26)
```

#### Proportional (Fig. 5)
| n (qubits) | g (gates) | Speedup vs CUDA-Q |
|-----------|----------|-------------------|
| 100 | 600 | ~10²-10³× |
| 200 | 1000 | ~10²-10³× |

Speedup is **independent of shot count m_i** (within 1σ over 3 orders of magnitude of m_i).
The speedup comes entirely from UPV (eliminating path finding) and flexible batch sizes
(using b=10 instead of b=24).

### Circuit generation (§IV.B)
Random circuits: single-qubit gates (H, X, Y, Z, T, Rx) + two-qubit nearest-neighbor
controlled gates (CX, CY, CZ, CH, CRx), 20% two-qubit. Noise: single-qubit Pauli (X, Y, Z)
and two-qubit depolarization, error probabilities uniform on [0.02, 0.2].

Hardware: H100 80GB, CUDA 12.9.0, cuQuantum v26.01.0, cuTensorNet v2.11.00, CuPy v2.2.3.
Baseline: CUDA-Q v0.13.0. Complex128 precision.

## Relevance to project [ours]
**Dimension: batched contraction blueprint for our 70-90 independent small operator calls.**

1. **UPV (§III.A) directly applies to our per-round operator fusion:** Our 70-90 quimb operator
   calls per round are each a small independent contraction. UPV shows that fusing error/gate
   tensors while preserving topology allows a single cached contraction path. Analogously,
   **fusing our 70-90 per-round operators into a single XLA-compiled kernel eliminates the
   path-finding overhead for each call.**

2. **NBS batch size optimization (§III.B, Fig. 7) is the key quantitative finding for us:**
   The optimal b=10 (282 qubits/s) vs b=24 (11 qubits/s) is a 25× improvement. Our per-round
   operators act on O(10) qubit subsystems — exactly in the b=5-15 sweet spot. **Smaller
   batches pack more efficiently, and our tensors are small enough to benefit.**

3. **Exhaustive final-batch sampling (§III.B):** For non-proportional use cases (e.g., generating
   training data for AI decoders), the 2^{b_f} population vector with b_f=28 can be dumped
   directly. This maps to our syndrome trajectory post-processing: after the MCWF integration,
   the final readout distribution can be exhaustively sampled.

4. **Embarrassing parallelizability over error sets (§III):** "Optimized tensor network PTSBE
   is an embarrassingly parallelizable HPC algorithm, as it can scale to as many GPUs as error
   sets E studied." Our GPU-serialized constraint means we process one E at a time, but each
   E can batch m_i shots internally via NBS.

5. **Path-finding ratio (§V, Fig. 6):** The 10²-10⁷ ratio of path finding to contraction time
   explains why our per-operator Python dispatch is so expensive relative to the actual tensor
   work. Eliminating it (via UPV/operator fusion) is the single highest-impact optimization.

6. **Proportional vs non-proportional distinction (§III.B):** For mechanism recovery (where we
   must preserve Born-rule statistics), we need proportional sampling. The 10³× speedup here
   is from UPV + flexible batch sizes alone — no statistical compromise. For training-data
   generation (AI decoders), non-proportional gives 10⁸×.

## Limitations
- **No MPS-specific results:** The paper benchmarks exact tensor network contraction, not MPS.
  The batching dynamics may differ for MPS (where SVD truncation intermediates are stateful).
- **Random circuits only (§IV.B):** All benchmarks are on random circuits with specific gate
  distributions (20% two-qubit). Structured circuits (like our syndrome extraction with
  periodic CNOT ladders and mid-circuit measurements) may have different optimal batch sizes.
- **Final batch size capped at b_f=28 (§V.A):** This is a single-GPU memory limit for 2^28
  complex128 population vector. Our 65 GB cap may allow b_f=29-30, but this is not characterized.
- **No mid-circuit measurement handling:** The paper's circuits have terminal measurements only.
  Our syndrome extraction has mid-circuit measurements that collapse the state — NBS's
  prefix-projection scheme applies but may interact differently with non-terminal measurements.
- **1 hypersample for fairness (§IV.C):** "use 1 hypersample per contraction path, as this
  increases contraction times and decreases path-finding times." This is a conservative choice
  for speedup ratio but may underestimate the absolute performance achievable with more
  optimization iterations.
- **GPU memory transfer model (§IV.C.2):** The 128-byte transfer bottleneck is characterized
  for Grace Hopper's unified memory. On our RTX 5090 (discrete GPU), the PCIe transfer
  overhead may be larger, making fusion even more important.

## Tags
- `[paper]` PTSBE = Pre-Trajectory Sampling with Batched Execution (extended to TN)
- `[paper]` UPV = Unified Path Variations: fuse error→gate tensors → same topology → one path for all errors
- `[paper]` NBS = Non-Degenerate Batched Sampling: collect multiple bitstrings per batch
- `[paper]` Optimal batch size b=10: 282 qubits/s vs b=24 default: 11 qubits/s (25× improvement)
- `[paper]` Non-proportional: up to 10⁸× speedup; proportional: up to 10³× (both vs CUDA-Q)
- `[paper]` b_f=28 max final batch for single H100 80GB (2^28 complex128 pop vector)
- `[paper]` Path finding / contraction ratio: 10²-10⁷ — path finding dominates
- `[paper]` Embarrassingly parallel over error sets E × GPUs
- `[ours]` UPV = blueprint for fusing our 70-90 per-round operators into single XLA kernel
- `[ours]` b=10 optimal batch size matches our O(10) per-operator qubit subsystem
- `[ours]` Eliminating path-finding overhead (equivalent to per-operator Python dispatch) is highest-impact optimization
- `[ours]` Proportional sampling (10³× speedup) preserves quantum statistics for mechanism recovery
- `[ours]` Non-proportional (10⁸×) for AI decoder training data generation
- `[ours]` Caveat: no MPS-specific results; mid-circuit measurements not tested
