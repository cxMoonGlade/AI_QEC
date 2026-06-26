# Full-text note (精读, abstract + intro + model/magnitude) — Song et al. (Wallraff group, ETH), "Microwave Crosstalk in Planar Superconducting Quantum Devices" (arXiv:2606.02440, 2026) + Seif/IQM, "Mitigating crosstalk errors for simultaneous single-qubit gates" (arXiv:2603.11018, 2026)

> **Provenance (2026-06-26): 精读 of Song 2606.02440 §abstract+intro+model** (via PDF→txt
> `outputs/papers/2606.02440.txt`, 16 pp, + a WebFetch of the HTML for the X-ratio numbers) + the IQM
> 2603.11018 result (search + my prior `project-digital-twin-noise-landscape` note). ETH Zurich (Wallraff) Jun
> 2026; IQM Mar 2026. The **FRONTIER (2026) DRIVE/microwave-crosstalk model + magnitude** — from the 2026-06-26
> crosstalk frontier-literature sweep (the user's "why are the crosstalk papers all 5+ years old?"). UPDATES the
> drive grounding `sarovar_detecting_crosstalk_errors_1908.09855` (2019).

## Why load-bearing [ours]
The current (2026) QUANTITATIVE physical model of microwave/drive crosstalk for planar devices with crossovers —
the first model that predicts the crosstalk at a qubit from the device GEOMETRY (prior work was PCB/wire-bond
package models or characterization-only). Updates the SOURCE understanding behind the drive-spillover teacher.

## The model + numbers [paper, Song 2606.02440]
- **Crosstalk metric:** the **cross-drive ratio `X_{k,j} = Γ_{k,j}/Γ_{j,j}`** = the fraction of drive POWER the
  unintended qubit k receives relative to the target j (a power ratio; amplitude fraction = √X).
- **Measured magnitudes:** proximity-induced `X ≈ −10 to −40 dB` (distance d ∈ 550–1165 µm); crossover-induced
  `X ≈ −9 to +2 dB` (air-bridge/coupler geometry); package-mediated (shorted pad at 5460 µm) `−30 to −40 dB`.
  ⇒ amplitude spillover fraction **c = √X ≈ 0.01 (−40 dB) to 0.1 (−20 dB)** — typical drive crosstalk.
- **TWO dominating mechanisms** (replacing the single-mechanism / pure-spectral-spillover picture):
  1. **Proximity:** `√X_prox = √X_cap + √X_pac` = direct CAPACITIVE coupling (`C_dl,eff = ∫ c_dl(x)cos(kx)dx`,
     standing-wave weighted; decays ~−26 dB/mm) + PACKAGE-MEDIATED coupling via the sample-package cavity
     (`∝ sin(kL)`; decays only **−2.7 dB/mm** — slow ⇒ DOMINATES at large distance).
  2. **Crossover:** drive line → air-bridge cross-capacitance `C_cross` → coupler → qubit. Reducing the
     air-bridge `C_cross` 2.2 → 0.6 fF gives **~11 dB reduction**.
- **NEW beyond Sarovar (2019):** the model **deviates significantly from the off-resonant Rabi / spectral-
  spillover approximation** — it accounts for EM package-cavity coupling + spatial standing-wave modulation. The
  package-mediated tail decays slowly, so **Sarovar's "separate the qubits far enough" distance-scaling is
  insufficient** on intermediate-scale chips (at d=1165 µm, package-mediated coupling DOMINATES total crosstalk).

## The gate-level residual + mitigation [paper, IQM 2603.11018]
- Modern **model-based qubit-frequency optimization → mean SIMULTANEOUS single-qubit-gate fidelity 99.96%**, plus
  a **crosstalk-transition-suppression pulse shaping** (minimize spectral energy near the leakage/crosstalk-
  inducing transitions). So the deployed RESIDUAL drive crosstalk (after frequency planning + pulse shaping) is
  small — the certifiable footprint is what survives the mitigation. (IQM = a physical-gate + analytic-model
  counterfactual demo — see `project-digital-twin-noise-landscape`.)

## Limitations / what does NOT apply [paper→ours]
- Song is a device-LAYOUT/EM-modeling paper (the crosstalk SOURCE), not a QEC channel; it does NOT discuss
  tunable couplers as mitigation (focuses on geometry: air-bridge dims, differential qubits, TSVs/bumps,
  coupler-segment destructive interference). For the TEACHER, the relevant object is still the EFFECT on the
  spectator B (an off-resonant drive), parameterized by the spillover fraction; Song fixes the MAGNITUDE +
  the source understanding, not the spectator-effect form.

## Relevance to the teacher (DRIVE/microwave crosstalk) [ours] — SOURCE update; magnitude ~OK
- **FORM (spectator effect): VALID — keep it.** The drive spillover = an off-resonant drive on the disjoint
  spectator B (our QuTiP `build_spillover_channel`: driven A + off-resonant Rabi on B, parameterized by the
  crosstalk fraction c). The PHYSICAL effect on B is still an off-resonant Rabi. No spectator-effect form change.
- **SOURCE understanding: UPDATED (not stale, but enriched).** Sarovar's pure-spectral-spillover picture is
  superseded by the multi-mechanism (capacitive + PACKAGE-MEDIATED cavity + crossover) source; the package tail
  decays slowly (−2.7 dB/mm) so crosstalk doesn't vanish with distance. Cite Song 2606.02440 for the source.
- **MAGNITUDE: roughly IN-RANGE (the least-stale of the three forms).** My QuTiP `SpilloverParams.c ≈ 0.05`
  (Sarovar illustrative) ↔ `X ≈ −26 dB`, squarely inside Song's measured `−10 to −40 dB` (c ≈ 0.01–0.1). KEEP
  the bracket **c ∈ [0.01, 0.1]** (SWEPT), now grounded in Song's measured X (not Sarovar's illustrative 1e-2),
  with the deployed-RESIDUAL (post-frequency-planning, IQM 99.96%) as the realistic low end.
- **Epistemic class:** (b) prediction band — drive spillover `c ∈ [0.01, 0.1]` (X = −40..−20 dB, Song-measured,
  SWEPT), with the post-mitigation residual as the realistic arm; the off-resonant-Rabi spectator-effect form +
  the cross-drive-ratio definition = (a)/grounded.

## Trust [ours]
精读 of Song's abstract + intro + the two-mechanism model (capacitive √X_cap + package-mediated √X_pac ∝ sin(kL),
−2.7 dB/mm; crossover C_cross) + the measured X = −10..−40 dB (the X-ratio numbers via the HTML WebFetch, the
mechanism/model via the txt). The IQM 99.96% simultaneous-SQ-fidelity + crosstalk-transition pulse shaping from
search + my prior note. The "c ≈ 0.01–0.1, magnitude in-range, source-understanding-updated" verdict is [ours].
The detailed EM circuit derivation (capacitance integrals, the 17-qubit-processor model fits) skimmed.
