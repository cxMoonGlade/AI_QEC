# BUILD CONTRACT — Full-Error-Coupling QEC Teacher Simulator

**Status:** synthesized build contract (chief-architect adjudication of two independent grounded drafts;
produced 2026-06-26 via a 5-reader repo-grounding + 2-architect + 1-judge workflow). Anti-toy is the
prime directive: every gate is constructed so it **cannot pass on a toy**, and any draft idea that would
let a gate pass on a toy is flagged and EXCLUDED (see EXCLUSIONS). Binds to
`full_error_coupling_prereg.md` (prediction layer §0–§7) and `nonmarkovian_coupling_constraint_ledger.md`
(rule-II ledger C1–C10). Mainline `src/` untouched until commit-gated (hard commit-gate).

**Earned-line up front:** what is earned today is a validated **non-Markovian SOURCE LAYER** + a
validated **per-mechanism primitive library** — **at the source layer only** (Ramsey/echo coherence). This
contract specifies what it takes to earn the **QEC simulator**: the joint-Lindbladian assembler (Axis-1),
the shared-latent param coupling (Axis-2), and above all a **measured, ablatable imprint on real QEC
records under the real schedule** (G4/G6). Until G1–G8 + C1–C10 pass on records, the simulator is NOT
earned.

---

## RESOLVED DECISIONS (user, 2026-06-26) — binding

- **[H4] First-slice register arm = qubit-window** (`window_channel.WindowChannel`, no-leakage, q=2 —
  faster path to G4; both axes still live via source-modulated T2/ZZ/detuning). **HARD CAVEAT (user):**
  the qubit-window is ONLY a register/feasibility choice — **the acceptance gates MUST remain real
  QEC-coupling-simulator gates, NOT source-only toy gates.** G4 is measured on emitted `{det,obs}` through
  the frozen decoder; G6 ablation is measured on records; G3a/G3b at the source layer do NOT substitute for
  G4/G6. Choosing the cheaper register must NEVER become a relaxation of the gates. Leakage (qutrit-DM arm)
  is a later slice.
- **[H1] G4 headline observable — ⚠ the 2-point form is RETRACTED by H2; re-registration to a MULTI-TIME
  signature is in progress.** Originally "detection-event LONG-RANGE (2-point) correlation vs Markov-k." H2
  (`h2_effectsize_g4_prereg.md` §6, verified) found, via an exact 2-state-HMM enumeration AND Kam et al.
  arXiv:2410.23779 (L4), that the **2-point detection-event correlation is a KNOWN-INSUFFICIENT discriminator**:
  it cannot separate a slow single RTN from a 1/f source at feasible Markov-k (`E(6)/E(1)` ≈ 0.43 vs 0.45–0.50,
  gap <0.07). A **single RTN is Markov-k-TRIVIAL** (exact residual O(1e-4) → N>1e8 → infeasible). **Resolved
  sub-decisions:** (i) the source for slice #1 = **1/f** (the only asymptotic-k non-finite-order arm); single
  RTN = negative/contrast control. (ii) The G4 observable MUST be re-registered to a **multi-time /
  timelike-string** signature (decode-relevant ΔLER / explicit multi-time correlator / excess-entropy gap —
  candidate evaluation in progress); the Markov-k rival stays, the statistic vs it must be multi-time. **Honest
  cap:** if no source beats Markov-k by |z|≥5 on the corrected multi-time observable at N≤1e6, the contribution
  is capped at the source layer (G3a/G3b) and does NOT upgrade to a record-level QEC imprint.
- **[POSITIONING — resolved 2026-06-26, BINDING]** After H2 + candidate-eval + a pairwise-slide re-review
  (all orchestrator-verified), a **mild physical 1/f source is confirmed NOT to upgrade to a novel
  record-level QEC ΔLER** (capped at the source layer; the heavy-tailed 1/f streak is amplitude-crushed at
  mild rate, and d3 has `L(d)=2`=pure-pairwise). **DECISION (user): still BUILD the simulator, but POSITION
  it as FAITHFUL FORWARD INFRASTRUCTURE — its value is faithfulness (a teacher that correctly joint-couples
  mechanisms (Axis-1) and carries realistic non-Markovian correlated noise (Axis-2)), a downstream tool — NOT
  a novelty headline.** The non-Markovian NOVELTY stays at the source layer (the earned coherence wedge). ⇒
  **G4/G6 are RE-FRAMED from "novel discrimination (|z|≥5 vs Markov-k)" to FAITHFULNESS verification** (the
  source leaves the physically-CORRECT imprint on records, cross-checked vs an INDEPENDENT reference —
  corrqec; the discrimination MAGNITUDE is reported, and being sub-floor for a mild source is a faithful
  PROPERTY, not a failure). The **source-coupling Θ(z_t) models the PHYSICALLY-REAL fan-out** (1/f → all
  frequency-mediated params: ZZ, T2, detuning, drive, AND syndrome-SPAM/gate where physical), NOT optimized
  for Kam Class-1/2 discrimination. The "EARNED" bar (§9) becomes: G1 (real schedule) + G2 (Axis-1 joint-L
  composed-vs-joint fidelity) + faithful oracle-validated channels + G7 (isolation) + G8 (durability) + the
  source leaves the corrqec-cross-checked CORRECT imprint (G4/G6 as faithfulness).
- **[Next step]** Resolve the remaining pre-build open questions (H3 dt-bracket, H5 G2-band pre-registration,
  H6 commit-gate sequencing, H7 cheat-twin spec) — H2 is done — then build the vertical slice. (H1/H4
  resolved above; the G4-observable = decode-relevant ΔLER, now as a faithfulness check.)

---

## SECTION A — CORE OBJECT + MODULE LAYOUT

**Core object: `CoupledCycleTeacher`** — an evaluator-only object implementing the existing
**`ControlledTeacher` Protocol** (`src/qec_twin/audit/certify/types.py:283–328`: `sched`, `truth`, `emit`,
`channels`, `emit_clifford_slice` — all confirmed present). NOT a new channel field, NOT a composition
chain. A generator-over-cycles, the 5-tuple:

```
CoupledCycleTeacher = ( SourceState z_t,         # Axis-2 dynamical latent      (NEW)
                        SubstepSchedule S,        # exact/xzzx_parser.XZZXSchedule (REUSE)
                        ParamMap Θ(z_t),          # source→many-mechanism params  (NEW)
                        JointLindbladAssembler A, # within-substep ONE expm        (NEW)
                        TruthStore τ )            # evaluator-only ground truth   (REUSE pattern)
```

Observable output is the **same seam-folded record surface** the carrier already emits —
`{"det": (N,B) uint8, "obs": (N,) uint8}` (`audit/certify/core.py:46–95`) — so it drops into
`certify_cells` (`core.py:150`) + the `Anchor`/`Control` independent-ground-truth ports **with no API
change**. The two coupling axes are properties of the forward LAW, not the record schema:
- **Axis-1 (instantaneous):** per substep, `A` assembles `L_substep = -i[Σ_i H_i, ·] + Σ_i D[c_i]` over
  **all** mechanisms occupant in that substep, then **one** `expm(L_substep·dt)`. Composition is allowed
  **across** substeps (real circuit time order) — **never within** a substep unless G2 licenses it.
- **Axis-2 (temporal):** `z_t` is a dynamical DOF evolving **across cycles**; `Θ(z_t)` feeds the **same
  draw** into many mechanism params. **Never** downgraded to per-round non-negative Lindblad rates — that
  is the Markovian baseline `.markovian_baseline()`, built explicitly as the G5/G6 control.

**Register & composition.** Within-window register = the **qutrit window density matrix**
(`forward/exact/qutrit_dm.QutritDM`, `apply_local_op_q`, leaked-readout POVM at `qutrit_dm.py:215`) for
the leakage arm; the **qubit-window alternative** is `window_channel.WindowChannel` (`SlotStep` builder,
`MAX_WINDOW_QUBITS=14`) for the no-leakage Pauli/coherent arm. Cross-window composition = the declared
seam rule `Phi_L[σ_R](ρ_L) = Tr_R[E_seam(ρ_L ⊗ σ_R)]` (`forward/scalable/composed.py`, ADR 0008).
GPU-only, no CPU fallback (memory rule).

**Module layout:**
```
src/qec_twin/
  forward/
    joint_lindbladian.py        [NEW]   Axis-1 assembler: ΣH+Σc → ONE matrix_exp → Choi→Kraus
    exact/qutrit_dm.py          [REUSE] QutritDM register (apply_local_op_q + leaked POVM)
    exact/xzzx_parser.py        [REUSE] XZZXSchedule.within_cycle_streams (real substep schedule)
    exact/rep_code.py           [REUSE] deterministic detector/obs XOR construction
    window_channel.py           [REUSE] SlotStep builder hook (qubit-window arm, ≤14)
    scalable/sv_sampler.py      [REUSE] SvSampler MCWF qutrit trajectory emit (leakage arm)
    scalable/seam.py            [REUSE] teacher_shots_to_events:261 / teacher_soft_shots_to_events:297
                                        build_matched_pauli_dem:97 (frozen-MWPM DEM)
    scalable/composed.py        [REUSE] seam conditional reduction (cross-window)
  mechanisms/
    coupled_teachers.py         [NEW]   CoupledCycleTeacher (ControlledTeacher impl)
    source_coupling.py          [NEW]   Θ(z_t): one latent → many mechanism params
    qutrit_teachers.py          [REUSE] WG leakage params, .params/truth pattern
    seam_teachers.py            [REUSE] .params/truth dataclass pattern
    catalog.py                  [REUSE] M0–M34 mechanism specs + generators
  audit/certify/                [REUSE] core/types/facade — record schema, Anchor/Control ports, scoring
outputs/teacher_prereg/
    nm_source.py                [REUSE] sample_rtn/1f_trajectory → Axis-2 source stepper
    nm_divisibility.py          [REUSE] rhp_measure/blp_measure → G3a CP-divisibility gate
    nm_wedge.py                 [REUSE-PARTIAL] envelope probe only (NOT the wedge metric — see F)
    qutip_*_channels.py         [REUSE] oracle-validated {H_i,c_i} Kraus primitives → assembler input
    qutip_teacher_source.py     [REUSE] the 4 source→param exemplars Θ extends
docs/twin_validation/gates/     [NEW, TRACKED] the 8-gate runner + result summaries + hashes (G8)
```

---

## SECTION B — THE 9 DESIGN-QUESTION ANSWERS

**1. CORE OBJECT.** `CoupledCycleTeacher` (§A): an evaluator-only `ControlledTeacher` whose forward law
carries both axes; emits the existing `{det,obs}` surface; drops into `certify_cells` + Anchor/Control
unchanged.

**2. SOURCE STATE EVOLUTION ACROSS CYCLES (Axis-2).** `z_t` is an explicit memory-ful DOF, **not** a
positive rate. Three registered forms reusing validated `nm_source.py` generators: RTN/TLS telegraph
(`sample_rtn_trajectory:213`, exact autocorr `e^{-2γ_sw|τ|}`, C2); 1/f drift (`sample_1f_trajectory:252`,
closed-form Dutta–Horn `sum_lorentzian_spectrum_analytic:192`, C6); shared-bath/burst (few explicit modes
/ windowed event broadcast). Per-cycle advance: between cycle `k`/`k+1` step `t→t+t_cycle`; memory
persists → consecutive-cycle params correlate `≈ e^{-2γ_sw t_cycle}` (P2 / C8a-latent-exact,
C8b-observable-band). Full per-shot `{z_t}` recorded evaluator-only (Q7).

**3. SOURCE → MECHANISM-PARAMETER MAP (joint modulation).** `Θ(z_t)` = a panel of declared,
physics-grounded maps `z_t → {θ_mech}` in new `mechanisms/source_coupling.py`, extending the four
exemplars in `qutip_teacher_source.py` (`_p_cz_to_t1tphi`, `_theta_leak_to_wg`, `_phi_to_J`,
`_B_to_gamma_burst`). The non-Markovian content = **one draw modulates many mechanisms at once**:

| source draw | co-modulated params (catalog M0–M34) | grounding |
|---|---|---|
| 1/f freq drift δω(z_t) | ζ (ZZ), γφ/T2, detuning, Ω (DR), spillover c_x | qubit-frequency-mediated; §5 |
| burst B(z_t) | γ₁↑, LK trigger, neighbour broadcast | elevated-T1 channel |
| shared TLS g(z_t) | correlated dephasing on a pair/neighbourhood | JC tls_exchange_channel |

Each map = class-(c) swept, recorded in `TruthStore` with epistemic class + bound (S1–S4). The Markovian
baseline calls the **same maps** with **independent per-round draws** (G6 negative control).

**4. ACTIVE MECHANISMS PER SUBSTEP FROM THE REAL SCHEDULE (Axis-1 trigger).** Read off `XZZXSchedule`
(`xzzx_parser.py:215`), **never hand-written**. Substeps = TICK-delimited layers (`_tick_layers`) →
`{1q-gate, CZ, idle, readout}`; per-qutrit CZ-layer participation (`WithinCycleStream.cz_layers`, `n_cz`)
gives which qubits are in each CZ substep (sparse 2–4 layers, **not** "all in all"); the mid-cycle X echo
(strictly between CZ-layer 2/3, `xzzx_parser.py:775–786`) and post-M Y (`RoundDataFrame`) are **applied,
never dropped** (Clifford-invariant ≠ leakage-invariant); the M boundary token separates pre-M (X echo)
from post-M (Y) per qutrit. A substep's active set = `{T1,T2}` (all) ∪ schedule-occupant
`{DR,SP,ZZ,LK,FS,RD,MI,…}` restricted to participating qubits.

**5. JOINT-LINDBLADIAN ASSEMBLER HOME (Axis-1).** New `src/qec_twin/forward/joint_lindbladian.py`
(sibling to `cptp_channel.py`, `mechanisms_torch.py`). Single entry:
```python
assemble_substep_channel(active: list[MechSpec], dt: float, *, q: int, device="cuda") -> KrausStack
#   1. build H_i, c_i (torch, qutrit dim q) from QuTiP-derived generators (reuse qutip_*_channels builders)
#   2. L = -i(H⊕−Hᵀ) + Σ_k (c̄_k⊗c_k − ½ I⊗c_k†c_k − ½ (c_k†c_k)ᵀ⊗I)     [Liouvillian]
#   3. S = torch.linalg.matrix_exp(L*dt)              [ONE expm on GPU]
#   4. Choi-eigendecompose S → CPTP Kraus (identity-sink completion)
```
Reuses `qutip_opensystem_channels.py:_full_superop_expm_gpu` (240–256) + `superop_to_truncated_kraus_1q`
(340–380). **SLICE #1 runs `q=2` (qubit-window, no leakage)** and threads into `window_channel` `SlotStep`;
the `q=3` qutrit path (`QutritDM.apply_local_op_q`/`apply_channel_2site` + leaked POVM) is the **slice #2**
extension — same entry point, no call-site change. Feasibility: exact joint-L GPU-feasible to the qutrit-DM
register (3⁹≈19.7k DM ≈5.77 GiB on RTX 5090); qubit windows to ~n=11 safely (n=14 tight); beyond → seam
(ADR 0008). No CPU fallback.

**6. EMIT SYNDROME/LOGICAL RECORDS.** `emit(regime, m, N, seed) -> {"det":(N,B)uint8, "obs":(N,)uint8}`.
**Leakage/qutrit arm:** `SvSampler.sample` (`sv_sampler.py:1238`, MCWF trajectories over
`MarshalledSchedule`) → packed shots → `teacher_shots_to_events` (`seam.py:261`); soft variant via
`teacher_soft_shots_to_events` (`seam.py:297`). **Qubit-window arm:** `WindowChannel.apply` + DEM. Detectors
= deterministic measurement-record XOR (`rep_code.py:103–136`). `emit_clifford_slice` for the bit-flip
slice. Records = the **only** learner-visible product.

**7. EVALUATOR-ONLY TRUTH STORAGE.** `TruthStore τ` extends the frozen `.params` pattern
(`seam_teachers.py:158`, `qutrit_teachers.py`). Evaluator-only: full per-shot `{z_t}` (seed-keyed), every
derived `Θ(z_t)` param set with (a/c) class + bound, the per-substep `{H_i,c_i}` + Kraus stacks, teacher
IDs, mechanism Kraus, seam edge field. Exposed via `.truth` (`types.py:289`) + `.channels()`
(`types.py:297`); Anchor ports read these. **Returned only in `CertReport.truth` (`core.py:160`) as
artifact — never an input to calibration.**

**8. LEARNER-VISIBLE BOUNDARY (no source leak).** Existing isolation machinery + a NEW scramble-invariance
assertion: learner consumes `(context, det, obs)` only (`calibration/nll.py`); `hardware/` never imports
`mechanisms/`; the teacher lives under `mechanisms/` (evaluator side); latent reachable only via
`.truth`/`.channels()`. **NEW (C9.v):** `assert_isolation` — learner records must be **invariant to
scrambling the latent's evaluator-only labels** (the binding gate). Structural: emitted payload keys ⊆
`{det,obs,marg}`; no `truth` key in the learner payload. (The latent-peeking cheat-twin is an OPTIONAL
reported DIAGNOSTIC under the faithful-infrastructure positioning, not a gate — see G7.)

**9. GATES BEFORE "EARNED" (re-ordered by the faithful-infrastructure POSITIONING).** All 8 hard gates
(G1–G8) + ledger C1–C10. **HEADLINE = G2 (Axis-1 joint-L composed-vs-joint fidelity)** — the genuine
forward-fidelity contribution: the teacher correctly JOINT-propagates coupled mechanisms within a substep
(exact-zero pairs `composed==joint`; nonzero pairs in their predicted band), the thing a naive composition
chain gets wrong. **G1 (real schedule) + G7 (isolation) + G8 (durability)** are the other load-bearing
infrastructure gates, and **faithful oracle-validated channels** (CPTP, vs INDEPENDENT analytic oracles) are
the channel-fidelity spine. **G4/G6 are RECORD-FAITHFULNESS / ablation gates** (the source emits the
physically-correct, independently-cross-checked correlated records) — NOT a novelty-discrimination headline
(H2: the mild-source record-level imprint is capped at the source layer; the non-Markovian novelty is the
`nm_wedge.py` source-layer wedge). The simulator is "earned" as faithful infrastructure when G1+G2+G7+G8 +
channel oracles pass and G4/G6 confirm faithful (cross-checked) record emission.

---

## SECTION C — THE 8 HARD GATES (pass/fail evidence object each)

Each gate = a committed script under `docs/twin_validation/gates/` (TRACKED, G8): precondition asserts +
printed evidence (hashes/shapes/numbers) + flushed output + `__main__` guard. Each emits a JSON evidence
object `{verdict∈{PASS,FAIL}, load-bearing numbers, content hash, measured_on}`. Runner aggregates rc /
fails fast.

**G1 — Schedule-faithfulness.** `g1_schedule.json` = `{source_circuit_hash, round_kind:"r10_interior",
n_data:9, n_stab:8, per_qutrit_h_patterns:[4 distinct], midcycle_X_between_layers:(2,3),
post_M_Y_present:true, per_qutrit_cz_layers:{2–4}, M_boundary_tokens:present,
terminal_readout_separated:true, sweep_init_resolved:true, reset_model:"ancilla_R_each_round"}`.
**Measured on:** parsed `XZZXSchedule` from shipped `circuit_ideal.stim`. **PASS** ⇔ all 12 checklist items
present + matching the real circuit; mid-cycle X strictly between CZ-2/3; post-M Y carried. **FAIL** on any
hand-written two-bit toy / missing physical gate / dropped echo / dropped frame / missing readout/reset.

**G2 — Joint-L (composed vs joint) [HEADLINE fidelity gate].** Evidence object `g2_jointL.json` carries
`{verdict, content_hash, measured_on:"assembled substep channels on the q=2 d3 window", metric:"process
(entanglement) infidelity 1−F_e (METRICS.md forward-fidelity ledger)", rows:[…]}` where each `row` =
`{pair_ij, substep, ‖[H_i,H_j]‖_fro, exact_zero:bool, witness, value, predicted_band, in_band:bool, class}`
(per-pair, per the schema — NOT a bare summary). **PASS** ⇔ (a) **every exact-zero pair** passes BOTH the
TIGHT STRUCTURAL witness `‖[L_A,L_B]‖_F ≤ NUMERICAL_ZERO(1e-12)` (expm-free, the analytic reason
composed==joint) AND the channel-level superoperator Frobenius distance `‖S_composed−S_joint‖_F ≤ 1e-10` (the DECLARED torch-c128
`matrix_exp` floor, class-(c); the Choi-state-from-Kraus diagnostic floors at ~6e-12 at dt=20 and is REPORTED
not gated — so "composed==joint" is witnessed at 1e-12 STRUCTURALLY + 1e-10 at the channel level, NOT a bare
≤1e-12 on the reconstructed channel); a deliberately-broken assembler FAILS the channel witness loudly
(~2e-1); (b) **every nonzero pair's** `1−F_e` (the METRICS.md process infidelity, `≈‖G‖²_F/d`) lands in its
predicted band (H5) with the predicted power laws (physical `dt²`, fixed-Ω small-`dt` `dt⁴`, `ζ²` — the sharp
metric-constant-independent tests), joint path used; (c) concurrent-Markovian couplings (DR×ZZ, LK×CZ)
**labeled BASELINE/control, NOT contribution**.

**G3 — Source-physics, SPLIT.**
- **G3a (C10a, RHP/CP-divisibility):** `g3a_rhp.json` = `{v/γ_sw grid, rhp(v), blp(v), onset:v≈γ_sw,
  markovian_control_reads_0:bool}` via `nm_divisibility.rhp_measure:146`/`blp_measure:208`. **PASS** ⇔ a
  plain `D[√Γ n]` control reads RHP=0 (C4) AND RHP>0 onset at `v=γ_sw`, BLP agreeing.
- **G3b (C10b, observable wedge):** `g3b_wedge.json` = `{v*_measured, shot_count, t_grid, revival_floor,
  band[γ_sw<v<v*]=RHP-positive-but-wedge-unobservable, spearman(wedge,revival_amp),
  out_of_family_markovian_control→wedge≤floor:bool}`. **PASS** ⇔ wedge collapses (≤floor) for `v≤γ_sw`,
  rises monotone in revival amplitude for `v≥v*`, AND an out-of-family Markovian source yields wedge≤floor.
  **G3b MUST NOT falsely kill a weak-but-real non-Markovian source** — a sub-shot-noise wedge in the
  `γ_sw<v<v*` band is a PASS-with-band finding, never a FAIL.

**G4 — QEC-integration (RE-FRAMED to FAITHFULNESS, not novelty discrimination — POSITIONING decision).**
Observable = decode-relevant ΔLER under the correlation-blind frozen marginalized Pauli-DEM
(`seam.build_matched_pauli_dem:97`) decoding the emitted `{det,obs}`: `ΔLER = LER(frozen DEM on true 1/f
records) − LER(matched-marginal-independent)`. `g4_imprint.json` = `{observable:"decode-relevant ΔLER",
source_resolved_LER, matched_marginal_independent_LER, delta, z_score, n_shots, d,
corrqec_crosscheck_agree:bool}`. **RE-FRAMED PASS (faithfulness, not |z|≥5 novelty):** the source leaves the
PHYSICALLY-CORRECT imprint on records — (i) the emitted records are CROSS-CHECKED against an INDEPENDENT
generation reference (corrqec, github.com/jkfids/corrqec, vendored pristine) to agree within MC error
(the teacher emits the right correlated records); (ii) the ΔLER MAGNITUDE is REPORTED with its (a/b/c) class
— and per H2 (`h2_effectsize_g4_prereg.md`), for a mild physical 1/f source the ΔLER is sub-floor at feasible
N: that is a FAITHFUL PROPERTY (mild non-Markovian correlation is decode-benign), NOT a failure. **What WAS
the old novelty bar (|z|≥5 vs Markov-k) is RETIRED** (H2: capped at the source layer; the non-Markovian
novelty is the `nm_wedge.py` source-layer coherence wedge, not a record-level discrimination). G4 now
certifies the teacher EMITS faithful, independently-cross-checked QEC records under the coupled source — the
infrastructure value — not a discrimination headline. (Source-only Ramsey/echo `|L|` remains G3b, the
source-layer wedge.)

**G5 — Record-level comparator / REPORTING discipline (re-framed; no surviving-gap novelty requirement).**
`g5_baseline.json` = `{comparators:[best-converged-Markov-k, finite-memory-null, matched-record-surrogate],
each_converged:bool, reported_deltas, dt_band}`. **Measured on:** the SAME QEC `{det,obs}` records.
Under the faithful-infrastructure positioning, G5 is NOT a novelty gate — it is the **reporting discipline**
for the G4 record statistics: report the source-resolved record statistic (ΔLER / correlation) against a
PANEL of converged record-level comparators (best Markov-k, finite-memory null, matched-record surrogate),
each declared + converged, so any reader sees the magnitude vs each rival. ⚠ **The source-layer
monotone-`|L|`/isotonic baseline is a COHERENCE object (G3b ONLY), NOT a `{det,obs}` statistic — never in
G4/G5.** **PASS** ⇔ the comparators are converged + declared and the deltas are reported with their (a/b/c)
class. **NO "surviving Markov-k gap" is REQUIRED** (H2: the mild-source gap is sub-floor — a faithful
property, reported, not a pass/fail). A non-converged or i.i.d.-only-strawman comparator = REJECTED (so the
REPORTED delta is honest); but a small/zero delta is a FINDING, not a failure. (monotone-`|L|` supremum +
named panel stay in G3b at the source layer.)

**G6 — Coupling-ablation ON RECORDS.** `g6_ablation.json` = `{shared_source:{cross_mech_corr,
cross_cycle_corr}, independent_source:{...}, off_source:{...}, structure_difference,
collapse_to_0_when_off:bool}`. **Measured on:** `det`/`obs` records (NOT the source latent). **PASS** ⇔
shared-source vs independent-source shows a cross-mechanism/cross-cycle structure difference **in the
records**, AND turning the shared source OFF collapses it to 0 (negative control). Anti-toy core of Axis-2.

**G7 — Isolation (simplified under the faithful-infrastructure positioning).** `g7_isolation.json` =
`{learner_inputs:[context,det,obs], learner_payload_keys⊆{det,obs,marg}:bool,
records_invariant_to_latent_scramble:bool, truth_only_via_CertReport:bool,
no_mechanisms_import_on_learner_path, cheat_twin_delta:reported_diagnostic}`. **GATE PASS** ⇔ (i) the learner
payload keys ⊆ `{det,obs,marg}` (no `truth` key); (ii) records INVARIANT to scrambling the evaluator-only
latent labels; (iii) true `{z_t}`/teacher IDs/oracle channels/per-shot hidden state reachable evaluator-side
ONLY. **The latent-peeking "cheat-twin" is now an OPTIONAL REPORTED DIAGNOSTIC, NOT a gate** (the elaborate
"informative audit" mattered for the retired record-level novelty claim; under faithfulness the binding
isolation test is payload-key + latent-scramble invariance). If reported, the cheat-twin's delta is
informational.

**G8 — Durability.** `g8_runner.json` = `{tracked_scripts, output_hashes, result_summaries,
runner_rc:fail-fast|aggregate, outputs_dir_scratch_only:true}`. **PASS** ⇔ minimal scripts + hashes +
summaries **git-tracked under `docs/twin_validation/gates/`** (gitignored `outputs/` = scratch only);
runner fail-fasts or aggregates rc; every run a committed guarded script.

---

## EXCLUSIONS — anti-toy flags (EXCLUDED — would let a gate pass on a toy)

1. **The coherence-wedge harness reused as QEC evidence.** `nm_wedge.coherence_wedge` +
   `fit_baseline_isotonic` are Ramsey-specific → **EXCLUDED from G4** (source-layer only; satisfies G3b at
   the source layer, never G4). Reusing the *baseline-construction shape* on QEC records (G5) is licensed;
   reusing the *wedge number* is not.
2. **A convenient two-bit / hand-written substep schedule.** The schedule must come from `XZZXSchedule`
   (G1). The 2-bit toy is EXCLUDED; G1 fails it.
3. **ΣD[c_i] with non-negative per-round rates as the contribution.** EXCLUDED as contribution; retained
   only as the G5/G6 Markovian baseline.
4. **An i.i.d. baseline.** EXCLUDED (G5).
5. **Ablation tested only on the source latent.** EXCLUDED; G6 requires the difference + collapse measured
   on `det`/`obs`.
6. **The two-round toy observation model** (`tc_burst_certify`-style). EXCLUDED as G4 evidence.
7. **Naive within-substep composition `E1∘E2∘…`.** EXCLUDED unless G2 licenses it per pair.
8. **The 2-resonator correlated-readout primitive** (Heinsoo Δ⁻²/⁻⁴). Scaling uncertified → EXCLUDED
   unless the Δ-scaling is non-critical to the cert.

---

## SECTION D — CURRENT MINIMAL NON-TOY ARCHITECTURE

```
SourceState z_t            (nm_source.py: RTN/1f/bath samplers — REUSE)
      │  Θ(z_t)            (NEW source_coupling.py; ONE draw → MANY params)
      ▼
SubstepSchedule            (exact/xzzx_parser.XZZXSchedule — REUSE; G1)
      │  per-substep active-mechanism set (§3; participating qubits only)
      ▼
JointLindbladAssembler     (NEW forward/joint_lindbladian.py
      │   L_substep = -i[ΣH_i,·]+ΣD[c_i]; ONE torch.linalg.matrix_exp; Choi→Kraus
      │   reuse qutip_opensystem _full_superop_expm_gpu + superop_to_truncated_kraus; G2)
      ▼
Register                   (SLICE #1: window_channel.WindowChannel SlotStep, q=2, NO leakage — REUSE
      │                     SLICE #2: forward/exact/qutrit_dm.QutritDM + leaked POVM — REUSE)
      │  cross-window: composed.py seam conditional reduction (REUSE; ADR 0008)
      ▼
emit → {det,obs}           (SLICE #1: per-shot Born/Pauli-frame sample of source-conditioned WindowChannel;
      │                     SLICE #2: SvSampler.sample → teacher_shots_to_events; rep_code XOR detectors — REUSE)
      ▼
TruthStore τ               (evaluator-only; extend .params pattern — REUSE; Q7/G7)
      ▼
certify_cells + Anchor/Control independent ground-truth ports   (audit/certify — REUSE; G2/G3a/G4)
```

---

## SECTION E — FIRST-PHASE VERTICAL SLICE

**Slice = single d3-XZZX window on the QUBIT-WINDOW (q=2, NO leakage) register, ONE 1/f source (single RTN =
negative/contrast control), co-modulated mechanisms across the 1q-gate AND CZ substeps, R rounds, both axes
live, emitted as REAL `{det,obs}` records
through the frozen decoder.** Per the resolved decision (H4): the register is `window_channel.WindowChannel`
(qubit, no `|2>`), NOT `QutritDM`/leakage — a register/feasibility choice only; **the gates stay
record-level QEC-coupling gates (G4/G6 on `{det,obs}`), never source-only.** The smallest object on which
**no gate can pass on a toy** (G2 positive control fails loudly on an assembler bug; G4/G6 verify faithful,
cross-checked record emission; G5 anchors the record baselines). **Build to the shortest path to G2 (Axis-1
joint-L fidelity = the headline) + the faithful record plumbing** before broadening mechanisms or distance.
**Leakage (qutrit-DM `QutritDM` + `SvSampler` MCWF + leaked POVM) is slice #2, not slice #1.**

**Steps:**
1. **Schedule (real):** parse the shipped d3 XZZX `circuit_ideal.stim` → `XZZXSchedule` with
   `within_cycle_streams`, interior round **r10 (NOT r01**, `xzzx_parser.py:736`). [G1] The schedule is the
   real leakage-capable circuit; on the qubit register the leakage tokens are inactive (no `|2>`).
2. **Axis-2 source:** a **1/f** source (`nm_source.sample_1f_trajectory`, the physical non-Markovian source
   per H2; a single RTN is the Markov-k-trivial NEGATIVE control), advanced per cycle over R rounds,
   memory-ful, shared across the window's **qubits**.
3. **Θ (PHYSICAL fan-out):** the one source draw modulates the PHYSICALLY-REAL set of frequency-mediated
   params in the same substep — `ζ` (ZZ, extended `_phi_to_J`) + `γφ` (T2, new `_drift_to_T2`) for slice #1
   (faithfulness, NOT discrimination-optimized; Kam Class-1/2 retargeting is a later faithfulness extension).
   Axis-1 + Axis-2 coupled in one place.
4. **Assembler (Axis-1) — TWO substeps, so the G2 gate sees BOTH the exact-zero control AND the DR×ZZ
   headline band:**
   - **CZ-layer substep** `L_CZ = -i[ζ n_a n_b, ·] + D[√(2γφ)n] + D[√γ₁σ⁻]` → the **ZZ×T2 exact-zero
     positive control** (both diagonal in n; two-witness: structural `‖[L_A,L_B]‖≤1e-12` + channel `≤1e-10`).
   - **1q-gate-layer substep** `L_1q = -i[(Ω/2)σx_a + ζ n_a n_b, ·] + D[√(2γφ)n] + D[√γ₁σ⁻]` → the **DR×ZZ
     nonzero headline band** (`1−F_pro` in the H5-registered band, both `dt`-sweeps + power laws).
   Each is ONE `matrix_exp(L·dt)` on the **q=2 qubit-window** (`WindowChannel`/`SlotStep`), Choi→Kraus;
   composed-vs-joint computed per substep (the G2 evidence object). `dt` swept per the H3 bracket.
5. **Emit:** R-round `{det,obs}` via the **qubit-window emit path** — per-shot Born/Pauli-frame sampling of
   the source-conditioned `WindowChannel` (each shot carries its own `z_t` trajectory) → `rep_code` XOR
   detectors. (NOT `SvSampler`-leakage; that is slice #2.)
6. **Records → audit/decoder:** `certify_cells`, frozen-MWPM DEM (`seam.build_matched_pauli_dem:97`),
   Anchor/Control ports.

**Gates exercised (all 8 evaluable on this single object):** **G2 (HEADLINE)** — ZZ×T2 is an **exact-zero
pair** (both diagonal in n) → positive control (two-witness: structural `‖[L_A,L_B]‖≤1e-12` + channel `≤1e-10`),
+ DR×ZZ as the nonzero predicted-band check (the Axis-1 joint-L fidelity, metric = process infidelity `1−F_e`); **G1** real schedule; faithful channel ORACLES (CPTP vs independent
analytic oracles); **G4 (faithfulness)** — the source-conditioned records cross-checked vs corrqec
(Pauli/temporal-mask layer ONLY — §H scope) + the decode-relevant ΔLER reported with its class (sub-floor for
the mild 1/f, a faithful property); G3a/G3b sweep `v/γ_sw` (source-layer); G5 **record-level** baselines
(best Markov-k / finite-memory null / matched surrogate); **G6 (faithfulness)** shared vs independent source
→ correlated-structure difference, OFF → collapse (the teacher's correlated structure is correct + ablatable);
**G7** latent-scramble invariance (+ structural payload-key check); **G8** one tracked runner.

**New files:** `forward/joint_lindbladian.py::assemble_substep_channel`;
`mechanisms/source_coupling.py::source_to_params + _drift_to_T2`;
`mechanisms/coupled_teachers.py::CoupledCycleTeacher (+ .markovian_baseline())`;
`docs/twin_validation/gates/run_gates.py` + `g1…g8_*.py` + `*.json` (TRACKED).
**Reused:** `xzzx_parser, qutrit_dm, rep_code, sv_sampler, seam, composed, window_channel,
audit/certify/{core,types,facade}, nm_source, nm_divisibility, qutip_*_channels, qutip_teacher_source`.

---

## SECTION F — REUSE VERDICT

| artifact | verdict | role |
|---|---|---|
| `nm_source.py` (RTN/1f exact + samplers) | **REUSABLE — source-DOF generator** | `z_t` (Axis-2); C2/C6/C7/C8a GT |
| `nm_divisibility.py` (rhp/blp/time_local_rate/intermediate_map_cp) | **REUSABLE — CP-divisibility detector** | G3a (C10a) + C4 positive control |
| `nm_wedge.py` envelope probe (simulate_envelope_observations, envelope_hat, analytic_envelope) | **REUSABLE — source-layer probe** | G3b coherence observable; source-layer ONLY |
| `nm_wedge.py` `coherence_wedge`, `fit_baseline_isotonic` (the wedge metric) | **CANNOT count as simulator evidence** | Ramsey-specific; G3b at source layer ONLY, **never G4**; the baseline-construction *shape* on QEC records (G5) is licensed, the *number* is not |
| `qutip_*_channels.py` (per-mechanism H,c Kraus) | **REUSABLE — DIRECT primitives** | the oracle-validated `{H_i,c_i}` fed to the assembler (G2) |
| `qutip_opensystem` 2-resonator readout (Heinsoo) | **NOT certified (scaling)** | EXCLUDED unless Δ-scaling non-critical |
| `qutip_teacher_source.py` (4 source→param exemplars) | **REUSABLE — pattern** | `Θ(z_t)` extends these |
| `tc_burst_certify` two-round toy obs model | **CANNOT count as G4 evidence** | minimal demo, not realistic QEC readout |

---

## SECTION G — EARNED-LINE

**ALREADY EARNED (source-layer + coherence-wedge ONLY):** an explicit memory-ful dynamical noise SOURCE
DOF (RTN/TLS/1f/shared-bath/burst), GT-validated; the source-physics gate at the source layer (RHP/BLP
v=γ_sw onset + Markovian-reads-0 control; finite-shot wedge with v*, motional-narrowing collapse,
unobservable-band reporting, out-of-family negative control) — **at the source layer**; a library of
oracle-validated CPTP first-principles per-mechanism Kraus primitives; the isolation contract, record
schema, certify harness + Anchor/Control ports, frozen-MWPM DEM, the real d3 XZZX substep schedule, the
qutrit-DM register + SvSampler emit, the seam composition — all production.

**NOT YET EARNED — NEW work the QEC simulator requires:**
1. `forward/joint_lindbladian.py` (NEW) — Axis-1 within-substep `L_substep` + ONE GPU `matrix_exp` +
   Choi→Kraus + the G2 commutator/composed-vs-joint gate. *Only per-channel expm exists; no joint-L
   assembler — channels are composed, not joint-propagated.*
2. `mechanisms/source_coupling.py` (NEW) — joint source→ALL-params fan-out. *Single-target exemplars exist;
   the joint fan-out does not.*
3. `mechanisms/coupled_teachers.py` (NEW) — `CoupledCycleTeacher` + `.markovian_baseline()`. *Does not
   exist.*
4. **G4 evidence (the decisive gap)** — the source's VERIFIABLE imprint on emitted records. **NO current
   nm_* result satisfies this** (all wedge evidence is Ramsey/source-layer). Separates "source earned" from
   "simulator earned."
5. **G6 on records** — shared-vs-independent cross-mechanism/cross-cycle difference on `{det,obs}` +
   shared-OFF collapse. Currently demonstrable only on the source latent — insufficient.
6. **G5 baseline rebuilt on QEC records** — best Markovian/CP-divisible competitor, each converged, fit to
   records (not the Ramsey envelope).
7. **G7 scramble + cheat-twin (C9.v)** and **G8 tracked gate suite**.

**Bottom line (faithful-infrastructure positioning):** earned-so-far = a validated non-Markovian source
layer + per-mechanism primitive library, at the source layer only (the non-Markovian NOVELTY lives here —
the `nm_wedge.py` coherence wedge). NOT yet built = the **Axis-1 joint-Lindbladian assembler** (the genuine
forward-FIDELITY contribution — the HEADLINE), the shared-latent physical fan-out (Axis-2), and the faithful
record plumbing. The simulator is "earned as faithful infrastructure" when **G2 (joint-L composed-vs-joint
fidelity)** + G1 (real schedule) + faithful channel ORACLES + G7 (isolation) + G8 (durability) pass, and
G4/G6 confirm faithful (corrqec-cross-checked, Pauli-layer-scoped) record emission. Slow is fast: front-load
**G1 + G2** on the single d3 vertical slice before broadening; G4/G6 are faithfulness checks, NOT a
novelty-discrimination headline (H2 capped that for mild sources).

---

## SECTION H — OPEN QUESTIONS (resolve with the user BEFORE building)

**RESOLVED (see the RESOLVED DECISIONS + POSITIONING blocks near the top):**
- ~~H1 G4 observable~~ → **RESOLVED: decode-relevant ΔLER under the correlation-blind frozen DEM, RE-FRAMED
  as a FAITHFULNESS check** (not |z|≥5 novelty; H2 capped the mild-source record-level imprint at the source
  layer). The 2-point "long-range correlation" form was retracted (H2 §6, Kam L4).
- ~~H2 effect-size~~ → **DONE + 3× verified** (`h2_effectsize_g4_prereg.md`): mild physical 1/f → no novel
  record-level ΔLER (capped at source layer). Drove the faithful-infrastructure repositioning.
- ~~H4 qutrit-DM vs qubit-window~~ → **RESOLVED: qubit-window (q=2, no leakage) for slice #1**; qutrit/leakage
  = slice #2.

**RESOLVED (prereg complete — `h3_h5_dt_g2band_prereg.md`):**
- ~~H3 substep `dt` provenance~~ → **RESOLVED:** per-substep `dt` bracketed from device values + SWEPT;
  sensitivity registered (the composed-vs-joint power law is `dt²` area-preserving / `dt⁴` fixed-Ω).
- ~~H5 G2 nonzero-pair band~~ → **RESOLVED (the headline G2 prereg):** ZZ×T2 exact-zero positive control
  (two-witness: structural `‖[L_A,L_B]‖≤1e-12` + channel superop `≤1e-10`); DR×ZZ band `1−F_e∈[6e-4,3e-3]`
  (physical, `dt²`) / `[4e-4,4e-3]` (fixed-Ω, `dt⁴`), metric = **process (entanglement) infidelity `1−F_e ≈
  ‖G‖²_F/d`** (METRICS.md forward-fidelity ledger, /d NOT /d²). The G2 build is gated on reproducing these.

**STILL OPEN — process only (not theory; resolved inline at build time):**
1. **[H6] Commit-gate sequencing.** The three NEW `src/qec_twin/` modules + tests require explicit user
   confirmation before commit (hard commit-gate). Build module-by-module with a separate-lane reviewer
   before each commit; the gate suite under `docs/` follows normal doc flow. (Process default — agreed.)
2. **[H7] Isolation check (simplified under faithfulness).** G7 isolation still holds (learner sees
   observations only). The binding test is **latent-scramble invariance** + the structural payload-key check;
   the cheat-twin is an optional reported diagnostic, not a gate. (Resolved — see G7/§B-8.)

**⚠ G4-FAITHFULNESS SCOPE (binding, anti-circular — user caveat 2026-06-26):** corrqec
(github.com/jkfids/corrqec) is a Stim FlipSimulator + temporal-mask Pauli generator. It can cross-check
ONLY the **reduced temporal-mask / matched-marginal PAULI generation** part of our records (the classical
correlated-Pauli structure). It **CANNOT** verify the full ANALOG joint-Lindbladian teacher (continuous,
leakage-capable, coherent). **Full joint-L fidelity is carried by G2 (composed-vs-joint) + the channel
ORACLE checks (CPTP vs INDEPENDENT analytic oracles), NOT by corrqec.** G4's corrqec cross-check is scoped
to the Pauli/temporal-mask layer only — else G4-faithfulness degenerates into a pseudo-independent
(circular) verification, exactly the toy the faithfulness protocol forbids.
