# Reading note (精读): Patti et al., "Augmenting Simulated Noisy Quantum Data Collection by Orders of Magnitude Using Pre-Trajectory Sampling with Batched Execution" (arXiv:2504.16297)

> **Provenance (2026-07-06): FULL-TEXT read (精读).** PDF → txt `outputs/papers/2504.16297.txt`
> (8 pages). All §/Eq refs from that text.
> Adjudication target: can the PTSBE decoupling of noise sampling from state propagation
> be adapted to our MCWF-on-MPS (quimb) batched trajectory framework? **Verdict: YES —
> the core idea of pre-computing Kraus draws before state evolution and batching shots
> from a single prepared state maps directly to our per-syndrome-round batched JC
> trajectory pattern.**

## Metadata [paper]
- **Authors:** Taylor Lee Patti, Thien Nguyen, Justin Gage Lietz, Alexander J. McCaskey, Brucek Khailany (NVIDIA)
- **Venue / status:** arXiv:2504.16297v1 [quant-ph], Apr 2025 → SC '25 (ACM, St. Louis, MO USA)
- **Type:** systems + algorithm (GPU-accelerated trajectory simulation with pre-sampling)

## Executive summary [paper]
Introduces **Pre-Trajectory Sampling with Batched Execution (PTSBE)**, a two-stage method
that decouples stochastic noise sampling from quantum state evolution. Stage 1 (PTS)
pre-computes all stochastic decisions — error types, locations, Kraus operator selections —
before any statevector propagation. Stage 2 (BE) prepares the quantum state once per
Kraus-operator set and then batches all desired shots from that state without redundant
state re-preparation. Three key innovations:

1. **Tailored error injection:** sampling algorithms can target specific Kraus operator
   subsets (proportional, probability-banded, most-likely-error combinatorial, etc.)
2. **Batched trajectory execution:** groups trajectories sharing identical noise patterns,
   eliminating redundant circuit recompilation and state initialization
3. **Error provenance tracking:** lightweight metadata tags (which Kraus operators were
   drawn per trajectory) attached to each shot — enables supervised training labels for
   ML decoders

Demonstrated on: (a) 35-qubit magic state distillation (MSD) circuit with statevector
backend — up to **10^6x speedup** over conventional trajectory methods; (b) 85-qubit MSD
preparation circuit with tensor network backend — **16x acceleration**. Generated datasets
of 1 trillion shots (statevector) and 1 million shots (tensor network), consuming 4,445
and 2,223 H100 GPU-hours respectively on NVIDIA's Eos DGX Superpod.

Now available in CUDA-Q 0.14.0 as `cudaq.ptsbe.sample()`, claiming >10^7x speedup for
non-proportional sampling.

## Key equations / algorithms [paper]

### Traditional trajectory method (Algorithm 1)
```
for operator in operatorSequence:
    apply gate matrix
    noiseChannel ← lookUp(noiseModel, operator)
    r ← cuRAND()
    if noiseChannel is unitaryMixture:
        k = index(r, {p_i})
        applyMatrix(U_k)
    else:
        p_i ← ⟨ψ|K_i^† K_i|ψ⟩          # state-dependent probability
        k = index(r, {p_i})
        applyMatrix(K_k / sqrt(p_k))
```

### PTSBE: two-stage decomposition

**Stage 1 (PTS) — Kraus operator pre-selection (Algorithm 2):**
```
Input: NoisyCircuit({K}, {p}), nsamples, nshots
KrausSets, KrausShots = [], []
for sample in range(nsamples):
    KrausSample = []
    for K, p in NoisyCircuit({K}, {p}):
        r ← randomUniform(0, 1)
        if r ≤ p:
            if compatible(K, KrausSample):
                KrausSample.append(K)
    if uniqueKraus(KrausSample, KrausSets):
        KrausSets.append(KrausSample)
        KrausShots.append(nshots)
Returns: KrausSets, KrausShots
```

**Stage 2 (BE) — batched shot collection:**
- For each unique Kraus operator set, prepare the quantum state ONCE
- Sample all m_alpha desired bitstrings (polynomial complexity after state is prepared)
- Trivially parallelizable across trajectories (embarrassingly parallel)

### Key performance formula
Batched speedup ~ (shots_per_Kraus_set) × (fraction_unique_shots). For 35-qubit:
- ~10^6x speedup at batch sizes of 10^6–10^7 shots
- >0.5 fraction unique shots even at 10^6 total shots (from 2^35-dimensional space)

### Unitary-mixture vs general Kraus channels
- Unitary mixture: K_i = sqrt(p_i) U_i → probability is STATE-INDEPENDENT → no expectation
  value calculation per trajectory
- General Kraus: requires ⟨ψ|K_i^† K_i|ψ⟩ → this distinction is orthogonal to PTSBE

## Relevance to project [ours]

**Directly applicable to our MCWF-on-MPS batched trajectory problem:**

1. **Our pattern matches PTSBE's sweet spot:**
   - Each syndrome round = 70-90 small quimb operator calls (MPS apply)
   - We need *many independent shots* (many trajectories)
   - Our noise model has a finite set of Kraus operators per round

2. **PTS applied to JC shared-mode trajectories:**
   - Pre-sample ALL stochastic noise decisions (jump/no-jump per operator, measurement
     outcomes) before any quimb MPS evolution
   - Group trajectories with identical noise patterns → prepare state ONCE per group
   - The JC shared-mode structure means many trajectories share the same noise
     trajectory up to the first stochastic divergence

3. **Batched shot collection:**
   - After MPS is evolved to the end of a round, sample all desired measurement
     bitstrings without re-evolving
   - Our per-round measurement output (syndrome) is exactly the "shot" PTSBE batches

4. **Memory consideration for 65 GB GPU cap:**
   - PTSBE's "prepare once, sample many" reduces peak memory by avoiding redundant
     state copies
   - Each MPS resides on GPU; batching shots avoids duplicate MPS evolution
   - The KrausSets metadata is lightweight (small integers — which error per location)

5. **Error provenance for our labels:**
   - In our teacher setting, we know ground-truth errors per trajectory
   - PTSBE's provenance metadata maps directly to training labels for our
     learner/decoder validation

## Limitations
- Primary demonstrations use statevector backend (35 qubits); the tensor-network
  backend (85 qubits) shows only 16x speedup — limited by CUDA-Q's lack of
  contraction-path caching and adaptive correlated sampling (noted as future work)
- PTSBE's speedup is largest for **unitary-mixture channels** (state-independent
  probabilities); our JC shared-mode Lindblad noise may have state-dependent jump
  probabilities, reducing the pre-sampling advantage
- Non-proportional (targeted) sampling gives the largest claimed speedup (>10^7x),
  but this is for non-uniform distributions — our use case may need full distribution
  coverage
- Multi-GPU distribution (required for 35+ qubits statevector) is assumed; our single-GPU
  65GB cap may limit the qubit count where PTSBE shines
- No explicit treatment of mid-circuit measurements with feedforward (our syndrome
  extraction pattern)

## Tags
- `[paper]` PTSBE = Pre-Trajectory Sampling + Batched Execution
- `[paper]` decouples noise sampling from state propagation
- `[paper]` prepare-once, sample-many: state preparation cost amortized over shots
- `[paper]` error provenance metadata for supervised ML training
- `[paper]` unitary-mixture channels have state-independent probabilities
- `[paper]` 35-qubit: 10^6x speedup; 85-qubit TN: 16x speedup
- `[paper]` CUDA-Q 0.14.0: `cudaq.ptsbe.sample()`
- `[ours]` directly applicable: MCWF-on-MPS with 70-90 ops/round, many shots
- `[ours]` pre-sample jumps → group identical noise patterns → evolve once per group
- `[ours]` syndrome measurement = the "shot" PTSBE batches
- `[ours]` error provenance = training labels for learner/decoder
