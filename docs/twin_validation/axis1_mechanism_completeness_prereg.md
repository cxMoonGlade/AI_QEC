# Axis-1 mechanism-completeness pre-registration — the M0–M34 catalog mapped onto the axis framework

Date: 2026-06-29. Status: **theory-first PRE-REGISTRATION (finish-plan Step 8 scope decision).**
Defines, by axis, which of the project's `mechanisms/catalog.py` error types are Axis-1's
responsibility, which are Axis-2, and which are downstream/twirled — so "mechanism-complete"
for the Axis-1 carrier is a fixed, bounded checklist rather than "cover all 35".

## Two distinct subsystems (the distinction that drives this doc)
`src/qec_twin/mechanisms/catalog.py` M0–M34 is the **teacher-learner controlled-mechanism
catalog** (the B-path / HARDEN recover–understand–manipulate–predict line), expressed at the
**channel / PTM / SPAM** level. Its consumers are `forward/channels.py`, `forward/ptm.py`,
`mechanisms/profiles.py`, `contexts/probe_contract.py`, `forward/exact/born_local.py` — **none
are `simulator/axis1_*`.** The **Axis-1 carrier** (`simulator/axis1_*`, the same-substep
joint-Lindbladian MCWF-on-MPS simulator) is a separate, parallel mechanism inventory expressed at
the **generator (Hamiltonian + collapse)** level: `DR / ZZ / FSIM_SWAP / FSIM_PHASE / CTRL_*`
+ `T1 / T1_UP / T2 / RD` + qutrit/ququart leakage families. This doc maps the M0–M34 catalog onto
the axis framework to define the Axis-1 carrier's mechanism-completeness target.

## Axis definitions (binding, as given)
- **Axis-1** = same-substep *instantaneous joint Lindbladian* / same-substep generator coupling.
- **Axis-2** = cross-cycle / source / memory / shared timeline.
- **Axis-3** = the residual NOT covered by Axis-1 ∪ Axis-2.

## The classification test (a)
An effect is **Axis-1 ⟺ it is a time-local GKSL generator (a Hamiltonian or a collapse operator)
acting WITHIN one substep on the system Hilbert space.** Coherent over-rotations / parasitic
couplings → Hamiltonians; relaxation / thermal / correlated decay → collapse operators; crosstalk
→ a Hamiltonian on the *extended* support (joined by the W-A connected-cluster machinery); reset/
prep imperfection → a channel on the reset/measurement substep. Drift *across* cycles, source
memory, and cross-cycle correlations → Axis-2. A twirled Pauli channel is Axis-1-*representable*
(as Pauli-jump collapse) but is the downstream form of upstream coherent generators.

## M0–M34 → axis classification

Legend: ✅ already in the Axis-1 carrier · ◐ Axis-1 but only partial (knob/channel missing) ·
❌ Axis-1 gap (not yet a primitive) · A2 = Axis-2 · DS = downstream/twirled (Axis-1-representable, architecturally redundant).

| ID | name | axis | carrier form | status |
|----|------|------|--------------|--------|
| M4 | amplitude_damping | **Axis-1** | collapse `√γ₁ σ⁻` (=T1) | ✅ |
| M5 | idle_dephasing_or_relaxation | **Axis-1** | collapse T2 (+T1) | ✅ |
| M8 | coherent_rzz_overrotation | **Axis-1** | Hamiltonian (=ZZ) | ✅ |
| M21 | conditional_phase_branch | **Axis-1** | Hamiltonian (=LEAK_COND_PHASE) | ✅ |
| M24 | thermal_excitation | **Axis-1** | collapse (=T1_UP) | ✅ |
| M34 | leakage_relaxation_surrogate | **Axis-1** | real leakage (SEEP/HEAT/EXCHANGE/TRANSPORT) — stronger than the surrogate | ✅ |
| M6 | coherent_rx_overrotation | **Axis-1** | 1q Hamiltonian (error knob on DR/CTRL) | ◐ |
| M7 | coherent_rz_overrotation | **Axis-1** | 1q Hamiltonian | ◐ |
| M20 | coherent_ry_overrotation | **Axis-1** | 1q Hamiltonian | ◐ |
| M27 | coherent_h_axis_overrotation | **Axis-1** | 1q Hamiltonian (XZ-vector axis) | ◐ |
| M17 | reset_to_1_bias | **Axis-1** | reset-substep channel imperfection | ◐ |
| M18 | prep_axis_or_reset_asymmetry_bias | **Axis-1** | reset/prep-substep channel | ◐ |
| M15 | hard_non_pauli_kraus_gate_error | **Axis-1** | declared same-substep CPTP/Kraus (stress) | ◐ |
| M19 | weak_type4_ptm_mixing | **Axis-1** | same-substep PTM-residual channel (stress) | ◐ |
| M10 | coherent_rxx_ryy_perturbation | **Axis-1** | 2q Hamiltonian (XX+YY) | ❌ |
| M22 | coherent_cxx_parasitic_coupling | **Axis-1** | 2q Hamiltonian (XX) | ❌ |
| M23 | coherent_cyy_parasitic_coupling | **Axis-1** | 2q Hamiltonian (YY) | ❌ |
| M28 | coherent_xy_parasitic_coupling | **Axis-1** | 2q Hamiltonian (XY) | ❌ |
| M29 | coherent_zx_parasitic_coupling | **Axis-1** | 2q Hamiltonian (ZX) | ❌ |
| M30 | coherent_zy_parasitic_coupling | **Axis-1** | 2q Hamiltonian (ZY) | ❌ |
| M31 | coherent_xz_parasitic_coupling | **Axis-1** | 2q Hamiltonian (XZ) | ❌ |
| M32 | coherent_yz_parasitic_coupling | **Axis-1** | 2q Hamiltonian (YZ) | ❌ |
| M33 | coherent_yx_parasitic_coupling | **Axis-1** | 2q Hamiltonian (YX) | ❌ |
| M11 | spectator_crosstalk_rz_or_zz | **Axis-1** | Hamiltonian on EXTENDED support (gate↔spectator); joined by the W-A connected-cluster machinery | ❌ |
| M12 | correlated_two_qubit_relaxation | **Axis-1** | two-site JOINT collapse operator (carrier collapse is 1-site today) | ❌ |
| M13 | drifted_coherent_overrotation | **Axis-2** | the instantaneous value is Axis-1 (M6/M7); the DRIFT across cycles is Axis-2 | A2 |
| M14 | operation_dependent_error | **Axis-2** (lean) | per-substep operation context = Axis-1; cross-cycle/history-conditioned = Axis-2 | A2* |
| M16 | measurement_context_bias | **Axis-2** | measurement-layer / cross-sample readout context | A2 |
| M1 | readout_0_to_1_bias | **Axis-2** | readout assignment SPAM (classical relabel); carrier has RD dephasing, not assignment bias | A2 |
| M2 | readout_1_to_0_bias | **Axis-2** | readout assignment SPAM | A2 |
| M3 | readout_symmetric_assignment_noise | **Axis-2** | readout assignment SPAM | A2 |
| M0 | local_stochastic_pauli_gate_error | **DS** | Pauli channel = twirl of coherent generators; representable as Pauli-jump collapse but downstream | DS |
| M9 | two_qubit_depolarizing_after_rzz | **DS** | 2q Pauli/depolarizing channel (twirl-downstream) | DS |
| M25 | stochastic_bit_flip_gate_error | **DS** | Pauli-X channel (twirl-downstream) | DS |
| M26 | stochastic_y_gate_error | **DS** | Pauli-Y channel (twirl-downstream) | DS |

## Counts
- **Axis-1, already covered (✅):** 6 — M4, M5, M8, M21, M24, M34.
- **Axis-1, partial (◐ — needs an error-knob / reset-channel / declared-channel):** 8 — M6, M7, M20, M27, M17, M18, M15, M19.
- **Axis-1, missing (❌ — not yet a primitive):** 11 — M10, M22, M23, M28, M29, M30, M31, M32, M33, M11, M12.
- **Axis-2 (NOT Axis-1):** 6 — M13, M14*, M16, M1, M2, M3.
- **Downstream/twirled (Axis-1-representable, architecturally redundant):** 4 — M0, M9, M25, M26.

Total 35. **None of the 35 are Axis-3** — they all fall into Axis-1 or Axis-2. (The genuine Axis-3
candidate — non-CP-divisible intra-gate bath memory — is NOT in this catalog; see
[`axis1_axis3_watch.md`](axis1_axis3_watch.md).)

## Conclusion — the Axis-1 mechanism-completeness target (Step 8)
"Mechanism-complete" for the Axis-1 carrier is **NOT "cover all 35"**; it is **"hold every M-mechanism
that is a same-substep generator"**: the **8 partial + 11 missing = ~19 Axis-1 mechanisms**, dominated by:
1. **Coherent 1q over-rotation knobs (4):** M6 rx, M7 rz, M20 ry, M27 h-axis — Hamiltonian error terms on the ideal control.
2. **Coherent 2q parasitic-coupling Hamiltonians (9):** M10 (xx+yy), M22 cxx, M23 cyy, M28 xy, M29 zx, M30 zy, M31 xz, M32 yz, M33 yx.
3. **Spectator crosstalk (1):** M11 — a same-substep Hamiltonian on the extended (gate ∪ spectator) support; **the W-A connected-cluster join (Step 1) is exactly its foundation.**
4. **Correlated two-qubit relaxation (1):** M12 — a two-site joint collapse operator (generalize the 1-site collapse path).
5. **Reset/prep-substep imperfection (2):** M17, M18 — channels on the reset/prep substep.
6. **Declared non-Pauli stress surrogates (2):** M15, M19 — same-substep CPTP/PTM-residual channels.

Each admitted mechanism is certified one-/two-site vs the independent oracle `assemble_substep_channel`
(process infidelity `1−F_e` / Choi trace distance), exactly as the existing leakage families are.

**Explicitly NOT Axis-1 (do not build into the same-substep carrier):**
- **Axis-2 (frozen):** drift M13, cross-cycle/history context M14, readout assignment SPAM M1/M2/M3/M16.
  These are cross-cycle/source/measurement-layer; they belong to the Axis-2 source-process line.
- **Downstream/twirled:** Pauli channels M0/M9/M25/M26. The carrier produces the *upstream coherent*
  generators (group 1–2 above); their twirl yields these Pauli channels. Adding them as carrier
  primitives is redundant (architecture choice, not a physical Axis-1 gap).

**Epistemic class:** the test (a) and the axis assignments are (a)-exact definitional classifications;
the "~19 is the Axis-1 target" is the (c)-gate scope decision for Step 8. No METRICS.md change, no new
scored quantity, no Axis-1-completion claim until each admitted mechanism is GPU-certified vs the oracle.
