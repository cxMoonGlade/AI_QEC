# Full-text 精读 — McKay, Wood, Sheldon, Chow, Gambetta, "Efficient Z-Gates for Quantum Computing" (arXiv:1612.00858)

> **Provenance (2026-06-30): FULL-TEXT 精读.** Source:
> `outputs/papers/1612.00858.txt` (PyMuPDF text extraction, 8 pages). Figures are not
> pixel-extracted; all equation, table, and figure references are from the extracted
> text. Published version: Phys. Rev. A 96, 022330 (PRA 96, 022330), arXiv:1612.00858v2
> [quant-ph], 28 Jun 2017 (dated June 29, 2017). (The PRA citation is from the task
> brief; the extract carries only the arXiv stamp on p. 1.)

Epistemic tags throughout: **[paper]** = stated/derived in the paper;
**[twin]** = our application or inference.

---

## Why load-bearing [twin]

This note is the primary literature anchor for **QEC-Twin M7 = coherent_rz_overrotation
(`RZ(ε)` coherent unitary error)** (`docs/error_mechanisms.md`; pre-reg
`m7_coherent_rz_overrotation_prereg.md`). M7 is the single-qubit `θ_Z Z` term of the
Twin's coherent generator `H_θ = Σ_k θ_k P_k`, physically a **frequency-detuning / phase
error** on a superconducting transmon. McKay et al. is the reference that (a) identifies
a Z-rotation error explicitly as "an unwanted Z-gate" / "a phase error" and shows it is
corrected by the inverse Z, (b) gives the **off-resonance-rotation (ORR) unitary**
`U₁ = exp(−it[(Ω/2)σ̂_X + Δσ̂_Z])` in which a **detuning Δ generates a σ_Z rotation** —
the physical origin of an RZ over-rotation, and (c) shows the **Stark-shift ORR error
increases for short gates**, giving the regime where coherent Z-errors matter. It grounds
M7's operator form and physical cause; it is not a QEC/LER reference.

---

## Metadata [paper]

- **Authors:** David C. McKay, Christopher J. Wood, Sarah Sheldon, Jerry M. Chow, Jay M.
  Gambetta (IBM T. J. Watson Research Center, Yorktown Heights, NY).
- **arXiv:** 1612.00858v2, quant-ph, 28 Jun 2017.
- **Type:** theory + experimental demonstration of the virtual-Z (VZ) gate on a real
  transmon.
- **Device [paper]:** "fixed-frequency superconducting transmon qubit of frequency
  ω/2π = 5.0353 GHz, anharmonicity α/2π = −235.5 MHz, and typical coherences T1 = 54(1)
  µs, Tφ = 135(4) µs."
- **Headline result [paper]:** DRAGZ "realizes a 13.3 ns Xπ/2 gate characterized by low
  error (1.95[3] × 10⁻⁴) and low leakage (3.1[6] × 10⁻⁶)."

---

## Executive summary [paper]

A Z-gate on a superconducting qubit is a change in the relative phase between |0⟩ and
|1⟩. It can be realized physically by detuning, or implemented as a **virtual** Z-gate
(VZ): "it is equivalent to rotate the axes with respect to the qubit state — such a gate
is known as a virtual Z-gate which corresponds to adding a phase offset to the drive
field for all subsequent X and Y gates." [paper] The VZ-gate is "essentially perfect"
(zero duration, self-calibrated). The paper shows VZ-gates lower error per Clifford and
**correct coherent rotation errors** (phase errors and off-resonance-rotation errors)
as an alternative to DRAG pulse shaping.

---

## M7 anchor 1 — the Z-error IS a phase error, corrected by the inverse Z [paper]

**VERBATIM (Sec. III "Correcting Errors with VZ-gates", p. 4, lines 470–472):**

> "For example, a VZ-gate can correct a phase error, i.e. an unwanted Z-gate, by applying
> the inverse Z-gate."

**[twin]** This is the cleanest published statement that the M7 mechanism — a coherent
**phase / control error** — is identically "an unwanted Z-gate," i.e. an RZ(ε)
over-rotation. The Twin's M7 carrier operator `H_M7 = (coeff/2)·Z`,
`U_M7 = exp(−i (ε/2) Z) = RZ(ε)` (`m7_coherent_rz_overrotation_prereg.md` §1) is exactly
the "unwanted Z-gate" this sentence names, and its physical correctability by `RZ(−ε)`
is the do()/knob inverse.

---

## M7 anchor 2 — detuning Δ generates a σ_Z rotation (the ORR unitary) [paper]

The off-resonance-rotation (ORR) error along X is the physical source of a Z-rotation
error. **VERBATIM (Eqs. 22–23, p. 4, lines 474–482):**

> "VZ-gates can also correct most off-resonance-rotation (ORR) errors. The unitary
> operator due to an ORR along the X axis is,"

```
U₁ = e^{ −i t [ (Ω/2) σ̂_X + Δ σ̂_Z ] } ,                         (22)
U₁ = e^{ −i (Ω_R t / 2) [ cos(λ) σ̂_X + sin(λ) σ̂_Z ] } ,         (23)
where  tan(λ) = Δ/Ω   and   Ω_R = √(Ω² + Δ²).
```

**[twin]** Eq. (22) is the load-bearing physics: a **detuning Δ (drive off resonance)
adds a `Δ σ̂_Z` term to the generator**, tilting the rotation axis off X toward Z by
`tan(λ) = Δ/Ω`. In the limit Ω→0 (or as the residual after the intended X rotation is
removed) this is precisely an RZ over-rotation — the M7 generator `H ∝ Z` arises from
frequency detuning. The COH_RZ family thus has a concrete superconducting origin:
qubit-frequency/drive detuning during the gate.

**The Z-correction exists when** `sin(θ/2)/cos(λ) ≤ 1` [paper, Eqs. 24–26, lines
505–528]: a valid `Zξ · U₁ · Zξ = Xθ` correction with `tan(ξ) = sin(λ) tan(Ω_R t/2)`.
"Physically there is no solution when the rotation is sufficiently off-resonance such
that it cannot pass through the plane defined by the desired final state. For example, a
detuned π pulse cannot be compensated" (lines 537–541). **[twin]** This bounds the regime
where an RZ over-rotation is a benign correctable phase vs an uncorrectable axis error —
relevant to whether the Twin's M7 knob is do()-invertible at a given ε.

---

## M7 anchor 3 — Stark-shift ORR increases for short gates [paper]

**VERBATIM (p. 4–5, lines 557–563):**

> "When resonantly driving the |0⟩ to |1⟩ transition, the drive frequency is only
> slightly detuned from the higher level transitions such as |1⟩ to |2⟩, and so there is
> a strong Stark effect which shifts the frequency of the |1⟩ state during the drive. The
> strength of the Stark shift is inversely proportional to the detuning, and thus ORR
> errors increase for short gates because of Fourier broadening of the drive frequency."

**[twin]** This pins the **regime** where M7 (Z over-rotation from a Stark-induced
frequency shift) is largest: short, high-amplitude gates. It is the Z-axis analogue of
the short-gate coherent-error growth that Lazăr et al. (2212.01077) document for the
amplitude/area (X/Y) channel — i.e. the over-rotation family is a short-gate phenomenon
across axes.

**Supporting detail [paper]:** the DRAG parameter that optimizes fidelity is `β = 1/2α`
in theory (line 429), but "in practice the experimentally optimized value of β is
different since the DRAG pulse also compensates phase errors from other sources" (lines
430–432) — i.e. real gates carry a residual coherent phase (Z) error that calibration
absorbs.

---

## Gate-set / Hamiltonian context [paper]

- **Drive Hamiltonian (rotating frame, Eq. 8, lines 230–236):**
  `H̃/ħ = Σₙ (Ωₙ(t)/2)[cos(γₙ)σ̂_X + sin(γₙ)σ̂_Y]`, so the drive phase γ selects the
  X (γ=0) / Y (γ=π/2) axis, and a VZ is a γ-offset (Eqs. 10–15). **[twin]** This is why
  X (M6) and Y (M20) rotations differ only by a phase, and Z (M7) is the orthogonal
  axis — the three COH_R* families are the three Bloch axes of this same generator.
- **Arbitrary SU(2) (Eqs. 16–19, Table I):**
  `U(θ,φ,λ) = Z_{φ−π/2}·Xπ/2·Z_{π−θ}·Xπ/2·Z_{λ−π/2}`; common gates listed (Zπ: θ=0,
  φ=π/2, λ=π/2; H: θ=π/2, φ=π/2, λ=π/2). **[twin]** The H-axis composite (M27) is built
  from X and Z rotations here, tying the over-rotation family to the Hadamard-axis
  mechanism.
- **VZ is near-perfect [paper]:** interleaved RB of the S=Zπ/2 gate gives error
  "−1.7(1.0)×10⁻⁵ with systematic errors bounds of [0,6×10⁻⁴] ... consistent with the
  VZ-gate having zero error" (lines 451–454). **[twin]** This is the do()-knob ideal: a
  perfect Z correction implies the M7 over-rotation is, in principle, fully removable in
  software — the residual the Twin models is the *uncorrected* detuning, not the VZ
  itself.

---

## What the paper does NOT provide [twin]

- **No QEC / LER number, no surface code.** Single-qubit gate engineering only; it notes
  leakage "can have detrimental effects on error correction protocols [18, 19]" (lines
  702–703) but makes no logical-error claim.
- **No injected-Z-angle sweep.** Unlike Sheldon (X over-rotation π/64…π/256), the Z error
  here is characterized via the ORR/detuning model and corrected, not deliberately
  amplitude-swept. A specific residual-Δ or residual-Z-angle magnitude for the M7 sweep
  is **[not in extraction]** — the paper's quantitative outputs are EPC/EPG/leakage
  (e.g. EPG 1.95(3)×10⁻⁴ for DRAGZ), not a Z over-rotation angle in radians.
- **No closed-form `1−F_e(ε)` for RZ.** The infidelity↔ε relation M7 uses comes from the
  Schumacher–Nielsen ledger (`schumacher_nielsen_entanglement_fidelity_quant-ph-0205035.md`),
  not from this paper.

---

## Limitations [paper]

1. **Higher-level / leakage limit.** "Ultimately leakage is limited by the finite
   temperature of the qubit" (abstract); the f-state leakage floor (here from an
   effective T = 46 mK) is set by heating, not pulse shape.
2. **ORR-correction non-existence for large detuning.** Eq. (24)'s solution requires
   `sin(θ/2)/cos(λ) ≤ 1`; a detuned π pulse is uncorrectable (lines 537–541).
3. **Multiqubit phase bookkeeping.** In multiqubit systems the VZ phase imprints on
   two-qubit drives (Eqs. 27–28); "for flux-tunable qubits ... compatibility with the
   VZ-gate is more difficult" (lines 782–784). The clean single-qubit Z picture does not
   transfer unchanged to two-qubit gates.

---

## Trust [twin]

- **"Phase error = unwanted Z-gate, corrected by inverse Z" (Sec. III):**
  certificate-grade for identifying the M7 mechanism as an RZ over-rotation and for the
  do()-knob inverse `RZ(−ε)`.
- **ORR unitary `U₁ = exp(−it[(Ω/2)σ_X + Δσ_Z])` (Eq. 22), detuning→σ_Z:**
  certificate-grade for the physical origin of the M7 generator `H ∝ Z`.
- **Stark-shift ORR increases for short gates (lines 557–563):** measurement-/
  theory-grade statement of the regime where M7 is largest.
- **Specific M7 over-rotation angle / residual Δ magnitude for the sweep:** ABSENT
  ([not in extraction]) — the Twin's ε range for M7 is anchored on Sheldon's π/64…π/256
  X-injection scale + the calibration-residual argument, not pinned here.
