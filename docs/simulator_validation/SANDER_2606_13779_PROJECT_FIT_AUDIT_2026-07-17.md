# Sander et al. 2606.13779 project-fit audit — 2026-07-17

## Disposition

Project fit: **high for resource decisions, non-authoritative for scientific correctness**.

The paper supplies a useful cost decomposition for MPS trajectory simulations: memory per trajectory,
runtime per trajectory, and sampling effort are independent channels. This directly warns against choosing
an unraveling or truncation merely because it lowers bond dimension. It does not provide a new trajectory
kernel, a finite-bond correctness theorem, or a record-faithfulness bound.

Recommended literature action: admit a concise source-only current note. Recommended project action: use
the `(alpha, kappa)` surface only after the compared routes have independently passed the same physical and
record-accuracy gates.

## Source integrity

- Source: Aaron Sander et al., *Computational regimes in matrix-product-state-based quantum trajectory
  simulations*, arXiv:2606.13779v1.
- Local artifact: `docs/papers/sander_computational_regimes_mps_trajectories_2606.13779.pdf`.
- SHA-256: `3b9ffcb54971c3ff0ea11eb4c2a10e3401f50349dbe3face5a2e1e3e8d6d06b7`.
- Full text read; load-bearing PDF pages visually checked: 3, 4, 5, 6, 10, 11.

## Transfer table

| Paper result | Exact locator | Project transfer | Limit |
|---|---|---|---|
| Physical rates and numerical time step are different controls | Sec. II.C, Eq. (6), PDF p. 3 | Keep physical noise parameters separate from discretization and jump-frequency diagnostics. | `delta p = gamma delta t` is not an independent physical parameter and is not sufficient to characterize trajectories. |
| MPS memory, runtime, and sampling costs scale differently | Sec. III.A, Eqs. (8)–(10), PDF p. 4 | Report memory/bond, kernel work, and trajectory variance separately. | The displayed `chi^2`/`chi^3` laws omit implementation-dependent prefactors and are not calibrated wall-clock predictions. |
| Bond and sampling inflation are scenario-dependent | Sec. III.B, Eq. (11), PDF pp. 4–5 | Pilot comparisons must freeze Hamiltonian, noise, observable, time step, final time, and accuracy target. | `alpha` and `kappa` do not transfer between models, observables, or record definitions. |
| Thread- and memory-limited decision boundaries differ | Sec. III.C, Eqs. (12)–(17), PDF pp. 5–6 | Hardware regime may reverse the preferred unraveling after accuracy is fixed. | The model is a resource-level criterion, not a measured runtime or fidelity theorem. |
| Sampling inflation cannot be inferred from bond dimension | Sec. IV.D, Fig. 5, PDF p. 10 | A bond-saving route still requires an independent estimator-variance/record comparison. | The exact-reference demonstration is a 10-site fixed-observable benchmark, not a multi-round QEC record. |
| Pilot variance estimates imply trajectory-count estimates | Sec. V.A, Eq. (21), PDF pp. 10–11 | Useful for budgeting a preregistered standard-error target. | Central-limit estimates do not measure truncation bias, record TV, or LER bias. |

## Conflict and reconciliation with the simulator contract

The paper sometimes speaks of fixed accuracy after treating finite-step and MPS errors as controlled or
subdominant. In this repository, those conditions must be demonstrated rather than assumed. A small
discarded-weight threshold and stable local observable do not establish the complete `Record` law.

The compatible project reading is therefore:

1. first authenticate physical equivalence and record accuracy against an independent oracle;
2. then measure bond, runtime, and sampling variance under the same frozen scenario;
3. only then apply the paper's hardware-aware cost comparison.

This sequencing makes the paper useful without allowing efficiency to promote an inaccurate carrier.

## Final verdict

`ADMIT_SOURCE_NOTE`: yes, as a directly relevant cost/decision source.

`SCIENTIFIC_GATE`: no. Neither lower `alpha`, lower `kappa`, nor a favorable hardware region closes the
finite-bond-to-record gap.
