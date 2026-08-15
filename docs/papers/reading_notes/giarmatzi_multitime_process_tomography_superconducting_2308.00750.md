# 精读 — Giarmatzi, Jones, Gilchrist, Pakkiam, Fedorov, Costa, "Multi-time quantum process tomography on a superconducting qubit" (arXiv:2308.00750)

> **Provenance (2026-07-03): FULL-TEXT 精读 of the core** (abstract, §1 intro, §2 multi-time-tomography
> formalism, §3 opening = the measure-and-prepare protocol). PDF → txt `outputs/papers/2308.00750.txt`
> (PyMuPDF, 13 pages, arXiv v3 12 Dec 2025; **Quantum, accepted 2025-12-02, CC-BY**). Detailed device/results
> (§3–5) in the txt. Secondary/support paper. Tags **[paper]**/**[ours]**.

## Metadata [paper]
- Giarmatzi, Jones (co-first) et al. (UTS / EQuS / UQ / Nordita). Quantum (2025). Experiment + method.
- Public code + data.

## Executive summary [paper]
Implements the **FIRST full tomography of a multi-time quantum process on a superconducting qubit** — a
complete (not restricted) description of its non-Markovian noise — using **sequential measure-and-prepare
operations** + a **novel post-processing that requires NO fast feed-forward**. Detects general multi-time
correlated noise AND **quantum** non-Markovian noise (part of the noise is from quantum sources, e.g.
physically nearby qubits on the chip), distinguishing quantum vs classical NM. Devices: UQ in-house transmon
+ IBM `ibm_perth` cloud.

## Method (deep) [paper]
- **Process matrix `W^{ABC}`** (= quantum comb / process tensor / strategy) on the joint input/output spaces
  of all times, `W ≥ 0`; instruments `M^A_{a|x}` (Choi, outcome `a`, setting `x`); generalized Born rule
  (Eq. 1): `p(a,b,c|x,y,z) = Tr[W^{ABC}(M^A_{a|x} ⊗ M^B_{b|y} ⊗ M^C_{c|z})]`. Reconstruct `W` by inverting
  Eq. 1 (state-tomography-like).
- **The key instrument = measure-and-prepare (a "causal break"):** `M^A_{a|x} = Π^{AI}_{a|x} ⊗ ρ_x^{AO T}` —
  a projective measurement immediately followed by preparing a chosen state `ρ_x`. This is the IC instrument
  that gives FULL (not restricted) reconstruction. Naively needs fast outcome-conditioned feed-forward
  (unavailable on most devices) — the historical bottleneck that forced prior work to "restricted" process
  matrices (unitaries + final measurement, or measurement without independent re-prep). **This work removes
  the feed-forward requirement via mid-circuit measurement + post-processing.**
- Classical vs quantum NM = distinguished by whether a classical or quantum channel is needed to simulate
  the memory (a quantum environment correlating the SE interactions in time is the quantum case).

## Findings [paper]
- Full multi-time process reconstructed on real superconducting hardware; general AND quantum NM detected in
  all cases, matched to a theoretical model. Quantum NM attributed partly to nearby on-chip qubits.

## Relevance to the reconstruction [ours]
- **The realizability proof for the active pivot.** White [[white_pollock_process_tensor_tomography_2106.11722]]
  said memory is only *inferable* (not directly measurable) WITHOUT measurement causal breaks. This paper
  IMPLEMENTS exactly those causal breaks (measure-and-prepare) on a superconducting qubit — WITHOUT exotic
  feed-forward hardware — and thereby FULLY reconstructs the multi-time process AND detects the QUANTUM
  (coherent-memory) part. So the reconstruction's active-observation characterization of the coherent
  non-Markovian noise is demonstrably realizable on the target platform, not just formal.
- **Mid-circuit measure-and-prepare = the concrete active-`W`/causal-break probe** the `qec_twin` `C_cal(r)`
  ladder must include (beyond unitary/twirl probes) to move from a restricted to a full characterization —
  a design input for the Phase-1 prereg + Phase-2 probe wiring.
- Quantum-vs-classical NM discrimination is exactly the reconstruction's "coherence = contribution vs
  stochastic = baseline" split, done experimentally.

## Related notes
[[white_pollock_process_tensor_tomography_2106.11722]], [[white_unifying_nonmarkovian_selfconsistent_2312.08454]],
[[ziyad_emergent_nonmarkovianity_logical_2512.08893]], [[keeling_process_tensor_2509.07661]].
