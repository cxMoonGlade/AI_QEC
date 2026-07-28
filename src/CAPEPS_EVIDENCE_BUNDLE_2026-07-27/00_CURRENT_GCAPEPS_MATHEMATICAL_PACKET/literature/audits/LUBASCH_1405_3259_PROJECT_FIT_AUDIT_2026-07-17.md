# Claim audit — Lubasch finite-PEPS source and current carrier questions

## Status and decision

This packet asks a bounded source-selection question: which current tensor-network carrier claims may
use Lubasch, Cirac, and Bañuls, *Algorithms for finite projected entangled pair states*, and which
claims must remain outside that source's evidentiary scope?

Decision: retain the paper for finite open-boundary PEPS representation, environment contraction,
positive-environment repair, reduced-tensor update, and PEPS gauge-conditioning facts. Do not use it
as evidence for restricted MPS actual-split semantics, stochastic trajectory probability mass,
finite-truncation record faithfulness, or a multi-time detector/observable record bound.

This packet changes no `src/**` file and authorizes no implementation or scientific claim upgrade.

## Frozen question charter

| field | frozen value |
|---|---|
| decision/consequence | Decide the exact source-only facts that may enter the current Lubasch reading note and prevent those facts from being promoted into a record-faithfulness premise. |
| importance x attackability | A metadata or scope error can contaminate the admitted RAG/KG corpus; the versioned PDF, local carrier contracts, and exact source locators make this directly auditable. |
| reusable object/test | A source-only reading note, a separate project-fit packet, artifact hashes, manifest admission, and RAG/KG queries that return the corrected facts. |
| mechanism | Finite open-boundary PEPS imaginary-time update using approximate environment contraction and alternating local tensor solves. |
| observable/record object | The paper evaluates norm-contraction error, local expectation values, energies, spin correlators, and linear-solve conditioning; the repository product is instead a multi-time detector/observable record. |
| mechanism-to-observable bridge | The paper connects cluster environment size to local-observable contraction error and fitted correlation length in specified Ising PEPS; it gives no bridge to the repository record law. |
| predicted direction/scale | In the reported 21 x 21 Ising cases, the fitted characteristic cluster size approximately tracks the fitted correlation length; no transferable record-error scale is asserted. |
| alternatives/invariants | State bond dimension `D` is distinct from boundary-MPO bond dimension `D'`; exact norm-environment positivity is distinct from positivity after approximate contraction; OBC-MPS canonical gauging is distinct from PEPS gauge conditioning. |
| possible no-go | If the paper does not define stochastic selective measurements or a joint multi-time record, no local conditioning, contraction, or ground-state benchmark in it can certify record faithfulness. |
| implementation target | None. This is literature maintenance. Any future code use remains subject to `docs/SIMULATOR.md` and `docs/FAITHFULNESS_PROTOCOL.md`. |
| kill condition | Any proposed use of this paper as a finite-bond MPS split reference, branch-mass reference, or local-metric-to-record theorem is rejected unless a different exact source establishes that bridge. |

## Source integrity correction

The pinned artifact is `docs/papers/1405.3259v2.pdf`, SHA-256
`5d7e010293770b0c97ac9c0b88075710ceda3a68988da7933dd2130621d8269a`, 18 pages. Its title page and
the versioned arXiv record identify the source as *Algorithms for finite projected entangled pair
states*, accepted and published as Phys. Rev. B 90, 064425 (2014), DOI
`10.1103/PhysRevB.90.064425`. The prior admitted note incorrectly called it *Unifying projected
entangled pair state contractions*; that is a metadata error, not an alternate title in this
artifact.

## Assigned closure rows

| assigned row | exact source location | paper says | paper does not say | status |
|---|---|---|---|---|
| Finite PEPS object | Sec. II, Fig. 1, PDF p. 2 | The work studies finite `L x L` square-lattice pure PEPS with open boundaries, local physical indices, and virtual bond dimension `D`. | It does not define a stochastic state ensemble or emitted detector/observable record. | closed |
| Local update objective | Sec. II, Eq. (1), PDF p. 2 | A Suzuki-Trotter step is approximated by minimizing a Hilbert-space distance with ALS; the local solve uses the norm matrix `N_l` and overlap vector `b_l`. | It does not establish that the local cost controls a later adaptive measurement law. | closed |
| Environment versus state approximation | Sec. III.A and Fig. 2, PDF p. 3 | Row contraction uses a boundary MPO with bond dimension `D'`, separate from PEPS state bond dimension `D`. | Increasing `D` alone does not certify environment-contraction accuracy. | closed |
| Cluster-error scale | Sec. III.A.1 and Fig. 4, PDF p. 4; footnotes 53--55, PDF pp. 17--18 | For the specified Ising PEPS and fits, local-observable cluster error decays exponentially and its fitted scale `delta_0` approximately follows fitted correlation length `zeta`. | This is not a theorem for arbitrary PEPS, a state-fidelity bound, or a record-distance bound. | closed |
| Environment positivity | Sec. III.A.2 and Figs. 5--7, PDF pp. 4--6 | Exact norm contraction produces a Hermitian positive-semidefinite environment; general approximate boundary-MPO contraction need not preserve it, while purification can enforce positivity at higher cost. | Positivity alone does not recover the exact environment or certify a downstream observable. | closed |
| Reduced-tensor and positive repair | Sec. III.B.1 and Figs. 9--10, PDF p. 6 | QR/LQ isolates reduced tensors, and the approximate reduced environment is Hermitianized before negative eigenvalues are clipped to form a positive-semidefinite approximant. | The clipping operation is not proved to equal the exact environment. | closed |
| MPS/PEPS gauge boundary | Sec. III.B.2, PDF p. 7 | An OBC MPS norm matrix can be gauged to identity, whereas a PEPS generally has no corresponding canonical form; PEPS gauge choices instead improve conditioning. | PEPS gauge conditioning does not inherit OBC-MPS Schmidt-cut semantics. | closed |
| Conditioning interpretation | Sec. III.B.2 and Table I, PDF p. 8 | The proposed gauge choices reduce observed norm-matrix condition numbers and speed ALS convergence; the authors explicitly state that a large condition number does not by itself imply low solution accuracy. | Condition number is not presented as a physical or record-level error metric. | closed |
| Deterministic normalization | Sec. III.B.3, PDF p. 9 | The imaginary-time PEPS state is normalized after each set of Trotter gates and tensors are rescaled for numerical stability. | The source does not preserve or analyze unnormalized stochastic branch probability mass. | missing: source-local |
| Restricted MPS split | Full-text scope; contrast in Sec. III.B.2, PDF p. 7 | MPS appears as a structural comparison for canonical gauging. | The source does not specify the restricted MPS two-site actual-split algorithm, discarded-weight ledger, or swap topology. | missing: source-local |
| Multi-time record bridge | Full-text scope and Sec. V, PDF pp. 13--14 | Benchmarks concern finite-PEPS ground-state energies, local order parameters, and spin correlations. | The source defines no selective-measurement instrument, temporal detector fold, logical observable, joint record distribution, or total-variation bound. | missing: source-local |

## Operation replay

| input | transformation | assumption | output | exact source location | replay status |
|---|---|---|---|---|---|
| Finite OBC PEPS `|phi>` and one or more Trotter gates `O` | Minimize `|| |psi> - O|phi> ||^2` by ALS, holding all but one tensor fixed in each local solve | Product-formula real/imaginary-time step and a solvable local pseudoinverse problem | Updated finite PEPS tensors | Sec. II, Eq. (1), PDF p. 2 | complete |
| Double-layer norm tensor network | Contract rows into a boundary MPO and truncate/fit that boundary to bond dimension `D'` | The selected `D'` makes the contraction accurate enough for the stated calculation | Approximate `N_l` and environment tensors | Sec. III.A and Fig. 2, PDF p. 3 | complete |
| Ising PEPS, local `sigma^X` or `sigma^Z`, cluster size `delta` | Compare cluster contraction with full contraction and fit exponential decay; separately fit the correlator | `D'=100` removes visible `D'` dependence in the reported cases; fitted points are those specified in footnote 54 | Empirical `delta_0 approximately zeta` relation | Sec. III.A.1 and Fig. 4, PDF p. 4; footnotes 53--55, PDF pp. 17--18 | complete |
| Approximate reduced environment `N_red` | Form `(N_red + N_red^dagger)/2`, diagonalize, and set negative eigenvalues to zero | Euclidean nearest Hermitian/positive-semidefinite matrix is an appropriate numerical stabilizer for the local solve | Positive-semidefinite approximant `U Sigma_+ U^dagger` | Sec. III.B.1 and Fig. 10, PDF p. 6 | complete |
| Nonseparable PEPS pair environment | Derive QR/LQ gauges from the environment square root, transform the reduced tensors, initialize by SVD, and sweep ALS | Gauge insertions leave the PEPS state unchanged and improve the local norm-matrix conditioning | Better-conditioned local tensor update | Sec. III.B.2 and Figs. 11--13, PDF pp. 7--8 | complete |
| Imaginary-time PEPS after a set of Trotter gates | Normalize the state and rescale tensors to equalize their largest absolute entries | The target is a deterministic normalized state, not a stochastic unnormalized branch | Numerically rescaled PEPS representation | Sec. III.B.3, PDF p. 9 | complete |

No replay row produces a detector/observable record. Adding measurement branching, branch-mass
accounting, temporal folding, or record comparison would be an unsupported transformation.

## Project application

1. The paper is directly relevant to the retained finite-PEPS research carrier only at the level of
   representation, environment approximation, local update, positive repair, conditioning, and
   deterministic state benchmarks.
2. It supplies a useful separation between PEPS state bond `D` and boundary-environment bond `D'`.
   These are independent approximation controls and must not be collapsed into one truncation score.
3. The exact environment is positive semidefinite, but the paper's Hermitianization/eigenvalue
   clipping is a numerical repair of an approximate environment. It does not prove recovery of the
   exact environment.
4. The MPS comparison is a limitation on transfer: OBC-MPS canonical-cut semantics do not carry over
   to a generic PEPS loop. Restricted MPS actual-split evidence must continue to use an MPS-specific
   source and independent reconstruction.
5. The paper normalizes a deterministic imaginary-time state. That operation cannot be imported into
   a stochastic trajectory at a point where raw norm represents physical branch probability without
   a separate probability-law derivation.
6. Energy, correlator, condition number, local contraction error, and environment positivity remain
   state/local-solve diagnostics. None is a substitute for the full detector/observable record
   comparison required by `docs/METRICS.md` and `docs/FAITHFULNESS_PROTOCOL.md`.

## Competing evidence and kill conditions

- Paeckel et al., Secs. 2.4--2.6 and Eqs. (13)--(18), is the current source for OBC-MPS canonical-cut
  and direct singular-value truncation semantics. A Lubasch PEPS gauge statement must not replace it.
- Evenbly, Secs. II--V and Appendix C, is the current source for closed-loop bond environments and the
  normalized full-environment truncation objective. Lubasch does not provide that FET objective.
- Jaschke et al., Sec. III.B, and Sander et al., Secs. III--IV, are the current sources for stochastic
  quantum-trajectory branch and finite-bond projection semantics. Lubasch does not address those
  objects.
- Any attempt to infer full-record faithfulness from `delta_0 approximately zeta`, positive-semidefinite
  repair, improved conditioning, or converged ground-state observables fires the kill condition.

## Theory-first closure

Local discovery was run on 2026-07-17 with:

- `python tools/literature_rag.py query "finite PEPS boundary MPO contraction correlation length gauge fixing record faithfulness" --top-k 12`;
- `python tools/literature_kg.py concept "PEPS environment"`.

The RAG query returned the admitted Lubasch facts plus the adjacent Evenbly, Paeckel, YASTN, and
variPEPS sources. The pre-repair graph contained no Lubasch relations, which is an admission-quality
gap to be corrected in the reading note. No external discovery search was needed for this bounded
source-selection decision: all positive rows were checked against the pinned primary PDF, while the
unsupported rows are explicitly source-local and are not field-wide literature-gap claims.

- `read_status: complete`
- `evidence_status: persisted`
- `closure_status: closed` for the bounded source-selection decision
- closed rows: finite-PEPS object, local update, environment control, cluster-error scale, positivity,
  positive repair, and gauge-conditioning boundary
- source-local missing rows: stochastic branch mass, restricted-MPS split, and multi-time record bridge
- preregistration: not applicable; no experiment or implementation is proposed
- downstream scientific permission: `CODE_BLOCKED` for production pruning or record-faithfulness use
- allowed action: admit the corrected source-only note and rebuild the local literature surfaces
