# Full-text review — Mundada, Zhang, Hazard, Houck, "Suppression of Qubit Crosstalk in a Tunable Coupling Superconducting Circuit" (arXiv:1810.04182)

> **Provenance (2026-06-29): FULL-TEXT read (精读).** PDF `outputs/papers/1810.04182.pdf` → txt
> `outputs/papers/1810.04182.txt` (PyMuPDF, 11 pages, ~1275 lines, 31 877 chars). All §/Eq/Fig/Table refs from
> that text. [Figures not pixel-extracted.] Published as Phys. Rev. Applied **12**, 054023 (2019).

## Why this note exists [ours]
**INDIRECT** support for QEC-Twin **M22 = coherent_cxx_parasitic_coupling**. Mundada et al. is primarily a **ZZ
crosstalk suppression** paper (the parasitic *longitudinal* term), but it (a) writes the **effective
transverse exchange `J`** between two qubits in **clean closed form** (Eq. 4), (b) shows the activated
transverse coupling `δ·∂J/∂Φ` is **"tunable from zero to a few MHz"**, and (c) quantifies the **residual ZZ
`ζ/2π = 2.26 MHz`** for contrast. It is the device-physics companion that gives the **exchange-coupling
formula** + a clean **"few MHz" transverse magnitude band**, while making explicit that the *parasitic* term
the architecture fights is **ZZ, not XX**.

## Metadata [paper]
- Authors: P. S. Mundada, G. Zhang, T. Hazard, A. A. Houck — Princeton, Dept. of Electrical Engineering.
- Venue / status: arXiv:1810.04182 (Oct 2018). Published Phys. Rev. Applied 12, 054023 (2019).
- Type: **experiment** (two transmons + tunable coupler) + theory.

## Executive summary [paper]
Two transmons coupled via a flux-tunable coupler. **Static ZZ crosstalk** (the always-on parasitic
longitudinal term) is cancelled by tuning the coupler so the ZZ contributions from two coupling paths
destructively interfere (verified by **simultaneous randomized benchmarking**). A **parametrically activated
iSWAP** (flux-modulating the coupler at `ωΦ = ω2 − ω1`) implements the transverse two-qubit gate while ZZ is
nulled: Bell-state fidelity 98.5 %, √iSWAP 94.8 %. The transverse coupling is the **effective exchange `J`**;
its modulation derivative `δ·∂J/∂Φ` sets the iSWAP rate, **tunable from zero to a few MHz**.

## Method (deep) [paper]
**Parametric iSWAP / effective transverse exchange (Eqs. 3–4, lines 226–252) — transcribed:**
Flux modulation `Φ(t) = Θ + δ cos(ωΦ t + φ)` with `ωΦ = ω2 − ω1`. The effective interaction in the rotating
frame is

```
H_int/ℏ = (δ/2)(∂J/∂Φ) ( a†_1 a_2 e^{−iφ} + a_1 a†_2 e^{iφ} )      # Eq. 3  — transverse (flip-flop) exchange
```

with the **effective exchange coupling**

```
J = Σ_{j=±} (g_{1j} g_{2j} / 2) [ 1/(ω1 − ωj) + 1/(ω2 − ωj) ]        # Eq. 4
```

mediated by the couplers (sum over coupler modes `j = ±`). The `a†_1 a_2 + a_1 a†_2` structure is the **same
σ⁺σ⁻ + σ⁻σ⁺ transverse flip-flop** (= ½(XX+YY) in the qubit subspace). **`δ·∂J/∂Φ` "can be tuned from zero to
a few MHz for moderate modulation amplitude δ"** (lines 304–307).

**ZZ residual `ζ` (the parasitic *longitudinal* term, the paper's main object).** Measured `ζ/2π` from Ramsey;
gate error at `ζ/2π = 2.26 MHz` is shown to increase (line 210); the coupler is tuned to the **null point
`ζ = 0`**. Device qubit/coupler frequencies and coupling-related scales (Appendix): detunings of order
85–750 MHz, coupler/qubit anharmonicities ~290–400 MHz.

## The MECHANISM (for implementation) [paper → ours]
- **Transverse term:** effective exchange `H/ℏ ∝ J (a†_1 a_2 + a_1 a†_2) = J(σ⁺₁σ⁻₂ + σ⁻₁σ⁺₂)` with the
  **closed-form `J = Σ_j (g1j g2j /2)[1/(ω1−ωj)+1/(ω2−ωj)]`** (Eq. 4) — coupler-mediated virtual exchange,
  parameterized by qubit–coupler couplings `g_{ij}` and mode detunings.
- **Physical origin:** virtual exchange through the tunable-coupler mode(s); the same dispersive
  second-order-coupling mechanism as Yan/Sung, written for the explicitly multi-mode (`j = ±`) coupler.
- **Magnitude [paper]:** the **activated** transverse coupling `δ·∂J/∂Φ` spans **0 → a few MHz** →
  **0 → ≈ 2π × (1–3 MHz) ≈ 0–0.02 rad/ns**. (The *static* `J` itself is dispersively suppressed at the ZZ-null
  bias; the *activated* swap is the few-MHz figure.) Residual ZZ at the off-null `ζ/2π = 2.26 MHz`.

**[ours] → M22:** corroborates the **few-MHz / ~10⁻² rad/ns** band for a realistic transverse coupling, and —
critically — shows the architecture's *parasitic* fight is against **ZZ (longitudinal)**, with the transverse
exchange being the *engineered* gate term. A *parasitic transverse* (residual XX) term, if present, sits at or
below this few-MHz activated scale.

## The OBSERVABLE / metric [paper]
- **Simultaneous randomized benchmarking** — detects ZZ crosstalk (the longitudinal parasitic) as excess error
  when both qubits are driven; the primary metric here.
- **Ramsey `ζ/2π`** — direct readout of the residual ZZ strength.
- **Parametric population exchange** |10⟩↔|01⟩ — reads the transverse iSWAP rate `δ·∂J/∂Φ`.

## Findings + numbers [paper]
- Effective exchange `J` closed form (Eq. 4); activated `δ·∂J/∂Φ` **0 → few MHz**.
- Residual ZZ `ζ/2π = 2.26 MHz` (off-null) → ~0 at the null (destructive interference of two coupler paths).
- Bell-state fidelity **98.5 %**, √iSWAP **94.8 %**.
- iSWAP via flux modulation at `ωΦ = ω2 − ω1` (e.g. 275 MHz), max population swap at ~190 ns.

## Limitations [paper]
- **The parasitic term targeted is ZZ (longitudinal), not XX** — so this is INDIRECT for a *pure-XX* mechanism;
  it grounds the transverse-exchange *form* and *magnitude band*, not an isolated residual-XX measurement.
- The static transverse `J` is dispersively small at the operating bias; the few-MHz figure is the *activated*
  (parametrically driven) coupling, not an always-on parasitic.
- Two-qubit, single-coupler-pair device; magnitudes device-specific.

## Relevance to qec_twin [ours]
- **Corroborates magnitude:** transverse exchange in the **few-MHz / ~10⁻² rad/ns** band — consistent with Yan
  (theory) + Sung (`g12/2π = 5 MHz`). Use as a second independent anchor for M22's `J_xx`.
- **Reinforces the pure-XX correction:** like Yan/Sung, the device term is the **exchange `J(σ⁺σ⁻+σ⁻σ⁺) =
  (J/2)(XX+YY)`**, not pure `X⊗X`. And it makes explicit that the *always-on parasitic* in these devices is
  **ZZ**, not XX — M22-as-parasitic-XX is therefore an idealization to declare, whereas a *parasitic ZZ* would
  be the more device-faithful "always-on" coherent two-qubit error (cf. existing notes
  pettersson_fors_zz_2408.15402, kubo_dtc_residual_zz_2402.05361).
- **Reuse:** Eq. 4 gives an explicit `J(g_{ij}, detunings)` if a *derived* magnitude is wanted from circuit
  parameters rather than a quoted MHz value.

## How to use / trust + open questions [ours]
- **Trust:** full-text 精读; Eq. 3/4 transcribed verbatim (certificate-grade for the form). The "few MHz" band
  is a stated magnitude (numerics-grade); the ZZ `ζ/2π = 2.26 MHz` is a measured number.
- **Open questions for M22:** confirms the cross-cutting issue — **declare pure-XX vs XX+YY**, and note that
  the device-grounded *always-on parasitic* is ZZ; a residual *transverse* term is bounded by the few-MHz
  activated scale.
- **GT-feasibility:** the `J(a†a + aa†)` exchange is closed-form / 2-qubit-exact — independent ground truth
  available without MC.
