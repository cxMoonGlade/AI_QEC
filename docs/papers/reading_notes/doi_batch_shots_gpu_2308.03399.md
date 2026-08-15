# Reading note (精读): Doi, Horii, Wood, "Efficient Techniques to GPU Accelerations of Multi-Shot Quantum Computing Simulations" (arXiv:2308.03399)

> **Provenance (2026-07-06): FULL-TEXT read (精读).** PDF → txt `outputs/papers/2308.03399.txt`
> (10 pages). All §/Eq refs from that text.
> Adjudication target: how does Qiskit Aer batch multi-shot into single GPU kernels, and
> does the shot-branching mechanism apply to our mid-circuit noise + many-shot pattern?
> **Verdict: YES — both batch-shots execution and shot-branching are directly relevant;
> the shot-branching tree structure is particularly valuable for our JC shared-mode
> trajectories where many shots share the same initial state evolution.**

## Metadata [paper]
- **Authors:** Jun Doi, Hiroshi Horii, Christopher Wood (IBM Research)
- **Venue / status:** arXiv:2308.03399v1 [quant-ph], Aug 2023 → Qiskit Aer upstream
- **Type:** systems (GPU kernel optimization for multi-shot noisy circuit simulation)

## Executive summary [paper]
Addresses the fundamental GPU inefficiency in multi-shot noisy quantum circuit simulation:
GPUs are good at large, uniform workloads but suffer from kernel launch overheads for
small-qubit circuits and from non-uniform operations caused by noise randomness across
shots. Proposes two complementary techniques:

1. **Batch-shots execution:** gathers multiple shots into a SINGLE GPU kernel program,
   dramatically reducing kernel launch overheads. Noise sampling is done at runtime within
   the batched kernel — ID gates are added for shots where no error occurs, maintaining
   uniform kernel execution across all shots.

2. **Shot-branching:** shares a single quantum state across all shots initially, then
   "branches" the state only when randomness occurs (noise, measurement, reset). This
   creates a tree of states on-the-fly, reducing both computation and memory when the
   number of distinct states is smaller than the number of shots (typical for low error
   rates).

Both techniques implemented in Qiskit Aer. Results: 10x-100x speedup over baseline GPU
implementation; GPU now faster than CPU across all qubit ranges (previously GPU was
slower for <~16 qubits). Works for both Pauli and Kraus noise models.

## Key equations / algorithms [paper]

### Batch-shots mechanism

**Data structure for batched multi-shot GPU kernel:**
Three GPU arrays stored per batch:
- `qubit_register`: probability amplitudes for each shot (sequential layout)
- `classical_bit_register`: measurement outcomes / conditional flags per shot
- `parameter_buffers`: gate parameters (matrices, target/control qubits)

**Shot index calculation within batched kernel:**
```
ishot = i / 2^(nq - ng)
```
where `i` = iteration count in kernel, `nq` = number of qubits, `ng` = gate qubits.

**Pauli noise batch optimization** (four parameters per shot stored in parameter buffer):
```
x_max   = max target bits for X/Y gates
x_mask  = bit mask for X targets
num_y   = number of Y gates (mod 4)
z_mask  = bit mask for Z targets
```
Kernel applies: bit-flip (swap amplitudes using x_mask), rotation (multiply phase from
num_y), phase-flip (popcount of index & z_mask). If ID is sampled for all shots in a
batch, the noise kernel becomes a no-op.

**Kraus noise batch optimization** (Figure 6 described in text):
- All iterations of the Kraus loop run on GPU (no host synchronization needed)
- Classical bit per shot tracks whether matrix multiplication completed
- Loop runs to completion even if all shots have selected their matrix
- Trade-off: unnecessary iterations vs GPU kernel launch overhead

**Measure/reset batch optimization:**
```
rnd = random()
sum = 0
qubits = (list of target qubits)
nq = sizeof(qubits)
dim = 2^nq
for i in dim:
    bit_mask = 0
    for j in nq:
        if ((i >> j) & 1) == 1:
            bit_mask |= qubits(j)
    prob(i) = probability(bit_mask)
    sum += prob(i)
    if rnd < sum at first time:
        reset(bit_mask)
        return prob
```

### Shot-branching mechanism

**Tree structure (on-the-fly):**
1. Start: single quantum state shared by ALL shots
2. At first randomness (noise/measurement), state is BRANCHED: copy to new state, update independently
3. Each shot tracked in a list per state
4. If insufficient GPU memory for new state → store shots in "waiting list"
5. Waiting-list shots re-simulated from the beginning with a new root state
6. Continue until all waiting shots are exhausted

**Key insight:** For low error rates (e.g., 1%), most shots follow the no-error path.
The number of distinct states << number of shots → large memory and computation savings.

**Final measurement optimization:** shot-branching sets allow sampling technique for
final measurement (unlike conventional multi-shot where each shot must be measured
independently).

### Performance results
- **Pauli noise, single GPU:** ~10x speedup over baseline (batch-shots optimization)
- **Kraus noise, single GPU:** 10x-100x speedup (larger gain because Kraus has more
  overhead per shot)
- **Shot-branching + batch-shots:** GPU faster than CPU across ALL qubit ranges
  (10-22 qubits), unlike baseline where GPU was slower for <~16 qubits
- **Multi-GPU (6x V100):** linear scaling for batch-shots; density matrix method limited
  to 16 qubits on 6 GPUs
- **Error ratio dependence:** Pauli noise time increases with error ratio (more
  non-ID operations); Kraus noise time is nearly error-ratio independent (all iterations
  of Kraus loop always execute)

## Relevance to project [ours]

**Two concrete mechanisms for our MCWF-on-MPS batched trajectory engine:**

1. **Batch-shots execution for our 70-90 quimb calls per round:**
   - Our per-operator quimb.MPS.apply calls are the equivalent of per-shot GPU kernels
   - Grouping identical operator sequences across trajectories → single batched apply
   - Our "ID gate" equivalent: trajectories where a specific Lindblad jump does NOT fire
     still need the no-jump evolution — this is the dominant case for low error rates
   - The batched noise scheduling (sampling at runtime within batch) maps to our JC
     shared-mode: pre-roll all jump/no-jump decisions, then batch trajectories that
     share the same pattern

2. **Shot-branching for JC trajectories:**
   - Our JC shared-mode: before the first stochastic jump, ALL trajectories share the
     identical state evolution → perfect shot-branching candidate
   - After each syndrome round, measurement outcomes branch trajectories into at most
     2^(n_ancilla) distinct states
   - At low physical error rates, most trajectories take the "no jump in this round" path
     → the branching factor stays small → large savings
   - The "waiting list" mechanism maps to our 65 GB memory cap: when branching would
     exceed memory, serialize remaining shots sequentially

3. **Memory considerations:**
   - Shot-branching's state-sharing directly addresses our 65 GB cap: we don't need
     N_trajectories × state_memory; we need N_distinct_states × state_memory
   - For d=3 surface code with ~17 qubits and low error rates, N_distinct_states << N_trajectories
   - The waiting-list mechanism gracefully handles memory pressure

4. **GPU kernel design pattern:**
   - Our quimb MPS operations on GPU are the "kernel" calls
   - Batching these across shots with identical noise patterns → single fused quimb call
   - The classical bit register pattern (mask shots for conditional operations) maps to
     our syndrome-dependent operations

## Limitations
- Demonstrated only on QFT circuits, not on QEC circuits with mid-circuit measurements
  and feedforward (our use case)
- Shot-branching re-simulates waiting-list shots from scratch — for deep circuits with
  many branch points, this could lead to exponential blowup if branching factor is large
- Batch-shots for Kraus noise always runs all Kraus iterations even after all shots
  have selected → unnecessary computation when error rate is low
- No explicit MPS / tensor-network integration — the paper uses statevector representation
- Multi-shot distribution uses MPI (high latency); our single-GPU setting doesn't need this
- Does not address the overhead of state-dependent Kraus probabilities
  (⟨ψ|K_i^† K_i|ψ⟩) in the batched context — this is exactly our JC jump case

## Tags
- `[paper]` batch-shots: multiple shots in single GPU kernel → reduces launch overhead
- `[paper]` shot-branching: tree-structured state sharing across shots
- `[paper]` Pauli noise: 4-parameter batch optimization (x_mask, x_max, num_y, z_mask)
- `[paper]` Kraus noise: all iterations on GPU, no host sync; classical bits mask completed shots
- `[paper]` 10x-100x speedup over baseline; GPU now beats CPU across all qubit ranges
- `[paper]` Qiskit Aer implementation (open source)
- `[ours]` shot-branching tree = JC shared-mode before first stochastic divergence
- `[ours]` waiting-list = graceful memory pressure handling under 65 GB cap
- `[ours]` batch operator application = fuse 70-90 quimb calls across trajectories
- `[ours]` ID-gate pattern = no-jump evolution (dominant at low error rates)
