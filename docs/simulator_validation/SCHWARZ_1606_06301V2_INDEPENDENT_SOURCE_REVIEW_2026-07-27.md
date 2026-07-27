# Schwarz et al. arXiv:1606.06301v2 — independent source reconstruction

Date: 2026-07-27

Reviewer: `/root/rereview_harper2605`

Status: **SOURCE RECONSTRUCTION COMPLETE — ADMISSION PENDING**

This report reconstructs the theorem, proof assumptions, error notion, and
complexity claims in the pinned source. It is not an admission review of a
candidate literature note: no candidate source-only packet was supplied or
inspected. It therefore records `admission pending`, not PASS.

## 1. Source object and review protocol

| field | verified value |
|---|---|
| title | *Approximating local observables on projected entangled pair states* |
| authors | M. Schwarz, O. Buerschaper, J. Eisert |
| source version | arXiv:1606.06301v2, version stamp 29 August 2016 |
| pinned artifact | `docs/papers/1606.06301v2.pdf` |
| SHA-256 | `bc240a9b78a84e886360d4d0a621a0b06b12fef93e4e399c6b9aa1f66d1e43c3` |
| PDF identity | PDF 1.5, 586,577 bytes, unencrypted, 7 pages |
| source extent | four-page main text, references, and a three-page appendix containing the detailed proof and transfer-operator discussion |

The PDF header, tail/xref marker, page count, version stamp, title, and author
block were checked. All seven pages were read in order. All seven rendered
pages were visually inspected; the load-bearing theorem, conjecture, equation,
assumption, and proof pages are pp. 2–7.

No legacy Schwarz note, candidate note/audit, retrieval-cache summary, or
CAPEPS-specific narrative was consulted. No note, audit, or corpus manifest was
modified.

## 2. Result in one bounded statement

Theorem 1 concerns one normalized expectation value of one constant-support
observable on a specified PEPS. It does **not** say that arbitrary PEPS can be
contracted efficiently.

As printed, the theorem takes:

- an unnormalised, injective PEPS \(\lvert\omega\rangle\) on a constant-
  dimensional lattice of \(N\) spins;
- bond dimension \(D\) and finite physical dimension;
- a local tensor collection \(\{A_i\}\);
- a parent Hamiltonian \(H_*\) that is *uniformly* gapped by a constant
  \(\Delta_*>0\);
- a condition-number bound
  \(\kappa_*=\max_i\kappa(A_i)\);
- an observable \(O_X\) with \(|X|<k\) for constant \(k\).

It outputs a scalar \(\widetilde O_X\) satisfying the additive absolute error

\[
\left|
\frac{\langle\omega|O_X|\omega\rangle}{\langle\omega|\omega\rangle}
-\widetilde O_X
\right|\leq\epsilon.
\]

For a patch radius

\[
\ell\in O\!\left(
\frac{2\ln\kappa_*+\ln(\epsilon^{-1})+\ln\|O_X\|}
{\Delta_*}
\right),
\tag{1}
\]

the source states deterministic classical time

\[
(D d)^{O(\ell^d)}
\]

and quantum time

\[
\widetilde O(\ell^d/\epsilon^2)
\]

with depth \(O(\operatorname{polylog}(\ell/\epsilon))\).

The paper uses the same symbol \(d\) for both lattice dimension and physical
spin dimension. To make the theorem legible without changing it, the
complexity should be read as

\[
(D d_{\mathrm{phys}})^{O(\ell^{d_{\mathrm{lat}}})}
\]

and the patch contains \(O(\ell^{d_{\mathrm{lat}}})\) spins.

For polynomially scaling \(D\), \(\kappa_*\), \(\epsilon^{-1}\), and
\(\|O_X\|\), with constant \(d_{\mathrm{lat}}\), \(d_{\mathrm{phys}}\), and
\(\Delta_*\), Eq. (1) gives \(\ell=O(\log N)\), and the printed classical
bound is quasi-polynomial rather than polynomial in general dimensions. The
paper separately notes that the one-dimensional MPS case can be handled in
polynomial time.

## 3. The conjecture objects are not the theorem

The source first fixes a local Hamiltonian
\(H=\sum_i h_i\) on a regular lattice, with a constant gap
\(\Delta>0\) above a unique ground state \(\rho\), and constant-support local
observables \(O_X\).

### Weak PEPS conjecture

Conjecture 1 says that for every such \(O_X\) and every \(\epsilon>0\), a PEPS
\(\omega\) of bond dimension \(O(\operatorname{poly}(N,\epsilon^{-1}))\)
exists such that

\[
|\operatorname{tr}(O_X\rho)-\operatorname{tr}(O_X\omega)|<\epsilon.
\]

This is a local-expectation approximation conjecture. The source mentions
stronger trace-norm and relative-entropy approximations in the one-dimensional
discussion, but it does not place a global trace-norm or fidelity conclusion
into Conjecture 1 for general higher-dimensional PEPS.

### Strong PEPS conjecture

Conjecture 2 adds that the approximating PEPS is injective and that its parent
Hamiltonian \(H_*\) has a constant spectral gap \(\Delta_*>0\). The source
motivates this by wanting the approximation to reproduce qualitative
correlation behaviour, not merely isolated numbers.

The paper says this strong form is available for states in the trivial phase
that can be quasi-adiabatically prepared from a product state. It explicitly
states that neither conjecture captures non-injective PEPS, non-unique ground
states, or intrinsic topological order. Those exclusions are load-bearing.

Theorem 1 is a conditional contraction theorem for a PEPS already satisfying
its hypotheses. Conjecture 2 is the proposed bridge from suitable gapped
ground states to such PEPS. The conjecture cannot be cited as a proved
generic-PEPS premise.

## 4. Assumption ledger

| object | exact source meaning | consequence |
|---|---|---|
| injectivity | after blocking a constant number of adjacent tensors, every local PEPS map \(A_v\) has a Moore–Penrose left inverse \(A_v^{-1}\) with \(A_v^{-1}A_v=I\) | permits the proof to remove boundary tensors using inverse maps; excludes generic non-injective and topological PEPS |
| parent Hamiltonian | the standard frustration-free local parent Hamiltonian of the injective PEPS, with the PEPS as unique ground state | the proof is not for an arbitrary Hamiltonian merely having a nearby PEPS state |
| uniform gap | every parent Hamiltonian \(H_t\) for every prefix/sub-PEPS \(\{A_v\}_{0\leq v\leq t}\) has gap \(\Delta_t\geq\Delta_*\) | strictly stronger than knowing only that the terminal parent Hamiltonian \(H_*=H_N\) is gapped |
| condition number | \(\kappa_*=\max_i\kappa(A_i)\), with the proof using \(\kappa(A_i)^2\) after division by the inverse-map norm | representation- and blocking-dependent numerical assumption; the theorem's useful radius grows logarithmically in \(\kappa_*\) |
| observable | \(O_X\) has support on fewer than constant \(k\) sites; \(X\) may be disconnected | covers a fixed-order correlation observable, not an extensive/global observable |
| error | additive absolute scalar error in one normalized expectation value | not state-vector error, trace distance, fidelity, instrument distance, or a joint outcome-law norm |
| geometry | regular cubic lattice in constant finite spatial dimension, finite local spin dimension | not an arbitrary graph or an infinite-dimensional local space |
| scaling regime | quasi-polynomial summary assumes polynomially bounded bond dimension and condition number, inverse-polynomial target error, polynomial observable norm, and constant gap/dimensions | dropping any one of these assumptions can invalidate the stated regime |

The paper's phrase “uniformly gapped parent Hamiltonian” is defined on p. 3 by
the entire family \(\{H_t\}_{0\leq t\leq N}\). Reading it as a gap only for
\(H_*\) would weaken the actual theorem.

## 5. Proof reconstruction

### 5.1 PEPS representation

The source writes the PEPS as local maps \(A_v\) applied to maximally entangled
virtual pairs,

\[
|\psi\rangle=\bigotimes_{v\in V}A_v\bigotimes_{e\in E}|\phi_e\rangle.
\tag{2}
\]

After constant blocking, injectivity makes the individual \(A_v\)
left-invertible.

### 5.2 Gapped prefix sequence

The proof orders the tensors so that the last
\(N_b=O(\ell^{d_{\mathrm{lat}}-1})\) tensors form a boundary at graph distance
\(\ell\) around \(X\). It defines normalized prefix states

\[
|\omega_i\rangle=
\frac{A_i\cdots A_1|\phi\rangle^{\otimes n}}
{\|A_i\cdots A_1|\phi\rangle^{\otimes n}\|},
\tag{8}
\]

with corresponding parent Hamiltonians \(H_i\). The uniform-gap assumption is
then invoked to apply exponential clustering to every \(H_i\), not just to the
final state.

### 5.3 One boundary-removal step

For each boundary tensor the proof chooses

\[
O_i=(A_i^{-1})^\dagger A_i^{-1}.
\]

Exponential clustering bounds the connected correlation between \(O_X\) and
\(O_i\). Dividing by the expectation of \(O_i\) maps the expectation in
\(|\omega_i\rangle\) to the one in \(|\omega_{i-1}\rangle\). Eqs. (10)–(13)
bound the additive error of that step by

\[
e^{-O(\ell\Delta_*)}\|O_X\|\kappa(A_i)^2.
\]

The condition number enters squared. It is not a discarded-weight or
state-fidelity quantity.

### 5.4 Boundary accumulation and radius

Applying the triangle inequality for
\(O(\ell^{d_{\mathrm{lat}}-1})\) removed boundary tensors gives Eq. (14),

\[
\left|
\langle\omega_*|O_X|\omega_*\rangle
-\frac{\langle\omega|O_X|\omega\rangle}{\langle\omega|\omega\rangle}
\right|
\leq
\ell^{d_{\mathrm{lat}}-1}
e^{-O(\ell\Delta_*)}
\kappa_*^2\|O_X\|.
\]

Eq. (15), matching main-text Eq. (1), chooses a logarithmic radius to make
this no larger than the requested additive error.

### 5.5 Patch factorization and contraction

After removing the boundary, the normalized state factors into a remainder
and a patch,

\[
|\omega_*\rangle=|\omega_R\rangle\otimes|\omega_P\rangle.
\tag{17}
\]

Because \(O_X\) acts only on the patch and
\(\langle\omega_R|\omega_R\rangle=1\), the numerator and denominator reduce
to the patch expression in Eq. (18). The proof therefore never computes the
global PEPS norm. Exact brute-force contraction of the patch gives the stated
\((D d_{\mathrm{phys}})^{O(\ell^{d_{\mathrm{lat}}})}\) time.

### Replay ledger

| input | transformation | assumption | output | exact source location | status |
|---|---|---|---|---|---|
| local PEPS tensors | block a constant number and regard each \(A_v\) as left-invertible | injectivity | invertible local PEPS maps | p. 3, injectivity paragraph | closed |
| tensor ordering around \(X\) | choose the final \(O(\ell^{d-1})\) tensors as a boundary | injectivity and lattice geometry | prefix family \(\{H_i,|\omega_i\rangle\}\) | p. 3 proof sketch; p. 5 Eq. (8) | closed |
| every prefix state | apply exponential clustering to \(O_X\) and \(O_i\) | uniform gap \(\Delta_i\geq\Delta_*\) for every \(i\) | connected-correlation bound | p. 3 Eq. (3); p. 5 Eq. (9) | closed under the strong gap assumption |
| one boundary tensor | choose \((A_i^{-1})^\dagger A_i^{-1}\), divide by its expectation | finite condition number | expectation change bounded by \(\kappa(A_i)^2\) | pp. 3–4 Eqs. (4)–(5); p. 6 Eqs. (10)–(13) | closed |
| all boundary tensors | sum per-step errors | boundary size \(O(\ell^{d-1})\) | Eq. (14) total additive error | p. 6 | closed asymptotically |
| requested \(\epsilon\) | choose Eq. (15) radius | constant gap and controlled \(\kappa_*,\|O_X\|\) | local patch sufficient to additive error | p. 6 Eq. (15) | closed asymptotically |
| separated patch | discard the normalized remainder scalar | exact factorization after boundary removal | patch-only normalized expectation | p. 6 Eqs. (17)–(18) | closed |
| patch tensor network | exact finite contraction | finite dimensions | classical estimate | p. 6 after Eq. (18) | closed |

## 6. Quantum-computer claim

The appendix invokes an external PEPS-preparation method for the patch of
\(O(\ell^{d_{\mathrm{lat}}})\) spins. It states preparation time

\[
O\!\left(
\ell^{d_{\mathrm{lat}}}
\operatorname{polylog}(\ell/\epsilon)
\right)
\]

with trace-distance error \(\epsilon\), parallel depth
\(O(\operatorname{polylog}(\ell/\epsilon))\), and
\(O(1/\epsilon^2)\) independent preparations and measurements. This yields the
reported \(\widetilde O(\ell^{d_{\mathrm{lat}}}/\epsilon^2)\) time.

This is repeated independent state preparation followed by estimation of one
local observable. It is not a sequential measurement process, a mid-circuit
reset protocol, a conditional branch simulator, or a multi-time measurement
Record generator.

The quantum claim also relies on the external preparation result cited as
Ref. 32; the present paper does not reprove that algorithm in full.

## 7. Transfer-operator and LTQO claims

The main text is careful that the proof does **not** establish LTQO as defined
in Ref. 33. The proof adds boundary terms to keep a unique ground state, whereas
the cited LTQO definition allows only removal of boundary Hamiltonian terms.
The paper therefore claims only a variant of LTQO with unique ground states.

The transfer-operator appendix adds assumptions beyond the bare theorem:

- validity of Conjecture 2;
- all assumptions of Theorem 1;
- translational invariance;
- a one-dimensional line \(L\) obtained after contracting the rest of the
  cubic lattice.

Under those conditions it defines the line transfer operator in Eqs. (19)–(21),
uses exponential decay of two-point correlations in Eq. (22), and concludes

\[
\frac{\lambda_2}{\lambda_1}\leq e^{-c_2\delta}
\tag{24}
\]

for the two largest transfer-operator eigenvalues. This is a conditional gap
claim for that induced one-dimensional transfer operator. It is not a theorem
that every PEPS transfer operator, arbitrary two-dimensional environment map,
or non-injective/topological transfer operator is gapped.

## 8. Printed formula and argument anomalies

These points must be preserved rather than silently repaired in any future
source-only note:

1. **Overloaded \(d\).** The theorem uses \(d\) both for lattice dimension and
   physical dimension, including in \((Dd)^{O(\ell^d)}\). The two roles have
   to be separated when applying the bound.
2. **Undefined transfer symbol.** The \(\delta\) in Eqs. (22) and (24) is not
   defined in the transfer-operator section. The text verbally relates the
   decay/gap to the parent-Hamiltonian gap, but the printed quantitative
   relation is incomplete.
3. **Quantum patch-size inconsistency.** Earlier the source obtains
   \(\ell=O(\log N)\), so a \(d_{\mathrm{lat}}\)-dimensional patch has
   \(O(\log^{d_{\mathrm{lat}}}N)\) spins. Page 7 instead prints
   \(\ell^d=O(\log N)\). That equality is valid only with an additional
   restriction or altered choice of \(\ell\), neither of which is stated.
4. **Constant-time wording omits \(D\).** The discussion after Theorem 1 says
   deterministic time is constant when \(d,\Delta_*,\kappa_*,\epsilon\) are
   constant, but the theorem's runtime still contains the bond dimension
   \(D\). Constant time additionally requires bounded \(D\), or the statement
   must be read as constant in \(N\) only under such a bound.
5. **Observable-norm dependence in sampling.** The quantum
   \(O(1/\epsilon^2)\) Chernoff count is stated without a
   \(\|O_X\|^2\) or variance factor, although Theorem 1 permits general
   \(\|O_X\|\) and Eq. (1) retains it. The sampling statement is directly
   justified only for a suitably normalized/bounded observable.
6. **Big-O inside a negative exponential.** Eqs. (3)–(5) and (9)–(14) use
   \(e^{-O(\ell\Delta_*)}\) as an upper bound without exposing the positive
   clustering constants. This conveys exponential decay but is not a
   numerically executable error certificate.
7. **Non-injective approximation sentence.** Page 3 says any non-injective
   PEPS is \(\epsilon\)-close to an injective one but specifies no norm and
   supplies no gap or condition-number control. This sentence does not extend
   Theorem 1 to non-injective PEPS.
8. **Transfer injectivity wording.** Page 7 first says that injectivity of the
   MPS is inherited by the PEPS, but the subsequent derivation uses the
   opposite direction—line-MPS injectivity inherited from PEPS injectivity.
9. **Transfer spectral expansion.** Eq. (23) writes a simple left/right
   eigenvector expansion and does not discuss non-diagonalizable transfer
   operators or Jordan blocks. The intended spectral-gap conclusion may be
   recoverable by a more careful argument, but that treatment is absent here.
10. **Main/appendix cross-references.** Main-text p. 4 refers to Eqs. (17) and
    (18) while the adjacent displayed formulas are numbered (6) and (7).
    The appendix later repeats them as (17) and (18), so the objects can be
    identified, but the local references are confusing.

## 9. Evidence boundary

| assigned row | exact source location | paper says | paper does not say | source-local status |
|---|---|---|---|---|
| conditional local-observable theorem | Theorem 1 and Eq. (1), p. 2; proof Eqs. (8)–(18), pp. 5–6 | one normalized local expectation can be approximated to additive error under the theorem assumptions | arbitrary PEPS contraction is efficient | closed |
| injectivity assumption | p. 3 injectivity definition | constant-block injectivity supplies left inverses | generic non-injective or G-injective PEPS satisfy the theorem | closed as assumption |
| uniform gap assumption | p. 3 definition; pp. 3 and 5 proof setup | every prefix/sub-PEPS parent Hamiltonian is gapped by \(\Delta_*\) | a gap only for the terminal parent Hamiltonian suffices | closed as assumption |
| condition-number assumption | Theorem 1, p. 2; Eqs. (13)–(15), p. 6 | error carries \(\kappa_*^2\), radius carries \(2\ln\kappa_*\) | the bound is gauge/representation independent or well-conditioned automatically | closed as assumption |
| error norm | Theorem 1, p. 2 | absolute additive error in one scalar normalized expectation | state trace distance, global fidelity, or Record TV | closed |
| deterministic complexity | Theorem 1, pp. 2–3; after Eq. (18), p. 6 | \((Dd)^{O(\ell^d)}\), quasi-polynomial in the stated controlled regime | general polynomial-time two-dimensional contraction | closed with notation qualification |
| quantum complexity | Theorem 1, p. 2; quantum appendix, p. 7 | patch preparation and repeated measurement give \(\widetilde O(\ell^d/\epsilon^2)\) time and polylogarithmic depth | a complete quantum execution proof independent of Ref. 32 or arbitrary-norm sampling bound | qualified |
| standard LTQO | p. 4, LTQO discussion | the proof yields only a boundary-term variant | standard LTQO follows | contradicted by source |
| transfer-operator gap | pp. 4 and 7, Eqs. (19)–(24) | conditional induced line-transfer gap under extra assumptions | all PEPS transfer/environment operators are gapped | qualified |
| generic/non-injective PEPS | pp. 2–3; conclusion p. 4 | excluded; G-injective extension left as future work | theorem applies after an uncontrolled perturbation to injectivity | missing |
| intrinsic topological PEPS | Conjecture discussion, p. 2; conclusion p. 4 | neither conjecture captures intrinsic topological order | a topological-sector or degenerate-ground-space theorem | missing |
| global-state fidelity | Conjecture discussion p. 2; Theorem 1 p. 2 | only local expectations are controlled by the higher-dimensional theorem | global state fidelity or trace-norm approximation | missing |
| measurement/reset branches | full-text boundary; quantum appendix p. 7 | independent preparation and measurement of \(O_X\) | Born-branch ledger, conditional post-measurement states, or reset instrument | missing |
| detector/observable Record | full-text boundary | no multi-round QEC measurement object is defined | raw measurement law, temporal detector fold, logical-observable bits, or Record distance | missing |
| practical PEPS truncation guarantee | proof and conclusion, pp. 3–4 and 5–6 | exact contraction of a theoretically sufficient finite patch | a finite-bond environment truncation rule or global error certificate for numerical PEPS algorithms | missing |

## 10. Admission-pending disposition

This source can support a future atomic evidence record for:

- Theorem 1's conditional, additive local-expectation approximation;
- the exact injectivity, uniform-prefix-gap, condition-number, locality, and
  dimension assumptions;
- the patch radius and classical/quantum complexity formulas as printed,
  accompanied by the anomalies above;
- the explicit exclusion of non-injective and intrinsically topological PEPS;
- the distinction between the source's boundary-term LTQO variant and standard
  LTQO;
- the conditional one-dimensional transfer-operator statement.

It cannot support:

- generic, non-injective, G-injective, or topological PEPS contraction;
- global wavefunction fidelity or trace-distance control;
- conditional measurement branches, reset semantics, or a multi-time Record;
- a finite-bond PEPS truncation guarantee;
- a CAPEPS implementation or efficiency comparison;
- a claim that a terminal parent gap alone is sufficient;
- a numerical error certificate obtained by substituting values into the
  paper's hidden-constant \(e^{-O(\ell\Delta_*)}\) notation.

Review read status: `complete`

Review evidence status: `persisted`

Source-note admission status: `pending`
