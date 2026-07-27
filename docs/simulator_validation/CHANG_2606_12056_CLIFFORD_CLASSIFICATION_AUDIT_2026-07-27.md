# Claim audit — Chang et al. Clifford equivalence classes for an exact-small qubit search

## Status and decision

This packet audits arXiv:2606.12056v1 only for the phase-free two-qubit
Clifford classification used to reduce an entanglement-spectrum search.  The
source closes the local-equivalence criterion, the invariant hash, and the
reported reduction from 720 phase-free symplectic actions to 20 classes.  It
does not supply a repository-pinned representative catalogue, a PEPS
contraction, a truncation certificate, or a detector/observable Record bound.

An independent source-only reviewer checked every claim and locator against
the fixed v1 PDF.  The reviewed note remains outside `CURRENT_CORPUS.toml`
because manifest admission is a separate step not performed by this audit.
This audit changes no implementation and grants no code permission by itself.

## Assigned closure rows

| row | exact source location | source says | source does not say | status |
|---|---|---|---|---|
| Symplectic convention | Sec. 2.2, Eqs. (5)--(7), PDF p. 3 | A phase-free \(n\)-qubit Clifford action is encoded by a \(2n\times2n\) binary symplectic matrix; Pauli row labels act from the right, and the matrix order reverses the Clifford product order. | The phase-free matrix does not retain Pauli factors or global phase. | closed |
| Entanglement objective | Sec. 2.3, Eq. (8), Fig. 1, PDF p. 4 | The local search minimizes the bipartite order-\(1/2\) Rényi entropy, equivalently a function of the Schmidt coefficients, across the selected MPS bond. | This is not the order-2 Rényi objective used by Liu and Clark, and the source does not prove one objective selects the same representative as the other. | closed |
| Local-equivalence criterion | Sec. 2.4, Fig. 2 and Eq. (10), PDF p. 5 | Two phase-free Clifford actions are equivalent when \(S_2^{-1}S_1\) is block diagonal with independent symplectic actions on the two halves; such local actions leave the Schmidt spectrum unchanged. | The source does not define a double-sided quotient. | closed |
| Hash definition | Appendix, Algorithm 1 and Eqs. (A1)--(A3), PDF pp. 13--14 | For \(S=\begin{psmallmatrix}A&B\\C&D\end{psmallmatrix}\), the hash packs \(AQA^T\), \(AQC^T\), and \(CQC^T\). | A packed integer alone does not preserve phases or identify a unitary representative. | closed |
| Hash completeness | Appendix, Theorem 1, Eqs. (A12)--(A30), PDF pp. 14--15 | Equality of the three hash matrices is necessary and sufficient for the block-local equivalence criterion. | The proof does not validate any external representative file or ordering. | closed |
| Search-space count | Sec. 2.4, Eqs. (9)--(10), PDF pp. 4--5; conclusion, PDF p. 12 | The source reports 720 phase-free two-qubit actions and 20 equivalence classes; it reports the four-qubit reduction separately as 47,377,612,800 to 91,392. | It does not report a qutrit 90-class construction. | closed |
| Reproducible representative catalogue | Sec. 2.5, PDF p. 5; Code and data availability, PDF p. 15 | The source names QuantumClifford.jl for generation and links the Camps module of Focus plus an examples repository. | The paper artifact contains no representative array, canonical ordering, file SHA-256, or independent orbit-coverage test. | missing |
| PEPS and Record bridge | Full-text scope, especially Secs. 2.3--2.5 and 4 | The classified gates are tested in an MPS/CAMPS electronic-structure workflow and VQE preprocessing. | No PEPS residual, branch instrument, detector fold, complete Record law, or state-to-Record error theorem is defined. | missing |

## Operation replay

| input | transformation | assumption | output | exact source location | replay status |
|---|---|---|---|---|---|
| A phase-free Clifford action | Encode Pauli-generator images as a binary symplectic \(S\) satisfying \(S\Omega S^T=\Omega\) | Pauli phases and global phase are intentionally quotiented out | Symplectic action \(S\) | Sec. 2.2, Eqs. (5)--(7), PDF p. 3 | complete |
| Two actions \(S_1,S_2\) | Form \(F=S_2^{-1}S_1=\Omega S_2^T\Omega S_1\) | The paper's row-vector convention and bipartition are fixed | Same class iff \(F=\operatorname{diag}(s,s')\) | Sec. 2.4, Eq. (10), PDF p. 5 | complete |
| \(S=\begin{psmallmatrix}A&B\\C&D\end{psmallmatrix}\) | Compute \(T_1=AQA^T\), \(T_2=AQC^T\), \(T_3=CQC^T\), then pack their bits | \(n\) is even and all arithmetic is over \(\mathbb Z_2\) | Integer class hash | Appendix, Algorithm 1 and Eqs. (A1)--(A3), PDF pp. 13--14 | complete |
| Two class hashes | Compare all three component matrices | Both inputs are valid symplectic matrices in the same convention | Hash equality iff block-local equivalence | Appendix, Theorem 1 and Eqs. (A12)--(A30), PDF pp. 14--15 | complete |
| All phase-free two-qubit symplectic actions | Group by the proven hash | Generation covers all 720 actions exactly once | 20 reported classes | Sec. 2.4, PDF p. 5; conclusion, PDF p. 12 | complete at source-claim level |

## Project application

The following statements are project inferences, not claims made by Chang et
al.

1. With the source's row-vector convention, Eq. (A18) gives
   \(S_1=S_2\operatorname{diag}(s,s')\).  Because Eq. (7) reverses physical
   Clifford product order, this matrix-side right multiplication corresponds
   to an output/post-action local Clifford multiplying the physical gate.
   The relevant object for a fixed input and a bipartite Schmidt-spectrum
   score is therefore a one-sided output-local quotient, not a double
   quotient.
2. For two qubits, the phase-free group has 720 elements and the independent
   one-qubit phase-free local actions have \(6\times6=36\) elements.  The
   source's reported 20 classes are consistent with \(720/36=20\).  This
   arithmetic is a reconstruction of the reported count; it is not a
   substitute for enumerating and checking every orbit.
3. An exact-small implementation may use one representative per verified
   post-local orbit because a unitary acting separately on the two output
   halves preserves every Schmidt coefficient.  The implementation must
   freeze the physical/matrix multiplication convention and compare the
   20-candidate minimum with an independently enumerated 720-candidate
   minimum.
4. The paper's hash classifies phase-free actions.  A runtime unitary still
   needs an exact phase lift, and any catalogue must be independently checked
   for 20 disjoint orbits of size 36 before it can serve as an executable
   source object.
5. Nothing in this paper extends the 20-class result to qutrits or establishes
   a scalable approximate-PEPS correctness certificate.

## Competing evidence, anomalies, and kill conditions

- The source minimizes order-\(1/2\) Rényi entropy, whereas Liu and Clark use
  order-2 Rényi entropy/purity.  The quotient remains score-invariant because
  both depend only on the Schmidt spectrum, but equality of their selected
  minimizers is not a source claim.
- A classification that treats \(S_1\) and \(S_2\) as equivalent after
  arbitrary local multiplication on both physical sides is stronger than
  Eq. (10) and is not supported by this source for a fixed input state.
- Kill catalogue use if the 20 representatives do not generate 20 disjoint
  post-local orbits of 36 phase-free actions whose union has size 720.
- Kill convention use if an explicit unitary/tableau replay shows that the
  chosen matrix multiplication side corresponds to pre-action rather than
  output/post-action local gates.
- Kill any PEPS or Record-faithfulness conclusion if the only evidence is the
  local class count or a reduced entanglement score.

## Source-local verdict

- read_status: complete
- evidence_status: persisted and source-only reviewed, not manifest-admitted
- assigned-row status: criterion, hash theorem, and counts closed; catalogue
  reproducibility and PEPS/Record bridges missing
- downstream permission: source-note review and exact-small preregistration
  design only; no implementation or scientific-status upgrade

