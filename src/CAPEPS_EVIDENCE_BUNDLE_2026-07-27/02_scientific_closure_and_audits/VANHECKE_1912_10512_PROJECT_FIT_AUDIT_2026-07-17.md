# Vanhecke--Vanderstraeten--Verstraete 1912.10512 project-fit audit — 2026-07-17

## Disposition

Project fit: **direct for operator-construction mechanics, non-load-bearing for record faithfulness**.

The paper gives a compact, symmetry-preserving MPO/PEPO cluster expansion for exponentials of
nearest-neighbour Hamiltonians.  It is useful when choosing how to represent a deterministic time-evolution
operator and when separating operator-approximation error from the later state-bond truncation.  It does
not study noisy instruments, raw branch mass, mixed-state trajectories, measurement/reset histories, or
detector records.

Recommended literature action: retain a strict source-only review, but do not add this source to the
smallest load-bearing current corpus unless the operator-construction question is reopened.
Recommended simulator action: no change.  The paper cannot authorize a bond cap on a selective branch
operator or a precision promotion for the restricted carrier.

## Source integrity

- Source: Bram Vanhecke, Laurens Vanderstraeten, and Frank Verstraete, *Symmetric cluster expansions
  with tensor networks*, arXiv:1912.10512v2; published in Physical Review A 103, 042612 (2021).
- Local artifact: `outputs/papers/pepo_survey/1912.10512v2.pdf`.
- SHA-256: `53e4e79c4f08f14c603a29e066cd0e0e48bb5dc0a86c43039c5a599c9f9f80ba`.
- All four pages read and visually checked.

## Transfer table

| Paper result | Exact locator | Project transfer | Limit |
|---|---|---|---|
| Cluster MPOs include exact finite-cluster exponentials while remaining size extensive | Construction in one dimension, PDF pp. 1--2 | Provides an alternative deterministic operator representation. | The expansion approximates a Hamiltonian exponential, not a stochastic instrument. |
| A maximum cluster size `p` is correct through order `t^(p-1)` and misses a stated fraction of order-`p` terms | Construction in one dimension, PDF p. 2 | Keeps cluster-expansion error distinct from state compression. | The counting argument is not a bound on finite-MPS state or record distance. |
| The evolved MPS is compressed by variational global-overlap optimization | XXZ example, PDF p. 2 | Supplies an explicit post-operator compression comparator. | The displayed observables and entanglement are empirical benchmarks; no joint-outcome-law theorem is given. |
| The construction extends to a square-lattice PEPO and adds a new virtual level for a plaquette loop | Construction in two dimensions, PDF pp. 2--3 | Useful topology-aware operator-construction evidence for a future PEPS path. | It does not define a PEPS state truncation metric or an environment-accuracy certificate. |
| Imaginary-time PEPO fixed-point optimization approaches the variational PEPS optimum as `tau` tends to zero | Table I and ground-state paragraph, PDF p. 3 | Separates fixed-point/operator error from the PEPS variational family. | Ground-state energy convergence is not trajectory, branch, or detector-record validation. |

## Record-faithfulness adjudication

The paper controls which Hamiltonian-cluster terms enter an approximate deterministic exponential.  Its
finite-MPS demonstration subsequently truncates the state by a different global-overlap optimization.  The
two errors therefore cannot be collapsed into one scalar even in the paper's setting.

No selective measurement or Kraus branch is present, so the construction supplies no statement about
unnormalized probability mass.  No adaptive sequence is present, so neither the cluster counting argument
nor the terminal observables can be transferred to a multi-round record distribution.

## Final verdict

`SOURCE_ONLY_REVIEW`: yes.

`CURRENT_CORPUS_ADMISSION`: no for the frozen record-faithfulness question; the source is adjacent
mechanics rather than a load-bearing bridge or disconfirmation.

`IMPLEMENTATION_AUTHORITY`: no.
