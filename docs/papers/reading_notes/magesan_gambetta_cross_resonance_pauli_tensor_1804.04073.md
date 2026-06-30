# Full-text note (精读) — Magesan & Gambetta, "Effective Hamiltonian models of the cross-resonance gate" (arXiv:1804.04073)

> **Provenance (2026-06-29): FULL-TEXT read (精读).** PDF `outputs/papers/1804.04073.pdf` → txt
> `outputs/papers/1804.04073.txt` (PyMuPDF, 16 pp). All §/Eq/Fig refs from that text; figures not
> pixel-extracted (Fig.1/3/6 numbers = captions + axis labels in text). Published Phys. Rev. A 101,
> 052308 (2020). IBM T.J. Watson. **The canonical theory source for the 2-qubit cross-resonance (CR)
> effective Hamiltonian written as the full Pauli⊗Pauli coefficient tensor** — the DIRECT evidence
> for the M22 = `coherent_cxx_parasitic_coupling` (H = J_xx · X⊗X) dossier, and — critically — the
> source that shows the CR interaction tensor is **ZX-dominated with NO XX/XY/XZ control-side block**.
> Sibling 2q-coupling notes: `foxen_fsim_twoqubit_gateset_2001.08343` (fSim XX+YY swap + ZZ),
> `pettersson_fors_zz_coupling_comprehensive_2408.15402` (static ZZ), `sarovar_detecting_crosstalk_errors_1908.09855`
> (crosstalk Hamiltonian inference), `harper_nonclifford_crosstalk_surface_2605.29514` (ZZ crosstalk),
> and the complementary **transverse-XX** note `geller_gmon_tunable_coupler_xx_zz_1405.1915` (where pure XX *does* arise).

## Why load-bearing [ours]
This is the single most-cited theory paper that writes the **two-qubit effective Hamiltonian of a
real superconducting entangling gate (the IBM fixed-frequency-transmon CR gate) as an explicit sum
of Pauli⊗Pauli coefficients** `Σ a_{αβ} σ_α⊗σ_β`, computed two ways (perturbative canonical transform
+ exact "principle of least action" block-diagonalization), benchmarked against the experimental
Hamiltonian-tomography numbers of Sheldon et al. (Ref.[6], Phys. Rev. A 93, 060302). For the M22
dossier it answers the load-bearing question directly: **in the CR family the transverse / control-X
block — XX, XY, XZ, YX, YY, YZ — is identically ABSENT; the only non-zero terms are A⊗B with
A∈{I,Z}, B∈{I,X,Y,Z}** (and even there IY=ZY=0 absent classical crosstalk). So a *pure X⊗X*
generator is NOT what the CR effective Hamiltonian produces — it produces ZX (the entangler) + ZI
(Stark) + IX + IZ + ZZ. This is the honest physics nuance the dossier needs: the CR literature does
NOT support "XX as an isolated interaction"; XX lives in a *different* coupling family (see the gmon note).

## The starting Hamiltonian [paper]
Two transmons (Duffing oscillators) dispersively coupled to a bus resonator (Eq.2.1):
`Hsys = Σ_j [ ω̄_j b†_j b_j + (δ_j/2) b†_j b_j (b†_j b_j − 1) ] + ω_r c†c + Σ_j g_j (b†_j c + b_j c†)`.
After adiabatic elimination of the bus (project onto 0-photon subspace), the effective two-transmon
Hamiltonian (Eq.2.12) is `H^(0)_sys = Σ_j [ ω̃_j b†_j b_j + (δ_j/2) b†_j b_j(b†_j b_j − 1) ] + J(b†_1 b_2 + b_1 b†_2)`,
with **exchange coupling** `J = g_1 g_2 (ω̄_1 + ω̄_2 − 2ω_r) / [2(ω̄_1 − ω_r)(ω̄_2 − ω_r)]` (Eq.2.13).
The CR drive is a single X-quadrature tone on the **control** qubit (qubit 1) at the **target** frequency:
`Ω(t) cos(ω_d t)(b†_1 + b_1)` (Eq.2.14/2.15).

## Method (deep) [paper]
Two effective-Hamiltonian constructions (Appendix A):
- **Principle of least action** (Sec.A 1, exact): find the block-diagonal Hermitian `H_eff` closest to the
  true `H` (same spectrum, support only on the chosen subspaces) by the least-action unitary
  `T = X X†_BD (X_BD X†_BD)^{−1/2}`, `argmin_F ‖T − I‖₂`. Valid at strong drive; analytic only in simple cases.
  Figure of merit `I(H_eff) = tr(X_BD X†_BD)/dim(H) ∈ [0,1]` measures how well `H_eff` captures `H` (deviates
  from 1 near the perturbative poles).
- **Perturbative canonical transform** (Sec.A 2, weak drive): `H_eff = U†HU = Σ_m λ^m H^(m)`, with
  `H^(m) = i[S_m, H_0] + H^(m)_x`, block-diagonality enforced order-by-order via `S_m` (order parameter λ = Ω).
  Gives closed-form Pauli coefficients in the weak-drive limit.

The dressing of higher levels (Eq.4.1-4.5) induces a static `ZZ` already at the drive-off level:
`H̃^(0)_sys = ω_1 Z⊗I/2 + ω_2 I⊗Z/2 + ξ ZZ/2`, with `ξ = −J²(δ_1+δ_2)/[(Δ+δ_1)(δ_2−Δ)]` (Eq.4.5),
Δ = ω̃_1 − ω̃_2. **"The presence of higher levels has produced an effective ZZ interaction."**

## The EXACT effective Hamiltonian as a Pauli tensor [paper] — THE LOAD-BEARING EQUATIONS

**Ideal-qubit limit (infinite anharmonicity), Eq.3.16:**
```
H_CR = (Δ − √(Δ²+Ω²)) · Z⊗I/2  −  ( JΩ/√(Δ²+Ω²) ) · ZX/2
```
i.e. only TWO terms: a control-qubit Stark shift `ZI` (Eq.3.15) and the entangling `ZX` (Eq.3.14,
`tr(H_CR · ZX/2) = −JΩ/√(Δ²+Ω²)`). **No XX. No IX. No YY. No XY.** Pauli operators are scaled by 1/2
(by the system-Hamiltonian convention; 1/2^{n−1} for n qubits).

**Realistic transmon (higher levels), full Pauli-coefficient tensor — Appendix C (verbatim, of the form
A⊗B, A∈{I,Z}, B∈{I,X,Y,Z}):**
```
IX/2 coeff = −JΩ/(Δ+δ_1) + ΔδJΩ³/[(Δ+δ_1)³(2Δ+δ_1)(2Δ+3δ_1)]      (large, finite-anharmonicity term)
IY/2 coeff = 0
IZ/2 coeff = (J²Ω²/2)·[ … ]                                          (small, see Eq. App.C)
ZI/2 coeff = −δ_1Ω²/[2Δ(δ_1+Δ)] + (J²Ω²/…)·[ … ]                    (large Stark shift; diverges, Fig.2)
ZX/2 coeff = −(JΩ/Δ)(δ_1/(δ_1+Δ)) + JΩ³δ_1²(3δ_1³+11δ_1²Δ+15δ_1Δ²+9Δ³)/[2Δ³(δ_1+Δ)³(δ_1+2Δ)(3δ_1+2Δ)]
ZY/2 coeff = 0
ZZ/2 coeff = (J²/2)·[ … ]                                            (static-ZZ offset + drive dependence)
```
(Eq.4.25/4.26 give the ZX 1st/3rd-order pieces; full set in Appendix C, page 16 of the txt.) The
**linear ZX** is `ZX/2|linear = −(JΩ/Δ)(δ_1/(δ_1+Δ))` (Eq.4.26). **`H_CR = Heff + (ω_d − ω_d1) F(b†b⊗I)F†`** (Eq.4.23).

**The decisive structural fact (Sec.VI Discussion, verbatim):** the realistic CR model predicts
"non-zero Pauli coefficients of the form A⊗B with A∈{I,Z}, B∈{I,X,Z}". So the **control-side
operator is restricted to {I,Z}** — there is no `X_control` (no XX/XY/XZ), and on the target side only
{I,X,Z} survive in the bare model (IY, ZY = 0). The IX term is **produced by finite anharmonicity +
higher levels** and "is not present in the pure qubit model" (Sec.IV B); `ZX` and `IX` have the largest
magnitude (Fig.1, Fig.3).

## The OBSERVABLE / metric [paper]
**Hamiltonian tomography (HT) / "partial Hamiltonian tomography"** (the scheme of Sheldon et al. Ref.[6])
extracts each Pauli coefficient `a_{αβ}` of the block-diagonal CR Hamiltonian as a *rate* (MHz) vs drive
amplitude Ω. The plots (Fig.1, Fig.2 for ZI, Fig.3 for the small IY/IZ/ZY/ZZ, Fig.6 with crosstalk) are
**coefficient (MHz) vs drive power (MHz)** sweeps. The model→experiment metric is agreement of these
coefficient curves (theory vs Ref.[6] Fig.2b). The figure of merit `I(H_eff)` (Sec.A 1) flags where the
effective-Hamiltonian description itself fails (near the poles Δ = 0, −δ_1/2, −δ_1, −3δ_1/2).

## Findings + numbers [paper]
- Device parameters from Ref.[6] (Sec.IV B): ω_1/2π = 5.114 GHz, ω_2/2π = 4.914 GHz, δ_1=δ_2/2π = −0.330 GHz,
  g_1/2π = 0.098 GHz, g_2/2π = 0.083 GHz, ω_r/2π = 6.31 GHz, static-ZZ ξ/2π = **277 kHz**, exchange **J/2π = 3.8 MHz**.
- Largest terms: **ZX and IX** (a few MHz at tens-of-MHz drive); **ZI** (Stark) is the largest and "diverges
  quickly since the control qubit is driven far off-resonance" (Fig.2). **IZ and ZZ barely move** with drive;
  the ZZ offset = the static 277 kHz.
- **IY = 0 in the model** (Appendix C, exact), but Ref.[6] *measured* a large IY — Magesan & Gambetta
  attribute it to **classical crosstalk** (a phase-shifted drive A·Ω cos(ω_d t + φ_t) leaking onto the target,
  Eq.5.1); with A = 0.071, φ_c = π, φ_t = −0.62 (Eq.5.2) the model reproduces Ref.[6] Fig.2b (Fig.6). So
  **IY is an artifact of crosstalk, not an intrinsic CR Hamiltonian term.**
- Past detuning Δ = −δ_1 the **ZX rate collapses to ~0** (Fig.5): two transmons detuned beyond their
  anharmonicity "look like harmonic oscillators … entanglement can not be created between two harmonic
  oscillators."

## Limitations [paper]
- Perturbative expressions valid only `Ω/Δ ≪ 1` and away from the poles Δ = 0, −δ_1/2, −δ_1, −3δ_1/2;
  the principle-of-least-action method extends to strong drive but has no general closed form.
- Single-CR-drive model (control only) — the intrinsic tensor has IY = ZY = 0; *any* observed
  IY/ZY is attributed to classical crosstalk, whose microscopic channel is left as future work.
- Fixed-frequency-transmon CR architecture specifically (IBM); does not model tunable-coupler / iSWAP-family
  interactions (where transverse XX/YY *does* appear — see the gmon note).

## Relevance to qec_twin [ours]
- **DIRECT support that the CR effective Hamiltonian is a full Pauli tensor with the transverse/XX block
  EXPLICITLY ABSENT.** The interaction term that entangles is `ZX` (control-Z ⊗ target-X), with `ZZ`, `IX`,
  `ZI`, `IZ` accompanying it. This is the honest counter-evidence to naming the M22 mechanism a generic
  "parasitic XX": in the CR family the parasitic/always-on structure is **ZZ + ZX**, not XX.
- **CORRECTION this paper forces on M22's framing:** treating `X⊗X` as the canonical coherent 2q parasitic
  generator is **not defensible from the CR literature** — the CR tensor has no X_control term at all. A pure
  X⊗X term is a *different* coupling family (capacitive/transverse position-position coupling and exchange,
  e.g. the gmon coupler, fSim swap). For the carrier's M22 to be honest, X⊗X must be cited to the
  transverse-coupling family (gmon 1405.1915 / fSim 2001.08343), and the CR-family parasitic term must be
  labeled ZX/ZZ, NOT XX. The carrier already separates these (M27/M20 ZZ etc.); this note pins the boundary.
- **What to REUSE:** the explicit per-coefficient closed forms (Appendix C) are a ready ground-truth for any
  "fit a 2-qubit interaction tensor and check which Pauli terms are present" identifiability probe — they let
  us assert (exact-class) that a CR teacher's tensor has zero XX/XY/XZ/YX/YY/YZ and a ZX:ZZ:IX hierarchy.
- The static-ZZ value (ξ/2π = 277 kHz) and the exchange J/2π = 3.8 MHz are realistic magnitudes to anchor a
  teacher's ZZ/exchange knobs (cross-check vs `pettersson_fors_zz_coupling_comprehensive_2408.15402`).

## How to use / trust + open questions [ours]
- **Trust:** full-text read; the load-bearing equations (Eq.3.16, Eq.4.2, Eq.4.25/4.26, Appendix C) are
  transcribed from the text, not figures. The Pauli-tensor *structure* claim (A⊗B, A∈{I,Z}) is the paper's
  explicit Discussion statement + the exact Appendix-C zeros (IY=ZY=0) — certificate-grade as a statement
  about THIS model.
- **Classification: DIRECT** — writes H as an explicit sum of Pauli⊗Pauli coefficients; the XX/transverse
  block is "visible" precisely by being provably ABSENT (a negative but explicit result), and the full
  {IX, IY, IZ, ZI, ZX, ZY, ZZ} set is given in closed form.
- **Open question for the dossier:** the carrier's X⊗X must be sourced from the transverse-coupling family,
  not CR. Use this note to *bound* the claim: "in the CR effective Hamiltonian, XX is identically zero; a
  pure XX term arises only in capacitive/inductive transverse couplings (gmon) where the interaction is
  position-position ϕ₁ϕ₂ → σx⊗σx, not control-driven."
