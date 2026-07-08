# Reading note (精读): Zhang et al., "TensorCircuit-NG: A Universal, Composable, and Scalable Platform for Quantum Computing and Quantum Simulation" (arXiv:2602.14167)

> **Provenance (2026-07-06): FULL-TEXT read (精读).** PDF → txt `outputs/papers/2602.14167.txt`
> (33 pages). All §/Eq refs from that text. This is the next-generation successor to TensorCircuit
> (a JAX/TF/PyTorch-native differentiable quantum simulation framework).
> Adjudication target: can TensorCircuit-NG replace the serial quimb hot-loop in our MCWF-on-MPS
> trajectory engine, eliminating per-operator Python overhead via trace-once → XLA compile → operator
> fusion → vmap over shots? **Verdict: YES — the JIT/VMAP pipeline is exactly designed for this
> problem; the `MPSCircuit` with vmap over shots directly addresses our 70-90 operator calls/round
> overhead.**

## Metadata [paper]
- **Authors:** Shi-Xin Zhang, Yu-Qin Chen, Weitang Li, Jiace Sun et al. (Institute of Physics, CAS)
- **Venue / status:** arXiv:2602.14167v1 [quant-ph], 15 Feb 2026
- **Type:** framework / software platform (differentiable quantum simulation + ML integration)

## Executive summary [paper]
TensorCircuit-NG evolves from a circuit simulator into a comprehensive quantum science platform
fusing quantum circuits, tensor networks, and neural networks into a single differentiable computational
graph. Built on JAX/TensorFlow/PyTorch backends, the framework introduces:
1. **Deep interoperability:** quantum circuits as native differentiable layers in PyTorch/Keras via
   DLPack zero-copy cross-framework tensor transfer.
2. **Complex physical modeling:** qudit systems (d>=3), fermion Gaussian states, continuous time
   evolution, and a customizable noise profile engine.
3. **Comprehensive simulation engines:** analog (time-dependent Hamiltonian ODE), stabilizer (Stim
   integration for Clifford), and **approximate MPS (MPSCircuit)** with differentiable SVD truncation.
4. **HPC-ready scalability:** data parallelism (jax.pmap, jax.sharding) and model parallelism
   (DistributedContractor with cotengra tensor slicing for multi-GPU).

The core philosophy: **everything is a tensor** — quantum states, gates, noise channels, and
measurements are first-class tensors in a backend-agnostic computational graph, enabling AD, JIT,
and VMAP at every level.

## Key equations / architecture [paper]

### JAX/XLA compilation pipeline (§I.B)
The trace-once → compile pipeline:
```
vqe_grad = K.value_and_grad(tfim_energy)       # AD through tensor network
vqe_batch = K.vmap(vqe_grad, vectorized_argnums=0)  # batch over params
vqe_step = K.jit(vqe_batch, static_argnums=(2,))    # XLA compile entire graph
```
"The tensor contraction path and the gradient graph are traced once and compiled into optimized
machine code (XLA for JAX/TF) for the target hardware. This removes Python overhead and enables
operator fusion." After compilation, there is zero Python overhead — all operations are fused
XLA kernels.

### vmap mechanism (§I.B, §VII.C)
"VMAP promotes the batch dimension directly into the tensor operations, allowing thousands of
independent circuit instances to be executed simultaneously. This eliminates the overhead of
Python loops and maximizes device utilization."

Demonstrated in MIPT simulation benchmark:
```python
# Parallel trajectory batching with vmap
c = tc.MPSCircuit(n, split={"max_singular_values": 16})
# vmap over hundreds of trajectories
# Single GPU processes thousands of unique quantum trajectories simultaneously
```

### MPSCircuit (approximate MPS simulator) (§V.C)
Fully differentiable MPS with SVD truncation:
```python
c = tc.MPSCircuit(n, split={"max_singular_values": 16})
# Supports same API as Circuit class
# Gradients flow through iterative complex-valued SVD truncation steps
val = c.expectation((tc.gates.z(), [i]), (tc.gates.z(), [i+1]))
```
"Unlike standard tensor network libraries that are often static, TensorCircuit-NG's MPS module
is deeply integrated with the AD engine. This allows gradients to flow through the iterative
complex-valued SVD truncation steps."

Key caveat: "This method is inherently approximate. By truncating the singular value spectrum,
users explicitly trade off numerical precision for the ability to scale to significantly larger
system sizes."

### scan for deep circuits (§VII.B, §VII.C)
Instead of unrolling deep circuits (O(D) compilation cost), `jax.lax.scan` compiles to a
fixed-size loop:
```
final_state, _ = jax.lax.scan(one_layer, c.state(), weights)
# Compilation O(D) → O(1); memory constant regardless of depth
```
Used for deep QML (40-layer MNIST, 30-layer CIFAR-100) and MIPT (40-layer Haar-random).

### Performance benchmarks
| Task | Method | Hardware | Performance |
|------|--------|----------|-------------|
| VQE TFIM (32q, 16L) | DistributedContractor | 8×H200 | 7.5× speedup, 2.38s/step |
| VQE TFIM (40q, 20L) | DistributedContractor | 8×H200 | 18 min/step, 11700 params |
| MIPT (20q, 40L, 1000 traj) | MPSCircuit + vmap | H200 | 84.16s total, 0.084s/traj |
| MIPT (20q, 40L, 1000 traj) | MPSCircuit + vmap | CPU | 1097s total, 1.097s/traj |
| Classical shadows (20q, 256 shots) | JAX GPU | RTX 5090 | 0.29s (10× vs CPU) |
| MNIST QML (10q, 40L, 60k data) | JAX GPU | RTX 5090 | 1.88s/epoch (8× vs CPU) |

### Tensor network object translation (§III.C)
Bidirectional conversion between TensorCircuit-NG and quimb/TeNPy/TensorNetwork:
```python
tc_mps = qu.QuOperator(...)
quimb_tn = qu.qop2quimb(tc_mps)
tc_mps_restored = qu.quimb2qop(quimb_tn)
```

### Noise model engine (§IV.E)
Configurable noise profiles with site-dependent, gate-type dependent, and logic-based noise:
```python
noise_conf.add_noise("cnot", tc.channels.generaldepolarizingchannel(1e-3, 2))
# Site-dependent: higher-index qubits noisier
noise_conf.add_noise("ry", [tc.channels.phasedampingchannel(rate)], qubit=[(i,)])
# Readout error mitigation
mitigator = tc.results.readout_mitigation.ReadoutMit(execute_fn)
```

## Relevance to project [ours]
**Dimension: direct replacement for serial quimb hot-loop in MCWF-on-MPS trajectories.**

1. **Trace-once → XLA compile → operator fusion (§I.B):** Our 70-90 small quimb operator calls
   per syndrome round → each call is a small tensor contraction. With TC-NG, the entire round
   is traced once, compiled into fused XLA kernels. **No per-operator Python overhead.**
   The result: the Python-loop dispatch cost drops to zero after the first trace.

2. **vmap over shots (§VII.C):** Instead of looping over MCWF trajectories sequentially,
   `jax.vmap` promotes the shot dimension directly into tensor operations. The MIPT benchmark
   shows 1000 trajectories at 0.084s each vs 1.097s on CPU (13× GPU speedup). For our
   trajectores, this eliminates the Python-shot-loop overhead entirely.

3. **MPSCircuit (§V.C):** Provides identical API to standard `Circuit` with automatic SVD
   truncation. Can be swapped in/out with minimal code change. The differentiable SVD means
   gradients flow through truncation — essential if we want to optimize bond dimensions or
   truncation cutoffs.

4. **scan for deep circuits (§VII.B):** Our syndrome round has O(rounds) depth; scan keeps
   compilation cost O(1) rather than O(rounds), making long-time simulations practical.

5. **quimb interoperability (§III.C):** Can convert existing quimb tensors into TC-NG format
   via `qop2quimb` / `quimb2qop`, enabling gradual migration.

6. **Qudit support (§IV.B):** Our JC model uses shared bosonic baths (effectively qudit-like
   truncated Fock spaces). TC-NG natively supports d≥3 systems with `QuditCircuit`.

7. **65 GB GPU memory constraint:** TC-NG's MPS mode has memory ∼ dnχ², linear in n for
   fixed χ and d. For our surface code d=3 (17 data qubits), with JC shared-mode bond
   dimension χ∼O(10-20), memory is negligible. Even d=5 (49 qubits) with χ∼50 is well
   under 65 GB.

## Limitations
- **MPS is fundamentally approximate (§V.C):** truncation error from SVD must be monitored.
  The trade-off is explicit: bond dimension ↔ accuracy ↔ memory. For our purpose (recovering
  qualitative mechanism structure), moderate bond dimensions should suffice.
- **quimb interoperability is not zero-cost:** the `qop2quimb` translation may not preserve
  all quimb-specific features (e.g., custom TN contraction optimizations). A full port may
  be simpler than interop.
- **Noise model (§IV.E) is Kraus-map based:** quantum trajectories use stochastic sampling
  of error channels. The MCWF method (continuous unraveling) is not directly provided —
  would need to implement the stochastic Schrödinger equation via the ODE solver (§IV.D).
- **Mixed-backend complexity (§III.A):** while cross-backend via DLPack is possible,
  the simplest path is committing to a single backend (JAX) for the whole pipeline.

## Tags
- `[paper]` TensorCircuit-NG = JAX-native differentiable quantum simulation with MPS backend
- `[paper]` JIT/VMAP pipeline: trace-once → XLA compile → operator fusion → vmap batch
- `[paper]` MPSCircuit: fully differentiable MPS with SVD truncation, same API as Circuit
- `[paper]` quimb <-> TC-NG bidirectional conversion via `qop2quimb`/`quimb2qop`
- `[paper]` scan for O(1) compilation cost in deep circuits
- `[paper]` qudit support (d>=3) relevant for JC bosonic mode truncation
- `[paper]` MIPT benchmark: 20q/40L, 1000 trajectories at 0.084s/traj on H200
- `[ours]` DIRECT REPLACEMENT for serial quimb hot-loop: trace-once eliminates per-operator overhead
- `[ours]` vmap over shots eliminates Python-shot-loop overhead
- `[ours]` qubit count within 65 GB cap: memory ∼ dnχ², linear in n
- `[ours]` Caveat: MCWF continuous unraveling not built-in; Kraus-map trajectories are native
