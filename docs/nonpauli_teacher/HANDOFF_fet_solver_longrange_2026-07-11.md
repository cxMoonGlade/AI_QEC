# HANDOFF — FET truncator: joint bond grows = SOLVER unreliable on LONG-RANGE (loop) correlations; NEXT = Evenbly-2018 closed-loop gauge-fix (2026-07-11)

> ## ★ 60-second brief
> - The single-wire 2D PEPS carrier is FEASIBLE (crux resolved earlier: bond growth =
>   truncation-gauge over-count; physical `S_A` bounded 2–4 ebits). We BUILT the Stage-2
>   environment-optimal (FET) truncator as a `fet_env` truncation mode
>   (`src/error_coupling_simulator/carrier/peps/fet.py` + `trajectory.py`). Unit gates 34/34.
> - **WP1' (the real joint test): the joint per-edge bond GROWS 6→12→15** under a single-sweep
>   per-stab `fet_env` truncation, while `S_A == GF(2) == 2.0` EXACT. A bounded-bond rep
>   provably exists (bounded `S_A`), so the truncator is failing to find it.
> - **ROOT (found this session): the FET SOLVER is unreliable.** A `fid(χ)`-curve probe showed
>   the achieved environment fidelity `Fid_Γ(χ)` is NON-MONOTONE (drops with more χ) and/or
>   PLATEAUS below 1 on the "dressed" bonds — the ALS gets stuck. This is a KNOWN FET pathology
>   (McKeever/NTU: an approximate NON-Hermitian/non-PSD metric → ill-conditioned `pinv(B)` →
>   crashes; the exact metric MUST be Hermitian-PSD to machine precision).
> - **A theory-fix (this session) applied 4 numerical fixes to `fet.py`** (Hermitize+PSD Γ,
>   regularized Hermitian pinv, clamp `fid≤1`, never-keep-full-bond). **Effect: max_bond went
>   12→36 down to 4→8 — a big improvement — but the ALS STILL fails on the most
>   long-range-correlated bonds** (`fid(χ=bare)` = 0.86 / 0.30 on some).
> - **USER STEER: "主要是修复长程关联" (the core is fixing the LONG-RANGE correlations).** The
>   residual failures are exactly the loop-carried long-range correlations the local ALS cannot
>   reliably remove. **NEXT = close the Evenbly-2018 "closed loops" gap and use its DETERMINISTIC
>   gauge-fixed canonical-spectrum (WTG) truncation as the PRIMARY**, replacing the unreliable ALS.
> - **NOTHING is committed** (src changes need explicit user confirmation). The `fet.py` edits +
>   an env-gated debug are in the working tree, uncommitted.

---

## 1. WHAT WE DID THIS SESSION (work log, 2026-07-11)

Starting point (prior session): the crux was RESOLVED — the single-wire 2D PEPS per-edge bond
growth is a truncation-GAUGE artifact (`S_A` bounded, (a)-exact d3/d5); the fix is an
environment-optimal (FET) truncator. Entry doc was `HANDOFF_crux_resolved_next_FET_2026-07-11.md`.

1. **FET Stage-1 diagnostic** (`outputs/nonpauli_teacher/fet_stage1_env_truncation.py`, contract
   `fet_stage1_design_pin_2026-07-11.md`): confirmed Γ-independently that a single grown bond
   collapses under the exact single-edge environment with the state EXACTLY preserved
   (B4_6 dim16→env_rank1, overlap 1.0, `S_A==GF(2)` to 1e-15). CONCEPT VALIDATED. Then realized
   the INSTRUMENT was too weak: single-edge env_rank is trivially ~1 for EVERY edge (loop
   redundancy) — the real feasibility question is the JOINT/sequential bond across rounds.

2. **Stage-2a src BUILT** via `contract-build` (contract `fet_stage2_src_contract_2026-07-11.md`,
   1 red-team round → F1 `_policy_precut`-crash blocker + F2 per-bond-sequential-not-independent +
   F4 GOLD-faithfulness, all fixed): a NEW `TruncationPolicy("fet_env", eps_fid=1e-8)` mode.
   `fet.py` (~380L, FET solver lifted from the Stage-1 diagnostic) + `trajectory.py` wiring
   (`_policy_precut` NO-OP + `_policy_cut` per-bond-SEQUENTIAL branch). **Unit gates 34/34:**
   existing 28/28 BYTE-IDENTICAL + 6 fet_env (G-ANTICIRC `Γ_TN==Γ_dense` + `Fid_Γ==fid_dense`;
   G-SA-CORROB `S_A==GF(2)`; wiring no-crash + `_policy_precut` no-op; full-rank losslessness).

3. **WP1' joint test** (`outputs/nonpauli_teacher/fet_stage2_wp1_run.py`, leak-off R=12, EXACT
   route): **max_bond GROWS 6→12→15** (hung at R4 as bonds explode `gamma_TN` cost), `S_A=2.0`
   exact every round. ⇒ single-sweep per-stab `fet_env` does NOT bound the joint bond.
   (Verdict reframed to bounded-through-R12 / growing-through-R12 / inconclusive; S_A-gated.)

4. **Drift-hunt** (`wf_cd391476`, tn_qsim `general_tn.py`/`pepdo.py`/`utils.py` vs `fet.py`, 4
   components + synthesis): Γ construction / ALS-core einsums / write-back mechanics ALL FAITHFUL
   (no drift). The named drift = rank-selection POLICY (tn_qsim truncates to a FIXED target dim 4
   and accepts the residual; ours = smallest χ with `Fid_Γ≥1−1e-8` + RT-F5-keep-full).

5. **`fid(χ)`-curve probe** (`outputs/nonpauli_teacher/fet_fidcurve_probe.py` +
   env-gated `FET_FIDCURVE_DEBUG` in `fet.env_optimal_rank`, behavior-identical): REFINED /
   partly OVERTURNED the synthesis. The real root is a **SOLVER FAILURE**: `Fid_Γ(χ)` is
   NON-MONOTONE (e.g. B1_3 D=6 bare=4 → `[0.96,0.32,0.14,0.14]`; χ=bare should be lossless=1 but
   gave 0.14) and/or PLATEAUS below 1−1e-8 → `accept=None` → RT-F5 kept the FULL bond (D up to 36)
   → growth. `Fid_Γ` slightly >1 ⇒ Γ not cleanly PSD. **"先证再改" caught that the synthesis's
   one-line policy fix would have FAILED** (it would accept `fid=0.14` garbage = corrupt the state).

6. **theory-fix** (skill; literature-closure loop, RAG + reading notes): grounded the FET
   algorithm. FINDINGS: (i) my ALS core IS the reference FET (gen-eig `R_m = B⁻¹P`, alternating);
   (ii) **the metric MUST be Hermitian-PSD** — NTU (Dziarmaga 2107.06635): the exact cluster
   metric `g` is "Hermitian and non-negative down to machine precision", and its exactness is the
   central stability advantage; the approximate NON-Hermitian FTU/FU metric causes "sudden
   crashes" — MY BUG; (iii) `pinv` stability = truncated-SVD / dynamic tolerance (McKeever+NTU);
   (iv) balanced `S^{1/2}` absorption; (v) "cut to fixed dim, accept residual" IS the reference
   method, faithful (discards internal correlations = no physical info; `S_A=2.0` certifies);
   (vi) FET is DESIGNED to remove internal correlations (McKeever, `S_cycle`). **Trip-wire #5
   fired: the growth is the LENS (immature non-PSD-metric implementation), NOT intrinsic physics.**
   **Applied 4 fixes to `fet.py`:** (1) `_hermitize_psd(Γ)` in `gamma_TN`, (2) regularized
   Hermitian pinv in `_als_inner` (both sites), (3) clamp `fid≤1` in `gamma_fidelity`, (4)
   `env_optimal_rank` accepts the BEST χ≤bare instead of RT-F5-keeping the full bond.

7. **Re-probe** (`fet_fidcurve_probe` after the fix): **max_bond 12→36 became 4→8** (big win;
   χ=bare now lossless on most bonds), BUT the ALS STILL fails on some dressed bonds
   (B0_2 `[0.94,0.019,0.007,1.0]` non-monotone; B1_3 r2 plateau `fid(χ=4)=0.86`; B3_6 r2 best 0.30).
   On those the accept-best fallback bounds the bond but takes a LOSSY truncation (would corrupt
   `S_A`) — a bad safety; the solver must be fixed properly.

8. **USER STEER: "主要是修复长程关联".** The residual-failure bonds are exactly the ones carrying
   strong LONG-RANGE (loop) correlations, where the local single-bond ALS is a non-convex problem
   it cannot reliably solve. The literature answer is **Evenbly 2018 [68] "Gauge fixing, canonical
   forms, and optimal truncations in tensor networks with CLOSED LOOPS" (PRB 98, 085155)** — the
   DETERMINISTIC closed-loop gauge-fix (WTG) + canonical-spectrum truncation. I had UNDER-weighted
   this as a non-load-bearing lit-gap in the theory-fix; the user's steer shows the closed-loop /
   long-range handling IS the load-bearing part.

## 2. CURRENT CODE STATE (all UNCOMMITTED — do NOT assume committed)

- `src/error_coupling_simulator/carrier/peps/fet.py` — the FET solver; has the 4 theory-fix edits
  (`_hermitize_psd`, regularized Hermitian pinv ×2, `fid≤1` clamp, accept-best) + the env-gated
  `FET_FIDCURVE_DEBUG` block in `env_optimal_rank` (behavior-identical; remove or keep as a tool).
  **py_compile clean.** The fix is PARTIAL (see §1.7).
- `src/…/carrier/peps/trajectory.py` — `fet_env` mode (`TruncationPolicy.eps_fid`, `_policy_precut`
  no-op, `_policy_cut` sequential branch) + a PRE-EXISTING `PEPS_SW8_TRIAGE` block (was `M` at
  session start, from a prior session — split into its OWN commit).
- **⚠ KNOWN ISSUE not yet resolved:** `_hermitize_psd` is currently INSIDE `gamma_TN`, so `gamma_TN`
  no longer returns the raw exact contraction — this may BREAK the `G-ANTICIRC` unit test
  (`Γ_TN == Γ_dense`, tol 1e-9; the Hermitization changes Γ by up to ~1e-6 since the >1 fids show
  Γ was non-PSD at that level). **NOT re-run since the edit.** Fix: MOVE `_hermitize_psd` to the
  SOLVER side (call it once at the top of `env_optimal_rank` on `gamma_TN`'s output), keep
  `gamma_TN` raw for `G-ANTICIRC`; OR update the `G-ANTICIRC` test. Then re-run `test_peps_fet.py`.
- Contracts/pins: `docs/nonpauli_teacher/fet_stage2_src_contract_2026-07-11.md`,
  `fet_stage1_design_pin_2026-07-11.md` (v3/v4).
- Diagnostics (`outputs/nonpauli_teacher/`, gitignored local evidence): `fet_fidcurve_probe.py`
  (+`_run.sh`, +`.log` = the fid-curve data), `fet_stage2_wp1_run.py` (+`_run.sh`, the WP1' driver),
  `fet_stage1_env_truncation.py` (the Stage-1 diagnostic the solver was lifted from).

## 3. WHAT TO READ (docs / literature / source)

**Handoffs + contracts (read first):**
- THIS file + `HANDOFF_crux_resolved_next_FET_2026-07-11.md` (the crux resolution).
- `fet_stage2_src_contract_2026-07-11.md` (§3 the two-pass seam; §5 gates), `fet_stage1_design_pin_2026-07-11.md`.

**Literature (the load-bearing gap + the closed reading notes):**
- **★ Evenbly 2018, PRB 98, 085155 — "Gauge fixing, canonical forms, and optimal truncations in
  tensor networks with closed loops"** — THE gap to CLOSE (front-half theory-first: find →
  download → convert → 精读 → write `docs/papers/reading_notes/evenbly_gauge_closed_loops_...md`).
  The DETERMINISTIC closed-loop gauge-fix (WTG), canonical form, cycle entropy, optimal single-bond
  truncation for LOOPY / long-range-correlated networks. NOT yet read; no reading note.
- Reading notes ALREADY in `docs/papers/reading_notes/` (used this session):
  - `mc_keever_stable_ipepo_fet_wtg_2012.12233.md` — FET+WTG (mixed-state, adapts Evenbly). The
    gen-eig `R_m = B⁻¹P`, alternating sweeps, "FET removes internal correlations", `S_cycle`,
    stability = truncated-SVD / dynamic pinv tolerance. (`Method (deep)` + `The MECHANISM`.)
  - `dziarmaga_ntu_truncation_2107.06635.md` — NTU: exact metric `g` Hermitian+PSD to machine
    precision is the "central advantage"; FTU non-Hermitian metric → crashes. The balanced
    `S^{1/2}` absorption + per-side "tilt" gauge (Fig. 5). This is the theory root of our bug.
  - `dziarmaga_gtu_truncation_2205.11067.md` — GTU (tangent-space overlap-per-site, beyond local).
  - `rudolph_tindall_gpu_peps_2507.11424.md` — BP simple update in the Vidal gauge; factorizable
    BP-message environment for loops (the belief-propagation / loop-corrected alternative).
  - Manabe `manabe_suzuki_darmawan_leakage_tn_2308.08186.md` (1D-MPS + FET-on-PEPDO reference).
- RAG: `/home/cx/miniconda3/envs/aiqec/bin/python -m qec_twin.rag.store --query "<q>"` (2230 chunks).
  KG: `outputs/knowledge_graph/kg_query.py`. Index: `docs/papers/CONCEPT_INDEX.md`.

**Reference CODE (Manabe's actual FET — READ-ONLY):** `external/reference_repos/tn_qsim/tn_qsim/`
- `general_tn.py`: `find_optimal_truncation_by_Gamma` (L569, the ALS), `fix_gauge_and_find_optimal_truncation_by_Gamma` (L804, the gauge-fix + gen-eig).
- `pepdo.py`: `prepare_Gamma` (L926), `find_optimal_truncation` (L992, the driver — fixed target dim 4).
- `utils.py`: `fix_gauge` (the WTG gauge — note the DEGENERACY SUM our `_fix_gauge` drops),
  `calc_optimal_truncation` / `execute_optimal_truncation` (multi-restart + 10× restart loop).
- Driver: `surface_opt_trun.py` (calls `find_optimal_truncation(node, edge, 4)`).

**Our SOURCE (the file to fix):** `src/error_coupling_simulator/carrier/peps/fet.py`
- `gamma_TN` (the exact env Γ + `_hermitize_psd`), `gamma_fidelity`, `_als_inner` (the unreliable
  ALS — the thing to replace), `_fix_gauge` (the gauge — drops degeneracy, argmax not sum),
  `fet_m2` (the closed-form gauge-fix top-χ — currently only a SEED; should become PRIMARY),
  `build_seeds`, `fet_m1` (multi-restart best-of), `apply_fet_truncation` (write-back),
  `env_optimal_rank` (the rank wrapper + the env-gated `FET_FIDCURVE_DEBUG` block).
- `trajectory.py`: `_policy_cut` / `_policy_precut` `fet_env` branches; `TruncationPolicy`.

## 4. NEXT-STEP PLAN

1. **Close the Evenbly-2018 gap (theory-first front-half).** Find/download/convert/精读 PRB 98,
   085155 → reading note. Extract: the closed-loop GAUGE-FIX algorithm (WTG), how the canonical
   form is defined for a cyclic/loopy bond, the cycle-entropy `S_cycle`, and the DETERMINISTIC
   optimal single-bond truncation (canonical-spectrum top-χ) vs the alternating ALS.

2. **Replace the unreliable ALS with the DETERMINISTIC gauge-fixed canonical-spectrum truncation
   as the PRIMARY** (`fet.py`). The gauge-fix + generalized-eigenvalue / canonical spectrum gives
   the GLOBAL optimum (monotone in χ, no non-convex ALS stall) and directly REMOVES the long-range
   (loop) redundancy. Fix `_fix_gauge`'s DEGENERACY handling (S_A=2 ⇒ 4-fold degenerate transfer
   eigenvalue; sum the degenerate eigenspace like `utils.fix_gauge`, not one argmax). Keep the ALS
   only as an optional refinement/fallback.

3. **DIAGNOSE the plateau bonds with the canonical spectrum.** For a bond where `fid(χ=bare)<1`,
   read its gauge-fixed canonical (WTG) spectrum: if it has ~4 large + a fp tail ⇒ rank-4 IS
   lossless and the ALS was just failing (the deterministic truncation fixes it). If it has a
   genuine long tail ⇒ that edge GENUINELY carries long-range correlations needing rank>4 (a
   physical fact — the single-wire per-edge bound may exceed `S_A` but should still be area-law
   bounded). This settles "solver failure vs genuine long-range physics" per bond.

4. **Remove the accept-best-on-garbage safety** (it bounds the bond by taking a LOSSY truncation
   that corrupts `S_A`). With the reliable deterministic solver, `fid(physical-rank)≈1`, so no
   lossy accept is needed. Keep "cut to physical rank, accept the fp/loop residual" (the reference
   method) — but verify the residual is fp/loop (S_cycle), not physical (S_A).

5. **Fix the `_hermitize_psd` placement** (move to `env_optimal_rank` / solver-side so `gamma_TN`
   stays the raw exact metric for `G-ANTICIRC`; or update the test). Re-run `test_peps_fet.py`
   (expect 6/6) + `test_peps_spike.py` (28/28 byte-identical).

6. **Re-probe `fid(χ)`** (predict: MONOTONE, `fid(χ=bare)=1` on every bond) + check `S_A==GF(2)`
   per round (predict: 2.0). Then **re-run WP1'** (`fet_stage2_wp1_run.py`) — predict:
   `max_bond` BOUNDED ~4 and flat across rounds, `S_A=2.0`. A miss is a FINDING (register the
   epistemic class before the run).

7. If per-round single-sweep with the reliable solver STILL doesn't bound it → escalate to the
   iterative multi-sweep (Stage-1 §0 outcome 2) OR the BP/loop-corrected environment
   (rudolph_tindall) — but this is the last resort; the deterministic gauge-fix should suffice.

**KEY OPEN QUESTION (what the canonical-spectrum diagnosis answers):** are the plateau bonds a
SOLVER failure (fixable) or GENUINE long-range physics (the loopy edge needs rank>4)? Do NOT
build a bound/No-Go conclusion before this is settled by the WTG spectrum.

## 5. DISCIPLINE / ENV (do not re-learn the hard way)

- **theory-fix / theory-first** before committing to an algorithm change; predict-before-measure
  with epistemic classes; a miss is a FINDING. **Faithfulness: independent GT** = the GF(2)
  stabilizer entropy (Clifford) + `dense_psi` `S_A` — never check Γ against itself.
- **src commits need EXPLICIT user confirmation; one reviewed diff per phase; NO co-author.** The
  pre-existing `PEPS_SW8_TRIAGE` block is a SEPARATE commit.
- **Scripted-execution:** every code run = a committed script (asserts + printed evidence + flush +
  `__main__` guard). The `fid(χ)` probe (`FET_FIDCURVE_DEBUG` env-gated) is the diagnostic tool.
- **GPU:** RTX 5090, GPU-only, SERIALIZE (user's live desktop, no concurrent GPU). Kill cleanly
  (`nvidia-smi --query-compute-apps` to confirm no orphan). d3 fet_env is SLOW (per-bond `auto-hq`
  `gamma_TN`); the debug computes all χ so it is slower still.
- **Env:** WSL python `/home/cx/miniconda3/envs/aiqec/bin/python`. Invoke via
  `wsl -d ubuntu-f -- bash -c 'cd /home/cx/Document/AI_QEC/AI_QEC && <cmd>'`. **TRAP: `$VAR` inside
  a `bash -c "…"` string gets PRE-EXPANDED to empty by the outer Git Bash — use LITERAL strings or
  a committed `.sh`** (vars work inside a real `.sh`). Capture the real python exit with
  `${PIPESTATUS[0]}` in the runner.
- **Chat in Chinese; docs/code/commits in English.** Communicate first; don't churn files.
- Reference the READ-ONLY tn_qsim FET impl; do NOT edit `external/`.

## 6. POINTERS
- **★ THIS = the entry point.** Detail memory: `project-peps-spike-build-state.md` (top block).
- Contracts: `fet_stage2_src_contract_2026-07-11.md`, `fet_stage1_design_pin_2026-07-11.md`.
- The file to fix: `src/error_coupling_simulator/carrier/peps/fet.py`. Reference: `external/reference_repos/tn_qsim`.
- The lit gap to close: Evenbly 2018 PRB 98, 085155 (closed-loop gauge fixing / WTG / optimal truncation).
