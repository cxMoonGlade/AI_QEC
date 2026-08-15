# Full-text review — Sung, Ding, Braumüller, Vepsäläinen, Kannan, Kjaergaard, Greene, Samach, McNally, Kim, Melville, Niedzielski, Schwartz, Yoder, Orlando, Gustavsson, Oliver, "Realization of high-fidelity CZ and ZZ-free iSWAP gates with a tunable coupler" (arXiv:2011.01261)

> **Provenance (2026-06-29): FULL-TEXT read (精读).** PDF `outputs/papers/2011.01261.pdf` → txt
> `outputs/papers/2011.01261.txt` (PyMuPDF, 34 pages, 131 443 chars). All §/Eq/Fig/Table refs from that
> text. [Figures not pixel-extracted — figure facts = captions + numbers stated in text.] Published as
> Phys. Rev. X **11**, 021058 (2021).

## Why this note exists [ours]
Grounds the **physical origin + magnitude** of QEC-Twin mechanism **M22 = coherent_cxx_parasitic_coupling**,
the pure two-qubit XX parasitic coupling `H = J_xx · X⊗X` (more precisely the transverse/flip-flop exchange
`g̃(σ⁺σ⁻ + σ⁻σ⁺)`, of which `X⊗X` is the symmetric half). Sung et al. is a **DIRECT** anchor: it (a) writes
the device Hamiltonian with an explicit **direct qubit–qubit transverse exchange term `g12`**, (b) **measures**
the **effective transverse coupling** `g̃_iSWAP` (the σ⁺σ⁻+σ⁻σ⁺ swap rate) as a function of coupler frequency
by fitting excitation-exchange oscillations, and (c) reports the **measured magnitude `g12/2π = 5.0 MHz`** in a
real MIT/Lincoln device parameter table.

## Metadata [paper]
- Authors: Y. Sung et al. (17 authors), MIT Research Lab of Electronics / Dept. EECS / Dept. Physics + MIT
  Lincoln Laboratory.
- Venue / status: arXiv:2011.01261 (Nov 2020; v3 18 Jun 2021). Published Phys. Rev. X 11, 021058 (2021),
  **DOI 10.1103/PhysRevX.11.021058** (verified against the arXiv abstract page 2026-06-30).
- Type: **experiment** (superconducting transmon device) + supporting theory (beyond-dispersive coupler model).

## Executive summary [paper]
A flux-tunable transmon **coupler** sits between two transmon qubits (QB1, QB2). The qubit–qubit interaction
is the **sum of a direct N.N.N. exchange `g12` and a coupler-mediated virtual exchange**; tuning the coupler
frequency `ωc` lets the two cancel (net coupling ≈ 0 at idle) or open an avoided crossing (gate ON). The
**transverse (iSWAP/flip-flop) coupling** is `g̃_iSWAP`, measured by preparing |100⟩ and watching it swap to
|001⟩. They demonstrate a CZ gate (99.76 %) and a **ZZ-free iSWAP gate (99.87 %)**, both T1-limited, by going
beyond the dispersive approximation to suppress the parasitic **longitudinal ZZ** while keeping the transverse
swap. Headline coupling numbers: `g1c/2π = g2c/2π ≈ 72 MHz` (qubit–coupler), **`g12/2π = 5.0 MHz`**
(direct qubit–qubit transverse exchange), residual ZZ `ζ` cancellable to ≈ 0.

## Method (deep) [paper]
**Device Hamiltonian (§I, Fig. 1a, Table I).** Three Duffing (anharmonic) oscillators — QB1 (ω1), coupler
(ωc), QB2 (ω2) — pairwise coupled "through exchange-type interactions with coupling strengths g1c, g2c, and
g12", with `g1c = g2c ≫ g12` (lines 152–155). The qubit–qubit term is the **direct exchange `g12`**; in
two-level form this is the transverse flip-flop `g12(σ⁺₁σ⁻₂ + σ⁻₁σ⁺₂)` (same structure made explicit in the
companion theory Yan et al. 1803.09813 Eq. 1, see that note).

**Effective transverse coupling `g̃` (the load-bearing object).** Tuning `ωc` sets the **effective QB1–QB2
coupling**: bias `ωc` near the qubits → "opening of the avoided crossings (|g̃_CZ| > 0, |g̃_iSWAP| > 0)"
(lines 223–225); bias it away → "the effective QB1–QB2 coupling is nearly zero ... (gic/(ωc−ωi) < 1/20)"
(lines 212, 217). The coupler **"switches off the effective transverse coupling between QB1 and QB2"**
(lines 941–942) — this verbatim phrase identifies `g̃_iSWAP` as exactly the transverse σ⁺σ⁻+σ⁻σ⁺ (= XX+YY)
exchange.

**Measurement of `g̃_iSWAP` (Fig. 2c–d, §II, lines 329–355).** Prepare |100⟩, bring |100⟩/|001⟩ on
resonance, "let them complete half an oscillation" so the states fully swap; the population transfer to
|001⟩ vs delay `τ` and coupler frequency `ωc` is a sinusoid. **Fit the excitation-exchange oscillations** to
extract the **swap rate `|2g̃_iSWAP|/2π`** (and analogously `|2g̃_CZ|/2π` from |101⟩↔|200⟩). The iSWAP gate
runs in **30 ns**, the CZ in 60 ns, in a strongly hybridized regime `gic/(ωc−ωi) ≈ 1/3`.

**ZZ residual (the parasitic *longitudinal* term, for contrast) (§V, Fig. 5, lines 740–897).** The negative-
anharmonicity transmons give an always-on `ζ` (ZZ) from |101⟩ level repulsion; they cancel it by engineering
the coupler level structure (`ηc/2π = −90 MHz`), reaching ZZ-free operation. `ζ/2π` extracted from the phase
accumulated over a swap period `2π/g̃_iSWAP`.

## The MECHANISM (for implementation) [paper → ours]
The **transverse / XX-type parasitic coupling** in a real transmon pair:

- **Exact term.** Direct qubit–qubit exchange `H_xx,direct/ℏ = g12 (σ⁺₁σ⁻₂ + σ⁻₁σ⁺₂)`
  `= (g12/2)(X₁X₂ + Y₁Y₂)` (two-level RWA; the symmetric `X⊗X` half is `J_xx = g12/2`). The **total effective**
  transverse coupling seen by the qubits is `g̃ = g12 + (coupler-mediated virtual exchange)`, tunable in sign
  and magnitude via `ωc`; at idle `ωc,idle` it is tuned to ≈ 0 (the *residual*), at the gate point it is tens
  of MHz.
- **Physical origin.** Two channels: (1) **direct capacitive N.N.N. coupling** `g12` (always-on, never exactly
  zero — set by the small stray capacitance `C12` between the two qubit pads), and (2) **coupler-mediated
  virtual exchange** through the tunable transmon coupler. The "parasitic" residual XX is what survives when
  the architecture tries to null the *net* coupling but cannot null the direct `g12` independently.
- **Measured magnitudes (Table I, lines 1277–1328; idling config ω1/2π=ω2/2π=ωc/2π=4.16 GHz):**
  - **`g12/2π = 5.0 MHz`** → **direct transverse exchange `g12 = 2π × 5.0 MHz = 0.0314 rad/ns`**; the `X⊗X`
    coefficient `J_xx = g12/2 = 2π × 2.5 MHz = 0.0157 rad/ns`.
  - `g1c/2π = 72.5 MHz`, `g2c/2π = 71.5 MHz` (qubit–coupler; line 1209 "≈ 72 MHz").
  - Anharmonicities `η/2π`: QB1 −220, CPLR −90, QB2 −210 MHz.
  - The **effective** transverse swap `g̃_iSWAP` (gate-ON) is much larger than `g12` (tens of MHz) because the
    coupler-mediated channel adds constructively; at idle it is tuned to ≈ 0.

**[ours] → M22 magnitude:** a realistic **always-on residual XX (`J_xx · X⊗X`)** in a tunable-coupler transmon
sits at the **direct-exchange floor `g12/2 ≈ 2π × (1–3 MHz) ≈ 0.01–0.02 rad/ns`** when the coupler nulls the
net coupling, and the **full transverse coupling reaches tens of MHz (≳ 0.1–0.3 rad/ns) when activated**. For a
*parasitic* (unwanted, idle) term, ~few MHz / ~10⁻² rad/ns is the grounded magnitude.

## The OBSERVABLE / metric [paper]
- **Swap-rate spectroscopy:** `|2g̃_iSWAP|/2π` extracted from the **frequency of coherent population exchange**
  |100⟩↔|001⟩ vs delay `τ` (Fig. 2c–d). This is the operational readout of the transverse coupling magnitude.
- **Residual ZZ `ζ/2π`:** phase accumulated over a swap period — the *longitudinal* parasitic, distinguished
  cleanly from the transverse `g̃`.
- Gate quality scored by **interleaved randomized benchmarking** (Fig. 5e): iSWAP interaction fidelity
  `F = 99.87 ± 0.23 %`, T1-limited.

## Findings + numbers [paper]
- Direct qubit–qubit transverse exchange **`g12/2π = 5.0 MHz`** (Table I).
- Qubit–coupler `g1c/2π = 72.5`, `g2c/2π = 71.5 MHz`.
- ZZ-free iSWAP: 30 ns, interaction fidelity **99.87 %**; CZ 60 ns, **99.76 %**; both ~T1-limited.
- Residual ZZ `ζ` tunable to ≈ 0 via coupler anharmonicity `ηc/2π = −90 MHz`.
- Strong-hybridization gate regime `gic/(ωc−ωi) ≈ 1/3`; idle null `< 1/20`.

## Limitations [paper]
- The **transverse** coupling is the *useful* gate coupling here, not framed as an error — but its **always-on
  direct floor `g12`** is exactly the parasitic-XX picture M22 needs; the paper does not separately quote a
  *residual transverse* number at idle (it states net ≈ 0, but `g12 = 5 MHz` is the irreducible direct piece).
- Two-level/RWA picture for the exchange; the real device is multi-level (Duffing) — the XX+YY ↔ pure-XX
  identification holds in RWA, breaks at strong drive.
- Device-specific magnitudes (one MIT/Lincoln tunable-coupler device); `g12` depends on `ω1, ω2, ωc` (footnote
  c) — not a universal constant.

## Relevance to qec_twin [ours]
- **Grounds M22's magnitude.** `J_xx ≈ g12/2 ≈ 2π × 2.5 MHz ≈ 0.016 rad/ns` for the always-on direct exchange;
  the activated/effective transverse coupling reaches tens of MHz. Use the **few-MHz / ~10⁻² rad/ns** band for
  a *parasitic* (idle, unwanted) `H = J_xx X⊗X`, and tens-of-MHz only when modelling a coupler intentionally
  ON.
- **Correction it forces:** a σ_x⊗σ_x term in a real transmon is most naturally the **symmetric half of an
  exchange `g(σ⁺σ⁻+σ⁻σ⁺) = (g/2)(XX+YY)`** — i.e. it comes paired with an equal `Y⊗Y`. A **pure** `X⊗X`
  (without `Y⊗Y`) is NOT what capacitive/exchange coupling produces; pure-XX would require breaking the
  exchange (RWA) symmetry (e.g. a driven/parametric term, or a deliberately anisotropic coupler). M22 as
  "pure XX" is an idealization — its physically-grounded sibling is the XX+YY flip-flop. [Flag for the
  pre-registration: declare whether M22 models pure-XX (idealized, no direct device origin at this magnitude)
  or the XX+YY exchange (device-grounded, this paper).]
- **Reuse:** the swap-rate spectroscopy `|2g̃|/2π` is the right *observable* to ground any "coupling magnitude"
  claim against; tie M22's `J_xx` to it.

## How to use / trust + open questions [ours]
- **Trust:** full-text 精读; magnitudes are from the explicit device parameter table (Table I) and named
  passages — **certificate-grade for the published numbers** (`g12/2π = 5.0 MHz`, `g1c ≈ 72 MHz`). Figures not
  pixel-extracted, but the load-bearing numbers are stated in text/table, not only in figures.
- **Open questions for M22:** (1) Does the twin's M22 mean pure `X⊗X` or the XX+YY exchange? (resolve before
  pre-reg). (2) For the *parasitic* (idle) regime, the grounded floor is the direct `g12` (~few MHz); confirm
  the twin uses that band, not the tens-of-MHz gate-ON value, when calling it "parasitic."
- **GT-feasibility:** the `g(σ⁺σ⁻+σ⁻σ⁺)` Hamiltonian is trivially closed-form / 2-qubit-exact — independent
  ground truth for the joint-Lindbladian Axis-1 carrier is available (no MC needed at this scale).
