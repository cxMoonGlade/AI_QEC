# Theory-first grounding — coupled-teacher RATES + record-level OBSERVABLE

> **NUMERICAL-PROVENANCE CORRECTION, 2026-07-13.** The literature values below are
> device-specific comparison scales. Neither the `~4 kHz` source point nor the `370 kHz` G2 point is
> calibrated to the shipped Google patch. The universal “record-DEAD at any distance” inference is
> withdrawn; the committed calculation is a local model/configuration result. Current authority:
> [`../NUMERICAL_PROVENANCE.md`](../NUMERICAL_PROVENANCE.md).

**Date 2026-06-30.** Prompted by the 3-agent review that FAILED
`coupled_cycle_teacher_d3_mcwf_design.md` (ungrounded rates + a retired observable). Theory-first
step 1 found the grounding ALREADY EXISTS in cached 精读 notes — this note synthesizes them for the
specific question, it does not reinvent. Epistemic classes: **(a) exact/theorem**, **(b) prediction
band / grounded literature value**, **(c) gate/decision rule**.

## (a) RATES — reconciling the ~90× `zeta` inconsistency against the real device

**The two code constants correspond to two project regimes; the small one is literature-order, not
device-calibrated.**

Convert the code's `zeta` to a residual-ZZ frequency (`ζ_rad/ns / 2π` = GHz):
- **G2** `zeta = 2π·0.37e-3 rad/ns` `[CODE axis1_bridge.py:51]` ⇒ **residual ZZ ≈ 370 kHz**.
- **source_coupling** `zeta ≈ 2.56e-5 rad/ns` (derived, `[CODE source_coupling.py]`) ⇒ **≈ 4 kHz**.

Grounded real residual-ZZ magnitudes (idle, between gates) — **(b)**:
- Modern **tunable-coupler** residual ZZ **< 1 kHz**; FTF **< 3 kHz** `[pettersson_fors_zz_coupling_comprehensive_2408.15402]`.
- **STC-class** (single-transmon coupler, highly detuned) residual ZZ **|J_ZZ| ≈ 60–80 kHz** `[kubo_dtc_residual_zz_2402.05361]`.
- Residual ZZ only "matters" (dominates over relaxation) **above ~100 kHz**; a CZ gate uses **ζ̄ = 2π·5 MHz** (on) `[pettersson_fors_...2408.15402]`.

⇒ The source-coupling value (`~4 kHz`) lies in a modern tunable-coupler literature order of magnitude,
while G2 (`370 kHz`) is a strong demonstration point above the cited idle regimes. Neither is a
measurement of this Google d3 patch, and the two papers do not establish a transferable Google range.

Coherence times — **(b)**:
- Illustrative transmon review: **T1=85 µs, T2*=95 µs, T2E=120 µs** `[krantz_superconducting_qubits_guide_1904.06560]`;
  prior 2D-transmon T1 ceiling **114 µs**, tantalum **360 µs** `[place_tantalum_transmon_2003.00024]`.
- The earlier `T1≈68 us, T2≈89 us` Willow sentence lacked an exact primary locator and is not used as
  evidence here. The shipped SI1000 circuit must be parsed directly before asserting its effective rates.
- Code: **G2 T1=T2=30 µs** `[axis1_bridge.py:52-53]` is PESSIMISTIC; **source T_φ=75 µs** `[source_coupling.py]`
  is realistic-order.

**Illustrative literature bracket for slice-1:** idle residual ZZ **~few kHz** in the cited tunable-coupler
study and CZ-window ZZ ~5 MHz in its stated setting. **`[c]` build rule:** ground exact per-cycle rates from the
shipped **SI1000 stim circuit** of a real Google d3 patch (not hand-set constants) before any record-level
claim; sweep ±1 order and report sensitivity.

## (b) FEASIBILITY — derivation, and the Kam refinement that changes the verdict

**Local zeta result only; the universal statement is retracted.** Residual ZZ is a coherent, **Z-basis-diagonal**
cross-Kerr `∝ σz⊗σz` `[pettersson_fors_...2408.15402]`; it moves records only for qubits in superposition,
and its per-cycle VARIATION under a realistic 1/f detuning source is ±~1e-9 rad/ns (the detuning shift is
~1e4× below the base detuning), giving record TV ~1e-11 in the frozen local model
`[VERIFIED g0_zeta_gammaphi_effectsize.py]`. This does not prove an all-distance or all-schedule null.

**`gamma_phi` raw-correlation scaling — (b) prediction band.** Dephasing acts every round; the per-cycle
detector-flip-rate perturbation accumulates, so the shared-vs-independent record TV grows ~linearly in
dephasing-bearing rounds (leading order, small per-round delta): TV(2 rnd)=5.77e-4 → TV(r10)≈2.9e-3
(N≈1.1e6) → TV(~20 rnd)≈5.8e-3 (N≈2.7e5). So more rounds DO soften the dense N≈2.7e7 by ~25×.

**BUT the Kam result caps this at the DECODE level — (a) from the paper.** `[kam_nonmarkovian_surface_code_2410.23779]`:
- "**Detector pairwise (2-point) autocorrelation does NOT distinguish benign from catastrophic**"; the
  multi-time **timelike string** is the real signature.
- **Temporal correlations on DATA qubits (Class 0) are BENIGN** (LER ≈ independent model); only on
  **SYNDROME qubits (Class 2)** are they catastrophic (timelike strings).

**Measured serial cost — (a) VERIFIED.** d3 q17 MCWF at the numerically-stable bond 48 =
**403.5 s/trajectory** `[VERIFIED g0_d3_mcwf_cost_triage.py]` (bond 16 crashes on a non-positive
probability). ⇒ ~89 trajectories in 10 h serially, vs T~1e6 for a raw-correlation statistic — **cost-
infeasible by ~4 orders**; and batched-MCWF-over-MPS is a multi-week custom-engine rewrite that barely
helps because trajectories diverge at the first measurement (round 1 of 10) `[3-agent design review]`.
So the raw-correlation route is dead on cost even before the signal question.

⇒ Source-modulated **data-qubit dephasing** produces a raw record correlation that grows with rounds
(the ~25× above) but is **decode-BENIGN** (LER ≈ independent) — a nonzero 2-point signal with ~zero
decode-relevant ΔLER. **This is exactly the contract's H2 "capped at the source layer," now anchored to
the mechanism (data-qubit temporal correlation = Kam-benign), not assumed.** The feasibility softening is
REAL for the raw correlation but IRRELEVANT for the decision-relevant quantity unless the coupling lands
on syndrome qubits in a multi-time streak.

## (c) OBSERVABLE — decode-relevant ΔLER, NOT the 2-point correlation (Kam-anchored)

The design's §4 gate (cross-cycle detector correlation / shared-vs-independent TV) is **precisely the
Kam-benign 2-point statistic** that "does NOT distinguish benign from catastrophic"
`[kam_...2410.23779]` — a retired strawman (contract H1/H2, `qec_coupling_simulator_build_contract.md:30-39`).

**Correct observable — (a)/(c):** **decode-relevant ΔLER** under the correlation-blind frozen Pauli-DEM
(`seam.build_matched_pauli_dem`), `ΔLER = LER(frozen DEM on coupled records) − LER(matched-marginal-
independent)`, computable from the emitted `{det,obs}` + the frozen DEM `[CONTRACT G4, :255-270]`. It is
first-order in the accumulated modulation (not squared like the correlation), collapses cleanly under the
`independent_baseline` ablation, and is the twin's headline object (decision regret). Cross-checked, per
the contract's binding anti-circular scope, against **corrqec** (Pauli/temporal-mask layer only, `:495-502`)
so a sub-floor null is a VERIFIED-correct faithful property, not an unmeasured one. The multi-time /
excess-entropy correlator is the physically-sharper Kam signature but heavier; the coherence-revival wedge
is the sharpest non-Markovian discriminator but is a SOURCE-layer object (G3b), excluded from record-level
gating.

## Bottom line for the build decision

1. **Rates:** the `~4 kHz` point is literature-order and G2's `370 kHz` is a demonstration scale;
   neither is device-calibrated. Exact rates must come from the matched hardware artifact.
2. **`zeta` was sub-floor in the frozen local calculation only;** `gamma_phi` raw signal softens ~25× at d3 but is Kam-BENIGN at the
   decode level** (data-qubit temporal correlation) — so the decision-relevant ΔLER is expected ~sub-floor,
   confirming H2 from the mechanism, not by assumption.
3. **Observable = decode-relevant ΔLER + corrqec cross-check**, never the 2-point correlation.
4. **Implication:** the record-level d3 coupling is honestly a FAITHFUL-EMISSION deliverable with a
   reported (expected sub-floor) ΔLER — NOT a discrimination headline. The Axis-1 coupling stands as the
   certified channel-level (G2) result. A record-level "signal" build is not justified by the physics; a
   faithful-emission + honest-ΔLER build is, if the record-level slice is pursued at all.

**Provenance:** full-text 精读 notes read this session (existing, not re-generated):
`pettersson_fors_zz_coupling_comprehensive_2408.15402`, `kubo_dtc_residual_zz_2402.05361`,
`krantz_superconducting_qubits_guide_1904.06560`, `place_tantalum_transmon_2003.00024`,
`kam_nonmarkovian_surface_code_2410.23779`, `willow_qec_below_threshold_2408.13687`; dataset note
`docs/.datasets/google_105Q_surface_code_d3_d5_d7.md`; contract `qec_coupling_simulator_build_contract.md`.
