# Patra et al. 2309.15642 project-fit audit — 2026-07-17

## Disposition

Project fit: **useful geometry/convergence falsifier, not a load-bearing carrier source**.

The paper demonstrates that graph PEPS with simple update and a mean-field observable environment can
be unusually accurate for a noiseless kicked-Ising circuit on the locally tree-like heavy-hex graph.  It
also reports the important counterexample to naive bond-dimension monotonicity near a critical region and
shows a deep-circuit regime without clear saturation.  These facts are useful for designing convergence
diagnostics, but the represented object is a terminal pure state and the reported validation surfaces are
selected expectation values.

Recommended literature action: retain a strict source-only review outside the smallest load-bearing
record-faithfulness corpus.
Recommended simulator action: no change; do not transfer the heavy-hex simple-update result to a loopy,
selective, mixed-state, multi-round carrier.

## Source integrity

- Source: Siddhartha Patra, Saeed S. Jahromi, Sukhbinder Singh, and Román Orús, *Efficient tensor network
  simulation of IBM's largest quantum processors*, arXiv:2309.15642v3, Physical Review Research 6,
  013326 (2024).
- Local artifact: `outputs/papers/2309.15642v3.pdf`.
- SHA-256: `aafacaf117d5a3a536760900800f473ef2c806f0c4485838e24db44712bc7fc6`.
- Full seven-page text and appendices read; load-bearing pages visually checked: 1, 2, 3, 5, 6, and 7.

## Transfer table

| Paper result | Exact locator | Project transfer | Limit |
|---|---|---|---|
| The state is a pure spin-half kicked-Ising circuit evolved by repeated unitary Trotter steps | Sec. II, Eqs. (1)--(3), PDF p. 1 | Fixes the narrow scientific object behind all benchmark claims. | No noise channel, trajectory branch, measurement, or reset is present. |
| gPEPS uses simple update and a mean-field environment for observables | Sec. III, PDF p. 2 | Supplies a cheap PEPS baseline and an explicit environment-blind corruption comparator. | Update equations are delegated to cited sources, and the approximation is justified empirically for this graph/model. |
| Five-step magnetization has a light-cone exact reference; higher-weight observables are also compared | Sec. IV.A and Fig. 2, PDF pp. 2--3 | Shows how a shallow independent oracle can expose method error. | Selected expectation values do not authenticate a terminal distribution, much less a historical record. |
| At 20 steps some parameters require larger bonds and one displayed point lacks saturation | Sec. IV.A and Fig. 3, PDF p. 3 | Supports fail-closed bond sweeps rather than assuming convergence. | The comparison is to another extrapolated TN result when no exact reference exists. |
| Long-depth observables are compared against the maximum achievable bond, not exact truth | Sec. IV.C and Figs. 5--7, PDF p. 5 | Provides an empirical self-convergence diagnostic. | Relative agreement with the largest computed bond is not an error certificate. |
| Lower bond can be more accurate near the critical region | Appendix A, PDF p. 6 | Directly falsifies naive monotonic-accuracy assumptions. | The authors still report eventual observable convergence at higher bonds for the studied case. |
| Heavy-hex has no local loop until a larger neighbourhood than the square lattice | Appendix C and Fig. 8, PDF p. 7 | Explains why simple update may work well on this geometry and supplies a topology-transfer warning. | Local tree likeness is model- and correlation-length-dependent. |

## Record-faithfulness adjudication

The paper contains no selective quantum instrument, so its PEPS norm is not an unnormalized branch mass.
It contains no mid-circuit observations, so its terminal expectation values do not define a joint outcome
law.  Its observable contraction uses a mean-field environment, and the high-weight observables exploit a
special Clifford rewrite into a local measurement after additional unitary evolution.

Therefore neither shallow exact agreement nor deep bond self-convergence gives a total-variation or logical
error-rate bound for an adaptive detector record.  The strongest transferable conclusion is diagnostic:
geometry and correlation length can make simple update look excellent, and bond increases can fail to
improve a chosen observable monotonically.

## Final verdict

`SOURCE_ONLY_REVIEW`: yes.

`CURRENT_CORPUS_ADMISSION`: no for the frozen record-faithfulness question.

`IMPLEMENTATION_AUTHORITY`: no.
