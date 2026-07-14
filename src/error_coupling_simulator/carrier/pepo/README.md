# carrier/pepo — 2D density-matrix PEPO carrier (rung 1: d3-certified, d-generic code)

The qutrit (fused d²=9 physical leg, `k = 3·t_ket + t_bra` row-major) density-matrix
PEPO forward carrier for the rotated d×d XZZX patch, per the binding rung-1 contract
(`docs/nonpauli_teacher/pepo_engine_rung1_contract.md` v4.2) under the governing
pre-registration (`docs/nonpauli_teacher/pepo_d5d7_carrier_prereg.md` v2.4). GPU-only,
torch-cuda-complex128 always (S8); devices passed in. Scope: the S10 compiled
(data-register) record law; rung-1 EVIDENCE is d3-only vs the exact-DM oracle
(`carrier/exact/qutrit_dm.py`), the code is d-generic.

Modules (disjoint builder ownership, contract §1):

- `layout.py` [A1] — diamond→`(u',v')` integer-grid transform (asserted), frozen
  max-balanced x-threshold cut site lists (`frozen_cut_a == (0,1,2)` at d3_at_q6_7),
  grid-adjacent plaquette paths (min inter-column crossings, D-P convention), the
  codestate PEPO builder (H-spread seed + bond-2 W chains, fused site-locally into
  `|m⟩⟨m|`; nonzero-norm asserted for BOTH m), and `dense_rho` (the ≤9-qutrit dense
  referee bridge for G1.0/G1.3/G1.9).
- `dynamics.py` [A2] — within-cycle single-site superops (F1 semantics), the exact
  stabilizer-channel TT, NTU truncation + the gap rule, `nonselective_round`, ledgers.
- `sampler.py` [A3] — reverse-pass boundary-MPS norm cache, general single-site fused
  caps for `Tr(ρ·Π)`, the two-term `E_s` expectation, Born sampling + selective update,
  the pinned obs law, compatibility re-exports of the neutral `carrier.record_fold`
  `s↔det` seam conventions, and the C3 negativity witness.

Pinned index/tag conventions (set by `layout.py`, consumed by A2/A3): site tensor tag
`Q{pos}` (engine position), fused physical index `k{pos}` (dim 9), fused virtual bond
`B{p}_{q}` (`p<q`) present on EVERY grid edge (dim 1 when structurally empty), site
tensors rank ≤ 5. No global gauge/canonical form is tracked; the only bond metadata is
the per-bond dimension + the truncation ledger (`PepoState.ledger`: discarded weight on
the squared-σ scale + per-round trace shift). Positivity is never assumed (C3/S9).

Gates + evidence scripts live under `outputs/nonpauli_teacher/pepo_rung1_*` [A4];
registered tests in `tests/test_pepo_rung1.py`.
