# GCAPEPS compression ladder — four-arm A/B Pre-Registration

Status: PRE-REGISTRATION, 2026-08-01. Predictions written BEFORE any run; a miss is a
finding, not a re-fit. Supersedes the A/B scope of
`GCAPEPS_BATCHED_EVENT_PEPO_PREREG_2026-08-01.md` (its mechanism closure, exactness
validators, corruption trips, and controls are inherited unchanged and remain in force).

## Erratum to the superseded prereg (recorded, not rewritten)

The independent verifier of the batched-event development A/B found two text defects in
the superseded prereg's P1, frozen before those runs: (i) the parenthetical "r4 cell:
57" misattributed the r10-cell P0 screen count to the r4 cell (which has 24 realized
events per input); (ii) "sequential arm = 3× that" holds at rotation granularity
(72 truncating rotations vs 24 events), not at event granularity. The class-(a)
relations that transfer held exactly (rank 2 ⇒ r = 4 for 24/24 events; plan computed
before the state run and matched exactly). The superseded P2 result stands as a
registered MISS: batched-greedy is worse than sequential-greedy by +7.7–9.1% relative
infidelity at round 3 (exceeding the 5% band) and +3.7–4.4% at round 4.

## -1. Question charter

- **Decision + consequence:** which compression discipline the batched-event lane
  should carry. The miss established that on this carrier, a more exact intermediate
  representation loses under greedy fabricated-gauge truncation; the field's libraries
  answer with variational fitting or environment-weighted truncation. This experiment
  decides between four arms on one frozen cell. Consequence: the winning arm becomes
  the registered candidate for the carrier-accuracy program; a null (no arm beats the
  shipped path) closes the batched-accuracy line entirely.
- **Attackability:** dense oracle at n=14; the batched lane's exact lowering is
  validated at 5e-16; the new compressors are upstream-tested quimb machinery
  (`fitting.py` ALS tests on 4-regular graphs; `tnag/compress.py` l2bp).
- **Alternative formulations:** YASTN EnvNTU/EAT truncation is the cross-stack
  formulation of arm D (registered as a possible follow-up leg, not run here).
- **Kill condition:** if neither C nor D beats A at any checkpoint, batching dies as
  an accuracy lever in full (wall-clock-only lane); if C or D beats A, the compression
  discipline — not the representation — is established as the binding constraint.

## 0. Arms (frozen)

All arms: r4 calibration cell (`calibration-g2-s2-w7-r4-a3-p3of4`), inputs 1 and 2,
cap 32, thread 1, `trim_cluster` ON, shipped wholesale policy, dense oracle truth at
every round checkpoint. Development execution first; the registered comparison awaits
the independent rereview of this prereg.

| arm | representation | compression | status |
|---|---|---|---|
| A | sequential two-term trees | greedy per-edge SVD, SU gauge (shipped) | control (measured) |
| B | batched four-term event PEPO | same greedy per-edge SVD | control (measured, the MISS) |
| C | batched event PEPO, exact fused candidate | **variational fit**: bond-32 state ALS-fit against the exact fused network (`fit_`, warm start = the arm-B greedy result; iterations/tol frozen below) | to build |
| D | batched event PEPO, exact fused candidate | **environment-weighted compression**: BP-message-weighted bond compression (`tensor_network_ag_compress(method='l2bp')`, convergence knobs frozen below) | to build |

Frozen compressor parameters (class (c) configuration, disclosed not tuned):
C: ALS `max_iterations=40, tol=1e-10`, warm start from the greedy-compressed state,
distance objective as shipped in `fitting.py`. D: l2bp defaults at the pinned fork
revision with `max_iterations=1000, tol=5e-6` message convergence; damping default.
Any deviation forced by the API is reported verbatim, never silently substituted.

Arms C/D may run at harness level on the validated uncompressed candidate (the fork's
exact lowering, I1-validated); strict carrier-ledger integration is NOT required for
the development comparison and is out of scope until an arm wins.

## 2a. Predicted observables (frozen)

- **P1 (class (a)):** arm combinatorics equal arm B's plan ledger (24 events, r = 4,
  exact fused bond ≤ 128); C/D perform exactly one compression per event.
- **P2 (class (b), the core bets):**
  - **P2a:** `1-F(D) ≤ 1-F(B)` at every checkpoint (environment beats greedy on the
    identical batched object).
  - **P2b:** `1-F(C) ≤ 1-F(A)` at every checkpoint (avoiding intermediate collapse
    beats the shipped path) — the headline bet; a miss kills the batched-accuracy
    line per the charter.
  - Ordering hypothesis (weaker, directional): C ≤ D ≤ B and C ≤ A. Bands: a claimed
    improvement must exceed 5% relative infidelity at the deciding checkpoint;
    differences within ±5% relative are reported EQUIVOCAL, not wins.
- **P3 (class (c) gates):** wall-clock C ≤ 5× A (ALS is expensive; the gate bounds
  tolerable cost); D ≤ 2× A. Algorithm-only and evidence-inclusive timings per v1
  discipline.
- Insufficient statistics (forbidden as headline): discarded weight; fit residual
  alone (must be reported beside dense fidelity, never instead of it).

## 2b. Disconfirmation surface

Strongest competitors: (i) the greedy sequence's implicit regularization survives even
against variational compression (C loses to A — kill condition); (ii) BP environments
on this loopy ladder are too mean-field to help (D ≈ B); (iii) ALS local minima from
the greedy warm start (control: one cold-start replicate per input at round 4 must
agree with warm start within the band, else reported as initialization sensitivity).

## 3. Independent ground truth

Dense oracle (import-firewalled) for every fidelity; the exact fused candidate is
I1-validated (5e-16) before any compressor touches it; fit/l2bp convergence records
disclosed per event.

## 3a. Constraint ledger additions (inherited rows remain)

| constraint | assertion | falsifier | broken input | trips |
|---|---|---|---|---|
| fit target integrity | arm C fits against the exact fused network | fit against a one-term-sign-flipped target must degrade dense fidelity > 1e-3 | sign-flipped term | to demonstrate pre-run |
| compressor equivalence at trivial cap | with `max_bond` ≥ exact rank, C and D reproduce the exact state to 1e-12 | uncapped control | — | to demonstrate pre-run |
| arm isolation | at event 1 (both inputs) the uncompressed candidates of arms B/C/D are byte-identical; at every later event each arm's candidate passes the I1 exact-lowering check against that arm's own pre-event state (arms evolve their own trajectories and legitimately diverge after event 1) | sha equality at event 1; per-event I1 at 1e-12 thereafter | — | structural. (Pre-run correction 2026-08-01: the original wording "same bytes as B across arms" was unsatisfiable beyond event 1; corrected before any run, no results inspected.) |
| convergence disclosure | per-event iterations/tol recorded; non-converged fits flagged, never silently accepted | harness assertion | forced max_iterations=1 must flag | to demonstrate pre-run |

## 5. Epistemic status

(a) exact: lowering validity; P1; uncapped controls. (b) bands: P2a/P2b/ordering.
(c) gates: P3; convergence flags. Headline PROVISIONAL until independent rereview and
the registered run.

## Gate

premises closed? yes (inherited closure + upstream-tested compressors as class-(c)
configuration) | metric bound? yes (inherited) | predictions frozen? yes | independent
GT? yes | falsifiers registered? yes (4 new rows + inherited) | simplifications
bounded? yes (harness-level arms; single cell; development-first) | controls
registered? yes | **preregistration gate: pass** — execution blockers: the four
pre-run trips above and the independent rereview before any registered comparison.

## Pre-registered-run erratum (2026-08-01, prescribed by the un-led independent review)

Recorded after the development execution and its un-led review (verdict: PASS,
conditional), BEFORE any registered run. Nothing below alters a frozen prediction or
band; each item repairs a text defect or registers an executed detail the review
found under-specified.

1. **Arm-C warm start wording.** "warm start = the arm-B greedy result" is
   satisfiable only at event 1 (arms evolve their own trajectories and legitimately
   diverge). The registered semantics — the only coherent reading, and the executed
   one — is: at each event, the warm start is the greedy compression of THAT ARM'S
   OWN exact fused candidate. The same divergence caveat applies to P2a's phrase
   "on the identical batched object": identity holds at event 1; thereafter each
   arm's candidate is exact for its own trajectory (per-event I1 at 1e-12).
2. **Verdict rule pinned.** "Holds at every checkpoint" means: no checkpoint worse
   beyond the 5% relative band (band-lenient ≤). The deciding checkpoints for the
   >5% improvement requirement are the final two round checkpoints (r3, r4);
   rounds at the machine floor (|1-F| < 1e-12) are marked FLOOR and excluded.
3. **Executed compressor configuration folded into the frozen text** (all forced by
   the shipped APIs, disclosed at execution, empirically confirmed by the review):
   `fit_` names its iteration cap `steps`; the ALS local solver uses
   `enforce_pos=True` with `pos_smudge = max(tol, 1e-15) = 1e-10` (default dense
   solver raises LinAlgError on this carrier's rank-deficient local grams); per-sweep
   convergence disclosure drives shipped single-sweep updates with the shipped stop
   rule `|d_k − d_{k−1}| < tol`; l2bp wrapper defaults `cutoff=1e-10`,
   `cutoff_mode='rsum2'`, `damping=0.0`, `update='sequential'`,
   `local_convergence=True`.
4. **Fit-target corruption term selection registered.** The flipped term is the
   first nonzero non-leading term whose pulled-back word MOVES the pre-event ray
   (a stabilizing-term flip is invisible to normalized fidelity — observed and
   corrected before the trip passed; the incident is recorded in the trips log).
5. **Anti-degeneracy instrument restated self-contained** (replacing the dead
   locator "spec §0b.6", whose source is the gitignored review artifact
   `outputs/gcapeps_review_a_2026-07-30/PARITY_REPAIR_SPEC.md` §0b.6): pullback
   weight is reported BESIDE every fidelity number; parity/fidelity at mean pullback
   weight ≈ 2.00 is the degenerate regime and is labeled as such. Registered
   artifacts must emit the pullback rows/weights themselves (not only their sha)
   beside the fidelities.
6. **Fired control carried forward.** Arm C is designated INITIALIZATION-SENSITIVE
   (cold start +44..+85% relative at r4, outside band) and 13/24 warm fits per input
   flagged non-converged at the 40-sweep cap; any registered arm-C headline carries
   both disclosures prominently.
7. **Arm E boundary.** The post-hoc composition arm E (l2bp-init + ALS fit) is
   outside this preregistration's arm table and may not enter the registered
   comparison without a frozen amendment carrying its own predictions.

## Pre-registered-run amendment 2 (2026-08-01): registered cells and provenance stamps

Recorded BEFORE the registered execution; no C/D/E result exists for any cell named
fresh below.

1. **Registered cells.** The registered comparison runs all four arms on the w7 r4
   γ-index-2 CALIBRATION cells at seeds **0, 1, 3** (never executed under arms C/D;
   FRESH), inputs 1 and 2. Seed 2 is additionally re-executed and reported as
   DEVELOPMENT-REPLICATE context only (its development results were inspected; it
   carries no registered standing). All frozen predictions (P1, P2a, P2b, ordering,
   P3 gates), bands, FLOOR rule, and controls apply per fresh cell unchanged. Arms A
   and B are executed fresh on every registered cell (the development A/B artifacts
   were seed-2 only and are never promoted).
2. **Provenance stamps (review conditions 1–2).** Every registered artifact records:
   the main-repository HEAD commit, the fork commit (batched lane landed as
   `87ad6ad6`), the sha256 of this preregistration file at run time, the committed
   runner script's own sha256, the fork pixi lock hash, and the interpreter version.
   The runner is a committed script under `scripts/external_baselines/`; the
   development harnesses in `.scratch` retain no registered standing.
3. **Cold-start control scope.** One cold-start arm-C replicate per FRESH cell
   (input 1, round-4 comparison), same disclosed scheme; fired results are reported
   under the registered initialization-sensitivity designation.
