# Reading note: Botzung & Fiorelli, "Error recovery protocols within metastable Decoherence-Free Subspaces" (arXiv:2506.19631, 2025)

> **Provenance (2026-07-05): Read abstract + intro + key results.** PDF → txt
> `outputs/papers/2506.19631.txt` (13 pages). June 2025 preprint.
> Adjudication target: does this provide a modern perspective on DFS for collective
> dissipation that validates the {|01⟩,|10⟩} DFS picture? **Verdict: YES — directly
> identifies {|01⟩,|10⟩} as the metastable DFS for two qubits under collective dissipation,
> and characterizes which errors are recoverable vs not.**

## Metadata [paper]
- **Authors:** Thomas Botzung (CESQ/ISIS, CNRS & U. Strasbourg), Eliana Fiorelli (IFISC, Spain)
- **Venue / status:** arXiv:2506.19631v1 [quant-ph], 24 Jun 2025. Preprint.
- **Type:** theory (Liouvillian spectral analysis of metastable DFS for passive QEC)

## Executive summary [paper]
Uses **quantum metastability** theory to characterize DFS as code spaces for **passive**
quantum error correction. The key idea: open quantum systems can have DFS that remain
approximately invariant for long transient times (the "metastable window") before relaxing
to a unique steady state. Two models studied:
1. **Two-qubit system under collective dissipation** — DFS = {|01⟩, |10⟩}
2. **Nonlinear driven-dissipative Kerr resonator** — cat-state encoding

## Key findings for two-qubit model [paper]

### The metastable DFS
Under collective dissipation (both qubits coupled to the same bath), the subspace
{|01⟩, |10⟩} is identified as the **metastable DFS**. It is protected against collective
dissipation but NOT against:
- **Dephasing (phase-flip) errors** → NOT recoverable in the qubit model
- **Bit-flip errors** → recoverable up to a certain measure
- **Spontaneous emission** → recoverable up to a certain measure

### Error recovery protocol
1. Initialize in |ψ⟩ ∈ DFS
2. Error channel acts for short time (≪ metastable window)
3. Unperturbed Liouvillian dynamics autonomously restore the state

The spectral properties of the Liouvillian (gap structure) determine which errors
are correctable.

## Relevance to project [ours]
**Validates the {|01⟩,|10⟩} DFS picture for collective dissipation and highlights the
dephasing vulnerability.**

Key insight for K-survival:
- The DFS {|01⟩,|10⟩} is protected against **collective dissipation** (energy relaxation)
  but NOT against **dephasing** — dephasing errors are explicitly NOT recoverable
- This means the DFS protection is noise-type-dependent: collective dissipation → DFS,
  collective dephasing → DFS, but **differential dephasing → no protection**
- Our quantum bath has σz coupling (pure dephasing). At r=1, the coupling is collective
  → DFS. At r≠1, the coupling has a differential component → DFS is broken.
- The "metastable" nature means even at r=1, the protection is imperfect (finite
  lifetime) due to the eventual relaxation to steady state

The paper's two-qubit model directly parallels our setup, with the crucial difference
that our "error" is the quantum bath's continuous dephasing, and our "measurement"
is the joint-parity extraction that probes the DFS coherence.

## Limitations [paper]
- Collective DISSIPATION model (not pure dephasing); the dephasing vulnerability is
  noted but not the main focus
- Markovian Lindblad; no non-Markovian bath memory
- Short-time error-recovery protocol; not multi-round syndrome extraction

## Tags
- `[paper]` {|01⟩,|10⟩} = metastable DFS for two qubits under collective dissipation
- `[paper]` dephasing errors NOT recoverable in qubit DFS model
- `[paper]` Liouvillian gap structure determines error correctability
- `[ours]` validates DFS picture; dephasing vulnerability = why r≠1 breaks protection
- `[ours]` "metastable" = even r=1 protection is imperfect (finite lifetime)
