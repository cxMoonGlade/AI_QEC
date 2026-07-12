# c64 screening-engine BUILD CONTRACT (2026-07-11, DRAFT — pre-red-team)

**Companion to** `peps_singlewire_spike_contract.md` v1.0 (this **amends SW-S8**
`torch-cuda-complex128 ALWAYS` by introducing a **declared, bounded c64 screening
variant** that runs alongside — never replaces — the c128 evidence engine).
**Design detail** lives in `c64_screening_engine_plan_2026-07-11.md`; this contract
pins only the commitments a gate must certify.

> Contract-build Stage 1 artifact. Status: **DRAFT — awaiting Stage-2 red-team to
> zero blockers before any code.**

---

## 1. Scope & the two-engine invariant

**In scope (Phase-1 = THIS build):** a per-run `dtype ∈ {c128, c64}` threaded through
the 2D PEPS single-wire carrier (`carrier/peps/{state,contraction,stab_tt,
trajectory}.py` + the reused cutters `carrier/pepo/dynamics.py`), plus the
**frozen-branch c128-vs-c64 validation harness** (an `outputs/` runner). Deliverable
= a c64 engine that PASSES the validation gates G0–G8 below.

**Out of scope (fenced — later, trigger-gated phases):**
- F1. The actual multi-round (~20–30) bond-saturation **screening RUN** and the
  **re-derivation of the SW8 runner §6.2 floors** (`FLOOR_P0_MOVEMENT`,
  `FLOOR_CROSS_ROUTE_D5`, `FLOOR_CHIB_DOUBLING`) for c64 — that is a run phase, not
  the engine phase; the engine only exposes the knobs.
- F2. Any **GB10/spark c64-reliability** probe.
- F3. Any change to the **c128 evidence path semantics** — c128 must stay
  byte-identical (G0).

**The two-engine invariant (load-bearing):** `dtype=c128` is the DEFAULT and its
numerical path is **byte-identical** to the pre-change code. c64 is opt-in. The two
coexist; the c128 globals are NOT mutated — dtype is threaded.

---

## 2. Representation & per-op dtype pre/post conditions

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

## 3. Referee registry (each c64 unit ↔ its c128 referee) + the non-circularity structure

Every c64 unit's referee is **the SAME unit at `dtype=c128`**, compared on a **frozen
branch** (§4 G3–G7). This is a **precision (simplification-bound) referee**, not an
independence referee — and that is correct here, in a declared **two-level** structure:

1. **c128 is faithful** — established SEPARATELY and independently by the d3 gate
   suite (`tests/test_peps_spike.py` vs exact-DM / Stim / closed-form oracles, and the
   S1 boundary-vs-exact d3 unbiasedness result). The c64 build does NOT re-establish
   this.
2. **c64 ≈ c128** — established by this build's frozen-replay (G3–G7). The bound
   COMPOSES onto (1).

**Honest limit (must be stated wherever a c64 number is reported):** at **d5** the
c128 engine itself is faithful only by **d3→d5 extrapolation** (d5 exact-DM is
infeasible — the reason the carrier exists). c64 inherits that existing extrapolation
and ADDS a bounded precision layer; it introduces **no new circularity**, but it is
**not** independent ground truth at d5. Hence the §5 direction-sign gate.

**Independence carry-over:** the c128 engine's own independence (the qutrit gate table
built by formula, sharing no path with `exact/qutrit_dm`, D4) is preserved — the c64
build only casts dtypes, never re-routes a referee import.

---

## 4. Threshold registry — UNITS pinned (the λ-vs-σ discipline)

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

## 5. Registered gates (predict-before-measure — ALL predicted to PASS; a miss is a finding)

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

**Direction-sign meta-gate (binds the RUN phase F1):** a c64 "grows/No-Go" flag may
trigger on c64 alone; a c64 "bounded/saturates/GO" REQUIRES a c128 confirmation at the
same rounds. (The engine phase only needs G0–G8; this meta-gate governs how the later
run reports.)

---

## 6. Build plan (Stage 3 disjoint ownership)

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

c64 engine outputs = class **(c) heuristic screening**. The BOUND is the G3–G7
frozen-replay numbers. c128 remains the evidence engine (its class unchanged).
Provisional-conclusion corollary: nothing downstream builds on a c64 number without a
c128 confirmation (the direction-sign meta-gate).
