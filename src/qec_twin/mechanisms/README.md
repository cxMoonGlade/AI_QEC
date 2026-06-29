# mechanisms — noise-mechanism definitions + controlled teachers

The catalog of physical noise mechanisms and the controlled teachers used as
counterfactual ground truth.

- `catalog.py` — mechanism-ID → CPTP / readout channel definitions (taxonomy in
  `docs/error_mechanisms.md`).
- `profiles.py` — mechanism weight / strength profiles.
- `axis1_primitives.py` — Axis-1 local two-qubit-window primitive lowering for
  `DR`, `ZZ`, `T2`, `T1`, finite-temperature excitation `T1_UP`, spectator
  `_B` variants, readout dephasing `RD/RD_B`, and computational-subspace fSim
  residual Hamiltonians `FSIM_SWAP/FSIM_PHASE`: public primitive names + parameters become
  `H_list`/`c_list` inputs for `forward.joint_lindbladian`. This is not a
  frontend ideal-gate library, not a channel assembler, not a record emitter,
  and not Axis-2 source truth. Generic frontend `CTRL_*` ideal controls are
  lowered in `qec_twin.simulator.axis1_ideal_controls` and combined with these
  primitives by the simulator Axis-1 bridge.
- `teachers.py` — controlled teachers for the B-path (e.g. a coherent
  over-rotation rep-code teacher) whose true channels and true `do() → ΔLER` are
  KNOWN — the only counterfactual ground truth. Includes the H2 non-factorized
  teacher (`coupled_mixed_teacher`: H0 mixed field + coherent `exp(-i φ Z⊗Z)`
  edge) and its correlated-stochastic twirl control (`correlated_dephasing_kraus`).
- `source_coupling.py` — Axis-2 `Theta(z_t)` fan-out: one shared source draw
  conditions multiple mechanism parameters in the same cycle/substep.
- `source_process.py` — Axis-2 explicit cross-cycle source timelines
  (`RTNSource`, `OneOverFDriftSource`, `PhaseBurstSource`,
  `TemporalStormSPPSource`) plus exact timeline replay, row-preserving
  matched-marginal baselines, explicitly unphysical per-field ablations, scalar
  and site-local bridges into `source_coupling.Theta`, and source self-audits.
  This owns source truth only; it does not assemble channels or records.
- `seam_teachers.py` — ADR 0008 C3 seam-test teachers (registration item 2;
  evaluator-only; constants unchanged by SEAM-TEST PRE-RUN AMENDMENT 1): the
  M3-scale iid local backdrop, the coherent seam edge `exp(-i φ Z⊗Z)` at the
  H2 placement on the strip's UNCHECKED seam data pair (+ bias-injection
  control), its Pauli-twirled correlated-dephasing control, the D5 T-B
  bunching member (r = 1.27e-2, R = 5, λ1 = 0.873) and its T-A Pauli-ablation
  (R = 1) variant — all exposing the same `SeamTeacher` equal-treatment
  observation surface (D8); nothing depends on a seam check existing.

**Boundary.** Defines mechanisms/teachers; does not calibrate or intervene.
Channels are realized via `forward`. Spec: `docs/TWIN.md`.
