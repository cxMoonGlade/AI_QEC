# Full-text note (focused 精读) — Google Quantum AI, "Quantum error correction below the surface code threshold" (Willow, arXiv:2408.13687)

> **Provenance (2026-06-25): FOCUSED 精读.** PDF → txt `outputs/papers/2408.13687.txt` (PyMuPDF, 27 pp).
> Close-read of the **leakage / DQLR / simulation-error-model SI** (the load-bearing part for path-B);
> the main superconducting-QEC results (Λ, the d=7 below-threshold demo) skimmed. Google Nature 2025
> (Willow processor). For the path-B leakage-transport theory-first (the deployed-regime + |3>-transport).

## Why load-bearing [ours]
The newest Google source confirming (a) the |3>-mediated leakage TRANSPORT, (b) the DQLR deployed regime +
its exact removal fidelities, and (c) how Google SCALES the leakage sim (GPTA → Clifford). Plus it names a
SECOND crosstalk (stray ZZ) distinct from leakage-transport.

## The simulation error model (SI, "Surface Code Performance at Large Code Distances") [paper]
Google's large-d surface-code sim dresses the circuit with: decoherence (T1, Tφ, **passive heating to |2>**);
readout+reset error; **dephasing-induced leakage of the higher-freq qubit during CZ, modeled as |11>→|02>**;
**stray-coupling crosstalk between nearest- and diagonal-neighbour qubits during PARALLEL CZ**; excess gate/
idle error; and **"Transport of leakage between CZ-gate qubits through higher-excitation transitions (e.g.
|12> → |30>)"**. ⇒ |3>-transport is explicitly in Google's faithful model (confirms path-B Arm 2).

## DQLR model + removal fidelities (the deployed regime) [paper]
DQLR modeled as a reset channel `K_ij = √(P_{j→i}) |i><j|`, `K0 = √(I − Σ K†K)`, **acting trivially on the
computational subspace**. Removal fidelities: **|2> at 100%, |3> at 50%** → `P_{2→1}=1, P_{3→2}=0.5,
P_{3→1}=0.5`. They also run WITHOUT DQLR to show its importance (leakage kills the exponential suppression).
Λ ≈ 2.0–2.2 at large d WITH DQLR (Λ3/5=2.16 … Λ11/13=2.01).

## How Google SCALES the leakage sim — GPTA [paper → ours]
After dressing with all channels, they apply a **Generalized Pauli Twirling Approximation (GPTA)** to each
noise channel → a generalized-Pauli channel **that also includes leakage** → Clifford-compatible → fed to the
**Pauli+ simulator**. **[ours] This is the KEY contrast with our path-B:** Google Pauli-TWIRLS the leakage
channel to scale (Clifford). **Our carrier keeps the FULL (un-twirled) channel on the DM/MPS** — a
fidelity edge (no twirl) at the cost of scale, exactly the DM-for-anchor / carrier-for-scale split. So our
|3>-faithful Arm 2 is strictly MORE faithful than Google's own GPTA sim at d3 (no Pauli-twirl of the leakage).

## Relevance to path-B [ours]
- Confirms the path-B Arm-2 mechanism (|12>→|30> transport) on Google's newest device + the DQLR-deployed
  regime (the bound regime where the |2>-only gap is small).
- Names **stray-ZZ crosstalk** (parallel-CZ, NN+diagonal-NN) as a SEPARATE form — relevant to the broader
  crosstalk taxonomy (form 1 ZZ is more than static; there's parallel-CZ stray ZZ too — fold into the ZZ
  BOUND when that prereg is finalized).
- The GPTA-vs-full-channel contrast is a publishable faithfulness point: our DM/MPS keeps the un-twirled
  leakage channel that Google twirls away to scale.

## Limitations / what does NOT apply [paper]
- It's a removal+scaling paper (GPTA + Pauli+ sim), NOT a channel-derivation paper — the transport Kraus form
  is inherited from Miao [29] / the 2023 "Suppressing errors" ref, not re-derived here. So for the channel
  FORM we still anchor on Miao SI S1 (g_eff) + QuTiP; Willow gives the deployed-regime + removal-fidelity
  context, not the microscopic coupling.
- d>5 are simulation (the hardware demo is d≤7 main; the large-d LERs are the GPTA sim).

## Trust [ours]
Focused full-text 精读 of the leakage SI; main-text QEC results skimmed. The DQLR fidelities (|2>100%/|3>50%)
+ the GPTA-for-scale + the |12>→|30> transport are the load-bearing, directly-quoted facts.
