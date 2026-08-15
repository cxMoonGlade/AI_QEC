# Full-text 精读 — Sheldon, Magesan, Chow, Gambetta, "Procedure for systematically tuning up crosstalk in the cross resonance gate" (arXiv:1603.04821)

> **Provenance (2026-06-30): FULL-TEXT 精读.** Source:
> `outputs/papers/1603.04821.txt` (PyMuPDF text extraction, 6 pages). Figures are
> not pixel-extracted; all equation, figure, and section references are from the
> extracted text (NUL bytes handled). Published as Phys. Rev. A 93, 060302(R)
> (Rapid Communication), 2016. arXiv:1603.04821v1 [quant-ph], 15 Mar 2016 (the
> arXiv line is in the extraction, page 1; the "(Dated: March 16, 2016)" line is
> the only date stamp in the extract — the PRA 93, 060302 journal citation is from
> the task metadata, NOT printed in this extraction).

Epistemic tags throughout: **[paper]** = stated/derived/measured in the paper;
**[twin]** = our application or inference.

---

## Why load-bearing [twin]

This note is the **device-MEASUREMENT** anchor for QEC-Twin **M29 =
coherent_zx_parasitic_coupling** (the parasitic / residual `Z⊗X` cross-resonance
term). M29's operator grounding already carries Magesan–Gambetta arXiv:1804.04073 as
the CR **effective-Hamiltonian THEORY** (the closed-form `H_CR ∝ ZX`). Sheldon et al.
is the **complementary primary source**: it is the IBM experiment that **measures the
full CR Hamiltonian on real fixed-frequency transmons via Hamiltonian tomography**,
extracting `ZX` (and the five other interaction terms `{IX, IY, IZ, ZX, ZY, ZZ}`)
directly from measured target-qubit Rabi rates. It therefore grounds M29's `Z⊗X` as a
**device-real, measured** interaction term — not merely an algebraic axis or a
theoretical effective coefficient. The pair {Magesan 1804.04073 (theory), Sheldon
1603.04821 (measurement)} gives M29 **two independent DIRECT-physical references, both
device-real ZX** — the strongest grounding of the coherent 2q parasitic-coupling
family.

---

## Metadata [paper]

- **Authors:** Sarah Sheldon, Easwar Magesan, Jerry M. Chow, Jay M. Gambetta (IBM
  T.J. Watson Research Center, Yorktown Heights, NY). [paper]
- **arXiv:** 1603.04821v1, quant-ph, 15 Mar 2016. Published Phys. Rev. A 93,
  060302(R) (per task metadata; not in the extracted body). [paper / metadata]
- **Type:** experiment + theory (Hamiltonian model + measured device data;
  interleaved-RB fidelities). [paper]
- **Subject:** the cross-resonance (CR) all-microwave entangling gate on two
  fixed-frequency transmons coupled by a bus resonator; a calibration procedure that
  "accurately measures the full CR Hamiltonian" and a second (active-cancellation)
  target drive that cancels unwanted CR-Hamiltonian components, raising the
  interleaved-RB two-qubit gate fidelity above 99%. [paper]

---

## Executive summary [paper]

The CR gate is an all-microwave two-qubit gate for fixed-frequency transmons that
needs no tunability; it had historically been limited to gate times > 300–400 ns and
fidelities of 94–96%. **[paper]** This paper develops (a) an effective block-diagonal
Hamiltonian model of the two-transmon system under CR drive, and (b) a **Hamiltonian-
tomography calibration procedure that "accurately measures the full CR Hamiltonian"**
by driving CR for varying times and measuring the target-qubit Rabi oscillations,
conditioned on the control qubit in `|0⟩` and `|1⟩`. **[paper]** From the two
control-conditioned Bloch generators they extract the six interaction terms
`{IX, IY, IZ, ZX, ZY, ZZ}` of the CR Hamiltonian. **[paper]** The measured Hamiltonian
agrees with the effective-Hamiltonian theory and reveals the error terms (notably an
unexpected `IY` attributed to classical crosstalk, and a `ZZ`) that limited prior CR
fidelity. **[paper]** Adding a second microwave drive on the target qubit to cancel
the unwanted `cos(φ)IX + sin(φ)IY` components reduced the gate time by ~2× and pushed
the **interleaved-RB CR-gate fidelity above 99%** (`f = 0.991 ± 0.002` at a 160 ns
gate; `f = 0.948 ± 0.018` for the same gate time WITHOUT the cancellation tone).

---

## The CR Hamiltonian structure (Eq. 2) [paper]

The effective block-diagonal model `H_BD := T†HT` (with `T` the minimal-distance
block-diagonalizing unitary, Eq. 1) predicts, for this device, **"ZX and IX
components of similar magnitude, negligible IZ and ZZ contributions, and a large ZI
term arising from a Stark shift of the control qubit from off-resonant driving."**
**[paper]** The complete CR Hamiltonian has the structure (VERBATIM, Eq. 2):

```
       Z ⊗ A     I ⊗ B
H  =  -------  +  -------  .                                   (2)
          2          2
```

**[paper]** Here `A` and `B` are single-target-qubit operators (the conditional and
the unconditional parts respectively); the `Z⊗A/2` block is the **control-conditioned**
part (`Z` on the control), and `I⊗B/2` is the unconditioned single-qubit part. **[twin]**
This is the device-measured form whose conditional block carries the `ZX` term — i.e.
M29's `Z⊗X` is one Cartan-tensor component of `Z⊗A`. The control-side operator is `{I, Z}`
(the same restriction Magesan 1804.04073 App. C states), so the entangling content lives
in `Z⊗A`. [paper for Eq. 2; twin for the M29 mapping]

---

## Hamiltonian tomography: extracting ZX from measured Rabi rates [paper]

This is the **load-bearing extraction** for M29 (the device MEASUREMENT of ZX).

**Method (VERBATIM, paraphrase-bridged where noted).** **[paper]** "we have developed
a protocol for experimentally measuring the CR Hamiltonian … This measurement is
accomplished by turning on a CR drive for some time and measuring the Rabi
oscillations on the target qubit. We project the target qubit state onto x, y, and z
following the Rabi drive and repeat for the control qubit in `|0⟩` and `|1⟩`."

**Target Bloch-vector norm (VERBATIM, Eq. 3)** — used to find the entangling gate
length (the two qubits are maximally entangled when this `→ 0`):

```
‖R⃗‖ = sqrt( (⟨X⟩₀ + ⟨X⟩₁)² + (⟨Y⟩₀ + ⟨Y⟩₁)² + (⟨Z⟩₀ + ⟨Z⟩₁)² )      (3)
```

**Bloch-equation fit model (VERBATIM, Eqs. 4–5).** **[paper]** "We fit the Rabi
oscillations corresponding to the control in `|0⟩` and `|1⟩` separately with a Bloch
equation model function":

```
r⃗̇(t) = e^{A t} r⃗(0) ,                                        (4)

        ⎡  0    Δ    Ω_y ⎤
A   =   ⎢ −Δ    0   −Ω_x ⎥ .                                   (5)
        ⎣ −Ω_y  Ω_x   0  ⎦
```

**[paper]** "Here `Δ` is the control drive detuning, and `Ω_{x,y}` is the Rabi drive
amplitude in along `{x, y}`. `r⃗(t)` is the vector composed of the measured
expectation values as a function of the length of the applied Rabi drive,
`(⟨X(t)⟩, ⟨Y(t)⟩, ⟨Z(t)⟩)`. We find two generators corresponding to the control qubit
in either `|0⟩` or `|1⟩`, characterized by the vectors"

```
v⃗_{0,1} = ( Ω^{0,1}_x , Ω^{0,1}_y , Δ^{0,1} ) .
```

**The six interaction terms + the ZX/IX extraction formulas (VERBATIM).** **[paper]**
"From these parameters we derive the CR drive Hamiltonian in terms of the six possible
interactions: `IX, IY, IZ, ZX, ZY, ZZ`. For example,

```
IX = (Ω⁰_x + Ω¹_x)/2     and     ZX = (Ω⁰_x − Ω¹_x)/2 .
```

Note that this method of Hamiltonian tomography is applicable to any system with a
Hamiltonian with the same form as Eq. 2." **[paper]** The paper further notes the
method **scales efficiently** for an n-qubit system (`n(n−1)/2` pairs, each needing
six Rabi measurements).

**[twin]** `ZX = (Ω⁰_x − Ω¹_x)/2` is exactly the **device measurement** of M29's
coupling strength: the difference of the target-qubit x-Rabi rate between control-`|0⟩`
and control-`|1⟩` (the conditional X rotation whose sign is set by the control's Z
state — the literal "ZX" structure M29 certifies). This is the measured counterpart of
Magesan 1804.04073's theoretical `tr(H_CR·ZX/2) = −JΩ/√(Δ²+Ω²)`.

---

## Measured device parameters and magnitudes [paper]

**[paper]** The test device: two fixed-frequency transmons coupled by a bus
resonator. Qubit frequencies **4.914 GHz (target)** and **5.114 GHz (control)**;
anharmonicities **−330 MHz** for both; bus frequency **6.31 GHz**. The qubit–qubit
coupling is **estimated `J/2π = 3.8 MHz`**. Single-qubit gate fidelities (simultaneous
RB): **0.9991 ± 0.0002 (target)**, **0.9992 ± 0.0002 (control)**.

**[paper]** Measured CR-Hamiltonian terms (Fig. 2(b), as a function of two-qubit drive
amplitude): `IZ` and `ZZ` are **small and independent of drive power**; with the CR
drive phase set so `ZY` is small, the **conditional component consists only of `ZX`**;
the measured `ZX` (and `ZZ`) agree with the effective-Hamiltonian theory predictions.
The interaction strengths span the **~2–7 MHz** range on the Fig. 2(b) vertical axis
(interaction strength in MHz vs CR amplitude). [paper — axis range read from the
extracted Fig. 2 tick labels; treat as approximate, figure not pixel-extracted]

**[paper]** Coherence: `T1 = 38 ± 2 / 41 ± 2 µs` (control/target), `T2 = 50 ± 4 /
61 ± 6 µs`; the coherence-imposed fidelity limit is **0.996** — i.e. the measured
fidelity is "still not yet limited by coherence," and some coherent error remains.

---

## The error terms revealed, and the ZX90 goal [paper]

**[paper]** The standard echoed CR gate refocuses `IX, ZZ, ZI` via a π-pulse on the
control and a CR-drive sign flip. An **unexpected `IY` term** appears when the CR phase
is set to maximize `ZX` / zero `ZY`; the paper **attributes this phase difference
between conditional and single-qubit terms to classical crosstalk**. Because `IY` does
not commute with `ZX`, the echo then fails to fully refocus the unwanted interactions
("all higher-order terms of the commutator will be on during the two-qubit gate").

**[paper]** "Ultimately the goal is to tune up a `ZX90`, which is a **generator of a
controlled-NOT (CNOT) with single-qubit Clifford rotations**." The calibration finds
the CR phase `φ₀` maximizing `ZX` (with `ZY = 0`), then a cancellation phase/amplitude
`φ = φ₀ − φ₁` that cancels `cos(φ)IX + sin(φ)IY`. With the cancellation tone
calibrated, the CR-Rabi oscillations are "much closer to the oscillations expected for
a `ZX` drive"; the residual error is consistent with a `ZZ` of the order measured in
the calibration sweeps plus an order-of-magnitude-smaller `IX`.

**[twin]** This is the device confirmation of M29's S2 bounded simplification: the
*pure*-ZX teacher omits the co-occurring `ZI` (large Stark shift), `IX`, `IY`
(crosstalk), and small `ZZ` that accompany `ZX` in the real CR Hamiltonian. Sheldon
measures all of them. The `ZX90` = CNOT-generator statement is the device-side echo of
the M29 derivation's "conditional-X / CNOT generator" label.

---

## Interleaved-RB fidelity [paper]

**[paper]** Two-qubit gate fidelities are characterized by **interleaved randomized
benchmarking** (standard RB to get the average fidelity per Clifford, then interleaving
the CR gate between random Cliffords; fits over 35 random sequences of 100 Clifford
gates). Headline numbers:

- **`f = 0.991 ± 0.002`** for a 160 ns echoed CR gate (with active cancellation; the
  160 ns includes 20 ns of single-qubit echo buffered by two 10 ns delays). [paper]
- **`f = 0.948 ± 0.018`** for the same gate time **without** the cancellation tone —
  demonstrating the cancellation drive removes the CR-Hamiltonian error terms. [paper]
- Abstract/intro headline: **"interleaved randomized benchmarking fidelities exceeding
  99%"**, with gate time reduced by ~2× vs the prior 300–400 ns CR gates. [paper]

**[twin]** IRB fidelity is the device-level figure of merit for the CR gate; it is the
operational measure whose coherent-error budget M29's `1−F_e` (entanglement
infidelity) models on the twin side. Not the same metric, but the device anchor for
"how good a real CR `ZX` gate is."

---

## Relevance to qec_twin M29 [twin]

### (a) Does this paper ground `Z⊗X` as a device-real interaction term?

**YES — directly, as a MEASUREMENT.** The CR Hamiltonian (Eq. 2, `Z⊗A/2 + I⊗B/2`) has
a control-conditioned `Z⊗A` block, and `ZX` is one of the six terms the paper
**measures** via Hamiltonian tomography (`ZX = (Ω⁰_x − Ω¹_x)/2`, the control-conditioned
target x-Rabi-rate difference). This is the device-measured counterpart of Magesan
1804.04073's theoretical `H_CR ∝ ZX`. **[twin]** Together the two clear M29's
operator-grounding bar with **two independent DIRECT-physical references, both
device-real ZX**: Magesan = CR effective-Hamiltonian *theory*; Sheldon = CR *measurement*.

### (b) Does this paper pin the M29 angle ε?

**NO — and M29 does not claim it does.** The paper measures interaction *strengths* in
MHz (e.g. `ZX` in the few-MHz band, `J/2π = 3.8 MHz` coupling), which anchor M29's
**physical magnitude** (`J_zx ≈ 2π × (0.1–3) MHz`, the same anchor M29 §1 already
carries). The carrier-native angle convention (`ε = coeff·dt`, factor 1/4) is a
convention statement, not claimed equal to any Sheldon rate. The S2 device-faithfulness
bound (pure-ZX omits ZI/IX/IY/ZZ) is *quantified* by this paper's Fig. 2/Fig. 3
measurements.

---

## Limitations [paper]

1. **One device.** All measured numbers are from a single two-transmon test system;
   they anchor magnitude/structure, not a universal value.
2. **Pure ZX is not what is measured.** The real CR Hamiltonian carries
   `{IX, IY, IZ, ZX, ZY, ZZ}` plus a large `ZI` Stark term simultaneously; the paper's
   whole point is that these co-occur and must be canceled/echoed. A *pure*-ZX teacher
   (M29) is the isolated entangling axis, with the local Stark/crosstalk terms
   (`ZI/IX/IY`, echo- or cancellation-removable) and the small correlated `ZZ` modeled
   as separate generators. [This is exactly M29's declared, bounded S2 simplification.]
3. **IY from classical crosstalk is device-specific.** The unexpected `IY` term is
   attributed to classical crosstalk and is a property of this hardware's control
   wiring; it is not a fundamental part of the CR Hamiltonian.
4. **Fidelity not yet coherence-limited; saturation at short gate times** attributed
   (suspected) to leakage to higher levels or drive-induced dephasing — i.e. residual
   coherent error remains even with cancellation; the `T1/T2` limit (0.996) is not yet
   reached.
5. **Figure values approximate.** Interaction-strength magnitudes are read from
   extracted figure tick labels (Figs. 2–3 not pixel-extracted); treat the few-MHz
   ranges as approximate.

---

## Trust [twin]

- **`Z⊗X` as a device-real, measured CR interaction term (Eq. 2 structure + the
  `ZX = (Ω⁰_x − Ω¹_x)/2` tomography formula):** certificate-grade for the *operator
  identity / device origin* of M29 — this is a direct measurement on real transmons,
  independent of (and corroborating) the Magesan effective-Hamiltonian theory.
- **Magnitude anchor (`ZX` few-MHz; `J/2π = 3.8 MHz`):** numerics-grade device anchor
  for M29's physical `J_zx` band; not a universal constant.
- **The pure-ZX simplification (M29 S2):** this paper *bounds* it (it measures the
  co-occurring `ZI/IX/IY/ZZ` that a pure-ZX teacher omits), confirming S2 is
  declared-and-bounded, not silent.
- **IRB fidelity (`f = 0.991 ± 0.002` / `0.948 ± 0.018`):** the device figure of merit
  for the CR gate; an operational companion to M29's `1−F_e`, not the same metric.

---

## "[not in extraction]" gaps (flagged for honesty)

- **The journal citation line "Phys. Rev. A 93, 060302".** [not in extraction] — the
  extracted body carries only the arXiv stamp (1603.04821v1) and "(Dated: March 16,
  2016)". The PRA 93, 060302(R) reference is from the task metadata, declared as such
  above.
- **Numerical values of the measured `ZX` coefficient at specific drive amplitudes.**
  Only the figure-axis ranges (interaction strength ~2–7 MHz vs CR amplitude/phase,
  Figs. 2–3) are recoverable from the extracted tick labels; the precise per-point `ZX`
  values live in the (non-pixel-extracted) figures, not the text. The explicit numbers
  present in the body are `J/2π = 3.8 MHz`, the qubit/bus frequencies, the
  anharmonicities, the `T1/T2` values, and the RB fidelities.
- **A closed-form symbolic expression for `ZX(Ω, Δ, J)`.** [not in extraction] — this
  paper extracts `ZX` *empirically* from the fitted Bloch generators (`ZX =
  (Ω⁰_x − Ω¹_x)/2`); the closed-form effective-Hamiltonian expression for the ZX
  coefficient is Magesan 1804.04073's contribution (Eqs. 3.16/4.26 there), not stated
  symbolically here. The two papers are complementary by design (measurement vs theory).
