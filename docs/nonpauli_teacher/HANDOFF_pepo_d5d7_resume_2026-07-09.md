# Handoff — Resume the d5/d7 PEPO carrier line (2026-07-09)

**Purpose.** A fresh-session resume brief for the 2D density-matrix PEPO carrier work. Covers the
arc that got here, the settled architecture, the VERIFIED d3 feasibility evidence (three gates),
the literature grounding, the complete code/test inventory + results, and the d5/d7 next-step
plan. Companion memories: `project-pepo-d3-feasibility-verified`,
`project-leakage-lru-const-memory-notion2shadow`. git_head at write = `d8d9697`.

---

## 0. One-paragraph orientation (read first)

The target is a **d=5 (and ultimately d7)** faithful/fast/oracle-bounded surface-code forward
SIMULATOR (the mainline error-coupling simulator; NOT a twin, NOT quantum advantage — see
`project-simulator-p0p4-plan-framing`). At d5 the 1D-MPS carrier hits the **2^(2d) bond wall**
(d5 χ≥512-1024 heavy-but-feasible; d7=16384≈630 GB DEAD). The candidate d5/d7 carrier is the
**2D DENSITY-MATRIX PEPO** (pays only the area-law boundary χ_b~D_ρ^d~2^d; d7→128). This session
**VERIFIED the PEPO's central untested feasibility question at d3** (three exact-DM gates, all
green) and settled the engine defaults. NEXT = write the d5/d7 PEPO prereg, then build the engine
(a genuine new build; contract-first; src commit-gated).

---

## 1. 前情提要 — the arc (how this session got here)

Started on **OPT2-2** (batched-MPS trajectory driver, per-round-varying leak). Through a chain of
user course-corrections the scope moved:

1. **OPT2-2 contract built + red-team converged** (blockers 8→2→0, three adversarial passes) —
   then **PARKED**: the user clarified **leakage is PER-ROUND-INDEPENDENT** (hardware LRU/DQLR
   resets |2> each cycle), so per-round-varying leak is off the critical path. Contract is
   correct + trigger-gated in `docs/twin_validation/batched_mps_backend_prereg.md` (§OPT2-2
   DESIGN + red-team OUTCOMES). Do NOT build it unless latent-coupled per-round leakage is ever
   wanted.
2. **Architecture settled** (theory-fix confirmed): **leakage = non-Pauli FLAVOR** (LRU-const,
   fast SV kernel at d3); **memory = notion-2** (classical multi-time record memory);
   **notion-1/CP-div is NOT syndrome-reachable** — appears only as its "notion-2 shadow"
   (protocol boundary). A trip-wire FIRED: "memory from notion-1" as a direct-record premise is
   FALSE. See `project-leakage-lru-const-memory-notion2shadow`.
3. **Target pivoted to d5** (user): SV kernel is d3-only (3^25 explodes), so **MPS is the only
   carrier** → MPS optimization back on. Confirmed MPS CAN carry notion-2 memory (per-round data
   Pauli channel via `kraus_sample_`, same seam as per-round leak).
4. **MPS-optimization literature survey** → 1D-MPS hits the 2^(2d) wall; **pure-state 2D PEPS
   re-incurs the wall** (doubled-layer norm); the ONLY 2D relief is the **density-matrix PEPO**
   (single-layer Tr(ρΠ)). TJM (tensor-jump) is largely inapplicable (our exact 1-site Kraus is
   stronger). → the PEPO route.
5. **PEPO feasibility verified** (this session's main output — §3). User contributed a 20-paper
   PEPO literature survey; own 精读 of the NTU + Kilda notes grounded the engine design.

---

## 2. Settled architecture (verified)

- **Leakage axis** — per-round-INDEPENDENT non-Pauli qutrit channel (LRU/DQLR-justified,
  Miao 2211.04728 "leakage≈Pauli-after-removal" bound; Willow 2408.13687 105Q DQLR deployment).
  On the PEPO: a per-site CPTP qutrit channel, vectorized d²=9 physical index. **Verified today
  to NOT grow the operator bond.**
- **Memory axis** — notion-2 classical multi-time record memory, via a **per-round-varying data
  Pauli channel** driven by an EXTERNAL classical latent (Θ fan-out of a shared latent z_t).
  Validated instrument = the CMI/G² Anderson-Goodman order test
  (`outputs/twin_validation/corrected_multitime_observable_run.py`, PASS). On the PEPO the latent
  is per-sample conditioned (MC average OUTSIDE the TN) → **verified today to be BOND-FREE**. The
  unsolved "PEPO + non-Markovian" seam (no 2022-2026 paper) applies ONLY to the parked
  quantum-bath (notion-3/Branch-B) line — NOT to us.
- **Carrier for d5/d7** — 2D density-matrix PEPO (primary) + 1D fixed-χ MPS (OPT2-3, the
  independent cross-validation arm; different geometry = different blind spot).

---

## 3. The VERIFIED d3 evidence — three exact-DM gates (ALL GREEN)

All on the exact d3 qutrit DM (`carrier/exact/qutrit_dm.py`, 3^9×3^9 ≈ 5.77 GiB), the p1c
physical cell (WG_L1=5e-3, θ=0.102444, g_seep=0.09, g_heat=0, b=0.9, arm=A), non-selective
sequential Lueders measurement, straight column cut A=[0,1,2]|B=[3..8] (x≤5, boundary=d=3). Every
script was un-led-reviewed BEFORE its GPU run (5 blockers caught across the three — see §5).

| Gate | Script | VERDICT | Load-bearing numbers |
|---|---|---|---|
| **R-gate** (does D_ρ grow with R?) | `pepo_feasibility_drho_vs_round_d3.py` | **SATURATE_FEASIBLE** | χ(1e-6)=**16 FLAT** over R=1..10 (= codestate rank, 2 crossing stabs→(2²)²); purity 0.991→0.915 monotone (mechanism live); corrected χ(1e-8)≈50-53 |
| **Record-gate** (does a truncated state reproduce the record law?) | `pepo_record_error_vs_eps_d3.py` | **RECORD_FEASIBLE**, bond χ~16 @ ε*=1e-3 | ε∈{1e-3,1e-4,1e-6} all cut at the SAME χ=16 (spectral gap), max dp=6.65e-6 = **dp/bar=0.017 (60× margin) @ N=1e6, z=4**; ε=1e-8→χ~52, dp/bar=0.039. **FINDING: gap-cut BEATS deep-cut** (ε=1e-8 keeps more weight but errs MORE — the gap-cut projects onto a round-stable subspace) |
| **ξ-gate** (which truncation algorithm?) | `pepo_xi_correlation_length_d3.py` | **ITRSU_VIABLE_NTU_MARGIN** (adjudicated) | dynamical **ξ(Zq)=0.48, ξ(n2)=0.18 lattice spacings** (≪ itrSU's ξ≲2; NTU's ξ~20 = 40× margin). Xq NO_FIT adjudicated (a)-exact BENIGN = the 2 weight-2 X-boundary stabs (s1=X₀X₂, s6=X₆X₈, ⟨XX⟩=1 structural). **X2b: χ(mix)=χ(lo)=χ(hi)=16 — classical latent BOND-FREE** (stronger than the registered subadditivity) |

**Consequence:** the 2D DM-PEPO route is GREEN at d3. Engine defaults settled: **NTU truncation
from the start**, **truncate at the SPECTRAL GAP** (not a fixed ε), **classical latent
per-sample conditioned**. **Scope caveat (honest):** all three are d3-exact-DM only; the
d-scaling (χ_b~D_ρ^d≲2^d) is an EXTRAPOLATION → the d5 tile is rung 2; χ_b itself is measurable
only inside the engine.

Results backfilled into `docs/nonpauli_teacher/2d_peps_leakage_forward_DESIGN.md` header
(✅ FEASIBILITY OUTCOMES block).

---

## 4. Literature grounding

- **Survey map:** `outputs/papers/pepo_survey/PEPO_COMPREHENSIVE_MAP.md` (20 PDFs, 15 精读 notes,
  KG node `pepo-literature-survey-2026-07-09`). arXiv-ID corrections logged there.
- **Truncation ladder** (the engine's algorithm selector, keyed by the ξ-gate):
  itrSU (ξ≲2, tePEPO 2512.01781's own admission) → Loop (ξ~5, 1906.04085) →
  **NTU (ξ~20, O(D⁸) fully-parallel, Hermitian non-neg metric — Dziarmaga 2107.06635, THE engine
  default; validated on mixed-state iPEPO)** → GTU (ξ~30, 2205.11067) →
  FET/WTG (mixed-state gold standard — Mc Keever 2012.12233, read-before-build).
  Notes: `dziarmaga_ntu_truncation_2107.06635.md`, `dziarmaga_gtu_truncation_2205.11067.md`,
  `zheng_yang_loop_update_1906.04085.md`, `mc_keever_stable_ipepo_fet_wtg_2012.12233.md`.
- **Stability (engine-build gates):** Kilda 2012.03095 (`kilda_ipepo_stability_2012.03095.md`) —
  SU-iPEPO can be UNSTABLE near dissipative critical points; increasing D can DESTABILIZE
  (D=12 works / D=14 fails). Mitigations: strong dissipation stabilizes; FET; NEVER certify by
  D-sweep alone. Our regime (per-round Lueders measurement = strong per-round decoherence) is the
  SAFE zone (confirmed by ξ≤0.5).
- **The QEC-PEPO anchors:** Darmawan-Poulin 1607.06460 (density-matrix PEPO, 153q single-round,
  χ_b=8, single-layer Tr(ρΠ)); Manabe-Suzuki-Darmawan 2308.08186 (qutrit leakage MCWF-MPS, thin
  strip only — our reference carrier); Shao 2606.00474 (noise-reduces-complexity, purity-
  controlled max-OEE = the SATURATE mechanism, INTUITION not theorem for our regime).
- **1D wall evidence:** `outputs/teacher_prereg/p11_codestate_ordering.py` — 1D-MPS bond exponent
  →2.0 for all orderings (RCM buys a 2× constant); d5→2^10=1024, d7→2^14≈630 GB dead.
- **The memory/architecture literature** (leakage LRU + notion-2 boundary) is inventoried in
  `project-leakage-lru-const-memory-notion2shadow`.

---

## 5. Code + test inventory (this session — ALL UNCOMMITTED)

Every script: committed file + `_run.sh` runner + `_result.json` + `logs/*.log`; scripted-
execution discipline (asserts, printed evidence, flush, `__main__` guard); GPU serial.

**PEPO feasibility (outputs/nonpauli_teacher/) — the three gates, all exit 0:**
- `pepo_feasibility_drho_vs_round_d3.py` — R-gate. (v2: `chi_for_eps` float32→float64 tail fix;
  the completed run's chi(1e-8) column is SUPERSEDED by the eps-map run.)
- `pepo_record_error_vs_eps_d3.py` — record-error↔ε map. (post-review: float64 tail chi, vacuity
  guard, split-projection memory fix.)
- `pepo_xi_correlation_length_d3.py` — ξ selector. (post-review: dynamic signal floor +
  distinct-distance guard, non-finite-xi verdict policy, CPU-offload arm scheduling, R=0 einsum
  anchor, lattice-unit distances, arms-differ guard.)

**OPT2-2 support (outputs/twin_validation/):**
- `opt2_2_d3_spread_check.py` — the G-D2-0 geometry precondition (worst d3 snake stab-spread=6≤8;
  d3 logical Z-type, log_supp_isx all-zero → terminal x_log dormant). Exit 0.
- `p2ii_effectsize_deriv.py` — **RETIRED**: the leakage-marginal ∂p/∂g_seep "#1" derivation from
  the abandoned P2-ii direction (memory=notion-2 superseded it; leakage marginal is memory-blind).
  Kept as a file; do NOT resume.

**Docs edited (docs/):**
- `twin_validation/batched_mps_backend_prereg.md` — OPT2-2 DESIGN build contract (§D2-1..D2-8) +
  red-team OUTCOMES (blockers 8→2→0). PARKED.
- `nonpauli_teacher/2d_peps_leakage_forward_DESIGN.md` — ✅ FEASIBILITY OUTCOMES header (the 3
  gates).

**Reused engine seams (src, UNCHANGED):** `carrier/exact/qutrit_dm.py`
(`within_cycle_dm_engine`/`apply_within_cycle_premeasure`/`project_stabilizer`/
`apply_within_cycle_postmeasure`); `forward/scalable/sv_sampler.py`
(`build_within_cycle_leak`/`marshal_within_cycle`); `mechanisms/qutrit_teachers.py`
(`calibrate_theta_for_wg_l1`); the p1c sequential-null pattern
(`outputs/twin_validation/p1c_full9q_record_bound.py`).

**Process record:** un-led-review-before-GPU-run is **5-for-5** on catching silent-wrong-answer
blockers this session: the float32 `torch.tensor(1-eps)` rounding (1-1e-8==1.0f → corrupted a
verdict branch), inf/nan-dropping verdict logic, floor-noise fake-ξ fits, a ~29 GiB VRAM peak on
the 32 GiB live-desktop card, and an identical-arms vacuous PASS. **Keep this discipline.**

---

## 6. NEXT STEPS — the d5/d7 plan

**Immediate:** write the **d5/d7 PEPO theory-first prereg** (task-tracked). It folds in: the 3
verified d3 gates + numbers; the gap-cut truncation rule; NTU-from-start (Dziarmaga); Kilda
engine gates (ε_Λ diagnostic + D=3..6 non-monotonicity sweep + independent-oracle cert, never
D-sweep alone); FET/WTG read-before-build; the two owned physics axes (LRU-const leakage +
notion-2 per-round-Pauli memory, latent bond-free); the multi-stabilizer CMI/G² symbolization
design decision; epistemic classes throughout.

**The validation ladder (DESIGN §7; no d7 claim until each rung passes):**
- **Rung 1 — PEPO engine @ d3** (a genuine NEW build; DESIGN §6 4-builder decomposition:
  codestate-PEPS / dynamics / boundary-MPS sampling / validation; quimb-2D or self-written NTU +
  boundary contraction). Gate: **{det,obs} == the exact-DM oracle** (today's numbers are the
  reference: bond 16, dp/bar≤0.017, the sequential-null marginals table) + Kilda ε_Λ + D=3..6
  sweep.
- **Rung 2 — d5 tile + two-arm cross-check.** PEPO@d5 vs the **1D fixed-χ arm** (OPT2-3;
  codestate floor χ≥512-1024) + sub-register DM tile oracle. Gate: **measure D_ρ(d5)/χ_b(d5)
  ≲ 2^d** (the extrapolation becomes measurement — the d7 go/no-go) + two-arm statistical
  equivalence z≤4.
- **Rung 3 — d7** only if rung 2 passes; else the honest FINDING "full d×d hits its own wall →
  thin 3×d strip is the feasible path" (a finding, not a failure).

**Disciplines (carry over):** theory-first before any mechanism/observable; predict-before-
measure with (a)/(b)/(c) classes; independent-oracle (non-TN exact DM) certification, never
TN-vs-TN; un-led review before every GPU run; GPU serial (live desktop, no concurrent jobs); src
changes commit-gated on explicit user confirmation; commit `docs/` + `outputs/` normally.

**Uncommitted state:** all §5 scripts + doc edits + 2 new memory files are UNCOMMITTED (no src
changes). A `docs/outputs` commit was offered and is pending user go-ahead.

---

## 7. Pointers

- Memory: `project-pepo-d3-feasibility-verified`, `project-leakage-lru-const-memory-notion2shadow`,
  `project-simulator-p0p4-plan-framing`, `project-fulld-1dmps-wall-and-2dpeps`,
  `project-cpdiv-notion-hierarchy-passive-record`, `feedback-scripted-execution`,
  `feedback-anti-toy-ground-truth-protocol`, `feedback-heavy-tasks-multi-agent`.
- Design: `docs/nonpauli_teacher/2d_peps_leakage_forward_DESIGN.md` (the PEPO engine design +
  today's FEASIBILITY OUTCOMES).
- Contract: `docs/twin_validation/batched_mps_backend_prereg.md` (OPT2-1 done / OPT2-2 parked /
  OPT2-3 = the d5 1D fixed-χ cross-check arm).
- Survey: `outputs/papers/pepo_survey/PEPO_COMPREHENSIVE_MAP.md`.
- Evidence: `outputs/nonpauli_teacher/pepo_*_d3_result.json` + `logs/pepo_*_d3.log`.
