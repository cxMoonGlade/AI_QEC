# Mc Keever--Szymańska 2012.12233 project-fit audit — 2026-07-17

## Disposition

Project fit: **high for the future PEPS/PEPO carrier, indirect for the restricted MPS verifier**.

The paper is a direct source for environment-aware truncation of a two-dimensional mixed-state tensor
network.  It distinguishes the state bond dimension `D` from the CTMRG environment dimensions and
replaces an environment-blind simple update with Full Environment Truncation (FET) in Weighted Trace
Gauge (WTG).  This is exactly the right source for deciding what a PEPS truncation objective means and
does not mean.  It is not a certificate for the present detector-history carrier: the optimized quantity
is a normalized Hilbert--Schmidt overlap of two iPEPO representations, while the strongest independent
benchmark is a nearest-neighbour reduced-state trace distance.

Recommended literature action: admit a rebuilt source-only current note.
Recommended simulator action: retain FET/WTG as a future PEPS comparator and design source, but do not
promote its local objective, cycle entropy, or finite-`D` convergence to a bound on the packed `Record`,
total variation, branch coverage, or logical error rate.

## Source integrity

- Source: C. Mc Keever and M. H. Szymańska, *Dynamics of two-dimensional open quantum lattice models
  with tensor networks*, Physical Review X 11, 021035 (2021), arXiv:2012.12233v1.
- Local artifact: `docs/papers/2012.12233v1.pdf`.
- SHA-256: `c9d066eabc2cf1e4769f4d733737e0330a7882663a48894ed7f6073a0f502b48`.
- Full text and appendices read end to end.  Load-bearing PDF pages visually checked: 3, 4, 5, 8, 12,
  13, and 14.

## Transfer table

| Paper result | Exact locator | Project transfer | Limit |
|---|---|---|---|
| The iPEPO is a vectorized density operator with physical dimension `d^2`, state bond `D`, and two distinct CTMRG environments | Sec. II.B and Fig. 2(a), PDF p. 3 | Fixes the represented object and separates state capacity from environment accuracy. | PEPO positivity is not inherent; this is not a pure-state trajectory MPS. |
| A first-order Trotter layer enlarges a bond from `D` to `D'` before compression | Sec. II.C--D, Eqs. (3)--(8), Fig. 2, PDF pp. 3--4 | Supplies an explicit operation order for a future iPEPO implementation. | Trotter, Krylov, environment, and truncation errors remain distinct. |
| FET maximizes the alternative mixed-state fidelity `tr(rho phi)/sqrt(tr(rho^2)tr(phi^2))` | Sec. II.D, Eq. (9), PDF pp. 4--5 | Supplies the exact local/network objective that a faithful FET replay must optimize. | This is normalized Hilbert--Schmidt overlap, not Uhlmann fidelity, trace distance, outcome-law TV, or lost branch mass. |
| The bond environment and alternating Rayleigh-quotient solve define the compression | App. B--C, Figs. 8--9, PDF pp. 12--13 | Provides an auditable operator-level reference for constructing `Upsilon`, solving for `R`/`L`, and recovering isometries. | CTMRG is approximate and the joint alternating optimization is not accompanied by a global-optimum guarantee. |
| WTG supports environment recycling and cycle entropy diagnoses loop correlations | Sec. II.D and App. E, Eq. (E1), PDF pp. 5, 14 | Useful gauge/conditioning and representation diagnostics for a future cyclic carrier. | The paper's `S_cycle` scale is algorithm-specific and is not a physical-error or record-faithfulness threshold. |
| FET beats simple update by about one order of magnitude in the reported local benchmarks | Sec. III.B, Figs. 4--5, PDF pp. 7--8 | Justifies including SU as a corruption/baseline comparator. | The result is empirical for the stated dissipative Ising regime and `D`; it is not a universal gain. |
| An exact local-observable reference is available for a special zero-field dissipative Ising family | Sec. III.A and App. D, Eq. (D1), PDF pp. 5, 13 | Supplies a useful independent benchmark for the paper's local dynamics. | Localized-observable solvability does not certify a QEC schedule or historical joint record. |
| CTMRG dominates at order `O(chi_hs^3 D^6)` | Sec. IV, PDF p. 11 | Identifies the environment solver as the future PEPS cost bottleneck. | Cost scaling says nothing about correctness or production admission. |

## Record-faithfulness adjudication

The paper evolves a translationally invariant thermodynamic-limit density operator and evaluates local or
equal-time reduced observables.  It does not define sequential instruments, measurement/reset feedback,
detector XOR folding, schedule-derived record columns, branch-mass ledgers, or logical decoding.

The local two-site trace-distance comparison is stronger evidence than the internal FET objective, but it
still controls only the selected reduced state at a selected time.  A transfer to a historical adaptive
record would require a separate theorem or audit packet that controls every conditional instrument step
and composes those errors over the schedule.  No such bridge appears in this source.

The paper also states that PEPO representations are not inherently positive.  Positivity of the exact
dynamical map therefore does not by itself authenticate the numerically compressed representation or its
conditional probabilities.  Positivity, normalization, branch coverage, and record-law comparison must
remain independent acceptance surfaces.

## Final verdict

`ADMIT_SOURCE_NOTE`: yes.  It is the principal mixed-state FET/WTG source and directly narrows the PEPS
truncation claim.

`IMPLEMENTATION_AUTHORITY`: no.  The paper supports a future operator-level replay and benchmark, not a
change to the current restricted carrier and not a production or record-faithfulness promotion.
