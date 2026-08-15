# GCAPEPS: A GCAMPS-Style Clifford-Augmented PEPS Representation with Exact Finite-Lattice Closure

## GCAPEPS：具有有限格点精确闭包的 GCAMPS 式 Clifford-Augmented PEPS

Authors: `[names]`

Date: 2026-07-27

Manuscript status: `MATHEMATICAL_CORE_REVIEWED__CONSISTENCY_REVIEW_PASS`

The frozen mathematical packet is
[`GCAPEPS_MATHEMATICAL_FEASIBILITY_THEOREM_2026-07-27.md`](GCAPEPS_MATHEMATICAL_FEASIBILITY_THEOREM_2026-07-27.md),
SHA-256
`7f5ec9c7c3dac2da7c377c0958f7eafc104d2da19b59350e1a7c336cc1cc10dc`.
Its independent review is
[`GCAPEPS_MATHEMATICAL_FEASIBILITY_INDEPENDENT_REVIEW_2026-07-27.md`](GCAPEPS_MATHEMATICAL_FEASIBILITY_INDEPENDENT_REVIEW_2026-07-27.md),
SHA-256
`23bac8a83cbca57d9b88fffc4f9ff8e3ded1578045ec9663b4998c00c76f47c7`.
The manuscript-level consistency review is recorded in
[`GCAPEPS_TECHNICAL_NOTE_INDEPENDENT_CONSISTENCY_REVIEW_2026-07-27.md`](GCAPEPS_TECHNICAL_NOTE_INDEPENDENT_CONSISTENCY_REVIEW_2026-07-27.md).

This draft claims exact finite representability and explicit construction
bounds only. It does not claim low bond dimension, efficient contraction,
runtime or memory advantage, a novel PEPS suggestion, or QEC Record
correctness.

## Abstract

We introduce GCAPEPS, a GCAMPS-style Clifford-augmented projected
entangled-pair-state representation for finite lattices. A state is represented
as \(|\Psi\rangle=C|\phi(A)\rangle\), where the leading Clifford \(C\) is stored
as a stabilizer tableau and the residual \(|\phi(A)\rangle\) is a PEPS. The
Clifford-frame identities and Pauli-expansion/commute-through skeleton are
inherited from GCAMPS; the two-dimensional closure argument is supplied in this
construction. Under the qubit or odd-prime generalized-Pauli convention fixed
below, a \(k\)-site gate has an expansion with \(r\le d^{2k}\) nonzero Pauli
coefficients, and its pullback through \(C\) is a sum of the same \(r\)
product-Pauli operators. Routing the term label along a lattice tree gives an
exact PEPO with bond at most \(r\) on routed edges. Fusing this PEPO with the residual PEPS gives
the explicit bound \(D'_e\le rD_e\) on those edges and leaves other edges
unchanged. A qubit Pauli rotation has \(r\le2\), while an adjacent two-site
Clifford refactor has the safe bound \(D'_e\le d^2D_e\). We provide examples
showing that both factors can be attained. These results prove that exact,
untruncated GCAPEPS is mathematically well defined on every finite connected
lattice. They do not imply that its bonds remain small or that contracting it
is efficient.

**Keywords:** GCAMPS; PEPS; Clifford frame; stabilizer tableau; PEPO;
tensor-network closure

## 1. Introduction

Clifford-dominated circuits contain two structures with very different
classical descriptions. Their Clifford component admits a compact stabilizer
tableau representation, whereas non-Clifford amplitudes generally require a
more expressive state representation. GCAMPS exploits this split by writing

\[
|\Psi\rangle=C|\mathrm{MPS}\rangle,
\tag{1}
\]

updating the leading Clifford directly and applying pulled-back non-Clifford
operators only to the residual MPS [1]. Its direct continuation applies the
same \(C|\mathrm{MPS}\rangle\) representation to coherent surface-code
simulations and lists PEPS and tree tensor networks as possible future layouts
[2]. Neither source gives a constructive PEPS closure theorem.

The narrow question addressed here is therefore not whether PEPS will be
faster, or whether a particular QEC application can be simulated efficiently.
It is the prior mathematical question:

\[
\boxed{
\text{Does the GCAMPS frame--residual algebra remain exactly closed when the}
\quad \mathrm{MPS}\text{ residual is replaced by a finite-lattice PEPS?}
}
\tag{2}
\]

The answer is affirmative. The key observation is that Clifford pullback does
not increase the number of Pauli-basis terms. Although it can make their support
nonlocal, every Pauli word remains a product operator. A finite sum of product
operators has a simple tree-routed PEPO representation, and PEPO action is
closed on PEPS by fusing virtual indices.

Our contributions are exactly three:

1. We define GCAPEPS as the exact pair \((C,A)\) representing
   \(C|\phi(A)\rangle\), and separate the identities inherited from GCAMPS from
   the PEPS-specific construction in this work.
2. We prove a tree-routed PEPO lemma and the resulting per-edge GCAPEPS update
   bound \(D'_e\le rD_e\), with \(r\le d^{2k}\) for a \(k\)-site gate and
   \(r\le2\) for a qubit Pauli rotation.
3. We apply the paired Clifford-refactor identity inherited from GCAMPS to a
   PEPS residual, give a safe adjacent two-site bound \(D'_e\le d^2D_e\), and
   exhibit tightness examples that also make the absence of an efficiency
   theorem explicit.

We do not claim that replacing MPS by PEPS was first suggested here. In
particular, Ref. [2] already names PEPS and tree tensor networks as future
layouts. The contribution is the explicit GCAMPS-compatible construction and
its finite-lattice bounds.

## 2. Preliminaries

### 2.1 Finite PEPS

Let \(G=(V,E)\) be a finite connected graph and let every vertex carry a local
Hilbert space \(\mathcal H_v\cong\mathbb C^d\). A PEPS tensor \(A_v\) has one
physical index and one virtual index of size \(D_e\) for every incident edge.
Contracting every virtual edge pair defines [3]

\[
|\phi(A)\rangle
=\sum_{\mathbf s}
\operatorname{tTr}\!\left[\bigotimes_{v\in V}A_v^{s_v}\right]
|\mathbf s\rangle .
\tag{3}
\]

The vector \(\mathbf D=(D_e)_{e\in E}\) records PEPS state bonds. It is distinct
from any boundary or environment bond introduced by an approximate contraction
algorithm.

### 2.2 Pauli basis and Clifford pullback

For \(d=2\), or for an odd-prime qudit dimension with a fixed generalized-Pauli
phase convention, the \(k\)-site Pauli words form an operator basis of size
\(d^{2k}\). Hence a \(k\)-site unitary has an expansion

\[
U=\sum_{\alpha=1}^{r}c_\alpha P_\alpha,
\qquad r\le d^{2k},
\tag{4}
\]

after zero coefficients are removed. If \(C\) is Clifford, then

\[
C^\dagger P_\alpha C
=\eta_\alpha\widetilde P_\alpha,
\qquad |\eta_\alpha|=1,
\tag{5}
\]

where \(\widetilde P_\alpha\) is another product-Pauli word. Clifford conjugation
is a phase-decorated permutation of the Pauli basis, so it preserves the number
of nonzero terms.

GCAMPS prints the Pauli expansion and instructs the simulator to commute its
terms through \(C\) [1]. Equations (4)--(5), including the explicit phase and
term-count statement, are our formalization of that step rather than a theorem
quoted verbatim from Ref. [1].

## 3. GCAPEPS representation and inherited updates

### Definition 1 — GCAPEPS

A GCAPEPS representation on \(G\) is

\[
\mathfrak G=(C,A),
\qquad
\mathcal R(C,A):=C|\phi(A)\rangle,
\tag{6}
\]

where \(C\) is Clifford and \(A\) is a PEPS tensor family. Equality is exact up
to global phase. The theorem below introduces no truncation.

### Proposition 1 — Clifford-frame update

For a physical Clifford \(F\),

\[
\mathcal R(FC,A)=FC|\phi(A)\rangle
=F\mathcal R(C,A).
\tag{7}
\]

Thus the residual PEPS and all \(D_e\) are unchanged.

### Proposition 2 — signed non-Clifford pullback

For a physical unitary \(U\), define

\[
\widetilde U=C^\dagger UC
=\sum_{\alpha=1}^{r}c_\alpha\eta_\alpha\widetilde P_\alpha.
\tag{8}
\]

Then

\[
UC|\phi(A)\rangle=C\widetilde U|\phi(A)\rangle.
\tag{9}
\]

The question is reduced to whether the product-operator sum \(\widetilde U\)
can be absorbed into a PEPS with finite controlled bond growth.

## 4. Tree-routed PEPO closure

### Lemma 1 — product-sum PEPO

Let

\[
O=\sum_{\alpha=1}^{r}c_\alpha
  \bigotimes_{v\in V}O_v^{(\alpha)}.
\tag{10}
\]

Let \(W\) be the vertices where \(O_v^{(\alpha)}\) depends on \(\alpha\), and
write the common local factor at every \(v\notin W\) as \(B_v\). For any
connected tree \(T\subseteq G\) whose vertices contain \(W\), \(O\) has an
exact PEPO with

\[
R_e\le
\begin{cases}
r,&e\in E(T),\\
1,&e\notin E(T).
\end{cases}
\tag{11}
\]

**Proof.** Label every tree edge by \(\alpha\in\{1,\ldots,r\}\). At every tree
vertex, including a chosen root, insert a copy tensor that vanishes unless all
incident labels agree. Use \(O_v^{(\alpha)}\) on \(W\), the common factor
\(B_v\) on routing vertices, and multiply \(c_\alpha\) once at the root.
Vertices outside \(T\) have one-dimensional PEPO bonds and retain \(B_v\).
Contraction enforces one global term label and sums it exactly. If \(T\) has one
vertex, place \(\sum_\alpha c_\alpha O_v^{(\alpha)}\) directly in its local
physical block. \(\square\)

The common-factor clause is essential. Replacing a routing factor by identity
would fail, for example, for
\(A\otimes X\otimes B+C\otimes X\otimes D\).

### Lemma 2 — PEPO action closes PEPS

If a PEPO has virtual dimensions \(R_e\) and a PEPS has virtual dimensions
\(D_e\), then applying the former to the latter gives an exact PEPS with

\[
D'_e\le D_eR_e.
\tag{12}
\]

**Proof.** Contract the PEPO physical-input index with the PEPS physical index
at every vertex and fuse the two virtual indices on every edge. \(\square\)

## 5. Main finite-lattice theorem

### Theorem 1 — exact GCAPEPS gate closure

Let \((C,A)\) represent a nonzero state on a finite connected graph. Let \(U\)
be a \(k\)-site unitary with \(r\) nonzero Pauli coefficients. Define

\[
W_U=\bigcup_{\alpha=1}^{r}
\operatorname{supp}(\widetilde P_\alpha),
\tag{13}
\]

and choose a connected routing tree \(T\) containing \(W_U\). Then an exact
PEPS \(A'\) exists such that

\[
UC|\phi(A)\rangle=C|\phi(A')\rangle,
\tag{14}
\]

with

\[
D'_e\le
\begin{cases}
rD_e,&e\in E(T),\\
D_e,&e\notin E(T).
\end{cases}
\tag{15}
\]

**Proof.** Equation (8) writes \(\widetilde U\) as a sum of the same \(r\)
product-Pauli words. Lemma 1 gives an exact tree-routed PEPO with \(R_e\le r\),
and Lemma 2 absorbs it into the residual PEPS. Equation (9) then gives the
physical-state identity. \(\square\)

### Corollary 1 — Pauli rotation

For a nonidentity qubit Pauli word \(P\),

\[
e^{-i\theta P/2}
=\cos(\theta/2)I-i\sin(\theta/2)P.
\tag{16}
\]

Therefore \(r\le2\), even when \(C^\dagger PC\) has global support, and

\[
D'_e\le2D_e
\tag{17}
\]

on a tree connecting that support. If one coefficient vanishes, \(r=1\).

### Corollary 2 — finite sequence

For non-Clifford updates \(t=1,\ldots,m\),

\[
D_e^{(m)}\le D_e^{(0)}
\prod_{t:\,e\in E(T_t)}r_t.
\tag{18}
\]

This bound counts only those PEPO updates. A nonidentity residual refactor
contributes its own factor; choosing the identity refactor leaves (18)
unchanged.

## 6. Exact Clifford refactor

GCAMPS optionally applies a Clifford \(Q\) to the residual and compensates it in
the leading frame [1]. The same identity holds for GCAPEPS:

\[
(C,A)\longmapsto(CQ^\dagger,A_Q),
\qquad
|\phi(A_Q)\rangle=Q|\phi(A)\rangle,
\tag{19}
\]

because

\[
(CQ^\dagger)|\phi(A_Q)\rangle=C|\phi(A)\rangle.
\tag{20}
\]

For an adjacent two-site \(Q\), an operator-Schmidt decomposition has rank
\(\rho(Q)\le d^2\), giving the exact safe bound

\[
D'_e\le\rho(Q)D_e\le d^2D_e
\tag{21}
\]

on that edge. This is not a promise that the selected \(Q\) lowers the bond.
The identity candidate is always valid, so refactor optimization is unnecessary
for mathematical closure.

## 7. Non-vacuity and tightness

### 7.1 Finite universality

Every state on a finite rectangular lattice has a finite PEPS representation.
Order the sites along a snake Hamiltonian path, perform successive Schmidt
decompositions to obtain an MPS, and set every unused lattice-edge bond to one.
The path bond at cut \(j\) is at most

\[
d^{\min(j,n-j)},
\tag{22}
\]

where \(n=|V|\). Taking \(C=I\) yields a GCAPEPS. This gives a universal
fallback, but the constructive content of Theorem 1 is stronger because it
tracks gate-dependent bond growth.

### 7.2 Factor-two tightness

For nonzero \(a,b\),

\[
(aI+bX^{\otimes n})|0\rangle^{\otimes n}
=a|0\cdots0\rangle+b|1\cdots1\rangle
\tag{23}
\]

has Schmidt rank two across every nontrivial bipartition. A Clifford can map a
single-site nonidentity Pauli to \(X^{\otimes n}\). Hence the factor two in
Corollary 1 is attainable after a local physical rotation is pulled through the
frame.

### 7.3 Two-site \(d^2\) tightness

On a four-site path, put Bell pairs on the two outer edges and bond dimension one
on the middle edge. Applying SWAP to the two middle qudits changes the Schmidt
rank across the middle cut from one to \(d^2\). Since SWAP is Clifford, the
general adjacent-refactor factor \(d^2\) cannot be lowered without additional
assumptions.

## 8. Limitations

The theorem is exact but deliberately modest.

First, repeated non-Clifford updates can make (18) exponential. The Clifford
frame can turn a local Pauli into a global word, and the theorem controls the
term-label bond, not the geometric size of its support.

Second, exact PEPS contraction is generically hard [4]. The local tensor update
is constructive, but evaluating norms or observables may still require
exponential work. Approximate boundary methods introduce a separate environment
bond and require their own error analysis.

Third, PEPS has no generic MPS-like canonical gauge that makes every local norm
matrix the identity [3]. No MPS canonical-form or local-SVD optimality claim is
transferred from GCAMPS. The “canonicalization” in the GCAMPS disentangler
section concerns two-qudit Clifford-tableau classes, not a PEPS canonical form.

Fourth, the abstract closure lemmas apply in any finite local dimension with a
consistent operator basis. An executable composite-dimensional tableau solver
requires more care: the published GCAMPS Eq. (5) invokes field Gaussian
elimination over \(\mathbb Z_d\), which is directly appropriate only for prime
\(d\), and its even-dimensional phase convention is underspecified [1].

Finally, the routed-tree PEPO is a mathematical construction. The current
prototype uses a global direct-sum residual representation; this note does not
claim that the software already realizes the per-edge bounds (15) and (17).

## 9. Conclusion

GCAPEPS is mathematically feasible on finite connected lattices. The GCAMPS
frame update and commute-through skeleton remain valid when the residual MPS is
replaced by a PEPS. The missing two-dimensional step is supplied by a
tree-routed PEPO construction and the exact closure of PEPS under PEPO action.
For a gate with \(r\) nonzero Pauli terms, there exists an exact updated
representation with \(D'_e\le rD_e\) on the selected routing tree; a qubit Pauli
rotation admits the factor-two bound. Paired Clifford refactoring is exact,
with an adjacent two-site safety factor \(d^2\).

These statements establish a well-defined representation and update calculus.
They do not establish scalability. Questions of compression, contraction,
runtime, memory, and application-specific performance belong to later work and
must not be folded into the present theorem.

## References

1. B. Harper, A. C. Nakhl, T. Quella, M. Sevior, and M. Usman, “GCAMPS: A
   Scalable Classical Simulator for Qudit Systems,” SCA/HPCAsia 2026,
   arXiv:2511.06672v2.
2. B. Harper, A. C. Nakhl, M. Sevior, and M. Usman, “Non-Clifford Crosstalk
   Noise in Surface Codes Using Hybrid Stabilizer--Tensor Network Methods,”
   arXiv:2605.29514v1. Eq. (7) remains \(C|\mathrm{MPS}\rangle\), with
   PEPS/TTN listed as future layouts.
3. M. Lubasch, J. I. Cirac, and M.-C. Bañuls, “Algorithms for finite projected
   entangled pair states,” Physical Review B 90, 064425 (2014),
   arXiv:1405.3259v2.
4. N. Schuch, M. M. Wolf, F. Verstraete, and J. I. Cirac, “Computational
   Complexity of Projected Entangled Pair States,” Physical Review Letters 98,
   140506 (2007).
