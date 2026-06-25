# WS1 — Moments-Certification Pre-Registration (theory-first, before any run)

Status: PRE-REGISTRATION, 2026-06-24. Companion to `axisA_teacher_prereg.md` §7. The predictions are
written BEFORE the certification run (theory-first; a miss is a finding, not a re-fit). Confirmed scope
(user, 2026-06-24): **WS1 first** (certify the ③④ misspecification moments) → WS2 (⑤ spatial/temporal)
→ WS3 (0c hardened gate); **retire** the arbitrary-truncation sub-register full-joint and **derive the
correct truncated-sub-code construction**; **hold the mainline commit** until the moments path is
certified.

## 0. What WS1 closes (and why it is the priority)

Batch-1 — ① stochastic Pauli + ② coherent `rx` + ③ non-unital amp-damp + ④ WG leakage — is BUILT
(`outputs/teacher_prereg/twin_xzzx_teacher_fullmix.py`) and certify-GREEN at the **R=1 `DETECTOR_MARG`**
level (DM-oracle gap 8.5e-4 « band 1.8e-2; stim wiring R=1/R=2; corrupt-stab controls fired —
`_certify_fullmix.log`, 2026-06-24, RTX 5090).

The misspecification the twin must handle does **not** live in the marginals — the iid-Pauli foil matches
the per-detector on-rates *by construction*. It lives in the **R≥2 moments**: the round-to-round
detector correlation (③) and the cross-round leakage signature (④). These are the residual the iid model
**cannot** represent at the fitted marginals, i.e. the entire non-triviality of the teacher. **They are
not yet certified against the independent DM ground truth** (the standalone check died at the
sub-register L4 before reaching the R≥2 moments). WS1 certifies them.

## 1. The L4 diagnosis + the corrected ground-truth surface

### 1.1 Why the sub-register full-joint failed (L4 RED — `_b2_oracle_validation.log`)
`twin_dm_record_oracle_check.py` L4 (R=1 full-joint oracle-vs-carrier on the truncated register: sites
[0,1,2,3], stabs {0,1}) FAILS — TV=0.596, the X-type detector reads oracle 0.482 vs carrier 0.076.
**Root cause (refined by B1's independent derivation `subcode_truncation_derivation.py`, 2026-06-24): an
arbitrary truncation of an XZZX patch is not a valid sub-code, by EITHER of two failure modes.** (a) A
weight-4 XZZX stabilizer whose support extends beyond the active sites becomes, when restricted, a
**different operator** ⇒ the kept stabs may no longer mutually commute and the truncated codestate is not
their joint +1 eigenstate. (b) Even when the kept stabs ARE intact and commuting — B1 found the documented
L4 stabs {0,1} on [0,1,2,3] actually DO commute — an ill-defined or **anticommuting restricted LOGICAL**
on the truncated register breaks the logical sector; that was the specific L4 divergence (a placeholder
logical anticommuting with a kept stab). Either way the branch-sum projection enumerates an **ill-defined
instrument**, so the dense-DM oracle and the carrier diverge. (B1's own eigenstate harness hit the same
trap and was fixed — `init_logical` defaulted to `{0:'Z'}`, anticommuting with X-stabs on site 0.)

This is a **harness construction error in the sub-register check, not a `record_oracle` core bug**:
- at the FULL register all 8 stabs commute, the codestate is their joint +1 eigenstate, and the R=1
  `DETECTOR_MARG` single-stab projection matches the carrier to 8.5e-4 (GREEN);
- the oracle's Pauli-slice enumeration vs stim `PAULI_CHANNEL` (L6) is GREEN (TV=3.1e-4);
- the internal trace identities (L1 mass=1, L2 `E0+E1=I`) and the corrupt-stab control (L3) are GREEN.

### 1.2 The correct truncated-sub-code construction (the (a)-exact falsifying test)
A valid small-register full-joint GT requires: **(i)** keep only stabilizers whose **full** Pauli support
lies within the active sites (intact stabs); **(ii)** the active sites + kept stabs must form a
well-defined stabilizer sub-code (the kept stabs **mutually commute** — `[S_i, S_j]=0` exactly); **(iii)**
a **logical** operator supported within the active sites (else there is no logical sector to read).
Falsifying test (zero-tolerance, (a)-exact): the prepared sub-codestate is the joint +1 eigenstate of
every kept stab (`max|<S_i>-1| < 1e-10`) **and** the kept-stab commutator table is exactly zero.
For this d3 XZZX patch the **weight-2 boundary stabs** (weights `[2,2,2,2]`) are the intact-on-few-sites
candidates; the logical Z is **weight-3** on `{0,2,5}`. WS1 **derives** whether a `≥2`-intact-stab
sub-code that also carries the (restricted) logical exists. If yes, the gold-standard R=1 full joint is
recoverable there; if no, the R=1 full joint is FULL-register-only (OOM at depth-8 ≈ 50 GB) and is
formally retired.

### 1.3 The corrected GT surface (decision, user-confirmed)
**Retire** the arbitrary-truncation sub-register full-joint as a GT. The certified GT surface for WS1 is:
- **R=1:** full-register `DETECTOR_MARG` (single-stab projection, ~12.4 GB, feasible, GREEN) — the
  well-specified marginal floor (the part the iid learner fits).
- **R≥2 (CORRECTED 2026-06-24 — the earlier "full-9q feasible via pruning" was WRONG):** the DM moments
  (`det_marg` + `rr_corr` + `spatial_corr`) are computed by `record_oracle`'s depth-`(n_stab·R)`
  enumeration whose **peak live memory is the depth-`(n_stab·R)` clone stack** (one DM clone per
  recursion level on the active root-to-leaf path; ~100 GB at full-9q R=2). **Pruning shrinks breadth +
  time, NOT the depth** — a surviving path still descends the full depth — so **full-9q R≥2 moments are
  INFEASIBLE on the DM** and the scale routes to the **carrier-MCWF** (the DM-for-anchor / MCWF-for-scale
  split; the capability descriptor gates on `depth·copy`, OOM-as-data). The DM moments GT therefore lives
  on a **small VALID intact-stab sub-code** (B1 found **164**; e.g. `[0,2,5,7]` with intact stabs `{1,7}`
  carrying the canonical logical Z `{0,2,5}`), where `depth·copy` fits the budget — `dropped_mass`
  reported and bounded. The full-9q moments come from the **carrier**, trusted transitively via the
  sub-code DM↔carrier Gate-4 (L-Gate4) + the analytic ClosedForm ③ check (L-③, register-agnostic).
- The R=1 full **joint** is **not** needed for the misspecification claim (the discriminating power is the
  marginals — matched by the foil — **plus** the moments). It IS recoverable on a valid intact-stab
  sub-code (B1: 164 exist) as an opportunistic gold standard, off the critical path.
- **Consequence for §3:** the moments ledger rows (L-③, L-Gate4, L-iid, L-corrupt) run on the valid
  sub-code register (DM feasible); the full-9q moments are carrier + ClosedForm.

## 2. Predicted observables (theory-first, written before the run) — class (b) prediction bands

### 2.1 ③ non-unital → `RR_CORR`
The embedded classical record chain has an effective per-round flip pair `(p01_eff, p10_eff)` and the
connected round-to-round detector correlation obeys the flip-flip identity `E[d_r d_{r+1}] = p01·p10`
(transient-corrected; `ClosedFormAnchor`).
- **amp-damp ALONE** is the degenerate absorbing member `(p01, p10) = (0, γ)` ⇒ `E[d_r d_{r+1}] = 0` ⇒
  `RR_CORR ≈ 0`. **A single non-unital mechanism is round-to-round-correlation-blind.**
- **In the FULL mix** the Pauli ① depol(q) supplies `p01 > 0` (the symmetric depol flips ~`2q/3` each
  way), composed over the `n_cz` CZ layers a qutrit touches and stacked with amp-damp's `p10 += γ`:
  `(p01_eff, p10_eff) ≈ (n_cz·2q/3, 1-(1-γ)^{n_cz} + n_cz·2q/3)` (a declared composition approximation
  — §4). With `q=8e-4, γ=0.04`: per-CZ `p01≈5.3e-4`, `p10≈0.04`. **PREDICTION:** full-mix `RR_CORR > 0`,
  set by `p01_eff·p10_eff`, **small** (connected `|corr| ~ O(1e-3)`, consistent with the prereg's
  ~2.6e-3), and the **DM `rr_corr` matches `ClosedFormAnchor(p01_eff, p10_eff)` within the d3 (b)-band**
  (the XZZX geometry + the seam fold perturb the per-qubit form). This cross-check is **non-circular**:
  `ClosedFormAnchor` is exact classical propagation sharing no code path with the DM, the carrier, or stim.
- **Baseline + teeth (CORRECTED 2026-06-24):** the core's independent-DETECTOR foil (the product model
  `det_f`) has `rr_corr ≡ 0` *structurally* (it factorizes across `(round, stab)`) — that is the teeth
  check (the statistic must read 0 for genuinely independent detectors). A Pauli-ONLY TEACHER, however,
  generally carries a **nonzero BASELINE `rr_corr`** (the engine's persistent-data-state Markov structure
  under stabilizer measurement is not detector-independent), so the non-Pauli MISSPECIFICATION is the
  **EXCESS** `rr_corr(full-mix) − rr_corr(Pauli-only)` — the `coherent − incoherent` control method the
  original `record_difference_R` already uses — NOT `rr_corr(teacher) − 0`. The iid control MEASURES the
  Pauli-only baseline; the excess is the (b)-bet (a miss is a finding). [Earlier "Pauli-only → rr_corr ≈
  0" was wrong: it conflated the independent-detector foil with the Pauli teacher.]

### 2.2 ④ leakage → cross-round signature
`|2>` is populated at ~`pop2 = 4.68e-3` per CZ (qutip-confirmed) and is **inert under the qubit gates**
(it relaxes only via `g_seep`). **PREDICTION:** (i) a **longer-lag** `RR_CORR` tail than the 1-step ①③
Markov — `|2>` persistence creates multi-round memory, so the lag-≥2 round-to-round correlation exceeds
both the iid=0 baseline and the pure-Markov decay; (ii) the **leaked-readout `b`-sensitivity** of the
flip-rate **grows with R** — at R=1 `pop2` is tiny and only the terminal readout sees `|2>` (fullmix log:
flip-rate `0.1172→0.1173` across `b∈{0.5,0.75,1.0}`, flat, confirmed), so we predict a **measurable
slope by R=3–5** as `|2>` accumulates. Measure `flip-rate(b, R)` over `b∈{0.5,0.75,1.0}`, `R∈{1,2,3,5}`.
GT: the DM moments path replays the composite leak exactly; the `|2>`-population trajectory is exact on
the 1-qutrit DM (independent qutip reference already GREEN).

### 2.3 ⑤ deferred to WS2.

## 3. Moments-path constraint ledger (theorems + a falsifying test each)
- **L1 mass** (a): `total_mass + dropped_mass = 1` (prune-bounded), `|Σ − 1| < 1e-10`.
- **L2 instrument** (a): `E0 + E1 = I` per branch (child traces sum to the parent), `|gap| < 1e-12`.
- **L-bounds** (a): `rr_corr, spatial_corr ∈ [-1, 1]`; `spatial_corr` diagonal `= 1`; symmetric.
- **L-foil teeth** (a): the independent-DETECTOR foil ⇒ `rr_corr ≡ 0` (structural; must hold to the MC
  band). **L-iid baseline** (b): the Pauli-only teacher's BASELINE `rr_corr` is MEASURED (not assumed 0);
  the non-Pauli signal = the EXCESS `rr_corr(full-mix) − rr_corr(Pauli-only)` (the `coherent − incoherent`
  control method).
- **L-③ cross-check** (b): DM `rr_corr ≈ ClosedForm(p01_eff, p10_eff)` within the d3 (b)-band.
  **Run-1 (B3, 2026-06-24):** `p01_eff=5.33e-4` (=2q/3, the SI1000 Pauli flip — matches §2.1) and
  `p10_eff=4.05e-2` (≈γ) are extracted correctly from the composite channel; but the realized DM
  `rr_corr` (~0.004) is ~10× BELOW the single-qubit-chain prediction (~0.039) — the sub-code XZZX
  geometry + per-round-lumped seam suppress it. The wide `band_d3=0.05` "passes" but is a WEAK check:
  read L-③ as validating the **mechanism extraction** (p01_eff/p10_eff), NOT as a tight prediction of the
  realized correlation.
- **L-Gate4** (b): DM moments (exact, pruned) `≈` carrier moments (MCWF-sampled) within the MC band —
  the cross-construction check (dense-DM enumeration vs SV sampling are **different objects**; not
  circular).
- **L-corrupt** (c): the corrupt-stabilizer control guards the moments. **Run-1 finding (B3,
  2026-06-24):** at this LOW-NOISE sub-code the corrupt-stab control is GENUINELY INERT on the R≥2
  moments — a corrupted geometry yields a correlation of the same tiny magnitude (~0.004), so the
  corrupted-vs-emitted gap stays under the MC band (a near-zero statistic cannot host geometric teeth).
  Handled correctly (NOT by forcing a vacuous control): the geometry teeth come from a R=1
  `DETECTOR_MARG` cell (corrupt gap 0.45, FIRES decisively) + the moments' OWN teeth = the
  **MC-noise-limited DM↔carrier agreement** (the Gate-4 gap shrinks with N: 3.0e-3→1.2e-3 as N
  50k→800k — a biased/wrong carrier would plateau, not shrink) + the **foil-vs-teacher discrimination**
  (foil 1.7e-3 vs full-mix 7.5e-3). **Refinement for the orchestrator's full run:** add a HIGHER-noise
  regime where the moments are large enough to host the corrupt-stab geometric teeth directly.

## 4. Bounded simplifications (declared; unbounded ⇒ STOP)
- **prune floor** (`NUMERICAL_ZERO = 1e-12`): `dropped_mass` reported per run; the moments are
  conditional on branch survival, bounded by `dropped_mass`.
- **ClosedForm d3 prediction** is class (b) (`band_d3` — the XZZX geometry + seam perturbation); only the
  isolated single-qubit chain is (a)-exact.
- **effective per-round `(p01_eff, p10_eff)`** is an `n_cz`-fold composition **approximation** for the
  cross-check *target*; `n_cz` is per-qutrit-heterogeneous (boundary vs bulk) ⇒ use the representative
  bulk `n_cz` and **report the per-qutrit spread** (never a frozen pin). The precise value is MEASURED;
  only the direction/scaling is the (b)-bet.
- **sub-register full-joint retired** (1.3): a declared honest gap, not a silent omission.

## 5. Epistemic status (METRICS.md ladder)
- **(a) exact:** §1.2 falsifying tests, §3 ledger identities (L1/L2/L-bounds), the ClosedForm
  single-qubit chain, the `|2>`-population vs qutip.
- **(b) bands:** §2 predicted observable magnitudes/directions (a miss is a finding); the d3 ClosedForm
  `RR_CORR`; the DM-vs-carrier moments agreement.
- **(c) gates:** the MC bands; the corrupt-stab + iid-foil positive controls.
- The "③④ moments certified" verdict stays **PROVISIONAL** (convergence + independent oracles),
  reportable + usable for go/no-go, nothing built on it.

## 6. Build org (heavy-task rule) + deliverables
Three disjoint-ownership builders + an un-led reviewer; long GPU runs driven by the orchestrator in
self-controlled background (NOT inside a sub-agent — the 2026-06-23 delegated-long-job-killed lesson):
- **B1 — L4 / truncated-sub-code:** derive §1.2 (which intact-stab subsets form a valid commuting
  sub-code carrying the logical) with the (a)-exact falsifying test; RETIRE (mark, don't delete) the
  arbitrary-truncation L4 path and redirect it to the corrected GT surface (1.3). Owns `outputs/` only.
- **B2 — moments DM-anchor:** wire `RR_CORR` + `SPATIAL_CORR` into `DMOracleAnchor` (capability =
  feasible at full-9q R≥2 **with prune**, declared bound; route to `record_oracle` moments); add
  `SPATIAL_CORR` to `core.emitted_statistic` and ensure the anchor/emitted **shapes match** (same
  reduction); extend `CorruptStabControl.guards` to the moments. Short smoke only (the orchestrator
  drives the full-9q validation). Owns `src/qec_twin/audit/certify/` + one new `outputs/` script.
- **B3 — ③ non-circular cross-check + iid control:** the `ClosedFormAnchor(p01_eff, p10_eff)` cross-check
  driver + the Pauli-only iid positive control, as an `outputs/` validation script (no `src` change).
- **Reviewer:** un-led (stage problem + ultimate goal + the artifact only; no diagnosis/expected answers).

GPU-only; scripted-execution (asserts + printed evidence + flushed + `__main__` guard); mainline
`src/qec_twin/` changes are **commit-gated** (build in the working tree; do not commit — the user holds
the commit until the moments are certified).

## 7. Independent un-led review (2026-06-24) — verdict + dispositions

An un-led adversarial reviewer (given ONLY the stage problem + ultimate goal + the artifacts, no
diagnosis/expected answers) re-derived the result from scratch. **VERDICT: SOUND-WITH-CAVEATS.**

**Independently CONFIRMED solid (re-derived, not rubber-stamped):**
- `record_oracle` moments are EXACTLY correct — a from-scratch full-enumeration sharing NONE of
  `record_oracle`'s recursion matched `rr_corr`/`spatial_corr` to `max|Δ| = 3.5e-18` (machine zero);
  the seam fold + the reductions have no bug. **(This also validates the SPATIAL_CORR machinery — see C1.)**
- the sub-code is a valid stabilizer sub-code (kept stabs commute; joint +1 eigenstate `|<S>-1|≤4.4e-16`;
  logical deterministic); the 164-count + the positive controls reproduced.
- the non-Pauli `rr_corr` signal is GENUINE — EXACT excess = **6.45e-3** vs a Pauli-only DM baseline that
  is EXACTLY ~0 (`5.2e-12`, machine zero); the sampled `z~7` (N=1e6) UNDERSTATES the true separation.
- the Gate-4 has teeth — the carrier→DM gap shrinks as `1/√N` (3.97e-3→1.87e-3→7.8e-4 over N
  50k→200k→800k; an unbiased carrier converges, a wrong one plateaus); gross perturbations (3× leak,
  5×/10× γ) are CAUGHT (FAIL). DM (dense enumeration) ≠ carrier (SV-MCWF) — a genuine cross-construction.

**Caveats + dispositions (the all-GREEN ledger overstated these; honest corrections):**
- **C1 — `SPATIAL_CORR` carries no teeth on this sub-code.** The 2 kept stabs have DISJOINT supports
  ({0,1} vs {2,3} local) ⇒ exact spatial corr ~2.4e-5 (4 orders below band) ⇒ the row passes for ANY
  carrier (even 10× γ). The spatial MACHINERY is validated (the machine-zero brute-force match above),
  but the spatial Gate-4 ROW has no teeth here. **KEY (physics) reframe:** WS1's teacher is
  **SINGLE-SITE** (Pauli + coherent + non-unital + leakage, all per-qutrit — the two-qutrit crosstalk
  ⑤ is WS2), so `spatial_corr ~0` is ALSO the **CORRECT NULL** — there is no spatial-correlation
  mechanism to detect, not merely a disjoint-stab artifact. The nonzero spatial SIGNAL + the spatial
  Gate-4 TEETH are a **WS2 (⑤ crosstalk) deliverable**; WS1 confirms the null + validates the spatial
  machinery (ready for WS2). **Disposition:** report `spatial_corr` as the correct WS1 single-site NULL,
  NOT as a teeth-bearing PASS to lean on; the spatial teeth land in WS2.
- **C2 — band > rr_corr signal at N=1e6** (band 8e-3 vs signal ~7.8e-3): the single band-pass barely
  separates full-mix from Pauli-only; the **`1/√N` CONVERGENCE is the real teeth**, not the band-pass.
  **Disposition:** the headline rests on convergence (stated), not the band-pass.
- **C3 — the moments Gate-4 ran with NO in-rollup control** (`certify_cells(..., [], N)`): the
  corrupt-stab FIRES on `rr_corr` (gap 0.02 > band) but was moved to the R=1 marginal cell.
  **Disposition (code fix, next):** re-attach the corrupt-stab control to the `rr_corr` moments cells.
- **C4 — L-③ ClosedForm is a WEAK check** (band 0.05 swallows an 8.8× discrepancy: pred 0.039 vs DM
  0.0045). **Disposition:** it validates the MECHANISM EXTRACTION (`p01_eff`/`p10_eff`), NOT the realized
  `rr_corr` — the ledger `[PASS]` is downgraded to "mechanism-extraction PASS".
- **C5 — the ④ leakage §2.2 b-sweep was NEVER run** (kernel/ninja invocation failures, now fixed via
  `conda activate`). The reviewer verified the DIRECTION EXACTLY on the DM (leak-on b-slope grows
  R=1:~0→R=2:1.1e-5→R=3:1.7e-5; leak-off EXACTLY 0); magnitude ~1.7e-5 (sub-code) ⇒ likely
  sub-MC-resolvable at feasible N. **Disposition:** §2.2 is resolved by the reviewer's EXACT DM
  b-sensitivity (direction holds; magnitude small = a FINDING at the grounded WG rate); a full-teacher
  carrier-MC b-sweep is running for a faithful (likely flat-within-MC) number.
- **C6 — b3-S1 per-round-lumped:** WS1 certifies the moments MACHINERY + carrier agreement on a valid
  LUMPED sub-code, NOT the faithful per-CZ siting (transitively trusted; per-CZ validated at R=1
  full-register marginals). Already declared.
- **F3 correction (supersedes §2.1):** the Pauli-only teacher's `rr_corr` is EXACTLY ~0 (machine zero)
  on this register — REFUTING the §2.1 hedge "a Pauli-only teacher generally carries a nonzero baseline".
  The EXCESS framing (full − Pauli) is conservative but here Pauli≈0, so the excess ≈ the full-mix
  `rr_corr` directly. (The "independent-detector foil ≡ 0" teeth check stands.)

**Net:** the WS1 moment MACHINERY + the non-Pauli `rr_corr` signal are reviewer-confirmed sound
(PROVISIONAL, on a valid lumped sub-code). The overstatements are presentation/completeness (spatial
vacuity, band-vs-signal, the dropped control, the weak L-③) + one owed run (④ b-sweep — direction
already exact). Remaining: re-attach the `rr_corr` control (C3); land the ④ b-sweep number; then the
commit-gate.

## 8. Stress test (2026-06-24) — correctness + robustness before commit (3 testers + concurrent reviewer)

Per the user's "ensure correctness + robustness FIRST," a 3-disjoint-tester + CONCURRENT-un-led-reviewer
stress test over DEEP R=10, SMALL leakage, and ALL measurement arms A/C/B1/B2 × b legs.

**MAINLINE confirmed correct + robust (independently re-derived):**
- `record_oracle` EXACT at deep R — `prune=0` vs `1e-12` bit-identical at R=10,12; an independent
  from-scratch moment recompute matches to 0.0.
- **Small-leakage prune does NOT drop the |2> leakage branches** (`dropped_mass ~1e-30`; the |2> mass
  flows into the SURVIVING branches via the POVM weight, not separately-prunable tiny branches) — no
  silent leakage loss (the feared correctness risk is ruled out).
- **Carrier MCWF: no renorm-masked drift (T2)** — the UN-masked PRE-renorm `|‖ψ‖²−1|` stays ~1e-13 and
  does NOT grow over R=10. Full-9q kernel R=10: `norm_drift` bounded, no NaN/inf, sensible LER. (NB the
  kernel's returned `norm_drift` is the POST-renorm MASKED quantity — the genuine accumulation is the
  sub-code instrument's pre-renorm check.)
- **POVM `F0+F1=I` EXACT across all 16 (arm,b) cells;** arms A/C/B1/B2 + b are handled correctly in BOTH
  the DM (`_leak_flag_dephase`) AND the kernel (`sv_traj_d3.cu:390-417` leak-flag projection).
- NaN/inf/zero-norm/zero-variance/all-pruned guards robust.

**2 issues found — BOTH in the `outputs/` TEST HARNESS, NOT the committed mainline — and FIXED:**
- **(Tester-B) the simplified sub-code TEST carrier `SubCodeTeacher` ALIASED arm C to arm A** (it lacked
  the leak-flag dephasing the mainline DM + kernel both have) ⇒ the arm C, b=0.5, R≥2 DM-vs-carrier
  moments cell FAILED (N-independent bias). FIXED (`_batched_leak_flag_project`); verified: carrier@A≠@C,
  carrier@C≈DM@C (gap 2.4e-3 « band), wrong-arm teeth fire. The MAINLINE carrier (kernel) was always
  correct for arm C.
- **(Reviewer F1) the validation default `WS1_N=100000` sat BELOW the rr_corr corrupt-stab control's
  firing threshold (~1.46e5)** ⇒ the script self-FAILed at its default. FIXED (default → 200000 + a
  guard); verified GREEN at default (control FIRES).

**Characterizations (not bugs):** the DM-vs-carrier EXACT moments cross-check caps at R≈6 on the 2-stab
sub-code (the depth-`(n_stab·R)` enumeration is exponential; R=10 is carrier-only + the convergence /
EXCESS teeth — the DM-for-anchor / MCWF-for-scale design); the carrier-MC resolution of a tiny leakage
signature is √N-limited (importance sampling is needed only for very small rates, a known property).

**Net:** the mainline ③④ moments code is **correct + robust** (reviewer-confirmed) across deep R, small
leakage, and all arms × legs; the two test-harness issues are fixed + verified. ⇒ the mainline is clean
for the commit-gate.
