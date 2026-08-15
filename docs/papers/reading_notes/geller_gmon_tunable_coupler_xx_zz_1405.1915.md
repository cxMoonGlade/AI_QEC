# Full-text note (精读) — Geller, Donate, Chen, Neill, Roushan & Martinis, "Tunable coupler for superconducting Xmon qubits: Perturbative nonlinear model" (arXiv:1405.1915)

> **Provenance (2026-06-29): FULL-TEXT read (精读).** PDF `outputs/papers/1405.1915.pdf` → txt
> `outputs/papers/1405.1915.txt` (PyMuPDF, 10 pp). All §/Eq/Fig refs from that text; figures not
> pixel-extracted (Fig.3/6/8/9 numbers = captions + axis labels). v1, May 2014 (UGA + UCSB/Martinis;
> the "gmon" tunable coupler that became the Google Xmon two-qubit architecture). **The DIRECT theory
> source where the two-qubit transverse interaction IS a *pure* σx⊗σx (X⊗X) term** — written explicitly
> as `δH = g σx₁σx₂`, with a separately-derived induced `δH = J σz₁σz₂`. This is the complement to the
> cross-resonance note (`magesan_gambetta_cross_resonance_pauli_tensor_1804.04073`, where XX is ABSENT and
> the entangler is ZX): together they fix WHEN a pure X⊗X arises vs when the interaction is ZX/ZZ-dominated.
> Sibling 2q-coupling notes: `foxen_fsim_twoqubit_gateset_2001.08343` (fSim = XX+YY swap + ZZ on the
> gmon platform), `pettersson_fors_zz_coupling_comprehensive_2408.15402` (static ZZ). For the M22 =
> `coherent_cxx_parasitic_coupling` (H = J_xx · X⊗X) dossier: THIS is the paper that licenses X⊗X.

## Why load-bearing [ours]
For M22 the question is "is a *pure* X⊗X generator physical, and where does it come from?" The CR note
answers "not from cross-resonance — that's ZX." THIS note answers the positive side: in a **capacitive/
inductive tunable coupler** (the gmon design: two Xmon transmons coupled through a flux-tunable Josephson
junction acting as a current divider), the leading qubit-qubit interaction projected into the
computational subspace is **exactly `g σx⊗σx`** (Eq.57), with magnitude set by the tunable coupler flux,
*plus* a small **induced `J σz⊗σz`** (Eq.82). It also makes explicit, through the projection algebra
(Eq.55-56), *why* the transverse term is pure XX and not the XX+YY exchange of an iSWAP — because the
coupling is a **position–position `ϕ₁ϕ₂` interaction**, not a `(a†b + ab†)` photon-exchange. That is the
honest physical nuance the dossier needs.

## The circuit / starting model [paper]
Two Xmon transmons, each a flux-biased Josephson junction (inductance L_j) shunted by capacitor C_i and
linear inductance L_0i, coupled through a shared flux-tunable junction (L_T, tuned by external flux Φ_ext:
`L_eff = L_T/cos δ`, Eq.1). The coupler acts as a **tunable current divider** — coupling vanishes at
δ mod 2π = π/2, 3π/2 (Eq.5). Full circuit Lagrangian Eq.17-18; Hamiltonian Eq.32 (the ξ_i are "massless"
nodes, adiabatically eliminated). Harmonic-approximation interaction (Eq.10/53):
`δH = (Φ_0/2π)² Γ_11 ϕ_1 ϕ_2` — a **flux-flux (position-position) coupling** with
`Γ_11 = −M/(K L_q²)`, mutual inductance `M = L_0²/(L_eff + 2L_0)` (Eq.9, Eq.49 in the nonlinear model).

## Method (deep) [paper]
Three layers, all checked against **exact numerical diagonalization** of the full nonlinear circuit (Fig.6):
1. **Weak-coupling classical** (Sec.I): coupling `g = Γ_11 L_q ω_q / 2` (Eq.15), from diagonalizing the
   quadratic form — the half-splitting between symmetric/antisymmetric eigenstates.
2. **Quantum projection into the qubit subspace** (Sec.III A): each Josephson phase operator projects as
   **(Eq.55)** `ϕ → ϕ_01 σx − ((ϕ_11−ϕ_00)/2) σz + ((ϕ_00+ϕ_11)/2) I`, and **by symmetry ϕ_00 = ϕ_11 = 0**
   so `ϕ → ϕ_01 σx` with `ϕ_01 = (2π/Φ_0)√(ℏ L_q ω_q / 2)` (Eq.56). Substituting into the `ϕ_1 ϕ_2`
   interaction (Eq.53) gives the pure transverse term (see THE EQUATIONS).
3. **Perturbative nonlinearity** (Sec.III B + IV): expand the cosine potentials to quartic order
   (Eq.35, tracked by λ = qubit nonlinearity, λ′ = coupler nonlinearity), giving anharmonic corrections
   (Eq.69 with coefficients Γ_04…Γ_22, Eq.70-74) that (a) suppress the transverse XX, (b) induce ZZ.

## The EXACT interaction as a Pauli tensor [paper] — THE LOAD-BEARING EQUATIONS

**Transverse (pure XX), Eq.57:**
```
δH = g · σx₁ σx₂          with   g = ℏ Γ_11 √(L_q1 L_q2) √(ω_q1 ω_q2) / 2     (Eq.58)
```
i.e. the interaction is **σx⊗σx ONLY** in the linearized projection — no σy⊗σy, no σz⊗σx, no IX. The
nonlinear correction (Eq.78) keeps the *same* σx⊗σx form and just rescales it:
`g_tot = ζ g`, `ζ = 1 + δg/g ≈ 1 − π²(ℏω_q/(Φ_0²/2L_j)) = 0.852` (Eq.80/81) — qubit anharmonicity
**suppresses the transverse XX by ~15%**. (Eq.77: `δg = (3/2)Γ_13(ℏω_q L_q/(Φ_0/2π))²`.)

**Induced diagonal (ZZ), Eq.82:**
```
δH = J · σz₁ σz₂          with    J ≈ g²/η          (Eq.88, dominant |2⟩-repulsion mechanism)
```
where `η` = qubit anharmonicity (Eq.86). J comes from `|11⟩` being pushed by `|02⟩` and `|20⟩`
(second-order, Eq.87: `δE_11 ≈ 2(√2 g)²/η`); computed exactly from the eigenenergies as
`J = [E_11 − (E_+ + E_−) + E_00]/4` (Eq.83). A subdominant Γ_22 contribution `J = Γ_22((2π/Φ_0)²ℏω_q L_q/2)²`
(Eq.90) is much smaller. **J is always positive from the |2⟩-repulsion** and zeros where g zeros.

So the full computational-subspace interaction tensor of the gmon coupler is **{XX (dominant, tunable), ZZ
(induced, ∝ g²/η)}** — and notably **NO YY** in the leading projection.

## Why pure XX and not XX+YY exchange [paper → ours]
[paper] The interaction enters as `ϕ_1 ϕ_2` (Eq.53), a product of two *position* (flux) operators, and each
`ϕ_i` projects to `ϕ_01 σx` only (Eq.55, because ϕ_00=ϕ_11=0 by parity of the harmonic well). A *position*
operator `ϕ ∝ (a + a†)` projected this way gives `σx`; the cross term `ϕ_1 ϕ_2 ∝ (a_1+a_1†)(a_2+a_2†)`
contains both the exchange `a_1†a_2 + a_1 a_2†` (→ XX+YY) *and* the co-rotating `a_1†a_2† + a_1 a_2`
(→ XX−YY) pieces; **the gmon coupler keeps both (no RWA that would drop the counter-rotating piece), and the
sum is the bare position-position σx⊗σx**, i.e. `(a_1+a_1†)(a_2+a_2†) → σx⊗σx` under the parity projection.
[ours] CONTRAST: an iSWAP/fSim swap interaction is `g(a_1†a_2 + a_1 a_2†)` (number-conserving exchange) →
`(g/2)(σx⊗σx + σy⊗σy)` — the **XX+YY** transverse block. So:
- **Pure XX** ⇐ a *static, energy-non-conserving* position–position (capacitive/inductive) coupling kept
  with its counter-rotating part (the gmon coupler at the always-on / idle bias, this paper).
- **XX+YY (exchange)** ⇐ a *resonant* number-conserving swap (iSWAP/fSim θ-rotation, Foxen 2001.08343).
- **ZX** ⇐ a *driven* cross-resonance interaction (Magesan 1804.04073).
- **ZZ** ⇐ the diagonal byproduct of any of these via the `|2⟩`/higher-level repulsion (here Eq.88).

## Findings + numbers [paper]
- Example parameters (Table I): C = 91 fF, L_j = 8.6 nH, L_0 = 200 pH, L_T = 1.3 nH; qubit frequency
  ω_q/2π ≈ 5.62 GHz (varies ~22 MHz with flux, Fig.7); anharmonicity **η/2π ≈ 213 MHz**.
- **Transverse XX coupling g/2π tunable from ≈ −10 to +15 MHz** across the flux range (Fig.3, Fig.8),
  passing through **exactly zero** at φ_ext mod 2π = 0.598π, 1.402π (Eq.16) — fully tunable, including OFF.
- **Nonlinear suppression of XX ≈ 15%** (ζ ≈ 0.852, Eq.81); coupler-junction nonlinearity (λ′) negligible.
- **Induced ZZ ≈ g²/η ≲ ~1 MHz** at the strongest coupling (Fig.9, J approx vs exact-diag), down to the
  kHz scale near the minima (Fig.10; exact diag dips slightly negative, ≈ −110 Hz, but that is at the
  numerical-accuracy floor). ZZ zeros where XX zeros (in the dominant mechanism).

## Limitations [paper]
- Perturbative to first order in the qubit/coupler nonlinearity (λ, λ′) and assumes the hierarchy
  L_0 ≪ L_j ≪ L_T (Eq.59) for the closed forms; the exact-diagonalization curves are the ground truth.
- Resonantly-tuned identical qubits for the ZZ derivation (Sec.IV); the YY term is dropped at the leading
  parity projection — a full higher-order treatment could in principle generate small XZ/YY corrections,
  not computed here.
- It is a *circuit/Hamiltonian* paper (no gate fidelities, no tomography of an operated gate); the operated
  gmon two-qubit gate (fSim) tomography is Foxen 2001.08343.

## Relevance to qec_twin [ours]
- **DIRECT support that a *pure* X⊗X coherent two-qubit term is physical** — it is exactly the gmon/Xmon
  tunable-coupler transverse interaction `δH = g σx⊗σx` (Eq.57), the very platform family the project's
  real-Google rung (R2-lite, XZZX/Willow Xmon transmons) lives on. This is the citation that licenses the
  M22 = `coherent_cxx_parasitic_coupling` generator H = J_xx · X⊗X.
- **But with the honest bound:** (i) on this platform the *always-on* parasitic term is a **combined XX +
  induced ZZ** (Eq.82, J ≈ g²/η), so a faithful M22 teacher that turns on XX should expect a *correlated*
  ZZ of order g²/η ≈ (a few MHz)²/213 MHz ~ tens-of-kHz unless the coupler is engineered ZZ-free; isolating
  XX with ZERO ZZ is an *idealization*, defensible only as a declared, bounded simplification. (ii) The
  leading projection has **no YY** — so X⊗X (not the XX+YY exchange) is the right pure-transverse generator
  for an *idle/always-on* coupler; the XX+YY exchange belongs to the *operated* iSWAP/fSim gate (Foxen).
- **What to REUSE:** g/2π tunable −10…+15 MHz and induced ZZ ≈ g²/η with η/2π ≈ 213 MHz are realistic
  magnitudes to anchor the M22 XX knob and its physically-correlated ZZ; the projection algebra (Eq.55-56)
  is the exact derivation of "position-position coupling → σx⊗σx" usable to *justify* the X⊗X generator
  form in the pre-registration.
- **CORRECTION to a prior assumption:** any framing that treats X⊗X as a *generic* coherent 2q crosstalk
  applicable across platforms is too loose — X⊗X is specifically the **transverse capacitive/inductive
  (gmon-coupler) always-on** form. The driven-CR family is ZX (Magesan), the resonant-swap family is XX+YY
  (Foxen). The dossier must source X⊗X to THIS paper, not to cross-resonance.

## How to use / trust + open questions [ours]
- **Trust:** full-text read; the load-bearing equations (Eq.55-58 for XX, Eq.82/88 for ZZ, Eq.80/81 for the
  ~15% suppression) transcribed from text, validated by the paper against exact diagonalization (Fig.6, Fig.9).
  The "pure XX, no YY in leading projection" statement is the paper's explicit projection result —
  certificate-grade as a statement about the gmon coupler's leading-order interaction.
- **Classification: DIRECT** — writes the two-qubit interaction explicitly as Pauli⊗Pauli terms
  (`g σx⊗σx` + `J σz⊗σz`) with the transverse XX block *present and quantified*. This is the positive-XX
  counterpart to the CR note's negative-XX result.
- **Open question for the dossier:** whether to make the M22 teacher emit XX *with* its correlated ZZ
  (g²/η) — the faithful choice on the gmon platform — or to declare a bounded XX-only simplification. This
  note supplies the bound (ZZ ~ tens-of-kHz at a few-MHz XX) needed to make that declaration honest.
