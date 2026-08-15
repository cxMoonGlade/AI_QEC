# Full-text note (精读, main text) — Heinsoo et al., "Rapid high-fidelity multiplexed readout of superconducting qubits" (arXiv:1801.07904)

> **Provenance (2026-06-25): 精读 of main text pp.1-3** (concept + architecture + crosstalk characterization);
> later pages (per-qubit fidelity tables, appendices) skimmed. PDF→txt `outputs/papers/1801.07904.txt` (13 pp).
> ETH Zurich (Wallraff group), 2018. The **readout-crosstalk** form for the teacher-completion (the
> incoherent/measurement crosstalk taxonomy item). Sibling crosstalk notes: `foxen_fsim..._2001.08343` (fSim
> coherent), `harper_nonclifford_crosstalk_surface_2605.29514` (⑤a ZZ), pending Sarovar/Gao.

## Why load-bearing [ours]
The canonical source for **readout (measurement) crosstalk** + its OBSERVABLE on superconducting qubits, and
— critically — it confirms readout crosstalk is **incoherent (a classical correlation + measurement-induced
dephasing)**, i.e. the certifiable-on-binary-syndrome form (contrast the coherent fSim/drive forms that are
syndrome-TWIRLED → d3-gated). Frequency-multiplexed readout = exactly the surface-code ancilla-readout setting.

## The mechanism + numbers [paper]
- 5 qubits, single 1.2 GHz feedline, 80 ns readout pulse, resonators populated < 250 ns, **avg correct
  assignment 97%**.
- **Readout-crosstalk magnitude:** the difference between individual readout errors and errors measured when
  reading all qubits SIMULTANEOUSLY is **within 1%**.
- **Two crosstalk channels (the mechanism):** driving resonator i off-resonantly populates untargeted
  resonator j (frequency spacing ΔR/2π ≈ 160 MHz) → (a) **measurement-induced DEPHASING of untargeted
  qubits**, and (b) **classical correlations in the readout assignment between pairs**. They characterize it
  by "analyzing correlations in the readout between all pairs of qubits and by measuring the additional
  dephasing imposed on untargeted qubits."
- **Mitigation:** dedicated per-resonator **Purcell filters** suppress off-resonant driving — intra-resonator
  photon number scales **∝Δ⁻⁴ (with filter) vs ∝Δ⁻² (without)**. κR/2π ≈ 10 MHz, J/2π=10, κP/2π=40.

## Limitations / what does NOT apply [paper→ours]
- A readout-ARCHITECTURE paper (the value is the crosstalk characterization + the magnitude, not a QEC
  result). Exact pairwise-correlation numbers are in the per-pair tables (skimmed); the load-bearing facts
  are the <1% magnitude + the two-channel mechanism + the Purcell ∝Δ⁻⁴ suppression.
- Device-specific (ETH); for a Google-Sycamore teacher the magnitude is BRACKETED (Purcell-protected ≪1%
  vs un-protected larger) — sweep, don't freeze.

## Relevance to the teacher (crosstalk form: readout) [ours]
- **Teacher recipe (two parts):** (a) **correlated ancilla-readout assignment** — the leaked/soft-readout
  POVM `b`-classifier on ancilla i acquires a dependence on neighbour j's measured state (a classical 2×2
  correlated assignment error); (b) **measurement-induced dephasing** on data/spectator qubits during ancilla
  readout. Magnitude bracketed ≲1% (Purcell-on) — SWEEP.
- **THIS IS THE CERTIFIABLE-NEW form.** Readout crosstalk is **incoherent / classical** → it appears
  DIRECTLY in the syndrome record as a **pairwise ancilla-readout correlation** (a moment observable) and is
  **NOT syndrome-twirled** — unlike the coherent fSim (`foxen...`) / drive forms, which are d3-gated. So it
  ADDS a certifiable misspecification axis at d3 (a neighbour-ancilla readout-correlation moment, distinct
  from the ⑤a error-spatial_corr and the ③ rr_corr), that an iid-readout learner misses.
- **Observable:** pairwise neighbour-ancilla readout correlation (decode-independent moment) + the
  spectator-dephasing contribution to data-qubit error. Anchor for the certify moment-check.
- **Epistemic class:** (b) prediction band — magnitude bracketed (Purcell-on ≲1%), the correlation observable
  is certifiable (incoherent); a registered bet that it is moment-detectable on the d3 sub-codes.

## Trust [ours]
Main-text 精读 (concept §I-II, the <1% simultaneous-vs-individual magnitude, the two crosstalk channels =
correlations + dephasing, the Purcell ∝Δ⁻⁴ suppression). Per-pair correlation tables skimmed (device-specific;
the teacher brackets the magnitude). The "certifiable-because-incoherent" verdict is [ours], grounded in the
classical/measurement nature of the mechanism + `project-axisA-teacher-ws1-ws2` (coherent→twirled→d3-gated).
