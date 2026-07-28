# Full-text review — G. Evenbly, "Gauge fixing, canonical forms and optimal truncations in tensor networks with closed loops" (arXiv:1801.05390)

> **Provenance (2026-07-13): FULL-TEXT read (精读).** arXiv:1801.05390v2 PDF
> `outputs/papers/coherent_leakage_longrange_closure/1801.05390v2.pdf` (12 pages,
> SHA256 `a5578205d15a7c44a11e0508e400109393c555be243d8478c20f668f75997f40`) →
> `outputs/papers/coherent_leakage_longrange_closure/1801.05390v2.txt` (`pdftotext -layout`).
> Provenance record:
> `outputs/papers/coherent_leakage_longrange_closure/1801.05390v2.provenance.json`.
> PDF pages 3, 5, 6, and 7 were rendered and visually inspected for WTG, cycle entropy, the FET
> optimization, and Table I. Tags: **[paper]** = source statement; **[ours]** = project inference.

## Metadata [paper]

- **Author:** Glen Evenbly, Université de Sherbrooke.
- **Venue/status:** Physical Review B **98**, 085155 (2018),
  DOI `10.1103/PhysRevB.98.085155`; arXiv:1801.05390v2, 17 May 2018.
- **Type:** tensor-network theory/method paper with finite-network and tensor-renormalization numerical
  demonstrations.

## Executive summary [paper]

The paper defines a **weighted trace gauge (WTG)** for arbitrary tensor-network bonds, introduces
**cycle entropy** to quantify correlations internal to a closed loop, and proposes **full environment
truncation (FET)** for non-bridge bonds. Its most important boundary is explicit: WTG coefficients in a
cyclic network need not be physical state properties, and simply retaining the largest WTG coefficients
is optimal only when cycle entropy is zero (or approximately safe when sufficiently small). For nonzero
cycle entropy, the proposed FET remains an iterative alternating optimization. The paper does not prove
that WTG provides a deterministic global-optimum truncation, nor does it connect its state fidelity to
QEC syndrome-record or rare logical-error fidelity.

## Selection + coverage [ours]

This is the source explicitly invoked by the active PEPS handoff to replace a failing ALS/FET solver
with “deterministic WTG canonical-spectrum truncation.” It is therefore load-bearing. It closes the
definitions of WTG, internal loop correlation, cycle entropy, and FET, while directly contradicting the
handoff's proposed replacement. Companion/contrary sources checked: Mc Keever–Szymańska 2021 (mixed-state
FET/WTG with approximate CTMRG environment), Sokolov–Zhang–Dziarmaga 2025 (ZMT as initialization), and
Werner et al. 2016 (a genuinely global trace-norm certificate, but only for a 1D local Markovian LPTN).

## Notation + source-location ledger [paper]

| symbol | object / domain | fixed or varied | assumptions | source |
|---|---|---|---|---|
| `T`, `|psi>` | TN representation and represented pure state | network-dependent | arbitrary geometry, internal bond matrices allowed | Sec. II |
| `sigma_AB` | matrix on selected bond | gauge-dependent | identity allowed initially | Sec. II, Fig. 1 |
| `Upsilon_AB` | four-leg bond environment from `<psi|psi>` | computed for selected bond | all other legs contracted | Eq. 1, Fig. 1 |
| `rho_L`, `rho_R` | left/right boundary matrices | gauge-dependent | PSD by construction | Eq. 2, Fig. 2 |
| WTG | gauge with `rho_L ∝ I`, `rho_R ∝ I`, diagonal positive `sigma` | defined when dominant fixed points are full rank | uniqueness requires nondegenerate leading transfer eigenvalue, modulo degeneracies/phases | Sec. III, Eqs. 3–8 |
| `s_i` | WTG coefficients | gauge-fixed representation quantity | equal Schmidt coefficients only for bridge/zero-cycle realization | Secs. III–IV |
| `S_cycle` | entropy of normalized absolute transfer spectrum | diagnostic | gauge-invariant on selected bond | Eq. 11, PDF p. 5 |
| `F(psi,phi)` | normalized pure-state overlap fidelity | FET objective | represented pure states | Eq. 12, PDF p. 6 |
| `u,v,sigma_tilde` | rank-reducing isometries/bond matrix | optimized | target rank fixed | Sec. V, Fig. 5 |

## Method (deep) [paper]

For a selected internal index, contract the norm network leaving the bond and its conjugate open to
obtain `Upsilon`. Insert the bond weights on either side to form completely positive transfer
operators, take their dominant left/right eigenoperators `L_0,R_0`, factor them, and transform the
bond so that both boundary matrices are proportional to identity. An SVD makes the transformed bond
matrix diagonal and positive (Eqs. 3–8).

Existence and uniqueness have nontrivial hypotheses:

- WTG exists iff the dominant eigenoperators used in the gauge transform are strictly positive
  (invertible), not merely positive semidefinite.
- Apart from WTG coefficient degeneracy and phases, uniqueness requires a nondegenerate dominant
  transfer eigenvalue. A degenerate leading eigenspace can yield multiple WTG choices.

The cycle entropy is

```text
lambda_tilde_alpha = |lambda_alpha| / sum_beta |lambda_beta|,
S_cycle = - sum_alpha lambda_tilde_alpha log2(lambda_tilde_alpha).  (Eq. 11)
```

If `S_cycle=0`, the bond can be realized as a bridge after an appropriate unitary cycle reduction, and
WTG coefficients coincide with the Schmidt coefficients of that realization. Only then is top-WTG
truncation optimal; “sufficiently small” `S_cycle` motivates near-optimal use but supplies no universal
threshold or error theorem.

For `S_cycle != 0`, FET replaces the selected bond by `u sigma_tilde v^dagger` and maximizes

```text
F(psi,phi) = <phi|psi><psi|phi> / (<phi|phi><psi|psi>).             (Eq. 12)
```

It alternates: with `u` fixed solve a generalized eigenvalue problem for
`R = sigma_tilde v^dagger`, SVD to update `sigma_tilde,v`, then fix `v` and update
`L = u sigma_tilde`; repeat to convergence. This is an iterative, non-convex-looking optimization,
not a canonical-spectrum closed form.

## The MECHANISM [paper]

The paper separates two kinds of correlation carried by a cyclic TN bond:

1. correlations among external/physical indices, which are properties of the represented state;
2. correlations internal to virtual closed loops, which may be representation redundancy.

WTG alone cannot distinguish these: two networks representing the same state can have different WTG
coefficient spectra. `S_cycle` detects internal loop structure, while FET uses the full environment to
optimize the represented-state fidelity after rank reduction.

## Mechanism mapping to the project [ours]

The project's “long-range correlation” label currently conflates physical long-range correlations with
internal loop correlations. Evenbly supplies a diagnostic vocabulary, not an automatic classifier:
nonzero `S_cycle` signals loop-internal structure, but it does not prove that every small direction is
physically disposable. The exact PEPS environment and the QEC record instrument still determine
whether a cut changes the product's observable.

## The OBSERVABLE / metric [paper]

- WTG existence/uniqueness and coefficient spectrum;
- cycle entropy `S_cycle`;
- pure-state overlap fidelity `F` before/after one bond truncation;
- Ising partition-function/free-energy errors in the renormalization demonstration.

None is a full QEC multi-time record metric. Eq. 12 is not a trace-distance certificate on a classical
record register and does not by itself bound a rare logical event.

## Findings + numbers [paper]

For critical square-lattice Ising tensor blocks, truncating `chi=16` to `chi_tilde=4` gives:

| network | cycle-reduction error | FET error | `S_cycle` before -> after |
|---|---:|---:|---:|
| `2x2` | `6.7e-4` | `5.0e-5` | `1.37 -> 1.04` |
| `3x2` | `2.0e-5` | `1.0e-8` | `2.27 -> 2.15` |
| `3x4` | `7.2e-6` | `5.0e-10` | `2.31 -> 2.22` |

The tests converged in fewer than 20 iterations and happened to reach the same final tensors from the
tested initializations. The paper says this **suggests** convergence to the global minimum; it is not a
proof or universal solver guarantee.

## Limitations [paper]

- WTG may fail to exist for rank-deficient dominant fixed points and may be nonunique for degenerate
  leading transfer eigenvalues/coefficients.
- WTG coefficients on a loop are not generally physical Schmidt values.
- Top-WTG truncation is optimal at zero cycle entropy and only heuristically near-optimal when it is
  sufficiently small. At nonzero cycle entropy that direct optimality is lost; the paper proposes
  iterative FET, not a theorem that FET is the unique possible solver.
- FET uses the supplied environment. The paper does not address error from an approximate PEPS
  environment such as finite-`chi_env` CTMRG.
- The numerical evidence is classical Ising/TN renormalization, not noisy measured QEC, leakage, or
  multi-round trajectories.
- No trace-norm, process/comb norm, full-record TV, or logical-error bound is derived.

## Contrary evidence and failure regimes [paper]

The paper's cyclic-MPS example is a direct counterexample to treating WTG coefficients as physical:
different virtual-loop representations of the same state have different WTG spectra. It also explicitly
states that cycle reduction followed by Schmidt/WTG truncation is not optimal when `S_cycle` is nonzero.
These facts contradict the active handoff's “WTG spectrum directly separates solver failure from genuine
long-range physics” and “deterministic WTG replaces ALS with a global optimum” language.

## Project kill conditions [ours]

- If measured `S_cycle` is not near zero, WTG-only top-`chi` truncation is not source-licensed.
- If WTG fixed points are rank-deficient or leading eigenvalues are degenerate, the claimed unique
  canonical spectrum does not exist without additional conventions.
- If the environment is approximate, “environment-optimal” means optimal only for that approximate
  objective; record faithfulness still requires an independent d3 record oracle.
- If only local/state fidelity is checked, no full-record or LER claim may propagate.

## Operation replay ledger [ours; source-checked]

| input | transformation | assumption | output | exact source location | replay status |
|---|---|---|---|---|---|
| `Upsilon,sigma` | dominant fixed points + factorization + SVD | full-rank fixed points | WTG bond | Eqs. 3–8, PDF pp. 3–4 | matched |
| WTG transfer spectrum | normalize absolute eigenvalues | selected bond/environment | `S_cycle` | Eq. 11, PDF p. 5 | matched |
| WTG with `S_cycle=0` | discard small WTG coefficients | bridge realization exists | optimal Schmidt truncation | Sec. IV, PDF p. 5 | matched |
| bond with `S_cycle!=0` | alternate `u`/`R` and `v`/`L` updates | environment computable | FET local optimum candidate | Sec. V, PDF p. 6 | matched |
| WTG spectrum on arbitrary loop | label small modes “gauge” | none in paper | physical-vs-redundant classifier | no source location | unsupported |
| FET/WTG state objective | infer full QEC record/LER error | no global cq-state bound | record-faithful truncation | no source location | unsupported |

## Relevance to AI_QEC [ours]

The source forces a correction to `HANDOFF_fet_solver_longrange_2026-07-11.md`: WTG is a gauge and a
safe direct truncation only in the zero/low-cycle regime; it does not replace FET on the very loopy bonds
that motivated the handoff. Sokolov's later ZMT may improve initialization and exactly remove true zero
modes, but it too is followed by variational optimization and has no QEC record theorem. The scientifically
defensible pipeline is `diagnose loop structure -> use exact-zero/WTG only where licensed -> FET/ZMT+
variational refinement otherwise -> certify the full d3 record against the exact instrument`.

## How to use / trust + open questions [ours]

- **Trust:** high for WTG/FET definitions and explicit validity boundaries; formula/table pages were
  visually checked.
- **Closed by this source:** WTG construction and assumptions; physical-vs-internal correlation
  distinction; `S_cycle`; iterative FET objective.
- **Contradicted:** deterministic top-WTG global-optimum replacement for general loopy bonds.
- **Missing:** finite-environment error propagation, multi-time measured-circuit behavior, and any
  bound to full-record TV or rare LER.
- **Cross-source status:** the long-range truncation claim remains open pending an exact cq-record
  certificate or d3 oracle comparison.
