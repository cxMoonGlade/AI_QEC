# Full-text review - Jaschke, Montangero & Carr, "One-dimensional many-body entangled open quantum systems with tensor network methods" (arXiv:1804.09796)

> **Provenance (2026-06-28): FULL-TEXT read.** PDF
> `docs/papers/jaschke_open_quantum_tensor_networks_1804.09796.pdf` -> txt
> `docs/papers/jaschke_open_quantum_tensor_networks_1804.09796.txt`
> (PyMuPDF/pdftotext-style extraction, 1649 lines). Figures were read through
> captions and extracted text; no pixel-level figure extraction is used here.
> Tags: **[paper]** = stated by the paper; **[ours]** = project inference.

## Metadata [paper]

- Authors: Daniel Jaschke, Simone Montangero, Lincoln D. Carr.
- Venue/status: arXiv:1804.09796v2, 30 Aug 2018; Quantum Science and
  Technology 4, 013001 (2018).
- Type: methods review plus benchmark implementation for one-dimensional
  Lindblad master-equation dynamics with tensor networks.

## Executive Summary [paper]

The paper reviews and benchmarks three tensor-network routes for Lindblad open
systems: quantum trajectories (QT), matrix-product density operators (MPDO),
and locally purified tensor networks (LPTN). The shared target is the Lindblad
master equation, with the Liouville-space form used for MPDO evolution and
pure-state stochastic unraveling used for QT. The authors' practical conclusion
is deliberately not one-size-fits-all: QT, MPDO, and LPTN cover different
resource/accuracy regimes, and a useful simulator should keep more than one
method available.

## Method (deep) [paper]

The base equation is the Lindblad master equation

```text
rho_dot = i [rho, H] / hbar + sum_nu L_nu rho L_nu^dag
          - 1/2 {L_nu^dag L_nu, rho}.
```

The paper derives it from the system+environment Schrodinger equation by the
usual Born-Markov and secular approximations, then sets `hbar=1`.

For direct density evolution, the density matrix is vectorized into a superket
`|rho>>` with a Schrodinger-like equation

```text
d |rho>> / dt = L(t) |rho>>
L(t) = -i H(t) x I + i I x H(t)^T
       + sum_nu L_nu x (L_nu^dag)^T
       - 1/2 (L_nu^dag L_nu x I + I x (L_nu^dag L_nu)^T).
```

An MPDO carries this Liouville-space object as a matrix-product operator. Moving
from an MPS to MPDO effectively squares local and bond dimensions: the paper
states the MPS tensor shape `(chi, d, chi)` becomes an MPDO shape
`(chi^2, d^2, chi^2)`.

For QT, each trajectory evolves a pure state under the non-Hermitian effective
Hamiltonian

```text
H_eff = H - (i hbar / 2) sum_nu L_nu^dag L_nu.
```

At each time step, the norm loss decides whether a jump occurs. If a jump is
triggered, the unweighted probabilities are

```text
p_nu = <psi| L_nu^dag L_nu |psi>,
P_nu = p_nu / sum_mu p_mu,
```

and one Lindblad operator is sampled and applied, followed by renormalization.
Trajectory observables are ensemble averages over trajectories, but the paper
explicitly notes that not every density-matrix quantity, e.g. purity, is the
average of the corresponding pure-trajectory quantity.

For TEBD on MPDOs, the global propagator `exp(L dt)` is split into local
two-site Liouvillian exponentials by a second-order Suzuki-Trotter formula:

```text
exp(L dt) =
  exp(sum_odd L_odd dt/2)
  exp(sum_even L_even dt)
  exp(sum_odd L_odd dt/2)
  + O(dt^3)
```

For `n` steps at total time `T=n dt`, the Trotter error scales as `O(dt^2)`.
The local exponentials use non-Hermitian matrix exponential machinery because
Liouvillians and `H_eff` are generally non-Hermitian.

The paper also treats the difficulty of nonlocal Lindblad operators. In
Appendix A it emphasizes that a Lindblad operator `L=A+B` cannot be split into
two independent Lindblad operators `A` and `B`; doing so drops the cross terms
in `L rho L^dag`. This is directly relevant to Axis-1: mechanisms in one
substep must be assembled into one joint generator, not sequenced or split in a
way that changes cross terms.

## Mechanism / carrier [paper -> ours]

- **QT carrier.** Pure-state MPS trajectory, with sampling error across
  trajectories and bond-truncation error inside each trajectory. This matches
  the shape already used in our leakage `forward/scalable/mps_forward.py`, but
  for Axis-1 computational-subspace GKSL we still need a new schedule-to-carrier
  adapter. [ours]
- **MPDO carrier.** Direct density evolution, good when a mixed state is the
  native object, but pays the squared local/bond dimension and does not
  structurally preserve positivity after truncation. [paper -> ours]
- **LPTN carrier.** Density matrix as `rho = X X^dag`, preserving positivity by
  construction; the detailed positivity/error certificate is better grounded by
  Werner et al. arXiv:1412.5746. [paper -> ours]

## Observable / validation objects [paper]

The paper uses exact diagonalization and analytic/macroscopic observables as
comparison objects for its benchmarks: finite-temperature Ising observables,
exciton center-of-mass dynamics under dephasing, and Bose-Hubbard double-well
center-of-mass damping. These are paper-local validation observables, not
project metrics for `qec_twin`.

For our Axis-1 prereg, the transferable object is the **carrier contract**:
given local `H` and `c_ops`, evolve a state/density/trajectory under the same
summed Liouvillian semantics used by the dense joint-L oracle.

## Findings + numbers [paper]

- MPDOs do not conserve positivity under truncation, and checking positivity of
  an MPO state is NP-hard in the cited literature. This is a structural warning,
  not a performance number.
- LPTN preserves positivity but may require larger resources and an auxiliary
  Kraus dimension.
- For QT, per-trajectory cost is close to closed-system MPS cost, and parallelism
  over trajectories is natural; ensemble sampling is the price.
- For MPDO TEBD, second-order Trotter splitting gives `O(dt^2)` global scaling at
  fixed total time. This is a paper method fact, not a project acceptance metric.
- Nonlocal Lindblad strings or `L=A+B` forms can inflate MPO bond dimension and
  cannot be naively split into separate Lindblad operators without changing the
  generator.

## Limitations [paper]

- The paper focuses on one-dimensional MPS-like chain structures; a 2D surface
  code requires an ordering or a higher-dimensional TN strategy.
- QT introduces trajectory sampling error; MPDO can lose positivity under
  truncation; LPTN keeps positivity but can be heavier.
- The benchmarks are not QEC schedules with measurement-record emission. They
  ground carrier choices, not a QEC simulator end-to-end claim.

## Relevance to AI_QEC / Axis-1 [ours]

1. The paper supports a multi-carrier design rather than a single universal
   backend: dense joint-L channel evidence for small windows, a state/trajectory
   carrier for larger schedules, and a possible positivity-preserving density
   carrier later.
2. QT/MPS is the closest first scalable slice because QEC record emission is
   naturally trajectory-like and the repo already has GPU MPS trajectory
   infrastructure for leakage. It does not replace dense G2 channel evidence.
3. MPDO is useful conceptually for density evolution but should not be the first
   production path unless positivity and truncation are explicitly bounded.
4. The Appendix A warning about `L=A+B` is an Axis-1 anti-toy guard: splitting a
   same-substep coupling into sequential or independent terms can erase cross
   terms.

## How to use / trust + open questions [ours]

- Trust level: high for carrier taxonomy and equations; it is a methods review
  plus implementation benchmark, not a QEC-specific simulator spec.
- Immediate use: cite as grounding for the Axis-1 scalable-carrier decision:
  QT/MPS first for record/state evidence, dense joint-L retained for channel
  evidence, LPTN deferred as the positivity-preserving density path.
- Open question: whether the existing leakage MPS infrastructure can be cleanly
  generalized from finite Kraus/qutrit op streams to computational-subspace
  `H,c_ops` GKSL trajectory steps without silently changing Axis-1 semantics.
