# GCAPEPS implementation–theorem correspondence

Date: 2026-07-28

Status: `SCOPED_ENGINEERING_GREEN__GENERIC_EQUIVALENCE_OPEN`

Scope: bind the frozen GCAPEPS mathematical-feasibility theorem to two distinct
implementations, record the executable construction witnesses added to the
Quimb fork, and state the exact boundary beyond which no implementation or
scientific claim is licensed.

This is a dated addendum. It does not amend the frozen theorem and does not turn
engineering tests into a proof.

## 1. Decision

The repository now contains two implementations with different responsibilities:

1. The registered parent service in `src/error_coupling_simulator/carrier/capeps/`
   still applies nonlocal coherent Pauli sums by an untruncated global virtual
   direct sum. It also implements exact one-site and adjacent-two-site Clifford
   refactors.
2. The experimental Quimb fork in `external/forks/quimb-gcapeps` now uses the
   tree-routed coherent PEPO construction as its production residual-update path.
   It measures Eqs. (9), (11), (16), and the PEPO-only Eq. (17) resource product,
   but it does not implement the paired Theorem-2 refactor.

Therefore theorem §10 item 9 remains accurate for the registered parent service
and is no longer accurate for the fork. The theorem remains frozen; this
commit-pinned addendum records the split.

The strongest justified fork statement is:

> The fork implements the untruncated tree construction with structural ledgers,
> performs a same-IR dense state-action check for every production update at
> most 10 qubits, and has one finite two-qubit full-basis reconstruction fixture.

It is not justified to replace that statement with generic operator equivalence,
certified PEPS contraction, finite-bond correctness, or efficiency.

## 2. Pinned artifacts

### 2.1 Frozen theorem

| artifact | path or ref | binding |
|---|---|---|
| feasibility theorem | `docs/simulator_validation/GCAPEPS_MATHEMATICAL_FEASIBILITY_THEOREM_2026-07-27.md` | SHA-256 `7f5ec9c7c3dac2da7c377c0958f7eafc104d2da19b59350e1a7c336cc1cc10dc` |
| independent review | `docs/simulator_validation/GCAPEPS_MATHEMATICAL_FEASIBILITY_INDEPENDENT_REVIEW_2026-07-27.md` | theorem hash binding remains intact |

The theorem hash was recomputed on 2026-07-28 after the fork changes. It is
unchanged.

### 2.2 Quimb fork

| field | value |
|---|---|
| repository | `https://github.com/cxMoonGlade/quimb` |
| branch | `gcapeps-carrier` |
| commit | `12838e4e1d32abb619c607d71ac3393018ce7b56` |
| commit subject | `Close GCAPEPS construction correspondence gaps` |
| push | confirmed on `origin/gcapeps-carrier` on 2026-07-28 |
| package | `quimb/experimental/gcapeps/` |

All fork statements below are statements about that exact commit.

### 2.3 Parent implementation baseline

The parent implementation and service registry were inspected at source commit
`fad86a9929442b22fd3d073ae261408ae6680ad3`. The correspondence update changes no
`src/**` file. The relevant binding sources are:

- `docs/service_status.json`, service `clifford_augmented_peps_prototype`;
- `src/error_coupling_simulator/carrier/capeps/README.md`;
- `CAPEPSState.refactor_residual_clifford`;
- `QuimbPepsResidual.apply_pauli_sum` and `apply_local_clifford`;
- `tests/test_capeps_gcamps_formulas.py`.

## 3. Top-down correspondence

Verdict vocabulary:

- `STRUCTURAL_LEDGER_ENFORCED`: the validator independently recomputes the
  structural formula and refuses before parent commit on disagreement.
- `SOURCE_CONSTRUCTION`: the tensor assembly visibly implements the stated
  formula, but the structural validator does not inspect tensor elements.
- `STATE_ACTION_EXACT_SMALL`: one production update on its current residual state
  is compared with a complete dense vector at the stated ceiling.
- `BASIS_FIXTURE_EXACT_SMALL`: one finite fixture reconstructs all matrix columns
  from basis-state actions.
- `TRACEABILITY_ONLY`: a test marker prevents silent loss of a named witness but
  does not prove its theorem clause.
- `OPEN`: not established by the implementation or acceptance evidence.

| theorem or project clause | fork witness at `12838e4e` | verdict |
|---|---|---|
| Lemma 3 copy tensor and three reviewed repairs | `_local_pepo_block`, finite repair fixtures, and current-state action checks through 10 qubits | `SOURCE_CONSTRUCTION` plus finite fixtures; generic value-level correctness `OPEN` |
| Lemma 3 operator equality | two-qubit full-basis reconstruction against `CoherentPauliSum.to_dense()` | `BASIS_FIXTURE_EXACT_SMALL`; generic statement `OPEN` |
| Lemma 3 / Eq. (9), tree PEPO bond rank | per-edge `operator_bond` and `pepo_rank_factor` recomputed from active rank and tree membership | `STRUCTURAL_LEDGER_ENFORCED` |
| Lemma 3 tree validity | graph membership, connectedness, acyclicity, terminals, and deterministic route recomputed | `STRUCTURAL_LEDGER_ENFORCED` |
| Lemma 4 / Eq. (11) | measured `state_bond_after = state_bond_before * operator_bond` without compression | `STRUCTURAL_LEDGER_ENFORCED` |
| Theorem 1 / Eq. (13) | implementation routes the tighter dependence set `W`; see §5 | structural Lemma-3 bound on the measured `W` tree, not a direct measured `W_U` ledger |
| Corollary 1 / Eq. (16) | Pauli rotation has active rank at most two and measured tree-edge growth | `STRUCTURAL_LEDGER_ENFORCED` |
| Corollary 2 / Eq. (17) | persistent PEPO-only product per edge | `STRUCTURAL_LEDGER_ENFORCED` |
| Project gauge layout | `g_new = kron(g_old, ones(r))`, old-bond index before term label | `STRUCTURAL_LEDGER_ENFORCED` plus asymmetric fixture |
| Theorem 2 / Eqs. (18), (19), and (21) | no nonidentity refactor constructor or `rho(Q)` witness in the fork | `OPEN` |
| Generic PEPS contraction or truncation certificate | none | `OPEN` |
| Complete measurement–reset–Record law | none | `OPEN` |

## 4. The three resource accounts

The Eq. (17) quantity remains PEPO-only. It was not silently redefined when the
future refactor column was introduced.

For each PEPS edge `e` and update step:

\[
f_e^{\mathrm{PEPO}} =
\begin{cases}
r, & e\in E(T),\\
1, & e\notin E(T),
\end{cases}
\]

\[
P_e^{\mathrm{PEPO},+}
=
P_e^{\mathrm{PEPO},-}f_e^{\mathrm{PEPO}}.
\]

The separately named refactor account is

\[
P_e^{\mathrm{ref},+}
=
P_e^{\mathrm{ref},-}f_e^{\mathrm{ref}}.
\]

The current tree lowerer has no nonidentity refactor and enforces

\[
f_e^{\mathrm{ref}}=1.
\]

The combined resource account is

\[
P_e^{\mathrm{total},+}
=
P_e^{\mathrm{total},-}
 f_e^{\mathrm{PEPO}} f_e^{\mathrm{ref}}
=
P_e^{\mathrm{PEPO},+}P_e^{\mathrm{ref},+}.
\]

`EdgeBondUpdate` records all factors and before/after products. The validator
rejects booleans, non-positive integers, wrong priors, wrong factors, inconsistent
split totals, and policy overflow. `max_routed_rank_product` guards Eq. (17)
without changing its meaning; `max_total_bond_growth_product` is a separate guard.

This closes the sequencing hazard in which a future refactor could otherwise be
added before its resource factor. It does not implement or accept that refactor.

The carrier also freezes independent prior snapshots. The lowerer receives
copies; the validator binds snapshots that the lowerer never receives; parent
state and ledgers change only after all checks pass. Regression mutants that
change the supplied priors to 97 and 89 either raise atomically or are rejected
when they return a self-consistent forged lowering.

## 5. Tight dependence set `W` versus safe support `W_U`

The implementation records two distinct sets:

\[
W
=
\{v: O_v^{(\alpha)} \text{ differs across active terms}\},
\]

and

\[
W_U
=
\bigcup_\alpha \operatorname{supp}(\widetilde P_\alpha).
\]

The tree lowerer routes terminals from the tighter set `W`, as licensed by
Lemma 3. Theorem 1 states its conservative existence bound using `W_U`.
Because `W \subseteq W_U`, both statements can be correct while describing
different trees.

Consequently the measured fork ledger must be described as the Lemma-3 `W`-tree
ledger. It must not be described without qualification as a measured Eq. (13)
`W_U` construction.

## 6. Numerical state-action evidence

For every production tree lowering with `n <= 10`, the carrier forms

\[
\psi_{\mathrm{reference}}
=
O_{\mathrm{dense}}\psi_{\mathrm{before}}
\]

and compares it with the complete post-lowering PEPS vector
`psi_candidate` before commit. The comparison is sensitive to phase, norm, and
every amplitude; fidelity is not used as a substitute.

To avoid falsely rejecting a valid near-zero result produced by coherent
cancellation, the tolerance uses input-side backward scales:

\[
B_\infty
=
\left(\sum_\alpha |c_\alpha|\right)
\lVert\psi_{\mathrm{before}}\rVert_\infty,
\]

\[
B_2
=
\left(\sum_\alpha |c_\alpha|\right)
\lVert\psi_{\mathrm{before}}\rVert_2.
\]

With

\[
k=\max(1,n,r),
\]

the numerical policy is

\[
\tau_\infty=512\,\epsilon_{64}\,k B_\infty,
\qquad
\tau_2=512\,\epsilon_{64}\,k B_2.
\]

The update records both errors, both scales, both allowed values, the formula,
complex128 precision, and
`independence_class = same_ir_not_an_independent_oracle`.

This is a numerical policy, not a theorem for approximate PEPS contraction. It
uses the same `CoherentPauliSum` IR to build the dense reference, so it cannot
independently validate that IR, the Pauli convention, or `to_dense()`.

At `n > 10`, the update explicitly records
`not_checked_above_exact_small_ceiling`; only the structural validator remains.
No generic semantic certificate is inferred.

A separate two-qubit test applies the implemented update to all four
computational-basis inputs, stacks the four output columns, and compares the
resulting matrix with the dense operator. That is a real full-basis check for one
finite fixture. It is not a proof for arbitrary graph, bond dimension, gauge, or
system size.

## 7. Gauge fusion convention

The routed gauge rule is

\[
g_e^{\prime}(i,\alpha)=g_e(i),
\qquad
g_e^{\prime}=g_e\otimes\mathbf 1_r.
\]

The named fused layout is `(old_bond, term_label)`, with the term label varying
fastest. A pairwise-distinct fixture uses

\[
g_e=[2,5],\qquad r=2,
\]

and requires

\[
[2,2,5,5]
\]

rather than the reversed-layout result

\[
[2,5,2,5].
\]

The fixture also passes the current-state dense action check. This closes the
previously underdetermined symmetric-fixture problem. It does not create a PEPS
canonical form or environment certificate.

## 8. Test-to-clause traceability

`tests/test_experimental/conftest.py` declares the required implemented-clause
set and registers `gcapeps_clause(name)`. During a complete experimental
collection, collection fails if any required clause has no witness or if a test
uses an unknown clause. A focused single-node run is deliberately allowed and
does not require unrelated witnesses.

The declared set covers Lemma-3 repairs and tree validity, Eqs. (9) and (11),
Theorem-1 structural accounting, and Eqs. (16) and (17). The operator-equality
marker is now attached only to the finite full-basis reconstruction test, not to
a single-state production check.

Marker coverage is a maintenance and traceability contract. It is not proof that
the marked mathematical statement holds generically.

## 9. Two-implementation responsibility table

| responsibility | registered parent `carrier/capeps` | fork `quimb.experimental.gcapeps` |
|---|---|---|
| hybrid invariant `C|phi>` | implemented | implemented |
| Clifford frame-only update and signed pullback | implemented with Stim default | implemented with Stim and explicit SDIM seam |
| nonlocal coherent residual update | untruncated global direct sum | untruncated tree-routed PEPO |
| Eq. (9)/(11) tree ledger | absent | implemented and validated |
| Eq. (16)/(17) tree resource ledger | absent | implemented; Eq. (17) remains PEPO-only |
| exact one-site refactor | implemented | absent |
| exact adjacent-two-site refactor | implemented | absent |
| Theorem-2 `rho(Q)` resource witness | absent | absent |
| finite-bond optimizer or truncation certificate | absent | absent |
| canonical complete Record | absent; raw conditional branch ledger only | absent; exact-small frame-free branch mechanics only |
| qutrit/leakage carrier | absent | absent |

The parent refactor is an exact local implementation path, but it does not by
itself provide the fork with Theorem-2 construction evidence or a `rho(Q)`
resource certificate. The two implementations are complementary, not yet one
accepted combined carrier.

## 10. Gap disposition

| gap | disposition at fork commit `12838e4e` |
|---|---|
| G1: tensor amplitudes absent from structural validator | `PARTIALLY_CLOSED_EXACT_SMALL`: state action for every production update through 10 qubits plus one finite full-basis fixture; generic equality remains open |
| G2: no theorem-clause test mapping | `CLOSED_TRACEABILITY_ONLY`: collection contract added; proof status unchanged |
| G3: PEPO ledger would miss a future refactor factor | `CLOSED_AS_SEQUENCING_GUARD`: PEPO, refactor, and total accounts separated; nonidentity refactor remains open |
| G4: gauge fusion layout unnamed and fixture symmetric | `CLOSED_CHARACTERIZATION_FIXTURE`: asymmetric `[2,5]` fixture locks the convention |
| G5: Theorem-2 refactor absent from fork | `OPEN` |
| G6: frozen theorem §10 item 9 differs across implementations | `CLOSED_BY_DATED_ADDENDUM`: theorem unchanged, responsibility split recorded here |
| caller-owned prior mutation | `CLOSED`: independent snapshots plus mutate-and-raise and mutate-and-return regressions |
| cancellation-sensitive output-scaled tolerance | `CLOSED_FOR_CURRENT_NUMERICAL_POLICY`: backward scales added; no generic contraction theorem claimed |

## 11. Four evidence ledgers

### 11.1 Implemented

- tree-routed PEPO construction and structural validator;
- clause-tag collection contract;
- exact-small current-state action evidence with explicit 10-qubit ceiling;
- finite two-qubit full-basis reconstruction fixture;
- PEPO-only, refactor-only, and combined bond-growth accounts;
- total-growth preflight guard;
- asymmetric gauge-layout fixture;
- parent-ledger snapshot isolation;
- cancellation-stable numerical comparison policy;
- documentation that keeps Theorem 2 and generic correctness open.

### 11.2 Focused engineering evidence

All results below were rerun from clean fork commit
`12838e4e1d32abb619c607d71ac3393018ce7b56`:

- GCAPEPS scoped ordinary suite: `97 passed`, one optional `kahypar` warning;
- complete experimental collection: `97 tests collected`, clause gate passed;
- isolated `gcapeps-sdim` live suite: `9 passed`;
- Ruff import check: passed using the fork `.pixi/envs/docs/bin/ruff`;
- Ruff format check: passed using the same fork Pixi tool, not the `ecs`
  environment;
- Python compilation check: passed;
- scoped package coverage: `1768` statements, `339` missed, `81%` total;
  `carrier.py` 90%, `pepo.py` 84%, `resources.py` 96%.

The coverage number is a code-execution diagnostic, not a scientific metric.

### 11.3 Scientific evidence

- the feasibility theorem remains hash-identical to its reviewed artifact;
- the fork gives executable structural witnesses for the untruncated tree
  construction;
- exact-small action and finite-basis evidence can falsify concrete numerical
  implementation defects;
- none of these artifacts supplies a generic a posteriori PEPS contraction
  certificate or upgrades the theorem beyond representation feasibility.

Scientific acceptance remains bounded by the theorem and by the explicit `OPEN`
rows above.

### 11.4 Release evidence

- fork commit pushed to `origin/gcapeps-carrier`: confirmed;
- full upstream Quimb test suite: not run;
- remote CI: not inspected in this packet;
- parent ECS fresh-process aggregate acceptance: not run;
- package release or production registration: not performed.

Therefore the scoped engineering checkpoint is green; an upstream or product
release is not declared green.

## 12. Claims still forbidden

This packet does not establish any of the following:

- GCAPEPS is faster than ordinary PEPS or MPS;
- its bond dimension remains small;
- generic exact or approximate PEPS contraction is efficient or certified;
- truncation preserves state, observables, measurements, or complete Record;
- a disentangler objective is globally well defined or convergent in 2D;
- non-Markovian or cross-round Record semantics are accepted;
- the fork implements Theorem-2 paired refactoring;
- the parent and fork paths are one equivalence-tested combined carrier;
- SDIM supplies prime-d qutrit residual evolution;
- leakage qutrits, composite-d tableaus, or qutrit GCAPEPS are implemented;
- the same-IR dense state-action check is an independent oracle;
- finite fixtures prove arbitrary-size operator equality.

## 13. Next implementation gates

1. Before any nonidentity fork refactor, add a dedicated constructor and
   validator that records a certified `rho(Q)` factor and updates only the
   refactor and total accounts.
2. Keep the PEPO Eq. (17) account unchanged and independently guarded.
3. If stronger exact-small operator evidence is needed, construct a dense PEPO,
   Choi matrix, or explicitly bounded full-basis reconstruction independent of
   the current residual state and record the exact ceiling.
4. Treat every result above the dense ceiling as structurally checked and
   semantically uncertified unless an independently justified conditional
   contraction class is added.
5. Integrate the parent local-refactor path and the fork tree path only behind an
   explicit equivalence and transaction contract; do not infer compatibility
   from the two separate implementations.
