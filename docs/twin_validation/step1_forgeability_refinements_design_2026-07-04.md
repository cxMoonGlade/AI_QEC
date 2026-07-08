# Step 1 refinements — the FORGEABILITY gate + two control fixes (predict-before-measure DESIGN)

**Status: DESIGN for un-led adversarial review, 2026-07-04.** Predictions written BEFORE any run; a miss is a
FINDING. Builds on `step1_shared_vs_off_lag2_Ndetect_derivation_2026-07-04.md` (round 1: TOTAL shared-vs-off
visible; common-mode-dominated; memory-alone borderline). This round installs the **anti-toy legitimacy
definition** the round-1 result forced, per user direction (2026-07-04).

**The correction this design implements (binding, user 2026-07-04):**
> *"visible vs off" (coupling present) ≠ "non-Markovian vs Markovian" (the real legitimacy claim).* The
> common-mode is **forgeable by a Markov model + a static shared offset** ⇒ it proves only *coupling present*,
> not *non-Markovian*, and per anti-toy discipline a forgeable signature is NOT legitimacy evidence. The
> **finite-time decaying memory** is the unforgeable fingerprint ⇒ **legitimacy must be anchored on the
> memory.** ([[project-nonmarkovian-wedge-must-be-coherence]], [[project-coupling-nonmarkovian-is-the-contribution]],
> [[feedback-anti-toy-ground-truth-protocol]], [[feedback-scrutinize-vacuous-checks]].)

## 0. Three refinements (all CPU add-ons to `step1_shared_vs_off_lag2_Ndetect.py`)

- **R1 — the FORGEABILITY gate (the anti-toy heart):** a `forge` null = **Markov (memoryless) per-round +
  static per-shot shared offset**, matched to the shared arm's marginals AND common-mode, that REPRODUCES the
  common-mode but CANNOT reproduce the finite-time memory. Turns "memory is the unforgeable signal" from
  argument into committed evidence, and settles that the common-mode does NOT count as legitimacy.
- **R2 — P5 fix:** the motional-narrowing control as a factor SWEEP `×1 → ×10⁴`, exhibiting the monotone
  `signal → 0` Markovian limit (the round-1 single `×100` only reached ratio 0.16 — under-averaged at R=12).
- **R3 — P4 fix:** report the memory `N_detect` as an explicit **conservative single-pair vs optimistic
  pooled BRACKET**, never a single gated verdict.

## 1. The forge null (R1) — construction

The shared conditional delta-rate `q_r` (derivation §2) carries two source imprints:
`μ_r = μ_instr(shot)  ⊕  p_deph,r`, where `μ_instr(shot)` (trajectory-mean readout/reset, S-1) is
quasi-static and `p_deph,r = ½(1−e^{−γφ_r τ_eff})` carries the finite-time `γφ` memory.

**`forge` keeps the first imprint verbatim and destroys the memory of the second:**
- **static per-shot offset:** keep `μ_instr(shot)` AS-IS (it IS the shared arm's quasi-static shared
  offset) ⇒ forge's common-mode `= Var_shot(Q_instr) =` shared's common-mode, EXACTLY.
- **memoryless per-round:** replace the ordered `γφ_r` sequence with an i.i.d.-across-rounds resample from
  the SAME pooled `γφ` marginal (independent draw per round per shot) ⇒ forge's `γφ` marginal `=` shared's
  (so `q̄` matched), but forge's `Cov(p_deph,r, p_deph,{r+k}) = 0` for all `k ≥ 1` ⇒ **no finite-time memory.**

So `forge` = {static shared offset (common-mode)} + {memoryless Markov per-round (no memory)} — the exact
Level-1 null the anti-toy claim must beat. It matches shared on {`q̄`, per-field marginals, common-mode} and
differs ONLY in the finite-time memory.

## 2. The discriminator — the lag-DECAY shape (an observable, no freeze needed)

The common-mode is **exactly flat** in lag (shot-constant ⇒ identical `Cov` at every `L ≥ 2`); the memory
**decays** in lag. So define the **memory-shape statistic**

$$ M \;=\; \mathrm{Cov}_{\text{shared}}(\text{lag }2) \;-\; \mathrm{Cov}_{\text{shared}}(\text{lag }L_{\max}), $$

with `L_max` large enough that the memory has died (`γφ` autocorr `e^{−2γ_min L}` negligible; the source's
slowest `γ_min=0.005/cycle` gives `e^{−0.01·L}`, so `L_max ≈ 8` retains ~92% — **CAVEAT flagged for review:
the 1/f slow tail may NOT have died by `L_max=8`; see §5 falsifier**). `M` cancels the flat common-mode and
leaves `mem(2) − mem(L_max) ≈ mem(2)`. Reported alongside the freeze-instrument memory-alone covariance
(round-1's direct isolation) as a cross-check — the two must agree.

**`p_ij`-level:** report `p_ij(lag)` for `lag = 1..L_max` on all three arms (`off`, `forge`, `shared`) — the
Kam multi-time vector. Predicted shapes: `off ≡ 0` (lag≥2); `forge =` flat common-mode floor; `shared =`
common-mode floor + decaying bump.

## 3. PREDICTIONS (predict-before-measure)

- **F0 (a-exact).** `forge` reproduces the common-mode: `Cov_forge(lag L) =` shared's common-mode floor,
  **flat** across `L ≥ 2` (equal at lag 2 and lag `L_max` within SE) ⇒ `M_forge = 0` within SE.
- **F1 (a-exact / the gate).** `M_shared > 0` and `≈ cov_mem(lag2)` (freeze-instrument), i.e. the shared arm
  shows a **resolvable lag-decay** that `forge` structurally lacks. ⇒ `M` is the unforgeable-memory detector;
  the common-mode does NOT contribute to it (`forge` has the full common-mode yet `M_forge=0`). **This is the
  committed proof that legitimacy lives in the memory, not the common-mode.**
- **F2 (b).** `N_detect(M)` ≈ the memory bracket: single-pair `~1e10` (slice-1) → `~8e6` (endpoint);
  pooled `~1e9` (slice-1) → `~5e5` (endpoint). Reported as the explicit **[single-pair, pooled] bracket**
  (R3), `τ_eff`-dependent. **Borderline at the Class-0 realistic endpoint** ⇒ legitimacy *motivates*
  Class-1/2 (not forced by the numbers).
- **F3 (c — R2 control).** Motional-narrowing factor sweep `×{1,3,10,30,100,300,1000,3000,10000}`: BOTH the
  common-mode AND the memory decrease monotonically; `M/M(×1) → 0` (the CP-divisible limit of the SAME 1/f
  source). Predict `M`-ratio `< 1e-2` by `×~10³–10⁴`.
- **F4 (honesty — the forgeability HIERARCHY, declared not tested here).** `M` separates shared from
  {static-offset, memoryless} (**Level 1**, this gate). A **single-RTN exponential** Markov process would
  still give `M>0` (**Level 2**); the **1/f power-law / multi-timescale** unforgeability vs any finite-order
  Markov (**Level 3**) is the deeper claim (h2 §2b `E(k)` residual-energy; RHP/BLP CP-divisibility) — Tier-2,
  NOT claimed here. Declaring this prevents over-reading the Level-1 gate as full non-Markovian certification.

## 4. Verdict reframe (what the report headlines)

- **Legitimacy headline = the MEMORY** (`M`, unforgeable at Level 1): borderline-feasible at the Class-0
  realistic endpoint (the [single-pair, pooled] bracket), `τ_eff`-dependent ⇒ motivates Class-1/2.
- **common-mode = a FAITHFUL real feature but FORGEABLE weak evidence** — reported (the source does imprint
  it), explicitly tagged as forgeable (F0: `forge` reproduces it), NOT the legitimacy headline.
- **coupling-present (TOTAL shared-vs-off) = easy/robust** but answers the *weaker* question.

## 5. Vacuity / circularity self-audit (rule II + [[feedback-scrutinize-vacuous-checks]]) — for the red-team

- **Is `M_forge=0` vacuous-by-construction?** Partly true-by-construction (memoryless ⇒ flat). NON-vacuous
  parts that CAN fail: (i) `forge` must genuinely MATCH shared's common-mode (could fail if the static-offset
  model can't reproduce the common-mode magnitude/lag-1) — a real check; (ii) `M_shared` must be RESOLVABLE
  (could be so small it is indistinguishable from `M_forge`) — a real check; (iii) if shared were memoryless,
  `M_shared` would be 0 too (correct null behavior). **Red-team: is this genuinely informative or a dressed-up
  tautology? Propose the strongest non-vacuous form.**
- **Circularity ([[feedback-anti-toy-ground-truth-protocol]]):** `M` is computed on the shared arm's own
  emitted `q` and compared to `forge` built from the SAME source draws — is comparing to a same-source shuffle
  an INDEPENDENT ground truth, or does it share a blind spot? (The Tier-2 upgrade is the theorem-grounded
  RHP/BLP null; is Level-1 forge enough to START?) **Red-team this.**
- **`L_max` choice:** `L_max=8` may not have let the 1/f slow tail die ⇒ `M` under-counts the memory (the
  slow tail leaks into the "floor"). **Red-team: does this bias the gate toward failure (conservative, OK) or
  success (dangerous)?** Falsifier: if `Cov_shared(lag)` has NOT plateaued by `L_max`, `M` is not clean.
- **Does `M` reintroduce the retracted shared−markovian subtraction?** `M` is a within-shared lag-difference
  (not shared−markovian); its magnitude equals the memory (the retracted number's true content), but read via
  the amplitude-swept clean-SE route, NOT the exchangeable-null 73%-retention SE. **Red-team: is this a
  distinction with a difference, or the retracted sizing in disguise?**

## 6. Epistemic classes

- **(a) exact:** F0 (`forge` flat lag≥2 = common-mode), F1 (`M_forge=0`; `M_shared=mem`), the common-mode
  `= Var(Q_instr)` identity.
- **(b) bands:** F2 `N_detect(M)` bracket.
- **(c) gates:** F3 motional ratio `<1e-2`; the [single-pair,pooled] feasibility bracket vs `1e6`.
- **Declared:** F4 hierarchy (Level-1 only); `L_max` bounded-simplification; S-1 common-mode modeling
  dependence (unchanged from round 1 — and now IRRELEVANT to the legitimacy headline, since `M` is
  common-mode-insensitive).
