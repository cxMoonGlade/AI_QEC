# Full-text review — Yan, Krantz, Sung, Kjaergaard, Campbell, Wang, Orlando, Gustavsson, Oliver, "Tunable Coupling Scheme for Implementing High-Fidelity Two-Qubit Gates" (arXiv:1803.09813)

> **Provenance (2026-06-29): FULL-TEXT read (精读).** PDF `outputs/papers/1803.09813.pdf` → txt
> `outputs/papers/1803.09813.txt` (PyMuPDF, 10 pages, ~1144 lines). All §/Eq/Fig/Table refs from that text.
> [Figures not pixel-extracted — figure facts = captions + numbers in text.] Published as Phys. Rev. Applied
> **10**, 054062 (2018).

## Why this note exists [ours]
Foundational **DIRECT** theory anchor for QEC-Twin mechanism **M22 = coherent_cxx_parasitic_coupling** (the
transverse XX coupling `H = J_xx X⊗X`). Yan et al. writes the **two-qubit transverse-exchange Hamiltonian
explicitly** (Eq. 1, the `g12(σ⁺₁σ⁻₂+σ⁻₂σ⁺₁)` term + qubit–coupler exchange), derives the **effective
transverse coupling `g̃` after a Schrieffer–Wolff transformation** (Eq. 2), and shows it is `g̃ = g1g2/Δ + g12`
— a **competition** between a coupler-mediated virtual exchange and the **direct N.N.N. exchange `g12`**, with
a worked realistic magnitude. This is the canonical physical origin of a residual/parasitic transverse (XX-type)
coupling in transmons.

## Metadata [paper]
- Authors: F. Yan, P. Krantz, Y. Sung, M. Kjaergaard, D. Campbell, J. I. J. Wang, T. P. Orlando, S. Gustavsson,
  W. D. Oliver — MIT.
- Venue / status: arXiv:1803.09813v1 (26 Mar 2018). Published Phys. Rev. Applied 10, 054062 (2018).
- Type: **theory** + circuit simulation (proposes the now-standard transmon tunable-coupler architecture).

## Executive summary [paper]
A center **tunable coupler** between two qubits creates two interaction channels: a **direct N.N.N. exchange
`g12`** and an **indirect (virtual) exchange via the coupler**. A Schrieffer–Wolff transformation decouples
the coupler, leaving an **effective two-qubit transverse exchange `g̃(σ⁺₁σ⁻₂+σ⁻₂σ⁺₁)`** with
`g̃ = g1g2/Δ + g12`. Because the virtual term is negative (`1/Δ < 0`) and the direct term positive, `g̃(ωc)`
can be tuned to **exactly zero** at a critical coupler frequency `ωc^off` (the OFF / idle point) — or opened up
for a gate. Errors from known parasitic effects are strongly suppressed; the scheme underlies the Google/MIT
tunable-coupler devices.

## Method (deep) [paper]
**Bare Hamiltonian (Eq. 1, lines 95–111) — the EXACT transverse coupling term, transcribed verbatim:**

```
H = Σ_{j=1,2} ½ ω_j σ^z_j  +  ½ ω_c σ^z_c
      + Σ_{j=1,2} g_j (σ^+_j σ^-_c + σ^-_j σ^+_c)          # qubit–coupler exchange
      + g12 (σ^+_1 σ^-_2 + σ^-_2 σ^+_1)                     # DIRECT qubit–qubit transverse (XX+YY) exchange
```

with `gj > g12 > 0` (N.N. stronger than N.N.N.), qubits negatively detuned `Δj ≡ ωj − ωc < 0`, dispersive
`gj ≪ |Δj|`.

**Effective two-qubit Hamiltonian after Schrieffer–Wolff (Eq. 2, lines 180–197):**
SWT generator `U = exp[ Σ_j (gj/Δj)(σ⁺_j σ⁻_c − σ⁻_j σ⁺_c) ]` decouples the coupler to 2nd order, giving

```
H̃ = Σ_{j=1,2} ½ ω̃_j σ^z_j  +  [ g1 g2 / Δ  +  g12 ] (σ^+_1 σ^-_2 + σ^-_2 σ^+_1)
```

where `ω̃_j = ωj + gj²/Δj` (Lamb shift) and `1/Δ = ½(1/Δ1 + 1/Δ2) < 0`. The **bracket is the total effective
transverse coupling `g̃`** — a virtual-exchange term `g1g2/Δ` (negative) plus the direct exchange `g12`
(positive).

**The OFF point (residual = 0).** Since the two terms have opposite sign, "one can always find a critical value
`ωc^off` at which the two terms cancel out and thereby turn off the coupling, i.e. `g̃(ωc^off) = 0`" (lines
214–219). At idle the coupler is biased to `ωc^off`; the **residual transverse coupling is the small `g̃` left
by imperfect cancellation** — exactly the parasitic XX of M22.

**Realistic capacitive parameters (lines 400–406):** ω1 = ω2 = 4 GHz, ωc = 5 GHz, Δ = −1 GHz, C1=C2=Cc=100 fF,
**C1c = C2c = 1 fF, C12 = 0.02 fF** (the small stray N.N.N. capacitance that sets the direct exchange). The
four dimensionless coupling contributions to the effective coupling are **(i) −1.25, (ii) −0.14, (iii) 0.5,
(iv) 1.0** (lines 405–406) — i.e. the direct and virtual pieces are the **same order of magnitude**, which is
the whole point (the direct `g12` is *not* negligible against the virtual term despite C12 ≪ C1c).

## The MECHANISM (for implementation) [paper → ours]
- **Exact term:** the parasitic/residual transverse coupling is the effective exchange
  `H̃_xx/ℏ = g̃ (σ⁺₁σ⁻₂ + σ⁻₂σ⁺₁) = (g̃/2)(X₁X₂ + Y₁Y₂)`, with **`g̃ = g1g2/Δ + g12`**.
- **Physical origin (two channels):**
  1. **Direct capacitive N.N.N. exchange `g12`** — from the stray capacitance `C12` between the two qubit
     pads; always-on, positive, the irreducible floor.
  2. **Coupler-mediated virtual exchange `g1g2/Δ`** — second-order, negative (Δ < 0), tunable via `ωc`.
  The **residual** parasitic XX is what survives when `g̃(ωc) → 0` is only approximately achieved at idle.
- **Magnitude [paper → ours]:** the paper reports `g̃` *dimensionlessly* (contributions of order ±1) rather than
  in MHz. To get an absolute scale, pair with the companion device (Sung 2011.01261, same group): there the
  direct exchange is **`g12/2π = 5.0 MHz`** and the full activated transverse swap is tens of MHz; the residual
  at the OFF point is tuned toward 0. So:
  - **Direct exchange floor:** `g12 ≈ 2π × 5 MHz ≈ 0.031 rad/ns` (→ `J_xx = g̃/2 ≈ 2π × 2.5 MHz ≈ 0.016 rad/ns`).
  - **Activated `g̃`:** tens of MHz (≳ 0.1–0.3 rad/ns).
  - **Residual (idle, parasitic):** small remainder after OFF-point cancellation — sub-MHz to few-MHz,
    i.e. **≲ 10⁻² rad/ns** for a well-tuned coupler.

## The OBSERVABLE / metric [paper]
- The coupling is read out as the **avoided-crossing / energy-gap `2g̃(ωc)`** of the one-excitation states
  |100⟩/|001⟩ (Fig. 2b caption: "the ωc-dependence of 2g̃ ... energy gap corresponds to the effective coupling
  2g̃", lines 305–317).
- Operationally, `g̃` drives **coherent swap oscillations** between |100⟩ and |001⟩; gate time set by
  `∫₀^τ 2g̃(t) dt = ½` for a full SWAP-half (line 452).

## Findings + numbers [paper]
- Effective transverse coupling **`g̃ = g1g2/Δ + g12`** (Eq. 2) — virtual + direct exchange.
- A coupler frequency `ωc^off` exists where `g̃ = 0` (continuous tunability ⇒ exact OFF).
- Realistic worked example: four contributions of order ±1 (−1.25, −0.14, +0.5, +1.0); **direct and virtual
  pieces are comparable** (C12 = 0.02 fF vs C1c = 1 fF).
- Coupler anharmonicity sign matters: `αc = +100 MHz` (capacitively-shunted) outperforms `αc = −100 MHz`
  for gate error (Fig. 3, lines 511–535).

## Limitations [paper]
- **Magnitudes are dimensionless / simulated**, not measured in MHz here (absolute scale comes from the
  companion experiment Sung 2011.01261). Two-level model for the exchange (multi-level Duffing used only for
  the leakage/error analysis).
- Dispersive assumption `gj ≪ |Δj|` for Eq. 2; the gate regime is weakly/non-dispersive (the OFF condition
  still holds in `gj < |Δj|`).
- The transverse coupling is the *engineered* gate coupling; "parasitic" here = the residual after `g̃ → 0`,
  plus the always-on direct `g12`.

## Relevance to qec_twin [ours]
- **Canonical derivation of M22's term and origin.** The transverse XX(-type) parasitic coupling in transmons
  IS the effective exchange `g̃(σ⁺σ⁻+σ⁻σ⁺)` with `g̃ = g1g2/Δ + g12`; its physical origin is a **direct
  capacitive N.N.N. exchange `g12` plus a coupler-mediated virtual exchange**. Cite Eq. 1 (bare) + Eq. 2
  (effective) for the exact Hamiltonian.
- **Correction it forces (same as Sung):** the device-grounded transverse term is **XX+YY (an exchange), not
  pure XX**. `g̃(σ⁺σ⁻+σ⁻σ⁺) = (g̃/2)(X⊗X + Y⊗Y)`. A *pure* `X⊗X` (M22 as literally `J_xx X⊗X` with no `Y⊗Y`)
  has **no capacitive/exchange origin at this magnitude** — it is an idealization. Declare M22 explicitly as
  either (a) idealized pure-XX (no direct device anchor) or (b) the XX+YY flip-flop (device-grounded, this
  paper + Sung).
- **Reuse:** the OFF-point picture (`g̃ → 0`) directly motivates a *residual* (small, imperfectly-cancelled)
  parasitic-coupling regime — the natural setting for a *parasitic* M22.

## How to use / trust + open questions [ours]
- **Trust:** full-text 精读; the Hamiltonian terms (Eq. 1, Eq. 2) are transcribed verbatim — **certificate-grade
  for the functional form**. Magnitudes are dimensionless/simulated here (numerics-grade for absolute scale;
  the MHz anchor is the companion Sung 2011.01261 Table I — certificate-grade there).
- **Open questions for M22:** (1) pure-XX vs XX+YY exchange — resolve before pre-reg (see Relevance). (2) Use
  the **direct-exchange floor (`g12 ≈ few MHz`) or the residual after OFF-cancellation (sub-MHz–few-MHz)** as
  the parasitic magnitude, NOT the tens-of-MHz activated value.
- **GT-feasibility:** `g̃(σ⁺σ⁻+σ⁻σ⁺)` is closed-form / 2-qubit-exact — an independent ground truth for the
  Axis-1 joint-Lindbladian carrier exists without Monte Carlo.
