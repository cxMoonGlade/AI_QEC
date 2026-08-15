# Zheng--Yang 1906.04085 project-fit audit — 2026-07-17

## Disposition

Project fit: **direct PEPS loop-update mechanics, supporting rather than load-bearing evidence**.

The paper turns a four-site iPEPS plaquette into a periodic-MPS-like loop, applies an MPO imaginary-time
update, preconditions the loop, and then applies cyclic Full Environment Truncation bond by bond.  This is
a concrete example of non-degenerate rank-reducing FET inside a two-dimensional update.  Its numerical
evidence concerns pure-state ground-state energy, magnetization, critical parameters, and cycle entropy;
it contains no stochastic branch or detector history.

Recommended literature action: retain a strict source-only review.  Evenbly remains the primary source for
the FET objective; this paper is an implementation/benchmark companion.
Recommended simulator action: use only as a future PEPS replay comparator.  Do not interpret the normalized
loop fidelity or cycle entropy as probability-mass or complete-record accuracy.

## Source integrity

- Source: Yi Zheng and Shuo Yang, *Loop update for infinite projected entangled-pair states in two spatial
  dimensions*, arXiv:1906.04085v1.
- Local artifact: `outputs/papers/pepo_survey/1906.04085.pdf`.
- SHA-256: `baa3c51fb6452c2a750b20ca9cada92f47cf3f24f700071de0faece318227567`.
- All five PDF pages read and visually checked.

## Transfer table

| Paper result | Exact locator | Project transfer | Limit |
|---|---|---|---|
| A/B four-site plaquettes define alternating loop updates of a 2-by-2 iPEPS unit cell | Sec. II, Eq. (1), Figs. 1--2, PDF pp. 1--3 | Supplies an auditable topology and operation order for a plaquette update. | The demonstrated evolution is imaginary-time pure-state optimization. |
| Applying the plaquette MPO enlarges each loop bond from `D` to `D chi_mpo` | Sec. II, Eqs. (2)--(3), PDF p. 2 | Provides an actual non-degenerate pre-truncation state. | External legs are weighted by the simple-update environment approximation. |
| The loop is pre-canonicalized and each bond is reduced by FET projectors maximizing normalized fidelity | Sec. II and Fig. 2, PDF pp. 2--3 | Concrete comparator for checking that a future FET path truly changes rank and tensors. | Normalized fidelity does not preserve unnormalized stochastic branch mass. |
| Full loop update replaces local weights with BMPS or CTM environments | Sec. II, paragraph after Fig. 2, PDF p. 3 | Distinguishes local loop optimization from full-environment accuracy. | BMPS/CTM remain approximate and introduce their own bond dimension. |
| Loop update modestly improves the reported Heisenberg energy and lowers cycle entropy relative to simple update | Sec. III and Fig. 3, PDF p. 3 | Supplies SU as a baseline and cycle entropy as a representation diagnostic. | The improvements are empirical and model/bond-specific. |
| Full loop update improves the reported transverse-Ising critical parameters | Sec. III and Fig. 4, PDF p. 4 | Demonstrates a critical-regime benchmark with QMC reference values. | Ground-state critical observables are not trajectory or record validation. |

## Record-faithfulness adjudication

The FET objective is a normalized overlap between an enlarged loop state and a rank-reduced loop state.
Because both states are normalized in the objective, the paper supplies no rule for preserving the raw norm
of a selective Kraus branch.  Its cycle entropy diagnoses internal correlations of a cyclic representation,
not an emitted probability distribution.

The numerical tests contain no measurements, resets, adaptive control, or terminal samples.  A future use
therefore requires separate operator-level reconstruction, non-degeneracy checks, state/oracle comparison,
and an independent record-law bridge.

## Final verdict

`SOURCE_ONLY_REVIEW`: yes.

`CURRENT_CORPUS_ADMISSION`: no; retain as a companion implementation source to Evenbly.

`IMPLEMENTATION_AUTHORITY`: no.
