# Claim audit — Fang, Lou, and Li, SymFT structural-cost evidence

## Status and decision

This packet audits arXiv:2607.28600v1 for the narrow question needed by the
no-cutoff structure census: what SymFT represents exactly, which
implementation-qualified quantities control its residual cost, and what the
source does and does not establish about scaling. It is not an audit of
sampling throughput and it grants no permission to implement a new simulator.

The source closes the representation and local-cost rows. It factorizes each
measurement branch into unitary Clifford/Pauli frames and an ordered residual
sequence of Pauli rotations and projectors. In its semantic monolithic
representation, a shared stabilizer coordinate system writes the active
coefficient tensor as a vector in `C^(2^k)`, and the paper gives a general
state-vector cost exponential in the peak planned active width `k_max^S`.
This is not a complete cost model for every current backend: Sec. 6 already
implements an exact CPU product-component lowering that can retain several
small dense vectors without materializing their full tensor product.

The coherent surface-code benchmark reports `k_max^S = 4, 7, 12, 22` for
`(d,r) = (3,1), (3,3), (5,1), (5,5)`. Those are
implementation-qualified observations, not an architecture-independent law.
Section 8 keeps SymFT's `k_max^S` distinct from Clifft's `k_max^C`. It gives
processing the same residual sequence while maintaining maximum-rank dormant
stabilizer subgroups after every prefix as a sufficient condition for the two
widths to coincide. It does not state that the condition is necessary.
Reordering, fusion, and coordinate choices can change the trajectories, and
the paper proves no family-level bound in code distance or rounds.

The source does not close the requested product claim. It gives an exact
sampler for its declared noisy adaptive Clifford-dominated circuit model, but
does not define a persistent cross-round coherent latent process, an exact
full detector/observable Record-law oracle, Pauli-pair reachability, a decision
diagram, or a retained-Record tensor graph. It therefore supports
route-qualified census meters, not scalability to a complete non-Markovian
Record.

The fixed artifact is `docs/papers/2607.28600v1.pdf`, SHA-256
`37c2e5b4276d4c348ee951b0c3fb8b72b5f1ac9893b707fecd3cad10ebc5af29`.
The full 28-page artifact was read; the 24-page paper body was visually checked
page by page. Independent round-two source-only review passed under reviewer ID
`independent_symft_2607_source_rereview_round2_2026_08_03`.

## Assigned closure rows

| row | exact source location | source says | source does not say | status |
|---|---|---|---|---|
| Branch object | Sec. 1.1, PDF p. 2; Sec. 3, Eqs. (2)–(4), PDF pp. 5–6 | `K(s,m)` is factorized up to global phase as `C E(s,m) O(s,m)`; the unitary frames do not affect `Pr(m|s) = ||O(s,m)|0^n>||^2`. | This conditional branch probability is not an independently certified complete folded Record law. | closed |
| Supported non-Clifford primitive | Sec. 2, PDF p. 4 | Pauli rotations are exact operations `R_P(theta)=cos(theta/2)I-i sin(theta/2)P`; Pauli measurements use `(I +/- P)/2`. | The source does not introduce a perturbative order or coefficient cutoff for these operations. | closed |
| Active-coordinate object | Sec. 1.1 and Sec. 4, PDF pp. 3 and 7 | Stabilizer coordinates define an active coefficient tensor semantically written as one vector in `C^(2^k)`. | This semantic form does not imply that every current backend materializes the monolithic tensor product, and the source gives no family-level bound on `k`. | closed |
| Active-width mechanics | Sec. 4.1, PDF pp. 7–9; Sec. 4.2, PDF pp. 9–13 | A rotation with dormant-nondiagonal coordinate `d != 0` promotes one coordinate; an active measurement with `d = 0` and `(a,b) != (0,0)` returns one coordinate to the dormant block. | The source gives no theorem that measurements keep peak width bounded with increasing rounds. | closed |
| General state-vector cost | Sec. 5, "Sampling complexity", PDF p. 15 | The paper gives `O((n_t+n^S_m,active) 2^(k^S_max))` state-vector work plus symbolic and noise terms. | This general/monolithic bound is not a full prediction of realized work or memory for the product-component backend. | closed |
| Current product-component backend | Sec. 6, "Adaptive product-component representation", PDF p. 16 | The CPU lowering exactly retains independent components, updates them separately, and merges only coupled components by exact Kronecker product. | The current lowering does not split a component again after merging and supplies no family-level component-size theorem. | closed |
| Coherent surface-code observations | Sec. 7.1, Tables 3–4, PDF pp. 19–20 | The coherent family has `k^S_max = 4, 7, 12, 22` for the four reported `(d,r)` cells; the `d=5,r=5` FP64 GPU row exceeds the stated shared-memory limit. | Four table entries do not establish an asymptotic growth law, and the PDF does not pin enough build inputs to reproduce the planner values. | closed as observations; replay missing |
| Full-distribution validation limit | Sec. 7.1, MSC distance-seven paragraph, PDF p. 19 | The authors had not generated enough shots to validate the full output distribution or rare logical-error behavior and make no correctness claim for that workload. | Attempted-shot throughput is not itself full-law validation. | closed |
| Clifft comparison | Sec. 8, "Closest universal QEC simulators", PDF pp. 21–22 | The source states a sufficient condition under which `k^S_max` and `k^C_max` coincide; it retains separate superscripts because reordering, fusion, and coordinate updates can change trajectories. | The stated condition is not claimed necessary, and neither width is an architecture-independent circuit invariant. | closed |
| SOFT comparison | Sec. 8, SOFT bullet, PDF p. 22 | SOFT uses a sparse generalized-stabilizer coefficient map with peak support `r_max`; worst-case `r_max <= 2^(k^S_max)`, but it can be much smaller. | The source does not identify `r_max` with a Pauli-pair reachable-state count or decision-diagram node count. | closed |
| Multi-object optimization | Sec. 9, PDF p. 24 | Future optimization should jointly consider `k^S_max`, symbolic-evaluation cost, and total dense-vector work; future structure work includes re-splitting and richer/adaptive representations. | Exact product components themselves are not future work: they are already implemented in the CPU backend. | closed |
| Persistent coherent Record scaling | Full-text body PDF pp. 1–24, especially Secs. 2–3, 5, and 7–9 | The model supports exact Pauli rotations, per-location stochastic Pauli choices, Pauli measurements, and parity-controlled feedback. | No single persistent coherent latent variable, complete non-Markovian Record scaling theorem, or independent full-law certification over increasing `d,r` is defined. | missing source-locally |
| Pair, DD, and treewidth meters | Full-text body PDF pp. 1–24, especially Secs. 8–9 | The source compares several representations and discusses possible tensor-network structure. | It supplies no exact `N_pair`, complete-Record `N_DD`, or retained-Record graph/treewidth value for the census. | missing source-locally |

## Operation replay

| input | transformation | assumption | output | exact source location | replay status |
|---|---|---|---|---|---|
| Circuit prefix with Clifford gates, Pauli noise/feedback, Pauli rotations, and Pauli measurements | Accumulate `C_t` and `E_t`; pull rotations and projectors back in execution order using the displayed per-operation rules | Clifford conjugation maps Paulis to Paulis; Pauli conjugation changes only a sign | `K_t` factorized as `C_t E_t(s,m) O_t(s,m)` up to global phase, with branch probability from `O_t` | Sec. 3, Eqs. (1)–(4), PDF pp. 5–6 | complete |
| Pulled-back residual Pauli | Decompose it as active/dormant coordinates `(a,b,d,c)` | Tableau generators remain a canonical stabilizer–destabilizer system | Dormant, active-diagonal, or active-pair instruction class | Sec. 4, Eq. (8) and Eqs. (9)–(13), PDF pp. 7–13 | complete at source-algorithm level |
| Dormant-nondiagonal rotation | Require `d != 0`, choose a dormant pivot, update coordinates, and promote it | The Pauli anticommutes with at least one dormant stabilizer | Width increases by one and `PromoteRot` is emitted | Sec. 4.1, PDF pp. 8–9 | complete |
| Active measurement | Require `d = 0` and `(a,b) != (0,0)`; project the appropriate active amplitudes and return a pivot to the dormant block | Active-diagonal and active-nondiagonal cases obey their separate probability formulas | Branch probability and a compacted vector of dimension `2^(k-1)` | Sec. 4.2, Eqs. (12)–(13), PDF pp. 11–13 | complete |
| Factorized residual sequence | Fuse compatible rotations and move measurements only under the guarded commutation rules | Detector boundaries, record order, and assignment-before-use dependencies are preserved | A possibly different, shorter-lived active trajectory before planning | Sec. 6, "Commutation-aware simplification before planning", PDF pp. 15–16 | complete |
| Planned monolithic active tensor | Identify exact product components and lower instructions to component-local updates and exact affected-component merges | The deterministic lowering and conservative cost model select the component representation | One small vector per current exact component without materializing the full tensor product | Sec. 6, "Adaptive product-component representation", PDF p. 16 | complete |
| Planned instruction stream | Reuse the plan for each shot and evaluate symbolic signs while executing active updates | `k^S_max` belongs to that particular planned trajectory | General monolithic state-vector work exponential in `k^S_max`, with separate symbolic/noise terms | Sec. 5, PDF p. 15 | complete as the stated upper-bound replay |
| Four coherent surface-code benchmark rows | Reconstruct the exact circuits and rerun the reported planner to recover `4,7,12,22` | Requires the authors' exact circuit artifacts, compiler commit, options, and rewrite configuration | Reproducible planner traces and values | Sec. 7.1, Tables 3–4, PDF pp. 19–20; repository footnote 3, PDF p. 18 | missing: PDF gives table values and an unpinned repository URL, not the required build identity |

`operation_replay_status = complete` for this packet means every load-bearing
source operation has a replay row and the irreproducible benchmark operation is
explicitly recorded as `missing`; it does not mean the missing external build
identity was reconstructed.

## Project application

The following rules are project inferences, not claims in the PDF.

1. Report SymFT's meter as `k_max_symft(plan_hash, compiler_commit, options)`,
   never as a bare circuit invariant. Bind both persistent-sign circuit hashes,
   the external commit, rewrite counters, planned-instruction trace, and output
   hash.
2. Report `2^k_max_symft` only as the general monolithic active-coordinate
   burden. Also report product-component capacities/merge trajectory when the
   selected CPU backend uses that current exact representation. A red
   monolithic burden cannot by itself kill the entire SymFT architecture.
3. A planner count has no coefficient cutoff, but it also does not validate the
   complete detector/observable Record law. No nonzero algebraic Record mass may
   be dropped by the census adapter.
4. Because the published benchmark cannot be replayed from its PDF identity,
   any local calibration is circuit- and commit-specific rather than an
   admission of the four table values for a modified persistent-mixture fixture.
5. Until all requested meters and an independent complete-law oracle exist,
   SymFT remains `CODE_BLOCKED` for the proposed full-Record route even if its
   compile-only structure meter is available.

## Competing evidence and kill conditions

- Clifft supplies a distinct planner-qualified active width. The two width
  trajectories may agree under the paper's sufficient condition, but either
  can differ after route-specific rewrites. Kill any adapter that silently
  equates the two names or substitutes one result for the other.
- SOFT's `r_max` is sparse coefficient support and can be much smaller than
  `2^k`; it is neither the requested Pauli-pair count nor a proof that sparse
  support remains controlled. Kill any census row that aliases these metrics.
- The current product-component backend is a direct counterexample to treating
  `2^k_max_symft` as universal realized CPU storage. Kill a whole-architecture
  disposition based solely on that monolithic counterfactual burden.
- Kill benchmark replay if the circuit hash, external commit, options, or
  rewrite trace is absent or differs. Reading `4,7,12,22` from the table is an
  observation check, not a replay.
- Kill any correctness or scalability claim derived from attempted-shot
  throughput alone; the source itself withholds a correctness claim for the
  unvalidated MSC distance-seven distribution.
- Kill a positive complete-Record claim if target-grid total variation remains
  unavailable, sampled only, marginal only, or shares the candidate's lowering
  path.

## Source-local verdict

- `read_status`: complete
- `evidence_status`: persisted and independently source-only reviewed
- branch factorization, operation rules, general active-width bound, current
  product components, and reported benchmark observations: `closed`
- exact reproduction of the four benchmark planner values from the fixed PDF:
  `missing`
- persistent coherent latent process and complete non-Markovian Record scaling
  certificate: `missing source-locally`
- Pauli-pair, complete-Record decision-diagram, and retained-Record treewidth
  meters: `missing source-locally`
- downstream permission: source-note re-review and preregistration design only;
  no solver implementation or scalability claim
