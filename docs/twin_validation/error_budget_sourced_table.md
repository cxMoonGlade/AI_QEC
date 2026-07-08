# Sourced error-budget + bath-spectrum table — the composition inputs for the (B) coupled noise model

**Date 2026-07-01. Theory-first deliverable — every number carries its source (arXiv id + table/§) and the
line locus in the cached full text (`outputs/papers/<id>.txt`).** Purpose: ground the COMPOSED (B) model —
Markovian background at real budget shares + the coupled non-Markovian mechanism at ITS real share — so no
mechanism is ever again assigned an artificial rate (the "one mechanism eats the whole budget" error).
Epistemic classes: every published number = **(a) cited fact**; every transfer/mapping decision = **(c)
declared design choice**; transfers across device classes = **declared brackets**.

## 1. Surface-code error budgets (1/Λ₃/₅), two generations side by side

Method (both): (Λ₃/₅)⁻¹ = Σᵢ wᵢ·p⁽ⁱ⁾_expt — component error × sensitivity weight [2207.06431 §XVII Eq;
2408.13687 suppl. Eq (5), txt:1964-1990].

| Component | Sycamore 72Q p_expt | wᵢ | share | Willow-era 72Q budget p_expt | wᵢ | share |
|---|---|---|---|---|---|---|
| CZ gates (local Pauli) | 4.85e-3 | 54.5 | **29.4%** | 2.8e-3 | 65 | **41%** |
| CZ crosstalk | 9.5e-4 | 158 | **16.7%** | 5.5e-4 | 91 | **11%** |
| CZ leakage | 2.0e-4 | 125* | 2.8% | 2.0e-4 | 108 | 5% |
| **Data qubit idle** | **2.46e-2** | 7.0 | **19.2%** | **0.9e-2** | 10 | **20%** |
| Readout | 1.96e-2 | 5.6 | 12.2% | 0.8e-2 | 6 | 11% |
| Reset | 1.86e-3 | 5.6 | 1.2% | 1.5e-3 | 6 | 2% |
| SQ gates | 1.09e-3 | 78.7 | 9.6% | 6.2e-4 | 63 | 9% |
| Leakage (heating) | 6.4e-4 | 125 | 8.9% | 2.5e-4 | 18 | 1% |

Sources: **Sycamore** = arXiv:2207.06431 (Nature 614, 676 (2023)) TABLE III [txt:4535-4560], 精读 note
`docs/papers/reading_notes/google_suppressing_errors_budget_2207.06431.md`; **Willow-era 72Q budget** =
arXiv:2408.13687 TABLE S4 [txt:2051-2091], sensitivities assume perfect DQLR + correlated matching
[txt:1978-1983], 精读 note `docs/papers/reading_notes/google_below_threshold_error_budget_2408.13687.md`.

**Cross-generation structure (the load-bearing reading):**
- **Data-qubit idle ≈ 19–20% of the budget in BOTH generations** — the share is stable even as the absolute
  error fell 2.7× (2.46e-2 → 0.9e-2). This is the grounded share for the dephasing-type mechanism slot.
- CZ-related total: ~49% (Sycamore) → ~57% (Willow-72Q budget rel. share). For Sycamore, crosstalk + CZ
  leakage alone is ~19.5%; crosstalk + CZ leakage + leakage-heating rows is ~28.4%. For Willow, the main
  text separately states **"correlated errors make up an estimated 17% of the budget"** [txt:289-291].
- **Model–experiment gap: "the error budget overpredicts Λ by 20%, indicating that most but not all error
  effects in our processor have been captured"** [2408.13687 main text, txt:286-289] — the un-modeled
  residual that motivates coupled/non-Markovian modeling. (a)-cited fact; its attribution is OPEN.

## 2. Detection fractions + device parameters (the observable-scale anchors)

| Quantity | Value | Source |
|---|---|---|
| Detection prob., weight-4 stabilizers | 0.185±0.018 (d5); 0.175±0.017 (d3 avg) | 2207.06431 [txt:263-267] |
| Detection prob., weight-2 stabilizers | 0.119±0.012 (d5); 0.115±0.008 (d3 avg) | 2207.06431 [txt:267-270] |
| Sycamore 72Q coherence | T1 = 20 µs; T2,CPMG = 30 µs | 2207.06431 [txt:149-150] |
| Willow-era 105Q processor coherence | T1 = 68 µs; T2,CPMG = 89 µs | 2408.13687 [txt:127-130]; not a 72Q Table-S4 coherence row |
| Cycle time | 1.1 µs | 2408.13687 [txt:16-17,100] |
| Willow d7 logical vs best physical lifetime | 291±6 µs vs 119±13 µs (2.4×) | 2408.13687 [txt:207-209] |

⇒ **Reference detector-event scale ≈ 0.10–0.19 per stabilizer per round** (weight-dependent). Our earlier
"detector rate 0.085" was realistic as a TOTAL detection fraction but was produced by ONE mechanism —
the composition error this table exists to prevent.

## 3. The non-Markovian / correlated candidate rows (where OUR mechanism sits)

- **Anchor quote (mechanism siting):** *"A significant contribution to the logical error budget is data
  qubit decoherence during the readout and reset of the measure qubits. **The primary decoherence mechanism
  is dephasing induced by low-frequency flux noise.** We mitigate dephasing through dynamical decoupling
  with XY-4 phase cycling…"* — 2207.06431 §XI.A [txt:1306-1318]. ⇒ the data-idle row (19–20%) IS
  low-frequency-flux-noise dephasing, and the published p_expt is the **post-DD residual** (declare: our
  mechanism models the residual channel, not the bare noise).
- **CZ crosstalk (11–16.7%)**: "unwanted interactions… can induce correlated ZZ and swap-like errors"
  [2408.13687 txt:281-284] — the SPATIAL correlated slot (matrix-g candidate).
- **Rare correlated bursts**: detection-fraction bursts ~once/hour (~1 per 3e6 shots), decay constant
  400–700 µs, measure qubits spatially grouped — distinct from quasiparticle bursts [2408.13687
  txt:2170-2182]. Out of the per-round composition; bracketed separately (consistent with the block-
  decomposition bracket).
- **The +20% unexplained residual** (§1) — not attributable from these papers alone; the honest slot for
  "structure beyond the local-Pauli + known-correlated model."

## 4. Bath spectral parameters (the pipeline input J(ω) → BCF → SDP → {H, Γ⪰0, g})

| Parameter | Value | Source + scope |
|---|---|---|
| 1/f flux-noise PSD at 1 Hz | A_Φ = (1.7 µΦ₀)² | Bylander et al., arXiv:1101.4707 (Nat. Phys. 7, 565 (2011)) [txt:248] — Ramsey/echo analysis, flux qubit |
| 1/f exponent (0.2–20 MHz, CPMG spectroscopy) | S_Φ ∝ 1/f^α, **α = 0.9**, amplitude (0.8 µΦ₀)² (low-f linear fit) | 1101.4707 [txt:433-434, 667, 680], 精读 note `docs/papers/reading_notes/bylander_flux_noise_spectroscopy_1101.4707.md` |
| Non-exponential free-decay; DD-refocusable | Ramsey non-exp., echo → T1-limited | 1101.4707 [txt:87-97, 240-247] |
| TLS bath: nonlocal/non-Markovian structure | TLS-qubit couplings + telegraph switching | gao 2605.23385 (精读 note `gao_nonlocal_nonmarkovian_tls_2605.23385.md`) |
| TLS/quasiparticle burst phenomenology | once/hour; 400–700 µs decay | 2408.13687 [txt:2170-2182]; tan 2406.18897 + kurilovich 2506.18228 (精读 notes) |

**Classical-limit validity (frequency hierarchy at 20 mK — explicit, after a 2026-07-02 user challenge):**
"high-T/classical" is a PER-MODE statement (βℏω_noise ≪ 1), NOT a device-temperature statement. Hierarchy:
Δ_Al/h ≈ 44 GHz (gap; superconductivity needs k_BT ≪ Δ ✓) ≫ ω_q/2π ≈ 5 GHz (qubit quantum: βℏω_q ≈ 12 ✓)
> k_BT/h ≈ 0.42 GHz (20 mK) ≫ ω_noise/2π ≤ 2.3 MHz (the fitted dephasing band: βℏω ≈ 5.5e-3 ⇒ classical ✓).
All three regimes coexist; the classical treatment applies ONLY to the ≤MHz dephasing band (pure dephasing
additionally uses only the SYMMETRIZED correlator — the antisymmetric part is a deterministic phase). The
limit BREAKS for GHz-band components (T1/relaxation, near-resonant TLS exchange) — those slots are reserved
for the pseudomode quantum-bath engine, not the classical field.

**Declared bracket (Rule III):** Bylander's amplitudes are measured on a **flux qubit** (superconducting
persistent-current qubit — NOT a photonic platform; the pseudomode METHOD has quantum-optics pedigree but
is platform-agnostic mathematics, and the spectral INPUTS here are superconducting-sourced), not Google's
tunable transmons. Google's own papers CONFIRM the mechanism ("low-frequency flux noise", §3) but do not
publish A_Φ in 2207.06431/2408.13687. ⇒ the spectral **shape** (1/f^α, α≈0.9) is (a)-sourced for Bylander's
flux-qubit spectroscopy and transferred here only as a declared bracket/design prior; the **amplitude** for
our model is CALIBRATED to reproduce the sourced share (data-idle p_expt of §1) rather than taken from the
flux-qubit value — amplitude = (c) share-calibrated. A device-matched transmon flux-noise spectroscopy source
can later tighten this bracket.

## 5. Mapping to the composed (B) model (all (c) design decisions, grounded above)

| Model slot | Budget rows | Share (Willow Table S4) | Our representation |
|---|---|---|---|
| **Markovian background** | CZ local + SQ + readout + reset | ~63% | standard Pauli/measurement-flip channels at the p_expt of §1 |
| **Coupled non-Markovian mechanism** | data-qubit idle (flux-noise dephasing, post-DD) | **~20%** | pseudomode dephasing channel from J(ω): shape prior = 1/f^0.9 (Bylander flux-qubit bracket), amplitude calibrated so the mechanism ALONE reproduces data-idle p_expt ≈ 0.9e-2/cycle |
| **Spatial correlated slot** | CZ crosstalk | 11–17% | shared-bath matrix-g across neighboring qubits (Pilot-4-certified assemble) |
| Deferred/bracketed | leakage rows; bursts | ~6–12%; rare | out of per-round scope (leakage = ADR 0010 axis); bursts bracketed |
| Open residual | budget-vs-experiment gap | ~20% overprediction | NOT modeled; the honest "unowned structure" slot |

**Calibration loop (next step, the PILOT-1 pipeline):** J(ω) = 1/f^0.9 tail (+ TLS Lorentzians) with
amplitude → BCF → matrix-pencil → SDP → {H, Γ⪰0, g}; run the mechanism ALONE in the carrier; check its
per-cycle data-idle-equivalent error hits 0.9e-2 (share-consistency); THEN compose with the background.

## Provenance / reading status
Full texts cached: `outputs/papers/2207.06431.txt` (44 pp), `2408.13687.txt` (27 pp), `1101.4707.txt`.
Full-text 精读 notes now exist for all three table-critical sources:
`docs/papers/reading_notes/google_suppressing_errors_budget_2207.06431.md`,
`docs/papers/reading_notes/google_below_threshold_error_budget_2408.13687.md`, and
`docs/papers/reading_notes/bylander_flux_noise_spectroscopy_1101.4707.md`.

Remaining caveats: figures were not pixel-extracted; the 68 µs / 89 µs Willow coherence row is sourced for
the 105Q processor, not for the 72Q Table-S4 budget device; and the Bylander PSD amplitude is not transferred
as a Google-device fact.
