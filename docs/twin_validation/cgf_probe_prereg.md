# CGF probe — Pre-Registration (the branch decider; criterion on disk BEFORE the run)

Status: PRE-REGISTRATION, 2026-07-02. This document operationalizes the user-ratified probe spec of
`HANDOFF_coupling_simulator_2026-07-02.md` §5 (direction 1: classical-representability boundary for
measured-circuit records). The clean/messy CRITERION below is fixed before any probe execution; the
probe result selects Branch A (theorem hunt headline) vs Branch B (#1 demoted to a measured bound;
headline = #2 exact functional + #3 Bochner inverse). **The probe is win-win by design — either
branch is publishable core scope.** Parent prereg: `quantum_bath_slot_prereg.md` (M1/M2; engine +
imitator machinery certified there, incl. amendments A-M2-1/A-M2-2). Scoring language: METRICS.md
ledger; the record-level statistic here is the record CGF/distribution distance defined in §2
(declared instrument, (c); the ledgered D_comb is its process-level companion at M3).

## 0. What already exists (no reinvention)

- Quantum arm: 1q+1mode GKSL engine certified (closed form 7e-16; full-line unitary oracle 5e-5;
  thermal KMS fixed point 3e-16) — `outputs/quantum_bath_m2_dual_arm.py`.
- Imitator arm: matched complex-OU classical field (exact discrete updates, structural unitality
  3.6e-18) + deterministic-control absorption (post-Rz optimization; validated on the dispersive
  Lamb-phase instance: 0.2756 → 0.0073, φ_opt = 0.557 rad, resonant point untouched).
- The Lamb-phase trap is DISMANTLED BY CLASS DEFINITION (handoff §5, M1-prereg §1): imitator =
  classical Gaussian process + arbitrary deterministic time-dependent Hamiltonian control.
- Theory anchors: KMS asymmetry weight A = tanh(βℏω/2) = 1/(2N̄+1) (closed knob); unitality theorem
  (channel level); measurement-back-action discriminator argument (M1-prereg §4).

## 1. Protocol (both arms; exact where possible)

**Record:** fixed initial state |e⟩ ⊗ (mode/field stationary state). R rounds of
[evolve τ_m] → [projective σ_z measurement of the qubit, outcome x_r recorded]. NO reset — the
measurement conditions the mode (quantum arm) but never the field's law (classical arm). Terminal
record x⃗ = (x_1..x_R).

- **Quantum arm (EXACT, no sampling):** conditional-DM tree enumeration — propagate the joint
  qubit⊗mode DM per branch, project/renormalize at each measurement, accumulate branch
  probabilities. 2^R branches, dim = 2·n_max ≤ 12 ⇒ exact P_q(x⃗) to solver precision.
  Mode thermal occupation N̄ set per sweep point; collapse ops √(κ(N̄+1))b, √(κN̄)b†.
- **Classical arm (MC over field paths, GPU):** per path, the qubit undergoes unitary evolution
  (exact per-step 2×2, M2 machinery) + the SAME projective measurements (collapse of the QUBIT is
  common to both arms; the FIELD path is unaffected by outcomes — the class-defining property).
  P_cl(x⃗) = path-average of the per-path record probabilities (computed by branch enumeration per
  path — per-path probabilities, not sampled outcomes: kills the outcome-sampling variance; the
  only MC noise is over field paths). N ≥ 4e5 paths × ≥3 seeds.
- **Imitator control (operationalized class, declared (c)):** per-round deterministic unitaries
  U_r ∈ SU(2) applied immediately before each measurement, parameters optimized numerically to
  minimize the §2 distance. DECLARED: this is a compilable SUBSET of the full
  deterministic-control class ⇒ the measured Δ is an UPPER bound on the class-Δ. Consequence for
  verdict logic: a switch that fails to kill Δ triggers the CLASS-WIDENING check (richer control:
  mid-interval rotations) BEFORE any MESSY declaration (§4 order of operations).

**Matching (χ-pinned; CORRECTED per A-M2-3 before any probe run):** the classical coupling is
**H_cl = w(t)σ⁺ + w̄(t)σ⁻ (no ½ prefactor)** with ⟨w(t)w̄(0)⟩ = g²(N̄+½)e^{−λ|t|}, ⟨ww⟩ = 0 —
the direct c-number replacement of the quantum H_int = σ⁺B + σ⁻B† at the symmetrized mode
correlator. (The M2 run-2 arm carried a spurious ½ ⇒ ¼ power — the un-led review's BLOCKER;
the reinstated rate gate below guards it here.) The asymmetry sweep varies N̄ AT PINNED
SYMMETRIZED WEIGHT g²(N̄+½) = const (the χ-pinning discipline): the classical arm is then
IDENTICAL across the sweep; only the quantum arm's asymmetry A = 1/(2N̄+1) varies.
**Reinstated integrity gate (anti-¼-power):** measured classical-arm flip intensity vs the
quantum arm's at the base point — ratio ∈ [0.9, 1.1] CRASH gate. **Gate-object clarification
(registered before the results run was read):** "flip intensity" = the DIRECTION-SUMMED round-1
flip probability (the matched/symmetrized object; implemented gate band [0.8, 1.25] allowing
4th-order corrections). The DIRECTIONAL e→g ratio is registered physics, not a bug axis:
quantum ∝ (N̄+1) vs classical (N̄+½) per direction ⇒ expected ≈ 2 at N̄ = 0 — reported as a
companion statistic (the tanh knob's marginal cousin; first sighting: measured 2.0026 on the
run that fired the mis-implemented directional gate).

**Base operating point (declared, weak-coupling perturbative regime):** τ_m = 0.2 µs; κ = 2.5 µs⁻¹
(κτ_m = 0.5 — mode memory spans a few rounds); g₀ = 2π·0.25 MHz (g₀τ_m ≈ 0.31 rad); N̄ = 0;
R = 4 primary (16 outcomes), R = 8 structure check; n_max = 4 with occupation evidence.

## 2. The registered statistic

Primary: **Δ = max over the registered λ⃗-grid of |K_q(λ⃗) − K_cl^opt(λ⃗)|**, K(λ⃗) = ln Σ_x⃗
P(x⃗) e^{λ⃗·x⃗} (record CGF; x_r ∈ {0,1}), λ-grid = {−1, −½, ½, 1}^R ∩ (‖λ⃗‖₀ ≤ 2) (singles +
pairs — the leading-order sectors); cl^opt = imitator minimized over its control class.
Companions (reported, not gated): TV(P_q, P_cl^opt); the direction-resolved conditional lag-1
excess (the physical signature: post-emission re-absorption enhancement).

**Power precondition (gate, before any verdict):** Δ_base ≥ 10·SE_MC(Δ). Otherwise: increase N /
g₀ per the declared ladder (g₀ ×2 at most once, N ×4 at most twice) — a probe without power is a
no-verdict, never a clean.

## 3. Registered predictions ((b) unless marked; derivation sketch = (c) heuristic guide)

Sketch (NOT theorem-grade; the clean verdict does not depend on it): a recorded emission leaves a
quantum in the mode within lifetime 1/κ; conditional re-absorption is enhanced ∝ (N̄+1) vs the
classical arm's direction-symmetric posterior enhancement ∝ (N̄+½); each exchange carries g²τ_m ⇒
the connected two-record sector of Δ scales as g⁴, carries the asymmetry factor A, and requires
the mid-circuit measurement to exist.

- P1 (product structure / asymmetry switch): at pinned χ, Δ(N̄)/Δ(0) tracks A = 1/(2N̄+1) over
  N̄ ∈ {0, 0.1, 0.5, 2, 10} (A = 1, 0.83, 0.5, 0.2, 0.048); the N̄ = 10 point must satisfy the
  KILL criterion (§4).
- P2 (measurement switch): terminal-only variant (evolve R·τ_m, single measurement): Δ_term must
  satisfy the KILL criterion; theory ((a)-level, controllability): the restricted imitator with
  one pre-measurement U achieves the single-time distribution exactly up to MC noise.
- P3 (coupling power law): log|Δ| vs log g over g ∈ {g₀/4, g₀/2, g₀, 2g₀}: a SINGLE clean power
  law; registered slope band [1.6, 4.5]. (Pre-run amendment, 2026-07-02, before any execution: the
  first sketch registered 4 ± 0.5 from the conditional-re-absorption sector alone; a second
  derivation pass found a competing O(g²) sector — pathwise 2×2-unitary transition symmetry
  |V_01| = |V_10| holds for the imitator, but the JOINT record breaks it via occupation
  reweighting (selection), admitting classical direction structure at O(g²) and quantum excess at
  the same order. Two candidate leading exponents {2, 4} are therefore declared; the EXPONENT is a
  measured characterization, and cleanliness = single-power fit quality. The branch decision rides
  on the kill switches, not on the exponent value.)
- P4 (direction sign): the quantum arm's conditional re-absorption excess is POSITIVE (emission
  stored ⇒ enhanced return) at N̄ = 0.

## 4. THE REGISTERED CLEAN/MESSY CRITERION (the branch decider)

KILL criterion at a switch point: |Δ| ≤ max(3·SE_MC, 0.05·|Δ_base|).

- **CLEAN ⇔ (asymmetry switch kills: P1's N̄ = 10 point) ∧ (measurement switch kills: P2) ∧
  (single power law: P3 slope within band and fit residual < 10% per point).**
- Order of operations on any switch that FAILS to kill: (1) class-widening check (add mid-interval
  control rotations; re-optimize); (2) power re-check; only if the switch still fails ⇒ **MESSY**.
- ANY switch surviving after class-widening ⇒ conjecture shape wrong ⇒ MESSY ⇒ **Branch B**:
  direction-1 demoted to a measured bound ("records classically representable to within ε at
  code-realistic parameters" — still a paper result), headline shifts to #2 (exact silent-floor
  functional) + #3 (Bochner inverse + local-real-data demo). M3 proceeds unchanged either way.
- CLEAN ⇒ **Branch A**: direction-1 is the headline; theorem hunt (classical-representability
  boundary, Milz–Sakuldee–Modi instantiation — reading debt attaches HERE) runs parallel to M3.
- P4 failing (sign flip) is a FINDING to report either way; it does not decide the branch.

## 5. Epistemic classes

- (a): KMS knob values; controllability of the single-time distribution (P2's theory floor);
  unitality bound machinery inherited from M2.
- (b): P1–P4 as stated (bands/directions); a miss is a finding, never citable as fact.
- (c): the operationalized control class (declared subset + widening ladder); all thresholds
  (3·SE, 5%, slope ±0.5, power ladder); the derivation sketch in §3; base-point parameters.

## 6. Falsifiers / integrity gates (CRASH class)

- Engine/imitator certs inherited from M2 must pass on the probe's parameter points (rerun of the
  thermal fixed point at each N̄; unitality per seed; halving on the probe τ_m). **Halving-object
  clarification (registered before the results run was read; A-M2-1-lesson applied):** the halving
  bound is on the RECORD LAW (path-averaged probabilities, weak error ~dt², gate max|ΔP| ≤ 5e-6);
  the per-path max|ΔU| is a strong-order (~dt, tail-path-dominated) diagnostic, printed not gated.
- Consistency: P_q, P_cl^opt are probability vectors to 1e-10; quantum-arm branch probabilities
  sum to 1; classical-arm path-average moment check (G2-style) per seed.
- Zeno sanity: at g → 0 both arms give x⃗ ≡ initial-state record; Δ(g=0) = 0 to MC noise (null
  control — must pass, else instrument bug).

### 6.1 Numerics mechanics (registered before the results run was read; all (c)-class)

- **GPU-RK4 route** for quantum trees with dim > 64 (zvode-CPU replaced): stability bound
  λ_max = κ(2N̄+1)(n_max+1) with safety λ·dt = 0.35 (the first attempt omitted the thermal-excitation
  channel and went unstable at λ·dt = 1.79 — nan, caught by the halving gate); cross-validated
  against the exact expm route at N̄ = 0.5 to 1.67e-15 (CRASH gate 1e-8); first-segment halving
  ≤ 1e-9 per tree; level-batched (same-level branches are independent).
- **Mixed-precision optimizer**: the imitator search runs in c64/f32 batched over independent
  (point, seed) slices (loss = sum of independent slices ⇒ elementwise Adam ≡ separate runs);
  justification: MC statistical noise per record-probability entry (~5e-4 at N = 4e5) is ~500× the
  f32 accumulation error. The REPORTED Δ/TV are re-evaluated in c128 at θ*; the |Δ_c64 − Δ_c128|
  gap is printed as evidence. The quantum arm and every structural gate stay c128.

## 8. RESULTS + BRANCH DECISION (2026-07-02, run complete; log `outputs/logs/cgf_probe_v1.log`,
data `outputs/_cgf_probe_v1.npz`; all integrity gates passed: cross-val 1.67e-15, rate gate 1.0013
with directional companion 2.0026 vs 2.0, halving 4.54e-7, precision evidence |Δ_c64−Δ_c128| = 1.9e-7)

- **Power precondition PASS:** Δ_base = 1.9166e-2 ± 2.7e-5 (≥ 10·SE); KILL threshold 9.58e-4.
- **P1 asymmetry switch: KILLED** — Δ/Δ_base over A = {1, .833, .5, .2, .048}:
  {1, 0.732, 0.291, 0.084, 0.013}; the N̄ = 10 point (2.48e-4 ± 1.4e-5) is far under threshold.
  Measured scaling is SUPERLINEAR, Δ ∝ A^(1.4–1.8) — richer than the conjectured A¹ product form.
- **P2 measurement-off switch: SURVIVES (Δ_term = 0.1718) — and the registered criterion is
  hereby documented as MIS-REGISTERED (a theory error in this prereg, caught by the data):** the
  §3 claim "deterministic control forges any single-time statistic" is FALSE for an ensemble — the
  control is deterministic across paths, so it acts on the path-AVERAGED (mixed, unital-reachable)
  state; the quantum arm's dissipative purification toward |g⟩ exceeds any random-unitary
  ensemble's reachable populations. The terminal wedge is bounded below by the channel-level
  non-unitality gap — **our own M2 γ/2-theorem applied at the terminal readout**. The registered
  class-widening step is therefore THEOREM-MOOT: any deterministic-control widening keeps the arm
  inside (unitary ∘ random-unitary ∘ unitary) = unital, and the floor stands. (Proof replaces the
  compute step; recorded here per the §4 order of operations.) Additionally Δ_term (0.172) ≫
  Δ_record (0.019): mid-circuit measurements Zeno-pin both arms and SHRINK the wedge — the
  measurement-off variant changes the dynamical regime rather than isolating back-action; the
  conjectured factorization does not describe this operating point.
- **P3 power law: slope 3.622 ∈ [1.6, 4.5] but NOT CLEAN** (max fit deviation 17.6% > 10%):
  local slopes 3.90 / 3.74 / 3.19 — ≈ g⁴ at small g (the conditional-re-absorption candidate),
  saturating at g = 2g₀ (gτ_m = 0.63, perturbative-regime edge, declared).
- **P4 companion: direction MISS (finding):** quantum conditional flip excess = −4.06e-2
  (registered positive), classical-opt = +3.30e-3. Physics: at N̄ = 0, after an e→g emission the
  qubit sits in g where flips (re-excitation) are rare — the absolute conditional flip rate drops
  (emission anti-bunching), dominating the mode-conditional re-absorption enhancement the
  registration reasoned from. The classical arm shows the common-cause POSITIVE clustering.
  Both signs are informative record-layer structure.

**REGISTERED CRITERION ⇒ MESSY ⇒ BRANCH B** (per §4: a switch survived + power not clean).
Consequences (handoff §5, adopted): direction-1 is demoted to a MEASURED characterization —
and the probe delivered more than a bound (superseded by §9: decomposition = the surviving
methodology sliver, ingredients owned per adjudication): a two-component decomposition of the record wedge,
(i) a theorem-pinned channel-non-unitality component (measurement-independent; the M2 object,
0.172 at terminal-only) and (ii) a measurement-modulated asymmetry component (killed as
A^(1.4–1.8) → 0, growing ≈ g⁴ in the perturbative regime). Headline shifts to #2 (exact
silent-floor functional) + #3 (Bochner-type physicality inverse + local-real-data demo);
the quantum-bath slot remains core scope with these measured numbers; the structure lemma (#4)
is the methodology spine. **M3 proceeds unchanged** (Branch-B scoring emphasis: D_comb vs the
matched-BCF classical null at the code layer + the record-layer characterization).

## 9. Amendment A-P1 (2026-07-02, USER-CAUGHT novelty & theory-first challenge — accepted in full;
downgrades §8's interpretive language)

**The challenge (accepted):** the probe's OBSERVABLE layer was not theory-first'd — the mechanism
(M1) and channel objects (M2) were grounded, but the probe's registered predictions and kill
criteria were derived from scratch where standing literature exists. Receipts: two of four
registered predictions were falsified by the run itself in ways the literature predicts — P4's
sign (anti-bunching / sub-Poissonian jump statistics: Carmichael; Plenio–Knight) and P2's criterion
(unital = random-unitary on qubits: Tregub; Kümmerer–Maassen; classical simulability of qubit
channels: Crow & Joynt, PRA 89, 042123 (2014)). P1's physical content is the qubit-as-quantum-noise-
spectrometer concept (Schoelkopf et al. 2003; Clerk et al., RMP 82, 1155 (2010)): absorption/emission
asymmetry probes S(ω) vs S(−ω). The record-classicality concept space is held by Milz et al.,
"When Is a Non-Markovian Quantum Process Classical?" (PRX 2020; Kolmogorov consistency) and the
Smirne–Huelga–Plenio line — the reading the handoff assigned to direction-1 positioning and this
prereg deferred to "Branch A debt" was in fact due BEFORE any interpretive claim.

**Consequences:**
1. §8's "two-component decomposition is a REPORTABLE structure" is DOWNGRADED to: an INTERNAL
   branch-decider characterization, prima facie an instance of known physics (component (i) =
   the unital-simulability boundary; component (ii) = spectral-asymmetry detection); any paper
   language must cite the owners and may claim at most the QEC-stabilizer-record instantiation +
   machine-matched-null methodology — and only if an A9-style adjudication (independent search +
   精读, principal-verified quotes) finds that specific gap open.
2. The BRANCH B decision STANDS and is STRENGTHENED: the prior art occupies direction-1's theorem
   space, independently confirming that the theorem-hunt headline is dead. The paper headline
   (#2 exact silent-floor functional + #3 Bochner inverse + the structure lemma) does not rest on
   any probe claim.
3. READING DEBT NOW DUE (before any paper prose touches these topics): Crow–Joynt PRA 89, 042123;
   Schoelkopf et al. 2003 + Clerk et al. RMP 82, 1155 (spectrometer formalism); Milz et al. PRX 2020
   + a Smirne–Huelga–Plenio representative; waiting-time/anti-bunching canon (Carmichael).
   All paper attributions above are as USER-FLAGGED + general knowledge — to be 精读-verified
   before entering any committed claim.
4. Standing-rule sharpening (also to memory): theory-first must cover the OBSERVABLE layer and
   every registered KILL CRITERION — check against (i) the field's literature for that observable
   and (ii) the project's own standing theorems (P2 contradicted our own M2 γ/2 floor).

## 9.1 Amendment A-P1-READ (2026-07-02, the reading debt PAID — 5 papers 精读'd, D1/D2/D3 adjudicated)

The A-P1 reading debt of §9.3 is discharged. Five load-bearing papers were downloaded, converted, and
full-text close-read; five committed reading notes landed. arXiv ids VERIFIED before download (never
cited from the flagged ids alone); every quote below spot-verified against the extracted txt by the
principal (line numbers are `outputs/papers/<id>.txt` lines). Two papers (Crow–Joynt, Milz) were read in
FULL by the principal directly; the other three were drafted by delegated 精读 and the principal
verbatim-verified their load-bearing quotes against the raw txt.

**Reading notes (committed):**
- `docs/papers/reading_notes/crow_joynt_classical_simulation_quantum_noise_1309.6383.md` (PRA 89, 042123)
- `docs/papers/reading_notes/schoelkopf_qubits_spectrometers_quantum_noise_cond-mat-0210247.md`
- `docs/papers/reading_notes/clerk_quantum_noise_measurement_amplification_0810.4729.md` (RMP 82, 1155)
- `docs/papers/reading_notes/milz_when_nonmarkovian_process_classical_1907.05807.md` (PRX 10, 041049)
- `docs/papers/reading_notes/plenio_knight_quantum_jump_dissipative_quant-ph-9702007.md` (RMP 70, 101)

### D1 — Attribution verification (the §9 receipts table, per-item verdict)

**P1 → Schoelkopf/Clerk (qubit-as-spectrometer; absorption/emission asymmetry probes S(ω) vs S(−ω)):
VERBATIM-CONFIRMED.**
- Schoelkopf cond-mat/0210247: excitation reads S(−ω), relaxation reads S(+ω); "the detailed balance
  condition is p_e Γ↓ = p_g Γ↑" [txt:724]; steady-state "P = tanh(ℏω01/2kBT)" [txt:865]; at T=0 only the
  emission side survives — "there remains noise at positive frequencies … from zero-point motion" [txt:456].
- Clerk 0810.4729: non-symmetrized S[ω]=∫dt e^{iωt}⟨F(t)F(0)⟩ (Eq. 2.1); detailed balance
  S[+ω01]=e^{βℏω01}S[−ω01] (Eq. 2.7); Γ_up=(A²/ℏ²)S[−ω01], Γ_down=(A²/ℏ²)S[+ω01] (Eq. 2.6); the quantum
  discriminator verbatim — a "strictly classical noise source, ⟨F(τ)F(0)⟩ would be real" ⇒ S(−ω)=S(+ω)
  [txt:7677].
- Our probe's asymmetry knob A = tanh(βℏω/2) = 1/(2N̄+1), and the asymmetry-kill sweep that travels the
  classical limit A→0, ARE this concept + KMS detailed balance. **Owned — cite, do not claim.**

**P2 → (was "Tregub/Kümmerer–Maassen + Crow–Joynt"): CORRECTED. Crow–Joynt CONFIRMED; the theorem source
is Landau–Streater, NOT Tregub/Kümmerer–Maassen.**
- Crow–Joynt 1309.6383 (title: "Classical simulation of quantum dephasing and depolarizing noise"):
  proves classical random-unitary simulability of single-qubit DEPHASING (defined by [H_S,H_SB]=0, the
  eigenstate-preserving side) and DEPOLARIZING only; and states the non-unital obstruction QUALITATIVELY —
  a cooled qubit's population shift is an affine (non-unital) term "which is not zero" for the quantum map
  while the classical map has T^(Cl)_i0=δ_i0, so this "physical process cannot be mimicked by classical
  external noise in the sense of random unitary evolution" [txt:320-335]; conclusion: classical simulation
  fails "when the decoherence comes from randomness in the population" [txt:1524-1527]. CONFIRMED.
- CORRECTION: Crow–Joynt cite the underlying unital/positive-map result to **Landau & Streater**, PRA/Lin.
  Alg. Appl. 193, 107 (1993) [their ref 6] and Helm–Strunz for one-qubit existence [refs 5,7]. **Tregub and
  Kümmerer–Maassen are NOT cited by Crow–Joynt, and we have not 精读'd them ⇒ they are STRUCK from the
  citing set** (unread; not the source in hand). The "unital qubit channel = mixture of unitaries (random
  unitary)" theorem is attributed to Landau–Streater (secondary citation via Crow–Joynt; a direct 精读 of
  Landau–Streater is a small deferred debt IF that theorem ever becomes load-bearing in prose).
- Consequence for ② below: Crow–Joynt/Landau–Streater own the QUALITATIVE non-unital obstruction; neither
  quantifies a γ/2-type floor.

**P4 → anti-bunching canon (Carmichael; Plenio–Knight): VERBATIM-CONFIRMED.**
- Plenio–Knight quant-ph/9702007: on detected emission the two-level atom is "reset back to its ground
  state on photodetection" [txt:1063] (also [txt:1016]) ⇒ zero re-emission rate at zero delay, rising only
  as it re-excites — "for short times τ we expect to see anti-bunching" [txt:597]; the jump record is
  sub-Poissonian, "for a sub-Poissonian field (∆n)² < ⟨n⟩" [txt:699], Mandel Q<0. This IS the P4 physics
  (after an e→g emission the conditional flip rate DROPS = emission anti-bunching). **Owned.** Caveat (in
  the note): the clean reset-to-|g⟩ is a two-level/V-system result; it applies because our data qubit is a
  TLS, and must not be silently extended to multi-level/leakage.

**Record classicality → Milz/SHP (Kolmogorov consistency): CONFIRMED as FRAMEWORK owner, with a boundary.**
- Milz 1907.05807 (Egloff, Taranto, Theurer, Plenio, Smirne, Huelga — i.e. the SHP line is co-authored
  here, one paper covers both): K-classical ⇔ the multi-time outcome distribution satisfies the Kolmogorov
  consistency conditions (Def. 1, Eq. 9, marginalize an intermediate outcome ⇒ lower-order distribution);
  measurement setting = sequential sharp projective measurement of the SAME fixed observable (Fig. 1);
  coherence-absence is necessary but NOT sufficient; genuinely-quantum (KCC-violating for all instruments)
  processes exist "only in the presence of (quantum) memory" [txt:3256-3258]. CONFIRMED as owner of the
  temporal-classicality concept + the coherence-not-sufficient fact.
- BOUNDARY (decisive for ⑤): Milz has ZERO QEC content — exhaustive term search returns 0 matches for
  stabilizer / syndrome / error-correction / quantum-error / surface-code; "Pauli" appears only naming the
  σ_z/σ_x of a single-qubit toy. Milz owns the DEFINITION, not any QEC-record instantiation.

### D2 — A9-style gap adjudication (the five probe statements; (a) owned-cite / (b) folklore-unquantified /
(c) apparently-open). Verdict bias: prefer OWNED. Result: only ⑤ is (c), and only in a narrow conjunction.

- **① Asymmetry switch kills the modulation component (measured A^(1.4–1.8)):** **(a) owned-cite.** The
  physics — spectral asymmetry A=tanh(βℏω/2) is the quantum signature, classical limit A→0 kills it — is
  Schoelkopf/Clerk detailed balance (D1-P1). The specific superlinear exponent A^(1.4–1.8) is a **(b)**
  internal measured band (a miss-would-be-a-finding number, never citable-as-fact), NOT a contribution.
- **② Measurement-off survives = unital floor (with our γ/2 saturation constant):** split verdict.
  The QUALITATIVE claim (T1/relaxation non-unital ⇒ NOT representable by classical field + arbitrary
  deterministic control, since control keeps the arm inside unital = random-unitary) is **(a) owned-cite**:
  Crow–Joynt affine-obstruction + Landau–Streater unital-qubit theorem, and it restates our own M2 §4
  unitality theorem. The QUANTIFIED constant — D_Choi(AD(γ), best-unital) = γ/2 — is **(b)
  folklore-unquantified**: an elementary convex-geometry computation, found stated in none of the read
  sources; compute-and-state it, cite the qualitative owners, do NOT claim the constant as novel. **Not
  (c)-open** in any contribution sense.
- **③ Two-component record-wedge decomposition (channel-non-unitality ⊕ measurement-modulated asymmetry):**
  **(b)/owned-composite.** Component (i) = the unital-simulability boundary (Crow–Joynt/Landau–Streater);
  component (ii) = spectral-asymmetry detection (Schoelkopf/Clerk). The decomposition is an INSTANCE of two
  known physics pieces (as A-P1 already downgraded); reportable, cite both owners, no standalone novelty.
- **④ P4 sign contrast (quantum negative / anti-bunching vs classical common-cause positive):** **(a)
  owned.** Quantum side = Plenio–Knight/Carmichael anti-bunching / sub-Poissonian (D1-P4); classical
  common-cause positive clustering is elementary. A reportable finding, not a novelty.
- **⑤ QEC-stabilizer-record + mid-circuit-measurement + machine-matched-null classicality instantiation:**
  **(c) apparently-open — the sole residual gap, narrowly.** The framework (Kolmogorov-consistency temporal
  classicality) is owned (Milz/SHP); generic classicality-via-KCC with non-Markovian signatures is owned
  (Milz; also the very recent generic-two-level arXiv:2601.01122); non-Markovianity OF QEC syndrome/logical
  records is studied but DECODING-oriented (arXiv:2509.16887, 2512.08893), not a classicality test. The
  specific conjunction below is instantiated in NONE of the read/searched literature. Per the "prefer
  owned" rule the open claim is confined to that exact conjunction; every component is individually owned.

  **Residual-gap statement (precise wording, since (c)):** *"Instantiating the Milz–Egloff–Taranto–
  Theurer–Plenio–Smirne–Huelga temporal-process-classicality criterion (Kolmogorov consistency of the
  multi-time outcome distribution) on the STABILIZER-SYNDROME record of a QEC circuit whose data qubit(s)
  are coupled to a near-resonant quantum bath — testing record classicality against an EXPLICIT
  bath-parameter (βℏω, g, κ) boundary, with a machine-matched-null (matched-marginal HMM surrogate)
  separating genuine quantum-memory measurement-back-action from the circuit's own parity+measurement HMM
  memory."* This is NOT a theorem-hunt headline (Branch B already killed direction-1 as headline); it is at
  most a methodological-instantiation claim, it MUST cite all component owners, and it is A8-compliant
  (record statistics, not decoding — the SIMULATOR-not-decoder rule). It remains win-win: if the
  machine-matched-null shows no separable quantum-memory KCC excess at code-realistic rates, that is a
  reportable classical-forgeability BOUND, not a failure.

**Gap summary:** four of five probe statements are OWNED (①②-qual ③ ④) or folklore-unquantified
(②-constant); one (⑤) is apparently-open only in the narrow QEC-stabilizer-record ∧ explicit-boundary ∧
machine-matched-null conjunction. This CONFIRMS and discharges the A-P1 condition (§9.1: "may claim at
most the QEC-stabilizer-record instantiation + machine-matched-null methodology — and only if an A9-style
adjudication finds that specific gap open"): it does, narrowly. The Branch B decision STANDS and is
independently re-confirmed (direction-1's theorem space is occupied by the owners above).

### D3 — M3 observable-layer grounding (literature-anointed observables + criteria; the M3-prereg input)

For the M3 unit (2 data + 1 anc + 1 mode; `D_comb` + record layer), the field-standard observables, each
with its owner and predicted direction (quantum-bath arm vs matched-BCF classical-field arm at fixed
marginals). Metric discipline: ledger rows only (D_Choi / D_comb / record stats with machine-matched
nulls, A7); no LER/DEM/decoder in the validity chain (A8; SIMULATOR-not-decoder).

1. **Channel-layer non-unitality / random-unitary-representability** [Crow–Joynt 1309.6383;
   Landau–Streater]. Observable: the affine (non-unital) part of the block Choi/transfer matrix — the
   Bloch-fixed-point shift. Criterion: quantum arm carries a nonzero affine term (∼γ/2 scale); classical
   arm has EXACTLY zero (T^(Cl)_i0=δ_i0). Predicted: D_Choi(quantum, best-random-unitary) ≥ the γ/2 floor.
   (a)-exact channel witness.
2. **Spectral-asymmetry / detailed-balance (FDT) witness** [Schoelkopf cond-mat/0210247; Clerk 0810.4729].
   Observable: up/down rate ratio Γ↑/Γ↓ = e^{−βℏω} and steady-state polarization P_ss = tanh(βℏω/2).
   Criterion: quantum arm asymmetric (KMS), classical matched-BCF arm symmetric (Γ↑=Γ↓, P_ss=0); the
   βℏω→0 sweep must send the wedge→0. Predicted leading form: wedge ∝ tanh(βℏω/2). (a)/(b).
3. **Temporal-classicality / Kolmogorov-consistency test on the syndrome record** [Milz 1907.05807].
   Observable: the multi-time joint syndrome-outcome distribution P_n(x_n,…,x_1) and its KCC residual
   Σ_{x_j}P_n − P_{n−1} (Eq. 9). Criterion: classical-field arm satisfies KCC (record admits an underlying
   classical process); quantum-bath arm VIOLATES it — but only via measurement-back-action on the
   conditioned mode (Milz: genuine-quantumness requires quantum memory; our σ_z stabilizer record is
   exactly Milz's fixed-single-observable setting). Reference is NOT zero: subtract the machine-matched
   (parity+measurement HMM) null KCC residual (A7). Direction-only (b).
4. **Waiting-time / anti-bunching record statistic** [Plenio–Knight quant-ph/9702007; Carmichael].
   Observable: the direction-resolved conditional lag-1 flip excess / waiting-time distribution of the
   syndrome-flip record; Mandel Q. Criterion: quantum arm NEGATIVE excess (anti-bunching, Q<0) at N̄=0
   (emission resets to |g⟩, re-excitation suppressed); classical common-cause arm POSITIVE clustering
   (Q>0). TLS-grade regime (clean reset holds for the two-level data qubit). (a) sign witness.
5. **Non-Markovianity backflow witness (BLP)** [ledgered; Milz frames the memory requirement]. Observable:
   BLP trace-distance backflow / population revival on the mode-conditioned data qubit. Criterion: quantum
   arm backflow>0 underdamped (g≳κ/4), →0 overdamped/motional-narrowing control; classical arm none.
   Direction-only (b) (= M2 G-Q5 lifted to the block).

## 7. Run plan

One committed script `outputs/cgf_probe_v1.py` (asserts, printed evidence, flushed; no
multiprocessing). Registration block prints §3/§4 before any measured Δ. Compute: quantum arm
exact (seconds); classical arm GPU MC (N = 4e5 × 3 seeds × sweep points; minutes). ONE job at a
time (live desktop). Probe runs only after the M2 un-led review returns and any blockers are
resolved. Results appended to this doc as a dated amendment; branch decision recorded explicitly.
