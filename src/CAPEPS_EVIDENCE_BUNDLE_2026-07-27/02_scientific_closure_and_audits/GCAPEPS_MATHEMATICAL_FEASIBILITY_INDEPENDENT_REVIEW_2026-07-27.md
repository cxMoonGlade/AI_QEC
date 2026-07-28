# GCAPEPS mathematical-feasibility theorem — independent review report

Date: 2026-07-27

Decision: **PASS**

Final reviewed theorem packet:
`docs/simulator_validation/GCAPEPS_MATHEMATICAL_FEASIBILITY_THEOREM_2026-07-27.md`

Final reviewed SHA-256:
`7f5ec9c7c3dac2da7c377c0958f7eafc104d2da19b59350e1a7c336cc1cc10dc`

Review scope: exact finite-lattice mathematical correctness, source/project
attribution, worst-case PEPO/PEPS bond bounds, tightness examples, and explicit
nonclaims. No claim of novelty, efficiency, implementation equivalence, or QEC
Record correctness was reviewed or granted.

## 1. Independent angles

Three independent reviewer roles examined the argument without editing the
theorem packet:

1. **GCAMPS-to-GCAPEPS translation reviewer.** Checked which statements are
   printed in arXiv:2511.06672v2 and arXiv:2605.29514v1, which steps are project
   formalizations, and which MPS-specific conclusions cannot transfer to PEPS.
2. **Tensor-network closure reviewer.** Reconstructed the product-sum PEPO,
   PEPO-on-PEPS fusion, per-edge bond bounds, sequence bound, refactor bound,
   and finite-grid universality proof.
3. **Adversarial mathematical reviewer.** Searched for counterexamples in the
   routing construction, root constraints, degenerate topology, active-set
   definition, tightness examples, and implementation/efficiency overclaims.

The tensor-network and adversarial reviewers independently performed strict
post-repair rereviews. Both returned `PASS` on theorem SHA
`94a80d4e9d0362a86d7e02b145d0d914300e2a091e70bd62db56e5010789a801`.
The adversarial reviewer then verified the final artifact SHA above after the
status line and the Eq. (17) refactor-scope clarification were added, and again
returned `PASS`.

## 2. Initial failure and concrete counterexample

The initial draft did **not** pass. All three angles identified the same real
defect in Lemma 3.

For

\[
O=A_1\otimes X_2\otimes B_3+C_1\otimes X_2\otimes D_3,
\]

the dependence set is \(W=\{1,3\}\), but the middle routing vertex carries the
common nonidentity factor \(X_2\). The initial construction incorrectly put an
identity there. The initial root wording also failed to require an equality-copy
constraint at a root of degree greater than one, allowing cross-label terms, and
it omitted the single-vertex-tree construction.

Admission was therefore blocked until the proof was repaired. A syntactically
valid document or plausible high-level identity was not treated as a proof.

## 3. Repairs verified

The final packet was checked to contain all of the following repairs:

1. Every \(v\notin W\) has an explicitly named common local factor \(B_v\),
   retained both on routing vertices and outside the tree.
2. Every tree vertex, including the root, enforces equality of all incident
   term labels; the root only adds the coefficient \(c_\alpha\).
3. A single-vertex tree directly uses
   \(\sum_\alpha c_\alpha O_{\rm root}^{(\alpha)}\); the empty-dependence case
   is covered.
4. The main theorem uses the safe active set
   \(W_U=\bigcup_\alpha\operatorname{supp}(\widetilde P_\alpha)\).
5. The theorem assumes a nonzero represented state and a physical unitary
   update; the Pauli-rotation corollary assumes a nonidentity Pauli.
6. The source's Pauli-expansion/commute-through instruction is separated from
   the project's signed pullback, term-count, PEPO, and PEPS-bond derivations.
7. The routed-tree bound is explicitly not claimed to be the current prototype's
   global-direct-sum behavior.

## 4. Final mathematical checklist

| statement | final verdict |
|---|---|
| \((C,A)\mapsto(FC,A)\) for a physical Clifford \(F\) | `PASS` |
| Clifford conjugation is a phase-decorated Pauli-basis permutation and preserves the nonzero term count \(r\) | `PASS` |
| a \(k\)-site qudit operator has \(r\le d^{2k}\) Pauli-basis terms | `PASS` |
| repaired tree-routed product-sum PEPO has \(R_e\le r\) on tree edges and \(R_e=1\) elsewhere | `PASS` |
| exact PEPO action gives \(D'_e\le D_eR_e\) | `PASS` |
| main bound \(D'_e\le rD_e\) on routed edges | `PASS` as a construction bound, not a minimum |
| qubit nonidentity Pauli rotation has \(r\le2\) | `PASS` |
| GHZ-type example can attain Schmidt-rank factor two | `PASS` |
| paired refactor \((C,A)\mapsto(CQ^\dagger,A_Q)\) preserves the physical state | `PASS` |
| adjacent two-site refactor satisfies \(D'_e\le\rho(Q)D_e\le d^2D_e\) | `PASS` |
| Bell-pair plus middle-SWAP example attains the \(d^2\) safety factor | `PASS` |
| sequence product bound Eq. (17) | `PASS`; nonidentity refactor factors are separate, while \(Q=I\) preserves the stated bound |
| snake-path MPS embedding proves finite rectangular-grid PEPS universality | `PASS` |

The display-math delimiter check on the final packet reports 26 opening and 26
closing display delimiters.

## 5. What this PASS authorizes

The reviewed mathematical conclusion is exactly:

> On a finite connected lattice, exact untruncated GCAPEPS is a well-defined
> GCAMPS-compatible representation. A pulled-back \(r\)-term Pauli-product sum
> admits a tree-routed PEPO, and applying it to a residual PEPS yields the
> explicit per-edge construction bound \(D'_e\le rD_e\) on routed edges.

This PASS does not authorize any of the following:

- polynomial or low residual bond;
- efficient PEPS contraction or optimization;
- a useful or optimal Clifford disentangler;
- truncation-fidelity guarantees;
- runtime or memory advantage over full PEPS;
- a first-ever PEPS suggestion or field-wide novelty claim;
- equality with the current global-direct-sum prototype implementation;
- measurement--reset--Record or QEC correctness.

The result is sufficient for the user's narrowed mathematical-feasibility goal.
It is best positioned as a constructive finite-lattice theorem, potentially the
core of a short technical note or a methods section, rather than as an efficiency
result.

## 6. Mutation boundary

No `src/**` file, corpus manifest, literature note, or source PDF was modified by
the independent reviewers. The review concerns only the theorem packet at the
exact final hash above.
