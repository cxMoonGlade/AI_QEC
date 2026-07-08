# DESIGN (predict-before-measure) — simulator coupling/non-Markovian LEGITIMACY via the direct-correlation observable

**Status: DESIGN for review, 2026-07-04. No code until this is reviewed (un-led) + user-approved.**
Predictions are written BEFORE any run; a miss is a FINDING, not a re-fit.

**Scope (binding, [[feedback-simulator-is-goal-twin-is-next]]):** this is a SIMULATOR faithfulness +
legitimacy test. The deliverable is the faithful forward simulator; its record `{det,obs}` is the product.
**Coupling is a SWITCH** (`coupling_arm` on/off): the simulator must faithfully **EXPRESS BOTH** regimes —
the UNCOUPLED (baseline / Markovian) errors that occur *without* coupling (switch off), AND the coupled
(non-Markovian, correlated) errors (switch on). **The uncoupled mode is a first-class, independently
deliverable output** whose whole point is to be a baseline **on par with established simulators** — because
to prove the COUPLED simulator correct we must first prove the UNCOUPLED one correct (user 2026-07-04).
Validity is **TWO AXES**, the uncoupled one foundational:
- **AXIS A — uncoupled-baseline cross-simulator EQUIVALENCE (foundational, run FIRST).** switch=off output
  is EQUIVALENT to INDEPENDENT, ESTABLISHED references — **split by error class, because our simulator must
  support NON-PAULI (this is a core requirement, not optional) and Stim CANNOT** (frontend README §54: the
  Stim path is "Stim-Pauli noise, not... leakage/qutrit"):
  - **Pauli / Clifford slice** `==` **Stim** (exact, `StimCliffordAnchor`) — the established external Pauli
    reference;
  - **NON-PAULI** (T1 amplitude damping, coherent non-Clifford, leakage/qutrit) `==` the
    previously-developed non-Pauli machinery (REUSE, do not reinvent): **QuTiP-cuQuantum `mcsolve`**
    (`frontend/qutip_cuquantum_backend.py`, `axis1_qutip_cuquantum_probe.py` — an established external
    open-system H/c_ops solver, ≤4-qutrit probe) + the **exact qutrit-DM** (`carrier/exact/qutrit_dm.py`,
    what `DMOracleAnchor` wraps) + the existing **leakage-oracle cert**
    (`axis1_qutrit_leakage_oracle_certification_manifest` vs `leakage_channel_super`);
  - optionally `==` SI1000 / PyMatching-decoded LER at recommended settings ([[feedback-baselines-pristine]]).
  Together (Pauli==Stim + non-Pauli==QuTiP/qutrit-DM, twirling gap declared where they overlap) this
  establishes our baseline is on-par with standard tools — a genuinely INDEPENDENT ground truth (Stim AND
  QuTiP are different implementations), stronger than matching our own DM oracle alone. **Honest limit:**
  QuTiP `mcsolve` probe ≤4 qutrits, exact qutrit-DM ~9 qutrits — non-Pauli equivalence is validated on
  small feasible fixtures and extrapolated (declared), Pauli==Stim scales to full d.
- **AXIS B — coupled-delta faithfulness + legitimacy (builds on A).** With the baseline proven equivalent:
  **(1b) coupled-record faithfulness** — the shared/coupled record matches the INDEPENDENT oracle; **(2)
  anti-toy legitimacy** — the coupling adds a feature DISTINGUISHABLE from the uncoupled/Markovian record
  (the §2–§3 direct-correlation observable) — else the coupling is a toy.

**`off` (Θ(0)) is NOT "zero errors":** it carries the full schedule-baseline error model (T1/T2/SPAM/gate
at the baseline `Axis1PrimitiveParams`), just without source modulation or cross-round correlation. Hence
`off` does DOUBLE DUTY — the faithful **uncoupled-error product** (validated in 1a) AND the structural-zero
**legitimacy null** (validated in 2). Every coupled record is baseline-error + coupling superimposed, so 1a
also guarantees the baseline content inside the coupled record.

The correlation observables below (`p_ij` / `RR_CORR`) are **simulator-internal validation instruments**
([[feedback-simulator-not-decoder]]: "record-char; p_ij = internal instrument"), NOT a learner-recovery /
`do()` / characterization deliverable (that is the separate, out-of-scope twin project).

**Purpose:** replace the retired G0-v2 / G6 observables (which mis-measured legitimacy) with the correct
one, fixing the three diagnosed errors — grounded in what the scout confirmed already exists in-repo.

---

## 0. The three errors this design fixes (each confirmed in-repo by the scout)

- **Error A — wrong observable + wrong null.** G0-v2 used an exact record-distribution **2-point TV** between
  two parameter points (`outputs/twin_validation/g0_v2_effectsize_rsweep.py::_tv`). G6 used a `p_ij` /
  count-autocov **z-score of shared MINUS an exchangeable "markovian" permutation null**. Both cancel the
  first-order signal and force second order: `g6_null_model_rederivation_2026-07-03.md` proves the
  round-delta stream is **MA(1)** (off-arm `p_ij(lag1)=μ=p_ro+p_rs−2p_ro p_rs≈0.0149`, `p_ij(lag≥2)=0`
  exactly), a permutation-invariant common-mode (~8.7e-5) cancels in shared−markovian, and the markovian
  permutation null is **EXCHANGEABLE, retaining ~73% of the shared lag-1 covariance at R=12** → the
  discriminator is second-order → `N_detect ∈ [1.1e10, 1.2e15]` (the retracted "sub-floor"). Kam
  arXiv:2410.23779 separately proves the 2-point detector autocorrelation alone is insufficient (→ need
  multi-time / lag≥2).
- **Error B — source too weak AND mis-sited.** Slice-1 uses `amplitude_radns=1e-4`, `gamma_phi_sensitivity
  =0.35` (`source/coupling.py`), which `h2_effectsize_g4_prereg.md §7.B` registers as **Kam Class-0
  (data-qubit ZZ/T2, provably BENIGN)** — the wrong error class for a record-detrimental signal. No
  physical 1/f-amplitude or Harper-Flammia LER bracket is wired (the knobs are class-(c) design defaults).
- **Error C — Prop IW-1 over-generalized.** IW-1's second-order suppression is ONLY the coherent
  (commutator, `Im K`) sector. The classical 1/f memory here is **stochastic** (`Im K ≡ 0`) — it is
  DIRECTLY present in the record correlation (`p_ij(lag≥2)`), first-order-estimable, not commutator-sector.

## 1. Reuse map (the machinery already exists — do NOT reinvent)

| need | reuse (path) | note |
|---|---|---|
| direct-correlation observable | `docs/twin_validation/gates/g6_ablation.py::spitz_p_ij(cube,lag)` / `s2_count_autocov` | already lag-resolved Spitz `p_ij` on the simulator's own `{det,obs}` cube |
| canonical exact `p_ij` | `src/qec_twin/hardware/pij.py::spitz_pij_exact` + `spitz_pij_delta_se` | EXACT Eq.13 + analytic SE (METRICS.md-ledgered); unify g6's local dup to this |
| multi-time / multi-site statistic | `src/error_coupling_simulator/certify/core.py` `Statistic.RR_CORR` / `SPATIAL_CORR` (`reduce_rr_corr`/`reduce_spatial_corr`) | round-to-round + same-round Pearson; **exactly 0 for independent-bit foils**; shared between emitted side AND DM anchor (apples-to-apples) |
| independent ORACLE (faithfulness) | `certify/anchors/dm_oracle.py::DMOracleAnchor` (RR_CORR feasible full-9q R≥2 via pruned branch tree) + `certify/anchors/closed_form.py` (analytic RR_CORR via `E[d_r d_{r+1}]=p01·p10`) | genuinely independent code paths; feasibility encoded as data |
| cross-simulator EQUIVALENCE — PAULI (Axis A) | `certify/facade.py::StimCliffordAnchor` (independent stim Clifford slice) + `external/baselines/` (pristine Stim / PyMatching) + SI1000 dataset circuits | Pauli slice only (Stim CANNOT do non-Pauli, README §54) |
| cross-simulator EQUIVALENCE — NON-PAULI (Axis A) | `frontend/qutip_cuquantum_backend.py` + `axis1_qutip_cuquantum_probe.py` (QuTiP `mcsolve`, ≤4 qutrit) + `carrier/exact/qutrit_dm.py` (exact qutrit-DM) + `axis1_qutrit_leakage_oracle_certification_manifest` (leakage cert vs `leakage_channel_super`) | the previously-developed non-Pauli machinery — REUSE; QuTiP = a different established implementation (independent GT) |
| genuine CP-divisible NULL (theorem) | `outputs/teacher_prereg/nm_divisibility.py` (RHP/BLP/`intermediate_map_cp`, `is_markovian`) + `nm_source.motional_narrowing_rate` | FROZEN (removed from live pkg 2026-07-03); single-qubit toy — REVIVE/extend, see §3 |
| off / structural-zero null | `CoupledCycleTeacher.off_source()` (`teachers/coupled_cycle.py:924`, Θ(0)) | the correct comparison arm (§3) |
| controls + anti-vacuity | `g6_ablation.py` PC/planted-memory (P2/P3); `certify/core.py::certify_cells` controls-first (inert control ⇒ FAIL; zero-firing ⇒ FINDING) | reuse verbatim |
| execution scaffold | `outputs/run_*.sh` + `docs/twin_validation/gates/_gate_common.py` (`round_delta_by_round`, `cluster_bootstrap_se`, `content_hash`, `GATE_RESULT`, `python-exit`) | scripted-execution discipline, verbatim |

## 2. The corrected observable (error A, part 1)

**Primary:** the **absolute lag≥2 direct correlation** the coupling imprints on the record —
`p_ij(lag≥2)` (Spitz Eq.13) and/or `RR_CORR` at lag≥2 — measured on the SHARED arm, read as an absolute
quantity, NOT as a shared−markovian difference.
- Why lag≥2: the MA(1) instrument floor is `p_ij(lag1)=μ`, `p_ij(lag≥2)=0` EXACTLY (a-exact,
  `g6_null_model_rederivation`). So any nonzero `p_ij(lag≥2)` on the shared arm is **pure coupling
  memory** — the 1/f source has long-range memory, so it populates lag≥2 where the instrument is silent.
- `RR_CORR` (certify) is the multi-site/round companion, exactly 0 for independent bits.
- **Explicitly RETIRED:** the G0-v2 2-point TV and the shared−markovian z-score as the legitimacy verdict.
- Multi-time (not 2-point-alone) per Kam: report `p_ij` across lags 2..L (a vector), not a single lag.

## 3. The corrected null (error A, part 2 — the decisive fix)

The legitimacy comparison is **shared vs OFF** (`off_source()`, Θ(0)), where `p_ij(lag≥2)=0` and
`RR_CORR=0` **structurally** — NOT shared vs the exchangeable `markovian_baseline()` (which retains ~73%
of the covariance and forces second order). This is the scout's own recommended fix and the core of
error A: measure the correlation directly against a genuine zero, don't subtract an exchangeable null.

**Two null tiers (predict-before-measure registers both):**
- **Tier 1 (v1, structural-zero):** shared-vs-off. `off` is Θ(0) — the amplitude-0 arm; `p_ij(lag≥2)`/
  `RR_CORR` are structurally zero there (up to shot noise). The legitimacy signal = shared `p_ij(lag≥2)`
  distinguishable from 0. Cheapest, cleanest, already wired.
- **Tier 2 (theorem-grounded CP-divisible, a BUILD):** revive `nm_divisibility` (RHP/BLP =0 for
  `exp(-Γt)`) + `nm_source.motional_narrowing_rate` (the exact Markovian LIMIT of the SAME 1/f source,
  `v≪γ_sw`) and extend from the single-qubit toy to the coupled teacher's channel family. This gives a
  null that is Markovian **by a theorem**, not a shuffle (Kattemolle: a shuffle/twirl can itself look like
  a distinct process). Registered as the rigorous upgrade; Tier 1 is sufficient to START.

Reason the shared-vs-off + absolute-lag≥2 route is expected to beat the retracted `1e10–1e15`: it removes
the ~73%-retaining subtraction penalty (compare to 0, not to an exchangeable null) — error A's efficiency
gain — and error B (realistic amplitude) enlarges the absolute correlation.

## 4. The source (error B) — realistic bracket + the architectural fork

- **Arm-in-scope-now (Class-0 amplitude sweep):** sweep `amplitude_radns` / `gamma_phi_sensitivity` from
  the slice-1 mild default up a **realistic bracket**. ⚠ **Open decision (D1):** no physical 1/f-amplitude
  bracket is wired today; the knobs are class-(c) design defaults. This design must EITHER anchor
  `amplitude_radns` to a cited flux/charge-noise 1/f spectroscopy value (theory-first gap-fetch), OR
  declare the sweep as class-(c) "up to the physically-grounded channel baseline `γφ=1/30000` (T2=30µs)"
  and report the effect-size vs that. Recommend the former (a real anchor) — flagged for the user.
- **The architectural fork (h2 §7.B, registered finding):** Class-0 (data ZZ/T2) is provably benign; a
  record-DETRIMENTAL coupling needs re-siting Θ onto **Class-1 (ancilla/syndrome SPAM)** or **Class-2 (CZ
  depolarizing)** — which the current dense carrier does NOT support on the ancilla axis (a build). So:
  - if the Class-0 lag≥2 correlation IS detectable vs off at realistic amplitude ⇒ the non-Markovian
    feature is legitimate (non-toy) as a faithful *correlation* feature — DONE for slice-1;
  - if it is NOT detectable even at realistic Class-0 amplitude ⇒ registered finding: legitimacy of a
    record-*detrimental* coupling requires the Class-1/2 ancilla-axis build (out of this test's reach; a
    declared dependency, NOT a "sub-floor" verdict).

## 5. Independent ground truth (non-circular)

- **Faithfulness of BOTH arms (record vs oracle):** `DMOracleAnchor` computes `RR_CORR`/`SPATIAL_CORR` +
  `DETECTOR_MARG` by an independent exact-DM path (RR_CORR feasible full-9q R≥2 via the pruned branch tree —
  realistic det-rate ~0.12 prunes) + `closed_form.py`'s analytic `E[d_r d_{r+1}]=p01·p10`. **The oracle
  validates BOTH the UNCOUPLED (off) arm AND the coupled (shared) arm** — the off arm's baseline detector
  marginals + `RR_CORR≈0` must match the oracle's memoryless prediction (validity 1a: faithfully expressing
  the no-coupling errors), and the shared arm's marginals + `RR_CORR` must match the oracle at the coupled
  value (1b). NOT `cross_mechanism_correlation()` (same-engine).
- **Observable closed form:** `g6_ablation.independent_gt_lag1_pij` (two formula routes must agree to 1e-12)
  + `g6_null_feasibility_from_constants.ma1_identity_selfcheck` (i.i.d.-bit MC self-check of the p_ij closed
  form) — validate the observable's algebra BEFORE any GPU run.
- **From-scratch record oracle:** `g0_v2_effectsize_rsweep._scratch_record_dist` pattern (independent numpy
  embedding/projectors/reset-Kraus/XOR) + its negative control (drop a channel layer ⇒ must diverge).

## 6. Controls (reuse; controls-first anti-vacuity)

- **off / structural-zero** (the null itself; must read ≈0 up to shot noise).
- **PC1** zero-delta (shared vs shared ⇒ statistic ≈ 0) and **PC2b** instrument-liveness (a known-nonzero
  planted memory must move the statistic) — from `g0_v2` / `g6_ablation` P2/P3 (planted common-mode + AR(1)).
- **Motional-narrowing collapse:** the fast-bath limit (`v≪γ_sw`, `nm_source.motional_narrowing_rate`) ⇒
  the lag≥2 memory → 0 (the CP-divisible limit of the SAME source). KEPT from the reconstruction's KEPT list.
- **Controls-first scoring** (`certify.certify_cells`): an inert control forces FAIL; an anchored PASS with
  zero firing controls downgrades to FINDING — never a vacuous PASS.

## 7. Predictions (predict-before-measure; class (b) bands unless noted)

- **P0 (AXIS A — uncoupled-baseline cross-simulator EQUIVALENCE; run FIRST):** the switch=off output is
  EQUIVALENT to established simulators on a matched model, **split by error class** — the **Pauli/Clifford
  slice** matches **Stim** (`StimCliffordAnchor`) to the declared tolerance; the **NON-PAULI** part
  (T1/coherent/leakage) matches **QuTiP `mcsolve`** + the **exact qutrit-DM** (with the declared twirling
  gap where Pauli/non-Pauli overlap); and `RR_CORR(off)≈0` / `p_ij(lag≥2)=0` structurally (memoryless
  baseline). Optional: matched-model decoded LER matches SI1000 / PyMatching. A miss here is a baseline
  FINDING that BLOCKS Axis B — the coupled delta means nothing until the baseline is proven on-par, on BOTH
  the Pauli AND the non-Pauli slice. This is the "prove the uncoupled version correct first" requirement
  made the foundational gate.
- **P1 (coupled-record faithfulness + the legitimacy claim):** on the SHARED arm at a realistic source amplitude, `p_ij(lag≥2)` (and
  `RR_CORR` lag≥2) is **nonzero and distinguishable from the off arm (structural 0) at feasible N** — with
  `N_detect` ORDERS below the retracted `1e10–1e15` (shared-vs-off + realistic amplitude removes the
  exchangeable-null penalty and enlarges the signal). Direction + a registered `N_detect` band from the
  §5 closed form recomputed at the realistic amplitude BEFORE the run.
- **P2 (vanishing controls):** the signal is ≈0 on the off arm and collapses in the motional-narrowing
  limit (ratio < 1e-2). (c) gate.
- **P3 (first-order-direct, error A/C):** the signal is recovered by the DIRECT absolute lag≥2 statistic
  (vs off), NOT requiring the shared−markovian difference; the stochastic memory lives at lag≥2 (not the
  commutator sector). Falsifier: if it is only recoverable as a shared−markovian second-order residual,
  error A's null-fix is wrong.
- **P4 (the honest architectural prediction, (b)):** at Class-0 siting, the realistic-amplitude lag≥2
  correlation MAY remain below the threshold that a record-detrimental (ΔLER-relevant) claim needs ⇒ then
  the registered finding is the Class-1/2 re-siting dependency (h2 §7.B), reported honestly — NOT a
  "sub-floor is faithful" verdict.
- **Falsifier for the whole design:** if shared-vs-off `p_ij(lag≥2)` at realistic amplitude is STILL
  `N_detect ≥ 1e10` (i.e. no better than the retracted shared-vs-markovian), then either the source is
  fundamentally record-silent at Class-0 (⇒ P4/Class-1-2) or the observable choice is wrong — a FINDING.

## 8. Epistemic status (METRICS ladder)

- **(a) exact:** the MA(1) closed form (`p_ij(lag1)=μ`, `p_ij(lag≥2)=0`); the Spitz Eq.13 identity; the
  `E[d_r d_{r+1}]=p01·p10` closed form; `RR_CORR=0` for independent bits; `RHP=BLP=0` for `exp(-Γt)`.
- **(b) bands:** P1 (`N_detect`), P4; the DM/closed-form faithfulness band (RR_CORR match).
- **(c) gates:** P2 control collapses; the `N_detect ≤ feasible` decision rule; the realistic-amplitude
  bracket (D1); the motional-narrowing ratio < 1e-2.
- **Provisional:** the headline "the simulator's non-Markovian coupling feature is legitimate (non-toy) at
  realistic source" stays PROVISIONAL until P1 passes vs the independent DM oracle with the controls firing.

## 9. Bounded simplifications (declared)

- **Tier-1 off-null instead of the theorem-grounded CP-divisible null (class (c), bounded):** off is Θ(0),
  a structural-zero (not a re-solved Markovian generator); it is a valid legitimacy null for the *classical*
  correlation (the coupling adds memory the off arm structurally lacks). Tier-2 (nm_divisibility revived)
  is the rigorous upgrade; the bound is the RHP/BLP residual of the off arm (expected 0 by construction).
- **d3 fixture, R rounds (class (c)):** the 4q/5q fixtures + the R-sweep; feasibility per the DM-oracle
  capability descriptor. Surface scaling later.
- **Class-0 siting (declared dependency, NOT a hidden simplification):** §4 fork; if it caps the signal,
  that is a registered finding routing to the Class-1/2 build.

## 10. Execution (scripted; GPU serial; H6 for src)

Reuse the committed-runner scaffold (`outputs/run_*.sh` pattern: `set -o pipefail`, pinned python, `tee`,
`${PIPESTATUS[0]}` → `python-exit`, `GATE_RESULT`, sha256 `content_hash`). The observable + null + oracle +
controls run as one committed gate script (extend the `docs/twin_validation/gates/` pattern, or promote the
p_ij/RR_CORR wrapper into `src/error_coupling_simulator` — a small refactor, H6-confirmed). ≥3 disjoint
builders + un-led reviewer if it grows; GPU serial, offload heavy to `ssh spark`. Regenerate CODE_MAP after
any src change.

## 11. Open decisions for the user (before build)

- **D0 — Axis-A equivalence references (split by error class):** minimum = **Pauli** slice `==` Stim
  (`StimCliffordAnchor`, wired) + **NON-PAULI** `==` QuTiP `mcsolve` + exact qutrit-DM (the
  previously-developed machinery — Stim can't do non-Pauli). Add vendored/dataset baselines (SI1000 /
  PyMatching-decoded LER)? On which matched noise model + what tolerance (exact for the Clifford slice; a
  band for the twirling gap and for the ≤4-qutrit / ≤9-qutrit non-Pauli feasibility extrapolation)?
  (Recommend: Stim + QuTiP/qutrit-DM both required; SI1000 LER as a second confirmation.)
- **D1 — realistic-source anchor:** anchor `amplitude_radns` to a cited 1/f-noise spectroscopy value
  (theory-first gap-fetch), or declare the sweep class-(c) up to the T2=30µs channel baseline? (Recommend
  the anchored value.)
- **D2 — null tier:** start with Tier-1 shared-vs-off (fast, wired), or build Tier-2 (revive
  `nm_divisibility` for the coupled teacher) first? (Recommend Tier-1 first; Tier-2 as the rigor upgrade.)
- **D3 — Class-0 vs Class-1/2:** run the Class-0 amplitude sweep now (answer P1/P4 for slice-1), or treat
  the Class-1/2 ancilla-axis re-siting (h2 §7.B) as a prerequisite build? (Recommend Class-0 sweep now — it
  is cheap and its P4 outcome decides whether the Class-1/2 build is even needed.)
