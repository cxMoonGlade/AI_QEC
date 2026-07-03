# Part-B constraint ledger + independent-GT + bounded-simplifications (gates G4–G8)

Faithfulness-protocol three-piece for the **record-gate lane** (Builder 3B). The
predictions/statistics/PASS conditions are registered in
`docs/twin_validation/coupled_teacher_round_gates_prereg.md` (§3 G4, §4 G5, §5 G6,
§6 G7, §7 G8, §8 the three-piece, §9 the predictions table). THIS note is the
by-the-builder record required before "done": it points each implemented falsifying
test to its prereg ledger row id and states what is grounded vs UNRESOLVED.

## I. Constraint ledger (prereg §8.1) — where each falsifying test is IMPLEMENTED

| # | constraint (prereg §8.1) | implemented falsifying test (this lane) | file:check |
|---|---|---|---|
| L1 | TV symmetric, ∈[0,1], TV(P,P)=0 | (Part A owns; no TV in Part B) | — |
| L2 | record probs sum to 1 ± 1e-8 | teacher's own manifest gate (`_tables_for`, C-6) runs on every emit; gates re-assert arm shapes | g4/g5/g6 `_emit_arm` shape asserts |
| L3 | branches = 2^M, no silent pruning | (Part A / teacher own it) | — |
| L4 | ζ live only on superposition edges | (Part A PC2b owns) | — |
| L5 | no check shares engine with referee | (Part A from-scratch GT owns) | — |
| **L6** | Spitz p_ij validity domain (denom>0, √-arg≥0); direct-cov cross-check on one arm | g6 S1 enforces the domain, flags+excludes+counts invalid pairs; the lag-1 p̂_ij is cross-checked on ONE arm vs the direct covariance formula at tol 1e-12 (the independent-GT, §8.2) | `g6_ablation.py::spitz_p_ij` + `::independent_gt_lag1_pij` |
| **L7** | DEM decode is correlation-blind (no teacher truth in the DEM) | g4 builds the matched DEM from PUBLIC fixture geometry + the record-empirical pooled shared-arm rate ONLY (never `teacher.truth`); a `construction_hash` over (fixture, R*, p, placement) pins the build; a truth-fed DEM would change that hash | `g4_imprint.py::build_matched_dem` (hash `dem_construction`) |
| **L8** | ablation arms differ where registered and ONLY there (marginals preserved) | g4 P-G4-3 pooled-det-rate marginal z-test (shared vs markovian); g6 C3/C4 | `g4_imprint.py::marginal_rate_check`; `g6_ablation.py::C3/C4` |
| **L9** | params must vary per round (dead-override toy, R1) | g6 C1 reads evaluator truth: per-cycle γφ spread > 0 on ≥90% of inspected shots + cross-mech corr(ζ,γφ) ≥ 0.9 | `g6_ablation.py::c1_positive_control` |
| **L10** | the statistic pipeline detects planted correlation and stays silent on none | g6 P1 (i.i.d. Bernoulli at shared marginals → \|z\|<3) + P2 (planted common-rate multiplier → z≥5) in-script stubs | `g6_ablation.py::p1_pipeline_null` / `::p2_pipeline_planted` |
| **L11** | cluster structure of batched shots enters the SEs | §2.4 trajectory-cluster bootstrap; preconditions FAIL if n_traj < 2000 | every gate `_cluster_bootstrap` + `_precondition_n_traj` |

## II. Independent ground-truth checks (prereg §8.2) — one per part (this lane owns Part B)

- **g6 (Part B core):** the ledgered Spitz p̂_ij at lag 1 cross-checked on ONE arm
  against the DIRECT covariance definition — an algebraic-identity check that trips
  on an implementation typo in EITHER path. Two independent formula routes on the
  SAME shot data, tolerance 1e-12. This is NOT a check vs the engine's own oracle
  (both routes are hand-written here from the shot bits). Implemented:
  `g6_ablation.py::independent_gt_lag1_pij`.
- **g4 (Part B):** corrqec is the registered EXTERNAL generation reference (contract
  §H Pauli/temporal-mask scope). It is NOT vendored (verified: absent from
  `external/baselines/`), so its absence is declared `DEFERRED(not vendored)` and it
  is NEVER simulated by our own generator (anti-circular). When the orchestrator
  vendors github.com/jkfids/corrqec pristine and passes `--corrqec-root`, the gate
  runs the §H-scoped 2-moment match. Implemented: `g4_imprint.py::corrqec_crosscheck`.

## III. Bounded simplifications (prereg §8.3) — class + bound

| simplification | class | bound / honesty statement |
|---|---|---|
| Matched DEM from pooled empirical rate | c | pooled inverse `p=½(1−√(1−2·d̄))` is (a)-exact on the declared i.i.d.-flip model; placement + pooling are (c); per-detector residuals REPORTED unbarred; MC error of d̄ ~ √(d̄/(N·n_det)) printed |
| Uniform finals noise p_fin = p_anc | c | declared placement; both arms decoded by the SAME frozen DEM ⇒ ΔLER insensitive at first order |
| Trajectory-mean readout/reset (slice-1) | c | inherited from the ratified slice scope; g6 S3 (r3) is the in-round leak witness |
| corrqec deferral when not vendored | c | `DEFERRED(...)` string in evidence; the gate NEVER fails on absence; scope §H Pauli-layer only |
| Batching S > 1 | c | recorded in every gate JSON; within-shot statistics unaffected; cluster SEs mandatory (L11) |
| Markov-k Laplace smoothing α=0.5 (g5) | c | comparator-fit smoothing constant; the comparator is reporting-only (no novelty bar) |
| g6 P2 planted g ~ N(0, 0.5²) | c | sized to be comfortably detectable (z≥5); a pipeline self-test constant, not a physical claim |
| g7 N_g7 = 64 | c | isolation is structural, not statistical; declared |

## Grounded G4 DEM-export entry points (brief handback requirement)

VERIFIED against source this session (NOT UNRESOLVED):

- `qec_twin.simulator.compiler.compile_code_spec(spec) -> CircuitIR` (public geometry;
  no teacher metadata) — compiler.py:22.
- Noise placement: `qec_twin.simulator.noise.NoiseBuilder().before_measurement(
  "X_ERROR", p, basis="Z")` inserts `X_ERROR(p)` before every Z-basis measurement
  (matches `M/MZ/MR/MRZ`, i.e. every ancilla round measurement AND every final data
  measurement) → `.build() -> TargetedStimNoiseSpec`. noise_spec.py:487 + the
  `_Z_MEASUREMENTS`/`_rule_matches_measurement` matcher. `target_filter` is an exact
  instruction-target tuple filter (never an inserted-target override) — used only if
  a per-instruction split is needed; the default `before_measurement` already lands on
  all measured targets, which is the registered "before every ancilla round + final
  data measurement" placement.
- `qec_twin.simulator.stim_source.CircuitIRSource(circuit_ir).compile(noise) ->
  CompiledCircuit`; `.noisy_circuit` is the noisy `stim.Circuit` — stim_source.py:111.
- DEM: `compiled.noisy_circuit.detector_error_model(decompose_errors=True)` (native
  stim; also wrapped by `stim_io.detector_error_model`) — stim_io.py:108.
- Decode: `qec_twin.hardware.m4_decode.decode_dem(dem, dets) -> [shots,
  num_observables] uint8` (frozen PyMatching, upstream defaults) — m4_decode.py:236.

Public-geometry reconstruction per fixture: `default_coupled_code_spec(rounds=R*)`
gives the 5q public spec (`coupled_teachers.py:401`, the SAME public fixture the
teacher uses, WITHOUT the teacher/evaluator truth). The 4q variant has no public
package helper, so G4 reconstructs its public 1-check `CodeSpec` inline from the
G0-v2-registered public parameters (3 data + 1 X-check ancilla, ZZ edge (0,3),
`logical_z2`) — public geometry, no truth. `dem.num_detectors == B` (= R*·n_stab) is
asserted (P-G4-5) so any geometry drift trips loudly.

A-DET-1 detector-column map (grounded correction): `teacher.sched.record_layout_ref["detectors"]`
carries per-detector `name`/`keys`/`coords` but **NOT** a `kind` field (verified in-source:
`analog_schedule._record_layout_ref` rebuilds the detector list from `DetectorDef` circuit steps
with name/keys/coords only, analog_schedule.py:1161). The underlying `RecordLayout` DOES carry
`kind` ("round_delta"/"final_closure", record_layout.py:117/130), but that is not what the
schedule exposes. So the gate discriminates round-delta vs final-closure by the DECLARED NAME
PREFIX — `delta:<check>:round<r>` vs `final:<check>` (record_layout.py:199/203) — which IS the
A-DET-1 declaration order. Detector count = (R-1)·n_stab round-delta + n_stab final-closure =
R·n_stab (matches the teacher's `detector count == rounds·n_stab` assert). A name matching neither
prefix fails the column-map loudly.

R* >= 3 precondition (grounded): there are R-1 round-delta rounds, so the lag-1 timelike pairs
(and the Markov-k interior) need R-1 >= 2, i.e. R* >= 3. `require_min_delta_rounds` fails G5/G6
loudly on a degenerate small-R* config rather than reading nan. G0-v2's decision tree expects R*
well above this (4q R* in {12,16}, §1.5), so this is a tripwire, not an expected path.

Two-tier L0 rule (§3.2): after the DEM is built, the gate inspects `dem_errors(dem)`
for any observable-carrying mechanism. On these fixtures the final data `X_ERROR` on
the logical qubit (data 2) participates in both its final-closure detector AND the
observable, so the observable-flipping mechanism is graphlike (has a detector), not
detector-less — PyMatching accepts it. If NO observable-flipping mechanism is present
(or PyMatching rejects the build), the gate sets `dem_can_flip_observable=false`, marks
the decode-delta sub-check `VACUOUS-structural`, and reports the raw obs-rate delta as
the record statistic (honest, per §3.2).
