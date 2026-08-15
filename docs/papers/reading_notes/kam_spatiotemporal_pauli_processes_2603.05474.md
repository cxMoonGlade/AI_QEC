# Reading note: Kam, Southwell, Gicev, Usman & Modi, "Spatiotemporal Pauli processes: Quantum combs for modelling correlated noise in quantum error correction" (arXiv:2603.05474, 2026)

> **Provenance (2026-07-05): Read abstract + intro + methods.** PDF → txt
> `outputs/papers/2603.05474.txt` (54 pages, substantial). March 2026 preprint by Modi's group.
> Adjudication target: does this paper's "multi-time Pauli twirl on process tensor" framework
> already compute K or answer the r-dependent K-survival question? **Verdict: NO — it twirls
> AWAY the quantum coherence that K measures, but the framework COULD be used to compute
> pre-twirl K as a diagnostic of what the twirl destroys.**

## Metadata [paper]
- **Authors:** John F. Kam, Angus Southwell, Spiro Gicev, Muhammad Usman, Kavan Modi
  (Monash / A*STAR / CSIRO / U. Melbourne / SUTD)
- **Venue / status:** arXiv:2603.05474 [quant-ph], 5 Mar 2026. 54 pp preprint.
- **Type:** theory + numerics (process tensor + QEC + correlated noise)

## Executive summary [paper]
Introduces **Spatiotemporal Pauli Processes (SPPs)** — a framework bridging stochastic Pauli
noise models (standard in QEC) and microscopic non-Markovian device dynamics. Key steps:
1. Apply a **multi-time Pauli twirl** to a general process tensor → maps arbitrary multi-time
   non-Markovian dynamics to a multi-time Pauli process
2. The result is a **process-separable comb** = classical joint probability distribution over
   Pauli trajectories in spacetime
3. Efficient tensor network representation with bond dimension bounded by environment
   Liouville-space dimension
4. Demonstrated on surface code memory up to **distance 19** for:
   - Temporally correlated "storm" model
   - 2D quantum cellular automaton bath → nonlinear probabilistic CA under twirling

**Headline physical finding:** coherent bath interactions can drive the system into a
**pseudo-critical regime** with critical slowing down and macroscopic error avalanches that
cause complete breakdown of surface code distance scaling.

## Key formalism

The process tensor T_{k:0} for k-step process is Pauli-twirled:
T^{PT}_{k:0} = (⊗_{i} P_i) T_{k:0} (⊗_{i} P_i)
where P_i are random Pauli frame rotations at each step. The twirled process tensor is
diagonal in the Pauli basis → classical probability distribution p(σ_1,...,σ_k) over
spacetime Pauli error configurations.

## Relevance to project [ours]
**This is the most directly relevant 2026 paper, but it twirls AWAY exactly what K measures.**

The SPP framework:
- ✅ Bridges process tensors + QEC + correlated noise (the three pillars of our vacuum)
- ✅ Provides tensor network methods for process tensor simulation at QEC scale
- ❌ **Pauli-twirls the process tensor → removes the quantum coherence that K detects**
- ❌ Does NOT compute Kolmogorov violation on the pre-twirl process tensor
- ❌ The "classical probability distribution over Pauli trajectories" IS Kolmogorov-consistent
  by construction — so K=0 for the SPP, but that's an artifact of the twirl

The key opportunity: the SPP framework provides the computational machinery to estimate the
process tensor at QEC scale. If we compute K on the **pre-twirl** process tensor and compare
to K on the **post-twirl** SPP, the difference IS the quantum-nonclassical contribution that
Pauli twirling destroys. This is exactly the "K-survival" question for syndrome records.

Specifically for our r-dependent K:
- At r=1 (common-mode): pre-twirl PT is approximately diagonal in the joint-parity basis
  → Pauli twirl doesn't change much → K small both pre and post
- At r≠1: pre-twirl PT has off-diagonal temporal correlations → Pauli twirl destroys them
  → K large pre-twirl, K=0 post-twirl
- The r-dependent K IS the "twirl loss" = how much quantum structure the Pauli twirl destroys

## Limitations [paper]
- Pauli-twirled (post-twirl) only; pre-twirl classicality not computed
- 54 pages but no Kolmogorov consistency analysis
- Focus on surface code logical error rates, not on quantum non-classicality diagnostics

## Tags
- `[paper]` SPP = process tensor + Pauli twirl → classical distribution over Pauli trajectories
- `[paper]` surface code d=19 simulation with correlated non-Markovian noise
- `[paper]` pseudo-critical regime with breakdown of distance scaling
- `[ours]` pre-twirl vs post-twirl PT difference = K-signal we want to measure
- `[ours]` SPP provides the computational framework; K provides the diagnostic of what's lost
- `[gap]` SPP does NOT compute K or study r-dependent dephasing symmetry
