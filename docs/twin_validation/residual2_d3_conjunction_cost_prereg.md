# Residual check ② — d3 conjunction cost/envelope confirmatory run (PRE-REGISTRATION, 2026-07-06)

**Claim under test** (due-diligence ② envelope, `conjunction_ownership_duediligence_2026-07-06.md`): *the conjunction
is deliverable + USABLE at d3 — the leakage-qutrit carrier generates records at usable cost, the exact qutrit-DM
oracle fits the card as declared (3^9 one copy 5.77 GiB; DETECTOR_MARG R=1 full-9q ≈ 12.4 GB feasible), and the
classical couplings (non-Markov temporal + shared-latent Θ) add ~zero state-space/runtime cost.* This run validates
the COST/feasibility numbers empirically. It is NOT the P2 conjunction wiring: per-round leakage modulation today has
exactly ONE seam (the caller-driven `apply_within_cycle_round` DM loop, `sv_sampler.py:1021,1042`); the SV kernel and
MPS carriers take a static Kraus stack per run (`sv_sampler.py:774-789`) — wiring Θ→leakage into the carriers is P2
src work, out of scope here.

**Status discipline:** all outcomes below are cost/feasibility evidence (class (b)/(c)); a prediction miss is a
FINDING against the envelope, never silently absorbed. GPU serial (live desktop), single script, committed under
`outputs/twin_validation/residual2_d3_conjunction_cost.py` + runner; requires a separate user GPU go-ahead.

## Arms + registered predictions (BEFORE the run)

**C1 — d3 leakage-carrier generation cost (the "usable" leg).**
Entry: `SvSampler(device='cuda') + RunSpec → sample()` (`sv_sampler.py:1238`, lumped kernel `sv_traj_d3`), shipped d3
XZZX r01 geometry, composite project fixture (theta from `calibrate_theta_for_wg_l1(WG_L1=5e-3)`, g_seep=0.09, unsupported project b=0.9, arm=A),
N=1024 shots, R=schedule default, c128. Plus an MPS spot-check (`MpsLeakageForward.sample`, hard2, N=8).
- **P-C1a (b, wide band DECLARED):** SV-kernel throughput in [10, 10^4] shots/min. No committed cost anchor exists
  for the kernel path (the 0.27 s/manifest figure is the QUBIT dense path — different machinery); the band is wide
  and class (c) on width. Outside band either way = finding (envelope "usable" claim re-scored).
- **P-C1b (b):** MPS 1–4 s/shot (anchor: `tests/test_soft_readout.py:10` ~2 s/shot comment).
- **P-C1c (a-ish):** VRAM: SV state 315 KB/shot·block (loader docstring) ⇒ N=1024 ≪ 1 GiB total; assert < 4 GiB.

**C2 — exact qutrit-DM oracle at full d3 register (the "oracle-bounded at d3" leg).**
Entry: `QutritDM` syndrome/record law at full 9 data qutrits, R=1, DETECTOR_MARG-style statistic (2 live DM copies —
the declared-feasible cell, `certify/anchors/dm_oracle.py:82-142`), WG leakage Kraus injected
(`leakage_kraus_torch`), same composite fixture as C1.
- **P-C2a (b):** peak device memory in [11.5, 15] GiB (2 × 5.77 GiB + workspace).
- **P-C2b (b, coarse band DECLARED):** wall-clock in [1, 30] min. Hard timeout 45 min in-script; timeout = FINDING
  ("oracle-bounded at d3" becomes sub-register-only, envelope re-worded).
- **P-C2c (c):** R=2 full-9q NOT attempted (declared infeasible ~100 GB — we do not test the declared wall by OOMing
  the user's desktop; the small-register R≥2 route is C3's).

**C3 — "classical couplings are free" (the conjunction-marginal-cost leg).**
Entry: caller-driven per-round DM loop (`apply_within_cycle_round`) on the n=5 sub-register of the real r01 XZZX
geometry (precedent: `tests/test_qutrit_dm_exact.py:285-324`), R=3. Two timed variants, identical except: (i)
constant leak params; (ii) per-round-varied params g_seep(r)=g_seep·(1+0.3·x_r), x_r a seeded RTN draw
(`RTNSource`) — an AD-HOC class-(c) modulation for the COST probe only (Θ→leakage is NOT a registered physics map;
the physics wiring is P2).
- **P-C3a (b):** cost ratio varied/constant ∈ [0.95, 1.15] (per-round Kraus rebuild = exp of a 9×9-superop-scale
  object, negligible vs 3^5-DM round evolution).
- **P-C3b (b):** standalone per-round Kraus rebuild < 10 ms.
- **P-C3c (a, sanity):** varied-params run changes the round syndrome distribution (liveness positive control — the
  modulation must not be silently dead plumbing).

**C4 — carrier-vs-oracle agreement tile: NO new run.** Existing precedents already bound this leg (cite, don't
re-run): zero-leakage identity < 1e-12 (`test_qutrit_dm_exact.py:222-282`), W-B dense-oracle STRICT 1-F_e ≤ 1e-6 /
record TV ≤ 1e-6 at window dim ≤ 256 (`axis1_mcwf_dense_certification.py`), one/two-site leakage lowering vs
hand-typed references ≤ 2e-12 (`axis1_qutrit_leakage_certification.py`). The full-suite pass (in flight) is the
freshness evidence.

## Verdict rule (registered)
Envelope ② is CONFIRMED iff: C1 generates 1024 d3 records within its band (or faster) AND C2 completes within
timeout at declared memory AND C3 confirms free coupling (ratio in band + liveness). Any single miss ⇒ the
due-diligence ② table is edited to the measured numbers (finding, not failure of the run) and the P2 plan re-costed.

## AMENDMENT v2 (2026-07-06, BEFORE the first run — pre-run adversarial review findings)
A single un-led reviewer verified the script against the engine sources and found the original C2 plan unsafe and two
evidence-corrupting mismatches. Registered corrections (the ORIGINAL bands above stay registered; their misses are
findings):
- **C2 is STAGED (the run-blocker fix).** The reviewer's allocation analysis: `QutritDM.apply_channel` (einsum
  temporaries) + `hermitianize` hold ~5 live full-DM copies during X-support rotations ⇒ true full-9q peak ≈ 23–29
  GiB, NOT the 2×5.77 GiB the `dm_oracle.py` capability gate declares — **the original P-C2a band [11.5, 15] GiB is
  arithmetically unreachable, and its miss is itself the finding that `dm_oracle`'s 2-copy estimate undercounts.**
  Staged protocol: (A) measure the empirical peak/copy multiplier `k_n` on n=7 and n=8 sub-registers (copies 0.077 /
  0.69 GiB ⇒ peaks ≤ ~3.5 GiB, safe); **P-C2d (b): k ∈ [3, 6]**. (B) attempt full-9q ONLY if `k_max × 5.77 GiB ≤ 24
  GiB`, under `torch.cuda.set_per_process_memory_fraction(0.8)` with `OutOfMemoryError` caught as data (desktop
  protected either way); skip-or-OOM = FINDING (full-9q DETECTOR_MARG infeasible at the true multiplier ⇒
  due-diligence ② and the `dm_oracle` capability gate both need correcting — flagged for a later src fix).
- **C1a: kernel JIT warmup excluded from the timed region** (an N=1 warmup sample precedes t0); throughput measured
  at BOTH R=schedule-default (the originally registered cell) and R=4 (the P0-comparable cell), reported as shots/min
  + shots·rounds/min. Both band edges now flag findings (the original "outside band either way" reading governs).
- **C3's round body is a DECLARED PROXY** (5× single-site `apply_channel`, no within-cycle stream replay/measurement)
  — smaller denominator than the registered `apply_within_cycle_round` seam, i.e. CONSERVATIVE AGAINST the
  free-coupling claim (rebuild overhead is a larger fraction of a cheaper round). Ratio band unchanged; reps
  interleaved (const/varied alternating) against clock drift; x_r drawn from `RTNSource` signs as originally named.
- Minor evidence fixes: per-arm incremental JSON dumps; `r10` metadata in the precondition gate; `n_stab` derived
  from the parsed schedule; C2 phase timestamps synchronized. Reviewer cost note (registered expectation): C2 wall
  likely UNDER the [1, 30] min lower edge — trips as a registered miss/finding, not a bug.

## Script skeleton (scripted-execution discipline)
One committed script, content_hash + git head + versions printed; per-arm timings/VRAM via
`torch.cuda.max_memory_allocated`; preconditions: CUDA present, no other GPU job (user-confirmed), r01 dataset paths
resolve; results json `outputs/twin_validation/residual2_d3_conjunction_cost_result.json`; GATE name
`RESIDUAL2_ENVELOPE_D3`. Estimated total GPU time: C1 ≈ minutes, C2 ≤ 45 min cap, C3 ≈ minutes.

---

## OUTCOMES (2026-07-06 run — GATE: FINDINGS; exit 0, no crash/OOM/timeout)
Script content_hash `1a27513f…13012a`, git `8bfa21c`, log `outputs/twin_validation/logs/residual2_d3_conjunction_cost.log`,
RTX 5090 31.8 GiB, torch 2.12.0+cu130. Registered-prediction scorecard:
- **P-C1a MISS (fast direction ×5):** SV kernel **51,363 shots/min** at R=1 / 44,913 at R=4 (179,652 shot-rounds/min);
  JIT warmup 40.4 s excluded as amended. "Usable generation" holds overwhelmingly.
- **P-C1c MISS:** C1a VRAM peak **17.35 GiB** (both R cells; ≈ 3 × the 5.77 GiB DM copy) — the `sample()` host path
  (codestate build) transiently materializes DM-scale temporaries although `build_codestate`'s docstring claims
  "no DM ever materialized at full scale". Doc-vs-reality gap; flagged with the dm_oracle item below.
- **P-C1b MISS (fast):** MPS **0.98 s/shot** at exact χ=243 (anchor said ~2 s/shot).
- **P-C3a MISS, cause understood & registered in v2:** ratio **2.053** — the declared PROXY round is so cheap
  (2.09 ms) that the 0.63 ms/round Kraus rebuild doubles it (the v2 amendment predicted the proxy is conservative
  against the claim). The ABSOLUTE numbers carry the envelope conclusion: **P-C3b PASS (rebuild 0.63 ms < 10 ms)**,
  **P-C3c PASS (liveness 4.76e-4 > 1e-12)**; rebuild is ~1e-3 relative to a real carrier round (SV batch-round
  ~0.3 s; DM n=8 round 0.6 s) ⇒ **parameter-modulated coupling is free where it matters**. Caveat recorded: the
  seeded RTN draw came out all-same-sign ([0.063]×3), so within-trajectory round-to-round variation was absent this
  draw; the rebuild-per-round cost (the measured quantity) executed regardless.
- **P-C2d PASS:** empirical peak/copy multiplier **k = 5.44 (n=7) / 5.05 (n=8)** — squarely in the registered [3, 6]
  band and matching the review's ~5-live-copy allocation analysis.
- **P-C2e / P-C2a:** full-9q attempt **SKIPPED by the staged gate** (projected k_max × 5.77 = **31.4 GiB > 24 GiB
  budget**). ⇒ THE load-bearing finding: **full-9q DETECTOR_MARG R=1 is NOT feasible on a 32 GiB card at the true
  multiplier; `dm_oracle.py`'s 2-copy capability estimate (≈11.5 GiB) undercounts by ~2.7×.** The sub-register DM
  oracle is fast and cheap (n=8: 0.6 s, 3.24 GiB peak) — the certify DM-for-anchor / carrier-for-scale split already
  accommodates this; the capability gate + (possibly) an in-place/chunked apply path need a src fix (flagged as a
  separate task).

**Envelope verdict after ② (superseded same day — see POST-FIX below):** d3 generation usable at ~5×10⁴ shots/min
(SV) / ~1 s/shot (MPS exact-χ); coupling parameterization free in absolute terms; the exact-DM oracle leg was
**sub-register (n ≤ 8)** at the pre-fix multiplier.

## POST-FIX RE-RUN (2026-07-06, same day — after the memory-lean QutritDM apply path landed)
The k≈5 finding was root-caused (apply_channel einsum temporaries + out-of-place hermitianize + dense
`embed_operator_q` vector ops + eager constructor DM) and fixed (chunked apply into a preallocated output above
`_CHUNK_MIN_DIM`, blockwise in-place hermitianize, local-contraction vector ops, lazy rho; 62-test falsifier suite +
review panel, 13 findings fixed). Same probe script re-run (git `85c2c63`, log
`outputs/twin_validation/logs/residual2_d3_conjunction_cost.log`):
- **C2 stage B UNLOCKED and PASSED: full-9q exact-DM DETECTOR_MARG R=1 DEMONSTRATED — peak 18.92 GiB, wall 0.18 min
  (~11 s)** on the 32 GB card (alloc-fraction 0.8 guard; stage-A k = 3.74/3.32 at n=7/8, projected 21.6 ≤ 24 GiB).
  The original P-C2a [11.5, 15] GiB band (2-copy-based) still missed — the honest full-9q number is ~19 GiB ≈ 3.3
  copies; the `dm_oracle` capability now declares a conservative 4×copy ≈ 24.8 GiB with an explicit
  `dm_safety` opt-in for this card (default stays conservative).
- **C1a side effect: 670,839 shots/min at R=1 (13× the pre-fix run) at 0.63 GiB VRAM (was 17.35)** — the codestate
  build no longer materializes dense DM-scale embeds (time AND memory were the same three tensors).
- C1b MPS 0.81 s/shot; C3 ratio 1.23 under unconditional chunking → the small-DM fast path (`_CHUNK_MIN_DIM`) was
  added the same day (n=5 proxy round restored to the single-contraction path; both branches equivalence-gated).
- **Final envelope (due-diligence ② updated): d3 = exact carrier at ~10⁵–10⁶ shot-rounds/min + full-register exact-DM
  oracle at ~19 GiB/11 s (deliberate-budget), sub-register oracle ms-scale; coupling parameterization free.**
