# HANDOFF — non-Markovian SYNDROME-VISIBILITY on the error-coupling SIMULATOR, 2026-07-04

> **HISTORICAL / SUPERSEDED 2026-07-13.** Do not reuse its notion taxonomy, universal
> reachability claims, “realistic” numerical brackets, or transfer a Gaussian/motional-narrowing
> CP-div result to the production finite-RTN source. Current authorities are
> `notion123_taxonomy_literature_closure_2026-07-13.md` and `../NUMERICAL_PROVENANCE.md`.

**SELF-CONTAINED.** Everything load-bearing (the scope rule §0, the three-error diagnosis §1, the plan §5,
the resource map §6) is fully contained IN THIS FILE — it does NOT depend on any external note resolving.
This hands off the ORIGINAL problem of the session — *is the non-Markovian error VISIBLE on the syndrome
record, and how do we fix it* — after a large scope correction and a three-error root-cause diagnosis.
**The previous handoff (`HANDOFF_reconstruction_active_observation_2026-07-03.md`, now VOID) COLLAPSED
because it omitted the three-error diagnosis of §1** and drifted into out-of-scope digital-twin machinery.
Do not repeat that: §1 is the load-bearing content; read it first.

> **On the `[[...]]` links:** these are Claude-Code AUTO-MEMORY notes (in the Claude Code project memory,
> auto-loaded via `MEMORY.md` at the start of a fresh Claude Code session) — **NOT repo files.** Do not
> grep the repo for `memory/…`; there is no `memory/` dir in the repo. In a fresh Claude Code session they
> load automatically; if you are NOT in one (or they don't load), this handoff still stands on its own.
> Also read the repo docs named inline (design doc, g6 rederivation, `h2_effectsize_g4_prereg.md`,
> `CLAUDE.md`) and query the local RAG for literature: `python -m qec_twin.rag.store --query "..."`.

---

## 0. Mission + the ONE scope rule (binding)

**We build the error-coupling SIMULATOR** — a faithful forward generator. Product = the record
`{det,obs}`. Validity = **(i) faithfulness** (record matches an INDEPENDENT oracle) **+ (ii) anti-toy
legitimacy** (the modeled coupling / non-Markovian feature is DISTINGUISHABLE from a genuine
CP-divisible/Markovian null — else it is a toy). **The digital twin — teacher-as-learner, twin RECOVERY of
the mechanism, `do()`, active-observation characterization — is a SEPARATE, LATER project, OUT OF SCOPE.**
([[feedback-simulator-is-goal-twin-is-next]], [[feedback-simulator-not-decoder]].)

**Detectability is BOTH scopes — the in/out line is the PURPOSE.** Mechanical test (apply it literally):
**IN** = does a FIXED statistic separate the shared arm from its null (no model fit)? → the anti-toy
legitimacy gate, the whole "syndrome visibility" question. **OUT** = does any procedure RECOVER/estimate
the mechanism parameters or run `do()`? → the twin. `N_detect` for a fixed `p_ij`/`RR_CORR` statistic is
IN; `N` to identify/recover the source is OUT. Track 1's `N_detect` is the fixed-statistic kind = IN.

## 1. THE THREE-ERROR DIAGNOSIS (verbatim — this is what the last handoff dropped; DO NOT drop it)

The program had concluded the non-Markovian imprint is "sub-feasible / a faithful sub-floor / unmeasurable
at feasible N" (G0-v2 STOP, G6 sub-floor). That conclusion is WRONG for three reasons (user, 2026-07-04):

- **错 A (核心, metrics 错了): the wrong observable AND the wrong null (two defects — fix BOTH).**
  *(i) Wrong observable:* G0-v2 used a two-point record TV; the literature instead **DIRECTLY learns the
  correlation distribution** (Zheng Walsh-Hadamard fault learning / Spitz `p_ij` / process tensor) —
  first-order, efficient. **Kam arXiv:2410.23779 proves the 2-point detector correlation is insufficient —
  you need multi-time (lag≥2).** *(ii) Wrong null (the DECISIVE half):* G6 discriminated *shared MINUS an
  exchangeable `markovian_baseline()` permutation null* — which **retains ~73% of the covariance and so
  subtracts the first-order signal, forcing it to second order** (→ the retracted `N∈[1.1e10,1.2e15]`). The
  fix is **shared-vs-OFF** (`off_source()`, Θ(0), structural zero where `p_ij(lag≥2)=0` EXACTLY), reading
  the **absolute** lag≥2 correlation — NOT a difference from an exchangeable null. **A fresh session that
  swaps only the observable (2-point→multi-time) but keeps the shared-minus-markovian subtraction
  reproduces the retracted trap — you must change the null too.**
- **错 B: the source was too weak AND mis-sited (Class-0 benign) — two halves.** *(weak)* slice-1
  `γφ ~ 1e-5` is ~6 orders BELOW the readout/reset instrument ("faithful sub-floor"); real non-Markovian
  noise is far stronger (Harper-Flammia ~2× LER; leakage tail). *(mis-sited)* slice-1 couples onto **Kam
  Class-0 (data ZZ/T2, provably BENIGN)** — the wrong error class for a record-detrimental signal; a
  record-*detrimental* effect may need re-siting Θ onto Class-1 (ancilla SPAM) / Class-2 (CZ depol), the
  ancilla-axis architecture NOT yet built (`h2_effectsize_g4_prereg.md §7.B`). Concluding "unmeasurable"
  from an unrealistically weak source on a benign class is over-extrapolation. The amplitude fix and the
  Class-0/1-2 siting fork (§2, §5 Track 3) are two halves of THIS error, not afterthoughts.
- **错 C: Prop IW-1 was over-generalized.** Prop IW-1 is a CORRECT theorem about the coherent (commutator,
  `Im K`) sector being *second-order*. It was wrongly stretched to "non-Markovian error is generally hard
  to measure." **The stochastic non-Markovian part is NOT in the commutator sector — it is first-order,
  directly learnable.**

**Consequence:** the **G0-v2 FAIL / G6 "sub-floor" do NOT stand** (they used the wrong observable A + weak
source B + over-generalized IW-1 C). They are to be REDONE with the corrected observable at a realistic
source. (Prior sessions flip-flopped on whether they "stand as anti-toy results" — the FINAL position:
they do NOT stand, because observable A was itself the wrong metric.)

## 2. The corrected FIX (the design — `simulator_legitimacy_direct_correlation_design_2026-07-04.md`)

- **Observable (fix A):** the **absolute lag≥2 direct correlation** — `p_ij(lag≥2)` (Spitz Eq.13) and/or
  `RR_CORR` — read on the SHARED arm as an absolute quantity. lag≥2 is chosen because the round-delta
  detector stream is **MA(1)**: off-arm `p_ij(lag1)=μ≈0.0149`, `p_ij(lag≥2)=0` EXACTLY, so any nonzero
  lag≥2 is pure coupling memory. Multi-time (a vector over lags), not a single 2-point (Kam). **RETIRE the
  G0-v2 2-point TV and the shared-minus-markovian z-score.**
- **Null (fix A, part 2 — decisive):** compare shared vs **OFF** (`off_source()`, Θ(0), structural zero),
  NOT shared vs the exchangeable `markovian_baseline()` (which retains ~73% of the covariance and forces
  the second-order trap → the retracted `N∈[1.1e10,1.2e15]`).
- **Source (fix B):** a REALISTIC amplitude sweep — plus the architectural fork: slice-1 sits on **Kam
  Class-0 (data ZZ/T2, provably BENIGN)**; a record-*detrimental* signal may need re-siting Θ onto **Class-1
  (ancilla/syndrome SPAM)** or **Class-2 (CZ depol)** — the ancilla-axis architecture NOT yet built
  (`h2_effectsize_g4_prereg.md §7.B`).
- **IW-1 scope (fix C):** predict the stochastic 1/f memory is directly present at lag≥2 (first-order), NOT
  the commutator sector.
- These observables (`p_ij`/`RR_CORR`) are **simulator-internal validation instruments**, NOT a twin
  deliverable.

## 3. The two-axis validation architecture (uncoupled is a first-class output)

**Coupling is a SWITCH** — the simulator must faithfully EXPRESS BOTH the uncoupled (baseline/Markovian)
AND the coupled records. "Prove the uncoupled version correct FIRST, then the coupled delta is
well-founded." `off` (Θ(0)) is NOT zero-error — it is the full schedule-baseline error model, no coupling.

- **AXIS A (foundational, run FIRST) — uncoupled-baseline cross-simulator EQUIVALENCE.** switch=off output
  `==` INDEPENDENT ESTABLISHED simulators, split by error class (this is stronger than matching our own
  DM oracle — Stim/QuTiP are different implementations):
  - **Pauli/Clifford slice `==` Stim** (`StimCliffordAnchor`). ⚠ **DROPPED for now (user 2026-07-04)** — see §4.
  - **NON-PAULI `==` QuTiP `mcsolve` + exact qutrit-DM** (the previously-developed machinery; Stim CANNOT
    do non-Pauli — frontend README §54).
- **AXIS B (builds on A) — coupled-delta faithfulness + legitimacy** (the §2 direct-correlation observable).

## 4. Decisions locked THIS session (binding)

- **Pauli backend DROPPED** (Db + Dc cancelled). Rationale (user): Pauli probably can't connect to
  coupling — coupling is a *continuous / non-Pauli rate modulation*, and the dense Axis-1 path rejects
  Pauli noise by design (`emit_clifford_slice` is `NotImplementedError`; "Stim noise is rejected by the
  schedule extractor by design"). So Axis-A's Pauli==Stim leg is shelved; focus is NON-PAULI.
- **Da = YES:** non-Pauli v1 = the continuous qubit-CPTP path (`emit`, already works); qutrit-leakage is a
  phased backend value (later).
- **Focus:** fully finish the NON-PAULI side, and — the actual point — RESOLVE the non-Markovian
  syndrome-visibility question.

## 5. THE PLAN (how to resolve syndrome visibility)

> **Approval status (be precise):** the ARRANGEMENT/priority below (do Step 1 first, analytic, cheap) is
> user-approved. The DESIGN it rests on
> (`simulator_legitimacy_direct_correlation_design_2026-07-04.md`) is still **"DESIGN for review — no code
> until un-led reviewed + user-approved"** and carries FOUR open decisions: **D0** (Axis-A equivalence refs
> + tolerances), **D1** (realistic-amplitude anchor — see Step 1), **D2** (null tier: shared-vs-off first,
> vs revive the theorem-grounded RHP/BLP CP-divisible null), **D3** (Class-0 sweep now vs Class-1/2 build
> first). Resolve D1 (and ideally D3) as part of Step 1; D0/D2 before Step 2+. Do NOT skip the un-led design
> review.

**Track 1 — resolve syndrome visibility (the point):**
- **Step 1 (ANALYTIC, cheap, DO FIRST — no big build, no GPU, no mainline-src change):** derive a **NEW
  closed-form `N_detect`** for the CORRECTED observable — the **absolute lag≥2 shared-vs-off** `p_ij`/`RR_CORR`
  (signal = shared-arm `p_ij(lag≥2)` distinguished from the off-arm STRUCTURAL ZERO; SE = shot-noise of an
  absolute `p_ij` estimate, `hardware/pij.py::spitz_pij_delta_se`). **⚠ Do NOT fork
  `g6_null_feasibility_from_constants.py`'s `record_N_sizing`/verdict — that is the RETRACTED
  shared-MINUS-markovian second-order lag-1 sizing that hardcodes the `N∈[1.1e10,1.2e15]` "SUB-DETECTABLE"
  conclusion.** Reuse from the template ONLY the source-sampling + the MA(1) self-check scaffolding; the
  N-sizing is new. Use `OneOverFDriftSource.analytic_psd` for the shared-arm lag≥2 autocorrelation.
  - **⚠ The "realistic amplitude" is OPEN (design D1) — resolve it, don't invent it.** No physical
    1/f-amplitude bracket is wired (the knobs are class-(c) design defaults). Two options: (a) commit a
    cited flux/charge-noise 1/f-spectroscopy anchor for `amplitude_radns`/`gamma_phi_sensitivity`
    (theory-first gap-fetch); or (b) declare a class-(c) SWEEP from the slice-1 default
    `amplitude_radns=1e-4` up to the physically-grounded channel baseline `γφ=1/30000` (T2=30µs) and report
    `N_detect` across it. **This must be settled by the user (D1) before the number means anything.**
  - **⚠ `h2 §7.C/§7.D` is NOT the realistic-amplitude anchor.** It is a registered NEGATIVE ΔLER finding
    (mild 1/f ΔLER ~100× below the 1e6 floor) for **Class-1**, in **ΔLER (record-detriment)** units — a
    DIFFERENT quantity from Step 1's **absolute correlation (legitimacy)**. A nonzero lag≥2 correlation vs
    off can be LEGITIMATE (non-toy) even where §7.C says the ΔLER is sub-floor — that is exactly the
    P4/Class-1-2 fork, not a contradiction. Do not read §7.C as bounding the correlation observable.
  - **Outcomes:** realistic Class-0 amplitude → feasible-N visible ⇒ visibility fixed (old sub-floor =
    errors A+B); proceed to Step 2 to confirm. Class-0 caps it even at realistic amplitude ⇒ visibility
    needs Class-1/2 re-siting ⇒ Track 3. (This pins the "lag≥2 is second-order-small in amplitude·sensitivity"
    concern with a number.)
- **Step 2 (GPU confirm; scripted; predict-before-measure):** run the corrected observable on the EXISTING
  non-Pauli `emit` (shared-vs-off, amplitude sweep), confirm Step 1, measure the real `N_detect`.
- **Track 3 (conditional):** if Class-0 caps it → build the Class-1/2 ancilla-axis re-siting, re-measure.

**Track 2 — finish the non-Pauli side (infrastructure, around Track 1):**
- Two-switch interface (non-Pauli: coupled/uncoupled = existing `coupling_arm` shared/off, exposed
  cleanly); qutrit-leakage as backend value 3 (Da, phased).
- Axis-A baseline equivalence: non-Pauli off arm `==` QuTiP `mcsolve` + exact qutrit-DM (P0).

**Key ordering:** Track 1 Step 1 does NOT depend on Track 2 (it uses the existing closed form) — it is the
cheapest, most decisive first step; it prevents building infrastructure on the wrong error class.
**IMMEDIATE NEXT ACTION = Track 1 Step 1.**

## 6. RESOURCES ON HAND (the reuse map — REUSE, do not reinvent; from a 4-agent scout, 2026-07-04)

**Forward pipeline / source (the simulator under test):**
- `src/error_coupling_simulator/teachers/coupled_cycle.py` — `CoupledCycleTeacher`; `emit(regime,*,m,N,seed)
  -> {"det":(N,R*n_stab) uint8, "obs":(N,) uint8}` (isolation-clean; `truth` evaluator-only). Switch already
  there: `coupling_arm ∈ {shared, off, independent}`; `markovian_baseline()`→independent (EXCHANGEABLE null,
  do NOT use as the legitimacy null), `off_source()`→off (Θ(0), THE structural-zero null). `emit_clifford_slice`
  = `NotImplementedError` (Pauli seam absent — dropped). d3 fixtures 4q(n_stab=1)/5q(n_stab=2); m=0 only.
- `src/error_coupling_simulator/source/process.py` — `OneOverFDriftSource` (n_fluctuators=8, γ∈[0.005,0.5]/cycle
  geomspace, `amplitude_radns=1e-4` total 1/f drift, closed-form `analytic_psd`); `RTNSource` (single-fluctuator,
  exact autocorr `exp(-2γ|τ|)`). `MEMORYFUL_SHARED_SOURCES` whitelist.
- `src/error_coupling_simulator/source/coupling.py` — Θ fan-out `source_to_params`/`trajectory_to_params`
  (8 fields); `SourceCouplingConfig` (`z_scale_radns=1e-4`, `gamma_phi_base_per_ns=1/75000` Tφ=75µs,
  `gamma_phi_sensitivity=0.35`, …); `independent_baseline_trajectory_to_params` (the exchangeable G6 null);
  `parameter_series` / `cross_mechanism_correlation` (helpers). **γφ is the ONLY record-carrying knob in
  slice-1** (ζ-only record TV=4.3e-11 record-dead; γφ joint TV=5.77e-4). Channel baseline (NOT source-modulated)
  `G2_GAMMA_PHI_PER_NS = G2_GAMMA_1_PER_NS = 1/30000` (T2=T1=30µs) at `frontend/axis1_bridge.py:52-53` —
  physically grounded (matches the `full_error_coupling_prereg` mechanism catalog).

**The corrected OBSERVABLE (mostly built — for the classical slice):**
- `docs/twin_validation/gates/g6_ablation.py` — `spitz_p_ij(cube,lag)`, `s2_count_autocov(cube,lag)`,
  `s3_r3`, cluster-bootstrap SEs, planted-memory positive controls, `independent_gt_lag1_pij`. **This is the
  STEP-2 (empirical, on an emitted `{det,obs}` cube) path: change its comparison from shared-vs-markovian to
  shared-vs-OFF and focus lag≥2.** (Step 1 is a pure ANALYTIC closed-form sizing where the off arm's lag≥2
  is the identity 0 — no cube; keep the two stages' edits separate.)
- `src/qec_twin/hardware/pij.py` — `spitz_pij_exact` + `spitz_pij_delta_se` (canonical EXACT Eq.13 + SE;
  METRICS.md-ledgered; unify g6's local dup to this).
- `src/error_coupling_simulator/certify/core.py` — `Statistic.RR_CORR` (round-to-round Pearson) +
  `SPATIAL_CORR`; both = 0 for independent-bit foils; shared between emitted side + DM anchor; `certify_cells`
  controls-first (inert control ⇒ FAIL; zero-firing ⇒ FINDING). `types.py` `SCALAR_FUNC` names `p_ij`.

**The g6 CLOSED FORM (the template for Track 1 Step 1):**
- `docs/twin_validation/g6_null_model_rederivation_2026-07-03.md` — a-exact MA(1): off-arm `p_ij(lag1)=μ=
  p_ro+p_rs−2p_ro p_rs≈0.0149`, `p_ij(lag≥2)=0`; common-mode ~8.7e-5; markovian null exchangeable (~73%
  of shared lag-1 covariance at R=12); shared-vs-markovian second-order signal `N_detect∈[1.1e10,1.2e15]`.
- `outputs/twin_validation/g6_null_feasibility_from_constants.py` — the committed-constant analytic script
  (CPU, `ma1_identity_selfcheck`) = the TEMPLATE to fork for Step 1 (shared-vs-off, lag≥2, realistic amp).

**Independent ORACLE (non-circular, faithfulness of BOTH arms):**
- `src/error_coupling_simulator/certify/anchors/dm_oracle.py` — `DMOracleAnchor` (exact-DM RR_CORR feasible
  full-9q R≥2 via a pruned branch tree; det-rate ~0.12 prunes). `closed_form.py` — analytic RR_CORR via
  `E[d_r d_{r+1}]=p01·p10` (two routes cross-validate). `facade.py::certify_teacher` (auto DMOracle +
  StimClifford + CorruptStab). NOT `cross_mechanism_correlation` (same-engine).

**Genuine CP-divisible null (Tier-2 rigor upgrade — FROZEN, single-qubit toy):**
- `outputs/teacher_prereg/nm_divisibility.py` (RHP/BLP/`intermediate_map_cp`, `is_markovian`; `exp(-Γt)`⇒
  RHP=BLP=0 by theorem), `nm_source.py::motional_narrowing_rate` (Markovian LIMIT of the SAME 1/f source).
  Removed from live pkg 2026-07-03; revive/extend from single-qubit to the coupled teacher when Tier-2 is due.

**Non-Pauli SCALE LADDER (the "9 is only the oracle" story):**
- `src/error_coupling_simulator/carrier/exact/qutrit_dm.py` — exact qutrit-DM ORACLE, ≤9 qutrit
  (3^9=19683, 5.77 GiB/copy) = one d3 tile. **(carrier tree = under `error_coupling_simulator`, NOT
  `qec_twin`.)**
- `src/qec_twin/forward/scalable/sv_sampler.py` (+ kernel at
  `src/error_coupling_simulator/carrier/kernels/sv_traj_d3.cu`) — dense SV-MCWF, 3^n pure state; d3 (3^9)
  fits, d5 (3^25=13.5 TB) dead. ⚠ `sv_sampler.py`'s own docstring mis-refers to `forward/kernels/…`; the
  kernel is actually at `carrier/kernels/`.
- `src/qec_twin/forward/scalable/mps_forward.py` — `MpsLeakageForward` (ADR 0010): qutrit MCWF-on-MPS,
  bond `chi` truncated (`exact_chi(n)=3^ceil(n/2)`, `MpsTruncationLedger`); d3 exact → thin-strip d5; full
  d×d DEFERRED; d7 needs PEPS/boundary-MPS (2308.08186). **This is the scalable non-Pauli carrier.**
- `frontend/qutip_cuquantum_backend.py` + `axis1_qutip_cuquantum_probe.py` — QuTiP `mcsolve` open-system
  reference (≤4 qutrit probe) = the external non-Pauli equivalence anchor. `frontend/qutrit_leakage.py`,
  `mechanisms/qutrit_teachers.py`, `axis1_qutrit_leakage_oracle_certification_manifest` (leakage cert vs
  `leakage_channel_super`).

**Scripted-execution scaffold (reuse verbatim):** `outputs/run_*.sh` (`set -o pipefail`, pinned python,
`tee`, `${PIPESTATUS[0]}`→`python-exit`), `docs/twin_validation/gates/_gate_common.py`
(`round_delta_by_round` → (shots,δround,n_stab) cube, `cluster_bootstrap_se`, `write_evidence`/`content_hash`,
`emit_gate_result` → `GATE_RESULT <name> <verdict> <hash>`).

## 7. RETRACTED / VOID — do NOT trust or resurrect

- **G0-v2 FAIL / G6 "sub-floor"** conclusions do NOT stand (§1, error A). `g0_v2_effectsize.json` = the wrong
  observable (2-point TV). Their MACHINERY (g6_ablation, the closed form, controls, oracles) is KEPT — reuse it.
  **⚠ Supersession pointer:** the VOID 2026-07-03 handoff's banner still asserts these findings "STAND as
  simulator legitimacy results" — that sentence is **SUPERSEDED by §1; they do NOT stand** (the earlier
  session flip-flopped; error A is the final word). If you read that banner, ignore its "STAND" claim.
- **The 2026-07-03 "active-observation reconstruction"** = a scope error (imported the twin), REVERTED: its
  docs (`RECONSTRUCTION_active_observation_*`, `reconstruction_active_observation_prereg`) DELETED; the
  retraction notices removed; `HANDOFF_reconstruction_active_observation_2026-07-03.md` marked ⛔ VOID.
- **G0-quantum GO-CORNER-ONLY** — a **coherent-sector (commutator / `Im K`) closed-form sizing**, UNTOUCHED
  by errors A/B (which are about the *classical stochastic* sector). It is **neither retracted nor part of
  this classical-visibility redo**: parked, still PROVISIONAL, not re-scored here. **Error C NARROWS the
  scope of Prop IW-1 / G0-quantum (coherent sector only), it does NOT retract them.**
- **Pauli backend** shelved (§4).

## 8. Disciplines + environment (standing)

- **Theory-first / predict-before-measure** (prediction written before any run — Track 1 Step 1 IS this).
- **Scripted-execution** (committed runner + pipefail + tee + `python-exit` + `content_hash` + `GATE_RESULT`
  + `__main__` guard). **wsl `$` pre-expansion trap** ([[feedback-wsl-exit-code-quote-chain]]): run via a
  committed `.sh`, never inline in the `bash -c` string.
- **H6:** every `src/**`+`tests/**` change user-confirmed BEFORE commit; docs/outputs = normal flow.
- **GPU serial, no concurrent** on the live desktop; offload heavy to `ssh spark` (192.168.1.88, user
  ednovas, key ~/.ssh/spark_ed25519, [[reference-ssh-spark-compute]]).
- **≥3 disjoint builders + un-led reviewer** for heavy builds/runs; reviewer gets problem+goal+artifact only.
- **CODE_MAP:** one generated map covers `src/qec_twin` AND `error_coupling_simulator`; regen
  `python tools/gen_code_map.py` after any src change; hand-edit only `docs/code_status.json`.
- **RAG-first:** `python -m qec_twin.rag.store --query "..."` ([[reference-local-rag-reading-notes]]).
- **Adversarial self-verification:** facts only from committed-script printed evidence — do NOT relay
  memory as fact (this session's repeated failure mode; verify in-source).
- **Env:** `aiqec` conda; `wsl.exe -d ubuntu-f -- bash -c 'cd /home/cx/Document/AI_QEC/AI_QEC && export
  PATH=/home/cx/miniconda3/envs/aiqec/bin:/usr/local/cuda/bin:/usr/bin:/bin && python …'`. Full pytest exits
  134/139 from a benign teardown crash AFTER the summary — parse the summary; scope pytest to `tests/`.

## 9. Pointers

Design: `docs/twin_validation/simulator_legitimacy_direct_correlation_design_2026-07-04.md`.
g6 closed form: `docs/twin_validation/g6_null_model_rederivation_2026-07-03.md` +
`outputs/twin_validation/g6_null_feasibility_from_constants.py`. Kam Class-0 finding + realistic bracket:
`docs/twin_validation/h2_effectsize_g4_prereg.md §7.B/§7.C`. Memory:
[[feedback-simulator-is-goal-twin-is-next]] (scope + the three errors), [[feedback-simulator-not-decoder]],
[[project-coupling-nonmarkovian-is-the-contribution]], [[feedback-anti-toy-ground-truth-protocol]],
[[feedback-scripted-execution]], [[feedback-wsl-exit-code-quote-chain]], [[feedback-code-map-anti-forgetting]],
[[reference-local-rag-reading-notes]], [[reference-ssh-spark-compute]], [[project-coupled-cycle-teacher-build-state]].

## 10. IMMEDIATE NEXT ACTION

**Track 1 Step 1** — a committed ANALYTIC script computing a **NEW** closed-form `N_detect` for the
**absolute lag≥2 shared-vs-off** `p_ij`/`RR_CORR` vs source amplitude, with the Class-0-visible vs
needs-Class-1/2 verdict. **Reuse ONLY the source-sampling + MA(1) self-check scaffolding of
`g6_null_feasibility_from_constants.py` — DISCARD its `record_N_sizing`/verdict (that is the RETRACTED
shared-minus-markovian second-order sizing).** **Resolve open decision D1 (realistic-amplitude anchor)
with the user first**, or run the class-(c) sweep `amplitude_radns=1e-4 → γφ=1/30000 (T2=30µs)` and report
across it. No GPU, no mainline-src change (docs/outputs normal flow). Present the prediction to the user
before Step 2. This directly answers the session's original question: **is the non-Markovian error visible
on the syndrome, and at what source strength / error class.**
