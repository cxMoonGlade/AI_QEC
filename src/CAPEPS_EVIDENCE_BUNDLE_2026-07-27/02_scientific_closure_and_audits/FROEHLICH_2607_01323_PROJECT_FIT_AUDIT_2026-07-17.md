# Fröhlich et al. 2607.01323 project-fit audit — 2026-07-17

## Disposition

Project fit: **high but model-restricted**.

The paper is directly relevant to MPS quantum-trajectory execution, raw norm loss, correlated
multi-site jump support, and the separation between trajectory variance and bond growth. It does not
certify the current qutrit leakage carrier or its multi-round `Record`, because its strongest
simplifications rely on sparse Pauli-Lindblad unitary jumps and its benchmarks use terminal/local
observables rather than schedule-derived detector histories.

Recommended literature action: admit a source-only current note after schema and artifact verification.
Recommended simulator action: use as a design/comparison source only; do not copy its one-jump window,
state-independent hazard, or bond-2 MPO conclusions outside their stated Pauli-string assumptions.

## Source integrity

- Source: Maximilian Fröhlich et al., *Noisy quantum circuit simulation with the tensor jump method*,
  arXiv:2607.01323v1.
- Local artifact: `docs/papers/froehlich_tensor_jump_method_2607.01323.pdf`.
- SHA-256: `cf1c6c23a33ac7c73b43c5891cee3a5c77c3ba3d36e8e818afe8f9647d65c13a`.
- Full text read; load-bearing PDF pages visually checked: 3, 4, 5, 7, 9, 13, 14.

## Transfer table

| Paper result | Exact locator | Project transfer | Limit |
|---|---|---|---|
| TJM no-jump norm loss determines total jump probability | Sec. II.B, Eqs. (2)–(7), PDF p. 3 | Supports keeping raw pre-normalization norm as physical branch mass. | Small-step MCWF formula; no license to truncate the branch operator before measuring its norm. |
| Pauli jumps have state-independent channel weights | Sec. II.C, Eqs. (8)–(13), PDF pp. 3–4 | Useful independent special-case comparator for Pauli-only paths. | Depends on `P_m^dagger P_m = I`; does not cover amplitude damping, leakage, reset, or general Kraus families. |
| cTJM uses a gate-local jump set and at most one jump per two-qubit gate | Sec. III and Algorithm 1, PDF pp. 4–5 | Provides a concrete bounded circuit-window algorithm to compare against. | Multi-jump windows are explicitly out of scope; the current schedule cannot inherit this approximation without its own hazard gate. |
| Error taxonomy separates sampling, splitting, TDVP integration/projection, and SVD truncation | Sec. III.B, Eqs. (15)–(16), PDF pp. 4–5 | Supports separate ledgers and acceptance gates rather than a single truncation scalar. | The paper says accumulated projection impact lacks a general-purpose estimator outside special cases. |
| Projector and analog unravelings reproduce the same Pauli-Lindblad generator | Sec. IV.A–B, Eqs. (18)–(35), PDF pp. 5–8 | Supports an eventual controlled unraveling comparison after physical equivalence is proven. | Equivalent ensemble generator does not imply equal finite-sample variance, bond demand, or per-seed record sequence. |
| Long-range `a I + b P` jumps admit exact bond-2 MPOs | Sec. IV.C, PDF pp. 9–10 | Useful comparator for Pauli-string nonlocal operators. | The form is special; it is not an exact-MPO theorem for arbitrary connected multi-qutrit operations. |
| Bond and variance benefits are regime-dependent | Sec. V, Figs. 1–3, PDF pp. 10–14 | Motivates reporting both trajectory variance and bond demand. | Benchmarks cap `chi` at 128 and monitor selected observables; they do not validate a QEC detector record or LER. |

## Record-faithfulness adjudication

The paper records per-gate expectation values and proves generator equivalence or variance laws in special
Pauli settings. It does not define the repository's measurement/reset schedule, detector XOR folding,
observable columns, branch-coverage ledger, or packed joint `Record`. Its raw-norm equations support the
probability bookkeeping discipline, but its normalized conditional trajectories do not supply a
finite-bond total-variation bound.

The source therefore strengthens two existing restrictions:

1. generic Kraus/no-jump/jump operations whose norm determines branch mass remain uncapped; and
2. lower variance or lower bond dimension is performance evidence only after an independent record oracle
   passes.

## Final verdict

`ADMIT_SOURCE_NOTE`: yes, because the paper directly sharpens the MPS trajectory and error-bookkeeping
surface.

`IMPLEMENTATION_AUTHORITY`: no. The source does not authorize changing the current simulator, enabling
production pruning, or promoting the restricted MPS routes beyond verification status.
