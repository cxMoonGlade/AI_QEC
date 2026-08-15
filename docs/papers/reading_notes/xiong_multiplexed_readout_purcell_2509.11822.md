# Full-text note (精读, abstract + intro + key results) — Xiong et al., "High-performance multiplexed readout of superconducting qubits with a tunable broadband Purcell filter" (arXiv:2509.11822, 2025) + Fechant et al., "Offset Charge Dependence of Measurement-Induced Transitions in Transmons" (arXiv:2505.00674, 2026)

> **Provenance (2026-06-26): 精读 of Xiong 2509.11822 §abstract+intro+key-numbers** (the modern multiplexed-
> readout-crosstalk SOTA) + **Fechant 2505.00674 §abstract+intro** (the MIST / measurement-induced-transitions
> NEW effect). PDF→txt `outputs/papers/{2509.11822,2505.00674}.txt`. SUSTech/IQA Shenzhen (Zhong/Chu) Sep 2025;
> KIT/Sherbrooke (Pop/Blais) Jan 2026. The **FRONTIER (2025-26) READOUT-crosstalk magnitude + form + the new
> measurement-induced-leakage axis** — from the 2026-06-26 crosstalk frontier-literature sweep (the user's
> "why are the crosstalk papers all 5+ years old?" correction). UPDATES the readout grounding
> `heinsoo_multiplexed_readout_crosstalk_1801.07904` (2018).

## Why load-bearing [ours]
The current (2025) multiplexed-readout-crosstalk SOTA on a tunable-Purcell-filter device — the modern standard
that supersedes Heinsoo 2018. Confirms the readout-crosstalk FORM (dispersive Γφ ~ χ²n̄/κ + classical assignment
correlation) but gives the modern magnitude (crosstalk now ~0.02%, not <1%), AND surfaces the NEW readout
sub-mechanism (measurement-induced leakage/MIST) the 2018 picture misses.

## The model + numbers [paper, Xiong 2509.11822]
- **Modern multiplexed-readout crosstalk = MINIMAL.** Simultaneous 3-qubit readout (100 ns): **avg fidelity
  99.5% with "low/minimal crosstalk"; cross-fidelity ≈ 0.02%** (off-diagonal of the simultaneous assignment
  matrix). vs Heinsoo 2018's "<1% simultaneous-vs-individual" ⇒ **~50× lower**.
- **Photon-noise-induced dephasing** (the measurement-induced-dephasing mechanism) caused by **residual photons
  n̄ from thermal noise or PARASITIC MEASUREMENTS** (= the readout-crosstalk dephasing channel). Suppressed **7×
  in idle** by detuning the tunable filter so `κr ≪ χ` (idle T_φ ~ 200 µs); read-on `κr ≈ 2χ` (~2–20 MHz). The
  classic `Γφ ∝ χ²n̄/κ` dependence is preserved (no revision). Residual `n̄ ≈ 5×10⁻⁴`.
- **99.6% fidelity (100 ns); 99.9% (50 ns multilevel via an X₁₂ pre-excitation to |2⟩); QND 99.4%.**
- **Assignment-matrix structure:** above-diagonal = relaxation (|1⟩→|0⟩); below-diagonal = measurement-induced
  EXCITATIONS (|0⟩→|1⟩) — i.e. the readout itself injects state transitions.

## The NEW effect [paper, Fechant 2505.00674] — measurement-induced transitions (MIST) / ionization
- **Readout-induced LEAKAGE / qubit ionization:** increasing the resonator photon number to boost SNR causes
  **unwanted qubit transitions to high-energy levels** ("MIST" / ionization) at SPECIFIC critical photon
  numbers (multiphoton qubit-resonator resonances). This NEGATES the benefit of strong readout drives and
  bottlenecks QEC.
- **Gate-charge (offset-charge) dependent:** because MIST involves HIGH-energy transmon states, the critical n̄
  is **offset-charge dependent** — and this dependence PERSISTS deep in the transmon regime where the 0-1
  frequency is charge-insensitive (experimentally confirmed; quantitative agreement needs higher-order
  harmonics in the transmon H). Xiong measures the readout **leakage rate ℒ↑ = 0.08% (seepage ℒ↓ = 1.70%)** at
  100 ns — a concrete MIST magnitude.

## Limitations / what does NOT apply [paper→ours]
- Both are device-physics / readout-architecture papers (not QEC results). The magnitudes are device-specific
  (Purcell-filter-protected ⇒ ≪ Heinsoo); for the teacher BRACKET, not freeze.
- Xiong's measurement-induced-dephasing on spectators during selective readout is "protected" (κ-2χ mismatch),
  so the spectator-dephasing crosstalk is near-negligible on modern protected hardware — the residual `n̄≈5e-4`
  is the floor.

## Relevance to the teacher (READOUT crosstalk) [ours] — the MAGNITUDE UPDATE + a NEW sub-axis
- **FORM: VALID — keep it.** Dispersive measurement-induced dephasing `Γφ ~ χ²n̄/κ` (the QuTiP
  `build_readout_dephasing_channel` exact-transient oracle) + the classical 2×2 correlated assignment (Sarovar
  Ex.4 / Heinsoo) are still the correct model (Xiong preserves them). No form change.
- **MAGNITUDE: STALE — update the bracket.** My readout `deph_rate` / assignment `pm` bracket was **≲1%**
  (Heinsoo 2018). Modern protected hardware: **cross-fidelity ≈ 0.02% (2e-4)**, residual `n̄ ≈ 5e-4` ⇒ the
  readout-crosstalk magnitude is **~50× SMALLER**. UPDATE: `pm` / spectator-dephasing bracket → **~2e-4 to 1e-3**
  (modern protected → a mediocre/unprotected upper edge), with the old ≲1% retired to a flagged "unprotected /
  pre-Purcell-filter" arm. (Note: the readout EXCESS observable was already sub-MC-floor on d3 — this only makes
  it smaller; the certifiable lever is unchanged.)
- **NEW sub-axis to ADD — readout-induced LEAKAGE (MIST):** a NEW readout-crosstalk mechanism absent from the
  2018 picture — the readout drive EXCITES the qubit to |2⟩+ (leakage) at a critical n̄, offset-charge dependent.
  Grounded magnitude: **ℒ↑ ≈ 0.08% per 100 ns readout** (Xiong) + the offset-charge-dependent critical-n̄ (Fechant).
  This **connects READOUT to the ④ leakage axis** — model it as a small readout-conditioned |1⟩→|2⟩ leakage
  channel (reuse the QuTiP WG-leak / a readout-power-conditioned leak), bracketed ~1e-3, SWEPT. A faithful
  teacher of modern readout should carry this (the readout no longer just dephases + mis-assigns — it leaks).
- **Epistemic class:** (b) prediction bands — the readout-dephasing/assignment magnitude `pm ∈ [2e-4, 1e-3]`
  (modern protected, SWEPT) + the readout-induced-leakage `ℒ↑ ~ 1e-3` (grounded Xiong 0.08%, MIST-mechanism
  Fechant). The Γφ form + the MIST mechanism = (a)/grounded.

## Trust [ours]
精读 of Xiong's abstract + intro + the headline numbers (99.5% simultaneous, 0.02% crosstalk, 7× dephasing
suppression, n̄≈5e-4, ℒ↑=0.08%, the κr≪χ idle / ≈2χ read-on filter mechanism) read directly; and Fechant's
abstract+intro (MIST = multiphoton ionization to high levels, offset-charge dependent, persists deep in the
transmon regime). The "~50× lower than Heinsoo" + "pm bracket → 2e-4..1e-3" + "add a readout-induced-leakage
sub-axis ~1e-3" verdicts are [ours], grounded in the read magnitudes + the MIST mechanism. Per-pair correlation
tables / the full filter-design / the MIST higher-harmonic theory skimmed.
