# Reading note (精读): Schieffer et al., "Harnessing CUDA-Q's MPS for Tensor Network Simulations of Large-Scale Quantum Circuits" (arXiv:2501.15939)

> **Provenance (2026-07-06): FULL-TEXT read (精读).** PDF → txt `outputs/papers/2501.15939.txt`
> (10 pages). All §/Eq refs from that text. An evaluation of CUDA-Q's GPU-accelerated MPS simulator
> (backed by cuTensorNet) on Grace Hopper hardware.
> Adjudication target: does this paper characterize the GPU bottlenecks we will face in
> GPU-accelerating our MPS trajectories, and does its profiling guide our kernel fusion strategy?
> **Verdict: YES — the profiling reveals that SVD under-utilizes GPU (33% activity, <1% Tensor
> Cores) and small data transfers (128 bytes per operation) dominate the contraction phase.
> This directly motivates our need for operator fusion to eliminate per-element launch overhead.**

## Metadata [paper]
- **Authors:** Gabin Schieffer, Stefano Markidis, Ivy Peng (KTH Royal Institute of Technology)
- **Venue / status:** arXiv:2501.15939v1 [quant-ph], 27 Jan 2025; pre-print submitted for publication
- **Type:** experimental evaluation / performance characterization (GPU-accelerated MPS simulation)

## Executive summary [paper]
Evaluates CUDA-Q's tensor network simulators (exact TN and approximate MPS, both backed by
cuTensorNet) on an Nvidia Grace Hopper Superchip (H100 GPU, 96 GB HBM3). Five representative
quantum circuits are benchmarked at up to 90 qubits. Key findings:

1. **Memory scaling:** MPS memory ∼ dnχ², linear in n for fixed bond dimension χ — this is the
   fundamental advantage over state-vector simulation (2ⁿ entries).
2. **Runtime scaling:** MPS runtime scales as t = αn^β (power law) for high-entanglement circuits
   (QAOA, Quantum Volume) and t = an + b (linear) for low-entanglement circuits (GHZ, QFT).
   Both are far weaker than the exponential scaling of state-vector simulation.
3. **SVD dominates but under-utilizes GPU:** 70% of MPS simulation time is GPU-resident SVD
   iterations, but GPU activity averages only 33% and Tensor Core utilization is <1%.
4. **Small transfer bottleneck:** The contraction phase (8% of time) has 60% idle GPU time
   due to host-to-device transfers of only 128 bytes per operation.
5. **Correctness threshold:** Default bond dimension χ_max=64 preserves the 4 most likely
   outcomes of a 10-qubit QAOA circuit; χ_max=16 is the minimum for correctness in this case.

## Key equations / findings [paper]

### Memory requirement (§II.B)
State vector: 2ⁿ complex values (exponential).
MPS: dnχ² parameters, where n = number of qubits, d = local dimension (2 for qubits),
χ = bond dimension. For fixed χ, **memory scales linearly with n**.

Concrete numbers: H100 (96 GB) holds 33 qubits single-precision state vector. For MPS,
60 qubits is routine (all circuits tested), 90 qubits for GHZ — all on a single GPU.

Circuit entanglement ratio R = N_2q / N_total (two-qubit gates / total gates):
- Counterfeit Coin: R = 0.25 (lowest entanglement)
- GHZ: R ≈ (n-1)/n → 1.0 (max entanglement)
- QFT: R ≈ (n+1)/(n+5) → 0.0
- Quantum Volume: R = 1.0 (max entanglement)
- QAOA: R ≈ 3(n-1)/(3n+1) → 1.0

### Runtime scaling (§IV.B)
**State vector:** exponential t ∝ e^αn (reference line for comparison)
**MPS for low-entanglement circuits (GHZ, QFT):** linear t = a·n + b
```
GHZ:   t = 5.53n - 155.16  (R² = 0.99)
QFT:   t = 2.11n - 50.82   (R² = 0.98)
```
**MPS for high-entanglement circuits (QAOA, QV):** power law t = α·n^β
```
QAOA:  t = 0.0017n^3.1644  (R² = 0.999)
QV:    t = 0.0008n^3.5786  (R² = 0.9967)
```
**Both MPS scaling forms are dramatically weaker than exponential state-vector scaling.**

### GPU profiling results (§IV.C)

#### Exact Tensor Network phase distribution
| Phase | Time share | Description |
|-------|-----------|-------------|
| CPU-only | 80% | Tensor network preparation (path finding, contraction ordering) |
| GPU + CPU | 20% | Contraction execution |

#### MPS phase distribution
| Phase | Time share | Description |
|-------|-----------|-------------|
| GPU SVD | 70% | Singular value decomposition iterations (33% avg GPU activity) |
| CPU-only | 22% | Tensor network preparation |
| GPU + CPU | 8% | Contraction execution (60% idle from 128-byte H2D transfers) |

Key profile finding: "the iterations of the SVD algorithm only partially utilize the GPU, as the
average activity reported in the profiling is 33%. This might indicate that the problem is too
small to leverage available GPU resources."

### Tensor Core utilization (§IV.C.2)
"Nsight Systems reports a utilization of Tensor Cores below 1% for both methods, over the whole
execution. This is surprising, as matrix operations performed both for SVD iterations and tensor
contractions can typically leverage Tensor Cores."

### SVD's dual role (§IV.C.2)
"SVD decomposition in MPS to reduce the computational cost of performing the contractions,
induced by the simplification of the tensor network." But the SVD itself is computationally
expensive: the MPS contraction phase (45 ms for 20-qubit QFT, 10 shots) is 5× faster than
exact TN contraction (225 ms for same task), but SVD overhead (1.7s) dominates.

### MPS approximation and correctness (§V)
Bond dimension χ_max vs correctness for a 10-qubit QAOA circuit (100,000 shots):

| χ_max | Correct top-4? | Notes |
|-------|----------------|-------|
| 64 | 4/4 | Default value; matches state-vector reference |
| 32 | 4/4 | Full correctness preserved |
| 16 | 4/4 | Still correct at this bond dimension |
| 15 | 2/4 | First failure point |
| 14 | 2/4 | Two of four top outcomes preserved |
| 13 | 2/4 | |
| 12 | 1/4 | Only one correct in top-4 |
| 8 | 1/4 | Insufficient bond dimension |

"The most likely outcomes [...] are preserved across both methods. This is a key property, as
quantum algorithms often provide an output as an observed state produced with a high probability."

### Cross-over point (§IV.A)
"Comparing the two tensor network methods, we observe that exact tensor network simulation
exhibits a lower execution time than the MPS alternative for number of qubits below 12, after
which the MPS method exhibits a lower runtime." — The SVD overhead only pays off for larger
systems.

## Relevance to project [ours]
**Dimension: GPU acceleration characterization for our MPS trajectories.**

1. **SVD under-utilization (33% GPU activity) is our primary target (§IV.C):** Our 70-90 small
   operator calls per round are exactly the kind of "too small to leverage GPU resources" workload
   described here. Each operator application is a small tensor contraction on modest tensors
   (χ∼10-20, d=2). The per-operator launch overhead dominates.

2. **The 128-byte H2D transfer bottleneck (§IV.C.2) directly motivates operator fusion:**
   "host-to-device memory movements are performed, with small data transfers, on the order of
   128 bytes per operation." If we fuse 70-90 operators into a single XLA kernel (as TC-NG's
   JIT pipeline does), we eliminate 69/70 of these transfers — each of which carries a
   ∼10-50 μs launch overhead.

3. **MPS correctness threshold (§V):** For our JC shared-mode trajectories (O(10) qubits,
   bond dimensions χ∼10-20), the paper suggests χ=16 may be sufficient for preserving the
   most-likely outcomes. However, our requirement is finer-grained (mechanism recovery, not
   just top-k sampling), so we should validate independently.

4. **No advantage of MPS below 12 qubits (§IV.A):** Our current small-window twin (d=3 surface
   code, n=17) straddles this boundary. MPS on GPU may not outperform state-vector simulation
   for such small systems — the SVD overhead is not amortized. We need to benchmark both paths.

5. **Tensor Cores are irrelevant for our workload (<1% utilization):** The fusion strategy
   should target CUDA core utilization via larger fused contractions, not Tensor Core ops.

6. **CPU path finding is significant (§IV.C):** 80% (exact TN) or 22% (MPS) of time is CPU-only
   preparation. For our iterative trajectory sampling, this highlights the importance of caching
   contraction paths (as in PTSBE/UPV from 2604.08467).

## Limitations
- **MPS only evaluated for sampling (cudaq.sample), not for differentiable gradients:**
  the paper only benchmarks shot collection, not the AD/backprop we need for mechanism recovery.
- **Single-precision only:** cuTensorNet MPS uses complex64; our twin uses complex128 for
  accuracy. The memory and speed trade-off at double precision is not characterized.
- **Grace Hopper specific:** results may differ on other GPU architectures (RTX 5090, H200).
  The unified memory of Grace Hopper may affect H2D transfer characteristics.
- **Mid-circuit measurement performance (§IV.A):** The counterfeit coin circuit (which has
  conditional mid-circuit measurements) showed drastically worse performance (4 min TN,
  19 min MPS for 12 qubits) — relevant for our syndrome extraction rounds which involve
  frequent mid-circuit measurements.
- **No performance comparison with quimb MPS:** the baseline was CUDA-Q's own state-vector
  and exact TN backends, not quimb's MPS. Direct quimb→cuTensorNet speedup comparison is
  not provided.

## Tags
- `[paper]` CUDA-Q MPS backed by cuTensorNet on Grace Hopper H100
- `[paper]` MPS memory: dnχ², linear in qubit count for fixed bond dimension
- `[paper]` MPS runtime: linear t=an+b (low-entanglement), power t=αn^β (high-entanglement)
- `[paper]` 70% GPU SVD phase at 33% average activity — severely under-utilized
- `[paper]` 128-byte H2D transfers dominate contraction phase (60% idle)
- `[paper]` Tensor Core utilization <1% for MPS on evaluated workloads
- `[paper]` χ_max=16 minimum for correct top-4 QAOA outcomes (10 qubits)
- `[paper]` MPS beats exact TN only above 12 qubits (SVD overhead cross-over)
- `[ours]` Directly characterizes the GPU bottleneck we face: small tensors + per-operator launch overhead
- `[ours]` Operator fusion is the primary lever: fuse 70-90 operators → one XLA kernel → eliminate launch overhead
- `[ours]` Our small-window twin (n=17) is near the MPS cross-over point; benchmark both SV and MPS paths
- `[ours]` Mid-circuit measurements (syndrome extraction) drastically increase runtime — need fusion
