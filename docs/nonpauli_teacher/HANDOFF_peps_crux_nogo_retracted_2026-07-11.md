> # ⛔ SUPERSEDED (2026-07-11 later same day) — the crux is now RESOLVED.
> Read **[`CRUX_RESOLVED_bond_is_gauge_artifact_2026-07-11.md`](CRUX_RESOLVED_bond_is_gauge_artifact_2026-07-11.md)** instead.
> The discriminating tests below WERE run: the per-edge bond growth is a **truncation-gauge
> representation artifact, NOT physics** — the carrier's true bipartition entropy `S_A` is
> **BOUNDED** (2–4 ebits, confirmed exact+anti-circular at d3 leakage-off, d5 leakage-off, d3
> leakage-on). The single-wire 2D PEPS carrier is **FEASIBLE**; the fix is an environment-optimal
> (FET/loop) truncator. The "PROVISIONAL / build on neither arm" verdict below is CLOSED. This
> file is kept for the reasoning-chain history only.

# HANDOFF — d5 PEPS crux: the pilot No-Go is RETRACTED (theory-fix), run the discriminating test next (2026-07-11)

> ## ★ READ THIS FIRST (the 60-second brief)
> - **The crux** (RUNG-B): does a single-wire 2D PEPS's per-edge bond **saturate** (bounded,
>   area-law) or **grow** under multi-round noisy+leaky d5 rotated-XZZX syndrome extraction?
>   The whole d5/d7 carrier line hinges on it. Contract:
>   [`peps_singlewire_spike_contract.md`](peps_singlewire_spike_contract.md) v1.0 (WP1/WP2, §6.1-6.4).
> - **What happened this session:** the d5-arm was built + d3-gated + committed; SW7 (d5 codestate)
>   passed; a **pilot** (N_traj=1, ε=1e-8, R=40) hit `D_abort=40` at round 2 (bond 4→18→"48") and the
>   WP1 verdict returned **No-Go (F-SW-BOND)**. Deep-research + 10 close-read MIPT notes, then an
>   **Opus theory-fix**, then a **verified code fact**, changed the picture.
> - **★★ THE VERDICT (theory-fix, Opus): the No-Go is RETRACTED as a physics result. It is
>   PROVISIONAL-ONLY.** The abort fired on a **PRE-TRUNCATION grown product rank (S0)**, NOT the
>   ε=1e-8-truncated physical bond (verified: `trajectory.py:469-479`). The "grew to >40 under ε=1e-8"
>   premise is **FALSE**. **Do NOT build on EITHER arm** (not "carrier feasible", not "infeasible").
> - **★★ DO NEXT (do not skip, do not go sideways):** run the theory-fix's single cheapest DECISIVE
>   test to settle **artifact vs real** — §4 below. Step 0 is near-free and exploits the verified bug.
>   Only after that test resolves may the crux verdict be re-opened.

---

## 1. THE FULL REASONING CHAIN (why we are where we are — read in order)

1. **Build (done + committed `e6c2881`, Dev-F).** Raced to the d5 crux (2b-ii). Built the d5-arm on
   top of the committed single-wire PEPS engine (`src/error_coupling_simulator/carrier/peps/`):
   - **M1** (src, committed): threaded a per-snapshot `NormCache` through the trajectory loop
     (`trajectory.py` + `contraction.py`, +73/−15). d3 gates stay **byte-identical** (all cache builds
     guard on `R_n is not None`; d3 uses the exact route). **pytest 28/28 green.**
   - **Scripts (outputs/, gitignored local evidence):** S1 #4 boundary-vs-exact d3 (ALL PASS — boundary
     route is unbiased, converges to exact); S2 #3 eps_l evolved-d3 indep-ref (core match green; a
     BP-vs-exact-on-grid non-vacuity nuance PARKED as a documented open finding, non-crux-blocking);
     S3 **SW7 d5 codestate cert = 7/7 PASS** (|2⟩-mass exact, per-edge dim==2^mult max bond 4,
     ⟨S_g⟩/⟨Z_L⟩ via caps χ_b=32 converged); S4 SW8 runner (the crux runner).
   - **Stage-4 adversarial review** (4 lenses → 14 findings): M1/S1/S2/S3 clean; **4 CONFIRMED in S4**
     (verdict honesty: F9 BLOCKER wrong-GO + F4/F5/F6) — ALL FIXED + independently re-verified. This
     paid off: the pilot's abort was correctly reported as No-Go (not F9's false GO).
2. **The pilot.** Ran the S4 runner in a new **`PEPS_SW8_PILOT=1`** mode (N_traj=1, R=40, ε=1e-8, no
   auto-extend). Result: per-edge max bond **4 (codestate) → 18 (round 1, post-truncation) → D_ABORT at
   round 2** (a path bond `B1_3` grew to dim **48** > `D_abort=40`). WP1 verdict: `all_saturate=False`,
   `GO=False`, `headline_abort_is_finding=True` ⇒ **F-SW-BOND (No-Go direction)**.
3. **Efficiency dig (the run is slow).** Per-round cost explodes with bond (r1 ~21 min). Profiled
   (`peps_spike_sw8_profile.py`): the **double-layer boundary-MPS READ = ~97% of cost**, truncation ~3%.
   Tried the two cheap speedups — **both measured NO-OP**: (a) cotengra contraction-path hyperopt
   (installed `optuna`; the boundary reads use quimb's structured 1D-fit, not cotengra pathfinding), and
   (b) fit convergence tol 1e-12→1e-9 (the fit converges in few iterations; cost is per-sweep linalg,
   not iteration count). The cost is inherent χ_b-scaled double-layer contraction. **The tol change was
   reverted** (contraction.py is back to the M1-committed state). `optuna` is installed (benign).
4. **Literature (deep-research + 10 close-read notes now in RAG, 2230 chunks).** The
   measurement-induced-transition (MIPT) / monitored-circuit literature is unanimous: a high measurement
   rate (syndrome extraction measures ~all ancillas/round ⇒ p≈1) sits **deep in the area-law/BOUNDED
   phase** (p_c ∈ [0.05, 0.78] across ALL models + geometries incl. 2D weight-heavy: Sierant 2210.11957,
   d2-plaquette 0.55 / d3-8-body 0.78). Manabe 2308.08186 (**ancilla-explicit** MPS, weak leak): bond
   **~4-10, saturates at ~20-30 ROUNDS** (not 2). This *seemed* to say the No-Go is an instrument
   artifact.
5. **★ Theory-fix (Opus, adversarial) — the correction.** Scrutinizing the convenient conclusion "it's
   an artifact because MIPT p≈1 → area-law" caught **two** things:
   - **(motivated reasoning)** The "MIPT p≈1 → area-law" *justification* is a **contradicted ANALOGY**
     for our object: every MIPT paper is a RANDOM 1D circuit with single-site measurements; ours is a
     FIXED 2D **weight-4 ancilla-COMPILED √E_s POVM + qutrit leakage**. Li-Chen-Fisher 1808.06134 shows
     the measurement-projector **rank/structure shifts p_c 4.5×** — so p≈1 is NOT provably below the
     effective p_c for the biased weight-4 √E_s. **Cannot cite MIPT as proof.**
   - **(the smoking gun — a VERIFIED CODE FACT)** `sample_stab` checks `D_abort` on
     `state.tn.ind_size(bond)` = the **GROWN, PRE-TRUNCATION** bond, right after `apply_stab_branch`,
     **BEFORE** `truncate_path_bonds` runs (verified in `trajectory.py:469-479`). So the pilot's **"48"
     is a raw S0-type product rank, NOT the ε=1e-8-truncated physical bond.** `D_abort=40` is a
     **RESOURCE guard** (avoid building a huge NTU metric), watching the **wrong quantity** for the WP1
     saturation signal. This is exactly the Skinner-Ruhman-Nahum 1808.05953 **Footnote-13** fragile-lens
     (raw bond count inflates while the truncatable entanglement stays bounded).
6. **Net.** The No-Go **measured the wrong quantity** and rests on a contradicted analogy ⇒ **retract it
   as a physics result**, but do NOT over-correct to "carrier feasible" — the *direction* ("likely not
   physics") has two theorem-grade priors (zero-noise stabilizer trajectory per-edge rank O(1); the
   per-injection √E_s bond bound (3,5,3), 28/28-asserted) but is not established.

---

## 2. EPISTEMIC LEDGER — what is true, what is retracted, what is FORBIDDEN to build on

| Item | Status |
|---|---|
| M1 norm-cache threading; d3 gates 28/28 byte-identical | (a)-exact, COMMITTED `e6c2881` |
| SW7 d5 codestate structurally faithful (bond 4, χ_b=32 converged) | (a)/(c) PASS |
| S1 boundary-MPS route is unbiased (converges to exact at d3) | (a) PASS |
| Per-injection √E_s bond bounded (3,5,3)/(3) | (a)-exact, asserted |
| `D_abort` fires PRE-truncation ⇒ pilot "48" = S0 product rank | **(a)-exact, code-verified `trajectory.py:469-479`** |
| The pilot **No-Go** (bond grows / not-saturating) | **RETRACTED — class-(c) provisional tripwire on an UN-DIAGNOSED instrument event; NOT a physics result** |
| "MIPT p≈1 ⇒ our bond bounded" | (c) **contradicted analogy** — NOT proof |
| WP1 band **D*∈[2,32]** | **MIS-GROUNDED** — imported Manabe rep-code/thin-strip/1e-4 numbers into a d5-2D-compiled-1e-8 setting; must be **re-derived** at the intended ε before use |

**FORBIDDEN (do not let a new session build on any of these):**
- ✗ Declaring the single-wire 2D PEPS carrier **feasible OR infeasible**.
- ✗ Proceeding to a heavy 8-traj WP1 run / gates on the assumption the No-Go was spurious **or** real.
- ✗ Citing MIPT p≈1 as a bounded-bond guarantee for the compiled biased weight-4 √E_s.
- ✗ Citing D*∈[2,32] as a satisfiable band (re-derive it first).
- ✗ Any d5→d7 bond-scaling extrapolation.
- ✗ Treating `D_abort=40` as a physics value (it is a pre-metric RESOURCE guard).

---

## 3. FAILURE-MODE SPLIT (what the discriminating test must resolve)

The pilot's bond growth has three candidate explanations (theory-fix estimate):
- **~60-65% BUG / instrument-setting** (DOMINANT): abort read the pre-truncation dim; ε=1e-8 is 2-4
  orders tighter than Manabe's 1e-4/1e-6; `D_abort=40` is a resource guard; round-2 is inside the
  transient (Manabe saturates at 20-30 rounds).
- **~20-25% COMPILED-SEMANTICS-REAL**: the compiled weight-4 √E_s injects representation-specific
  spurious singular values (S0-inflation) that an **ancilla-explicit** measure-and-reset would
  disentangle — real as an S0 effect, but BOUNDED by the (3,5,3) per-injection theorem; inflates the
  COUNT, not the physical entanglement.
- **~10-15% GENUINE-PHYSICS** (LEAST likely): near-stabilizer weak-leak should be area-law by two
  theorem priors; not fully excluded (leakage is non-Clifford; the weak/degenerate-projector p_c caveat).

---

## 4. ★ WHAT THE NEW SESSION DOES FIRST — the single cheapest DECISIVE test (artifact vs real)

**Goal:** decide whether the bond growth is a method artifact or real, using an INDEPENDENT,
non-circular ground truth (FAITHFULNESS_PROTOCOL rule I). Do NOT run the heavy 8-traj WP1 run until this
resolves. **src changes touch `trajectory.py` — get user confirmation before committing (docs/outputs
flow normally).**

### Step 0 — the near-free triage (do this FIRST; it directly exploits the verified bug)
The abort read the PRE-truncation bond. So the physical (post-ε-truncation) bond at round 2 was never
observed. Instrument the engine to see it:
- In `sample_stab` (`trajectory.py`), either **move the `D_abort` check to AFTER `truncate_path_bonds`**,
  or (cleaner, non-destructive) **keep the pre-truncation check but ALSO log both the pre- and
  post-truncation per-edge bond** each round, and **raise the effective abort ceiling** for this triage
  (e.g. `D_abort=200`; the `W_max=160` precut still caps the NTU metric, so the truncation is feasible on
  a grown dim ~48–90).
- Re-run the pilot 2-3 rounds (`PEPS_SW8_PILOT=1`, or a small dedicated triage runner). Read the
  **POST-ε-truncated kept bond + full Schmidt spectrum + cumulative discarded weight at `B1_3`**.
- **Decision:** if the "48" collapses to **≲20 with a fat sub-1e-8 tail** ⇒ **S0 artifact CONFIRMED on
  the spot** (the physical bond is bounded; the abort was firing on a pre-truncation product rank). If
  the post-truncation bond genuinely stays ≳40 and climbing ⇒ proceed to the decisive control below.

### Decisive — leakage-off control vs an independent Stim stabilizer oracle
- Set **leakage OFF** (`WG_L1_TARGET = 0` ⇒ θ=0 ⇒ the biased √E_s collapses to the **EXACT bond-2
  Clifford parity projector**, c=1, no |2⟩ weight). Re-run the **identical compiled-POVM syndrome-
  extraction circuit** 2-3 rounds on the PEPS carrier.
- Compare the PEPS per-edge (post-truncation) bond against the **exact stabilizer cut-rank** of the same
  noiseless-Clifford trajectory computed by an INDEPENDENT oracle: **Stim** (vendored in `external/`; the
  SW9 anchor `certify/anchors/stim_clifford.py` already wires Stim to this circuit) and/or
  `qec_twin/audit/bayes_floor.py` (the repo's exact per-sample oracle). A noiseless Clifford syndrome
  circuit is provably a stabilizer state at every round with **O(1) per-edge cut-rank** — so a PEPS bond
  of ~40 there has ZERO genuine-physics explanation.
- **Decision:** (i) leakage-off PEPS bond STILL climbs while Stim cut-rank is single-digit ⇒
  **UNAMBIGUOUS method artifact** (truncation-gauge / S0-inflation / abort-ordering) — retract the No-Go,
  the PEPS carrier survives pending a proper continuation; (ii) leakage-off bond stays O(1) and grows
  ONLY with leakage on ⇒ **leakage is the driver** — escalate to a p_leak-scaling + a post-ε-truncation-
  S1 (not S0) saturation check, and a **compiled-√E_s vs ancilla-explicit** comparison (Manabe's
  ancilla-explicit is bounded — is the compilation the culprit?), before any Go/No-Go.

### After the test resolves
- **If artifact:** (a) fix the WP1 saturation signal to read the **post-truncation** bond (S1), not the
  pre-truncation grown dim (S0); (b) **re-derive the D*/ε band** honestly for d5-2D-compiled semantics
  (do NOT reuse Manabe's rep-code/thin-strip 1e-4 numbers); (c) re-run a proper pilot to ~20-30 rounds
  (the physical saturation timescale) at a defensible ε with the corrected signal; (d) only then re-open
  the WP1 Go/No-Go.
- **If real (leakage-driven or genuine):** adjudicate the contract §5 falsification menu — (B') LPDO
  record-law arm, (C') thin-strip-only scope (mps_forward's proven regime), (D') geometry / ancilla-
  explicit change.

---

## 5. STATE / ARTIFACTS / POINTERS

- **Commits (Dev-F):** `e6c2881` (M1 norm-cache src + grounding doc). Nothing else src-committed this
  session. `contraction.py`/`trajectory.py` working tree = M1-committed state (the tol experiment was
  reverted).
- **Governing docs:** contract [`peps_singlewire_spike_contract.md`](peps_singlewire_spike_contract.md)
  v1.0 (SW7-SW9, WP1/WP2, §6.1-6.4); grounding
  [`peps_d5arm_grounding_2026-07-10.md`](peps_d5arm_grounding_2026-07-10.md) (what's built vs gaps, the
  seam map); the prior handoff
  [`HANDOFF_ancilla_explicit_rebuild_2026-07-10.md`](HANDOFF_ancilla_explicit_rebuild_2026-07-10.md)
  (single-wire vs doubled-wire; §2 = the compiled-vs-ancilla-explicit mechanism, directly relevant here).
- **Outputs scripts (gitignored, local evidence, `outputs/nonpauli_teacher/`):**
  `peps_spike_sw8_bond_saturation.py` (the SW8 runner — has `PEPS_SW8_PILOT=1` and `PEPS_SW8_SMOKE=1`
  modes) + `peps_spike_sw8_run.sh`; `peps_spike_sw8_profile.py` (the cost profiler);
  `peps_spike_sw8_pilot_monitor.sh`; `peps_spike_gates_d3_run.sh`; `peps_spike_boundary_vs_exact_d3.py`;
  `peps_spike_sw7_d5_codestate_cert.py` + `_run.sh` (precondition path uses the **double-nested**
  dataset root); `peps_spike_eps_l_evolved_d3.py`; `download_mipt_papers.sh`. The pilot's bond CSVs:
  `outputs/nonpauli_teacher/peps_spike_sw8_out/eps_1em08_R40/bond_perround.csv`.
- **Literature (committed):** 10 new MIPT/purification/geometry reading notes in
  `docs/papers/reading_notes/` (li_chen_fisher_…1808.06134, skinner_ruhman_nahum_…1808.05953,
  chan_…1808.05949, bao_choi_altman_…1908.04305, gullans_huse_…1905.05195 & …1910.00020,
  fidkowski_…2008.10611, negari_…2307.02292, iaconis_…2010.02196, sierant_…2210.11957) + PDFs/txt in
  `docs/papers/`. The **Manabe** note (`manabe_suzuki_darmawan_leakage_tn_2308.08186.md`) is the direct
  ancilla-explicit anchor. **RAG rebuilt: 2230 chunks.**
- **Memory:** `project-peps-spike-build-state.md` (the RESUME; carries the theory-fix retraction + the
  next test verbatim).

---

## 6. HOW TO RUN (env + traps)

- **Env python:** `/home/cx/miniconda3/envs/aiqec/bin/python` (conda NOT on non-login PATH). GPU = RTX
  5090, GPU-only, **serialize heavy GPU work** (user's live desktop, no concurrent jobs).
- **Invoke via wsl:** `wsl -d ubuntu-f -- bash -c 'cd /home/cx/Document/AI_QEC/AI_QEC && <cmd>'`.
  **Traps:** (i) `$VAR` reads inside the `bash -c '…'` string come back EMPTY — use literal absolute
  paths or a committed runner script (variables work inside a real `.sh` file); (ii) `bash /abs/path.sh`
  gets MSYS-path-mangled — always `cd <repo> && bash <relative/path.sh>`; (iii) capture the real python
  exit with `${PIPESTATUS[0]}` inside the runner, not the outer pipe.
- **d3 gates:** `bash outputs/nonpauli_teacher/peps_spike_gates_d3_run.sh` (28/28, ~18s).
- **RAG:** `python -m qec_twin.rag.store --query "<q>"` / `--build --force` (after adding notes).
- **Pilot / triage runner:** `PEPS_SW8_PILOT=1 bash outputs/nonpauli_teacher/peps_spike_sw8_run.sh`
  (writes `peps_spike_sw8.log` + bond CSVs; long — use `nohup` + the monitor pattern).

---

## 7. THE ONE-LINE FOR THE NEW SESSION
The crux is **UNRESOLVED**; the pilot No-Go is **RETRACTED** (it measured a pre-truncation S0 product
rank, verified in `trajectory.py:469-479`, and leaned on a contradicted MIPT analogy). **Do the §4
discriminating test FIRST** (Step 0 near-free post-truncation bond read → leakage-off vs Stim oracle),
build on NOTHING until it resolves, then re-derive the band and re-open Go/No-Go. Do not go sideways
into the heavy run, feasibility claims, or MIPT/band citations.
