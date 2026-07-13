# SUPERSEDED HANDOFF — earlier PEPS crux resolution reopened (2026-07-11; reopened 2026-07-13)

> **DO NOT BUILD ON THE STRONG VERDICT BELOW.** Exact checks established bounded `S_A` in the
> tested cuts, but they did not establish that all bond growth is gauge, that a small
> record-faithful bond exists, or that FET preserves the full QEC record/rare LER. Those bridges are
> open after literature closure. The current boundary is
> [`coherent_leakage_longrange_truncation_literature_closure_2026-07-13.md`](coherent_leakage_longrange_truncation_literature_closure_2026-07-13.md)
> and ADR 0011. The text below is retained as historical provenance.

> ## ★ READ THIS FIRST (the 60-second brief)
> - **The crux is RESOLVED.** The RUNG-B question — *does the single-wire 2D PEPS per-edge
>   bond saturate under multi-round noisy+leaky d5 syndrome extraction?* — read as a **No-Go**
>   (bond grew 4→18→48/abort). **That No-Go is FALSE: the bond growth is a truncation-GAUGE
>   representation artifact, NOT physical entanglement.** The carrier's *state* is exactly
>   correct; its true bipartition entropy `S_A` is **BOUNDED (2–4 ebits)**. **The carrier is
>   FEASIBLE.**
> - **Full write-up (READ IT):** [`CRUX_RESOLVED_bond_is_gauge_artifact_2026-07-11.md`](CRUX_RESOLVED_bond_is_gauge_artifact_2026-07-11.md).
>   The prior handoff `HANDOFF_peps_crux_nogo_retracted_2026-07-11.md` is **SUPERSEDED** (banner added).
> - **★★ DO NEXT (user-chosen order 2→3→1; 2 & 3 DONE):** build the **environment-optimal
>   truncator** (FET / loop-corrected) so the *represented* bond tracks the *true bounded* `S_A`
>   → then WP1 (the real S_A-saturation test over R=20–40) can finally run. See §5.
> - **Parked (orthogonal):** the c64 screening engine (plan + contract + red-team done, no code).

---

## 1. THE CONCLUSION (what is now TRUE — build on this)

**The per-edge bond `D_t(r)` was the WRONG feasibility instrument.** It measures the
non-canonical PEPS *representation cost*, not the physical entanglement. The physical
entanglement (von Neumann bipartition entropy `S_A`) is **BOUNDED** and does not grow. Proven
across all three regimes with an INDEPENDENT ground truth each (FAITHFULNESS rule I):

| regime | true `S_A` (INDEPENDENT GT) | representation (bond/rank) | script |
|---|---|---|---|
| **d3 leakage-off** (EXACT) | `dense_psi` SVD `S_A=2.00000` `==` **GF(2) stabilizer baseline to 2e-16** | bond 4→16 | `peps_leakoff_d3_entropy_control.py` |
| **d5 leakage-off** | codestate persists: `|⟨S_g⟩|-1=1.4e-15` (24 stabs) + `|⟨Z_L⟩|-1=4.4e-16` ⇒ GF(2) **4.000 ebits** | bond 4→16 | `peps_leakoff_d5_confirm.py` |
| **d3 leakage-on** (WG_L1=5e-3) | `dense_psi` `S_A=2.00000` UNCHANGED /6 traj | rank 4→29, bond 4→18, `|2>`-mass 1e-3 | `peps_leakon_d3_entropy_confirm.py` |

**Mechanism:** `√E_s` is an exact (3,5,3)-rank qutrit TT (faithful projector, mechanically ×3–5
per injection); the single-wire PEPS tracks **no canonical form**, so the LOCAL simple-update
pair-insertion bond (`_insertion_spectrum`) over-counts the true Schmidt rank (loop/gauge
redundancy) and the local ε-cut compounds it (the contract's **SW-S6** caveat). Weak leakage
adds a tiny Schmidt tail (`|2>`-mass 1e-3 ⇒ ~25 small σ) that inflates the RANK/BOND but ~0 the
ENTROPY (leakage is a LOCAL channel). ε=1e-8 keeps that tail. `loop_rank_probe.rank==dim` does
NOT refute — it is a LOCAL single-bond statement, not the bipartition Schmidt rank.

**Fix:** an environment-optimal (FET/loop/variational) truncator so the bond tracks `S_A`. §5.

---

## 2. THE REASONING CHAIN (how we got here — the discipline caught THREE wrong conclusions)

1. **Step-0 triage** read the POST-ε-truncation bond at the round-2 abort: eps-ranks 30/32/46
   (discarded ~1e-32 ⇒ genuine ranks) ⇒ falsified the prior "physical bond ≲20" retraction.
2. **User challenge:** "this contradicts the literature — is it a code bug?" ⇒ ran **`theory-fix`**.
   Result: the "contradiction" is **apples-to-oranges** — Manabe's bond is a 1D-MPS bipartition
   of a rep-code/thin-strip WITH ancilla reset; ours is a 2D-PEPS per-EDGE bond, no reset;
   MIPT bounds are steady-state, round-2 is a transient. **Not a bug, not a real No-Go.**
3. **User idea:** "find the papers' code" ⇒ found **`external/reference_repos/tn_qsim` = Manabe's
   ACTUAL code** (git author 真鍋秀隆/Hidetaka Manabe, Osaka U; the GTA method; 1D-MPS + FET-on-PEPDO).
4. **leakage-off gauge control** (`peps_leakoff_gauge_control.py`): the bond grew even in the
   Clifford limit with `loop_rank_probe.rank==dim` ⇒ (WRONGLY) looked like "not gauge, real
   over-entangling." → the discriminator: an INDEPENDENT `S_A` oracle.
5. **validity workflow** (theorem-grade): `√E_s` on a codestate = the exact projector ⇒ `S_A`
   PROVABLY constant ⇒ bond growth PROVABLY representational; caught that bond-vs-entropy is
   apples-to-oranges and `loop_rank_probe` is local-only. Prescribed the same-measure `S_A` test.
6. **d3/d5/leakon exact `S_A` tests** (§1) ⇒ RESOLVED.

The trail: `theory-fix` → the tn_qsim find → the validity workflow → the exact anti-circular
`S_A` tests. Each caught a specific wrong turn; none by "being careful."

---

## 3. KEY LITERATURE (grounded, in RAG — 2230 chunks)

- **Manabe-Suzuki-Darmawan 2308.08186** "Efficient Simulation of Leakage Errors in QEC Codes
  Using Tensor Network Methods" (NJP). **1D MPS** (rep code + THIN 3×d surface strip),
  ancilla-EXPLICIT with measure-AND-RESET (No-reset/MLR/DQLR), GTA (generalized twirling).
  His "bond ~4-10 saturating" = a **1D-MPS bipartition bond** (NOT a 2D per-edge bond); noisy
  bonds actually ~21-65; NEVER simulated a full d×d. **Code = `external/reference_repos/tn_qsim`**
  (numpy/jax/tensornetwork/cotengra/kahypar; the FET truncator = `surface.py` /
  `surface_opt_trun.py::find_optimal_truncation` on a PEPDO — the fix reference). Note:
  `docs/papers/reading_notes/manabe_suzuki_darmawan_leakage_tn_2308.08186.md`; Zenodo 10.5281/zenodo.15540949.
- **MIPT / monitored-circuit corpus** (10 close-read notes in `docs/papers/reading_notes/`):
  Li-Chen-Fisher 1808.06134 (projector-rank shifts p_c 4.5×: 0.15↔0.68), Skinner-Ruhman-Nahum
  1808.05953 (Footnote-13 raw-rank inflation — REFUTED as our artifact class since our discarded
  weights ~1e-32 are genuine), Sierant 2210.11957 (only genuine 2D/3D; 2-round window can't tell
  transient from volume-law; p_c ≤ 0.78), Negari 2307.02292, Gullans-Huse 1905.05195/1910.00020,
  Bao-Choi-Altman 1908.04305, Fidkowski 2008.10611, Chan 1808.05949, Iaconis 2010.02196.
  **All bound a 1D/steady-state BIPARTITION ENTROPY — none a 2D-PEPS per-EDGE bond ⇒
  apples-to-oranges with our result.**
- **tn_qsim other refs (independent PEPS/FET):** Rudolph-Tindall 2507.11424 (`eps_l` grounding),
  TEPEPO 2512.01781 (2D open-system TN), Varbanov 2002.07119 (qutrit leakage surface-17, quantumsim).

---

## 4. CODE MAP (the seams that matter — READ `docs/CODE_MAP.md` first, then these)

**The carrier** (`src/error_coupling_simulator/carrier/peps/`):
- `trajectory.py`: `sample_stab` (grow via `apply_stab_branch` → `d_abort` check on the
  **PRE-truncation** dim at :475 → `truncate_path_bonds` at :518); **`_insertion_spectrum`**
  (:151-160, `svdvals(R_A R_B^T)` — the LOCAL over-counting bond read), `_rank_for_tail`/`_sq_tail`
  (:163-191), `_exact_rank` (:194, the 1e-12 threshold), the dynamic-eps policy `_policy_precut`/
  `_policy_cut`/`truncate_path_bonds` (:201-365), `PepsSampler.sample` (:677, the entry:
  `R_n=None` ⇒ EXACT route byte-identical d3; `R_n=χ_b` ⇒ boundary route for d5), `round_hook`.
- `stab_tt.py`: `_stab_sqrt_diag` (:82-94, the 0/1 parity diagonal ⇒ `√E_s` = exact projector on
  {0,1}), `_tt_svd` (:97, the (3,5,3) TT), `apply_stab_branch` (:172).
- `contraction.py`: the double-layer boundary-MPS reads — `norm_cache`/`norm_read`,
  **`born_read_stab`** (:352, returns `(N,M,p0)`; `⟨S_g⟩=M/N`), **`expect_site_caps`** (:263,
  RAW `⟨ψ|O|ψ⟩` — divide by N for `⟨Z_L⟩`), `_fit_compress_rows` (`_FIT_TOL` in `pepo/sampler.py:73`).
- `state.py`: **`dense_psi`** (:302, exact `(3^n,)`, n≤9 — the d3 EXACT `S_A` bridge; pos 0 = MOST
  significant), `build_codestate_peps`, `qutrit_gate`, `CDTYPE/RDTYPE` (:45).
- `diagnostics.py`: `bond_profile` (:92), **`loop_rank_probe`** (:340, gauge-LOCAL, NOT Schmidt),
  `eps_l` (:BP loop-correlation — the A'/loop-corrected-truncator ingredient).
- Cutters (`carrier/pepo/dynamics.py`): `svd_precut_bond`/`ntu_truncate` (the reconstruction),
  `_qr_split`, `_cluster_metric` (v4.3 env-bounding).
- Noise: `xzzx_parser.py:130,723` — the carrier REPLACES the circuit's `DEPOLARIZE2` (on each CZ)
  with the leakage channel `exp(L/4)`; θ=0 ⇒ inert on {0,1} ⇒ leakage-off is NOISELESS Clifford.
- Leakage: `mechanisms/qutrit_teachers.py` — `calibrate_theta_for_wg_l1` (target 0 ⇒ θ=0),
  `wg_rates`/`coherence_of_leakage` (leakage-off asserts). `channels.py:621` `leakage_channel_super`.
- Stim anchor: `certify/anchors/stim_clifford.py` (`_pauli_targets`, `_stim_slice_records` — a
  detector-SAMPLER wiring check, NOT an entropy oracle; needs a `TableauSimulator` rebuild for entropy).

**Scripts written this session** (`outputs/nonpauli_teacher/`, gitignored local evidence, each with `_run.sh`):
- `peps_leakoff_d3_entropy_control.py` — d3 EXACT `S_A` (dense_psi SVD) vs GF(2) baseline. **The decisive test.**
- `peps_leakoff_d5_confirm.py` — d5 codestate-persistence (`|⟨S_g⟩|=1`) + GF(2) 4-ebit baseline.
- `peps_leakon_d3_entropy_confirm.py` — d3 leakage-ON `S_A` (full qutrit), 6 trajectories.
- `peps_leakoff_gauge_control.py` — the leakage-off gauge control (loop_rank_probe; superseded read).
- `peps_spike_sw8_bond_saturation.py` — the SW8 runner (has `PEPS_SW8_TRIAGE=1` mode + the src
  triage diagnostic in `trajectory.py` sample_stab, env-gated `PEPS_SW8_TRIAGE_SPECTRUM=1`,
  **UNCOMMITTED**; d3 gates stay 28/28 byte-identical since it's inert by default).
- **GF(2) stabilizer-entropy helper** (`stabilizer_entropy_SA`, `_gf2_rank`, `_pauli_to_symplectic`)
  is inlined in the d3/d5 scripts — the reusable independent-GT primitive (EXACT for stabilizer
  states, Gottesman-Knill; zero info loss).

---

## 5. ★ NEXT STEP — build the environment-optimal truncator (RUNG-B option 1)

**Goal:** replace the LOCAL simple-update ε-truncation so the represented per-edge bond tracks
the true bounded `S_A`. The fix has a spectrum (do the cheap validation first):

| layer | fixes | cost |
|---|---|---|
| looser ε (1e-8→1e-4/1e-6, à la Manabe) | ONLY the weak-leakage tail (1e-3) | trivial (a constant) |
| **loop-corrected / BP-environment truncation** (reuse `eps_l`/`loop_rank_probe`) | the non-canonical gauge over-count | medium |
| **full FET** (tn_qsim `find_optimal_truncation`, env-weighted fidelity) | both, optimal | heavy (new policy + env compute + validate) |

**CRITICAL:** looser ε does NOT fix the gauge over-count (those are genuine LOCAL Schmidt values,
globally redundant) — the core fix MUST be environment-optimal (FET/loop). The carrier already
computes the double-layer boundary-MPS *environment* for its reads, so the FET environment is
largely in hand.

**Validation gate (predict-before-measure):** on the d3 leakage-off state, the FET/loop-truncated
per-edge bond must **collapse toward ~4** (tracking `S_A`=2 ebits) while `S_A` stays 2.000 (state
preserved). Then d5, then re-run WP1' (§4 of CRUX_RESOLVED): `S_A` saturation over R=20–40 (the
real test the artifact bond previously blocked at round-2 D_abort).

**Discipline:** this is a mainline-src build ⇒ use the `contract-build` skill (contract-first,
adversarial red-team, disjoint builders, review-before-run); src commits need explicit user
confirmation. Reference the tn_qsim FET impl (READ-ONLY) for the algorithm.

**Also amend** `peps_singlewire_spike_contract.md` WP1 to gate on `S_A` (retire the `D*∈[2,32]`
per-edge-bond band; `D_abort` becomes a pure resource guard, decoupled from feasibility).

---

## 6. PARKED — the c64 screening engine (orthogonal; do NOT conflate with the fix)

The GPU FP64 cost (c128, ~21–94 min/round in the growth regime) motivated a c64 screening engine.
Plan + contract + red-team are done (NO code): `c64_screening_engine_plan_2026-07-11.md`,
`c64_screening_engine_contract_2026-07-11.md` (red-team `wf_5ffa62a3` findings banked — top blocker:
the c128 frozen reference only reaches ~round 2). c64 is a (c)-SCREENING accelerator, not the
evidence engine, and is now **lower priority** (the crux is resolved; the FET fix + a corrected
metric may make the runs cheap enough anyway). GB10/spark is DISQUALIFIED for c128 (large-linalg
garbage) but c64-on-GB10 untested. Revisit only if the FET-corrected WP1 run is still too slow.

---

## 7. ENV / RUN TRAPS

- **Env python:** `/home/cx/miniconda3/envs/aiqec/bin/python` (conda NOT on non-login PATH).
- **Invoke:** `wsl -d ubuntu-f -- bash -c 'cd /home/cx/Document/AI_QEC/AI_QEC && <cmd>'`. Traps:
  (i) `$VAR` (incl. loop vars) inside the `bash -c '…'` string come back EMPTY — use LITERAL paths
  or a committed `.sh` (vars work inside a real `.sh`); (ii) `bash /abs/path.sh` gets MSYS-mangled —
  always `cd <repo> && bash <relative/path.sh>` (start with a WORD); (iii) capture the real python
  exit with `${PIPESTATUS[0]}` in the runner.
- **GPU:** RTX 5090, GPU-only, **serialize** heavy work (user's live desktop, no concurrent GPU).
- **d3 gates:** `bash outputs/nonpauli_teacher/peps_spike_gates_d3_run.sh` (28/28, ~18s).
- **RAG:** `python -m qec_twin.rag.store --query "<q>"` (2230 chunks).
- **d3 scripts are CHEAP** (dense_psi exact, seconds–5 min); d5 leakage-off ~9 min; the growth-regime
  leakage-on d5 is ~94 min/round (why d3 is the workhorse for the exact `S_A` reads).

## 8. POINTERS
- **★ THIS + [`CRUX_RESOLVED_bond_is_gauge_artifact_2026-07-11.md`](CRUX_RESOLVED_bond_is_gauge_artifact_2026-07-11.md)** = the entry point.
- Memory: `project-peps-spike-build-state.md` (RESUME, carries the full chain).
- Contract: `peps_singlewire_spike_contract.md` (WP1 to amend per §5).
- Reference code: `external/reference_repos/tn_qsim` (Manabe / FET).
