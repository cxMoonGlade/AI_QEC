# Full-text note (精读, main text) — Gao, Zhang, Xu et al., "Non-Local and Non-Markovian Effects of a Microscopic Two-Level Defect in Superconducting Quantum Circuits" (arXiv:2605.23385v2, 2026)

> **Provenance (2026-06-25): 精读 of the full main text pp.1-8** (the shared-coupler TLS identification +
> tunable coupling + non-Markovian dynamics + noise spectroscopy + multipartite/correlated dynamics + gate-error
> simulations); references + SI (Sections VI-XIV) skimmed. PDF→txt `outputs/papers/2605.23385.txt` (10 pp).
> Beijing Academy of Quantum Information Sciences (Yan/Yu groups), on a 72-qubit tunable-coupler processor.
> The **TLS / spectator-defect crosstalk** form for the teacher-completion. Sibling crosstalk notes:
> `sarovar..._1908.09855` (drive + taxonomy + observable), `foxen..._2001.08343` (fSim coherent),
> `heinsoo..._1801.07904` (readout). Connects to `kam_nonmarkovian_surface_code_2410.23779` (⑤b temporal) +
> `bhardwaj_drifting_noise_estimation_2511.09491` (⑤b drift) + `kubo_dtc_residual_zz_2402.05361`.

## Why load-bearing [ours]
The canonical recent source for **TLS-as-a-crosstalk-mechanism** with the QEC-relevant twist: a single coherent
defect hosted in a **tunable coupler** couples SIMULTANEOUSLY to two spatially distant qubits (>1 mm apart),
and its dephasing is **non-Markovian (1/f)**. So one microscopic defect produces BOTH (a) **non-local spatial
correlation** between qubits that share it, and (b) **temporal correlation / drift / non-Markovianity**. This
is the microscopic PHYSICAL ORIGIN of our ⑤b temporal-correlation + drift axis (and a rare contributor to ⑤a
spatial). Confirms the prereg prediction: TLS/spectator → drift-like → reuses ⑤b machinery.

## The system + model [paper]
- Two tunable transmons Q1, Q2 coupled via a tunable transmon coupler C1 that **hosts** the TLS (in a Josephson-
  junction tunnel barrier). Direct couplings g1 (qubit-coupler), g2, gT (TLS-coupler). The TLS-qubit coupling
  is **mediated** by the coupler.
- **Effective TLS-qubit coupling (Eq.1, dispersive Δ≫g):** `g̃_k ≈ g_k·g_T / Δ`, where `Δ = ωC − ωT ≈ ωC − ωk`.
  ⇒ **tunable** via the coupler frequency (small Δ → large g̃, "several MHz" while still dispersive). This is
  the "previously overlooked" mechanism: a defect in a coupling element non-locally affects separated qubits,
  with a coupling that **changes during operation** (couplers tune near qubit freq during 2-qubit gates → g̃
  enhanced exactly when gates run).
- Long-time relaxation: `Γ_avg = Γ^Q_1 cos²θ + Γ^TLS_1 sin²θ`, `θ = arctan(2g̃1/δ)`, `δ = ω1 − ωT`.
- **Multipartite dynamics (the QEC-critical part):** TLS mediates excitation exchange between two IDLING qubits.
  At resonance δ=0, `|11⟩⊗|0⟩_T → (1/√2)(|01⟩+|10⟩)⊗|1⟩_T → |11⟩⊗|0⟩_T`; at `t = 1/(4√2 g̃)` the two qubits
  hit a **maximally entangled Bell state** while the TLS stays excited. "unwanted TLS excitations may accumulate
  and degrade subsequent operations, leading to **temporally correlated errors**."

## Key numbers [paper]
- TLS frequency `ωT/2π ≈ 3.48 GHz`. Direct couplings `g1/2π = 70 MHz`, `g2/2π = 61 MHz`, `gT = 30 MHz`.
  Tunable effective `g̃1,2/2π` up to ~10 MHz (measured 1.4–10.4 MHz across Δ = 0.3–2 GHz).
- TLS coherence: `T1 = 44.7 ± 1.3 µs`; `T2R ≈ 0.4 µs` (Ramsey) → `T2E ≈ 16 µs` (echo) → longer under CPMG
  (coherence revival with refocusing-pulse count N) ⇒ **dominant low-frequency (1/f) dephasing, DD-suppressible**.
  `T^TLS_φ ≈ 1.1 µs` (used in gate sims).
- **Noise spectrum:** `S(ω) ∝ 1/f^{1.05}` reconstructed over **ten decades (0.1 mHz – 1 MHz)**, with discrete
  Lorentzian bumps (TLF0, TLF1) → **Dutta-Horn** ensemble; 10 TLFs, switching rates 0.6 mHz – 0.2 GHz reproduce
  it (the count/range is phenomenological-illustrative, NOT a physical inventory). Integrated → predicted Ramsey
  T2 = 0.36 µs (matches). **Random TLS frequency jumps** observed (infrequent) → intrinsic defect = a drift/RTN
  source.
- Gate errors (iSWAP sim, tgate=60 ns): TLS coupled to BOTH qubits > local one-qubit coupling; for g̃=10 MHz,
  sub-1% gate error needs **300–500 MHz detuning** from ωT. Zeno/anti-Zeno: max gate error at `Γ^TLS_1 ≈ δ`;
  `Γ^TLS_1 ≫ g̃` → TLS relaxes too fast to be excited → effectively "invisible" (quantum Zeno).
- **Note added:** a TLS in a transmon tunnel barrier can also couple to the readout resonator and degrade
  readout (ref [59]) — connects to the Heinsoo readout-crosstalk form.

## Limitations / what does NOT apply [paper→ours]
- A **device-physics characterization** of ONE coupler-hosted defect on a specific chip; not a QEC or surface-
  code result. The numbers are device-specific → BRACKET (TLS density, g̃, switching-rate distribution vary by
  chip/fab; frequency-planning + DD already mitigate the strong/resonant cases).
- The dynamics are fundamentally **coherent** (vacuum Rabi exchange, Bell-state generation) at the MHz scale of
  idle/gate windows; the **dephasing/drift envelope** is the incoherent 1/f part. The two split (see verdict).
- Shared-defect (two-qubit) TLS is the *highlighted* case but stated to be relatively rare; the common case is
  a local single-qubit TLS (the standard fluctuating-T1 picture, Klimov [16]) → the dominant teacher-relevant
  footprint is the **drift/temporal-correlation envelope**, not the non-local Bell generation.

## Relevance to the teacher (crosstalk form: TLS / spectator-defect) [ours]
- **Teacher recipe (reuse ⑤b, NOT a new operator):** model the TLS footprint as the QEC-observable envelope it
  produces, in two reusable pieces:
  1. **Temporal correlation + drift (the dominant, certifiable piece)** — a slowly-fluctuating / 1/f / RTN
     modulation of the affected qubit's error rate (T1 jumps + low-freq dephasing) ⇒ the **⑤b** axis:
     Kam-temporal correlation (`kam_nonmarkovian_surface_code_2410.23779`, effective syndrome-bit-flip
     correlation) + Bhardwaj drift `g(r) = g0 + Σ gm sin(ωr)` (`bhardwaj_drifting_noise_estimation_2511.09491`).
     Grounded magnitude: 1/f^1.05, switching rates 0.6 mHz–0.2 GHz, occasional discrete jumps — BRACKET.
  2. **Non-local spatial correlation (rare)** — a shared coupler-defect couples two distant qubits ⇒ a rare
     **⑤a**-style correlated-error/entangling event (`mechanisms/teachers.py:zz_coupling_kraus` /
     `correlated_dephasing_kraus`); the coherent exchange = an effective two-qubit correlated kick. Rare,
     bracketed.
- **Coherent-vs-incoherent / certifiability verdict (fits the EMERGING PATTERN):** the **coherent** TLS exchange
  (vacuum Rabi / Bell generation) → on binary syndromes it is **syndrome-TWIRLED → d3-gated** (same class as
  ②/⑤a-coherent/fSim/drive — `[[project-axisA-teacher-ws1-ws2]]` coherence-not-identifiable-from-binary). The
  **incoherent envelope** (1/f dephasing drift + temporal correlation + occasional jumps) is the **certifiable**
  piece — it shows in the standard syndrome record as a **temporal autocorrelation / drift moment** an
  iid-stationary-Pauli learner misses. So TLS confirms the third row of the pattern: coherent→twirled→d3-gated;
  incoherent drift/temporal→certifiable moment (⑤b). (Caveat, grounded in `kam §IV.C`: the 2-point detector
  autocorrelation is INSUFFICIENT to fully witness streaky/non-Markovian temporal structure — the certify check
  needs a higher-order or fixed-marginal temporal statistic, not a bare lag-1 autocorr; cf. the Sarovar §6.5
  faithfulness caveat.)
- **The deeper teacher value — TLS is a MICROSCOPIC ORIGIN, not a new axis.** Gao grounds ⑤b physically: the
  drift/temporal-correlation axis is not an ad-hoc add-on but the QEC-level shadow of 1/f TLS dynamics. It also
  supplies the **knob semantics** for a do() intervention (coupler-frequency / Δ tuning → g̃ ∝ 1/Δ; DD/echo
  refocusing → suppress; this is a real deployed mitigation = frequency planning + DD), useful for the UQ-layer
  counterfactual `do()` on the teacher.
- **Epistemic classes for the prereg:**
  - TLS temporal-correlation + drift envelope (⑤b reuse) = **(b) prediction band** — a certifiable temporal-
    moment/drift misspecification, magnitude bracketed (1/f^1.05; rates 0.6 mHz–0.2 GHz; occasional jumps).
  - coherent TLS exchange (vacuum Rabi / non-local Bell) = **(c)/bounded-simplification** — coherent → twirled →
    d3-gated; rare for the shared-defect case; do NOT inflate.
  - the "TLS is the microscopic origin of ⑤b" + the do()-knob (Δ-tuning / DD) framing = **(c) heuristic/
    interpretation**, not a derivation premise.

## Trust [ours]
Full main-text 精读: the shared-coupler-TLS identification (Fig 1-2, the iSWAP excitation-transfer verification),
Eq.1 dispersive g̃, the coherence numbers (T1=44.7µs, T2R=0.4µs→T2E=16µs, T_φ=1.1µs), the 1/f^1.05 / ten-decade
spectrum + Dutta-Horn TLF model, the multipartite Bell-generation + "temporally correlated errors" statement,
the iSWAP gate-error sims (300–500 MHz detuning for sub-1%; Zeno/anti-Zeno at Γ≈δ). SI Sections VI-XIV
(noise-spectroscopy details, gate-sim setup) skimmed. The coherent→twirled→d3-gated vs incoherent-drift→
certifiable verdict and the "TLS = microscopic origin of ⑤b, reuse not new operator" mapping are [ours],
grounded in the 1/f / non-Markovian / temporally-correlated nature read directly + the certifiability map.
