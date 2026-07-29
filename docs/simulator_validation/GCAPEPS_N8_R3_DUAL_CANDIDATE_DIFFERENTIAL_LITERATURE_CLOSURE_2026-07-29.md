# GCAPEPS n=8, r=3 equal-status candidate differential — literature closure

Date: 2026-07-29
Status: **closed for one bounded, untruncated two-candidate state-action differential with an
independent exact-small dense anchor and fixture-level efficiency observation;
not a Record or scaling closure**

## Frozen claim

`decision/consequence`

: Compare two equal-status candidate state-action implementations of the same frozen eight-qubit
  operation: ordinary Quimb PEPS with a physical Clifford prefix and a native
  rank-three direct-sum PEPO, versus GCAPEPS with the Clifford held in a Stim
  tableau and only the pulled-back rank-three residual lowered through the
  tree-routed PEPO carrier. Complete-vector agreement supports a bounded
  differential-equivalence statement. A third NumPy-only exact-small anchor is
  planned to qualify only the one frozen
  input-state action without entering the efficiency comparison.
  Timings and representation resources describe this fixture only.

`mechanisms`

: Both lanes start from the same logical preparation. The plain lane computes
  \(|y_{\rm plain}\rangle=U_{\rm phys}C|\phi\rangle\) by physically applying
  \(C\) to the PEPS, building one native Quimb direct-sum PEPO for
  \(U_{\rm phys}\), and applying it without compression. The GCAPEPS lane keeps
  \(|\psi\rangle=C|\phi\rangle\), pulls back
  \(U_{\rm phys}=CU_{\rm res}C^\dagger\), and tree-routes

  \[
  U_{\rm res}=-i(0.8P_0+0.48P_1+0.36P_2)
  \]

  into the residual PEPS. Its physical audit vector is reconstructed by the
  frozen literal complex128 graph-local gate-list lift, not by Stim's
  phase-ambiguous complex64 tableau matrix.

`observable objects`

: The primary differential object is the pair of complete length-256
  complex128 output vectors in one frozen big-endian coordinate. Normalized
  squared whole-state fidelity is accompanied by phase-sensitive maximum and
  L2 differences plus relative norm error. Neither candidate is labelled
  oracle, Quimb truth, or ground truth. A
  separate planned NumPy-only anchor will construct the closed-form input,
  apply residual Pauli words by bit action, and independently replay the
  physical preparation/gate stream and signed physical words.

: Efficiency observations separately report Clifford handling, rank-three
  operator construction/application, complete-vector contraction, and total
  lane wall time; fresh-process peak RSS; every-edge and maximum state bond;
  state/operator tensor elements and logical bytes. Import/setup time and
  complete-vector contraction never masquerade as carrier-update time.

`mechanism-to-observable bridge`

: The neutral fixture, logical qubit-to-coordinate map, preparation gates,
  graph-local Clifford stream, signed physical Pauli terms, dtype,
  no-truncation settings, and contraction optimizer are identical across lane
  payloads. The canonical phase-dagger token/Stim instruction is exactly
  `S_DAG`; plain Quimb lowers it only as raw dense complex128
  `diag(1,-i)` through `Gate.from_raw`. All plain preparation/prefix Cliffords
  are raw `Gate.from_raw` objects. Both candidates and the anchor bind the
  frozen matrix SHA-256, unitarity, chronological target-order, preparation
  stream, and ten-gate stream ledgers. GCAPEPS calls `apply_clifford` once per
  gate and must finish with frame revision ten and ten Clifford events. Plain
  terms are combined only by the `add_PEPO` instance chain.

: Plain Quimb acts directly on its pure-state PEPS and is not the registered
  ECS density-matrix `carrier/pepo` service. GCAPEPS pulls the same terms back
  and exports residual plus literal-gate-list-lifted physical vectors. The
  planned anchor will import no Quimb, Stim, SDIM, or GCAPEPS code, will
  never be timed, and may qualify only this one n=8 input-state action after
  implementation and controls pass. Pair comparison remains symmetric; anchor
  comparisons localize a qualified miss.

`predictions`

: Complete vectors are predicted to agree at frozen complex128 bands. The
  native plain direct-sum PEPO is predicted to have operator bond three on
  every lattice edge, 576 operator elements, and a largest local operator
  tensor of 108 elements. The GCAPEPS tree PEPO is predicted to route only five
  edges, with 176 elements and largest local tensor 36. The directional runtime
  hypothesis is lower median current-implementation update time for GCAPEPS on
  this fixture; a miss is reported rather than repaired and no generic speedup
  follows.

`possible no-go`

: General PEPS contraction remains hard in the Schuch et al. setting. This
  independent anchor is feasible only because the n=8 Hilbert space has
  256 amplitudes. There is no scalable ground truth, scaling series, hardware
  model, or general a posteriori contraction certificate. The fixture cannot
  establish generic correctness, asymptotic complexity, or universal speedup.

## Coverage ledger

| load-bearing row | evidence/source | exact locator | status | implication |
|---|---|---|---|---|
| Clifford/residual hybrid | Harper et al. reading note | `docs/papers/reading_notes/harper_gcamps_2511.06672v2.md`, Sec. 3/Fig. 3, PDF p. 5 | closed | Supports the \(C|\mathrm{TN}\rangle\) skeleton and signed Pauli pull-through; the paper uses MPS, not PEPS. |
| exact tree PEPO | project theorem SHA-256 `7f5ec9c7c3dac2da7c377c0958f7eafc104d2da19b59350e1a7c336cc1cc10dc` and implementation-correspondence SHA-256 `b33c2fff6fcf7f6e7c934dceeeb47a7680a60be0d928670c5043b8a414f6642d` | `docs/simulator_validation/GCAPEPS_MATHEMATICAL_FEASIBILITY_THEOREM_2026-07-27.md`, Lemma 3/Eqs. (9),(11),(13),(16),(17); `docs/simulator_validation/GCAPEPS_IMPLEMENTATION_THEOREM_CORRESPONDENCE_2026-07-28.md`, §§2–7 | theorem construction closed; implementation correspondence remains `SCOPED_ENGINEERING_GREEN__GENERIC_EQUIVALENCE_OPEN` | Supports the frozen exact untruncated routed construction/resource ledger only; generic Eq. (9)/(11) implementation equivalence and contraction efficiency remain open. |
| ordinary Quimb candidate | current fork public Quimb API | native `PEPO_product_operator`, instance `term0.add_PEPO(term1).add_PEPO(term2)` chain, and PEPO-on-PEPS apply | closed for bounded design | Provides a pure-state operator-PEPO state-action baseline; it is neither an oracle nor the registered ECS density-matrix `carrier/pepo` service. |
| complete-state differential | Evenbly overlap definition plus project phase/norm companions | `docs/papers/reading_notes/evenbly_closed_loop_truncation_1801.05390_source_review.md`, Sec. V Eq. (12), PDF p. 6 | closed | Complete vectors support a symmetric equality diagnostic at n=8. |
| independent exact-small anchor | current faithfulness protocol plus finite-dimensional literal construction | closed-form four-amplitude input; literal bitwise residual/physical Pauli action; independent complex128 gate replay | closed for n=8 design | May qualify one input-state action only after implementation and controls; never enters timing ratios. |
| timing/resource observation | project benchmark protocol | this packet and preregistration | closed by bounded design | Wall times, RSS, bonds, and element counts are fixture observations, not literature facts. |
| contraction/scaling boundary | Schuch et al. VOR reading note | `docs/papers/reading_notes/schuch_peps_complexity_prl_98_140506_source_review.md`, PDF pp. 2–3 | closed | Forbids extrapolating this exact-small comparison to generic efficient contraction. |

## Role and qualification boundary

The two state-action lanes remain equal-status performance candidates. A third,
untimed NumPy-only anchor is specified independently and may qualify only this
one exact-small state action after implementation and controls pass. Therefore:

- `differential_agreement` compares plain Quimb with GCAPEPS symmetrically;
- `anchor_verdict` grades each lane against the independently built vector;
- `state_action_qualification_status` may become
  `BOUNDED_EXACT_SMALL_STATE_ACTION_ANCHORED` only when differential
  `AGREE`, all anchor qualification rows `PASS`, and the SDIM-frame verdict is
  `PASS`;
- neither lane is Quimb truth, an oracle, or a scalable/generic PEPS ground truth;
- a pair mismatch plus one anchor pass can localize the failing lane;
- a common anchor failure or qualification failure prevents attribution.

This anchor is possible because n=8 has only 256 amplitudes. It does not solve
or evade the generic PEPS contraction problem.

## Anomaly and exclusion ledger

| issue | consequence |
|---|---|
| GCAMPS derives an MPS residual, not this PEPS carrier | PEPS routing remains a project construction. |
| Current GCAPEPS n<=10 apply includes an internal same-IR dense audit and norm contraction | GCAPEPS update timing is current-implementation end-to-end time including exact-small checks, not pure carrier-kernel time. Generic implementation equivalence nevertheless remains open in the correspondence packet. |
| Stim tableau unitary is only defined up to global phase and is complex64 | It is excluded from physical-vector grading; the frozen literal complex128 gate-list lift fixes the comparison phase convention. |
| Fidelity ignores nonzero scaling | Direct vector and norm companions remain mandatory. |
| Wall time is system-sensitive | Fresh-process AB/BA ordering and all raw samples are required; no universal performance conclusion is allowed. |
| Structural bond savings do not imply contraction speedup | Bond/element and timing outcomes are reported separately. |
| SDIM carries no PEPS and shares a Stim translation surface | SDIM is signed-frame corroboration only, never a third carrier or qutrit result. |
| No measurement/reset/Record law is in scope | No multi-round, detector, observable, leakage, or branch-probability claim is allowed. |

## Frozen implementation and environment boundary

The existing development fork is not cleaned or used for execution. The frozen
commit is materialized into a fresh temporary execution checkout; only that
checkout must have empty exact
`git status --porcelain=v1 --untracked-files=all --ignored` output after
materialization, before controls, before target workers, and after execution.
Pixi uses detached environments and keeps environment/cache/log/bytecode/
coverage paths outside the temporary checkout; locked/frozen execution may not
rewrite `pixi.lock`. The `detached-environments` configuration value is an absolute
private path, not a boolean. These are provenance gates, not scientific
evidence.

## Local search record

The artifact-verified local literature corpus was audited and the admitted
Harper, Evenbly, and Schuch source reviews were read at their exact locators.
No external acquisition was needed because the other load-bearing objects are
explicit project mechanisms and a bounded benchmark protocol, not missing
literature premises. No field-wide literature-gap claim is made.

## Closure verdict

- `closure_status: closed_for_bounded_anchored_candidate_state_action_differential_design`
- Supported downstream object: one n=8, active-rank-3, untruncated equal-status plain-Quimb
  versus GCAPEPS candidate state-action differential, one untimed NumPy exact-small anchor, and
  fixture-level timing/resource observations.
- Epistemic status: anchorable only as one-input exact-small state action; no
  generic implementation-equivalence, Carrier, contraction, or Record promotion.
- Runtime advantage is a preregistered fixture hypothesis, not a closed
  literature conclusion.
- Record, leakage/qutrit, finite-bond truncation, non-Markovian/cross-round,
  generic contraction, scaling, and general efficiency certification remain
  open.
- `CODE_PERMITTED` is effective only after this renamed differential closure, its preregistration,
  `CONTEXT.md`, `docs/service_status.json`, `docs/METRICS.md`, and
  `docs/NUMERICAL_PROVENANCE.md` are committed together before experiment code
  or target output.
