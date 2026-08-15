# Vanderstraeten et al. arXiv:2110.12726v2 — source-only audit

Date: 2026-07-27

Status: `DRAFT_REPAIRED_PENDING_INDEPENDENT_SOURCE_ONLY_REREVIEW`

Independent admission reviewer: `pending`

Source: arXiv:2110.12726v2

Scope: infinite-PEPS contraction mechanisms, assumptions, observables,
benchmarks, failure cases, and source-local absences

The complete 18-page source was read in order. PDF pages 1--12 and 14--18 were
rendered, with the load-bearing identities, equations, plots, applicability
limitation, and failure case visually checked. Text extraction was used for
navigation only. This packet is a source reconstruction, not an admission
review; admission requires a fresh independent source-first rereviewer after
the corrections required by the first independent review.

## 1. Pinned source

| field | value |
|---|---|
| title | *Variational methods for contracting projected entangled-pair states* |
| authors | Laurens Vanderstraeten, Lander Burgelman, Boris Ponsioen, Maarten Van Damme, Bram Vanhecke, Philippe Corboz, Jutho Haegeman, Frank Verstraete |
| version | arXiv:2110.12726v2, version stamp 7 June 2022 |
| source URI | `https://arxiv.org/abs/2110.12726v2` |
| source artifact | `docs/papers/2110.12726v2.pdf` |
| SHA-256 | `58763a732ef1c5b660bacbc708a2134b1c8a09096eca1e44326c03a1b540a184` |
| extent | 18 pages |

## 2. Source question and bounded answer

The paper asks when contraction of an infinite translationally invariant PEPS
can be cast as an algorithm-independent variational problem, and how common
boundary-MPS and CTMRG contractions compare inside that setting.

Its positive result is deliberately restricted. When the relevant PEPS
transfer matrix is Hermitian, the dominant boundary MPS can be characterized
by a variational free-energy-density objective. The authors derive direct
optimization and VUMPS fixed-point forms, extend the machinery to selected
multi-row settings and finite-window evaluations of general correlation
functions, and benchmark them on symmetry-constrained, optimized infinite
PEPS for the square-lattice \(J_1\)-\(J_2\) model.

This is not a generic exact-contraction theorem. It does not turn environment
bond dimension \(\chi\) into the PEPS virtual bond dimension \(D\), certify a
finite-\(\chi\) state norm or global fidelity, or define a selective
measurement--reset--Record instrument.

The paper also gives an explicit applicability warning for the Hermitian
subclass. Hermiticity forces the transfer-matrix eigenvalues to be real; using
the cited MPS relation between transfer eigenvalues and dominant correlation
wavevectors, the authors expect ground states with dominant incommensurate
correlations, including critical states at incommensurate filling, to be
poorly represented by this subclass. The construction studied is restricted
to square-lattice PEPS; triangular, kagome, and more complicated unit-cell
settings are left for future work.

## 3. Assigned closure rows

| row | exact source location | source says | source does not say | status |
|---|---|---|---|---|
| infinite-PEPS contraction controls | PDF pp. 1--2, Introduction and Sec. II | The PEPS ansatz has virtual bond dimension \(D\); approximate contraction introduces a separate environment bond dimension \(\chi\). CTMRG truncates environment tensors to \(\chi\), while boundary-MPS methods approximate a transfer-matrix fixed point with an MPS of bond \(\chi\). | It does not identify \(D\) and \(\chi\), nor make finite \(\chi\) exact. | `closed` |
| Hermitian transfer-matrix subclass | PDF pp. 3--4, Eqs. (13)--(20), and PDF p. 12, Discussion and Outlook | Reflection/time-reversal or a more general local tensor condition can make the relevant transfer matrix Hermitian, including stated larger-unit-cell constructions. The source explicitly expects states with dominant incommensurate correlations to be poorly represented because the subclass has only real transfer eigenvalues, and it studies square-lattice PEPS only. | Hermiticity is not claimed for arbitrary PEPS tensors, chiral states, incommensurate-correlated states, other lattices, or arbitrary unit cells. | `closed_with_explicit_applicability_limit` |
| variational boundary contraction | PDF pp. 4--5, Eqs. (21)--(35) | For the Hermitian subclass, the dominant boundary MPS minimizes the free-energy-density objective in Eqs. (23) and (25); its gradient and VUMPS fixed-point equations are derived. | The derivation is not a global state-fidelity or local-observable error certificate at a chosen \(\chi\). | `closed_at_source_conditions` |
| two-row and three-or-more-row boundary | PDF pp. 5--6, Sec. IV.B, Eqs. (36)--(43); PDF p. 6, Sec. IV.C, Eqs. (44)--(48); Appendix B, PDF pp. 15--18, Eqs. (B1)--(B14) | The two-row construction admits the stated variational treatment. For three or more rows, the simultaneous free-energy variational characterization can break down, while the sequential normalized-fidelity objective in Eq. (48), matched by Eq. (B4), remains available. | The source does not prove convergence of multi-site VUMPS for all larger unit cells. | `closed_with_explicit_failure_boundary` |
| finite-window correlation summation | PDF pp. 6--8, Sec. V, Eqs. (49)--(68), with the local perturbation and finite-window operation in Eqs. (58)--(68) | A finite-window MPS is updated through variational normalized-fidelity steps to evaluate contributions to general two- and \(N\)-point correlation functions. | The summed structure factor is not itself variational, and window size and \(\chi\) remain approximation controls. | `closed_as_algorithm` |
| finite-\(\chi\) energy gradient | PDF p. 8, Energy gradient paragraph | Automatic differentiation can evaluate a finite-\(\chi\) energy gradient; the approximate summation construction is exactly compatible with the gradient only in the infinite-\(\chi\) regime. | The paper does not certify finite-\(\chi\) optimization as the infinite-environment PEPS optimum. | `closed_with_source_caveat` |
| reported contraction benchmarks | PDF pp. 9--11, Figs. 1--6 | On selected symmetry-constrained \(J_1\)-\(J_2\) PEPS with PEPS virtual bond dimension \(D=5\), the variational boundary MPS and CTMRG approach comparable local energies as \(\chi\) grows; the window-MPS scheme is more accurate for the shown structure factors. | These are selected numerical comparisons, not a theorem of equivalence or a matched CAPEPS/full-PEPS runtime-memory study. | `closed_at_displayed_workloads` |
| monotonic variational quantity | PDF p. 9, Fig. 1 and Sec. VI.A | The optimized free-energy proxy \(f=-\log\lambda\) decreases monotonically with increasing boundary bond dimension in the displayed variational calculation. | The paper does not establish monotonicity of local energy, structure factor, global fidelity, Record-TV, or any syndrome statistic. | `closed_only_for_displayed_variational_objective` |
| multi-site VUMPS counterexample | Appendix B, PDF pp. 15--18, Eqs. (B1)--(B14) and Figs. 7--10 | The paper distinguishes free-energy and normalized-fidelity optimality and shows a three-row Ising transfer-matrix case in which multi-site VUMPS becomes unstable near criticality while the power method converges. | It does not support a generic multi-site-VUMPS convergence assumption. | `closed_as_disconfirmation` |
| QEC instrument and CAPEPS bridge | complete source scope, bounded by Discussion on PDF pp. 11--12 | The source studies deterministic infinite-PEPS contraction and correlation functions. | It contains no Clifford frame, selective Born branches, reset map, ordered raw-history mass, detector/observable Record fold, conditional fidelity, Record-TV, or CAPEPS/full-PEPS comparison. | `missing` |

## 4. Notation ledger

| symbol | source meaning | exact locator | project-use constraint |
|---|---|---|---|
| \(A\) | local PEPS tensor in an infinite repeated unit cell | PDF pp. 1--2, Sec. II and Eq. (1) | state-ansatz tensor, not an environment |
| \(D\) | virtual bond dimension of the PEPS tensor | PDF pp. 1--2 | controls the PEPS variational class |
| \(\chi\) | bond dimension of CTMRG or boundary-MPS environment tensors | PDF pp. 1--3 | contraction-accuracy control distinct from \(D\) |
| \(\mathcal T\) | one- or multi-row PEPS transfer matrix | PDF pp. 2--6 | variational results require the stated Hermiticity conditions |
| \(M,\widetilde M\) | independently parametrized boundary MPSs found from the two directions in the general contraction environment | PDF p. 3, Sec. II, Eqs. (10)--(12) and footnote 3 | there is generally no simple relation between them |
| \(M,\bar M\) | boundary-MPS tensor in the Hermitian variational ket \(\lvert\Psi_M\rangle\) and its complex-conjugate bra tensor in \(\Lambda(M,\bar M)\) | PDF p. 4, Sec. IV.A, Eqs. (24)--(29) | this ket/bra pair is not the independently parametrized \(M,\widetilde M\) pair |
| \(\Lambda,\lambda\) | extensive transfer eigenvalue and per-site channel eigenvalue | PDF p. 4, Eqs. (21)--(28) | generate the norm/free-energy-density objective |
| \(f=-\log\lambda\) | source variational free-energy-density proxy | PDF p. 4, Eqs. (22)--(25) | not physical energy or state fidelity |
| \(N\)-point | number of operator insertions in a general correlation function | PDF p. 1, Abstract; PDF p. 6, Sec. V opening | correlation-function order, not window length |
| \(N_i\), displayed as \(N_1,N_2,\ldots,N_L\) | non-translation-invariant tensors inside the finite window; the displayed terminal index is \(L\) | PDF p. 8, Eq. (62) | do not relabel Eq. (62)'s terminal \(L\) as the benchmark window-size symbol \(N\) |
| \(N\) (benchmark window size) | window-size control used in the structure-factor benchmarks, including \(N=10\) in Fig. 6 | PDF pp. 10--11, Sec. VI.C prose and Figs. 5--6 | second benchmark approximation control in addition to \(\chi\), distinct from \(N\)-point order and Eq. (62)'s \(N_i,\ldots,N_L\) notation |

## 5. Operation replay

### 5.1 CTMRG and boundary-MPS contraction

Start from an infinite PEPS with virtual bond \(D\). CTMRG grows a local
environment and truncates its tensors to \(\chi\). The boundary-MPS route
instead treats a row transfer matrix as an MPO and approximates its dominant
left/right fixed points by independently parametrized \(M,\widetilde M\)
boundary MPSs of bond \(\chi\), as in PDF p. 3, Eqs. (10)--(12) and footnote
3. Local observables are then formed by inserting the operator into the
corresponding approximate environment. Both are approximate for finite
\(\chi\).

### 5.2 Variational boundary MPS

Under the source's transfer-matrix Hermiticity condition, the PEPS norm is an
infinite power of the leading transfer eigenvalue and defines

\[
f(A,\bar A)=-\log\lambda.
\]

At fixed \(\chi\), the boundary tensor \(M\) in the Hermitian variational ket
\(\lvert\Psi_M\rangle\), paired with its complex-conjugate bra tensor
\(\bar M\), is chosen by the objective in PDF p. 4, Eqs. (24)--(29), with
Eq. (25) stating the optimization. This \(M,\bar M\) ket/bra pair is not the
general Sec. II \(M,\widetilde M\) left/right pair. Equation (30) gives the
gradient, and Eqs. (32)--(35) recover the VUMPS fixed-point equations. The
invariant is optimality of this fixed-\(\chi\) boundary objective, not exact
equality to the infinite-\(\chi\) contraction.

### 5.3 Correlation window

The source's “\(N\)-point” wording counts operator insertions in a general
correlation function (PDF p. 1, Abstract; PDF p. 6, Sec. V opening); it is not
the window length. PDF p. 8, Eq. (62) writes the finite-window tensors as
\(N_i\), displaying \(N_1,N_2,\ldots,N_L\), and Eqs. (64) and (68)
variationally compress the window by maximizing normalized fidelity. The
benchmark prose on PDF pp. 10--11 and Figs. 5--6 separately use \(N\) for the
window size, including \(N=10\) in the Fig. 6 caption. Increasing this
benchmark window-size \(N\) adds correlation-function contributions. Figure 5
shows that inadequate \(\chi\) can prevent convergence to the correct
displayed result even when that window size is increased. The paper therefore
supplies no universal finite-\((\chi,\text{benchmark window-size }N)\) error
certificate.

### 5.4 Larger-unit-cell failure replay

Appendix B separates two objectives: blocked single-row free-energy optimality
and sequential normalized-fidelity optimality. For two rows they are
compatible in the stated construction; for three or more rows the free-energy
interpretation of multi-site VUMPS need not hold. In the explicit three-row
Ising example, Figs. 9--10 show instability near \(T_c\). This is a source
counterexample to assuming generic convergence, not a defect to suppress.

## 6. Project application and kill conditions

This source may support only the following bounded statements:

1. PEPS contraction introduces an environment accuracy parameter \(\chi\)
   separate from the PEPS virtual bond dimension \(D\).
2. A Hermitian-transfer subclass admits a variational boundary-MPS objective.
3. CTMRG and boundary-MPS contractions can be empirically compared at matched
   \(\chi\), but finite-\(\chi\) observables remain approximate.
4. Multi-site VUMPS has an explicit larger-unit-cell failure mode.
5. The Hermitian subclass has an explicit expected failure regime for dominant
   incommensurate correlations and was developed only for square-lattice PEPS
   in this source.

The following inferences are killed without independent mechanisms and target
experiments:

- “variational contraction” means exact generic PEPS contraction;
- the Hermitian subclass safely represents states with dominant
  incommensurate correlations or transfers unchanged to non-square lattices;
- monotone norm/free-energy improvement implies monotone energy, fidelity, or
  Record-law improvement;
- environment \(\chi\) is interchangeable with PEPS virtual bond \(D\);
- agreement of two methods on the displayed workloads is an independent exact
  reference;
- deterministic expectation-value contraction supplies Born branch masses,
  reset correctness, or a repeated-round Record pushforward;
- the source establishes a CAPEPS efficiency advantage over full PEPS.

## 7. Source-local verdict

- `read_status: complete`
- `evidence_status: persisted_repaired_pending_independent_source_only_rereview`
- infinite-PEPS contraction taxonomy: `closed`
- Hermitian-transfer variational principle:
  `closed_with_explicit_incommensurate_and_lattice_limit`
- finite-\(\chi\) exactness or certified state fidelity: `missing`
- CTMRG/boundary-MPS benchmark: `closed_at_displayed_workloads`
- generic multi-site VUMPS convergence: `contradicted_by_source_counterexample`
- PEPS-virtual-\(D\)/environment-\(\chi\) interchangeability: `contradicted`
- measurement--reset--Record instrument: `missing`
- Clifford-augmented PEPS construction: `missing`
- matched CAPEPS/full-PEPS runtime and memory result: `missing`

Admission remains pending a fresh independent full-source semantic rereview
and artifact-verified schema validation of the repaired companion note.
