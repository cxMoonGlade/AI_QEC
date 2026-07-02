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
quantum arm's at the base point — ratio ∈ [0.9, 1.1] CRASH gate.

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

## 7. Run plan

One committed script `outputs/cgf_probe_v1.py` (asserts, printed evidence, flushed; no
multiprocessing). Registration block prints §3/§4 before any measured Δ. Compute: quantum arm
exact (seconds); classical arm GPU MC (N = 4e5 × 3 seeds × sweep points; minutes). ONE job at a
time (live desktop). Probe runs only after the M2 un-led review returns and any blockers are
resolved. Results appended to this doc as a dated amendment; branch decision recorded explicitly.
