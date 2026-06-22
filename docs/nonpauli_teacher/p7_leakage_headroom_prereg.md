# Phase ⑦ — binary-leakage decoding-headroom decision (pre-registration)

> **Status:** PRE-REGISTRATION (theory-first gate). DESIGN ONLY — this doc designs the decision run;
> it does NOT build the harness, edit mainline, or commit. Authored against the ANTI-TOY PROTOCOL
> (`docs/FAITHFULNESS_PROTOCOL.md`) and the METRICS.md epistemic-status ladder. Every quantitative
> item is tagged **(a) exact/theorem**, **(b) prediction-band**, or **(c) heuristic/gate**.
>
> **Decision ⑦ answers:** Is the binary-leakage decoding headroom **CAPPED** on the certified faithful
> d3 XZZX leakage teacher? Score = `gap-to-Bayes = LER(Pauli-DEM + frozen MWPM) − LER*(Bayes floor)`
> (+ `%ΔLER`) on the teacher's `(syndrome-history, logical)` shots. Capped ⇒ pivot to soft-readout;
> not capped ⇒ build the binary-leakage learner for this axis.
>
> **Certified upstream finding (machine-exact vs the raw circuit, P4a):** the real per-round DD echoes
> (mid-cycle transversal X + post-M transversal Y, `H·X·H = Z`) refocus the leaked population to
> `|2⟩(R) ~ 5e-4`, FLAT in R (`docs/nonpauli_teacher/p4a_within_cycle_model.md` §5–§6; the no-echo
> engine runs away to ~7e-2). This is the load-bearing physical input: the leakage that survives into
> the syndrome record is small and non-accumulating.

---

## 0. Theory-first prediction (registered BEFORE the run)

**Headline prediction P0 (b) — "small gap → capped".** On the certified faithful d3 XZZX leakage teacher,
at the registered central siting (θ=0.07, g_seep=0.09 ⇒ WG_L1≈2.34e-3, WG_L2≈9.05e-2, C_L>0), for
R∈{1,3,5}:

> the leakage-specific gap-to-Bayes is **small and does NOT grow with R**:
> `gap_leak(R) = gap_on(R) − gap_off(R) < τ_cap` with the registered cap
> **τ_cap = 0.2 percentage-points of LER (2e-3 absolute), AND `%ΔLER_leak < 5%`** at every R∈{1,3,5},
> AND `gap_leak(5) ≤ gap_leak(1) + τ_cap` (no opening with R).

**Physical reasoning behind the bet (the derivation that precedes the run).** The Pauli-DEM+MWPM decoder
is blind to leakage by construction (the foil). Its excess over the Bayes floor (misspecification Lemma 2,
`outputs/decoding_floor_derivation.md` §I.4) is `E_s[ |2η−1| · 1{m̂_DEM ≠ m̂_Bayes} ]` — the disagreement
region weighted by the true margin. Leakage can enlarge this region only through the `|2⟩` population that
(i) survives the DD refocusing into the syndrome/terminal record and (ii) the DEM cannot model. Since the
certified `|2⟩(R)` is ~5e-4 and FLAT (refocused), the leakage-induced disagreement mass is `O(5e-4)` per
round and does not accumulate, so the gap it opens is `O(10⁻³)` and R-flat → **capped**. The temporal-memory
channel a learner could exploit (leakage persisting across rounds) is exactly what the echoes kill.

**θ-sweep corollary P1 (b).** Sweeping leakage UP the registered grid (THETA_SWEEP × G_SEEP_SWEEP, and a
calibrated WG_L1∈{1e-3, 5e-3, and an OUT-OF-BAND stress 2e-2}), `gap_leak` grows **sub-linearly and stays
below τ_cap through WG_L1=5e-3 (the Miao band)**; we register the leakage level (if any) at which
`gap_leak` first crosses τ_cap as the **headroom-opening threshold θ\***. Prediction: θ\* lies ABOVE the
device band (WG_L1 > 5e-3), so the decision is "capped in the physical regime."

**Falsifiers (a miss is a FINDING, never silently re-read):**
- F1: `gap_leak(R)` exceeds τ_cap at any R∈{1,3,5} in-band → headroom is NOT capped → **build the learner**.
- F2: `gap_leak(R)` grows with R (slope > τ_cap from R=1 to R=5) → temporal-memory headroom exists →
  **build the learner** (this is the rung R=1 cannot show; §2).
- F3: θ\* falls inside the device band (WG_L1 ≤ 5e-3) → in-regime headroom → **build the learner**.

These are **(b) prediction-bands**: a miss is the registered finding. τ_cap and the 5% are **(c) decision
gates** (go/no-go thresholds), NOT premises. P0/P1 are PROVISIONAL until the run + the constraint-ledger
controls (§3) print green.

---

## 1. The machinery map (file:line — what is reusable, what is a gap)

### 1.1 Bayes floor `LER* = ½(1−TV(P₀,P₁))` — BUILT (reuse) ✅

- **Pure floor math** (engine-independent): `outputs/teacher_prereg/exact_floor_run.py:124`
  `total_variation(p0,p1)`, `:130 bayes_floor(p0,p1)`. Three closed forms (min-sum / TV / margin) all
  cross-checked; hand cases + 20k random instances (`outputs/decoding_floor_derivation.md` §I.3).
- **Exact R=1 floor from the teacher** (exact-by-enumeration, NO Monte-Carlo):
  `exact_floor_run.py:171 floor_from_engine`, `:204 floor_from_engine_with_channel`,
  `:229 run_swept_b_floor` (b-bracket), `:744 run_full_d3_floor(schedule, …)` — drives `QutritDM`
  over all 2⁸=256 joint syndromes on the full 3⁹ DM. Headline R=1 runner:
  `outputs/teacher_prereg/run_d3_floor.py` (registered Miao-band L1 sweep, b-bracketed).
- **Exactness proof** (the floor IS the exact integral over Kraus branches, not MC):
  `outputs/teacher_prereg/exact_floor_feasibility.py` — density-matrix projection `Tr[Π_s ρ]` ==
  full Kraus-branch sum to <1e-13; 3⁹ DM = 5.77 GiB fits the 5090 with headroom.
- **DEM-decoder-vs-floor decomposition theory** (the misspecification lemma; the entire "gap-to-Bayes"
  object): `outputs/decoding_floor_derivation.md` §I.1–I.4 (Theorem 1: ANY decoder LER ≥ LER*; Lemma 2:
  plug-in excess = disagreement-margin integral). **(a) exact, cold-reviewed sound.**

**Exact-small-R path vs large-R estimator (the load-bearing R>1 subtlety):**
- **R=1 (exact):** `P_m(s)` over 2⁸=256 syndromes is enumerated exactly from the 3⁹ DM
  (`run_full_d3_floor`); `LER* = ½(1−TV)` is **(a) exact-by-enumeration** given b.
- **R>1 (NOT a naive ½(1−TV) over 2^(8R)):** the syndrome space is 2^(8R) (R=3 → 2²⁴ ≈ 1.7e7;
  R=5 → 2⁴⁰), so `P_m(s)` is NOT estimable nonparametrically from finite shots (collisions vanish;
  the plug-in BC → 0, the lower bound goes vacuous — `decoding_floor_derivation.md` §II.3). The
  **correct R>1 floor characterization** (§II.2, the CORRECTED crux): `TV(R) → 1` (NOT 0) for distinct
  rounds; the Bayes ERROR decays as `e^{−C R}` (C = Chernoff information) toward PERFECT recovery, and
  the genuine nonzero per-round floor is `ε_d^floor = q` = the **undetectable-flip rate** (a logical
  fault producing an identical detector-record distribution). So at R>1 the floor estimator is NOT a
  TV over the full 2^(8R) space.

  **GAP (R>1 floor method — must be wired, §4):** the project has the R=1 exact floor and the *theory*
  for R>1, but **no committed R>1 floor estimator**. Two declared-bounded arms (§3 ledger item iv):
  (A1) **exact-DM R>1 floor on a feasible sub-register / small R**: chain the within-cycle DM oracle
  per round (`sv_sampler.apply_within_cycle_round` → `QutritDM.syndrome_distribution`, the SAME path the
  Gate-4 ladder enumerates R∈{2,3} at — `outputs/teacher_prereg/p4a_verify_wc_gate4_ladder.py:8`) to
  enumerate `P_m(s_{1:R})` exactly for R∈{2,3} on a reduced support, giving an exact `½(1−TV)` anchor;
  (A2) **decoder-sandwich at full R** (the always-honest UPPER side, `decoding_floor_derivation.md`
  §II.3 table): `LER* ≤ min over held-out decoders` — pairs with (A1)'s exact small-R lower anchor and
  the `e^{−CR}`/`q` extrapolation (a **(b)** band) to BRACKET the R∈{5} floor. The decision uses the
  bracket, never a point claim at large R.

### 1.2 Pauli DEM (the foil — leakage is NOT in it) — BUILT (reuse) ✅

- **DEM from a stim circuit:** `src/qec_twin/decoder/stim_dem.py:38 extract_dem_data(circuit, *,
  decompose_errors=True)` wraps `circuit.detector_error_model(decompose_errors=…)`.
- **Skeleton freeze + re-probability:** `src/qec_twin/hardware/dem_compose.py:331 load_skeleton(dem)`,
  `:432 with_probabilities(skel, probs)` (clamp [1e-6, ½−1e-6]).
- **How the DEM is built from the RAW circuit (ledger item ii):** for the leakage teacher there is NO
  shipped noisy `.stim` — the teacher is the qutrit DM/SV engine. The Pauli-DEM foil is built by
  `stim analyze_errors` on the **qubit-projected** d3 XZZX circuit at a matched Pauli noise level
  (DEPOLARIZE on the same CZ/data positions the WG leak slices sit on), i.e. the SI1000-style DEM the
  field would deploy. **The leakage is deliberately ABSENT from this DEM** (that is the foil). This DEM
  is built from the raw circuit, never from a parallel reduction of the leakage channel.

  **GAP (matched-Pauli-DEM construction — must be wired, §4):** a small adaptor that emits the qubit
  d3 XZZX DEM at the Pauli noise level matched to the teacher's leak rate (so `gap_off ≈ 0`, ledger
  item iii). Lives in OUR tree (baseline discipline: no edits to `external/`).

### 1.3 Decoders — MWPM BUILT (reuse) ✅; TN-MLD present but not wired

- **Frozen MWPM (pymatching, pinned 2.4.0):** `src/qec_twin/hardware/m4_decode.py:74 PYMATCHING_PIN`,
  `:183 build_matching(dem_like)` (`Matching.from_detector_error_model`, upstream defaults, no tuning),
  `:236 decode_dem(dem, dets) -> uint8[shots, n_obs]`, `:191 _normalize_dets` (explicit
  bit-packed↔bool). This is the **frozen baseline decoder** for the foil. Version/settings DECLARED:
  pymatching 2.4.0, `from_detector_error_model` defaults, no reweighting (the A3c two-pass path
  `:1799` is NOT used here).
- **Metrics (reuse):** `src/qec_twin/hardware/m4_report.py:507 pct_delta_lers(l_a,l_b) = 100·(l_b−l_a)/l_b`
  (Sivak convention, +=better), `:512 paired_shot_bootstrap` (paired-shot CI + Kish deff),
  `:580 mcnemar_exact`. The d7 +2.96% program's scoring template:
  `outputs/reest_dem/decode_score_heldout.py` (held-out decode of two DEMs → LER → %ΔLER → bootstrap +
  McNemar). **Reuse this scoring spine verbatim.**
- **TN-MLD:** present as the differentiable likelihood `src/qec_twin/forward/scalable/hypergraph_dem.py`
  (`HypergraphDemTNLikelihood`, `from_stim_dem`) but NOT a decoder; the cuda-qx TN-MLD is vendored
  reference only. **Not load-bearing for ⑦** (the foil is the Pauli-DEM+MWPM; the floor is the
  information-theoretic optimum, which already upper-bounds TN — `decoding_floor_derivation.md` §I.4).
  Optional sensitivity arm only.
- **Moment/Walsh re-estimation** (`outputs/reest_dem/moment_reestimator.py`): the +2.96% d7 program.
  **Not needed for the decision** (⑦ scores the FOIL DEM vs the floor, not a re-estimated DEM). It would
  be the *learner* if ⑦ returns "not capped" — out of scope here.

### 1.4 The certified teacher's output (shots → events → decode → LER) — BUILT (reuse) ✅

- **Within-cycle SV sampler (the certified faithful path):** `forward/kernels/sv_traj_d3_loader.py:223
  sv_traj_d3_wc(...)` (circuit-faithful per-CZ `exp(L/4)` op-schedule, the P4a within-cycle model);
  host driver `forward/scalable/sv_sampler.py` (`SvSampler`, `RunSpec`, `marshal_within_cycle`,
  `build_within_cycle_leak`). Availability gate: `sv_traj_d3_loader.available("c128")`.
- **Shot/packing format (§6 contract):** `packed_shot_bits` uint8 `[N, out_stride]`, shot-major;
  per shot `R·n_stab` syndrome bits packed **round-major then stab-order**, then `logical_flip` in the
  **trailing byte** (value 0/1, NOT bit-packed); `out_stride = ceil(R·n_stab/8) + 1`. `logical_flip =
  logical_parity(terminal data readout) XOR m` — the ISOLATION-respecting label (never m itself,
  contract §4). `norm_drift` `[N]` is the `|1−⟨ψ|ψ⟩|` diagnostic.
- **The existing shot→decode→LER flow to mirror:** `outputs/reest_dem/decode_score_heldout.py` —
  read packed detection events → `m4_decode.decode_dem(dem, dets)` → `LER = (preds XOR actual).mean()`
  → `m4_report.pct_delta_lers` + `paired_shot_bootstrap`. The teacher's `sv_traj_d3_wc` output unpacks
  into exactly the `(dets[N, R·n_stab], obs_flips[N])` arrays this flow consumes.

  **GAP (teacher-shots → detection-events adaptor — must be wired, §4):** a thin unpacker from the
  `sv_traj_d3_wc` packed buffer to the `(detection_events, obs_flips)` arrays `decode_dem` expects,
  PLUS the detector-vs-measurement convention bridge (the DEM is over stim DETECTORS = round-to-round
  XOR differences of the raw stabilizer record; the teacher emits raw per-round syndrome bits, so the
  adaptor must form detectors = consecutive-round XOR consistent with the matched DEM's detector
  definition). This is the single most error-prone seam → ledger item v + a deterministic positive
  control (§3).

### 1.5 Summary of GAPs to wire (none are new algorithms — adaptors + a driver)

| Gap | What | Where it lives | Risk |
|---|---|---|---|
| G1 | matched-Pauli-DEM builder (qubit d3 XZZX, leak-matched DEPOLARIZE) | OUR tree adaptor | low |
| G2 | teacher packed-shots → `(detection_events, obs_flips)` + detector convention | OUR tree adaptor | **high (the seam)** |
| G3 | R>1 floor estimator: (A1) exact-DM small-R/sub-register anchor + (A2) decoder-sandwich + (b) `e^{−CR}`/`q` band | new committed script reusing `apply_within_cycle_round` + `decode_dem` | medium |
| G4 | the ⑦ decision driver (orchestrates teacher → DEM+MWPM → floor → gap → θ-sweep) | new committed script | low (glue) |

---

## 2. The experiment design

### 2.1 Noise isolation (do())

**Two teacher arms, BOTH run (the leakage-specific gap is their difference — ledger item iii):**
- **`leak_on`:** leakage-ONLY do()-isolated teacher (WG `(θ, g_seep, g_heat)` on data qutrits, NO Pauli
  background) — the clean decision number. The `|2⟩` population is the only non-Pauli signal.
- **`leak_off`:** the SAME circuit with θ=g_seep=g_heat=0 (identity leak slice) — the Pauli/Clifford
  control. Must reproduce the matched-Pauli-DEM exactly (LER_off ≈ LER*_off ≈ matched-DEM LER).

**Decision number:** `gap_leak(R) = gap_on(R) − gap_off(R)`, where `gap_x(R) = LER_x(DEM+MWPM) −
LER*_x(floor)`. Subtracting `gap_off` removes any residual DEM-vs-floor gap from the Pauli substrate and
the detector-convention seam, ISOLATING the leakage contribution. **Justification:** a clean leakage-only
decision (the do()-isolated mechanism) is the headroom attributable to the non-Pauli axis; the
`leak_off` control proves the seam (G2) is faithful (gap_off ≈ 0). We ALSO report `leak + SI1000-Pauli
background` as a sensitivity arm (the realistic deployment), but the GO/NO-GO is on `gap_leak` from the
isolated arm (cleanest attribution).

### 2.2 Rounds R

- **R=1** — the exact Bayes-floor anchor (2⁸ enumerable via the DM oracle, `run_full_d3_floor`). Sanity:
  R=1 **cannot** show temporal-memory headroom (it lives at R>1 — `decoding_floor_derivation.md` §II.2),
  so R=1 alone cannot answer ⑦; it pins the floor exactly and validates the seam.
- **R∈{3,5}** — the temporal-memory rung (where leakage persistence would open headroom if the echoes
  did NOT refocus). The decision REQUIRES R>1. R=3 gets an exact-DM floor anchor on a feasible
  sub-register (A1); R=5 uses the decoder-sandwich + band (A2).

### 2.3 Bayes floor per R (method + epistemic class)

- **R=1:** exact `½(1−TV)` over 2⁸, b-bracketed (`run_full_d3_floor`). **(a) exact-by-enumeration given b.**
- **R∈{3}:** (A1) exact-DM enumeration of `P_m(s_{1:R})` on a feasible sub-register (chain
  `apply_within_cycle_round`; the Gate-4 ladder already does R∈{2,3} on reduced support). **(a) exact on
  the sub-register; (b) the full-9q value is bracketed by it.**
- **R∈{5}:** (A2) decoder-sandwich UPPER (`LER* ≤ min held-out decoder LER`, §II.3) + the small-R
  exact anchor extrapolated by the registered `e^{−CR}`/`q` form. **(b) prediction-band; declared NOT
  exact** (the large-R floor has no (a)-exact companion — §II.2 regime caveat; the naive ½(1−TV) over
  2^(8R) is WRONG and is NOT used).

**The large-R subtlety, restated for the pre-reg (ledger item iv):** the floor at R>1 is NOT
`½(1−TV(P₀^{(R)}, P₁^{(R)}))` naively estimated from finite shots — `TV(R)→1` and the plug-in is vacuous.
The genuine per-round floor is the undetectable-flip rate `q`; the distinguishable part decays as `e^{−CR}`.
We report the floor at R∈{3,5} as a **bracket** (exact small-R anchor + decoder-upper + band), never a
single MC number, and declare its class explicitly per R.

### 2.4 Baseline (the foil — version/settings declared, baseline discipline)

- **Pauli DEM:** built from the RAW qubit d3 XZZX circuit via `stim analyze_errors`
  (`circuit.detector_error_model(decompose_errors=True)`), DEPOLARIZE matched to the teacher's leak
  level on the CZ/data positions. **The leakage is NOT in the DEM** (the foil). stim version declared
  with the numbers.
- **Decoder:** frozen MWPM, **pymatching 2.4.0** (`m4_decode.PYMATCHING_PIN`),
  `Matching.from_detector_error_model` at upstream defaults, NO reweighting, NO tuning
  (`m4_decode.build_matching` / `decode_dem`). Frozen before any teacher shots are decoded.
- **Optional sensitivity:** TN-MLD (cuda-qx) and the moment/Walsh re-estimated DEM as upper-side
  comparators only (they cannot breach the floor — §I.4); NOT the GO/NO-GO baseline.

### 2.5 Metric (field-standard, METRICS.md ladder)

- **Primary: gap-to-Bayes** `gap = LER(DEM+MWPM) − LER*` (absolute, in LER units) — the
  `decoding_floor_derivation.md` object (Lemma 2 excess). Field-standard (model-free Bayes-error gap).
- **%ΔLER** (Sivak convention, += reduction): `m4_report.pct_delta_lers(l_a, l_b)` =
  `100·(l_b − l_a)/l_b`, reported as `%ΔLER(floor vs DEM)` = how much LER the optimum would remove.
- **Per-round LER** (Fowler convention): `1 − (1 − LER_total)^{1/R}` for the R-scaling view.
- **Uncertainty:** `paired_shot_bootstrap` (shot = iid unit, Kish deff) + `mcnemar_exact` on discordant
  pairs (the d7 program's exact apparatus). R=1 floor: exact-by-enumeration (no CI on the floor itself;
  the DEM LER carries the shot CI).

### 2.6 θ-sweep (registered leakage regimes — NOT pinned)

Registered grid (from `mechanisms/qutrit_teachers.py`, all (c) swept design constants):
`THETA_SWEEP = (0.0, 0.045, 0.07, 0.10)` × `G_SEEP_SWEEP = (0.05, 0.09, 0.10)`, plus calibrated
WG_L1 endpoints via `calibrate_theta_for_wg_l1`: **WG_L1 ∈ {1e-3, 5e-3 (Miao band), 2e-2 (OUT-OF-BAND
stress)}**. For each leakage level: `gap_leak(R)` at R∈{1,3,5}, b-bracketed. Output: the curve
`gap_leak vs WG_L1`, and the registered headroom-opening threshold θ\* (the WG_L1 at which `gap_leak`
first crosses τ_cap). The stress point brackets whether the gap opens at higher-than-device leakage.

---

## 3. The constraint ledger (Rule II — invariants + a falsifying test each)

> Each invariant has a falsifying test that MUST FAIL LOUDLY on a broken input (confirm it trips before
> trusting it — the protocol's core). These are gating tripwires (c), not premises.

| # | Invariant (MUST hold) | Falsifying test (must trip on a broken input) | Class |
|---|---|---|---|
| **i** | **Bayes-optimality:** ANY decoder LER ≥ the Bayes floor (Theorem 1). So `gap = LER(DEM+MWPM) − LER* ≥ 0` always. | A measured `gap < −ε` (ε = shot-CI half-width) ⇒ a BUG (floor over-estimated, decoder leakage, or a label/seam error). Positive control: feed the floor a decoder that intentionally violates MAP → its gap must be > 0 and large; feed the EXACT Bayes decoder (R=1, from the enumerated `P_m(s)`) → its gap must be 0 to <1e-9. A negative gap fires the tripwire. | (a) bound / (c) test |
| **ii** | **DEM from the RAW circuit, not a parallel model:** the Pauli-DEM foil is `stim analyze_errors` on the qubit d3 XZZX circuit, NEVER a Pauli reduction of the leakage channel (which could share the leak model's blind spot — circular verification). | Diff the DEM's error supports against the raw circuit's `analyze_errors` output byte-for-byte; assert the leak channel is ABSENT from the DEM (no |2⟩ DOF). Broken control: a DEM that secretly encodes the leak rate → the absence check fails. | (a) provenance / (c) test |
| **iii** | **Leakage-off control:** `gap_off = gap(leak_off) ≈ 0` (the Pauli substrate + the seam are faithful); the leakage-specific gap is `gap_leak = gap_on − gap_off`. `leak_off` ⇒ matched LER (LER_off ≈ matched-DEM LER to shot precision). | If `gap_off` is not ≈ 0 (within shot CI) the SEAM (G2) or the DEM match (G1) is broken — HALT, do not report `gap_on`. Positive control: a deliberately mis-matched DEM (wrong Pauli rate) → `gap_off` inflates and the tripwire fires. | (a)/(c) test |
| **iv** | **The Bayes floor's large-R epistemic class:** R=1 exact; R>1 floor is NOT a naive ½(1−TV) over 2^(8R) (TV→1, plug-in vacuous); the genuine per-round floor is the undetectable-flip rate `q`, distinguishable part `e^{−CR}`. R∈{3,5} floor reported as a bracket (exact small-R anchor + decoder-upper + (b) band), declared per R. | Compute the NAIVE plug-in `½(1−TV)` over the full 2^(8R) at R=5 and SHOW it goes vacuous (collisions → 0, BC → 0, bound → 0) — the registered direction tripwire (§II.4 control iv). If a run reports a single exact R=5 floor number, that is the bug (the large-R floor has no (a) companion). | (a)/(b)/(c) per §II.2–II.4 |
| **v** | **Metric conventions carried with the numbers:** gap in LER units (absolute); %ΔLER = `100·(l_b−l_a)/l_b` (Sivak, += better, `pct_delta_lers`); per-round LER = `1−(1−LER)^{1/R}` (Fowler); the detector convention (DEM over stim DETECTORS = round-to-round XOR; the teacher's raw per-round syndrome → detectors via the SAME XOR the DEM assumes). | A deterministic positive control: a teacher shot with a KNOWN single-fault syndrome history → the unpacked detection events must equal the hand-computed detectors AND `decode_dem` must return the hand-computed correction. A wrong XOR/endianness/round-order → the control mismatches and fires. (This is the G2 seam tripwire — the highest-risk seam.) | (a) identity / (c) test |
| **vi** | **CPTP + |2⟩(R) sanity (inherited P4a):** the leak slice is CPTP <1e-12 and composes (`‖exp(L)−(exp(L/4))⁴‖<1e-12`); the certified `|2⟩(R)~5e-4` FLAT (the refocused echo). The teacher used by ⑦ MUST be the certified within-cycle path (echoes IN), not the lumped/no-Y engine. | Assert the teacher run's `|2⟩(R)` matches the §5 table (within MC); a θ=0 incoherent control gives MONOTONE-rising |2⟩ (no refocus) — if the "faithful" teacher shows runaway |2⟩, the echo (X;Y) was dropped (the blood-bought pit). Re-uses `p4a_verify_wc_gate4_ladder.py` physics controls. | (a) exact / (c) test |

**Standing-ledger pits this run must NOT re-commit (from `FAITHFULNESS_PROTOCOL.md` Rule II):** (1) apply
every physical gate — the X echo AND post-M Y MUST be in the teacher (dropping the Y over-states |2⟩ ~10×);
(3) Clifford-invariant ≠ leakage-invariant — the echoes are detector-invariant but DECISIVE for the leak
trajectory; (6) underdetermined ⇒ bracket — b (leaked readout) and the R>1 instrument arm are SWEPT/
bracketed, never frozen to a "physical truth."

---

## 4. Declared + bounded simplifications (Rule III)

| Simplification | Declared class | Error bound vs the faithful version | Status |
|---|---|---|---|
| **S1 — R>1 floor method** (exact small-R/sub-register anchor + decoder-sandwich + `e^{−CR}`/`q` band, NOT exact full-9q R=5) | **(b) band** | Bounded BELOW by the decoder-sandwich upper (LER* ≤ min decoder LER, exact population) and ABOVE/anchored by the exact small-R DM enumeration; the gap between the bracket arms IS the reported uncertainty. The decision uses the bracket, never a point. | bounded ✅ (the bracket is the bound) |
| **S2 — noise isolation** (leakage-ONLY do() teacher for the headline; SI1000-Pauli-background as a sensitivity arm) | **(c) design** | `gap_leak = gap_on − gap_off` removes the Pauli-substrate gap exactly (same circuit, same DEM, same seam); the residual is the leakage-attributable gap. The SI1000-background arm bounds the realistic-deployment shift. | bounded ✅ (the off-control IS the bound) |
| **S3 — decoder freezing** (frozen MWPM pymatching 2.4.0 at upstream defaults; no reweighting/tuning) | **(c) design / baseline** | The frozen MWPM is a WEAK baseline (memory: Google's shipped corrMatch/RL-prior beat it); but for a FLOOR comparison the foil only needs to be Pauli-leakage-BLIND, which any Pauli DEM decoder is. Stronger Pauli decoders (TN-MLD) are upper-side sensitivity arms and CANNOT breach the floor (§I.4), so they only TIGHTEN the gap, never change the cap verdict's direction. | bounded ✅ (floor upper-bounds all of them) |
| **S4 — b (leaked readout) + R>1 instrument arm** | **(c) swept nuisance** | NOT pinned: b ∈ [0.5,1.0] bracketed (`LEAKED_READOUT_BIAS_SWEEP`); R>1 instrument arms A/C/B1/B2 reported as a sensitivity table (contract §4). The decision is robust across the bracket or it is flagged. | bracketed ✅ (no freeze) |
| **S5 — r01 geometry reused for R>1** (within-cycle interior streams from r10; stabilizer geometry from r01) | **(a) exact** (per P4a §1) | CZ-leak geometry reuse-stable r01↔r10 (9/9 nCZ identical, coordinate-keyed); only the round-boundary gate set (init-H / terminal-no-Y) is per-position handled. Inherited, already certified. | bounded ✅ (P4a-certified) |

**No unbounded simplification remains** (the protocol's STOP condition). The one genuinely band-class
item (S1, the R>1 floor) is bracketed by an exact small-R anchor + an exact-population decoder upper, so
its uncertainty is reported, not assumed away.

---

## 5. Build plan (what to wire; suggested agent split)

> Heavy-task rule (≥3 agents + a reviewer, disjoint ownership): this is an M3-scale build. NONE of the
> mainline changes — all four gaps live in OUR `outputs/` tree as committed scripts (the teacher,
> DEM machinery, MWPM, floor, and metrics ALL already exist; ⑦ is GLUE + a floor driver + a decision
> driver). No `src/qec_twin/**` edit ⇒ no commit-gate on mainline (docs/outputs follow the normal flow).

**Agent A — the seam adaptor (G1 + G2, the highest-risk piece).** `outputs/teacher_prereg/p7_seam.py`:
(a) the matched-Pauli-DEM builder (qubit d3 XZZX, `stim analyze_errors`, leak-matched DEPOLARIZE);
(b) the teacher packed-shots → `(detection_events, obs_flips)` unpacker + the detector-XOR convention
bridge. Deliverable INCLUDES the ledger-item-v deterministic positive control (a known single-fault shot
→ hand-computed detectors + correction) and the ledger-item-ii DEM-absence check. **This agent owns the
seam; brief it un-led with the raw circuit + the §6 packing contract + the goal, NOT the expected answer.**

**Agent B — the R>1 floor driver (G3).** `outputs/teacher_prereg/p7_floor_rgt1.py`: (A1) chain
`SvSampler.apply_within_cycle_round` → `QutritDM.syndrome_distribution` to enumerate `P_m(s_{1:R})`
exactly for R∈{2,3} on a feasible sub-register (reuse the Gate-4 ladder pattern), `½(1−TV)`; (A2) the
decoder-sandwich upper from held-out MWPM; (b) the `e^{−CR}`/`q` extrapolation to R=5. Deliverable
INCLUDES the ledger-item-iv direction tripwire (show the naive 2^(8R) plug-in goes vacuous).

**Agent C — the decision driver + θ-sweep (G4).** `outputs/teacher_prereg/p7_decision.py`: orchestrate
`leak_on`/`leak_off` teacher runs (within-cycle `sv_traj_d3_wc`) → matched DEM + frozen MWPM
(`decode_dem`) → `gap_on`/`gap_off`/`gap_leak` at R∈{1,3,5} → `pct_delta_lers` + `paired_shot_bootstrap`
+ `mcnemar_exact` → the θ-sweep curve + θ\*. Asserts P0/P1 against τ_cap and emits the GO/NO-GO verdict.
Reuses `outputs/reest_dem/decode_score_heldout.py` as the scoring spine.

**Reviewer — independent red-team (FAITHFULNESS_PROTOCOL Rule III.2).** Brief un-led (stage problem +
ultimate goal + the artifacts ONLY; omit the diagnosis/banked answers). Job: BREAK the seam against the
raw circuit (the highest-risk piece — does the detector convention match the DEM? does `gap_off ≈ 0`?),
verify the floor's epistemic class per R, and confirm every ledger tripwire trips on a broken input.

**Sequencing:** A (seam + controls) → must pass the ledger-v control + `gap_off ≈ 0` BEFORE B/C consume
it. B and C run in parallel once A's seam is green. Reviewer clears before any production-N (≥1e5 shots)
run. Gates 4–5 (DM convergence + throughput) already exist for the teacher; ⑦ adds the seam control +
the floor-bracket check.

---

## 6. Design forks needing the orchestrator's call

1. **R=5 floor — accept the band, or push exact-DM to R=5 on a smaller sub-register?** The exact-DM R>1
   anchor (A1) is feasible to R∈{2,3} on a reduced support; R=5 exact on the full 9q is infeasible
   (2⁴⁰ syndromes). The pre-reg defaults to the **bracket** (exact small-R + decoder-upper + band) for
   R=5. **Fork:** if the orchestrator wants an exact R=5 lower anchor, we can enumerate a 3–4-qutrit
   sub-register to R=5 (cheap) as an additional exact anchor — at the cost of a sub-register
   representativeness caveat. *Recommendation: take the bracket (it is honest and decision-sufficient);
   add the sub-register R=5 anchor only if the bracket straddles τ_cap.*

2. **Headline isolation arm — leakage-ONLY, or leakage + SI1000 background?** The pre-reg defaults the
   GO/NO-GO to the **leakage-ONLY do() arm** (cleanest attribution of the non-Pauli headroom) and reports
   the SI1000-background arm as sensitivity. **Fork:** if the orchestrator considers the realistic
   deployment (leak + Pauli) the decision-relevant number, we swap the headline. *Recommendation: keep
   leakage-only as the headline (the decision is about the NON-PAULI axis's headroom); report both.*

3. **Decoder strength for the foil — frozen MWPM only, or also TN-MLD as the GO/NO-GO baseline?** The
   pre-reg uses frozen MWPM (weak but Pauli-leakage-blind, which is all the floor comparison needs) and
   TN-MLD as an upper-side sensitivity arm. **Fork:** the memory notes plain MWPM is a weak baseline vs
   Google's shipped frontier — if the orchestrator wants the cap verdict to clear the SHIPPED frontier
   (not just MWPM), we promote TN-MLD/RL-DEM to the headline foil. *Recommendation: frozen MWPM for the
   decision (any Pauli decoder is ≥ floor; a small MWPM gap already proves "capped"); but if the decision
   is "not capped", re-run the foil at the shipped-frontier strength before building the learner (a
   not-capped verdict vs a weak baseline could be a baseline artifact, per the decoder-gate memory).*

---

## 7. Epistemic-status master table

| Item | § | Class |
|---|---|---|
| Bayes floor `LER*=½(1−TV)`, R=1 exact-by-enumeration | 1.1 | (a) exact |
| Theorem 1 (gap ≥ 0), Lemma 2 (gap = disagreement-margin integral) | 1.1 | (a) exact (cold-reviewed) |
| R>1 floor: TV→1, Chernoff `e^{−CR}`, per-round floor = `q` | 2.3 | (a) i.i.d. idealization / (b) on real data |
| R=3 exact-DM sub-register floor | 2.3 | (a) sub-register / (b) full-9q bracketed |
| R=5 floor (decoder-sandwich + band) | 2.3 | (b) prediction-band (NO (a) companion) |
| Pauli-DEM foil from raw circuit (leak absent) | 1.2, 2.4 | (a) provenance |
| Frozen MWPM pymatching 2.4.0, %ΔLER/per-round conventions | 1.3, 2.5 | (a) tooling pins |
| τ_cap = 2e-3 / 5% / no-R-growth gates | 0 | (c) decision gates |
| P0 (small gap → capped), P1 (θ\* above band) | 0 | (b) prediction-band |
| Noise isolation `gap_leak = gap_on − gap_off`; b/arm brackets | 2.1, S4 | (c) design / swept |
| All §3 falsifying tests | 3 | (c) tripwires |
| |2⟩(R)~5e-4 FLAT (certified upstream) | preamble, vi | (a) exact GIVEN (θ,g_seep) (P4a) |

**Provisional-conclusion note.** Every conclusion here except the tagged (a) theorems is PROVISIONAL:
usable for go/no-go gating, but nothing may be built on it until the run + the §3 controls print green and
the reviewer clears the seam. A falsifier (F1/F2/F3) firing is the registered FINDING (build the learner),
never re-read away.
