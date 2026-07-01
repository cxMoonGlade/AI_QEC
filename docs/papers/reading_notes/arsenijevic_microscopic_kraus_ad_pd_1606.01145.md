# Full-text 精读 — Arsenijević & Banković, "Microscopic Derivation of the One-Qubit Kraus Operators for Amplitude and Phase Damping" (arXiv:1606.01145)

> **Provenance (2026-06-30): FULL-TEXT 精读.** Source:
> `outputs/papers/1606.01145.txt` (PyMuPDF text extraction, 15 pages). The
> extraction contains embedded NUL bytes; quotes below taken after `tr -d '\000'`.
> Figures are not pixel-extracted; equation references read from the extracted text.
> Header: "arXiv:1606.01145v1 [quant-ph] 3 Jun 2016". (No journal citation line in
> this extract.)

Epistemic tags throughout: **[paper]** = stated/derived in the paper;
**[twin]** = our application or inference.

---

## Why load-bearing [twin]

This note anchors the **channel (Kraus-operator) form** of two QEC-Twin mechanisms,
giving the exact operator set the channels apply — what Krantz (1904.06560) gives only as
rates:

- **M4 = T1 amplitude damping.** The standard AD master equation (Eq. 13) and Kraus
  operators `{Ê0 = |0⟩⟨0| + √(1−λ)|1⟩⟨1|, Ê1 = √λ |0⟩⟨1|}` (Eq. 14).
- **M5 = T2 / pure dephasing (phase damping).** The **microscopic Lindblad master
  equation `dρ/dt = r(σ_z ρ σ_z − ρ)`** (Eq. 48), the dephasing rate `r` (Eq. 49), the
  Kraus operators `{Ê0 = √(1−p/2) Î, Ê1 = √(p/2) σ_z}` with **`p(t) = 1 − e^{−2rt}`**
  (Eq. 55), the **completeness relation `Σ_k Ê_k† Ê_k = Î`**, and the **coherence decay
  `φ_τ(σ_x) = e^{−2rt} σ_x`** (Eq. 56b/c) with `φ_τ(σ_z) = σ_z` (Eq. 56d).

The value of this paper for M5 is that the phase-damping Kraus operators are **derived
from a microscopic Hamiltonian/master equation**, not merely asserted — closing the
faithfulness gap "the form of these operators is usually estimated without insight into
the microscopic details."

---

## Metadata [paper]

- **Authors:** M. Arsenijević (Univ. of Kragujevac, Serbia) and N. Banković (Technical
  College of Applied Studies, Kragujevac).
- **arXiv:** 1606.01145v1, quant-ph, 3 Jun 2016.
- **Type:** theory — microscopic derivation of one-qubit AD/PD Kraus operators via the
  Andersson–Cresser–Hall method [Ref. 8: Andersson et al., J. Mod. Opt. 54, 1695 (2007)].
- **Abstract (verbatim):** "This article presents microscopic derivation of the Kraus
  operators for (the generalized) amplitude and phase damping process… The form of these
  operators is usually estimated without insight into the microscopic details of the
  dynamics."

---

## M4 — amplitude-damping channel form [paper]

**Master equation at T = 0 (Eq. 13):**

```
dρ̂_S/dt = (γ/2)(2 σ̂_− ρ̂_S σ̂_+ − σ̂_+ σ̂_− ρ̂_S − ρ̂_S σ̂_+ σ̂_−)              (13)
```

**Standard AD Kraus operators (Eq. 14) — the load-bearing M4 operator set:**

```
Ê0 = |0⟩⟨0| + √(1 − λ(t)) |1⟩⟨1|,    Ê1 = √(λ(t)) |0⟩⟨1|                  (14)
```

**[paper]** with the conventions "σ̂_z = |0⟩⟨0| − |1⟩⟨1|, σ̂_x = |0⟩⟨1| + |1⟩⟨0|, σ̂_y =
i|0⟩⟨1| − i|1⟩⟨0|, and σ̂_± = ½(σ̂_x ± i σ̂_y)." **[twin]** `λ(t)` is the M4 damping
probability (`λ = 1 − e^{−γt} = 1 − e^{−t/T1}`); `Ê1 = √λ |0⟩⟨1|` is the relaxation
(`|1⟩ → |0⟩`) jump — the exact operator M4 applies. The paper also derives the
**generalized** (finite-T) AD channel (Sec. 3, Eqs. 15–17, 25–37) and proves the GAD set
is unitarily equivalent to the standard one, reducing to Eq. 14 "for Nth = 0 i.e. p = 1".
**[twin]** The finite-T (GAD) version connects to M24's nonzero up-rate.

---

## M5 — phase-damping channel form (the load-bearing extraction) [paper]

**[paper]** "The phase damping (PD) quantum channel models pure decoherence without loss
of energy for a single-qubit system." Total-system Hamiltonian (Eq. 47):

```
Ĥ = (ω0/2) σ̂_z + ∫_0^{ωmax} dω â†_ω â_ω + σ̂_z ⊗ ∫_0^{ωmax} dω h(ω)(â†_ω + â_ω)   (47)
```

**Microscopic Markovian master equation (Eq. 48) — the M5 dephasing Lindblad:**

```
dρ̂_S/dt = r(σ̂_z ρ̂_S σ̂_z − ρ̂_S)                                         (48)
```

**Dephasing rate (Eq. 49) [paper]:**

```
r = 2π lim_{ω→0} J(|ω|) ⟨n(|ω|)⟩                                          (49)
```

**[paper]** "under assumption lim_{ω→0} J(|ω|) = 0. J(ω) is the spectral density of the
bath while ⟨n(ω)⟩ is the mean number of the bosons for the thermal state of the bath with
the frequency ω." **[twin]** This grounds the M5 rate `r` in a bath PSD (cf. Krantz Eq. 54
for the T1 analogue) and ties the M5 dephasing to **σ_z (longitudinal) coupling** in
Eq. 47 — exactly Krantz's "pure dephasing is caused by longitudinal noise via the z-axis."

**Phase-damping Kraus operators (Eq. 55) — the M5 operator set:**

```
Ê0 = √(1 − p(t)/2) Î,    Ê1 = √(p(t)/2) σ̂_z       where  p(t) ≡ 1 − e^{−2rt}   (55)
```

**[paper]** "where p(t) ≡ 1 − e^{−2rt} while the **completeness relation
`Σ_k Ê_k(t)† Ê_k(t) = Î`** is satisfied." **[paper]** These are "the σ̂_z = |0⟩⟨0| −
|1⟩⟨1| representations of the well known Kraus operators for the PD channel." (The
diagonal-basis forms Eq. 53–54 are `E1 = diag(√((1−e^{−2rt})/2), −√((1−e^{−2rt})/2))`,
`E2 = √((1+e^{−2rt})/2) Î` — the same channel.)

**Coherence decay / channel action (Eq. 56) — the M5 dephasing law [paper]:**

```
φ_τ(Î)   = Î,                                                            (56a)
φ_τ(σ̂_x) = e^{−2rt} σ̂_x,                                                 (56b)
φ_τ(σ̂_y) = e^{−2rt} σ̂_y,                                                 (56c)
φ_τ(σ̂_z) = σ̂_z.                                                          (56d)
```

**[paper]** and the full evolved state (Eq. 57), for initial `ρ = ½(Î + n⃗·σ⃗)`:

```
φ_τ(ρ̂) = ½[ Î + e^{−2rt} sin v cos u σ̂_x + e^{−2rt} sin v sin u σ̂_y + cos v σ̂_z ]   (57)
```

**[paper]** "Notice diagonalizability of the state eq.(57) for long times (t → ∞) in the
σ̂_z eigenbasis, which becomes the **'pointer basis'** for the decoherence process." **[twin]**
Eq. 56b/c is the M5 coherence-decay factor `e^{−2rt}`: the off-diagonal (x,y) Bloch
components decay, the z (population) component is preserved — identical structure to
Krantz Eq. 44's `e^{−Γ2 t}` on the off-diagonals with **no** population loss, i.e.
`Γφ = 2r` for the pure-dephasing piece (`Γ2 = Γ1/2 + Γφ`; with `Γ1 = 0` for pure PD,
`Γ2 = Γφ = 2r`).

**Conclusion (verbatim) [paper]:** the microscopic derivation "gives rise to the Kraus
operators that describe **exactly the same process as the standard Kraus** operators" —
i.e. the textbook AD/PD channels are recovered from a microscopic master equation, not
merely posited.

---

## Limitations / bounds for M4–M5 [paper] / [twin]

1. **[paper]** Single-qubit, Markovian master equations (Eqs. 13, 48) — no multi-qubit /
   correlated channel (M12 etc.) and no non-Markovian memory. The PD result assumes the
   secular/Markov limit "`lim_{ω→0} J(|ω|) = 0`."
2. **[paper]** Pure phase damping in Eq. 55 is **energy-conserving** (`φ_τ(σ_z) = σ_z`,
   Eq. 56d): it does **not** model T1. Realistic T2 = combination of AD (M4) + PD (M5);
   the additive `Γ2 = Γ1/2 + Γφ` is Krantz's relation, not derived jointly here.
3. **[twin]** The decay is strictly exponential (`e^{−2rt}`), so this M5 channel is the
   **Markovian** (white/Lorentzian) limit; the measured transmon dephasing is ≈1/f
   (Place: stretched exponent `n < 1`, PSD `A/f^{0.7}`) → Gaussian decay (Krantz Eq. 46),
   which this single-`r` Lindblad does not reproduce. M5 with one `r` is bounded to the
   Markovian regime.
4. **[twin]** `λ(t)` (M4) and `r` (M5) are left as channel parameters; their *values* are
   set by device data (Place/Krantz T1/T2), not by this paper.

---

## Trust [twin]

- **AD Kraus `{|0⟩⟨0|+√(1−λ)|1⟩⟨1|, √λ|0⟩⟨1|}` (Eq. 14), AD master eq. (Eq. 13):**
  certificate-grade for the M4 channel operator form.
- **PD master eq. `dρ/dt = r(σ_z ρ σ_z − ρ)` (Eq. 48), Kraus `{√(1−p/2)Î, √(p/2)σ_z}`,
  `p = 1−e^{−2rt}`, completeness `ΣÊ†Ê=Î`, coherence decay `e^{−2rt}` (Eqs. 48–57):**
  certificate-grade for the M5 channel operator form, microscopically derived.
- **Validity regime:** single-qubit Markovian only; bounded by 1/f / non-Markovian and
  by joint AD+PD composition — both carried as M5/M4 simplifications.
