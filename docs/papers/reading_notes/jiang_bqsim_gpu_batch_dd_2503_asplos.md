# Reading note (精读): Jiang et al., "BQSim: GPU-accelerated Batch Quantum Circuit Simulation using Decision Diagram" (ASPLOS '25)

> **Provenance (2026-07-06): FULL-TEXT read (精读).** PDF → txt `outputs/papers/asplos2025_bqsim.txt`
> (17 pages). All §/Eq refs from that text.
> Adjudication target: does the task graph-based batched execution + DD-to-ELL conversion
> approach apply to our 70-90 quimb operator calls per syndrome round? **Verdict: YES —
> the task graph overlap of kernel execution and data movement, plus the DD-based gate
> fusion for reduced MACs, are directly relevant to batched MPS operator application.**

## Metadata [paper]
- **Authors:** Shui Jiang, Yi-Hua Chung, Chih-Chun Chang, Tsung-Yi Ho, Tsung-Wei Huang
  (CUHK / UW-Madison)
- **Venue / status:** ASPLOS '25, March 30-April 3, 2025, Rotterdam, Netherlands
- **Type:** systems (GPU-accelerated batch quantum circuit simulation using decision diagrams)

## Executive summary [paper]
Introduces **BQSim**, a GPU-accelerated batch quantum circuit simulator for **BQCS**
(batch quantum circuit simulation — simulating the same circuit across many input states).
Three-stage pipeline:

1. **BQCS-aware gate fusion** using Decision Diagrams (DD): exploits matrix sparsity and
   regularity to reduce MAC operations. Defines BQCS cost = max non-zero elements per row
   (NZR) of the gate matrix, computed efficiently via DD-based NZR vector (NZRV) traversal.
   Fuses diagonal/permutation gates (cost 1), pairs of cost-2 gates, then greedy fuses
   remaining.

2. **DD-to-ELL conversion:** converts fused gates from CPU-centric DD representation to
   GPU-efficient ELL sparse format. Hybrid (CPU/GPU) selection based on DD edge count
   threshold. ELL chosen because quantum gate NZRs are nearly uniform across rows
   (CV ~0–0.0328), minimizing thread divergence.

3. **Task graph-based execution:** models BQCS kernels and data movement as a task graph
   with dependency scheduling via CUDA Graph. Uses double-buffered memory (2 buffers for
   even batches, 2 for odd) to overlap kernel execution with CPU-GPU data transfers.

Results: 3.25x faster than cuQuantum, 159.06x faster than Qiskit Aer, 311.42x faster than
FlatDD on 16 MQT-Bench circuits (6–21 qubits). Ablation: gate fusion = 1.39–6.73x speedup,
DD-to-ELL = 5.55–35.08x, task graph = 1.46–1.73x. Scales with batch size (speedup
increases from ~2.16x at batch=32 to ~2.52x at batch=512 for VQE n=16).

## Key equations / algorithms [paper]

### BQCS cost = max NZR (non-zero elements per row)
```
Cost(M) = max_{row r} NZR(r)
```
where NZR(r) = number of non-zero elements in row r of gate matrix M.
Computed efficiently via DD-based NZR vector (NZRV):

**NZRV algorithm (Figure 3):**
- DFS traverse DD nodes; each node = sub-matrix
- Leaf nodes (constant-one, constant-zero) have NZRVs [1, 0]^T or [1, 1]^T
- Internal nodes: NZRV = DDConcatenate( DDAdd(child_top, child_bottom),
  DDAdd(child_bottom, child_top) ) — native DD operations
- Final cost = max value in root's NZRV

### Gate fusion steps (Figure 4):
1. Fuse consecutive diagonal/permutation gates (all cost 1) → fused gate stays cost 1
2. Fuse pairs of cost-2 gates → fused gate cost 4 (same total cost, but fewer memory ops)
3. Greedy fusion: fuse if resulting gate cost < sum of individual costs

### ELL format for quantum gate matrices:
```
ELL_value[i][j]     = non-zero value at row i, j-th non-zero column
ELL_colidx[i][j]    = column index for ELL_value[i][j]
#columns = max_NZR (rows with fewer non-zeros are zero-padded)
```

### DD-to-ELL GPU conversion (Algorithm 1):
- One CUDA block per row of gate matrix
- Block runs iterative DFS with edge_stack, left_right[qubit], up_down[qubit] arrays
- up_down array initialized from block index (determines which half of matrix)
- On reaching constant-one node: write (val × edge_weight, col_idx) to ELL matrices
- Uses shared memory for stack and direction arrays

### Task graph memory buffers:
```
For batch IB, kernel k:
  input = D[2*(IB%2) + (floor(IB/2)*(L+1) + k) % 2]
  output = D[2*(IB%2) + (floor(IB/2)*(L+1) + k + 1) % 2]
```
where L = number of BQCS kernels per batch, D = 4 memory buffers.

Allows overlap: kernel k of batch B runs simultaneously with:
- memcpy of batch B+1 input to GPU (in different buffer)
- memcpy of batch B-1 output from GPU

### Performance numbers (selected, Table 2):
| Circuit | #Qubits | #Gates | cuQuantum | Qiskit Aer | FlatDD | BQSim |
|---------|---------|--------|-----------|------------|--------|-------|
| QNN     | 17      | 934    | 246,280   | 1,663,228  | >24h   | 24,218 ms |
| VQE     | 16      | 78     | 24,619    | 874,623    | 2,443,323 | 10,026 ms |
| Portfolio | 16    | 424    | 56,934    | 1,035,447  | 3,393,370 | 11,159 ms |

### Ablation study speedups (Figure 13):
- Without gate fusion: 1.39–6.73x slower
- Without DD-to-ELL (using DD on GPU directly): 5.55–35.08x slower
- Without task graph: 1.46–1.73x slower

### Runtime breakdown (Figure 12):
- For N=10 batches: simulation 42–56%, gate fusion 16–42%, DD-to-ELL 2–42%
- For N=200 batches: simulation 93%, gate fusion 2%, DD-to-ELL 5% — overheads amortized

## Relevance to project [ours]

**Three-stage pipeline maps to our MCWF-on-MPS batched execution needs:**

1. **BQCS-aware gate fusion** → **operator fusion across our 70-90 ops/round:**
   - Our 70-90 quimb operator calls per syndrome round = equivalent to circuit gates
   - Fusing consecutive diagonal/structured operators reduces total MPS apply calls
   - The DD-based NZR cost metric could map to MPS bond-dimension cost rather than
     MAC count — **we need an MPS-cost analogue of NZR**
   - Greedy fusion criterion: fuse if bond_dim(fused_op) < sum(bond_dim(individual_ops))

2. **DD-to-ELL conversion** → **quimb MPS operator compilation:**
   - The ELL conversion principle: transform operators into a GPU-efficient format ONCE,
     then reuse across all batch executions
   - For our quimb MPS: compile MPO representations of fused operators once, reuse
     across all trajectories in the batch
   - Avoids the cost of per-trajectory MPO construction (which is the equivalent of
     per-shot DFS in DD)

3. **Task graph execution** → **overlap MPS evolution with data transfer:**
   - Our pattern: each round = evolve MPS (GPU) → measure syndrome → transfer to CPU
     for decoding → conditional operations for next round
   - Double-buffered approach: while trajectory group A's MPS is evolving, copy
     trajectory group B's syndrome data between CPU-GPU
   - The task graph concept maps to our per-round dependency DAG: each round's
     evolution depends on the previous round's measurement outcome

4. **Batch-size scalability (Figure 10):**
   - BQSim's speedup increases with batch size, saturating at memory bandwidth limit
   - Our many-shot regime (thousands of trajectories) is exactly this sweet spot
   - 65 GB memory cap: this limits batch size; the task graph approach maximizes
     use of whatever batch fits in GPU memory

5. **Specific applicability:**
   - Our JC shared-mode: the mode (density distribution) is the "input state" that
     is batched; each trajectory is a "shot" from this distribution
   - The 70-90 ops/round: these are the "gates" that BQSim fuses and compiles
   - Task graph dependency: subsequent round depends on previous round's syndrome

## Limitations
- Demonstrates only NOISELESS statevector simulation (ideal circuits); does not address
  noise channels, stochastic jumps, or mid-circuit measurements
- Requires all input states in batch to have the SAME circuit (our trajectories do,
  but with stochastic noise → different effective circuit per trajectory)
- DD-to-ELL conversion requires the gate matrix to fit in GPU memory — for large n,
  dense fused gates may exceed memory (even in ELL sparse format)
- Custom CUDA kernel for ELL spMM — we would need to write equivalent "ELL-based MPS
  apply" or demonstrate that quimb's existing operators are already efficient
- Maximum 21 qubits demonstrated; scaling to larger qubit counts requires multi-GPU or
  circuit partitioning
- The gate fusion cost model (max NZR) assumes uniform row distribution — true for
  ideal gates, but noisy/stochastic channels may have different sparsity patterns
- Evaluated on GPU with 48 GB memory; our 65 GB cap is close but the memory model
  (buffer allocation, batch-size limits) needs recalibration

## Tags
- `[paper]` BQCS = batch quantum circuit simulation (many inputs, same circuit)
- `[paper]` BQSim: 3-stage pipeline (gate fusion → DD-to-ELL → task graph execution)
- `[paper]` BQCS cost = max non-zero elements per row (NZR)
- `[paper]` DD-based NZRV computation via DFS + DDConcatenate/DDAdd native ops
- `[paper]` global CUDA Graph scheduling on CPU (overlaps kernel + data movement)
- `[paper]` 3.25x vs cuQuantum, 159x vs Qiskit Aer, 311x vs FlatDD
- `[paper]` ablation: gate fusion 1.4-6.7x, DD-to-ELL 5.6-35.1x, task graph 1.5-1.7x
- `[paper]` hybrid DD-to-ELL conversion (CPU/GPU switch based on DD edge count)
- `[paper]` double-buffered memory: 4 buffers for overlapping batches
- `[ours]` fuse 70-90 quimb ops/round using MPS-cost analogue of NZR
- `[ours]` compile MPO representations once, reuse across batch trajectories
- `[ours]` task graph: overlap MPS evolution with syndrome data transfer
- `[ours]` batch-size scalability → our many-trajectory sweet spot under 65 GB cap
