# Full-text 精读 — Lazăr, Ficheux, Herrmann, Remm, Lacroix, Hellings, Swiadek, Colao Zanuz, Norris, Bahrami Panah, Flasby, Kerschbaum, Besse, Eichler, Wallraff (ETH Zurich), "Calibration of Drive Non-Linearity for Arbitrary-Angle Single-Qubit Gates Using Error Amplification" (arXiv:2212.01077)

> **Provenance (2026-06-30): FULL-TEXT 精读.** Source:
> `outputs/papers/2212.01077.txt` (PyMuPDF text extraction, 13 pages; this close-read
> covers the main text pp. 1–6 and Appendices A–E pp. 7–10, where the load-bearing
> equations/numbers live). Figures are not pixel-extracted; all equation, table, and
> figure references are from the extracted text. arXiv:2212.01077v1 [quant-ph], 2 Dec
> 2022 (dated December 5, 2022). (No journal citation line in the extract.)

Epistemic tags throughout: **[paper]** = stated/derived in the paper;
**[twin]** = our application or inference.

---

## Why load-bearing [twin]

This note is the primary literature anchor for **QEC-Twin M6 = coherent_rx_overrotation
(`RX(ε)`) and M20 = coherent_ry_overrotation (`RY(ε)`)** (`docs/error_mechanisms.md`;
pre-regs `m6_*`, `axis1_mechanism_completeness_prereg.md` group 1). M6/M20 are
**drive-amplitude / pulse-area errors**: the X (and by drive-phase symmetry, Y) rotation
angle deviates from its target because the drive rate does not scale linearly with the
programmed pulse amplitude. Lazăr et al. is the reference that (a) measures, on a real
transmon, a concrete **over-rotation angle (≈ 0.4°) and the amplitude error that causes
it (≈ 0.7 mV)**, and (b) states the **mechanism**: a simple linear amplitude downscaling
introduces a *systematic over-rotation* because the drive response is non-linear. It
grounds the operator interpretation (`ε` = pulse-area error) and the realistic magnitude;
it is not a QEC/LER reference.

---

## Metadata [paper]

- **Authors:** Stefania Lazăr, Quentin Ficheux (equal contribution), Johannes Herrmann,
  Ants Remm, Nathan Lacroix, Christoph Hellings, Francois Swiadek, Dante Colao Zanuz,
  Graham J. Norris, Mohsen Bahrami Panah, Alexander Flasby, Michael Kerschbaum,
  Jean-Claude Besse, Christopher Eichler, Andreas Wallraff (ETH Zurich; ETH–PSI Quantum
  Computing Hub).
- **arXiv:** 2212.01077v1, quant-ph, 2 Dec 2022.
- **Type:** experimental — error-amplification calibration on two flux-tunable transmons.
- **Devices [paper, Table I]:** two qubits from two 17-qubit devices A and B.
  Device A: ωQ/2π = 6.257 GHz, α/2π = −153 MHz, T1 = 12.3 µs, T2* = 9.86 µs,
  15-ns π-pulse amplitude Aπ = 730 mV. Device B: ωQ/2π = 4.640 GHz, α/2π = −183 MHz,
  T1 = 60.9 µs, T2* = 55.3 µs, Aπ = 235 mV.

---

## Executive summary [paper]

Standard gate calibration "assume[s] that the control parameters respond linearly to the
control fields," but mixers, amplifiers, and pulse generators are non-linear at high
power. The non-linearity makes the qubit drive rate scale sub-linearly with programmed
amplitude, so a rotation calibrated by linear amplitude scaling **over-rotates**. Using
an N-pulse error-amplification sequence, the authors measure these small rotation errors
("for a 15-ns pulse, the rotation angles deviate by up to several degrees from a linear
model"), correct them, and reach **coherence-limited 15-ns gates with control errors
~2×10⁻⁴ (half the total gate error) and leakage below 6×10⁻⁵**. [paper]

---

## M6/M20 anchor 1 — the measured over-rotation angle and amplitude error [paper]

The N-pulse method initializes |+⟩ and applies N repetitions of `X_{π/k+ε}` gates,
amplifying the per-gate angle error ε; the excited-state population is fit to a
master-equation model. **VERBATIM (Sec. II, p. 2, lines 178–183 of the extract):**

> "To calibrate rotation angles up to π/2, we use a pulse sequence in which each π-pulse
> is split into k repetitions of Xπ/k+ε gates, see the pulse sequence in Fig. 1(d). For
> an Xπ/2 rotation, we find an over-rotation error of around 0.4◦ [see Fig. 1(d)],
> corresponding to an amplitude error of around 0.7 mV."

**[twin]** This is the load-bearing magnitude: a real superconducting `Xπ/2` carries an
**over-rotation ε ≈ 0.4° ≈ 0.0070 rad** (degree→rad conversion ours) sourced by a **0.7
mV amplitude error** on the programmed pulse. This directly grounds M6's interpretation
of `ε` as a pulse-area error and anchors the *lower* end of the calibration-residual
regime the Twin sweeps. By the drive-phase symmetry of the rotating-frame Hamiltonian
(X and Y differ only by drive phase γ), the identical mechanism applies to RY (M20).

**Companion magnitudes [paper] (same family, other angles):**
- `Xπ` (32-ns DRAG, device A): "around 0.9◦ of rotation error ... around 1.7 mV of
  amplitude error for a pulse amplitude of 335 mV" (lines 153–158).
- `X5π/6`: "an under-rotation error of around −1.0◦, corresponding to an amplitude error
  of around −1.9 mV" (lines 190–192) — note **sign flips to under-rotation** at this
  larger angle.
- Shorter gate → larger error: "around one degree of rotation error for a 32-ns gate,
  and 3.6◦ when the length is decreased to 15 ns" (lines 396–398).

---

## M6/M20 anchor 2 — linear downscaling *causes* a systematic over-rotation [paper]

This is the mechanism statement. **VERBATIM (Sec. II, p. 2, lines 203–207):**

> "Figure 1(h, i) shows that a simple linear downscaling of the amplitude with respect to
> the calibrated π-pulse amplitude introduces a systematic over-rotation error, see the
> filled purple region in Fig. 1(i)."

And the supporting cause (lines 113–120): "a pulse produced by the waveform generator
with amplitude A ... reaches the qubit with an amplitude which shows a reduction from a
linear behavior ... This reduction becomes more pronounced with larger input amplitudes
and leads to a rotation angle of the qubit state which is smaller than the targeted one."

**[twin]** This pins the *physical origin* of the M6/M20 over-rotation knob: it is **not**
random — it is a **systematic, deterministic, angle-dependent coherent error** produced by
the non-linear drive response when one assumes linear amplitude↔angle scaling. That is
exactly a coherent `RX(ε)`/`RY(ε)` with ε set by the calibration model error, which is
why M6/M20 are coherent (quadratic-accumulating) mechanisms, not stochastic Pauli.

**Polynomial response model (Eq. 1, lines 210–212), verbatim:**

```
θ(Ã) = 180◦ ( 1 + b(Ã² − 1) + a(Ã⁴ − 1) ) Ã ,                   (1)
```

where `Ã = A/Aπ` is the amplitude scaled to the π-pulse amplitude, and `a, b` are
fit parameters "capturing the non-linearity of the upconversion circuitry." [paper]
**[twin]** The deviation `θ(Ã) − 180°·Ã` from the linear model IS the over-rotation
angle as a function of target angle — a deterministic ε(θ) the Twin could in principle
import if it wanted a hardware-shaped (rather than swept-constant) M6/M20 profile.

---

## M6/M20 anchor 3 — coherent control error is half the gate error, > leakage [paper]

**VERBATIM (abstract + Sec. III):** "control errors reach 2×10⁻⁴, which accounts for half
of the total gate error" (lines 18–19); at 15 ns "the coherent gate errors account for
about half of the total gate error [Fig. 2(a)], while the leakage remains comparatively
low at around 6×10⁻⁵" (lines 422–425); "the coherent errors produced by this effect are
up to one order of magnitude larger than leakage into the non-computational states"
(lines 432–434).

**[twin]** Quantitative weight of the M6/M20 channel on a real device: at the
short-gate operating point the **coherent over-rotation is the dominant non-decoherence
error and ~10× the leakage** — i.e. the over-rotation family is a first-order coherent
contribution, consistent with the Twin treating M6/M20 as load-bearing Axis-1
mechanisms. Random-angle XEB with linear scaling gives "around 3.8 × 10⁻⁴ of coherent
control errors" vs `8.9(4) × 10⁻⁴` total with polynomial correction (lines 634–639).

**Master-equation extraction model [paper, App. B, Eq. B1]:** `H = Ωσx/2` with
`dρ/dt = −i[H,ρ] + (Γφ/2)(σzρσz − ρ) + Γ1(σ−ρσ+ − {σ+σ−,ρ}/2)`,
`σ+ = |1⟩⟨0|`, `σ− = |0⟩⟨1|`, `Γ1 = 1/T1`, `Γφ = 1/T2 − 1/(2T1)`, `Ω = απ/τ`
with `α` the dimensionless fraction of a π rotation, `A = αAπ` (lines 775–843).
**[twin]** This is the exact RX generator `H = (Ω/2)σx` — the same `H_M6 = (coeff/2)X`
form the Twin's carrier uses — with the angle error entering as the fitted Rabi fraction
α; it cross-checks the Twin's operator and gives the T1/T2 dressing used to read ε off
the population.

---

## What the paper does NOT provide [twin]

- **No QEC / LER number, no surface code.** Single-qubit gate calibration only; QEC codes
  are cited as motivation (refs [4–8]), no logical-error statement.
- **No pure RZ (M7) over-rotation.** The errors are amplitude/area errors on X (and, by
  symmetry, Y) rotations; Z gates are virtual (software phase, "perfect fidelity",
  App. D line 1002). The paper explicitly notes its protocol "is not highly sensitive to
  other types of control errors, such as leakage, crosstalk, or phase errors which may
  arise from off-resonant driving" (lines 673–676). For M7 the companion is McKay et al.
  1612.00858 (`mckay_efficient_z_gates_1612.00858.md`).
- **No universal ε.** "While the exact magnitude of these errors is specific to our
  setup, the presented method is applicable to any source of non-linearity" (abstract,
  lines 22–24). The 0.4°/0.7 mV numbers are device/line-specific — a realistic anchor,
  NOT a constant to freeze.
- **No closed-form `1−F_e(ε)`.** The infidelity↔ε relation M6/M20 use comes from the
  Schumacher–Nielsen ledger, not from this paper (this paper reports E, Einc, Ecoh, L
  from RB/PB/XEB).

---

## Limitations [paper]

1. **Setup-specific magnitude.** The dominant non-linearity is "the frequency
   upconversion device" (lines 261–263, App. C); the 0.4°/0.7 mV scale is tied to that
   line and the 1-dB compression point, not universal.
2. **Residual unmodeled errors.** After correction, "small residual oscillations ... are
   not caused by rotation errors captured by our model, and could originate ... from
   off-resonant driving by higher harmonic frequency components, or from uncompensated
   non-linear distortions" (lines 165–171) — i.e. the over-rotation model does not
   capture everything.
3. **Room-temperature calibration incomplete.** Path-2 (rerouted to detection)
   "systematically overestimate[s]" the in-situ result "by about 0.2◦ at an amplitude
   ratio of 0.5" (App. C, lines 927–931); the in-situ N-pulse measurement is required.
4. **Sign/angle dependence.** The error is over-rotation at small angles (Xπ/2: +0.4°)
   but under-rotation at larger ones (X5π/6: −1.0°); a single scalar ε does not describe
   the full angle range — Eq. (1)'s polynomial does.

---

## Trust [twin]

- **Over-rotation angle ≈ 0.4° ↔ amplitude error ≈ 0.7 mV (Xπ/2, Sec. II):**
  measurement-grade on this transmon — the realistic magnitude anchor for the M6/M20
  calibration-residual regime, NOT a universal constant.
- **"Linear amplitude downscaling introduces a systematic over-rotation" (Sec. II):**
  certificate-grade for the *mechanism* (deterministic, coherent, angle-dependent
  pulse-area error) — grounds M6/M20 as coherent `RX/RY(ε)` knobs.
- **Generator `H = (Ω/2)σx` extraction model (App. B, Eq. B1):** certificate-grade for
  the operator form match to the Twin's `H_M6 = (coeff/2)X`.
- **Coherent control error ≈ half the gate error and ~10× leakage at 15 ns (Sec. III):**
  measurement-grade weight of the over-rotation channel on real hardware.
- **Any QEC/LER implication, and any RZ (M7) over-rotation:** ABSENT — out of scope here
  (M7 grounded by 1612.00858).
