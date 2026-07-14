# HISTORICAL PEPS c64 build proposal — BLOCKED / NON-AUTHORIZING (2026-07-11)

This is retained design provenance for a proposed PEPS c64 variant. It **does not amend**
`peps_singlewire_spike_contract.md` SW-S8: PEPS remains `torch-cuda-complex128 ALWAYS`.
The historical design detail lives in `c64_screening_engine_plan_2026-07-11.md`; neither
document authorizes implementation or a run.

> Contract-build Stage 1 artifact. **2026-07-13 theory-fix verdict: REPAIR.**
> The active policy applies only to `FusedWithinCycleSampler` / `sv_traj_d3_wc`:
> ``optimization -> c64 / screening_only`` and
> ``final|certification -> c128 / c128_candidate``. The PEPS c64 build described below
> remains **BLOCKED**: it requires the
> dtype-aware tolerance/FET work fenced out of the current P0.  No c64 scientific
> artifact is ever evidence-eligible; a candidate conclusion requires a separate frozen
> c128 artifact and its owning scientific gates. The threshold proposals below are retained
> as unapproved historical hypotheses, not implementation authorization.

---

## 1. Historical proposed scope — currently blocked

**Not in the current build.** The 2026-07-11 proposal would have threaded a per-run
`dtype ∈ {c128, c64}` through
the 2D PEPS single-wire carrier (`carrier/peps/{state,contraction,stab_tt,
trajectory}.py` + the reused cutters `carrier/pepo/dynamics.py`), plus the
**frozen-branch c128-vs-c64 validation harness** (an `outputs/` runner). That deliverable
is blocked and has not superseded the c128-only PEPS contract.

**Historical fences (no phase below is active):**
- F1. The actual multi-round (~20–30) bond-saturation **screening RUN** and the
  **re-derivation of the SW8 runner §6.2 floors** (`FLOOR_P0_MOVEMENT`,
  `FLOOR_CROSS_ROUTE_D5`, `FLOOR_CHIB_DOUBLING`) for c64.
- F2. Any **GB10/spark c64-reliability** probe.
- F3. Any change to the **c128 evidence path semantics** — c128 must stay
  byte-identical (G0).

**Current invariant:** PEPS has one c128 path. The proposed two-engine invariant below is
historical only; reactivation requires a new user authorization and a theory-first/tolerance/FET
review.

---

## 2. Historical representation proposal — do not implement

A `PepsState` carries a declared `dtype` (its site tensors' complex dtype). The
**real dtype stays float64 in BOTH engines** (`RDTYPE=float64` unchanged — all
squared-σ / tail / rank arithmetic accumulates in f64 on top of the state's f32/f64
σ's).

| Op class | pre | post | rule |
|---|---|---|---|
| site tensor construction (`PepsState.__init__`) | `data.dtype == state.dtype` | gate accepts the DECLARED dtype | parametrized assert, not literal c128 |
| codestate build | built c128 | `.to(state.dtype)` AFTER all c128 asserts | c128 island → cast at the boundary |
| operator build (`qutrit_gate`, leak Kraus, stab-TT cores, terminal/cap effects) | built c128 | **cast to `state.dtype` at apply** | operators are c128 islands; the op↔state dtype join must match or `tensordot` up-casts the state |
| boundary read / SVD / QR (`contraction.*`, `_qr_split`, `_insertion_spectrum`, `svd_precut_bond`, `ntu_truncate`) | input = state tensor (state.dtype) | output follows input dtype | **the free c64 win**; no cast needed, only the reconstruction casts must follow state.dtype |
| cutter reconstruction (`sqrt_s`, `MA/MB`, `Rm`, `_gauge_cut_pair`) | — | cast to `state.dtype` (not pepo-c128) | else the written-back state reverts to c128 |
| NTU metric g + pinv refinement | may stay c128 (small island) | write-back cast to state.dtype | value-only refinement within the fixed rank; c128 costs ~0 |
| tail/rank arithmetic (`_sq_tail`, `_rank_for_tail`, `_exact_rank`) | σ's in state real-dtype | **accumulate in float64** | close the `(S*S).real`→f64 asymmetry |

**Post-condition invariant (every op):** the state's site-tensor dtype after the op
equals `state.dtype` (no silent up-cast). This is the single most-tested post-condition.

---

## 3. Historical referee proposal and its unresolved limit

The proposal would compare every c64 unit with **the SAME unit at `dtype=c128`** on a **frozen
branch** (§4 G3–G7). This is a **precision (simplification-bound) referee**, not an
independence referee. It cannot establish carrier faithfulness:

1. The c128 PEPS carrier is a **reference/evidence candidate**, not ground truth. Its d3
   checks constrain implementation behavior, while full multi-round record faithfulness remains
   open under `docs/SIMULATOR.md` and ADR 0011.
2. A hypothetical c64≈c128 frozen replay would bound only the additional precision
   simplification. It would not promote either artifact or close the record-faithfulness gap.

**Honest limit:** d5 exact-DM is infeasible, so c128 PEPS is not independent ground truth
there; a hypothetical c64 comparison would add another approximation layer to an already
oracle-free regime.

**Bounded independence note:** the formula-built qutrit gate table shares no implementation path
with `exact/qutrit_dm` for that local D4 check. This does not make the c128 PEPS carrier an
independent full-record ground truth.

---

## 4. Historical threshold hypotheses — BLOCKED; no tolerance/FET authorization

| Threshold | value (c128) | value (c64) | UNITS | action |
|---|---|---|---|---|
| dynamic-eps cut `eps_spike` | 1e-8 | **1e-8 (unchanged)** | **relative squared-σ tail** (Σ_{k>r}σ²/Σσ²); cut ⇒ σ/σ₀~1e-4 | NO CHANGE — 3 orders above the c64 amplitude floor |
| rider eps arms | 1e-6, 1e-10 | same | rel squared-σ tail | 1e-10 ⇒ σ/σ₀~1e-5, still 2 orders up — keep |
| exact-rank / structural drop `> NUMERICAL_ZERO·σ₀` | 1e-12 | **~1e-6** | **relative amplitude** (σ/σ₀) | dtype-aware: split NUMERICAL_ZERO's dual role — 1e-12 stays for O(1) floors; a NEW ~1e-6 rel drop for c64 rank/SVD reads |
| CPTP / Kraus completeness | 1e-12 | **1e-12 (kept, c128)** | abs `max|ΣK†K−I|` | operators stay c128 → keep the check c128; do NOT relax |
| `_FIT_TOL` (boundary fit) | 1e-12 | **~1e-6** | ALS residual delta | relax or the fit burns all 64 iters every read (speed loss) |
| `_NTU_PINV_RTOL`, `_NTU_REL_STOP` | 1e-12 | **~1e-6** (if NTU run c64) | rel | else pinv inverts noise → NaN; moot if NTU stays c128 |
| `bp_tol`, `_EPS_L_BOUND_TOL` (eps_l) | 1e-10, 1e-9 | ~1e-6 | rel / abs | diagnostic only; relax to keep WP2 numbers usable |
| O(1)-norm positivity floors | 1e-12 | **1e-12 (unchanged)** | abs on O(1) norms | 1e-12 ≪ c64 noise on an O(1) quantity — safe |
| structural `|2>`-mass zero | 1e-12 | **1e-12 (unchanged)** | abs; slot-2 is exact 0 | structural zero survives fp32 — do NOT relax |
| SW8 runner §6.2 floors | 1e-8 / 1e-6 | **re-derive by MEASUREMENT** (F1, deferred) | rel | class (c); measured c64-vs-c128 gap, never guessed |

**Epistemic class of each c64 threshold change:** class **(c)** design constant
(a screening gate), declared here; the c128 values are unchanged and remain whatever
class they already are.

---

## 5. Historical proposed gates — not registered for current execution

| Gate | Statement | Input | Tolerance | Prediction | Class |
|---|---|---|---|---|---|
| **G0** (regression, PRIMARY) | at `dtype=c128` the d3 suite is **byte-identical** to the pre-change baseline | `tests/test_peps_spike.py` (28) + hashed sample outputs vs a git-worktree baseline at the pinned parent commit | exact hash equality; 28/28 | pass — c128 untouched | (a) |
| **G1** (c64 codestate) | c64 codestate `|2>`-mass **== 0.0 exactly**; `‖c64−c128 codestate‖` bounded | build both, compare | `|2>`-mass == 0.0; ‖Δ‖ ≤ 1e-6 | pass | (a)/(c) |
| **G2** (no loud failure) | on a short c64 run (rounds 1–2) the 4 showstopper asserts do NOT trip: stab-TT `ranks≤(3,5,3)`; CPTP; `_exact_rank` returns true rank (not full); fit/NTU reach tol (not max-iter) | c64 run, R=2 | all asserts pass; fit iters < max | pass after the §4 relaxations | (c) |
| **G3** (frozen eps-rank — THE BOUND) | per-edge `r_dyn` agrees c64-vs-c128 within **±2 every round** AND **mean(c64−c128) ≥ 0** | frozen c128 branch (d3 full + the c128 triage rounds), replayed in c64 | ±2 per round; mean ≥ 0 | pass | (c) |
| **G4** (noise floor) | c64 insertion-spectrum noise floor **< 1e-4·σ₀** every round | same frozen run | < 1e-4·σ₀ | pass | (c) |
| **G5** (spectrum overlay) | sorted σ/σ₀ overlay at `B1_3` + per-round max bond agrees down through the 1e-4·σ₀ band | frozen run | agree ≥ ~1e-4·σ₀ | pass | (a)-ish |
| **G6** (read-error budget) | `max|Δp0| ≤ 1e-5`; would-be free-sampling branch flips ≈ 0 over the record | frozen run | ≤1e-5; flips ~0 | pass | (c) |
| **G7** (eps-band) | eps ∈ {5e-9,1e-8,2e-8}: saturation TREND qualitatively identical c64 & c128 | frozen run | qualitative match | pass | (c) |
| **G8** (speedup — raison d'être) | c64 per-round wall ≤ 1/5 of c128 on the same round | timed round | ≥ 5× (target 10–30×) | pass | (c) |

**Historical direction-sign proposal:** a c64 "grows/No-Go" flag would have been only a
screening trigger; a c64 "bounded/saturates/GO" reading would have required a separate c128
run. No current PEPS run or gate is authorized by this paragraph.

---

## 6. Historical build plan — BLOCKED

- **Module builder A** — dtype threading in `state.py` + `contraction.py` +
  `stab_tt.py` (state construction gate, codestate cast, op-apply dtype match, fit
  guess/tol, boundary reads). Owns the "state side".
- **Module builder B** — dtype threading in `trajectory.py` + the reused cutters
  `pepo/dynamics.py` (the `_sq_tail`/`_rank_for_tail`/`_exact_rank` f64 asymmetry, the
  reconstruction casts, the dtype-aware rank threshold split, the CPTP/NTU islands,
  `PepsSampler.sample` reading `spec.dtype`). Owns the "truncation/trajectory side".
- **Test builder** (parallel, cannot see the code) — writes G0–G8 against THIS
  contract, plus the KILLER catalog (Stage 6): a sabotaged variant per load-bearing
  assert (e.g. an op left at c128 → G-postcondition must trip; a c64 rank read at the
  1e-12 threshold → G2 must trip; RDTYPE dropped to f32 → G3/G4 must degrade).
- **The frozen-replay harness** (`outputs/`) is a committed runner: it takes a c128
  reference record (d3 + the triage rounds), forces the identical host-RNG branches in
  the c64 replay, and emits the G3–G7 comparison tables.

**Ban:** builders do static checks + `py_compile` + `--collect-only` only. All GPU
runs serialize with the orchestrator AND wait for the c128 triage to free the GPU.

---

## 7. What could make a correct implementation FAIL a gate (for the red-team to hunt)

Seed list (extend in Stage 2): (a) is the ±2 tolerance in G3 too tight if the true
spectrum has a dense shoulder at 1e-4·σ₀ (skeptic FM-6)? (b) does "mean(c64−c128)≥0"
have a defensible estimator + sample size, or can a single deflating round hide in the
mean? (c) is G0 byte-identity actually achievable, or does adding a `dtype` kwarg with
a c128 default perturb any codepath (e.g. a changed tensor-construction order)? (d) is
the c128 "frozen branch" long enough (the triage only reaches round 2) to certify a
20–30 round screening claim, or is G3 certifying far less than the run needs? (e) does
forcing host-RNG branches actually reproduce identical branches, given the p0/pk reads
differ (the branch is chosen from `u < p0`, but the STATE evolution downstream diverges
after the first non-forced numerical difference)?

---

## 8. Epistemic classing (closes the loop, Stage 7)

Had it been built, PEPS c64 outputs would have remained class **(c) heuristic screening**.
They would never become evidence. A separate c128 final/certification artifact would still be
only `c128_candidate` until the owning scientific gates passed. This proposal remains blocked.
