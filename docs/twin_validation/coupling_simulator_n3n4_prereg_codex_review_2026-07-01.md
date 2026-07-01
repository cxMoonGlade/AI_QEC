# Codex review — coupling simulator n=3-4 pre-registration

**Date:** 2026-07-01  
**Reviewed object:** `docs/twin_validation/coupling_simulator_n3n4_prereg.md`  
**Mode:** read-only critical review, theory-first / claim-contract stance.  
**Verdict:** do **not** build yet. Close two theory gates first; then the pre-registration is close to runnable.

## Executive Summary

The pre-registration is scientifically much closer to the right shape than the previous architecture
synthesis: it frames the work as a **forward coupling simulator, not a twin**; it absorbs the Gaussian
scope decision; it uses a layered metric stack instead of the contradictory phrase "coherence-sensitive
Delta LER"; and it correctly treats the n=2/N=1 pilot as a narrow embedding + oracle-methodology
success, not as a validated cross-qubit correlated teacher.

The remaining blockers are not implementation details. They are contract gates:

1. The pre-registration uses the 2506.10308 Eq. 8 SDP as if the scalar/vector construction already covers
   a matrix-valued MIMO BCF. The local grounding does not yet prove that.
2. The primary multi-qubit closed-form independent-boson oracle is asserted as exact before the derivation
   exists.

Those two gates should be closed before installing dependencies or writing the n=3-4 prototype.

## Findings

### P0 — Matrix-BCF SDP construction is under-derived

**Location:** `coupling_simulator_n3n4_prereg.md:31-35`  
**Severity:** P0

The pre-registration says the n=3-4 matrix BCF will be fit by the paper's Loewner/SDP construction:

```text
min_{Y>0} ||l - Y r||^2 s.t. i(Y Lambda - Lambda^\dagger Y) >= 0
```

and then uses `X=sqrt(Y)`, `K=X Lambda X^-1`, `g=Xr`.

This is directly grounded for the scalar/vector BCF representation in the 2506.10308 reading note:

- `coupled_lindblad_pseudomode_2506.10308.md:179-194` gives Eq. 8 with vector `l,r`.
- `coupled_lindblad_pseudomode_2506.10308.md:196-208` states the feasibility condition in that same vector
  form.

The multi-qubit section is separate:

- `coupled_lindblad_pseudomode_2506.10308.md:210-234` says the multi-site BCF becomes a matrix
  `C^c(t)=g^\dagger exp(-iKt)g`, with `g in C^{N x n}`.

What is missing is the bridge: how Eq. 8 is lifted to a matrix-valued / MIMO realization. The prereg needs
to state whether the build will use:

- a MIMO Loewner realization directly;
- a block-stacked scalar realization;
- a shared-`K` per-entry construction with a common gauge;
- or another construction from the paper's supplementary material.

**Required fix before build:** add a theory-first derivation of the matrix-BCF SDP dimensions and constraints.
The derivation must identify the shapes of `l`, `r`, `Y`, `K`, and `g`, and prove that the resulting
`Gamma=(K^\dagger-K)/(2i)` remains positive semidefinite while reproducing the matrix BCF.

Until this is closed, `cvxpy` installation is premature.

### P0 — Primary closed-form oracle is asserted before derivation

**Location:** `coupling_simulator_n3n4_prereg.md:58-61`, `112`, `137-139`  
**Severity:** P0

The pre-registration states the multi-qubit independent-boson oracle as:

```text
exp(-sum_ij (s_a-s_b)_i (s_a-s_b)_j Gamma_ij(t))
```

and then uses it as the class-(a) primary oracle and C3 theorem-grade constraint.

The user already flagged the problem: this oracle has not yet been derived. I agree that this is blocking.
The formula is the natural Gaussian cumulant generalization, but in this project it cannot function as a
Rule-I oracle until it is hand-derived from the bare system-bath Hamiltonian.

**Required fix before build:** downgrade the oracle in the prereg to `PENDING-THEOREM` and add a pre-build
theory task:

1. Start from the bare Hamiltonian `H_SB = sum_i Z_i B_i`, not from pseudomode `K,g,Gamma`.
2. Derive the coherence between computational basis states `|a>` and `|b>` using the Gaussian cumulant /
   independent-boson route.
3. Define `Gamma_ij(t)` directly from the matrix BCF.
4. Check reductions:
   - n=1 single-qubit limit;
   - n=2 rank-1 collective limit from the v1 pilot;
   - diagonal/private-bath limit where off-diagonal terms vanish;
   - sign/factor convention for `(Delta s_i)(Delta s_j)`.

Only after that derivation should C3 be labeled `(a)`.

### P1 — Non-Gaussian "must fail" boundary should not block the Gaussian rung

**Location:** `coupling_simulator_n3n4_prereg.md:66-68`, `89-93`, `119-126`  
**Severity:** P1

The non-Gaussian boundary gate is a good architecture decision, but the acceptance gate currently requires
that it fail as predicted before the Gaussian rung can pass.

That is too strong. The Gaussian n=3-4 rung is supposed to certify the Gaussian / Lorentzian-sum simulator.
An out-of-scope explicit-TLS boundary experiment should characterize the scope boundary, not block progress
on the Gaussian carrier.

There is also a scientific issue with "MUST FAIL": a weak-TLS or many-TLS limit may be well approximated by a
Gaussian BCF model. If the Gaussian carrier matches an explicit TLS in some regime, that is a finding about
scope, not a failure of the Gaussian rung.

**Recommended fix:** remove the non-Gaussian boundary as a required PASS conjunct in `§7`. Keep it as a
separate boundary characterization:

- fail strongly: confirms a non-Gaussian blind spot;
- match in a controlled regime: widens the empirically valid scope;
- ambiguous / unbounded discrepancy: stop hardware-faithfulness claims for that regime.

### P1 — `%Delta LER coupled-vs-factorized` is not yet the ledgered same-process metric

**Location:** `coupling_simulator_n3n4_prereg.md:53-55`  
**Severity:** P1

The prereg defines the deferred decoder value as:

```text
same decoder on records from the coupled simulator vs a matched-marginal factorized simulator
```

That is a meaningful simulator comparison, but it is not exactly the ledgered same-process
PT-aware-vs-Markov decoder comparison.

`docs/METRICS.md:187` defines `%Delta LER` as decoder-prior utility under the same decoder, same held-out
shots, and named priors/baselines. The non-Markovian layered section also says the decoder layer is a
PT-aware-vs-Markov decoder on the **same process** (`docs/METRICS.md:303-304`).

**Recommended fix:** choose one and name it precisely:

- If the code-scale value is coupled simulator vs matched-marginal factorized simulator, call it
  `LER_model_gap` or `factorization_penalty`, not ledgered `%Delta LER`.
- If the code-scale value is the ledgered metric, define it as PT-aware decoder vs Markov/factorized decoder
  on the same coupled process, with held-out NLL and frozen decoder conventions.

### P1 — BLP/RHP implementation text still relies on scalar shortcuts

**Location:** `coupling_simulator_n3n4_prereg.md:45-49`, `74-84`, `114-115`  
**Severity:** P1

The metric choice is correct, and `docs/METRICS.md:295-321` now gives a good source-layer ledger. But the
pre-reg still phrases the operation in scalar pure-dephasing terms.

The BLP reading note says the pure-dephasing shortcut is known for dephasing, while the matrix/multi-qubit
case needs the pair search redone:

- `blp_nonmarkovianity_measure_0908.0238.md:66-78`

The RHP note says the pure-dephasing closed form is direct, but the general/matrix case requires
intermediate-map reconstruction:

- `rhp_nonmarkovianity_measure_0911.4270.md:62-75`

**Recommended fix:** split the metric implementation into:

- selected-coherence lower-bound witness for quick falsification;
- actual BLP estimate with declared initial-pair search;
- actual RHP estimate from reconstructed intermediate maps, with invertibility caveat.

Do not state `RHP I > 0 iff negative TCL rate` as the general matrix-BCF constraint unless the map is still in
a proven pure-dephasing commuting class where the TCL-rate reduction is derived.

### P2 — "Best factorized approximation" needs a predeclared model class and objective

**Location:** `coupling_simulator_n3n4_prereg.md:50-52`  
**Severity:** P2

The channel-layer proxy compares the coupled channel against its "BEST FACTORIZED" approximation. This is
underspecified.

"Best" could mean:

- matched one-qubit marginal BCFs;
- product of per-qubit reduced channels;
- minimizer of `D_Choi`;
- minimizer of `1-F_e`;
- minimizer of Pauli-twirl distance;
- likelihood/NLL fit on emitted observations.

These need not agree.

**Recommended fix:** predeclare the factorized model family and the fitting objective. A clean version would be:

```text
Factorized baseline = tensor product of per-qubit Gaussian pseudomode channels with BCFs set to the diagonal
C_ii(t), i.e. all off-diagonal C_ij(t) zeroed. Score D_Choi and 1-F_e after this fixed construction.
```

If you want the true optimum over a factorized class, declare the optimization objective and solver.

## What Holds Up

- The simulator-not-twin framing is clean and important.
- The n=2/N=1 tautology boundary is stated sharply.
- Dense-`Gamma` jump-operator eigendecomposition is the right implementation seam for leaving the N=1 pilot.
- Gaussian scope + explicit non-Gaussian boundary is the right architecture choice.
- The layered stack solves the "coherence-sensitive Delta LER" confusion in the right direction.
- The prereg correctly defers code-scale decoder value and JC/amplitude-damping RWA cost.

## Required Pre-Build Checklist

Before any n=3-4 build:

1. Derive the matrix-BCF / MIMO SDP construction.
2. Derive the multi-qubit independent-boson closed-form oracle.
3. Move non-Gaussian explicit-TLS boundary out of the Gaussian rung PASS condition.
4. Rename or redefine the deferred decoder value metric so it matches `METRICS.md`.
5. Specify BLP/RHP implementation for matrix-BCF beyond scalar dephasing shortcuts.
6. Define the factorized baseline model class and fitting objective.

After those are done, this prereg is close to runnable.
