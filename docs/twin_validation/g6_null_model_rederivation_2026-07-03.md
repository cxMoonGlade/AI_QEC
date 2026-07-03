# G6 null-model re-derivation + record-level feasibility (Track B / F1, 2026-07-03)

**Status: DERIVATION — written BEFORE re-running any gate (predict-before-measure, theory-first).**
This document re-derives the null distribution of the G6 record statistics on a *correct*
`CoupledCycleTeacher`, proves (a-exact) that the §5-as-registered pass/fail conditions cannot
behave as registered, sizes the genuine cross-cycle memory signal, and concludes that the
memory discriminator is sub-detectable at the feasible cap — a **faithful property, not a
failure**. It is the basis for the §5 re-registration (`coupled_teacher_round_gates_prereg.md`
§5 + §10 amendment log).

Committed-constant evidence: `outputs/twin_validation/g6_null_feasibility_from_constants.py`
(CPU-only; runner `outputs/run_g6_null_feasibility.sh`; artifact
`outputs/twin_validation/g6_null_feasibility.json`; run 2026-07-03, `python-exit=0`). Every
number below is printed by that script from the committed `SourceCouplingConfig` /
`OneOverFDriftSource` defaults; the (a)-class MA(1) identity additionally carries a from-scratch
i.i.d.-bit Monte-Carlo self-check independent of the dense emitter.

**Epistemic frame (binding, [[feedback-anti-toy-ground-truth-protocol]]):** there is NO ground
truth — everything is simulation. The teacher is a noise model we *specify*; the closed forms
below are FORMAL derivations of that specified model (they catch mis-registration / plumbing
bugs, never certify correspondence to nature). Each quantitative item is tagged **(a) exact**,
**(b) prediction band**, or **(c) heuristic gate/decision rule** per METRICS.md.

---

## 0. Scope — what carries the coupling, and what G6 was asked to show

The slice-1 coupling rides on `zeta × gamma_phi` at the **channel** level (G2-certified) and on the
cross-cycle memory of the shared source. Two facts fix the record-level scope
(`coupled_teachers.py` S-1/S-4, design §4):

- **Only `gamma_phi` varies per round.** `zeta` is record-dead under realistic 1/f draws (S-4;
  G0-v1 zeta-only record TV ≈ 4.3e-11), and readout/reset are held at the **per-trajectory
  mean** (S-1, single-slot instrument). So within one shot's R rounds, the ONLY per-round-varying,
  temporally-ordered field is `gamma_phi`.
- **The negative control matches marginals.** `markovian_baseline()` permutes each field's cycle
  order (`independent_baseline_trajectory_to_params`), preserving every one-field marginal and
  destroying temporal order. So any shared-vs-markovian discriminator must be **second-moment or
  higher** — a first-moment (rate/marginal) test is matched to zero by construction.

G6-as-registered (§5.1–5.4) asks the records to show cross-cycle correlation that is present in
`shared`, killed in `markovian`, and absent in `off`, tested by the **raw** Spitz p_ij / count-
autocovariance z-scores against zero. The reviewer (F1) showed this cannot behave as registered.
This document derives why, and what is true instead.

---

## 1. The record structure: the delta stream is MA(1)

Round-delta detector, check `c`, round `r ∈ [1, R-1]` (`record_layout.py:110-135`):

$$ D_{c,r} \;=\; m_{c,r-1} \oplus m_{c,r}, $$

the XOR of two **consecutive raw ancilla measurement bits**. Consecutive detectors share a bit:
`D_{c,r}` and `D_{c,r+1}` both contain `m_{c,r}`; `D_{c,r}` and `D_{c,r+2}` share nothing. So for a
fixed check the delta stream is the **first difference** of the measured-bit stream — a **moving-
average process of order 1 (MA(1))**: 1-dependent, with structural correlation at lag 1 and
**exactly zero** correlation at lag ≥ 2, *whatever* the measured-bit marginals, as long as the
measured bits are independent across rounds.

The measured bit of a quiet stabilizer is
$$ m_{c,r} \;=\; \tilde s_{c,r} \,\oplus\, e^{\text{ro}}_{c,r} \,\oplus\, e^{\text{rs}}_{c,r-1}, $$
i.e. the true syndrome XOR this round's readout error XOR the previous round's reset error carried
into this ancilla. Readout and reset errors are independent per round, so the per-bit **effective
flip probability** is
$$ \mu \;=\; p_{\text{ro}} + p_{\text{rs}} - 2\,p_{\text{ro}}p_{\text{rs}}. $$
With the committed base values `p_ro = 1e-2`, `p_rs = 5e-3`:
$$ \boxed{\mu = 0.014900} \quad\text{(a-exact).} $$

---

## 2. (a-exact) The off-arm closed form — §5.4 "Off ≈ 0 exactly" is FALSE

`off` sets amplitude 0 → constant `Θ(0)` params → i.i.d. measured bits `m_r ~ Bernoulli(μ)`. For
the delta stream `D_r = m_{r-1} ⊕ m_r`:

- Mean: `⟨D_r⟩ = 2μ(1-μ) = 0.029356` (the off-arm delta rate).
- Lag-1 covariance (shared bit `m_r`):
  `Cov(D_r, D_{r+1}) = μ(1-μ)(1-2μ)²`.
- XOR mean: `⟨D_r ⊕ D_{r+1}⟩ = ⟨m_{r-1} ⊕ m_{r+1}⟩ = 2μ(1-μ)`, so the Spitz denominator is
  `1 - 2·2μ(1-μ) = (1-2μ)²`.
- **Spitz p_ij at lag 1** (the ledgered Eq. 13):
  $$ \hat p_{ij}(1) = \tfrac12 - \sqrt{\tfrac14 - \tfrac{\mu(1-\mu)(1-2\mu)^2}{(1-2\mu)^2}}
     = \tfrac12 - \sqrt{\tfrac14 - \mu(1-\mu)} = \tfrac12 - \left(\tfrac12 - \mu\right) = \boxed{\mu}. $$
- **Lag ≥ 2:** no shared bit → `Cov = 0` → `p_ij = ½ - √(¼) = 0` (exact).

So on a *correct* teacher the off arm reads **`p_ij(lag1) = μ ≈ 0.0149`, not 0**, and lag ≥ 2 = 0.
The X-check's `μ` carries a small extra physical-dephasing term (`≈ 0.5·γφ_base·τ_eff`, §6); the
Z-check's `μ = p_instr` exactly. Pooled ≈ 0.0149 + small.

**From-scratch self-check (a):** an i.i.d.-bit Monte-Carlo (draw `m ~ Bernoulli(0.0149)`, XOR to
deltas, compute the exact moment-Spitz) gives `p_ij(lag1) = 0.014889 ≈ μ` and `lag2 cov = -6.7e-7 ≈ 0`
— reproducing the closed form from a reconstruction that shares no code with it
(`g6_null_feasibility_from_constants.py::ma1_identity_selfcheck`).

### 2.1 Consequence: C3/C4 "flat" clauses are unsatisfiable at usable N

G6-§5.2 requires the off arm to read `|z(S1@lag1)| < 3` (C4) and the markovian arm likewise (C3).
But `p_ij(lag1)` is a **nonzero constant ≈ 0.0149** whose bootstrap SE shrinks as `~1/√N`. Hence
`z = 0.0149 / SE → ∞` as `N` grows: at `N = 1e6` the off arm reads `|z| ≈ 15`, not `< 3`. The
registration inherited the *hardware* p_ij intuition (far-apart detectors as the null), which does
NOT hold for **adjacent round-deltas**. The z-against-zero test measures "is there ANY lag-1
correlation," and the structural MA(1) answer is **yes, in every arm**. §5.4 and C3/C4 as written
are provably wrong.

---

## 3. (b) The trajectory-mean-instrument common-mode

The instrument is held at the per-trajectory MEAN (S-1), but that mean **varies shot-to-shot**:
different trajectories have different mean readout/reset, so each shot's whole-record delta rate
`ρ̄(shot)` fluctuates. By the law of total covariance, pooling over shots,
$$ \mathrm{Cov}(D_r, D_{r+\ell}) = \underbrace{\mathbb E_z[\mathrm{Cov}(D_r,D_{r+\ell}\mid z)]}_{\text{MA(1): }0\text{ for }\ell\ge2}
   \;+\; \underbrace{\mathrm{Cov}_z(\rho_r(z), \rho_{r+\ell}(z))}_{\text{common-mode}} . $$
The common-mode term is **present at all lags** (including ℓ ≥ 2) and is **permutation-invariant**
(the trajectory mean is unchanged by shuffling cycles within the trajectory), so it is **identical
in `shared` and `markovian`** and cancels in `shared − markovian`.

Committed-constant magnitude (variance over shots of the trajectory-mean delta rate
`q(shot) = 2μ(shot)(1-μ(shot))`, driven by the trajectory-mean readout+reset):
$$ \boxed{\text{common-mode} = 8.68\times10^{-5}} \quad\text{(reviewer F1b: }\approx 8\times10^{-5}\text{).} $$
This is ~10³× the memory signal (§6) and dominates the raw S2 z-scores — another reason the "flat"
clauses fail — yet carries **no** memory information.

---

## 4. (c) The markovian null is EXCHANGEABLE, not independent

`markovian` permutes each field per shot. Conditional on a trajectory's multiset of rates
`{ρ_i}`, a uniformly random permutation gives, for `r ≠ r+ℓ`,
$$ \mathrm{Cov}_\pi(\rho_{\pi(r)}, \rho_{\pi(r+\ell)}) = -\frac{s^2_\rho}{R-1}, $$
the finite-population exchangeable anticorrelation (`s²_ρ` = within-trajectory sample variance).
Adding the between-trajectory common-mode `Var_z(ρ̄)`:
$$ \mathrm{Cov}^{\text{markov}}(\ell) = \mathrm{Var}_z(\bar\rho) \;-\; \frac{\mathbb E_z[s^2_\rho]}{R-1}. $$
Because `Var_z(ρ̄)` (common-mode) dominates, the markovian arm **retains most of the shared arm's
lag-1 covariance**. Committed evidence at `R = 12`:
$$ \frac{\mathrm{Cov}^{\text{markov}}(1)}{\mathrm{Cov}^{\text{shared}}(1)} = 0.727 \quad\text{(reviewer F1c: }\approx 74\%\text{).} $$
So C3's two clauses ("markovian flat" AND "shared − markovian difference z ≥ 3") are jointly
strained: the arms differ by only the ~27% memory residue, itself second-order small (§6).

---

## 5. Summary of the null structure (per arm, per lag)

| arm | lag-1 detector correlation | lag ≥ 2 detector correlation |
|---|---|---|
| `off` | `p_ij = μ ≈ 0.0149` (structural MA(1)) | **0 (exact)** |
| `markovian` | MA(1) `μ` + common-mode; retains ~73% of shared's excess | common-mode only (`≈ 8.7e-5`); no memory |
| `shared` | MA(1) `μ` + common-mode + memory | common-mode + **decaying memory autocov** |

The genuine memory signature is the **decaying** shared autocovariance (committed `Δγ(ℓ)` =
`5.58e-12, 2.65e-12, 6.70e-13, ~0` at lags 1–4, in γφ² units) — the right *shape* (present only in
`shared`), but a tiny *amplitude*.

---

## 6. (d) The memory discriminator is second-order — feasibility

Only `gamma_phi` varies per round, so the shared-vs-markovian memory signal is the **autocovariance
of the `gamma_phi`-induced per-round rate fluctuation** — second order in a small modulation.

- Per-round rate slope (teacher C-10(b)): `∂(delta rate)/∂γφ ≈ 0.5·τ_eff`, where `τ_eff` is the
  effective within-round dephasing window. `τ_eff` is the **one** quantity not fixed by a committed
  *constant* (it lives in the compiled schedule dt's); bracket it `τ_eff ∈ [50, 1000] ns`.
- Record-level memory signal: `Δ_record(ℓ, τ) = (0.5·τ)²·Δγ(ℓ)`, with committed
  `Δγ(1) = 5.58e-12` (γφ²).
- Noise: the shared−markovian difference of a covariance estimate has SE `≈ √2·Var(D)/√N`,
  `Var(D) ≈ q(1-q)`, `q ≈ 0.0294 + 0.5·γφ_base·τ`.
- Detection at 3σ: `N = (3·√2·Var(D) / Δ_record)²`.

Committed-constant N (script `[d]` block):

| τ_eff (ns) | Δ_record (lag1) | N to detect at 3σ |
|---|---|---|
| 50 | 3.49e-9 | **1.23e15** |
| 100 | 1.40e-8 | 7.83e13 |
| 225 (nominal) | 7.07e-8 | 3.22e12 |
| 500 | 3.49e-7 | 1.48e11 |
| 1000 | 1.40e-6 | **1.11e10** |

$$ \boxed{\;N_{\text{detect}} \in [1.1\times10^{10},\; 1.2\times10^{15}] \gg 10^6 = \text{FEASIBLE\_N}\;} $$

(conservative: a single pooled covariance statistic, no cross-pair averaging). An **optimistic**
estimate that pools all `n_stab·(R-2)` lag-1 pairs as if independent (a √(n_pairs) SE gain) and
takes the most generous `τ = 1000 ns` bottoms out at `N ≈ 2.4×10^8` — still **240×** the cap; you
would need `τ_eff ≈ 3000 ns` (beyond one full source cycle, unphysical) to reach `~3×10^6`. So
across the ENTIRE `τ_eff` bracket AND both SE conventions the discriminator is infeasible by **2–9
orders**. The reviewer's `N ≳ 7e9` sits between these corners. At nominal `τ`, the common-mode is
`1.23e3×` the memory signal — the discriminator drowns in a permutation-invariant nuisance that
cancels only in the difference, whose SE then needs `N ≳ 1e8` even optimistically. **The intended
second-moment γφ signal is sub-detectable on records at feasible N by construction** (matched
marginals force second order; mild 1/f makes it tiny).

*Independent reconciliation (adversarial re-derivation, un-led, 2026-07-03):* a from-scratch
theorist reproduced μ = 0.0149, `p_ij(lag1) = μ` (via 8-point EXACT enumeration and the closed-form
reduction to `(½-μ)²`), `lag ≥ 2 = 0`, the permutation-invariant common-mode (`7e-6…1.2e-4` per
check — brackets the empirical `8.7e-5`), and `N_detect ∈ [2.4e8, 6e10]` (its optimistic-pooled
corner), independently recommending the same faithfulness-report reframe and the "test collapse at
lag ≥ 2" fix. Three independent paths (reviewer F1, the committed-constant script + from-scratch
i.i.d.-bit self-check, this re-derivation) agree.

---

## 7. The reframe — a FAITHFULNESS REPORT, not a pass/fail discriminative gate

A sub-floor record imprint of **mild 1/f** is a **faithful property**, consistent with:
- G0-v1 (ζ record-dead; γφ-carried joint TV already sub-feasible at 2 rounds),
- H2's finding that `ζ + γφ-on-data = Kam Class 0 = decode-benign`,
- the build-contract's re-frame of G4/G6 to **faithfulness** (handoff §0; the brief's "sub-floor at
  mild 1/f is a FAITHFUL property, not a failure"),
- the standing scope ([[project-coupling-nonmarkovian-is-the-contribution]]): the classical 1/f
  slice is **scaffolding**; the contribution is the quantum-bath / coherence sector. A **classical**
  1/f drift leaving no forgeable record signature is exactly the strawman that memory
  [[project-nonmarkovian-wedge-must-be-coherence]] says must be beaten by a coherence-revival
  signature — so this finding *sharpens* the scope rather than undermining it.

The simulator's validity chain ([[feedback-simulator-not-decoder]]) is channel-level certification
(G2) + record-level characterization with matched nulls — **not** a G6 discriminative pass. G6
reframed to "reproduce the derived record structure + honestly report the sub-detectable memory
imprint" IS record characterization with matched nulls. Nothing load-bearing depended on G6
passing as a discriminator.

**Predict-before-measure discipline:** the discriminator was registered before this derivation was
done; the honest outcome of the derivation is "the registered discriminator is infeasible." Per the
theory-first rule, we re-register the gate to test what IS feasible and true, and record the
infeasibility as the finding — we do NOT keep a gate whose pass condition is unsatisfiable, and we
do NOT weaken thresholds post-hoc to manufacture a pass.

---

## 8. What the re-registered report tests (feasible, GENUINE, predict-before-measure)

Registered predictions for the re-run (see prereg §5, revised):

- **R-G6-A (a-exact, feasible).** Off-arm `p_ij(lag1) = μ_c` per check (Z-check `= p_instr = 0.0149`;
  X-check `= p_instr + O(0.5 γφ_base τ_eff)`), and off-arm `Cov(lag ≥ 2) = 0` within SE. A wiring
  bug (wrong detector fold, non-independent rounds) breaks these. **Replaces the broken C4.**
- **R-G6-B (a-exact, feasible).** The delta stream is 1-dependent: `S2(lag1) ≠ 0`, `S2(lag ≥ 2) = 0`
  within SE in the off arm — the MA(1) signature.
- **R-G6-C (b, feasible).** Common-mode equality: `shared` and `markovian` agree at lag ≥ 2 within
  SE (permutation-invariance of the common-mode ≈ 8.7e-5). Genuine check that `markovian_baseline`
  preserves marginals + common-mode (a mis-built control would diverge here).
- **R-G6-D (b, the honest sub-detectability finding — REPORTED, never gated).** The
  shared−markovian memory autocovariance is second-order; the derived `N_detect ∈ [1.1e10, 1.2e15]`
  ≫ 1e6. Reported as the faithful sub-floor property. This is the reframed "coupling ablation": the
  memory lives at the channel level (G2) and in the source truth; on records at mild 1/f it is a
  faithful sub-floor.
- **C1 kept** (positive control from truth: params vary per round + cross-mech corr ≥ 0.9) — feasible,
  genuine, independent of the record-N problem.
- **C5 kept** (S3 r3 ζ-witness ≈ 0 all arms) — feasible, genuine.
- **P1 FIXED** (F1): draw i.i.d. **measured bits** and XOR into deltas (reproducing the MA(1) floor),
  not i.i.d. delta bits — so the pipeline self-test exercises the *real* null.
- **P2 RELABELED**: the planted per-shot common-rate latent is the **common-mode**, so P2 validates
  the pipeline's common-mode sensitivity — NOT memory discrimination. Add **P3**: a planted
  *memory* positive control (AR(1)-correlated per-round rate vs its permutation) at an INFLATED
  amplitude where the difference statistic IS detectable, to validate the shared−markovian machinery,
  then note the real teacher's amplitude is sub-floor.

**Verdict rule (revised, c):** G6 PASSES as a faithfulness report iff R-G6-A ∧ R-G6-B ∧ R-G6-C ∧ C1
∧ C5 ∧ P1 ∧ (P2 ∧ P3) ∧ (the §8.2 L6 independent-GT lag-1 algebraic-identity check, a-exact) hold;
R-G6-D is REPORTED with its derived N and never flips the verdict. **R-G6-C is CONDITIONAL** — it
gates only when the common-mode is detected in the shared arm (S2 lag≥2 |z| ≥ 3); when the
common-mode is sub-detected at the chosen N it is VACUOUS-power (reported, non-blocking). No clause
requires the infeasible memory discrimination. The magnitude of the memory imprint never gates
(consistent with G4's ΔLER-never-gates rule). *(This list matches prereg §5.2 and the gate code's
9-condition verdict exactly.)*

---

## 9. Constraint-ledger deltas (faithfulness protocol rule II)

| # | old (§5) | corrected |
|---|---|---|
| L-null | "off S1/S2 ≈ 0 exactly" (§5.4) | off `p_ij(lag1) = μ` (MA(1)); only lag ≥ 2 is 0 |
| L-common | S-1 instrument bound covers per-shot variation | trajectory-mean instrument injects a permutation-invariant common-mode ≈ 8.7e-5 at all lags |
| L-perm | "permutation destroys alignment" (C-9/§5.4) | permutation is EXCHANGEABLE; retains ~73% of lag-1 cov at R=12 |
| L-order | discriminate shared vs markovian on raw z | second-order signal; N ≥ 1.1e10 ≫ 1e6 → report, don't gate |

Independent ground truth (rule I): the **a-class** claim (the MA(1) identity `p_ij(lag1) = μ`,
`lag ≥ 2 = 0`) rests on an **airtight** from-scratch check — an i.i.d.-bit Monte-Carlo self-check
(~0.07%) plus an exact 8-point enumeration; this is the load-bearing certification. The **b-class**
source-covariance AMPLITUDE (`Δγ`, which never gates — R-G6-D is reported-only) has only a
**~15%-loose linearized consistency check**: the analytic RTN-sum `Σ_k v_k² e^{-2γ_k ℓ}` under a
LINEAR `γφ(z)` map gives `1.76e-11` vs the empirical `2.05e-11` (14% apart, the convex
`γφ=base·exp(sens·x)` map understates). The RTN cross-check is disclosed as a linearized
consistency check, NOT a tight GT of the amplitude — nothing load-bearing depends on `Δγ` to better
than ~15%.

Bounded simplifications (rule III): `τ_eff` is bracketed `[50, 1000] ns` (the infeasibility holds
across the whole bracket); the N formula uses the worst-case `√2·Var(D)/√N` covariance-difference
SE (conservative); the record-rate γφ slope uses the teacher's own C-10(b) `0.5·τ_eff` leading form.
