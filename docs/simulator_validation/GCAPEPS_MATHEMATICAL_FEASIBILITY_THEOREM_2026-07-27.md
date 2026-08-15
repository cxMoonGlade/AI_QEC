# GCAPEPS mathematical-feasibility theorem packet

Date: 2026-07-27

Status: `MATHEMATICAL_CONTENT_REVIEWED_PASS`

Active scope: finite-lattice, exact, untruncated GCAMPS-to-PEPS extension.

Out of scope: a low-bond theorem, efficient PEPS contraction, an optimal
disentangler, measurement--reset--Record correctness, QEC performance, and any
advantage over full PEPS.

## 1. Question and answer

The only active question is:

\[
\text{Does the GCAMPS representation }C|\mathrm{MPS}\rangle
\text{ admit a mathematically well-defined finite-2D extension }
C|\mathrm{PEPS}\rangle?
\]

For a finite connected lattice, the answer is **yes**. The nontrivial useful
statement is not merely that every finite state can be encoded as a PEPS. It is
that the GCAMPS update algebra has a constructive PEPO-to-PEPS realization with
an explicit per-edge worst-case bond bound.

The result established below is:

\[
\boxed{
|\Psi\rangle=C|\phi(A)\rangle,
\qquad
U|\Psi\rangle=C|\phi(A')\rangle,
\qquad
D'_e\le rD_e
}
\]

on the edges of a selected routing tree, where \(r\) is the number of nonzero
Pauli terms in the pulled-back gate. For a \(k\)-site gate on prime-dimensional
qudits, \(r\le d^{2k}\). For a qubit Pauli rotation, \(r\le2\).

This proves exact finite representability. It does **not** prove that \(D'_e\)
remains small after many updates.

## 2. Exact source boundary

The source-backed inputs are intentionally minimal.

| input | source location | exact artifact identity | role here |
|---|---|---|---|
| GCAMPS hybrid state, Clifford-frame update, Pauli expansion/commute-through instruction, and paired Clifford refactor | Harper et al., arXiv:2511.06672v2, PDF pp. 3--5, especially Sec. 3 and Fig. 3 | PDF SHA `880c44e25e9c1fd589a75ca5e824e58a2436c0c35a7ee7dddebbb61d439a0c42`; admitted note SHA `770bad822875f1e301beab5627d4e395daea29f5b74ffaacc7ffffdd4e570f02`; audit SHA `0851e0c193d47df5ac789c6fa398a4bd9357bc04611f148aa59d77928a6a6cea` | supplies the tensor-network-topology-independent frame/residual skeleton, for an MPS residual |
| finite open-boundary PEPS | Lubasch, Cirac, and Bañuls, arXiv:1405.3259v2, Sec. II and Fig. 1, PDF p. 2 | PDF SHA `5d7e010293770b0c97ac9c0b88075710ceda3a68988da7933dd2130621d8269a`; admitted note SHA `be8457fdb099ed00ce8b329a6eb51e372d37031a5946d940865c1dd5936da97a`; audit SHA `dfe5f0e507970465c9af1df3b688da513c028f70d9842365a29a31e0d6c107ea` | supplies standard finite-square-lattice PEPS background, not the theorem below |
| orthodox GCAMPS QEC continuation | Harper et al., arXiv:2605.29514v1 | PDF SHA `c13096aa841acf2b2161f18140c56dd9d3549b268969f79328ff0865583a35dd`; admitted note SHA `980501ee4e824c5e1fd3858d2724e2f48ce984565c7b630bf916a52fab351311` | fixes predecessor/positioning only; it does not provide a PEPS theorem |

The PEPO construction, PEPO-on-PEPS closure, and the resulting GCAPEPS bond
bounds are project derivations. The explicit signed \(C^\dagger PC\) formula,
Pauli-term-count statement, and \(d^{2k}\) count below are also project
formalizations of the source's high-level commute-through instruction; they are
not attributed to the GCAMPS papers as printed theorems.

The continuation arXiv:2605.29514v1 still uses
\(C|\mathrm{MPS}\rangle\) on PDF p. 4, Eq. (7), says on the same page that its
experiments did not use Clifford optimization, and lists PEPS and tree tensor
networks only as possible future layouts on PDF p. 7. It therefore supports the
adjacent-work boundary and the non-necessity of refactoring for exactness, but
does not supply the theorem below. Merely suggesting an MPS-to-PEPS replacement
is not claimed as this project's novelty.

## 3. Setting and definition

Let \(G=(V,E)\) be a finite connected graph, in the intended application a
finite open-boundary square lattice. Every vertex carries a qudit Hilbert space
\(\mathcal H_v\cong\mathbb C^d\). For the clean generalized-tableau statement,
take \(d=2\) or odd prime \(d\); composite \(d\) is discussed separately below.

A PEPS tensor family \(A=\{A_v\}_{v\in V}\) has one physical index of size
\(d\) at each vertex and one virtual index of size \(D_e\) for every incident
edge \(e\). Contracting all virtual edge pairs gives

\[
|\phi(A)\rangle
=\sum_{\mathbf s}
  \operatorname{tTr}\!\left[\bigotimes_{v\in V}A_v^{s_v}\right]
  |\mathbf s\rangle .
\tag{1}
\]

Let \(\mathrm{Cliff}_d(V)\) be the Clifford normalizer of the generalized Pauli
group on the vertices. A **GCAPEPS representation** is the pair

\[
\mathfrak G=(C,A),
\qquad
|\Psi(\mathfrak G)\rangle:=C|\phi(A)\rangle,
\qquad
C\in\mathrm{Cliff}_d(V).
\tag{2}
\]

The Clifford is stored independently, for example as a stabilizer tableau. The
PEPS stores only the residual. Equality below is exact up to a physically
irrelevant global phase. No truncation is permitted in the theorem.

## 4. Algebra inherited from GCAMPS

### Lemma 1 — physical Clifford update

For any physical Clifford \(F\),

\[
F C|\phi(A)\rangle=(FC)|\phi(A)\rangle.
\tag{3}
\]

Hence

\[
(C,A)\longmapsto(FC,A)
\tag{4}
\]

is exact and leaves every residual PEPS bond \(D_e\) unchanged.

**Proof.** This is associativity of operator composition. The product of two
Cliffords is Clifford. \(\square\)

### Lemma 2 — signed Pauli pullback

Let a \(k\)-site operator have a generalized-Pauli expansion

\[
U=\sum_{\alpha=1}^{r}c_\alpha P_\alpha,
\qquad r\le d^{2k},
\tag{5}
\]

where only nonzero coefficients are retained. Because \(C\) normalizes the
Pauli group,

\[
C^\dagger P_\alpha C
=\eta_\alpha\widetilde P_\alpha,
\qquad |\eta_\alpha|=1,
\tag{6}
\]

and every \(\widetilde P_\alpha\) is again a tensor product of one-site Pauli
operators. Therefore

\[
UC=C\widetilde U,
\qquad
\widetilde U=C^\dagger UC
=\sum_{\alpha=1}^{r}c_\alpha\eta_\alpha\widetilde P_\alpha.
\tag{7}
\]

Conjugation is a bijection on Pauli words modulo phase, so it does not increase
the number \(r\) of nonzero terms. It may, however, turn a local Pauli word into
a lattice-wide Pauli word.

**Proof.** Equation (7) follows by inserting \(CC^\dagger\), applying the
normalizer definition term by term, and retaining every conjugation phase.
The \(d^{2k}\) bound is the dimension of the operator space on \(k\) qudits.
\(\square\)

Lemma 1 and the Pauli-expansion/commute-through skeleton of Lemma 2 are inherited
from GCAMPS. Lemma 2's explicit signed formula and counting statements are the
project's formalization. The resulting operator identity is independent of
whether the exact residual is an MPS, PEPS, tree tensor network, or another
state representation.

## 5. Two tensor-network closure lemmas

### Lemma 3 — finite product-sum operator has a finite PEPO

Let

\[
O=\sum_{\alpha=1}^{r}c_\alpha
  \bigotimes_{v\in V}O_v^{(\alpha)}
\tag{8}
\]

be a sum of \(r\) product operators. Define the dependence set

\[
W:=\{v\in V:O_v^{(\alpha)}\text{ is not the same local operator for all }
\alpha\}.
\tag{8a}
\]

For every \(v\notin W\), write that common local operator as \(B_v\). Choose
any connected tree \(T\subseteq G\) whose vertex set contains \(W\). Then \(O\)
has an exact PEPO
representation with virtual dimensions

\[
R_e\le
\begin{cases}
r,&e\in E(T),\\
1,&e\notin E(T).
\end{cases}
\tag{9}
\]

If \(r=1\), all PEPO bonds can be one-dimensional.

**Construction and proof.** First suppose \(T\) has at least one edge. Give
every edge of \(T\) a label \(\alpha\in\{1,\ldots,r\}\). At **every** vertex of
\(T\), including the root, use a copy tensor that is zero unless all incident
tree labels agree. At \(v\in W\), multiply its physical input--output block by
\(O_v^{(\alpha)}\); at a routing vertex \(v\in T\setminus W\), use the common
block \(B_v\), which need not be the identity. At one root, additionally
multiply the common label sector by \(c_\alpha\). Vertices outside \(T\) have
one-dimensional PEPO bonds and use \(B_v\). Contracting the connected copy
network enforces one global value of \(\alpha\) and then sums it exactly.

If \(T\) consists of a single root vertex, put
\(\sum_\alpha c_\alpha O_{\mathrm{root}}^{(\alpha)}\) directly in its physical
block and use \(B_v\) everywhere else. This also covers the empty-dependence-set
case after choosing an arbitrary root. Both constructions yield (8). \(\square\)

The tree is a routing choice, not an assertion that the operator is physically
one-dimensional. A spanning tree of \(G\) always exists, so the construction is
defined even when the pulled-back Pauli support is global or disconnected.
Connectedness of \(G\) is essential for this statement: a fixed PEPS on a
disconnected graph is a product across graph components and cannot in general
represent an operator-generated entangled superposition across those components.

### Lemma 4 — exact PEPO action closes PEPS

Let \(O(B)\) be a PEPO on \(G\) with virtual edge dimensions \(R_e\), and let
\(|\phi(A)\rangle\) be a PEPS with virtual dimensions \(D_e\). Then

\[
O(B)|\phi(A)\rangle=|\phi(A')\rangle
\tag{10}
\]

for an exact PEPS with

\[
D'_e\le D_eR_e.
\tag{11}
\]

**Construction and proof.** At every vertex contract the PEPO physical-input
index with the PEPS physical index. Fuse, on each incident edge, the original
PEPS virtual index of size \(D_e\) with the PEPO virtual index of size \(R_e\).
The new local tensor has the PEPO physical-output index and fused virtual edge
size \(D_eR_e\). Full contraction gives exactly the left side of (10).
\(\square\)

No environment approximation, canonical form, SVD truncation, or global PEPS
contraction is used in this closure statement.

## 6. Main theorem — exact GCAPEPS gate closure

### Theorem 1 — finite-lattice GCAPEPS feasibility

Let \((C,A)\) be a GCAPEPS representation of a nonzero state on a finite
connected graph \(G\). Let \(U\) be a \(k\)-site physical unitary gate with
\(r\) nonzero generalized-Pauli
coefficients, where \(r\le d^{2k}\). Write
\(\widetilde P_\alpha=C^\dagger P_\alpha C\) up to its retained phase and define
the safe active set

\[
W_U:=\bigcup_{\alpha=1}^{r}\operatorname{supp}(\widetilde P_\alpha).
\tag{11a}
\]

Let \(T\) be any connected routing tree whose vertices contain \(W_U\).

Then there is a constructible PEPS tensor family \(A'\) such that

\[
U C|\phi(A)\rangle=C|\phi(A')\rangle
\tag{12}
\]

and

\[
D'_e\le
\begin{cases}
rD_e,&e\in E(T),\\
D_e,&e\notin E(T).
\end{cases}
\tag{13}
\]

Consequently the class of finite, exact GCAPEPS representations is closed under
every finite sequence of Clifford gates and finite-support non-Clifford gates.

**Proof.** Use Lemma 2 to write \(UC=C\widetilde U\), with \(\widetilde U\) a
sum of the same \(r\) product-Pauli words. Lemma 3 gives an exact PEPO for
\(\widetilde U\) with \(R_e\le r\) on \(T\) and \(R_e=1\) elsewhere. Lemma 4
absorbs that PEPO into the residual PEPS and gives (13). Equation (12) then
follows from the pullback identity. Clifford gates are handled by Lemma 1.
All numbers are finite because the graph and gate list are finite. \(\square\)

### Corollary 1 — qubit Pauli rotation

For a nonidentity qubit Pauli word \(P\),

\[
U_P(\theta)=e^{-i\theta P/2}
=\cos(\theta/2)I-i\sin(\theta/2)P.
\tag{14}
\]

Writing \(Q=C^\dagger PC\), the pulled-back residual gate is

\[
\widetilde U_P(\theta)
=\cos(\theta/2)I-i\sin(\theta/2)Q.
\tag{15}
\]

Thus \(r\le2\), independent of the support size of \(Q\), and one may choose

\[
D'_e\le2D_e
\tag{16}
\]

only on a tree connecting \(\operatorname{supp}(Q)\). At angles for which one
coefficient vanishes, \(r=1\).

This is the cleanest mathematical reason that a local coherent rotation remains
exactly representable after a Clifford pullback even when it becomes nonlocal.

When both displayed coefficients are nonzero, the factor two cannot be replaced
by one in general. For nonzero \(a,b\),
\((aI+bX^{\otimes n})|0\rangle^{\otimes n}\) has Schmidt rank two across every
nontrivial bipartition. A Clifford can map a one-site nonidentity Pauli to
\(X^{\otimes n}\), so this behavior can occur after the pullback of a local
Pauli rotation.

### Corollary 2 — a finite gate sequence

For non-Clifford updates \(t=1,\ldots,m\), with Pauli-term counts \(r_t\) and
routing trees \(T_t\), an untruncated construction obeys

\[
D_e^{(m)}
\le D_e^{(0)}
\prod_{t:\,e\in E(T_t)}r_t.
\tag{17}
\]

For qubit Pauli rotations this is at most \(2^{m_e}D_e^{(0)}\), where \(m_e\)
counts routed rotations whose selected tree crosses edge \(e\). This bound is a
feasibility certificate and simultaneously shows why no efficiency conclusion
follows: it can be exponential.

Equation (17) counts the non-Clifford PEPO updates only. If a nonidentity
residual refactor is also applied, its PEPO or operator-Schmidt factor must be
included separately; choosing the always-valid \(Q=I\) preserves (17).

## 7. Exact GCAMPS-style Clifford refactor

### Theorem 2 — paired refactor invariant

For any Clifford \(Q\) that is applied exactly to the residual,

\[
(C,A)\longmapsto(CQ^\dagger,A_Q),
\qquad
|\phi(A_Q)\rangle=Q|\phi(A)\rangle,
\tag{18}
\]

preserves the represented physical state:

\[
(CQ^\dagger)|\phi(A_Q)\rangle
=(CQ^\dagger)Q|\phi(A)\rangle
=C|\phi(A)\rangle.
\tag{19}
\]

If \(Q\) is a two-site gate on the endpoints of an edge \(e\), take an operator
Schmidt decomposition

\[
Q=\sum_{a=1}^{\rho(Q)}L_a\otimes R_a,
\qquad \rho(Q)\le d^2.
\tag{20}
\]

It is an edge-local PEPO, so it may be absorbed exactly with

\[
D'_e\le\rho(Q)D_e\le d^2D_e,
\qquad D'_{e'}=D_{e'}\quad(e'\ne e).
\tag{21}
\]

The identity candidate \(Q=I\) is always valid. Therefore mathematical
feasibility does not depend on finding an entanglement-reducing Clifford. The
choice of \(Q\), its objective, and whether it lowers any PEPS bond are separate
optimization questions.

The \(d^2\) safety factor is also tight for general two-site Cliffords. On a
four-site path, start with Bell pairs on the two outer edges and bond dimension
one on the middle edge. A SWAP on the two middle qudits is Clifford and changes
the Schmidt rank across the middle cut from one to \(d^2\).

## 8. Universality on a finite rectangular lattice

The preceding theorem gives a constructive update bound. A simpler existence
check is also useful.

### Proposition 3 — every finite state has a finite PEPS representation

Order an \(L\times W\) rectangular lattice along a snake Hamiltonian path.
Successive Schmidt decompositions represent any \(n=LW\) qudit state as an MPS
on that path with bond rank at cut \(j\) no larger than

\[
d^{\min(j,n-j)}.
\tag{22}
\]

Regard the path tensors as PEPS tensors and give every unused lattice edge bond
dimension one. This is an exact finite PEPS. Taking \(C=I\) makes it a GCAPEPS.

This proposition proves representational universality, but by itself would be a
nearly vacuous feasibility statement. The constructive non-vacuous content is the
GCAMPS-compatible update construction and the explicit bounds (13), (16), and
(17).

## 9. Composite local dimensions

The representation and PEPO closure lemmas are finite-dimensional and do not
require prime \(d\). The clean tableau algorithm inherited from the GCAMPS
source is different: its Eq. (5) invokes Gaussian elimination over
\(\mathbb Z_d\) as a field, which is directly valid only for prime \(d\), and
the source also leaves an even-\(d\) phase-column ambiguity.

Accordingly:

- the theorem is immediately rigorous for qubits and odd-prime qudits under a
  fixed phase convention;
- a composite-\(d\) GCAPEPS theorem remains true at the abstract Clifford-
  normalizer level;
- an executable composite-\(d\) tableau solver requires a separate module/ring
  treatment and must not be claimed from the published GCAMPS Eq. (5).

## 10. What is and is not proved

### Proved in this packet, subject to independent mathematical review

1. The definition \(C|\mathrm{PEPS}\rangle\) is exact and nonempty.
2. Physical Clifford gates update only the leading Clifford frame.
3. A finite-support non-Clifford gate pulls back to a finite Pauli-product sum
   with unchanged term count.
4. That product sum has an explicit finite-tree PEPO.
5. Exact PEPO application closes PEPS with a per-edge product bond bound.
6. Paired Clifford refactoring preserves the represented physical state.
7. A finite circuit therefore produces a finite exact GCAPEPS representation.

### Not proved, and not needed for mathematical feasibility

1. The residual bonds remain polynomial, small, or smaller than full PEPS.
2. Exact or approximate PEPS contraction is efficient.
3. A useful Clifford disentangler can be found efficiently.
4. The PEPS has an MPS-like canonical form or a globally optimal local SVD.
5. Truncation preserves fidelity or observables within a stated bound.
6. GCAPEPS is faster or uses less memory than full PEPS.
7. The MPS scaling curves in either GCAMPS paper transfer to two dimensions.
8. A measurement--reset--Record or QEC theorem follows from state closure.
9. The routed-tree construction is not claimed to be the behavior of the
   current software implementation; the present prototype uses a different
   global direct-sum representation, so Eqs. (13) and (16) are mathematical
   construction bounds, not measured implementation ledgers.

## 11. Minimal paper spine after the scope correction

The mathematics supports a much smaller and cleaner paper:

1. **Definition.** GCAPEPS is the exact pair \((C,A)\) representing
   \(C|\phi(A)\rangle\).
2. **Inheritance and formalization.** GCAMPS supplies the frame update, Pauli
   expansion/commute-through skeleton, and paired refactor identity; this work
   writes the signed pullback explicitly.
3. **Constructive theorem in this work.** A pulled-back \(r\)-term Pauli sum has
   a tree-routed PEPO and maps a PEPS with \(D_e\) to one with at most \(rD_e\)
   on routed edges.
4. **Special case.** A qubit coherent Pauli rotation has \(r=2\), even if its
   pulled-back Pauli support is global.
5. **Limitation.** Repeated updates may grow bonds exponentially and generic
   contraction remains hard; the paper claims well-defined exact feasibility,
   not a demonstrated speedup.

The broader XZZX/Record/benchmark programme should not appear as the proof's
motivation or acceptance gate. At most it can be named as a possible future
application after the mathematical GCAPEPS construction is established.
