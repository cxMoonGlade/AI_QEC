# Full-text note (精读, main text) — Foxen et al., "Demonstrating a Continuous Set of Two-qubit Gates for Near-term Quantum Algorithms" (arXiv:2001.08343)

> **Provenance (2026-06-25): 精读 of main text pp.1-6** (model + benchmarking + conclusions); SI pp.7-20
> (the 5-parameter control model + numerics) skimmed. PDF→txt `outputs/papers/2001.08343.txt` (20 pp).
> Published **Phys. Rev. Lett. 125, 120504 (2020)**, **DOI 10.1103/PhysRevLett.125.120504** (verified
> against the arXiv abstract page 2026-06-30).
> Google AI Quantum, 2020. The **coherent two-qubit-gate-error (fSim) crosstalk form** for the
> teacher-completion (the "coherent XX/YY/ZX beyond ZZ" taxonomy item). Sibling crosstalk notes:
> `harper_nonclifford_crosstalk_surface_2605.29514` (⑤a ZZ), pending Sarovar/Heinsoo/Gao.

## Why load-bearing [ours]
The canonical source for the **fSim two-qubit gate model** (`fSim(θ,φ)`: θ=|01⟩↔|10⟩ swap = σXσX+σYσY,
φ=|11⟩ phase = σZσZ) and — critically — the finding that the CZ's coherent error (residual swap δθ +
phase δφ) is **calibrated to a purity-limited residual** on Sycamore-class gmon transmons. Sets the teacher's
"coherent gate-error crosstalk" form AND its bounded magnitude.

## The model [paper]
- `fSim(θ,φ)` matrix in {|00⟩,|01⟩,|10⟩,|11⟩}: diag/swap block `[[cosθ, −i sinθ],[−i sinθ, cosθ]]` on
  {|01⟩,|10⟩}, `e^{−iφ}` on |11⟩, 1 on |00⟩ (Eq.1). The CZ used by the surface code = `fSim(0, π)`.
- Full low-leakage two-qubit unitary = **5 parameters**: θ, φ + 3 single-qubit phases (SI VII).
- Coupled-transmon physics: η (nonlinearity) = **240 MHz fixed**, detuning Δ, tunable coupling g
  (gmon, |g|/2π up to ~45 MHz). CZ via diabatic |11⟩→|02⟩→|11⟩ swap (CPHASE family); θ via on-resonance g.
- T1 = **25.3 ± 7.3 µs**; control = synchronous rectangular flux pulses, 13–15 ns.

## Key numbers [paper]
- **Purity-limited avg two-qubit Pauli error = 3.83e-3 per fSim gate; purity = 3.76e-3** ⇒ the **coherent
  (control) residual ≈ error − purity ≈ 7e-5 — calibrated to NEGLIGIBLE.** The gate is decoherence-limited,
  not coherent-error-limited, after calibration.
- CPHASE family avg Pauli error 1.9e-3 (accumulates a small parasitic swap **θ ≤ 5°** for a 13 ns gate, a
  calibration byproduct, reducible by lengthening the gate); iSWAP-like 1.2e-3 (accumulates φ ∝ θ²).
- **Leakage to |02⟩ is the dominant error WITHIN the fSim model** (the |11⟩↔|02⟩ resonance near Δ≈η).
- TLS defects appear as a band of higher error near φ≈240° (a weakly-interacting TLS in one qubit's
  spectrum) — the device avoids them by shifting both qubit frequencies at fixed Δ.

## Limitations / what does NOT apply [paper→ours]
- ISOLATED-pair XEB. The coherent error being calibrated-negligible is for the **isolated** gate; it does
  NOT cover **parallel-operation stray coupling** (the stray-ZZ during PARALLEL CZ that Willow 2408.13687
  names) — that is a separate SPATIAL crosstalk form (fold into the ⑤a ZZ axis, not here).
- Purity/XEB twirls to a Pauli error — the residual coherent structure (δθ, δφ) is not separately reported
  per gate beyond "purity-limited"; for a faithful teacher the coherent residual is BOUNDED (≲1e-4-scale),
  not zero.

## Relevance to the teacher (crosstalk form: coherent fSim error) [ours]
- **Teacher recipe:** apply the CZ as `fSim(δθ, π+δφ)` — a small coherent over-rotation (residual swap δθ +
  phase miscalibration δφ). Grounded magnitude: **bounded-NEGLIGIBLE** (purity-limited, coherent residual
  ~7e-5; δθ ≲ 5° only as an uncalibrated byproduct).
- **Two parts of the fSim error split cleanly:** (1) leakage |11⟩→|02⟩ = the dominant error = **already
  path-B** (leakage-transport); (2) the coherent residual (δθ, δφ) = this form = small + **coherent ⇒
  syndrome-TWIRLED ⇒ d3-GATED** (same class as ②/⑤a-coherent — `project-axisA-teacher-ws1-ws2`
  coherence-not-identifiable-from-binary). So at d3 this form's certifiable payoff is gated; its honest
  observable is the coherent excess-LER/twirl-underestimate (Bravyi 1710.02270), d-gated at distance-2.
- **Epistemic class for the prereg:** (c)/bounded-simplification — declare the fSim coherent crosstalk as
  **bounded-negligible after calibration** (purity-limited) + d3-gated; do NOT inflate it. The TLS-band
  finding connects to the Gao TLS form; the parallel-CZ stray-ZZ connects to ⑤a.

## Trust [ours]
Main-text 精读 (model Eq.1, benchmarking Figs 3-4, the purity-limited 3.83e-3 / purity 3.76e-3, θ≤5°,
leakage-dominant). The "coherent residual ≈ 7e-5" is my arithmetic from error−purity (declared inference,
not a paper-stated number). SI control-model detail skimmed.
