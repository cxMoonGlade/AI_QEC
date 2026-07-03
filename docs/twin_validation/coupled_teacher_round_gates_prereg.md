# PRE-REGISTRATION — CoupledCycleTeacher round: G0-v2 effect-size R-sweep + record gates G4–G8

**Date 2026-07-03. Status: REGISTERED (author lane, Builder 3) — written BEFORE any run;
an independent un-led reviewer sees this + the scripts before anything executes.**
Binds to: `docs/twin_validation/coupled_cycle_teacher_design.md` (THE SPEC; §4 G0, §6 gates,
§6b red-team), `docs/twin_validation/qec_coupling_simulator_build_contract.md` §C (gate
evidence objects) + §H bottom (corrqec anti-circular scope), `docs/twin_validation/
h2_effectsize_g4_prereg.md` §6/§7 (what H2 established: 2-point observable retracted;
G4 = decode-relevant ΔLER re-framed to faithfulness; ζ+γφ-on-data = Kam Class 0 = benign),
`docs/METRICS.md` (TV / Spitz p_ij / ΔLER / 1−F_e ledger rows), `docs/FAITHFULNESS_PROTOCOL.md`.

**Epistemic-class rule (METRICS.md, binding):** every quantitative item below is tagged
**(a) exact**, **(b) registered prediction band** (a miss is a FINDING, never later citable
as fact), or **(c) heuristic gate/decision rule** (go/no-go only; never a premise). Undeclared
⇒ (c).

**Amendment budget (c):** at most ONE amendment per gate, logged in §10 with date + reason;
any second amendment demand = a registered FINDING and a STOP for that gate. Standing
reviewer meta-rules carried: print the pileup fraction where a statistic pools events;
"χ²/NLL-in-band ≠ parameter accuracy" is printed wherever a fit is reported.

**Run order (ratified 2026-07-03):** G0-v2 (this doc §1) → teacher acceptance decision →
gate suite (§2–§7: fresh G2 re-run, then G4→G7, then the G8 runner object). G1/G3a/G3b are
NOT in this round's order and appear as explicit SKIPPED rows (§7), never silently.

---

## 1. G0-v2 — effect-size R-sweep (pre-build anti-toy gate, THE build gate)

Script: `outputs/twin_validation/g0_v2_effectsize_rsweep.py`; runner `outputs/run_g0_v2.sh`;
evidence `outputs/twin_validation/g0_v2_effectsize.json`.

### 1.1 Grounded context (verified in-source this session)

- G0-v1 (2026-06-30, `outputs/twin_validation/g0_zeta_gammaphi_effectsize.py`) measured, at
  R=2 on the 5q frontend fixture: representative record-TV = **5.77e-4** → N_detect ≈ 2.7e7
  (≫ 1e6 ⇒ FAIL, scope re-opened); ±3σ TV = 2.02e-3 → N ≈ 2.2e6; **ζ-only TV = 4.3e-11**
  (static-ZZ record-dead under realistic 1/f draws — faithful property, not a bug); PC2b
  ζ-liveness at the G2 magnitude TV ≈ 3e-3 (instrument live).
- The 5q fixture (`build_axis1_codespec_frontend_spec`): 3 data + 2 ancilla, checks x0
  (X on data 0, ancilla 3) + z1 (Z on data 1, ancilla 4), logical `logical_z2` (Z on data 2),
  finals {q0:X, q1:Z, q2:Z} ⇒ **measured bits M(R) = 2R + 3** (asserted in-run, not assumed).
- The enumeration engine branches unconditionally per measured bit
  (`measure_qubit_enumerate`: (B,dim,dim) → (2B,dim,dim); **no pruning**), so
  branches = 2^M exactly and resident memory = 2^M · (2^n)^2 · 16 B (c128).
- New 4q variant (in-script, same frontend API + compiler seal): 3 data + 1 X-check ancilla
  (check x0 identical, z1 dropped), same ZZ edge (0,3), same logical `logical_z2`. Data
  qubit 1 sits in no check/observable, so (grounded from `record_layout.final_measurements`)
  it gets NO final measurement ⇒ finals {q0:X, q2:Z} ⇒ **M(R) = R + 2**. Registered as a
  SEPARATE curve — no silent fixture swap (S2).

### 1.2 Statistic, points, N formula (v1-IDENTICAL — no re-registration)

- Statistic: exact record-distribution **TV** = ½·Σ|p_A − p_B| over
  `record_probabilities` from the UNCHANGED dense emitter
  `axis1_measurement_record_evidence_manifest` (two static param points = two
  compiler-sealed manifests). TV is the ledgered distribution-comparison metric
  (METRICS.md: "Comparing DISTINCT distributions … always uses the ledgered NLL / KL / TV").
- Param points: `source_to_params(±1·z_scale)` representative (the decision statistic);
  `±3·z_scale` wide point (reported). z_scale = 1e-4 rad/ns, γφ base = 1/75000 ns⁻¹,
  sensitivity 0.35 (the committed `SourceCouplingConfig` defaults, class (c) there).
- N formula (c, v1 verbatim): `N_detect = ceil((GATE_Z/TV)^2)`, GATE_Z = 3.0; worst-case
  p=½ variance bound (conservative upward). FEASIBLE_N = 1e6.
- PC1 zero-delta TV ≤ 1e-12 (a); PC2b ζ-liveness at the G2 magnitude
  (0.002324778563656447 rad/ns) TV > 1e-12 (a-scoped) — both per fixture at R=2.

### 1.3 R grids + grounded cost model (c)

| fixture | grid | attempt (OOM-as-data) | hard-skip (mem cap) |
|---|---|---|---|
| 5q (M=2R+3, dim 32, 16 KiB/branch) | R ∈ {2,3,4,6} (2 MiB…512 MiB) | R=8 (8 GiB resident; transient ~2–3×) | — |
| 4q (M=R+2, dim 16, 4 KiB/branch) | R ∈ {2,4,8,12,16} (64 KiB…1 GiB) | — | R=20 (16 GiB resident > cap) |

Declared caps (c): RESIDENT_ATTEMPT_CAP_GIB = 12.0 (predicted-resident hard-skip; protects
the live desktop); WALL_CAP_S = 600 per manifest (reported flag, not a skip). OOM inside an
attempted point is caught and recorded as a data row (OOM-as-routing), never a crash.
Wall time per manifest is measured and printed per point — it is the orchestrator's input
for the later teacher-emit batching decision (§2.4).

### 1.4 Registered predictions

- **P-G0V2-1 (b) — the β bet.** TV(R) = TV(2)·(R/2)^β with **β ∈ [0.5, 1.0]** per fixture
  (log-log LSQ fit over the fixture's completed points; fit requires ≥3 points).
  *Derivation bracket (written before the run):* treating the R rounds as accumulating
  near-independent per-round evidence with per-round flip mass q ~ γφ·t_round ~ 1e-3:
  (i) the product-measure/Hellinger argument gives TV ~ √R (β = 0.5) once R·q ≳ 1;
  (ii) the rare-event regime R·q ≪ 1 gives TV ≈ R·δq (β = 1, linear — the mass difference
  concentrates on the zero-flip record). The swept R (≤16) sits in R·q ≪ 1, so the interior
  expectation LEANS β→1; the 06-30 3-agent review claimed linear, the Hellinger-product
  argument gives sqrt — **the sweep decides**. Out-of-bracket β = registered FINDING
  (printed loudly; reported; does not by itself flip the verdict — the decision rule does).
- **P-G0V2-2 (b).** TV_4q(2) ∈ [0.5, 1.5]·TV_5q(2) (the dropped z1 check is a Z-basis
  stream carrying ~no γφ signal; the finals differ by one bit).
- **P-G0V2-3 (a).** PC1 per fixture: zero-delta TV ≤ 1e-12.
- **P-G0V2-4 (a-scoped by the v1 measurement).** ζ-only representative-delta TV ≤ 1e-9 at
  R=2 per fixture (record-dead; v1 measured 4.3e-11) AND PC2b liveness TV > 1e-12 per
  fixture (else the deadness statement is an inert-instrument artifact).
- **P-G0V2-5 (c) — THE DECISION RULE.** Qualifying point = {status ok, N_detect(rep) ≤ 1e6,
  enumeration inside the declared caps}. Chosen (fixture, R\*, N\*) = the qualifying point
  minimizing the projected emit cost N_detect × wall_per_manifest; tie → smaller R.
  **NO qualifying point ⇒ G0-v2 FAIL ⇒ STOP** (no teacher acceptance; orchestrator reports
  to the user). The chosen triple becomes the slice design constants consumed by §2–§6.
- **P-G0V2-6 (c).** v1 anchor reproduction: |TV_v2(5q,R=2,rep)/5.77e-4 − 1| ≤ 5e-3
  (anchor-verdict reuse rule: the committed v1 number is re-derived before reuse).
- **P-G0V2-7 (a; tolerances declared (c)).** From-scratch ground truth at (4q, R=2, rep
  pair): an independent numpy/scipy **CPU** branch enumeration — own operator embedding
  (entrywise bit-gather construction), own projectors, own reset Kraus {|0⟩⟨0|, |0⟩⟨1|},
  own X-basis rotation, own XOR, own TV — reproduces both record distributions with
  per-record |Δp| ≤ 1e-10 and |ΔTV| ≤ 1e-10. Its NEGATIVE control (drop applied-layer 0)
  must diverge with max|Δp| ≥ 1e-8 (self-test against a vacuous GT). **Declared
  shared-input boundary:** the compiler schedule, the selection plan, and the
  per-selection joint-channel assembly are shared (each independently certified elsewhere:
  compiler seal + coverage ledger + G2/qutip-oracle certs); the check certifies the
  ENUMERATION/RECORD layer (state threading, branching, projection, reset, rotation, XOR,
  normalization, TV).
- **P-G0V2-8 (a).** Every manifest: total-probability residual ≤ 1e-8 and
  record_count == 2^M with the fixture's M(R) formula asserted (5q: 2R+3; 4q: R+2).

### 1.5 Derived N(R) decision tree (b — consequences of P-G0V2-1/2, written before the run)

Anchored at TV_5q(2) = 5.77e-4 (v1) and TV_4q(2) ≈ TV_5q(2) (P-G0V2-2):
N(R) = N(2)·(2/R)^{2β}, N(2) ≈ 2.7e7.

| scenario | 5q (R ≤ 8) | 4q (R ≤ 16) | expected decision |
|---|---|---|---|
| β = 1 (linear) | N(6) ≈ 3.0e6, N(8) ≈ 1.7e6 — no qualify | N(12) ≈ 7.5e5 ✓, N(16) ≈ 4.2e5 ✓ | PASS via 4q, R\* ∈ {12,16} |
| β = 0.5 (sqrt) | no qualify | N(16) ≈ 3.4e6 — no qualify | **FAIL ⇒ STOP** |

So the β bet is decision-relevant, not decorative: β near the sqrt endpoint kills the slice
at feasible N and the registered STOP fires. The 5q fixture is EXPECTED to never qualify
(registered expectation, part of P-G0V2-1's interior lean); if it does, that is a finding.

### 1.6 Verdict rule (c)

PASS ⇔ (chosen point exists) ∧ (PC1 ∧ PC2b ∧ ζ-dead per fixture) ∧ (v1 anchor) ∧
(from-scratch GT + its negative control). β/ratio misses = FINDINGS (reported).
Smoke mode (`--smoke`): R=2-only grids; verdict = machinery-only (controls + GT + anchor;
the qualifying-point requirement is NOT evaluated); evidence → `*_smoke.json`,
GATE_RESULT tag suffixed `_SMOKE` — never the gate evidence.

---

## 2. Gate-suite common protocol (G4–G8)

Scripts: `docs/twin_validation/gates/{g4_imprint,g5_baseline,g6_ablation,g7_isolation,
run_gates}.py` (TRACKED); runner `outputs/run_gates_suite.sh`; per-gate JSON evidence next
to each script. Every gate: module docstring binding this prereg, precondition asserts,
printed evidence, per-check dicts, verdict, `check_class` self-classification
(`GENUINE | VACUOUS-<reason>` per check — memory: scrutinize-vacuous-checks), content_hash,
one `GATE_RESULT <gate> <verdict> <hash>` line, `__main__` guard, repo-root sys.path shim.

### 2.1 Run config seam (c)

G4–G7 REQUIRE `--config <path>` (default `docs/twin_validation/gates/gate_run_config.json`),
authored by the ORCHESTRATOR after G0-v2 (it carries G0-v2's chosen triple). Schema:

```json
{
  "schema": "qec_twin.gates.coupled_teacher_gate_run_config.v1",
  "fixture": "4q | 5q            (G0-v2 chosen)",
  "R_star": 0, "N_star": 0,
  "shots_per_trajectory": 1,
  "m": 0,
  "seeds": {"shared": 101, "markovian": 202, "off": 303},
  "teacher_factory": "qec_twin.mechanisms.coupled_teachers:CoupledCycleTeacher",
  "teacher_kwargs": {},
  "corrqec_root": null,
  "n_lags": 4,
  "bootstrap": {"B": 200, "seed": 777},
  "g6_n_override": null,
  "g7_n": 64
}
```

**STATED ASSUMPTION A-CFG-1** (flagged to the reviewer): the teacher is constructed by
importing `teacher_factory` ("module:callable") and calling it with `**teacher_kwargs`;
Builder 2 / the orchestrator guarantees the kwargs encode (fixture, R\*). The gates verify
consistency structurally (det width B == R\*·n_checks; n_checks: 4q→1, 5q→2) and fail
loudly with the observed shapes otherwise.

### 2.2 Pinned teacher interface (assumed per the builder brief)

`CoupledCycleTeacher.emit(regime, *, m, N, seed) -> {"det": (N,B) uint8, "obs": (N,) uint8}`
(+ optional `"marg"`), `.markovian_baseline()`, `.off_source()`, `.truth` (evaluator-only),
`.sched`, `.channels()`. `regime = qec_twin.audit.certify.Regime(R=R_star,
register="subregister", n_active=<fixture qubits>, n_stab=<n_checks>)`. Emit at fixed seed
is deterministic (checked by G7; consumed by G4/G5/G6 re-emitting the same arms).
**STATED ASSUMPTION A-DET-1:** det columns follow the schedule `record_layout_ref`
detector order (round-major `delta:` rows then `final:` rows); the gates READ
`teacher.sched.record_layout_ref["detectors"]` and build the (check, round) column map
from it — the assumption is only that emit uses that same order; column-count mismatch
fails loudly.

### 2.3 Registered seeds + arms (c)

Arms: shared = teacher; markovian = `.markovian_baseline()`; off = `.off_source()`.
Emit seeds: shared 101, markovian 202, off 303; `m = 0`. Bootstrap seed 777, B = 200.

### 2.4 Batching + cluster-aware inference (c; red-team R6)

Default one-trajectory-per-shot (S = `shots_per_trajectory` = 1). Because one inner exact
enumeration per trajectory costs wall(R\*) (measured by G0-v2), the orchestrator MAY set
S > 1 (declared in config; recorded in every gate JSON; expected also in teacher truth).
All registered statistics here are WITHIN-shot (cross-round / det↔obs / per-shot decode),
so sharing a trajectory across S shots does not distort them; ALL standard errors use a
**trajectory-cluster bootstrap** (clusters = consecutive S-blocks of shot indices), which
degenerates to a shot bootstrap at S = 1. Registered floor (c): number of clusters
n_traj = N_run/S ≥ 2000; a config violating this fails the gate preconditions.

### 2.5 GENUINE-vs-VACUOUS self-classification

Every gate JSON carries `"check_class": {"<check>": "GENUINE|VACUOUS-<reason>"}` — the
author's declaration of whether the check CAN fail, has an informative regime, and has an
independent reference. A check classified VACUOUS is never counted toward a PASS.

---

## 3. G4 — record-imprint faithfulness (decode-relevant ΔLER + corrqec cross-check)

Script `gates/g4_imprint.py`; evidence `gates/g4_imprint.json`. N = N\* per arm;
arms shared (seed 101) + markovian (seed 202).

### 3.1 Observable (contract §C-G4, H2 §7.A registered form)

ΔLER = LER(frozen matched-marginal Pauli DEM decoding SHARED records) − LER(same frozen DEM
decoding MARKOVIAN-baseline records). LER per arm = mean(pred ≠ obs) under
`hardware.m4_decode.decode_dem` (frozen PyMatching path, upstream defaults). SE via the
§2.4 cluster bootstrap; z = ΔLER/SE.

### 3.2 Matched DEM construction (correlation-blind by construction)

From the PUBLIC fixture geometry only (the same CodeSpec builder as G0-v2 at R\*, WITHOUT
teacher metadata) → `compile_code_spec` → `CircuitIRSource(...).compile(noise)` →
noisy stim circuit → `circuit.detector_error_model(decompose_errors=True)`.
Noise placement (declared (c)): `X_ERROR(p)` before every ancilla round measurement and
before every final data measurement (per-instruction `target_filter`). Matching rule:
p = ½·(1 − √(1 − 2·d̄)) with d̄ = pooled round-delta detector rate of the SHARED arm —
(a)-exact inverse of d = 2p(1−p) ON the declared i.i.d.-flip model class; the placement +
pooling are the (c) parts. Per-detector matched-vs-empirical residuals are REPORTED
(no bar — the DEM is a correlation-blind foil, not a fit).
**Two-tier L0 rule (declared):** the finals noise gives the DEM an observable-flipping
mechanism (`error(p) L0`, detector-less on the idle logical qubit). If the frozen
PyMatching build REJECTS the detector-less L0 mechanism, fall back to the ancilla-only
DEM, record `dem_can_flip_observable = false`, and mark the decode-delta sub-check
`check_class = VACUOUS-structural(pred≡0 ⇒ LER reduces to the raw obs-rate difference)` —
reported honestly, and the raw obs-rate delta is then the reported record statistic.

### 3.3 Registered predictions

- **P-G4-1 (b).** ΔLER ∈ 0 ± 3·SE_boot. Basis: the slice-1 coupling (ζ+γφ on data) is Kam
  Class 0 = decode-benign (H2 §7.B); ζ is record-dead (G0-v1); readout/reset held at
  trajectory-mean is arm-constant; additionally on these fixtures the Z-logical on an idle
  data qubit is dephasing-invariant (a). Outside the band ⇒ registered FINDING — **reported,
  never a gate FAIL** (the brief's "sub-floor at mild 1/f is a FAITHFUL property").
- **P-G4-2 (a/c).** Pooled matched-rate identity holds by construction (a on the pooled
  statistic); per-detector residuals reported (no bar).
- **P-G4-3 (b) — the genuine marginal tooth.** The markovian baseline preserves one-field
  marginals ⇒ pooled det-rate difference shared-vs-markovian |z| < 3. A miss ⇒ G4 FAIL
  (it means the negative-control arm is mis-built — red-team R1/R3 territory).
- **P-G4-4 (b/c) — corrqec cross-check, contract §H scope (binding).** Scope = the
  Pauli/temporal-mask layer ONLY; corrqec can NEVER verify the analog joint-L teacher
  (that is G2 + the channel oracles). corrqec is NOT vendored: with `corrqec_root` absent
  the gate emits `corrqec_crosscheck: "DEFERRED(not vendored)"` — honestly reported, does
  NOT fail the gate (c). When the orchestrator vendors github.com/jkfids/corrqec (pristine,
  declared commit) and provides the root: generate temporal-mask correlated-Pauli records
  matched to the teacher's γφ channel on (pooled det rate, lag-1 p_ij) and compare det rate
  + lag-2..4 Spitz p_ij within |z| < 3 each (b) — match 2 moments, test the rest. NEVER
  compared to our own generator (anti-circular). Adapter mismatches are reported as
  `DEFERRED(adapter-mismatch: …)` with the discovered package structure printed.
- **P-G4-5 (a-structural).** dem.num_detectors == B; num_observables == 1; arm shapes/dtypes.

Verdict: PASS ⇔ structural ∧ P-G4-3 ∧ (P-G4-4 PASS or DEFERRED) ∧ the ΔLER report complete
with class tags. ΔLER magnitude never gates.

---

## 4. G5 — record-level comparator panel (reporting discipline; NO novelty bar)

Script `gates/g5_baseline.py`; evidence `gates/g5_baseline.json`. Records: shared arm at
N\* (seed 101), on the round-delta detector stream.

- Comparator (a): **best-converged Markov-k** fit of the per-check delta-bit stream:
  empirical order-k transition probabilities, Laplace smoothing α = 0.5 (c), fitted on a
  50/50 TRAJECTORY-level split (seeded), scored as held-out per-bit NLL (nats — the
  ledgered held-out NLL row) over interior rounds r > k. k = 0,1,…,6.
  **Convergence criterion (c, P-G5-1):** smallest k\* with ΔNLL(k\*→k\*+1) < 3·SE(ΔNLL)
  (paired trajectory-bootstrap); none by k=6 ⇒ comparator REJECTED loudly ⇒ **G5 FAIL**.
- Comparator (b): **finite-memory k=0 null** — per-round marginal-matched independent
  bits (round-resolved marginals; labeled "reporting-only", never a novelty rival).
- Comparator (c): **matched-record surrogate** = the markovian_baseline arm records
  (seed 202) — no tractable likelihood; statistic deltas only (stated).
- Reported per comparator: held-out NLL ((a),(b)); Spitz p_ij + count-autocovariance at
  lags 1..4 computed on comparator records (synthetic sample n = N_run for (a),(b), seeded)
  minus the shared-arm values, each with cluster-bootstrap SE and (a/b/c) class.
- **P-G5-2 (b).** Converged k\* ≤ 4 at N_run (per-step NLL gain of the long-memory source
  shrinks below noise quickly at these rates); a miss is a FINDING.
- **P-G5-3 (a-structural sanity).** NLL(k\*) ≤ NLL(k=0) + 3·SE (the fit is not worse than
  the null beyond noise).
- Printed caveats: "NLL/χ²-in-band ≠ parameter accuracy"; pileup fraction (q̂/2 proxy, §5.5).

Verdict: PASS ⇔ (a) converged ∧ all three comparators declared + reported with classes.
Small/zero deltas are FINDINGS, not failures.

---

## 5. G6 — record-level coupling FAITHFULNESS REPORT (Axis-2; re-registered 2026-07-03)

Script `gates/g6_ablation.py`; evidence `gates/g6_ablation.json`. Three arms at N_run
(= N\* or `g6_n_override` ≤ 1e6): shared (101) / markovian (202) / off (303).

**RE-REGISTRATION NOTICE (amendment G6-A1, §10; done BEFORE any G6 run — predict-before-measure).**
The original §5 (pass/fail discriminative gate on the raw Spitz-p_ij / count-autocov z-scores) was
proven — from committed constants, before any run — to be unsatisfiable on a *correct* teacher.
Derivation + committed-constant evidence:
`docs/twin_validation/g6_null_model_rederivation_2026-07-03.md` +
`outputs/twin_validation/g6_null_feasibility_from_constants.py` (run 2026-07-03, `python-exit=0`).
The four proven facts (all reproduced from committed constants, the a-class one with a from-scratch
i.i.d.-bit self-check):

1. **(a-exact) The delta stream is MA(1).** `D_{c,r} = m_{c,r-1} ⊕ m_{c,r}` shares the measured
   bit `m_{c,r}` with `D_{c,r+1}` (`record_layout.py:110-135`). Under i.i.d. rounds (the `off` arm)
   the pooled Spitz **`p_ij(lag1) = μ = p_ro + p_rs − 2 p_ro p_rs = 0.0149`** (NOT 0), and
   `p_ij(lag ≥ 2) = 0` exactly. So §5.4-old "Off ≈ 0 exactly" is FALSE and the old C3/C4
   "flat (|z|<3)" clauses read `|z| ≈ 15` at N=1e6 — unsatisfiable.
2. **(b) A trajectory-mean-instrument common-mode** ≈ `8.7e-5` sits at ALL lags in BOTH `shared`
   and `markovian` (permutation-invariant), ~10³× the memory signal; it cancels only in the
   difference.
3. **(c) The markovian permutation is EXCHANGEABLE, not independent:** at R=12 it retains
   `0.727` of the shared lag-1 covariance — the old C3 two-clause test is jointly strained.
4. **(d) The genuine memory discriminator (shared vs markovian) is second-order** in the small
   γφ-only per-round rate modulation (ζ record-dead, readout/reset at trajectory mean), giving
   `N_detect ∈ [1.1e10, 1.2e15]` across `τ_eff ∈ [50,1000] ns` — `≫ 1e6` by 4–9 orders.

The sub-floor record imprint of **mild 1/f** is a **FAITHFUL property, not a failure** (consistent
with G0-v1, H2's `ζ+γφ = Kam Class 0`, the build-contract G4/G6→faithfulness reframe, and the
scope that the classical 1/f slice is scaffolding while the contribution is the coherence sector).
G6 is therefore re-registered as a **faithfulness report**: reproduce the derived record structure
+ honestly report the sub-detectable memory imprint. No clause requires the infeasible memory
discrimination; the memory magnitude never gates (as with G4's ΔLER).

### 5.1 Registered statistics (unchanged definitions; declared null values added)

- **S1 — the LEDGERED Spitz p_ij** (METRICS.md DEM-edge row, exact Eq. 13):
  `p̂_ij = ½ − √(¼ − cov(x_i,x_j)/(1 − 2⟨x_i⊕x_j⟩))` for timelike pairs
  (i,j) = (delta(c,r), delta(c,r+ℓ)), ℓ ∈ {1..4}, pooled over r and checks c (per-pair retained).
  Validity domain enforced (denom > 0, √-arg ≥ 0; invalid flagged+excluded+counted). Two-point
  hyperedge blindness stated (Takou–Brown). **Declared null (a):** off-arm `p_ij(lag1) = μ_c`
  (Z-check `= p_instr = 0.0149`; X-check `= p_instr + O(0.5 γφ_base τ_eff)`), `p_ij(lag ≥ 2) = 0`.
- **S2 — lag-ℓ autocovariance of per-round detector counts:** D_r = Σ_c x_{c,r};
  ĉ_ℓ = mean over r of Cov_shots(D_r, D_{r+ℓ}), ℓ ∈ {1..4}. **Declared null (a/b):** off-arm
  ĉ_1 ≠ 0 (MA(1)), ĉ_{ℓ≥2} = 0; shared & markovian carry the common-mode `≈ 8.7e-5` at all lags.
- **S3 — cross-mechanism r3 = Pearson_shots(Σ_r D_r, obs)** (the ζ-witness): obs (Z on an idle data
  qubit) is dephasing-invariant (a) and could co-move with the γφ-carried det stream only through
  a ζ-mediated channel (record-dead, G0-v1) or a per-round-varying readout/reset instrument
  (excluded by trajectory-mean scoping) ⇒ registered ≈ 0 all arms. Degenerate: Var(obs)=0 ⇒
  r3 := 0 + flag `degenerate_obs_constant`.
- SEs: §2.4 trajectory-cluster bootstrap (B=200, seed 777). Primary lag = 1; lags 2..4 reported.

### 5.2 Registered predictions + PASS conditions (report, not discriminate)

Feasible, GENUINE checks (each has a falsifiable regime + an independent reference):

- **R-G6-A (a-exact) — off-arm MA(1) closed form.** off `p_ij(lag1)` matches the declared per-check
  `μ_c` within 3·SE (Z-check to `p_instr = 0.0149`; X-check to `p_instr + O(0.5 γφ_base τ_eff)`),
  AND off `S1/S2(lag ≥ 2)` consistent with 0 within 3·SE. Independent reference: the closed form
  (derivation §2) + the from-scratch i.i.d.-bit self-check. **Replaces the old C4.** A wiring bug
  (wrong fold / non-independent rounds) breaks it.
- **R-G6-B (a-exact) — MA(1) 1-dependence.** off `|z(S2@lag1)| ≥ 3` (nonzero lag-1) AND off
  `S2(lag ≥ 2)` consistent with 0 — the moving-average signature.
- **R-G6-C (b) — common-mode equality.** `shared` and `markovian` agree at lag ≥ 2 within 3·SE_diff
  (permutation-invariance of the ≈ 8.7e-5 common-mode). Genuine check that `markovian_baseline`
  preserves marginals + common-mode; a mis-built control diverges. **Replaces the old C3's
  "markovian flat" intent.**
- **R-G6-D (b) — REPORTED sub-detectability, NEVER gated.** The shared−markovian memory
  autocovariance (S2 difference at lag ≥ 2) is reported with its cluster-bootstrap SE alongside the
  derived `N_detect ∈ [1.1e10, 1.2e15]` (τ bracket). Expectation: consistent with 0 at N ≤ 1e6 (the
  faithful sub-floor). A surprise |z| ≥ 3 here at N ≤ 1e6 would be a FINDING (reported, not a fail —
  it would mean the imprint is larger than the second-order derivation predicts).
- **C1 (kept) — R1 positive control.** From truth: per-cycle γφ varies across rounds (spread > 0)
  for ≥ 90% of the exposed param-sample shots, AND `cross_mechanism_correlation(zz_zeta_radns,
  gamma_phi_per_ns) ≥ 0.9` on a shared-arm truth trajectory. **A-G6-1:** truth key spellings from a
  declared candidate list; unresolvable ⇒ loud FAIL printing `sorted(truth.keys())`. Independent of
  the record-N problem (reads the fan-out, not the records).
- **C5 (kept) — ζ-witness.** |z(r3)| < 3 in ALL three arms (or degenerate-flagged).
- **P1 (FIXED) — pipeline null.** Synthetic i.i.d. **measured bits** `~ Bernoulli` at the shared
  arm's per-(c,r) implied bit rate, XORed into deltas (reproducing the MA(1) floor), run through the
  SAME pipeline: the shared−off **difference** at lag 1 and all lag ≥ 2 z-scores must read `|z| < 3`
  — the pipeline must not manufacture correlation ABOVE the MA(1) floor. (The old P1 drew i.i.d.
  *delta* bits — the wrong null; it missed the whole MA(1) structure.)
- **P2 (RELABELED) — common-mode sensitivity control.** The planted per-shot common-rate multiplier
  `exp(g), g ~ N(0, 0.5²)` IS a common-mode; P2 confirms the pipeline detects a common-mode latent
  (`|z| ≥ 5`). Declared: this validates common-mode sensitivity, NOT memory discrimination.
- **P3 (NEW) — planted-MEMORY positive control.** Synthetic records with an AR(1)-correlated
  per-round rate at an INFLATED amplitude (c constant, sized detectable), compared to its
  per-round permutation via the shared−markovian **difference** statistic: `|z| ≥ 5`. Validates that
  the difference machinery CAN detect memory when the amplitude is large enough — then §5.3 notes
  the real teacher's amplitude is sub-floor. Falsifies a difference statistic that is blind to
  memory by construction.

**Verdict rule (c):** PASS ⇔ R-G6-A ∧ R-G6-B ∧ R-G6-C ∧ C1 ∧ C5 ∧ P1 ∧ P2 ∧ P3 ∧ (the §8.2 L6
independent-GT lag-1 algebraic-identity check, a-exact). R-G6-C is CONDITIONAL — it gates only when
the common-mode is detected in the shared arm (S2 lag≥2 |z| ≥ 3); when the common-mode is
sub-detected at the chosen N it is VACUOUS-power (reported, does not block PASS). R-G6-D is REPORTED
(never flips the verdict). No clause requires the infeasible memory discrimination; the memory
imprint magnitude never gates.

### 5.3 Feasibility note (the honest finding — REPORTED, class b)

The memory discriminator was sized before the run (derivation §6): `N_detect ∈ [1.1e10, 1.2e15]`
(conservative, single pooled statistic) across `τ_eff ∈ [50, 1000] ns`; even the OPTIMISTIC corner
(pool all lag-1 pairs, `τ = 1000 ns`) bottoms at `~2.4e8`, still ≥240× the 1e6 cap (you would need
an unphysical `τ_eff ≈ 3000 ns` to reach ~3e6). ≫ the cap by 2–9 orders — because matched marginals
force the discriminator to second order and mild 1/f makes it tiny, while a permutation-invariant
common-mode (≈ 8.7e-5, ~10³× larger) cancels only in the difference. Independently reconciled by an
un-led adversarial re-derivation (`N ∈ [2.4e8, 6e10]`, its optimistic-pooled bracket). This is the registered FINDING: **the
record-level cross-cycle memory imprint of the slice-1 mild-1/f source is sub-detectable at feasible
N — a faithful property.** The coupling is certified at the CHANNEL level (G2) and in the source
truth; it is NOT claimed to be record-discriminable at this amplitude. (The old §5.3 "one-time re-run
at 1e6" amendment path is retired — subsumed by this reframe; G6's single amendment is this
re-registration.)

### 5.4 Registered expectations per arm (a/b) — CORRECTED

- **Off:** `p_ij(lag1) = μ ≈ 0.0149` (structural MA(1), a-exact), `p_ij / S2 (lag ≥ 2) = 0` exact;
  S3 ≈ 0.
- **Markovian:** MA(1) `μ` at lag 1 + the common-mode ≈ 8.7e-5 at all lags; retains ≈ 0.73 of the
  shared lag-1 excess covariance at R=12 (exchangeable, not independent); S3 ≈ 0.
- **Shared:** MA(1) `μ` + common-mode + a **decaying** memory autocovariance (γφ² lags 1–4 ≈
  `5.6e-12, 2.6e-12, 6.7e-13, ~0`) — the right SHAPE (present only in shared), sub-floor AMPLITUDE
  on records; S3 ≈ 0.

### 5.5 Printed diagnostics

Pooled delta-detector rate q̂ per arm; pileup fraction proxy q̂/2 (parity-saturation heuristic,
class (c)); n_traj, S, cluster count; the derived `N_detect` bracket; the common-mode estimate.

---

## 6. G7 — isolation (structural + scramble invariance)

Script `gates/g7_isolation.py`; evidence `gates/g7_isolation.json`. N_g7 = 64 (c) —
isolation is structural, not statistical.

- **P-G7-1 (a-structural).** Payload keys ⊆ {det, obs, marg}; det (N,B) uint8; obs (N,)
  uint8; no `truth`/manifest keys in the payload (red-team R4).
- **P-G7-2 (a).** (i) Determinism: emit(seed) twice → byte-identical det+obs.
  (ii) Truth-label scramble: deep-copy `teacher.truth`, scramble every string-valued
  label field in the LIVE dict (guards emit reading truth mutably), re-emit at the same
  seed → byte-identical. (iii) Relabel-hook probe: if the teacher exposes a documented
  relabel/clone-with-labels hook, exercise it; else emit `SKIPPED(no-relabel-hook)` —
  visible, not silent. **STATED ASSUMPTION A-G7-1:** the binding scramble form depends on
  Builder 2's constructor surface; the gate records exactly which forms ran.
- **P-G7-3 (a-structural).** `isinstance(teacher, ControlledTeacher)` (runtime-checkable
  protocol); `.truth` is a dict property reachable evaluator-side only (never in the
  payload); CertReport.truth is the only cert-side conduit (asserted by type surface).
- **P-G7-4 (a-static).** Static import scan: NO module under `src/qec_twin/calibration/`
  or `src/qec_twin/hardware/` imports `qec_twin.mechanisms` (regex over source files).
  **Declared scope:** the learner path per the isolation contract = calibration (consumes
  observations) + hardware (contract §B-8 "hardware/ never imports mechanisms/");
  `simulator/` is EXCLUDED from the scan with the printed reason (the evaluator-side
  frontend legitimately imports `mechanisms.axis1_primitives`).
- Cheat-twin: `SKIPPED(optional diagnostic per contract G7 — not a gate)` row.

Verdict: PASS ⇔ P-G7-1 ∧ P-G7-2(i,ii) ∧ P-G7-3 ∧ P-G7-4.

---

## 7. G8 — runner + durability object

Script `gates/run_gates.py`; evidence `gates/g8_runner.json`; runner
`outputs/run_gates_suite.sh` (v6 pattern: pipefail, abs conda python, tee log,
`python-exit=${PIPESTATUS[0]}` appended, exit rc).

- Sequence: **G2 fresh re-run** (`gates/g2_jointL.py` — evidence refresh vs the 06-29
  module edits) → G4 → G5 → G6 → G7, each a subprocess; stdout streamed + `GATE_RESULT`
  lines parsed.
- **SKIPPED rows** for G1, G3a, G3b with reason string exactly:
  `"not-this-round (ratified 2026-07-03 order: G0→teacher→G4-G8)"` — visible, not silent.
- `g8_runner.json` = {tracked_scripts (paths + sha256), output_hashes (per-gate JSON
  sha256), result_summaries (gate, verdict, content_hash, rc), skipped rows, runner_rc,
  `outputs_dir_scratch_only: true`, content_hash}. rc = 0 ⇔ every RUN gate PASS.
  `--fail-fast` stops at the first FAIL (default: run all, aggregate).

---

## 8. Faithfulness three-piece (protocol I–III) — this round's deliverable

### 8.1 Constraint ledger (rule II; falsifying test each)

| # | constraint | falsifying test (must trip when violated) |
|---|---|---|
| L1 | TV symmetric, ∈[0,1], TV(P,P)=0 | G0-v2 PC1 + in-run assert on every TV |
| L2 | Record probabilities sum to 1 ± 1e-8 | G0-v2/g-gates assert; trips on branch-mass loss |
| L3 | branches = 2^M, no silent pruning | record_count == 2^M assert per manifest |
| L4 | ζ observable only on superposition-bearing edges; instrument must be LIVE at large ζ | PC2b trips if inert |
| L5 | No check may share the engine with its referee | G0-v2 from-scratch GT + its drop-a-layer negative control (trips if vacuous) |
| L6 | Spitz p_ij validity domain (denominator > 0, √-arg ≥ 0) | g6 flags + excludes + counts invalid pairs; direct-covariance cross-check on one arm |
| L7 | DEM decode is correlation-blind (no teacher truth in the DEM) | g4 builds the DEM from public geometry + record-empirical pooled rate only; a truth-fed DEM would break the declared construction hash |
| L8 | Ablation arms must differ where registered and ONLY there (marginals preserved) | P-G4-3 marginal z-test; g6 R-G6-A/B (off MA(1) floor) + R-G6-C (common-mode equality shared≈markov) |
| L9 | Params must actually vary per round (dead-override toy, R1) | g6 C1 positive control |
| L10 | The statistic pipeline must detect planted correlation (common-mode P2 + memory P3) and stay silent above the MA(1) floor on the correct null (i.i.d. measured bits → deltas, P1-fixed) | g6 P1/P2/P3 stubs |
| L11 | Cluster structure of batched shots must enter the SEs | §2.4 cluster bootstrap; preconditions fail if n_traj < 2000 |

### 8.2 Independent ground-truth checks (rule I; one per part)

- Part A: P-G0V2-7 from-scratch numpy enumeration (+ negative control) and the v1
  committed-anchor reproduction (P-G0V2-6).
- Part B (g6): the ledgered Spitz p̂_ij at lag 1 cross-checked on ONE arm against the
  direct covariance definition (independent formula path: cov/denominator reconstruction
  vs the closed form; tolerance 1e-12 on identical shot data — an algebraic-identity
  check that trips on an implementation typo in either).
- Part B (g4): corrqec is the registered EXTERNAL generation reference (scoped §H);
  until vendored, its absence is declared DEFERRED — never simulated by our own generator.

### 8.3 Bounded simplifications (rule III)

| simplification | class | bound / honesty statement |
|---|---|---|
| N_detect worst-case p=½ variance bound | c | conservative upward on N (never optimistic) |
| Matched DEM from pooled empirical rate | c | pooled identity (a)-exact; per-detector residuals REPORTED unbarred; MC error of d̄ ~ √(d̄/N·n_det) printed |
| Uniform finals noise p_fin = p_anc | c | declared placement choice; both arms decoded by the SAME DEM ⇒ ΔLER insensitive at first order |
| Trajectory-mean readout/reset (slice-1) | c | inherited from the ratified slice scope; S3 (r3) is the in-round leak witness |
| corrqec deferral when not vendored | c | DEFERRED string in evidence; gate never fails on absence; scope §H Pauli-layer only |
| 4q fixture variant | c | separate registered curve (S2); TV ratio band P-G0V2-2 |
| Batching S > 1 | c | recorded; within-shot statistics unaffected; cluster SEs mandatory (L11) |
| GT tolerances 1e-10 / divergence 1e-8 | c | two exact c128 enumerations; roundoff floor |

---

## 9. Registered-predictions summary table

| id | class | statement (short) | miss handling |
|---|---|---|---|
| P-G0V2-1 | b | β ∈ [0.5, 1.0]; interior lean β→1 | FINDING |
| P-G0V2-2 | b | TV_4q(2)/TV_5q(2) ∈ [0.5, 1.5] | FINDING |
| P-G0V2-3 | a | PC1 TV ≤ 1e-12 | gate FAIL |
| P-G0V2-4 | a-scoped | ζ-only ≤ 1e-9; PC2b live > 1e-12 | gate FAIL |
| P-G0V2-5 | c | decision rule; none qualifying ⇒ STOP | STOP |
| P-G0V2-6 | c | v1 anchor within 5e-3 rel | gate FAIL |
| P-G0V2-7 | a | from-scratch GT ≤ 1e-10; neg-ctrl ≥ 1e-8 | gate FAIL |
| P-G0V2-8 | a | Σp residual ≤ 1e-8; count = 2^M | gate FAIL |
| P-G4-1 | b | ΔLER ∈ 0 ± 3·SE | FINDING (report only) |
| P-G4-2 | a/c | pooled matched-rate identity; per-det residuals reported | report |
| P-G4-3 | b | shared-vs-markov pooled det-rate \|z\| < 3 | gate FAIL |
| P-G4-4 | b/c | corrqec §H-scoped agreement or DEFERRED (the RUN comparison is NOT yet implemented — vendored+wired+API-discovered but the interaction_func→lag-1 inversion needs a theory-first reading note; `gates:False` is permanent until then, so the "RUN mismatch" branch is currently unreachable, by design) | FAIL only on a RUN mismatch |
| P-G4-5 | a | DEM/detector-width structural | gate FAIL |
| P-G5-1 | c | Markov-k convergence by k=6 else REJECTED | gate FAIL |
| P-G5-2 | b | converged k\* ≤ 4 | FINDING |
| P-G5-3 | a | NLL(k\*) ≤ NLL(0) + 3·SE | gate FAIL |
| G6 R-A | a | off p_ij(lag1)=μ_c (0.0149); lag≥2=0 | gate FAIL |
| G6 R-B | a | MA(1): off S2(lag1)≠0, S2(lag≥2)=0 | gate FAIL |
| G6 R-C | b | common-mode equality shared≈markov (lag≥2) — CONDITIONAL (gates only if common-mode detected in shared; else VACUOUS-power, reported) | gate FAIL (when gated) |
| G6 R-D | b | memory sub-detectable at N≤1e6 (derived N≥1.1e10) | REPORTED (never gates) |
| G6 C1 | c | params vary + cross-mech corr ≥ 0.9 | gate FAIL |
| G6 C5 | b/c | r3 ≈ 0 all arms | gate FAIL |
| G6 P1 | c | pipeline null (i.i.d. bits→deltas) silent above MA(1) | gate FAIL |
| G6 P2/P3 | c | common-mode detected / planted-memory detected | gate FAIL (pipeline) |
| P-G7-1..4 | a | payload/scramble/protocol/import-scan | gate FAIL |
| G8 | c | runner object complete; G1/G3a/G3b SKIPPED-visible | gate FAIL |

## 10. Amendment log

- **G6-A1 (2026-07-03, pre-run, Track B / reviewer F1) — G6 re-registered from a pass/fail
  discriminative gate to a FAITHFULNESS REPORT.** *Reason:* the original §5 conditions (raw Spitz-p_ij
  / count-autocov z-scores discriminating shared vs markovian vs off) were proven, from committed
  constants BEFORE any G6 run, to be unsatisfiable on a correct teacher — the delta stream is MA(1)
  (off `p_ij(lag1)=μ=0.0149`, not 0; C3/C4 "flat" clauses read `|z|≈15` at N=1e6), a permutation-
  invariant common-mode ≈ 8.7e-5 dominates and cancels only in the difference, the markovian
  permutation is exchangeable (retains ~73% of the lag-1 covariance at R=12), and the genuine memory
  discriminator is second-order with `N_detect ∈ [1.1e10, 1.2e15] ≫ 1e6`. *What changed:* §5.1 adds
  the declared closed-form nulls; §5.2 replaces C2/C3/C4 with R-G6-A (off MA(1) closed form),
  R-G6-B (1-dependence), R-G6-C (common-mode equality), R-G6-D (reported sub-detectability, never
  gates), keeps C1/C5, fixes P1 (i.i.d. measured bits → deltas, not i.i.d. delta bits), relabels P2
  (common-mode sensitivity), adds P3 (planted-memory positive control); §5.3 records the
  sub-detectability FINDING and retires the "re-run at 1e6" path; §5.4 corrects the per-arm
  expectations; §9 rows updated. Derivation:
  `docs/twin_validation/g6_null_model_rederivation_2026-07-03.md`; committed-constant evidence:
  `outputs/twin_validation/g6_null_feasibility_from_constants.py` (`python-exit=0`). This CONSUMES
  G6's single amendment (§0 budget); a second amendment demand on G6 = a registered FINDING + STOP.
