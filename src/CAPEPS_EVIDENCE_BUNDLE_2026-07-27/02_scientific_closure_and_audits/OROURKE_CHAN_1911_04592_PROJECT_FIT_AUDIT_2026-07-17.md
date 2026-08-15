# Claim audit — O'Rourke--Chan boundary gMPO and the operator-propagation boundary

## Status and decision

Retain O'Rourke and Chan, *A simplified and improved approach to tensor network operators in two
dimensions*, as a direct source for evaluating a deterministic Hamiltonian expectation
`<psi|H|psi>` on a finite rectangular PEPS by decomposing a PEPO contraction into boundary-MPS,
MPO, and generalized-MPO operations. It also gives explicit static Hamiltonian encodings for local,
finite-range, uniform long-range, and approximately represented isotropic long-range interactions.

The paper is not a source for constructing `exp(-beta H)`, a thermal density operator, an
imaginary-time evolution operator, a real-time channel, or a measurement trajectory. Its word
"operator" refers here to static Hamiltonian representations used inside energy/expectation-value
contraction. The method therefore informs deterministic operator contraction but does not certify the
project's density-matrix PEPO propagation or adaptive `RecordBatch` law.

This audit changes no implementation and authorizes no carrier-status or faithfulness upgrade.

## Assigned closure rows

| row | exact source location | source says | source does not say | status |
|---|---|---|---|---|
| Target quantity | Abstract and Sec. I, PDF p. 1 | A PEPO expectation value, especially the energy of a two-dimensional Hamiltonian on a PEPS, is evaluated on-the-fly with MPOs and gMPOs. | The target is not a partition function, Gibbs state, propagator, trajectory, or outcome probability distribution. | closed |
| gMPO definition | Sec. III A and Fig. 1, PDF pp. 4--5 | A gMPO adds an external virtual index to operator-valued MPO matrices so that summing that index couples operators outside the one-dimensional MPO domain into a resulting MPO. | The extra index is not a time, measurement-outcome, or Kraus-branch index. | closed |
| Boundary gMPO algorithm | Sec. III B, Eq. (16), Fig. 4, and steps 1--6, PDF pp. 6--7 | Horizontal bipartitions divide Hamiltonian terms into below, above, and crossing groups; cached norm environments, a running energy, and an approximate `intops` boundary accumulate `<psi|H|psi>` row by row. | The procedure does not update `|psi>` under `H`, apply `exp(-tau H)`, or output a new operator/state. | closed |
| Approximation and cost | Sec. III B step 5 and following discussion, PDF p. 7 | Approximation enters through boundary absorption/compression of `intops`; removing horizontal operator virtual indices reduces the stated PEPO-relative absorption and compression costs by factors `D_op^4` and `D_op^6`. | These factors are not physical-state or outcome-law error bounds. | closed |
| Static Hamiltonian constructions | Sec. IV A--B and Appendix A, Eqs. (17)--(24), (29)--(30), PDF pp. 8--11 and 15 | The paper explicitly constructs gMPO ingredients for nearest-neighbor, diagonal-neighbor, general finite-range, and equal-coefficient long-range Hamiltonians. | These constructions do not exponentiate the Hamiltonian or define thermal/imaginary-time evolution. | closed |
| Isotropic long-range approximation | Sec. IV C, Eqs. (25)--(28), PDF pp. 11--13 | A smoothly decaying isotropic potential is approximated by a sum of radial Gaussians; each Gaussian factorizes into one-dimensional factors represented by vertical MPOs and horizontal gMPOs. | The Gaussian fit is for spatial interaction coefficients, not a Trotter or imaginary-time expansion of `exp(-beta H)`. | closed |
| Numerical evidence | Tables I--II and Figs. 5 and 7, PDF pp. 8--9 and 14 | On the reported finite PEPS tests, boundary gMPO is comparably accurate and often faster than explicit PEPO or uncached term-by-term evaluation; the Coulomb example converges with boundary dimension and Gaussian-basis size. | The results do not prove uniform accuracy for all PEPS/Hamiltonians, and no statistical uncertainty or general contraction-error theorem is supplied. | empirical |
| Infinite systems | Sec. V, PDF p. 14 | The paper expects the boundary-starting formulation to generalize to infinite systems. | No explicit infinite-system algorithm or benchmark is provided. | proposed |
| Thermal or time-evolution operator | Full-text scope and Sec. V, PDF pp. 1--15 | The source constructs representations of static Hamiltonians for expectation evaluation. | It does not construct a Gibbs PEPO, `exp(-beta H)`, imaginary-time gates, real-time evolution, a channel, or a sequence of evolved density operators. | missing |
| Adaptive Record law | Full-text operational scope | Every reported result is a deterministic scalar Hamiltonian expectation for a fixed PEPS. | No measurements, outcomes, conditional operations, resets, detector folding, or joint Record distribution appear. | missing |

## Operation replay

| input | transformation | assumption | output | exact source location | replay status |
|---|---|---|---|---|---|
| Finite `L_x x L_y` PEPS `|psi>` and static two-dimensional Hamiltonian `H` | Horizontally partition `H` into below, above, and crossing terms as in Eq. (16) | Hamiltonian is expressible through the paper's localized PEPO/MPO operator structure | Row-dependent term groups for a boundary sweep | Sec. III B and Eq. (16), PDF p. 6 | closed |
| PEPS norm network | Contract from the top and cache partial boundary-MPS environments | Finite rectangular lattice and boundary-MPS contraction | `envs[0],...,envs[L_y-2]` | Sec. III B step 1 and Fig. 4(c), PDF p. 6 | closed |
| Bottom row, first environment, and in-row Hamiltonian terms | Apply an MPO between bra and ket and contract | MPO encodes all terms completed in row 1 | Initial scalar accumulator `E_bot` | Sec. III B step 2 and Fig. 4(d), PDF p. 6 | closed |
| Operators beginning below the partition | Form complementary operator vectors and then an `intops` boundary | Crossing terms have the pair structure described in Eq. (16) | Boundary object carrying unfinished interactions | Sec. III B steps 3 and 5, PDF pp. 6--7 | closed |
| Current `intops`, cached upper environment, and row `y` gMPO | Contract the newly completed Hamiltonian terms, add the scalar, then absorb/compress a new `intops` | Approximate boundary compression is accepted | Updated `E_bot` and approximate `intops` | Sec. III B steps 4--5, PDF pp. 6--7 | closed |
| Final row | Apply the last gMPO and contract with `intops` | All terms have been classified and accumulated once | One scalar `<psi|H|psi>` | Sec. III B step 6, PDF p. 7 | closed |
| Isotropic coefficient function `V(r)` | Fit `V(x,y)` by `sum_k c_k exp[-lambda_k(x^2+y^2)]`; encode the one-dimensional Gaussian factors | Smooth decay and finite Gaussian fit; one-dimensional coefficient MPO is numerically approximated | Static Hamiltonian expectation as a sum of `K` gMPO evaluations | Sec. IV C, Eqs. (25)--(28), PDF pp. 11--13 | closed |
| `H`, `beta` or imaginary-time step `tau` | No exponentiation or time-step construction is specified | Outside the paper's scope | `exp(-beta H)`, thermal state, or imaginary-time-evolved state | Full-text scope | missing |
| Measurement schedule and adaptive branches | No measurement operation is specified | Outside the paper's scope | Multi-round Record law | Full-text scope | missing |

## Project application

The paper can guide static expectation-value plumbing around a PEPS/PEPO contraction: classify
operator terms at a spatial boundary, keep only unfinished complementary operators in `intops`, and
accumulate completed scalar contributions. Its Gaussian factorization is also a source for compactly
encoding smooth isotropic *spatial Hamiltonian coefficients*.

It cannot be promoted to a PEPO time-evolution recipe. No operation in the replay changes the PEPS
state or density matrix. The object swept from row to row is a contraction boundary, not a physical
time slice, while the gMPO auxiliary index couples spatial operator terms rather than stochastic or
temporal branches. The paper therefore does not provide the channel, positivity, trace-preservation,
normalization, or causal conditioning properties needed by the project's qutrit density-matrix PEPO
carrier.

`docs/SIMULATOR.md` further requires validity on the declared Record law. A deterministic energy or
terminal expectation can be a useful diagnostic, but it is not a distribution over intermediate
measurement outcomes and cannot validate detector folds, observables, per-target reset, or adaptive
control. Those require a separate operation-level literature bridge and an independent Record oracle.

## Competing evidence and kill conditions

- `docs/SIMULATOR.md` labels PEPO a retained research density-matrix carrier, not the canonical record
  backend, and records finite-truncation full-record faithfulness as open.
- Kill any citation to this paper for a thermal PEPO or imaginary-time construction: no
  `exp(-beta H)`, Trotterized imaginary-time step, partition function, or Gibbs state is defined.
- Kill any interpretation of the boundary sweep as time evolution: it is a spatial contraction order
  used to evaluate a fixed `<psi|H|psi>`.
- Kill any interpretation of a gMPO auxiliary index as a measurement or Kraus branch: it couples
  spatial operator fragments and is summed inside a deterministic tensor contraction.
- Kill a general accuracy theorem inferred from Figs. 5 or 7: the evidence is numerical for the stated
  finite PEPS, Hamiltonians, boundary dimensions, and Gaussian fits.
- Kill use as a Record certificate if energy agreement replaces comparison of the full emitted
  detector/observable distribution against an independent reference.

## Source-local verdict

- read_status: complete
- evidence_status: persisted
- finite boundary-gMPO energy-evaluation row: closed
- static local/long-range Hamiltonian-encoding row: closed
- contraction-accuracy row: empirical
- infinite-system row: proposed
- thermal/imaginary-time operator row: missing
- adaptive multi-round Record-law row: missing
