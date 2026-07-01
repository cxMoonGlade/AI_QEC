# Full-text 精读 — Jin, Kamal, Sears et al. (Gustavsson & Oliver), "Thermal and Residual Excited-State Population in a 3D Transmon Qubit" (arXiv:1412.2772)

> **Provenance (2026-06-30): FULL-TEXT 精读.** Source:
> `outputs/papers/1412.2772.txt` (PyMuPDF text extraction, 11 pages). The
> extraction contains embedded NUL bytes; quotes below taken after `tr -d '\000'`.
> Figures are not pixel-extracted; figure references read from the extracted text /
> captions. Header: "arXiv:1412.2772v3 [quant-ph] 4 May 2015" (Phys. Rev. Lett.
> 114, 240501 (2015); no journal line in this extract). Note: the Maxwell-Boltzmann
> distribution is the paper's **Eq. (3)**, not "Eq. 1" — corrected below per the
> extraction.

Epistemic tags throughout: **[paper]** = stated/measured in the paper;
**[twin]** = our application or inference.

---

## Why load-bearing [twin]

This note is the primary anchor for QEC-Twin **M24 = residual / thermal excited-state
population** (the finite ground-state-preparation error: a qubit starts not perfectly in
`|g⟩` but with a small `P|e⟩`). The paper measures, in a 3D transmon:

- **A residual floor: "Below 35 mK, the excited-state population saturates at
  approximately 0.1%."** — the M24 magnitude.
- **An effective temperature: `Teff = 35 mK`.** — the M24 temperature.
- **Thermal (Maxwell-Boltzmann) behavior over 35–150 mK**, then deviation/saturation
  below 35 mK — the M24 temperature dependence and where it stops being thermal.

M24 needs a measured residual `P|e⟩` and a `Teff` rather than a guess; this paper supplies
both, plus the mechanism attribution (hot quasiparticles, cross-referenced to Wenner
1209.1674).

---

## Metadata [paper]

- **Authors:** X. Y. Jin, A. Kamal, A. P. Sears, T. Gudmundsen, D. Hover, J. Miloshi,
  R. Slattery, F. Yan, J. Yoder, T. P. Orlando, S. Gustavsson, W. D. Oliver (MIT RLE;
  MIT Lincoln Laboratory).
- **arXiv:** 1412.2772v3, quant-ph, 4 May 2015 (PRL 114, 240501).
- **Type:** experimental — systematic study of first-excited-state population vs bath
  temperature in a 3D transmon (cross-checked with a flux qubit).
- **Apparatus:** Leiden cryogen-free dilution refrigerator (CF-450), variable
  temperature; protocol adapted from Geerlings et al. [1].

---

## M24 — residual population, effective temperature, thermal range [paper]

**Abstract (verbatim, the three load-bearing claims):** "we observe the excited-state
population to be consistent with a **Maxwell-Boltzmann distribution**, i.e., a qubit in
thermal equilibrium with the refrigerator, over the temperature range **35-150 mK**.
**Below 35 mK, the excited-state population saturates at approximately 0.1%.** We
verified this result using a flux qubit with ten-times stronger coupling to its readout
resonator. We conclude that these qubits have **effective temperature Teff = 35 mK**.
Assuming Teff is due solely to hot quasiparticles, the inferred qubit lifetime is 108 µs
and in plausible agreement with the measured 80 µs."

**Saturation paragraph (verbatim) [paper]:** "For temperatures below 35 mK, P|e⟩
saturates to a residual value of approximately 0.1%, a factor 2.5 larger than the error
of our measurement. Ascribing this residual population entirely to non-equilibrium hot
quasiparticles, the upper limit of quasiparticle density is estimated to be **2.2 × 10⁻⁷
per Cooper pair**. The corresponding quasiparticle-induced decay time is calculated to be
**T1 = 108 µs**, in reasonable agreement with the independently measured decay time
**T1 = 80 µs**. This suggests that both the residual excited-state population and
relaxation times may be limited by quasiparticles for this device."

**Fig. 3 caption (verbatim) [paper]:** the P|e⟩ ratio (Eq. 1) is plotted "versus
temperature, 15-150 mK"; the data follow the Maxwell-Boltzmann estimate "over the range
35-150 mK", and "Below 35 mK (Fig. 3b), the ex[cited-state population] deviates from
thermal equilibrium, saturating" — "The data saturate to 0.1% at lower" temperatures
(caption: "residual population ~ 0.1%", "P|f⟩ = P|e⟩ = 0.1% (purple dashed line)").

**Prior-art context [paper]:** "the empirical excited-state population [corresponds] to
effective temperatures Teff = 50 − 130 mK [1, 31–33]" — i.e. published 3D-transmon Teff
historically sat in this band; this device's 35 mK floor is at the low (good) end.
**[twin]** Use as the broad M24 Teff range; 35 mK as the best-device anchor.

---

## The Maxwell-Boltzmann model [paper]

**Eq. (3) — the thermal population law (verbatim):**

```
P|i⟩ = (1/Z) g_i exp(−E_i / k_B T)                                      (3)
```

**[paper]** "Z = Σ_j g_j exp(−E_j/kBT) is the partition function, g_i is the degeneracy
of each energy level E_i, and k_B is the Boltzmann constant. In our analysis, we define
E|g⟩ ≡ 0, g_i = 1, and consider the lowest-four energy levels in the transmon." **[paper]**
"The equilibrium traces P^exp_|e⟩ and P|e⟩ are indistinguishable for T ≤ 50 mK." (For the
upper levels the paper notes "Eef/kB ≈ 235 mK, we take P|f⟩ → 0 in our analytic
treatment.") **[twin]** For M24, the two-level reduction of Eq. (3) gives
`P|e⟩ = e^{−ℏωq/kBT} / (1 + e^{−ℏωq/kBT})`; the paper's "lowest-four levels" is the
faithful transmon version.

**Measurement range [paper]:** "Excited-state population measurements were performed as a
function of temperature over the range T = 15 − 150 mK." Resolution: pushing "the
resolution from 1% to 0.1% would require a factor 100×" improvement (i.e. the 0.1% floor
is near the instrument's resolution edge — see Limitations).

---

## Limitations / bounds for M24 [paper] / [twin]

1. **[paper]** The 0.1% residual is "a factor 2.5 larger than the error of our
   measurement" — small margin above noise; the 0.1% is a *measured floor with limited
   SNR*, and finer resolution "would require a factor 100×."
2. **[paper]** The hot-quasiparticle attribution is conditional: "**Assuming** Teff is
   due solely to hot quasiparticles" / "Ascribing this residual population **entirely**
   to non-equilibrium hot quasiparticles" → the 2.2×10⁻⁷/Cooper-pair density is an
   **upper limit**, and the T1 = 108 µs (vs measured 80 µs) is "**plausible**"/"reasonable"
   agreement, not exact. **[twin]** M24's mechanism is consistent-with, not proven-to-be,
   quasiparticles here (Wenner 1209.1674 is the mechanism reference).
3. **[paper]** Device-specific: one 3D transmon, cross-checked on one flux qubit; prior
   art spans Teff = 50–130 mK, so 35 mK is **not universal** — M24 Teff should be treated
   as a device-dependent value/range, not a constant.
4. **[twin]** The thermal law (Eq. 3) holds only down to ~35 mK; below that the
   population is **non-thermal** (saturates), so an M24 that assumes pure Boltzmann
   `P|e⟩(T)` overpredicts how low the population goes as T → 0 — the floor must be imposed.

---

## Trust [twin]

- **Residual `P|e⟩ ≈ 0.1%` floor, `Teff = 35 mK`, Maxwell-Boltzmann over 35–150 mK
  (abstract; Fig. 3; Eq. 3):** certificate-grade measured values for the M24 magnitude,
  temperature, and thermal regime — with the SNR caveat (factor 2.5 above error).
- **Hot-quasiparticle attribution, 2.2×10⁻⁷/Cooper-pair, T1 = 108 µs inferred:**
  conditional/upper-limit (explicitly "assuming"/"plausible") — use as mechanism context,
  not as a fixed M24 parameter.
- **Prior-art `Teff = 50–130 mK` band:** citable range for M24 across devices.
