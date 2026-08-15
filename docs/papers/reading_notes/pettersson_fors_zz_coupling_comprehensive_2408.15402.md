# Full-text note (精读, model + magnitude sections) — Pettersson Fors, Fernández-Pendás, Kockum, "Comprehensive explanation of ZZ coupling in superconducting qubits" (arXiv:2408.15402v2, 2024)

> **Provenance (2026-06-26): 精读 of §I-II (the ZZ definition + the impact/magnitude estimates) + the
> abstract/conclusions + the near-zero-region results**; the Schrieffer-Wolff diagrammatic machinery (§V-VII)
> skimmed. PDF→txt `outputs/papers/2408.15402.txt` (45 pp). Chalmers (Kockum group), Dec 2024. The
> **FRONTIER (2024) ⑤a ZZ-crosstalk magnitude + form** source — fetched in the 2026-06-26 crosstalk
> frontier-literature sweep (the user's "why are the crosstalk papers all 5+ years old?" correction). UPDATES
> the ⑤a grounding `harper_nonclifford_crosstalk_surface_2605.29514` (which I used for J_ZZ·t_g≈1e-3).

## Why load-bearing [ours]
The current, comprehensive (2024) treatment of static ZZ crosstalk for the **two fixed-frequency transmons +
flux-tunable transmon coupler** architecture — the modern tunable-coupler standard. Confirms the ⑤a teacher's
**form is exactly right** (cross-Kerr / `exp(-iφ Z⊗Z)`) but gives the **modern magnitude** that supersedes the
fixed-coupling-era bracket I was using.

## The model [paper] — confirms the ⑤a form EXACTLY
- **ZZ = cross-Kerr (Eq.3):** `ζ = E'_11 − E'_10 − E'_01 + E'_00` — the discrepancy of the dressed |11⟩ energy,
  `∝ σz⊗σz`. "called the ZZ coupling, or cross-Kerr term". An always-on conditional energy shift; for a
  time-dependent H it is the instantaneous `ζ = ζ(t)`.
- **The unitary (Eq.6):** in the frame rotating with the dressed single-qubit frequencies (single-qubit phases
  removed by virtual-Z), `U_ζ = diag(1,1,1, e^{−iφ_ζ})`, with **`φ_ζ(t_g) = ∫_0^{t_g} ζ(t')dt' ≡ ζ̄·t_g`**
  (ζ̄ = time-averaged ZZ). This is the |11⟩-only conditional phase = gauge-equivalent (up to single-qubit Z) to
  our `zz_coupling_kraus(φ) = diag(e^{−iφ},e^{iφ},e^{iφ},e^{−iφ})` — SAME physics, **φ = ζ̄·t_g**.
- **Fidelity impact (Eq.7):** an iSWAP under ZZ → `F = 1 − (3/10)(1−cos(ζ̄ t_g)) ≈ 1 − (3/20)(ζ̄ t_g)² `
  (weak-ZZ). The decode-relevant footprint of residual ZZ is this coherent fidelity loss / the twirl-
  underestimate (cf. Bravyi `correcting_coherent_errors_surface_1710.02270`).

## Key numbers [paper] — the magnitude thresholds (the load-bearing update)
- **Coherence-limited threshold (Eq.9):** ZZ matches the relaxation error when `ζ̄ = √(16/(3 t_g T1))`. For
  current tech (t_g=100 ns, T1=100 µs): **`ζ̄ < 2π × 100 kHz`** is needed for relaxation (not ZZ) to dominate.
  ⇒ residual ZZ only "matters" above ~100 kHz.
- **CZ-gate (strong ZZ):** a 100 ns CZ needs `ζ̄ = 2π × 5 MHz`. So a tunable coupler must span **100 kHz
  (off, coherence-limited) ↔ 5 MHz (on, CZ)**.
- **Three near-zero-ZZ parameter regions** exist for the two-transmon + tunable-coupler system, "all accessible
  with current technology without major redesigns" (the abstract's headline). So **modern residual idle ZZ is
  engineered to near-zero**.
- **Modern measured residual (from the 2026-06-26 sweep, sibling sources):** tunable couplers reach residual ZZ
  **< 1 kHz**; FTF (fluxonium-transmon-fluxonium) **< 3 kHz across the full coupler bias, < 100 Hz at the
  coupler-off point** ([arXiv:2505.22276] Leek; the FTF refs). I.e. ~100–1000× below the 100 kHz threshold.

## Limitations / what does NOT apply [paper→ours]
- A THEORY paper (mechanisms + near-zero parameter regions via Schrieffer-Wolff diagrammatics + a state-
  assignment algorithm); it does not report a single device's measured residual number — the modern measured
  residual (<1 kHz) comes from the sibling experimental sweep sources. The two together fix the bracket.
- The cross-Kerr ζ has a "significant additional contribution from higher-excited states" (the |2⟩-mediated
  level repulsion) — our ⑤a `exp(-iφ ZZ)` is the effective 2-level projection (the higher-level contribution is
  folded into ζ̄). Faithful for the conditional-phase footprint; the |2⟩-leakage path is a separate axis (④).

## Relevance to the teacher (⑤a ZZ crosstalk) [ours] — the MAGNITUDE UPDATE
- **FORM: VALID — keep it.** The ⑤a `exp(-iφ Z⊗Z)` / cross-Kerr is exactly Eq.3/Eq.6, with **φ = ζ̄·t_g**. No
  form change. The QuTiP static-ZZ deriver (`build_static_zz_channel`, ζ from the dispersive Duffing pair) is
  the right first-principles object; its `phi_analytic = ζ·t_g/4` knob maps directly.
- **MAGNITUDE: STALE — update the bracket.** My current ⑤a `φ ∈ [1e-3 .. 0.15]` corresponds (t_g≈25 ns) to
  `ζ ≈ 6 kHz .. 1 MHz`:
  - the low end (φ=1e-3 → ζ≈6 kHz) is already ~6× ABOVE the modern <1 kHz residual;
  - the high end (φ=0.05–0.15 → ζ≈300 kHz–1 MHz) is **STRONG ZZ / near-CZ regime, NOT residual crosstalk** —
    it's between the 100 kHz coherence-limited threshold and the 5 MHz CZ value. Retire it as the residual
    default (keep only as a deliberately-amplified / fixed-coupling-era visible probe, clearly flagged).
  - **UPDATED modern-residual bracket:** `ζ ≈ 100 Hz .. 1 kHz` ⇒ **`φ ≈ 1.6e-5 .. 1.6e-4`** (t_g≈25 ns;
    coupler-off ↔ coupler-on residual), with the **100 kHz coherence-limited threshold (φ ≈ 1.6e-2) as the
    "where ZZ starts to matter" upper edge**. So the realistic ⑤a residual is ~10–1000× SMALLER than my old
    bracket — the clearest "magnitude stale" of the three crosstalk forms.
- **Epistemic class for the prereg:** (b) prediction band — the ⑤a residual-ZZ magnitude bracketed
  `φ ∈ [1.6e-5, 1.6e-2]` (modern tunable-coupler residual → coherence-limited edge), SWEPT, grounded in Eq.9 +
  the modern measured <1 kHz residual; the old 0.05–0.15 retired to a flagged "amplified/fixed-coupling" arm.
  The form + the coherence-limited threshold (Eq.9) = (a)-grade (a derived identity).

## Trust [ours]
精读 of the ZZ definition (Eq.3), the conditional-phase unitary (Eq.6, φ_ζ=ζ̄ t_g), the fidelity-impact (Eq.7),
and the coherence-limited threshold (Eq.9, ζ̄<2π·100 kHz) + the CZ value (5 MHz) + the three-near-zero-region
headline — all read directly from §II. The Schrieffer-Wolff diagrammatic mechanism derivation (§V-VII) skimmed
(not load-bearing for the teacher — we use the QuTiP-derived ζ). The modern measured residual <1 kHz is from the
sibling sweep sources ([arXiv:2505.22276] + the FTF refs), cross-checked against this paper's near-zero-region
claim. The "φ bracket → 1.6e-5..1.6e-4" is [ours] arithmetic from φ=ζ̄·t_g at the modern ζ + t_g≈25 ns.
