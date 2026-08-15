# GCAPEPS finite-memory fixture v2 (X8 family) — Pre-Registration (theory-first, LITERATURE-GROUNDED)

Status: PRE-REGISTRATION, 2026-08-01. Predictions written BEFORE any confirmatory run;
a miss is a finding, not a re-fit.

Parent artifacts. v1 closure and preregistration:
`GCAPEPS_FINITE_MEMORY_BOND32_LITERATURE_CLOSURE_2026-07-29.md`,
`GCAPEPS_FINITE_MEMORY_BOND32_PREREG_2026-07-29.md` (both untouched; v2 amends
neither and never touches v1's HELDOUT partition). v2 delta-closure (closed):
`.scratch/gcapeps-fixture-v2/theory/CLOSURE_PACKET.md`. Design screening
(nonclaim-bearing, adversarially verified): `.scratch/gcapeps-fixture-v2/screening/`.

## -1. Question charter (importance × attackability)

- **Decision + consequence:** whether fixture v2 — the v1 persistent-memory unitary
  dilation plus an intermittent deterministic cross-row CX layer and reduced collision
  density — carries a positive, visible, measurable fixed-pair BLP witness. If yes, v2
  becomes the science fixture of the GCAPEPS finite-memory line; the v1 fixture is
  provably unable to carry that claim (witness invisible at checkpoints; `g_C = 0`
  product-frame theorem; 2×w = MPS; error budget 20×–1000× short).
- **Plausible attack + independent anchor:** exact dense oracle at n=14 (0.4 s/run);
  GF(2) tableau instruments; an exactly computable Clifford-only anchor arm; a 2×2
  lever-isolation control suite already verifier-confirmed at the screening stage.
- **Alternative formulations + invariants:** X5 family (per-round CX + thinning) as
  registered alternative; temporal process-tensor formulation of the same memory;
  invariant: the fixed-pair witness is a lower bound on the sup-over-pairs BLP measure
  (v1-closed) and any positive dense increment above the numerical guard witnesses
  non-Markovianity of the registered trajectory.
- **Kill condition:** a published theorem forcing monotone coupling-dependence of
  backflow (searched 2026-08-01; none found — counterexamples exist: McCloskey
  δ-thresholds, Pleasance order dependence); or failure of the interaction-effect
  replication on confirmatory cells (that is a finding that kills the X8 design, not
  a licence to re-fit).
- Selection warning acknowledged: the screening magnitudes are development data, not
  evidence of importance.

## 0. Grounding ledger

| sub-axis / mechanism | mechanism source | observable source | reading note | in-repo reuse |
|---|---|---|---|---|
| collision primitive, event law | McCloskey–Paternostro 1402.4639v3 Eqs. (1)–(4), Sec. II.B | — | `mccloskey_paternostro_collision_1402.4639v3_source_review.md` | v1 emitter `_collision_operation` |
| fixed-pair BLP witness | — | BLP 0908.0238v2 Eqs. (1), (10)–(12) | `breuer_laine_piilo_nonmarkovianity_0908.0238v2_source_review.md` | v1 dense reference + comparator |
| order/schedule dependence; CCM embedding; commuting-W no-go; backflow-correlation bound | Pleasance et al. NJP 27 114514 (2025) Thm 1, Eqs. (8), (33), (35)–(42) | same | `pleasance_collision_order_njp_27_114514_source_review.md` | — (adjacent grounding only) |
| θ=0 stabilizer anchor | Aaronson–Gottesman quant-ph/0406196v5 Sec. III | inner product, end of Sec. III | `aaronson_gottesman_stabilizer_circuits_0406196v5_source_review.md` | Stim tableau (ecs) |
| pure-state trace distance | complete project derivation | — | `.scratch/gcapeps-fixture-v2/theory/v23_pure_state_trace_distance_control.py` (204 checks PASS incl. corruption gate) | — |
| rotation-density regime | Masot-Llima et al. 2602.15942 T/N regimes | — | existing admitted note | magic accounting instruments |
| candidate family behavior | project screening (dense, n=14) | same | `.scratch/gcapeps-fixture-v2/screening/SCREENING.md` + JSON, adversarially verified | `screening/common.py` machinery (nonclaim) |

## 1. The mechanism

v2 = v1 fixture (2×7 ladder, per-round intra-row Clifford layers, event-conditioned
cross-rung partial-SWAP-decomposed rotations, persistent memory row) **plus**:

- **X8 delta:** one cross-row `CX(system 3 → memory 10)` on even rounds, inserted
  **after the memory-CX layers and before the collision layer**. The insertion
  position is load-bearing (verifier: end-of-round insertion shifts trajectories by
  1.1e-2, start-of-round by 4.8e-2) and is a frozen emitter-contract field.
- **Rotation thinning:** keep collision events with even global event index
  (87/171 at the screening cell), halving non-Clifford density; the thinning rule is
  a frozen schedule transformation, not a new stochastic law.
- **Registered variant axis (design freedom, frozen before implementation):**
  odd-round CX placement (covers round 1, `g_C > 0` from the first coupled round);
  X5 (every-round CX + thinning) as the high-magnitude/lower-robustness alternative.
- Everything else — event masks, γ grid, axis families, inputs, coordinate
  convention, complex128 rule — inherits v1's frozen definitions verbatim.

Design no-go (class (a), Pleasance Eq. (8)): the cross-row Clifford layer must not
commute with the collision rotations; the X8 CX does not commute with the XX/YY/ZZ
rung rotations, and the corruption falsifier below enforces the no-go's teeth.

## 2. Metric binding (forced standard-metric ladder)

- **Existing ledgered metric:** the v1-registered fixed-pair BLP objects — dense
  trace distance `D_r = ½||ρ_{S,1}(r) − ρ_{S,2}(r)||₁` and positive-increment sum
  `N_pair^(R) = Σ_r max(0, D_r − D_{r−1})`, numerical guard `1e-10`, verdict
  vocabulary `NO_WITNESS_FIXED_MASK_FOR_REGISTERED_PAIR` (v1 prereg §5, METRICS.md
  BLP entries). No new metric is introduced.
- **New registered guard (anti-manufacture):** the headline verdict uses a
  **two-sided margin**, not the bare sign test: a cell reports WITNESS only if its
  maximum increment exceeds `10 × err_cell`, where `err_cell` is the plain-lane
  trace-distance error measured on that cell against the dense oracle at the same
  cap. Increments in `(guard, 10 × err_cell]` report `WITNESS_BELOW_MARGIN`.
- **Forbidden proxies:** entanglement or bond growth (v1); state fidelity or parity
  alone (degenerate-policy hazard — pullback weight is reported beside every
  fidelity number, spec §0b.6); any averaging of pathwise witnesses (v1 forbids);
  the bare sign test.

## 2a. Predicted observables (class (b) bands, frozen before any confirmatory run)

Confirmatory cells: fresh seeds drawn from a **new v2 heldout-seed derivation**
(same construction as v1's `HELDOUT_SEED`, new namespace string), on the v2 grid;
the six screened cells (γ-index 1–3, seeds 0–3, w7 r10) are permanently
development-only. Checkpoints: **every round**.

- **P1 (witness existence):** X8 shows a positive dense witness above the numerical
  guard in at least 4 of any 6 confirmatory cells, with magnitude in
  `[1e-3, 1e-1]` and location within rounds 1–5. (Screening spread: 3.1e-3–6.6e-2,
  locations r1→r2 … r3→r4, 6/6 positive; the band widens both ends for seed
  novelty.)
- **P2 (interaction effect):** on the same cells, the CX-only arm (X1-analog,
  full rotations) shows **no** positive witness above guard in the majority of
  cells; the thin-only arm (X7-analog, `g_C = 0`) shows a positive witness in a
  **minority** of cells; both-levers (X8) in the majority. The distinguisher
  against the strongest competitor (rotation-density-only explanation): if the
  thin-only arm matches X8's witness rate, the CX lever is not established — that
  outcome kills the X8 mechanism reading and is reported as such.
- **P3 (θ=0 anchor):** the X8 θ=0 arm is flat (every increment below `1e-12`); the
  X5-variant θ=0 arm, if run, shows the Clifford recurrence (D reaching exactly 0
  and reviving to 1.0 at fixed rounds). Class (a) once computed — exactly checkable.
- **P4 (frame relevance):** `g_C(sys|mem) = 1` on every CX-coupled round and 0
  before the first coupling (GF(2), exact).
- Statistic the literature proves insufficient: a zero witness is never evidence of
  Markovianity (BLP fixed-pair limitation, v1-closed).

## 2b. Disconfirmation surface

Strongest contrary facts held: X5 fails outright at screening seed 3; X7 produces a
large witness (+5.3e-2) at seed 0 with `g_C = 0`; witness magnitude varies ~20×
across cells. Prospective searches run and logged (closure packet): no
monotone-coupling theorem; published counterexamples of threshold/order dependence.
The observation separating the preferred reading (joint CX+density mechanism) from
the strongest competitor (density-only) is P2's arm comparison on fresh cells.

## 3. Independent ground truth

- Dense oracle: numpy+stdlib exact evolution (v1 leg with verified import firewall);
  every headline number is dense-computed; carriers are never their own oracle.
- θ=0 arm: Stim tableau + A-G inner-product magnitude + the controlled pure-state
  trace-distance identity — a second route with a different blind spot from the
  dense arm; the two must agree at `1e-12` on the θ=0 trajectories.
- GF(2) instruments (pullback weight, `g_C`): validated exactly against
  state-vector arms in the sealed review (five-point sweep, exact agreement).

## 3a. Constraint ledger + corruption falsifiers

| constraint | exact assertion | falsifying test | deliberately broken input | evidence test trips |
|---|---|---|---|---|
| commuting-W no-go (Pleasance Eq. (8)) | a commuting cross-row Clifford leaves the reduced dynamics identical to P0 | axis-family-1 (Z-only rotations) cell with CZ-type cross-row layer: D(r) must equal P0's bitwise | the X8 CX in the same cell must produce a differing trajectory | to demonstrate pre-run |
| pure-state trace-distance identity | dense `½||Δ||₁` equals `sqrt(1−|⟨ψ1|ψ2⟩|²)` at 1e-13 | `v23_pure_state_trace_distance_control.py` | corrupted formula `sqrt(1−F)` | **already trips** (204 checks, corruption separates) |
| θ=0 stabilizer exactness | Stim-route D(r) equals dense D(r) at 1e-12, all rounds | anchor comparison harness | sign-corrupted tableau update; A-G printed example `1/√2` must reproduce | to demonstrate pre-run |
| insertion-position pinning | candidate layer sits after memory-CX, before collisions | emitter-contract validator | end-of-round insertion (shifts trajectory ≥1e-2, verifier-measured) | to demonstrate pre-run |
| lever-isolation structural integrity | every original Clifford preserved in order; kept rotations an in-order subset with angles untouched; insertions exactly the declared CX set | ledger diff against P0 (verifier's construction check) | one dropped Clifford; one altered angle hex | to demonstrate pre-run |
| exactness controls (v1) | untruncated run F=1 to machine precision; LOCAL-alphabet control F=1 exactly; θ=0-plus-no-CX arm has constant D | v1 control suite | v1's registered corruptions | inherited, must re-trip on v2 |
| determinism precondition (R0) | thread-invariance regression passes at a tolerance ≥10× below the smallest discriminating difference | spec Stage-0 runner at 1/2/4/8 threads | — | **currently FAIL at HEAD — blocks every claim-bearing v2 run until passed or tolerance-justified in writing** |

## 3b. Negative controls + non-degeneracy

- Inert control expected to FAIL: the shipped checkpoint set `{0,1,2,4,10}` applied
  to P0 must report NO WITNESS while the all-rounds set reports +7.227e-4 at r8→r9
  — demonstrating the checkpoint repair is load-bearing.
- Object movement: X8 vs P0 dense trajectories differ by more than 10× the guard on
  coupled rounds; the 2×2 arms are pairwise distinguishable.
- Degeneracy detector: pullback weight reported beside every fidelity/witness
  number; weight ≈ 2.00 flags an inert frame.

## 4. Bounded simplifications (unbounded ⇒ STOP)

- Screening→confirmation split: all six screened cells are development-only; the
  P1/P2 bands are bets on fresh cells. Bound: the band itself.
- n=14, cap 32 (16× over-provisioned): every v2 witness number is in the exact
  regime — v2 makes **no truncation or carrier claim**; carrier comparisons remain
  v1-prereg territory. Bound: exactness (class (a) dense).
- One trajectory per fixed mask (v1 pattern); the 32-mask ensemble object inherits
  v1's mixture-map definition unchanged.
- Thinning halves realized non-Clifford count; T/N regime per cell is reported
  (class (a) arithmetic), not assumed.

## 5. Epistemic status

- (a) exact: dense oracle values; θ=0 anchor equalities; `g_C` and pullback-weight
  GF(2) values; the trace-distance identity; the commuting-W no-go.
- (b) bands: P1, P2 as stated. A miss is a finding, never later citable as fact.
- (c) gates: the 10×-margin verdict rule; the R0 determinism gate; control
  pass/fail assertions.
- The headline verdict stays PROVISIONAL until the independent rereview of this
  preregistration passes (v1 pattern) and the R0 gate is green.

## 6. Build org

- Emitter v2 and engine checkpoint changes are separate diffs, owner-confirmed
  before landing (repo rule); the fixture emitter seams are
  `emit_gcapeps_finite_memory_fixture.py:_round_ledger` (new layer),
  `_state_contract` (`unconditional_cross_row_gate`), and the grid gate — v2 uses a
  new schema version, not an in-place mutation of v1.
- The screening machinery is not the production implementation; production workers
  reuse the v1 fresh-process topology.
- An un-led independent rereview of this preregistration (v1 pattern:
  `..._PREREG_INDEPENDENT_REREVIEW_...`) must precede the first confirmatory run.

## Gate

premises closed? **yes** (delta-closure closed 2026-08-01; v1 closure inherited) |
standard metric bound? **yes** (v1-ledgered BLP objects + registered margin rule) |
predictions frozen? **yes** (P1–P4) | independent GT? **yes** (dense; Stim/A-G
anchor; GF(2)) | constraint falsifiers registered? **yes** (7 rows; 1 already
tripped, 4 to demonstrate pre-run, 1 inherited, 1 currently failing and blocking) |
simplifications bounded? **yes** | controls registered? **yes** |
**preregistration gate: pass** — with two execution blockers on record: (i) R0
thread-invariance FAIL at HEAD blocks every claim-bearing run; (ii) the four
to-demonstrate corruption trips must be shown before the first confirmatory run.

## Pre-run amendment 1 (2026-08-01): rereview-condition discharges and frozen adjudications

Appended after the independent pre-run rereview
(PASS-CONDITIONAL, 8 conditions; `.scratch/gcapeps-fixture-v2/rereview/
INDEPENDENT_REREVIEW.md`) and the §3a corruption-trip discharge
(4/4 demonstrated; `.scratch/gcapeps-fixture-v2/corruption_trips/
TRIPS_DISCHARGE.md`, run log exit 0). Nothing above this line changes; no frozen
band or prediction is altered. Load-bearing numbers are restated here because the
discharge artifacts live on gitignored paths.

1. **Confirmatory cell frame (C1).** The confirmatory cells are exactly: the single
   v2-heldout seed the landed emitter admits (emitter heldout-namespace guard,
   lines 443–447) × inputs {1, 2} × the X8 arm, plus the mandatory X5-variant θ=0
   arm of item 3. The frozen text's "fresh seeds" (plural) is recorded as a text
   defect: the heldout namespace contains one seed by design. No other cell may run
   under this preregistration.
2. **P2 majority semantics (C2).** "Majority" means ≥ 4 of 6. Exactly 3/6 scores
   NOT-CONFIRMED (MISS). The tie is frozen now because the development X7 rate sat
   at exactly 3/6.
3. **Non-flat θ=0 corruption vehicle (C3).** The X8 θ=0 anchor trajectory is flat
   (D ≡ 1), so the sign-corruption falsifier could pass vacuously there. The
   X5-variant θ=0 arm is MANDATORY as the corruption vehicle (discharged
   demonstration: dense agreement 2.0e-15; the 1→0→1 Clifford recurrence at
   r7–r9; three sign-corruption variants each collapse an exact instrument
   value to 0.0). Because the θ=0 D-trajectory is provably sign-blind
   (letters-only), the confirmatory harness runs BOTH gates: the D-trajectory gate
   AND the inner-product/A–G reproduction gate.
4. **All-below-margin adjudication (C4; owner-decided 2026-08-01: strict).** If all
   six confirmatory cells report WITNESS_BELOW_MARGIN, the outcome scores as a
   fixture-capability MISS at the current carrier error floors — this fixture
   cannot certify the witness with these carriers — and the confirmatory claim
   dies. It is NOT evidence of witness absence. Revisiting requires a NEW
   preregistration round anchored on a demonstrably lower MEASURED err_cell; the
   development margins (1.5×–31×) were computed against an err_cell never measured
   on the modified fixture, and this clause forecloses post-unblinding floor
   shopping.
5. **R0 discharge against the row's own criterion (C5).** R0 is discharged by
   commit edb8ae8 (Stage-0 amended acceptance, threads 1/2/4/8; flag-off control
   still FAILs). The row's criterion — thread variance ≤ (smallest discriminating
   difference)/10 = 1e-4 — is met by the MEASURED value, not by the band: the
   committed runner records a ≥ 53× worst-pair margin against its 6.1e-4 fallback
   band, i.e. measured worst-pair 1-F ≤ 1.2e-5 < 1e-4. The band alone would NOT
   satisfy the criterion. The confirmatory run's provenance must re-record the
   measured worst-pair value from its own Stage-0 evidence and the run is REFUSED
   if that value exceeds 1e-4.
6. **Geometry acknowledgment (C8).** The v2 geometry remains exactly-MPS under rung
   fusion (the central cross-row CX(3,10) is a rung gate). Escape from v1-death-3
   is via the §4 no-carrier-claim bound only. No PEPS/2D-representational-content
   claim may ride on this fixture in any report.
7. **Corruption-trip discharge nuances (§3a).** All four to-demonstrate trips fired
   with non-corrupted controls passing. Binding nuances: (i) item 3's dual-gate
   requirement; (ii) the "≥ 1e-2" insertion-shift parenthetical is the verifier's
   X5 measurement — X8's own end-of-round shift measures 7.696e-3 (still ~10⁷× the
   emitter guard); X5-measured numbers are citable only as X5's (also rereview M3).
8. **Inherited v1 exactness controls.** The confirmatory harness must re-trip the
   inherited v1 exactness controls at run time (§3a inherited row); the four
   demonstrations above do not cover them.
9. **Remaining pre-run engineering (C6, C7), recorded.** (i) Production emitters
   for the CX-only and thin-only P2 arms; (ii) the engine v2-schema dispatch /
   every-round-checkpoint diff (owner-reviewed, load-bearing surface); (iii) the
   committed confirmatory harness embedding items 3, 5, and 8; (iv) the
   Masot-Llima (arXiv:2602.15942) T/N-regime paper_fact note row must be admitted
   before any report cites regime placement. Reporting rules from rereview minors:
   rotation counts are cited as rotations, not events (M7).

## Pre-run amendment 2 (2026-08-01): confirmatory frame arithmetic and harness ambiguity rulings

Appended after the confirmatory-harness build surfaced eight ambiguities (FA-1..FA-8
in the harness build report); owner-decided 2026-08-01. Append-only; no frozen band
or prediction is altered. Amendment 1 item 1 contained an arithmetic defect, corrected
here: a witness cell CONSUMES the registered input pair (the BLP distinguishability
D(r) is computed between the two inputs' trajectories), so "× inputs {1,2}" cannot
multiply cells, and one heldout seed × γ{1,2,3} yields three witness cells, not the
six that P1/P2 and amendment-1 items 2 and 4 adjudicate.

1. **Six-cell confirmatory frame, frozen (FA-1).** The confirmatory cells are exactly:
   heldout seeds {hv2-0, hv2-1} — the FIRST TWO seeds of the existing v2 heldout
   derivation stream — × γ-index {1, 2, 3} × w7 r10 × the X8 arm, each cell carrying
   the registered input pair internally. Six cells, structurally congruent to the six
   development screening cells. This requires widening the emitter's heldout
   namespace admission from one seed to two, as a separate owner-reviewed diff;
   the second seed inherits every collision/anti-build guard, and NOTHING from either
   heldout seed may be built before the owner's release of the confirmatory run.
2. **X5-θ0 vehicle by equivalence (FA-2).** At θ = 0 every rotation is the identity
   and thinning acts only on rotations, so the X5-variant θ=0 Clifford stream equals
   the CX-only arm's stream operation-for-operation. The mandatory X5-θ0 anchor arm
   is REALIZED AS the landed cx-only-arm emitter at θ=0; the harness must verify and
   print the op-for-op equivalence at run time (already demonstrated in the dry run).
   X5-measured numbers remain citable only as X5's (amendment 1 item 7).
3. **Inherited-control surfaces (FA-5).** (i) The "untruncated run F = 1" control is
   retained: a separate owner-reviewed diff adds an explicit uncapped-bond override
   to the plain engine, reachable ONLY from the confirmatory harness's control lane;
   the control's semantics are unchanged. (ii) The "LOCAL-alphabet F = 1" inherited
   row is AMENDED DOWN with justification: no implementation exists anywhere in the
   repository, rebuilding one is new mechanism code carrying its own validation debt,
   and the remaining controls (untruncated F=1; θ0-plus-no-CX constancy with firing
   corruption trip; the dual θ0 gates; the §3b controls) cover the pipeline-integrity
   surface it addressed. Its removal is a disclosed weakening, not a silent one.
4. **err_cell definition (FA-3).** Both operational definitions — trajectory-level
   max_r |D_r^plain − D_r^dense| and state-level max reduced trace distance over
   checkpoints and inputs — are computed and recorded; the run REFUSES if they ever
   classify a cell differently under the 10×-margin rule.
5. **Arms are controls, not cells (FA-4).** The CX-only and thin-only arms run on the
   same six coordinates as P2 controls; they are never additional confirmatory cells
   and never carry witness adjudication weight outside P2.
6. **Minority semantics (FA-6).** "Minority" for the thin-only sub-claim is the
   complement of the ≥4/6 majority rule: ≤2/6 is a minority PASS for that sub-claim;
   exactly 3/6 scores the sub-claim NOT-CONFIRMED (mirrors amendment 1 item 2).
7. **P1 read conjunctively (FA-7).** Per cell, P1 requires guard AND magnitude band
   AND location band simultaneously; the three components are additionally reported
   separately for audit.
8. **Fresh-cell control deviations (FA-8).** The §3b inert-checkpoint control's
   numeric cross-check (+7.227e-4 at r8→r9) binds on the development cell only; on
   confirmatory cells the control's value is recorded and any deviation is a reported
   finding, not an automatic refusal (the refusal surfaces remain the frozen gates).

## Pre-run amendment 3 (2026-08-01): fifteen-cell frame, parallel topology, owner ratifications

Owner-decided 2026-08-01, after review and landing of the confirmatory package
(commit e2a5b8c). Append-only; per-cell bands and all gate semantics are unchanged —
only the frame size, the derived adjudication counts, and two numeric/topology
selections change, before any heldout byte has ever been derived.

1. **Fifteen-cell confirmatory frame.** Two heldout seeds give too little replication;
   the frame becomes FIVE heldout seeds × γ-index {1, 2, 3} × w7 r10 × the X8 arm
   (registered input pair internal to each cell) = 15 confirmatory cells. Seed
   derivation, frozen: with D0 = sha256(b"gcapeps-finite-memory-heldout-v2") and
   D1 = sha256(D0), the seeds hv2-0..hv2-4 are the consecutive non-overlapping
   big-endian 8-byte windows [D0[0:8], D0[8:16], D0[16:24], D0[24:32], D1[0:8]] —
   a deterministic hash-chain stream with zero new inputs; hv2-0 remains
   byte-identical to the originally frozen seed and hv2-1 to the landed second seed.
   All five inherit every collision and anti-build guard, pairwise distinctness is
   guarded, and NOTHING from any heldout seed may be built before the owner's
   release token.
2. **Adjudication counts rescale by fraction, not by renegotiation.** Amendment 1
   item 2 chose the strict 2/3 fraction (≥4/6); the same fractions apply verbatim to
   15: P1 guard and P2 X8 majority = **≥ 10/15**; thin-only minority = **≤ 5/15**;
   any count strictly between 5 and 10 scores the affected sub-claim NOT-CONFIRMED.
   The strict all-below-margin rule (amendment 1 item 4) now reads over all 15 cells.
3. **Parallel execution topology.** Confirmatory cells execute in PARALLEL as fresh
   single-threaded child processes (thread envelope pinned per child, exactly as the
   serial design), with the acceptance-supervisor discipline: the immutable plan is
   written before any child launches, bounded concurrent jobs, one aggregation
   writer, atomic summary publication. Parallelism changes wall clock only; every
   per-cell computation, gate, and record is identical to the serial semantics, and
   the runner must refuse if any child reports a thread envelope other than 1.
4. **Untruncated F=1 band: 1e-12, owner-selected** (was 1e-10 in the landed package).
   If the control cannot meet 1e-12 for a numerically justified reason, that is a
   dated-erratum FINDING with the measured value — never a silent widening.
5. **Engineered-fixture claim boundary.** The v2 fixture is an engineered-schedule,
   witness-positive TEST ARTICLE: the even-round cross-row CX, its pinned position,
   and the halved collision density were selected by screening precisely to produce
   the witness. No generic-noise or naturally-occurring-non-Markovianity inference
   may ride on any v2 result, in any report; v2 results certify instrument
   capability only. The harness payload claim_boundary must carry this sentence.
6. **Owner ratifications recorded.** The hv2 derivation reading (consecutive 8-byte
   windows of the frozen digest, item 1's chain extension) and the plain-engine
   untruncated_control override (control-lane-only, instrumented-refused) are
   ratified as reviewed and landed in e2a5b8c.

## Pre-run amendment 4 (2026-08-01): untruncated-control vehicle after measured infeasibility

Owner-decided 2026-08-01, during the first release-token execution. FINDING: the
inherited "untruncated run F = 1" control is computationally INFEASIBLE at the
confirmatory coordinates — an uncapped plain child on the loopy w7 r10 lattice was
measured at 2 h 17 min CPU and 11 GB RSS, still growing (uncapped bond growth is
exponential on the 2×7 cycle graph; the control's v1-native context was w3-scale).
The aborted attempt built only the first cell's controls fixture; no adjudication
artifact was produced and no band was consulted, so nothing is unblinded. Rulings:
1. The untruncated F = 1 control is RE-VEHICLED to the v1-native feasible
   coordinates: one uncapped plain child per run on a w3-scale fixture through the
   IDENTICAL code path (plain engine, untruncated_control opt, fidelity-vs-dense
   gate at the amendment-3 1e-12 band). On-coordinate (w7) pipeline integrity
   remains covered by the existing exact-regime agreement gates and the capped
   err_cell lanes.
2. Control children gain a RESOURCE REFUSAL guard (wall-clock timeout): a control
   that exceeds its budget refuses the run with the measured evidence — never
   hangs, never silently degrades.
3. The infeasibility is recorded as a disclosed defect of amendment 2 item 3i's
   feasibility assumption (no coordinate-level screen was run before freezing the
   vehicle); this amendment is that screen's finding.

## Pre-run amendment 5 (2026-08-01): the section-3b control's vehicle is the development cell

FINDING, second release-token execution: the section-3b inert-checkpoint control is a
P0 (v1-family) fact, but the runner asked the v1 emitter to build P0 at the first
CONFIRMATORY coordinates. That is unbuildable BY CONSTRUCTION — P0's HELDOUT
partition carries v1's own frozen heldout seed, which is not a v2 stream seed and
whose science namespace stays untouchable under the standing v1 freeze (the v2
release token releases the v2 namespace only). The v1 emitter refused correctly;
the run stopped before any witness computation (nothing unblinded; the theta-0 and
inherited-control gates had already passed, including the amendment-4 w3 vehicle at
1-F = 1.11e-16). Rulings:
1. The section-3b control RE-VEHICLES to its own development cell (CALIBRATION
   s2-g2-r10 w7), where amendment 2 item 8 already binds its numeric cross-check
   (+7.227e-4 at r8→r9); it runs there as a run-time re-trip, like every other
   inherited control vehicle. The control certifies a schedule-family property
   (shipped checkpoint set is witness-blind on P0 while every-round is not); it
   was never per-confirmatory-cell evidence.
2. Amendment 2 item 8's phrase "on confirmatory cells the control's value is
   recorded" is recorded as VOID AS WRITTEN for this control: P0 at v2-heldout
   coordinates cannot exist. The recording clause survives only where a control
   actually runs.
3. The control function gains a fail-closed guard: any non-CALIBRATION vehicle
   request refuses outright — no control lane may ever build from a heldout seed
   of either namespace.
