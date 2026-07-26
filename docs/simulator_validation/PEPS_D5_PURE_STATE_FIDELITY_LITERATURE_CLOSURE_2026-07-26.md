# PEPS d5 pure-state fidelity — literature closure

Date: 2026-07-26  
Status: **closed for the bounded pure-state benchmark; not a QEC Record closure**

## Frozen claim

`decision/consequence`

: Decide whether a maintained finite-PEPS implementation can evolve a
  25-qubit, 5-by-5, checkerboard-X/Z-frame coherent circuit at useful global
  pure-state fidelity. A positive result permits a later, separately
  preregistered d5 measurement/Record experiment; it does not certify one.

`mechanism`

: Deterministic nearest-neighbour unitary evolution of a pure qubit state.
  Each edge gate is
  `exp(-i theta P_i tensor P_j / 2)`, where the checkerboard frame assigns
  `P=X` on one sublattice and `P=Z` on the other. Non-Clifford `RY` rotations
  follow each complete edge layer.

`observable`

: Exact normalized global pure-state fidelity
  `F=|<psi_ref|psi_TN>|^2/(<psi_ref|psi_ref><psi_TN|psi_TN>)`.

`mechanism-to-observable bridge`

: The candidate state and a separately constructed dense state represent the
  same frozen ordered gate list and basis convention. Their normalized overlap
  is evaluated from full `2^25` complex128 state vectors. Local discarded
  weight, BP residual, boundary-bond convergence, or a product of gate-local
  retained weights is not substituted for this overlap.

`predicted direction/scale`

: Increasing the retained PEPS edge bond should improve the overlap for this
  fixture. Four applications of an operator-Schmidt-rank-two gate to any one
  lattice edge prove only that a direct untruncated PEPS representation exists
  with per-edge `D <= 2^4 = 16`. They do not prove that a particular library
  update discards no rank at `D=16`; that requires a separately authenticated
  rank ledger. The engineering usefulness bands are preregistered separately
  and are not literature facts.

`alternative formulations/invariants`

: A Torch tensor-axis replay and an independent NumPy computational-basis
  bit-index replay must agree amplitude-by-amplitude on d3. Norm preservation,
  gate unitarity, the explicit half-angle matrices, qubit/basis ordering, and
  the per-edge rank-growth ledger are exact invariants.

`possible no-go`

: General exact PEPS contraction is `#P`-complete in the Schuch source's
  problem setting. That worst-case result blocks an unrestricted efficient
  solver; it does not prevent this fixed 25-qubit dense comparison.

`implementation target`

: Pristine full clones of `quantinuum-dev/pepsy`,
  `JoeyT1994/TensorNetworkQuantumSimulator.jl`, `yastn/yastn`, and
  `jcmgray/quimb`, with repository-owned neutral fixtures and adapters.

## Coverage ledger

| load-bearing row | required object | local evidence queried | external search queried | source / exact location | status | implication |
|---|---|---|---|---|---|---|
| finite 2D pure-state PEPS and local gate update | A finite planar pure-state network whose two-site updates become exact when no singular value is discarded | RAG: `finite PEPS quantum circuit gate evolution bond dimension contraction fidelity`; KG/current corpus audit | Reused the 2026-07-26 PEPS/PEPO AnySearch map; reran `finite PEPS quantum circuit exact state fidelity benchmark normalized overlap 5x5 square lattice` | Rudolph and Tindall note, Sec. II, Eqs. (1)-(2), PDF p. 3; Lubasch et al. note, Secs. II-III, PDF pp. 2-3 | closed | A finite PEPS is an appropriate representation, but the loopy simple-update error product is only approximate. |
| global pure-state fidelity | A metric comparing complete pure states rather than local truncation data | RAG: `PEPS global state fidelity normalized overlap truncation circuit simple update` | Same exact-fidelity batch plus `projected entangled pair state circuit simple update global fidelity exact statevector comparison` | Evenbly note, Sec. V, Eq. (12), PDF p. 6 | closed | Use the normalized squared overlap. |
| state-bond versus contraction-bond control | Separate representation and contraction approximations | RAG query above and `finite open-boundary PEPS`; current concept index | Reused PEPS/PEPO landscape queries | Lubasch et al., Sec. III.A and Fig. 2, PDF p. 3; Rudolph and Tindall, Sec. II, PDF pp. 3-4 | closed | The primary gate accepts only complete complex128 candidate vectors. A finite boundary bond or non-materialized overlap is `UNAVAILABLE`, not silently folded into `F`. |
| local diagnostic versus true global overlap | Evidence that the convenient retained-weight product is not the requested fidelity | RAG exact-fidelity query | Same AnySearch batch | Rudolph and Tindall, Sec. II, Eqs. (1)-(2), PDF p. 3 | closed | Report the product only as a diagnostic, never as the headline fidelity. |
| magnitude / pass threshold | A universal field threshold for “not too low” | RAG and current metric ledger | AnySearch exact-fidelity batch; Lee et al. 2025 and adjacent random-circuit work inspected as discovery | No universal QEC or PEPS threshold is used as a premise | closed by scope exclusion | `0.99/0.95` are explicit project decision bands, class (c), not physical or literature thresholds. |
| exact-complexity boundary | Why the experiment is finite and does not imply a scalable exact solver | RAG: `PEPS contraction #P complete`; KG: `general tensor-network contraction` | Reused Schuch/Haferkamp/Schwarz search | Schuch et al. note, “The classical complexity of PEPS,” VOR PDF pp. 2-3 | closed | The result is fixture-bound and cannot support unrestricted polynomial-scaling language. |
| implementation path | Maintained finite-PEPS code with the required pure-state gate surface | Local source audit and exact-commit landscape | AnySearch code queries listed in the landscape | `PEPS_PEPO_LITERATURE_LIBRARY_LANDSCAPE_2026-07-26.md`, library shortlist and source locators | closed for repository selection | Repository capability is engineering evidence, not scientific ground truth. |

## Anomaly ledger

| contrary fact / ambiguity | source and exact location | affected object | implication | status/action |
|---|---|---|---|---|
| The product of retained gate weights only approximates final-state fidelity on a loopy network. | Rudolph and Tindall, Sec. II, Eqs. (1)-(2), PDF p. 3 | candidate diagnostic | It cannot determine the verdict. | preserve; compare full vectors |
| State bond and boundary contraction bond are different approximations. | Lubasch et al., Sec. III.A and Fig. 2, PDF p. 3 | overlap evaluation | A finite environment bond can bias the reported value. | primary gate requires the complete complex128 candidate vector; otherwise `UNAVAILABLE` |
| Larger bond need not improve every approximate simple-update observable monotonically near difficult regimes. | Patra et al. note, Appendix A, PDF p. 6 | convergence prediction | Monotonic fidelity is a prediction, not an invariant. | a miss is a finding |
| Exact PEPS contraction is hard in general. | Schuch et al., VOR PDF pp. 2-3 | scalability inference | A successful d5 point says nothing universal about d7 or asymptotic cost. | hard claim boundary |
| The fixture uses d5 data-patch geometry but is not a stabilizer-measurement round. | Project object definition | QEC interpretation | No detector/observable Record, LER, measurement, reset, or leakage claim follows. | explicit exclusion |

## External acquisition ledger

Search backend: AnySearch `academic.search` plus general search, 2026-07-26
UTC. The complete earlier code-query ledger is retained in
`PEPS_PEPO_LITERATURE_LIBRARY_LANDSCAPE_2026-07-26.md`.

| gap row | exact query | candidate | disposition |
|---|---|---|---|
| 5-by-5 circuit fidelity precedent | `finite PEPS quantum circuit exact state fidelity benchmark normalized overlap 5x5 square lattice` | Lee et al., *Scalable projected entangled-pair state representation of random quantum circuit states*, PRR 7, 033252 (2025) | relevant discovery, but not load-bearing: this experiment directly computes the complete dense overlap and does not import the paper's random-circuit scaling law |
| global fidelity | `projected entangled pair state circuit simple update global fidelity exact statevector comparison` | Rudolph and Tindall plus adjacent circuit-TN work | Rudolph/Tindall is already full-text reviewed and admitted; no new premise required |
| failure/nonmonotonicity | `PEPS bond dimension convergence nonmonotonic fidelity square lattice quantum circuit limitation` | finite-PEPS contraction and complexity sources | current admitted Lubasch, Patra, Rudolph/Tindall, and Schuch rows already close the required limitations |
| independent exact overlap | `finite PEPS state fidelity normalized overlap independent exact contraction` | finite-PEPS contraction literature | the field-standard normalized overlap is already source-located in the admitted Evenbly note |

Search snippets and abstracts close no row. They were used only to test whether
the current admitted source set missed a load-bearing definition or no-go.

## Closure verdict

- `closure_status: closed`
- Closed rows: finite pure-state PEPS update; global normalized overlap;
  separate state/contraction controls; proxy limitation; exact-complexity
  boundary; repository-selection surface.
- Remaining gap: the full d5 measurement/reset `Record` bridge remains open
  and is outside this frozen object.
- Load-bearing notes:
  - `docs/papers/reading_notes/rudolph_tindall_gpu_peps_2507.11424.md`
  - `docs/papers/reading_notes/evenbly_closed_loop_truncation_1801.05390_source_review.md`
  - `docs/papers/reading_notes/lubasch_finite_peps_1405.3259_source_review.md`
  - `docs/papers/reading_notes/patra_gpeps_ibm_processors_2309.15642.md`
  - `docs/papers/reading_notes/schuch_peps_complexity_prl_98_140506_source_review.md`
- Supported implementation path: full-vector complex128 dense reference
  against pristine external finite-PEPS implementations, with exact fixture
  identity and corruption checks.
- Allowed downstream action: preregister and execute only the bounded d5
  pure-state fidelity benchmark.
