# GCAPEPS exact-tree versus Quimb-native forced truncation — formal result

Status: **PASS_BOUNDED_BRIDGE_TRANSIENT_TRUNCATION, 2026-07-29**

This is the formal result for
[GCAPEPS_NATIVE_FORCED_TRUNCATION_PREREG_2026-07-29.md](GCAPEPS_NATIVE_FORCED_TRUNCATION_PREREG_2026-07-29.md),
grounded by
[GCAPEPS_NATIVE_FORCED_TRUNCATION_LITERATURE_CLOSURE_2026-07-29.md](GCAPEPS_NATIVE_FORCED_TRUNCATION_LITERATURE_CLOSURE_2026-07-29.md).
It is bounded two-site, exact-small state-action evidence. It is not canonical
ECS Carrier or Record acceptance.

## 1. Result

On the frozen two-site bridge, the exact tree-PEPO lane and the untruncated
Quimb-native compilation agree with the independent dense anchor. Applying
`max_bond=1` after each native two-site gate discards the preregistered positive
transient Schmidt component and produces the complete-state error predicted
before execution, even though the final exact physical state has rank one and
fits bond dimension one.

The verdict is therefore:

```text
PASS_BOUNDED_BRIDGE_TRANSIENT_TRUNCATION
```

The allowed conclusion is only:

> For this frozen two-site bridge, untruncated Quimb-native compilation agrees
> with exact tree-PEPO state action, while per-gate `max_bond=1` discards a
> nonzero transient Schmidt component and produces the preregistered
> complete-state error even though the final exact state fits bond one.

## 2. Frozen identities and artifact boundary

| Object | Bound identity |
|---|---|
| Parent repository commit | `1e9517af31f83d174bcbdf656c1955f12227b605` |
| Parent repository tree | `17c17eb549d5f091263e7deaa86476d90420174b` |
| Quimb GCAPEPS fork commit | `e6cbe016f336843925e01a559db26f209fa9d37b` |
| Quimb GCAPEPS fork tree | `854ff4d5ef692497f017a57250cf8f440e47110f` |
| Result schema | `error_coupling_simulator.external.gcapeps_native_forced_truncation.v1` |
| Execution-time result path | `/tmp/gcapeps_native_forced_truncation_1e9517af31f83d174bcbdf656c1955f12227b605.json` |
| JSON byte SHA-256 | `55d428ceebb38aba91e1fbeb2e2a6d6f1b2f5da944534179ef2f583e4fa65ac7` |
| Canonical internal content SHA-256 | `73ca030b410b0bf60f6fc6a1e599064ec21a5c024c8ecfd28955e8f7ad934a58` |

The committed execution owners are
[run_gcapeps_native_forced_truncation.py](../../scripts/external_baselines/run_gcapeps_native_forced_truncation.py)
and the structurally independent NumPy-only
[gcapeps_forced_truncation_dense_anchor.py](../../scripts/external_baselines/gcapeps_forced_truncation_dense_anchor.py).
The parent and fork identities, tracked claim-source hashes, import origins,
and source hashes were revalidated after execution. All post-execution
repository, source, and import checks passed. Both repositories were clean at
the claim-bearing checkpoints; the fork's bounded ignored-file inventory was
recorded. `PYTHONPATH` was absent, state and gate values were NumPy
`complex128`, and no timing was collected.

The raw JSON is deliberately not committed. Its `/tmp` path is ephemeral and
may disappear. This document plus the byte and canonical-content hashes is the
durable audit record; reproducing or independently inspecting every raw field
requires a fresh run of the committed runner at the bound repository
identities. No claim of continuous repository immutability between
checkpoints is made.

## 3. Frozen fixture

The input and target were

\[
|\phi\rangle
=
\left(\frac{12}{13}|0\rangle+\frac{5}{13}|1\rangle\right)\otimes|0\rangle,
\qquad
U_{ZZ}=e^{-i(\pi/5)Z_0Z_1/2}.
\]

The native chronological path was

```text
CX 0 1
RZ(pi/5) 1
CX 0 1
```

with no state normalization, phase fitting, coordinate permutation, or dtype
cast in the verdict-driving complete-vector comparisons.

## 4. Complete-vector results

All values below are against the independent dense anchor. Here \(F\) is
normalized squared fidelity and \(D_{\rm tr}\) is normalized pure-state trace
distance.

| Lane | Policy / role | \(\|y\|_2\) | \(d_2\) | \(d_\infty\) | \(d_{\rm norm}\) | \(F\) | \(D_{\rm tr}\) |
|---|---|---:|---:|---:|---:|---:|---:|
| A | NumPy-only anchor | 1 | 0 | 0 | 0 | 1 | 0 |
| T | exact tree-PEPO | 1 | 0 | 0 | 0 | 1 | 0 |
| N0 | native, no cap, cutoff 0 | \(0.9999999999999997\) | \(3.787898901196402\times10^{-16}\) | \(3.376611507232129\times10^{-16}\) | \(3.3306690738754696\times10^{-16}\) | 1 | 0 |
| N1 | native, `max_bond=1`, cutoff 0 | \(12/13=0.923076923076923\) | \(5/13=0.38461538461538464\) | \(5/13\) | \(1/13=0.07692307692307698\) | \(144/169=0.8520710059171598\) | \(5/13\) |
| N2 | native, `max_bond=2`, cutoff 0 | \(0.9999999999999997\) | \(3.787898901196402\times10^{-16}\) | \(3.376611507232129\times10^{-16}\) | \(3.3306690738754696\times10^{-16}\) | 1 | 0 |
| D1 | direct literal \(U_{ZZ}\), `max_bond=1` | \(0.9999999999999997\) | \(3.787898901196402\times10^{-16}\) | \(3.376611507232129\times10^{-16}\) | \(3.3306690738754696\times10^{-16}\) | 1 | 0 |
| K0 | native, no cap, relative cutoff 0.4 | \(0.9999999999999997\) | \(3.787898901196402\times10^{-16}\) | \(3.376611507232129\times10^{-16}\) | \(3.3306690738754696\times10^{-16}\) | 1 | 0 |
| K1 | native, no cap, relative cutoff 0.5 | \(12/13=0.923076923076923\) | \(5/13=0.38461538461538464\) | \(5/13\) | \(1/13=0.07692307692307698\) | \(144/169=0.8520710059171598\) | \(5/13\) |

The exact tree lane T is bit-for-bit equal to the anchor vector in the emitted
representation. N0, N2, D1, and K0 differ only at floating roundoff scale. All
lane gates matched the preregistered numerical bands.

N1 and K1 produce the same complete vector, but their ledgers establish
different causes. Equal output is not evidence of equal truncation policy.

## 5. Split-level causal evidence

At N1's first native two-site split, the observed full and kept spectra were

\[
s_{\rm full}
=
\left(\frac{12}{13},\frac{5}{13}\right)
=
(0.9230769230769231,0.38461538461538464),
\qquad
s_{\rm kept}
=
\left(\frac{12}{13}\right).
\]

The ledger records:

| Field | N1 value |
|---|---:|
| gate role | `parity_compute_cnot` |
| cause | `max_bond` |
| configured cap | 1 |
| configured relative cutoff | 0 |
| kept bond dimension | 1 |
| discarded squared weight | \(25/169=0.14792899408284024\) |
| positive discarded weight | `true` |

K1 records the same positive discarded squared weight and final vector, but
with cause `cutoff`. D1 applies the final literal \(U_{ZZ}\) directly and
records no positive discarded weight. The final exact physical rank is one.
Together these controls locate the discrepancy at the decomposition's
intermediate split, rather than at final-state representability.

For this constructed fixture,
\((5/13)^2=25/169\) also equals the squared complete-vector error. That equality
is an exact-small property of this fixture, not a generic conversion from a
local PEPS discarded tail to a whole-state error bound.

## 6. Operator and corruption checks

Before interpreting the lossy lane, the untruncated native compiler was
checked on all four basis columns. The full-operator result passed with

\[
\|U_{\rm native}-U_{ZZ}\|_\infty
=1.2412670766236366\times10^{-16}.
\]

All preregistered corruption controls fired, including:

- moving the \(R_Z\) to the wrong site;
- flipping the signed angle;
- omitting the final CNOT;
- relabeling cutoff loss as cap-only loss;
- claiming positive cap loss for a lossless lane;
- changing a spectrum without recomputing its weight;
- relying on phase-blind fidelity while changing the raw vector;
- substituting a `complex64` candidate;
- applying a shared corruption to tree and native candidates; and
- retaining the wrong singular component.

The native plan, canonical transcript, execution ledger, and result were
digest-bound. The independent anchor did not execute candidate code and
imported no Quimb, Stim, SDIM, or GCAPEPS module.

## 7. Claim boundary

This result permits a bounded implementation statement and one
counterexample-style scientific observation:

- the committed two-site native Pauli-rotation path implements the frozen gate
  to exact-small precision when untruncated; and
- a final state that fits bond one can still be changed by a bond-one cap
  applied to an intermediate native decomposition.

It does **not** establish any of the following:

- generic PEPS truncation faithfulness or a global a posteriori contraction
  certificate;
- that a loopy local discarded tail bounds complete-state, observable,
  measurement, or Record error;
- accumulated multi-gate, cross-round, measurement/reset, or full Record-law
  correctness;
- runtime, memory, contraction, scaling, or GCAPEPS-over-PEPS performance
  advantage;
- qutrit, prime-\(d\), SDIM, composite-\(d\), or leakage correctness; or
- release-level acceptance of GCAPEPS as an ECS scientific Carrier.

The result is scoped scientific evidence, not release evidence. Larger and
loopy PEPS carriers, repeated rounds, non-Markovian memory, and Record-level
faithfulness remain separate experiments with separate preregistrations and
independent references.

## 8. Post-result theory-fix

Decision: **`ACCEPT_WITH_CLASS`**.

The accepted class is the one frozen before execution: a class-(a)
finite-dimensional bridge identity corroborated by class-(c) numerical and
software evidence. The result does not acquire a broader PEPS epistemic class.

| Wire | Result | Evidence |
|---|---|---|
| Full-configuration theorem/symmetry | survives | The exact \(U_{ZZ}\) action preserves the \(q_1=0\) product subspace, while the compiled CNOT path passes through the independently derived Schmidt pair \((12/13,5/13)\). The direct-gate control returns rank one without positive loss. |
| Formulation and measured object | survives | Dense \(U_{ZZ}\), exact tree-PEPO, native CNOT–\(R_Z\)–CNOT, full-operator reconstruction, and complete-vector metrics agree in the untruncated lanes. The local tail is used only to identify the split cause, never as a substitute for the complete-vector metric. |
| Independent reference | survives | The NumPy-only anchor imports no candidate implementation, the four-dimensional identity is hand derivable, and all four operator columns were checked. |
| Degenerate intervention | survives | N1 differs from N0 by \(d_2=5/13\), and its first split has `keep_by_cap=1`, `keep_by_cutoff=2`, and positive discarded weight \(25/169\). D1 shows that the same cap is lossless on the direct final gate. |
| Suppressing lens | survives within scope | The two-site bridge removes the loopy-environment ambiguity on purpose. That simplification makes this test interpretable but forbids promotion to loopy or multi-round PEPS. |
| Un-led reproduction | survives | A reviewer given the raw JSON and problem statement, but no expected numbers, independently recomputed its canonical content hash, plan transcript digest, complete-vector errors, fidelity/infidelity, split cause, and final rank. |
| Predict-before-measure | survives | The exact values, bands, lanes, kill conditions, and corruption controls were committed in the preregistration-only parent commit `595a9db` before the implementation commit and formal target execution; no band or headline observable was refit. |
| Propagation | survives | Current registry updates carry only the two-site transient-path statement and retain explicit prohibitions on global, loopy, Record, performance, and qutrit/SDIM/leakage claims. |

The local post-result literature query returned the already admitted Evenbly,
Rudolph–Tindall, and related PEPS truncation limitations. It exposed no new
load-bearing row for this finite bridge claim and reinforced the existing
loop/no-global-certificate boundary. No external acquisition was needed
because the reopened coverage ledger remained closed for exactly this scope.

The raw report does not embed the complete anchor payload, only its canonical
hash and the complete verdict-driving vectors. It also does not embed the Git
objects, source bytes, or the execution trace of each corruption control. The
un-led review can therefore verify the numerical result and internal
provenance consistency, but full offline regeneration of the anchor and
external commit/clean/corruption claims still requires the hash-bound sources
or a fresh run. This is a reproducibility boundary, not a contradiction of the
bounded result.
