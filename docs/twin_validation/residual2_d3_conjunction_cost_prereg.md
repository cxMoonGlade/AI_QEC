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
XZZX r01 geometry, physical cell (theta from `calibrate_theta_for_wg_l1(WG_L1=5e-3)`, g_seep=0.09, b=0.9, arm=A),
N=1024 shots, R=schedule default, c128. Plus an MPS spot-check (`MpsLeakageForward.sample`, hard2, N=8).
- **P-C1a (b, wide band DECLARED):** SV-kernel throughput in [10, 10^4] shots/min. No committed cost anchor exists
  for the kernel path (the 0.27 s/manifest figure is the QUBIT dense path — different machinery); the band is wide
  and class (c) on width. Outside band either way = finding (envelope "usable" claim re-scored).
- **P-C1b (b):** MPS 1–4 s/shot (anchor: `tests/test_soft_readout.py:10` ~2 s/shot comment).
- **P-C1c (a-ish):** VRAM: SV state 315 KB/shot·block (loader docstring) ⇒ N=1024 ≪ 1 GiB total; assert < 4 GiB.

**C2 — exact qutrit-DM oracle at full d3 register (the "oracle-bounded at d3" leg).**
Entry: `QutritDM` syndrome/record law at full 9 data qutrits, R=1, DETECTOR_MARG-style statistic (2 live DM copies —
the declared-feasible cell, `certify/anchors/dm_oracle.py:82-142`), WG leakage Kraus injected
(`leakage_kraus_torch`), same physical cell as C1.
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

## Script skeleton (scripted-execution discipline)
One committed script, content_hash + git head + versions printed; per-arm timings/VRAM via
`torch.cuda.max_memory_allocated`; preconditions: CUDA present, no other GPU job (user-confirmed), r01 dataset paths
resolve; results json `outputs/twin_validation/residual2_d3_conjunction_cost_result.json`; GATE name
`RESIDUAL2_ENVELOPE_D3`. Estimated total GPU time: C1 ≈ minutes, C2 ≤ 45 min cap, C3 ≈ minutes.
