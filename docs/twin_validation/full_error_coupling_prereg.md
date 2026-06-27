# Full-error cross-mechanism coupling — pre-registration

**Status:** pre-registration (theory-first; predictions written BEFORE the joint-Lindbladian
build). User directive 2026-06-26: *"所有机制都可能彼此联动 … 这也是我们 teacher 能高保真的原因"*
followed by *"耦合是全 error 耦合, 不是只有 leakage 和 crosstalk"*. This document predicts, for
the FULL teacher error catalog, which mechanism pairs couple (and how strongly) so the
window-joint-Lindbladian assembler is built against a falsifiable prediction, not assembled blind.

**Epistemic frame (per `docs/METRICS.md` declaration rule):**
- **(a) exact** — commutator identities `[H_i, H_j] = 0` (algebraic; the only class usable as a
  premise). These become the assembler's POSITIVE CONTROLS: composed must equal joint to machine
  precision, else the assembler is buggy.
- **(b) prediction band** — every cross-term magnitude estimate `ε_ij ≈ ½‖[H_i,H_j]‖·t²` below is a
  registered falsifiable bet (order-of-magnitude + scaling). A miss is a finding, never later cited
  as fact.
- **(c) gate/decision** — the LARGE / MEDIUM / SMALL / EXACT ranking and the "include in joint-L vs
  compose-and-bound" cut are decision rules only.

All scales in angular frequency **rad/ns**, times in **ns**. Process infidelity of dropping a
coupling (composing instead of joint-propagating) scales as `1 − F ≈ ε_ij²` to leading Trotter order,
with `ε_ij ≈ ½‖[L_i, L_j]‖ t²` and for Hamiltonian generators `‖[L_i,L_j]‖ ≈ ‖[H_i,H_j]‖`.

---

## 0. The worth-doing filter (PRIMARY ranking — applied to couplings, user 2026-06-26)

Cross-term MAGNITUDE (`ε_ij`) is NOT the primary ranking. The project's OWNED-vs-OPEN ("伪命题")
standard applies to couplings too — a coupling is worth modelling as a CONTRIBUTION only if it passes
BOTH filters:

- **F1 — not already owned by the dominant simulator.** QMCtwin (arXiv:2606.19848, quantum-trajectory
  Pauli twin, d7/97q) already does **coherent + incoherent CONCURRENT Markovian** coupling, and frames
  its **reported simulations in a non-negative Markovian rate model** (verified against the arXiv
  source, 2026-06-26 — the primary-source support for the non-Markovian-source wedge). An explicit
  non-Markovian source is therefore outside its model class.
- **F2 — not removable by hardware/calibration.** A coupling that echo / DD / gate-recalibration /
  tunable-coupler ZZ-cancellation / DQLR-LRU leakage-removal suppresses has no decision value in a twin
  (the hardware already deletes it).

| coupling class | examples | F1 owned? | F2 removable? | verdict |
|---|---|---|---|---|
| **coherent concurrent Markovian** | DR×ZZ, SP×ZZ, coherent leakage×CZ | YES (QMCtwin) | YES (echo/DD/recal/coupler/LRU) | **伪命题 → BASELINE** (reproduce as a control, do NOT claim as contribution, regardless of large ε) |
| **non-Markovian correlated** | TLS telegraph, 1/f drift, shared/structured bath | **NO** (QMCtwin avoids — Markovian rates can't) | **NO** (materials/fab-level) | **THE CONTRIBUTION** (passes both filters) |

**Consequence — the §4.2 ε-ranking is DEMOTED.** DR×ZZ has the largest `ε` (~0.02–0.045 rad) yet fails
BOTH filters → it is BASELINE, not the contribution. The deliverable is the **non-Markovian / cross-
cycle correlated** coupling, NOT the concurrent-Markovian pairs.

### 0.1 Methodological crux — non-Markovian coupling ≠ a sum of non-negative-rate Lindbladians

A sum `Σ_i D[c_i]` of non-negative-rate Lindblad terms is **CP-divisible = Markovian by construction** —
exactly QMCtwin's / quantum-jump-MCWF's / Stim-pij's assumption domain. Summing positive-rate
generators REPRODUCES the owned class; it cannot produce memory/correlation. To deliver the
contribution the model must **carry the noise SOURCE as an explicit dynamical degree of freedom**:

- **TLS** → an explicit telegraph fluctuator (two-state switch, rate τ⁻¹ ~ gate/cycle scale → memory);
- **1/f** → an explicit colored classical process with `S(f) ∝ 1/f` (power-law → long-time
  correlation → non-Markovian); the TLF-1/f push is the validated seed (emergent round-corr +0.133);
- **shared/structured bath** → a few explicit bath modes with spatio-temporal correlation.

Trace out the source → the reduced qubit dynamics is non-Markovian (the time-local generator develops
transiently **negative rates** / information backflow). **The non-Markovianity is the wedge** — it is
the structural feature the non-negative-Markovian baseline cannot represent. Axis 2 (§5) is therefore
not a correlational add-on; it IS the contribution, and must be implemented as an explicit memory-ful
source, never a rate. The concurrent-Markovian joint-L (§4) is built only as the BASELINE control.

### 0.2 Wedge metric

Non-Markovianity quantified by a CP-divisibility breaking measure (e.g. RHP: the transient negativity
of the time-local rates, or BLP information-backflow / trace-distance revival), AND by the
cross-mechanism + cross-cycle CORRELATION the factorized non-negative-Markovian baseline (QMCtwin-class:
correct marginal single-mechanism rates, independent factors) misses. The twin captures both; the
baseline captures neither — that gap, measured, is the contribution.

---

## 1. Object & claim

The faithful per-cycle teacher evolution is NOT a composition chain of individually-derived channels.
It has two coupling axes:

- **Axis 1 — instantaneous (within a time sub-step):** every mechanism active in the same sub-step
  enters ONE Lindbladian `L_substep = -i[Σ_i H_i, ·] + Σ_i D[c_i]`, propagated once
  `E_substep = expm(L_substep · t)`. Sub-steps (1q-gate layer → CZ layer → idle → readout) ARE
  temporally ordered, so composition ACROSS sub-steps is physically correct;
  composition WITHIN a sub-step is the approximation, dropping the cross-terms `[H_i,H_j]`.
- **Axis 2 — temporal (across windows):** a single stochastic draw (1/f drift, burst, shared bath)
  modulates MANY mechanisms' parameters at once → correlated. Implemented by a shared latent fed into
  every affected parameter map, NOT independent per-channel sampling.

**Claim (to be validated, not assumed):** the coupling magnitude is a MEASURED number
(composed-vs-joint for axis 1; shared-vs-independent for axis 2), and it is what makes the teacher
high-fidelity. Both comparisons are anti-circular: the joint/shared object is the exact reference,
the composition/independent object is the approximation under test.

---

## 2. Mechanism catalog (generators + scales)

Generators are the QuTiP-derived `{H_i, c_i}` (see `qutip_channel_derivation_prereg.md`). Truncated-
qubit identities: `n = |1⟩⟨1|`, `σ⁻ = |0⟩⟨1|`, `σx = σ⁺+σ⁻`, `[σx, n] = iσy` (used throughout).
Leakage adds the |2⟩ level (qutrit) → `n`, ladder operators on dim 3.

| # | mechanism | generator | scale (rad/ns) | active in |
|---|---|---|---|---|
| T1 | relaxation | `c=√γ₁·σ⁻` (or `a`) | γ₁=1/T1≈3.3e-5 (T1≈30µs) | all sub-steps |
| T2 | pure dephasing | `c=√(2γφ)·n` | γφ=1/Tφ≈3.3e-5 | all sub-steps |
| DR | 1q gate drive | `H=(Ω/2)σx` | Ω=π/t_g≈0.126 (t_g=25ns, π) | 1q layer |
| ZZ | static cross-Kerr | `H=ζ·n_a n_b` | ζ≈2π·0.37MHz≈2.3e-3 | always-on (all) |
| SP | drive spillover | `H=(c_x Ω/2)σx_b` | c_x≈0.01–0.1 → 1.3e-3–1.3e-2 | 1q layer |
| FS | fSim residual | `H` on {|11⟩,|02⟩,|20⟩} | dθ,dφ (swept) | CZ layer |
| LK | leakage \|1⟩↔\|2⟩ | `H=(Ω₁₂/2)(\|1⟩⟨2\|+h.c.)`, `c` seepage | per-CZ leak≈1e-3 | CZ (+ drive) |
| TLS | two-level system | `H=g(σ⁺σ⁻_TLS+h.c.)` | g≈2π·(0.1–1)MHz≈6e-4–6e-3 | always-on |
| RD | readout dephasing | `c=√Γφ_m·n` (meas-induced) | Γφ_m (strong during meas) | readout |
| MI | MIST (\|1⟩→\|2⟩) | semiclassical-cavity `H` | leak≈8e-4/100ns (Xiong) | readout |
| BU | burst | elevated `c=√γ₁ᴮ·σ⁻`, correlated | event-wise | rare, multi-q |
| DF | 1/f drift | parametric (modulates ζ, Δ, Ω…) | slow latent | across cycles |

---

## 3. QEC-cycle sub-step occupancy (which mechanisms are simultaneous)

| sub-step | t (ns) | simultaneously-active mechanisms |
|---|---|---|
| **1q-gate layer** | ~25 | DR (targets), SP (neighbors), ZZ, LK (drive-induced), TLS, T1, T2 |
| **CZ layer** | ~25–40 | CZ+FS, ZZ, **LK (dominant)**, TLS, T1, T2 |
| **idle** | ~100s | ZZ, TLS, T1, T2, (DF modulating all) |
| **readout** | ~100–500 | RD, **MI**, T1, T2 |
| **(cross-cycle)** | — | DF (correlated parameter drift), BU (multi-mechanism event), shared bath |

Composition ACROSS these four sub-steps is faithful (real time order). The prediction below is for the
WITHIN-sub-step pairs only (axis 1) + the cross-cycle correlations (axis 2).

---

## 4. Cross-term prediction (the core) — every within-sub-step pair

`ε_ij ≈ ½‖[H_i,H_j]‖·t²` (rad); `1−F ≈ ε_ij²`. Diagonal-in-`n` operators mutually commute (exact).

### 4.1 EXACT-ZERO pairs — class (a), composition is exact (POSITIVE CONTROLS)

| pair | reason `[H_i,H_j]=0` |
|---|---|
| T2 × ZZ | both diagonal in `n`: `[n_a, n_a n_b]=0` |
| T2 × cross-Kerr, ZZ × any diagonal | all diagonal in `n` |
| DR_a × DR_b (distinct qubits) | `[σx_a, σx_b]=0` |
| DR_a × SP_a / SP × DR (both σx-type) | `[σx, σx]=0` |
| RD × T2 (both `n`-dephasing) | `[n, n]=0` |
| T1_a × T1_b, any single-site op on distinct qubits | disjoint support |

**Falsifying/control test:** the assembler MUST return composed == joint to ≤1e-12 for every row here.
A nonzero result is an assembler bug, not physics (broken-check-must-fail-loudly discipline).

### 4.2 NON-ZERO pairs — class (b) magnitude bands

| pair | sub-step | `[H_i,H_j]` core | `‖[H_i,H_j]‖` (rad²/ns²) | t (ns) | **ε_ij (rad)** | 1−F | rank |
|---|---|---|---|---|---|---|---|
| **DR × ZZ** | 1q | `(Ω/2)ζ·iσy_a n_b` | ~1.4e-4 | 25 | **~0.02–0.045** | ~5e-4–2e-3 | **LARGE** |
| **LK × CZ/FS** | CZ | \|1⟩↔\|2⟩ vs CZ drive | strong (non-Pauli) | 25–40 | **non-perturbative** | project frontier | **LARGE** |
| LK × ZZ | CZ/1q | \|2⟩ has different ζ | ~(leak)·Δζ | 25–40 | ~1e-2 (cond. on leak) | ~1e-4 | MEDIUM |
| TLS × DR | 1q | `g·(Ω/2)` | ~3.8e-5 (g=6e-4) | 25 | ~0.012 | ~1.4e-4 | MEDIUM |
| MI × RD | readout | leak vs `n`-deph | leak·Γφ_m | 100–500 | ~1e-2 (built) | ~1e-4 | MEDIUM |
| SP × ZZ | 1q | `c_x·(Ω/2)ζ·iσy_b n_a` | `c_x`×(DR×ZZ) | 25 | ~1e-3 (c_x=0.05) | ~1e-6 | MEDIUM/SMALL |
| TLS × ZZ | idle | `g·ζ`, off-diag×diag | ~1.4e-6 | 100s | ~1e-2 (long t) | ~1e-4 | MEDIUM/SMALL |
| T1 × DR | 1q | `[σ⁻,σx]=-σz` | √γ₁·Ω type | 25 | ~2.6e-3 | ~7e-6 | SMALL |
| T1 × ZZ | idle | `[σ⁻,n]=σ⁻` | √γ₁·ζ | 100s | ~small | <1e-6 | SMALL |
| T1 × T2 | all | `[σ⁻, n]≠0` | γ₁·γφ | — | 2nd-order tiny | <1e-7 | SMALL |

**Headline prediction:** the largest-ε instantaneous coupling is **DR × ZZ** (static-ZZ during the
single-qubit gate — coherent conditional-phase, ε~0.02–0.045 rad), then **leakage × CZ**. ⚠ **But per
§0 these are BASELINE, not the contribution** — coherent concurrent Markovian, owned by QMCtwin AND
hardware-removable (echo/DD/recal/LRU). Large ε ≠ worth-claiming. This §4 table is the
**baseline/positive-control** spec (reproduce the concurrent-Markovian couplings to show the twin is not
missing them), not the deliverable. Everything diagonal-in-`n` composes EXACTLY (§4.1) — a large
fraction of the catalog, which is why naive composition is "mostly" right. **The contribution lives in
§5 (non-Markovian correlated), not here.**

---

## 5. Axis-2 correlational couplings (shared stochastic source) — **THE CONTRIBUTION (§0)**

Not commutators — coupling via a shared latent draw. This is the worth-doing class: non-Markovian,
materials-level-unremovable, outside QMCtwin's non-negative-Markovian model. **Implemented as an
explicit memory-ful source (§0.1), not a positive rate.** Magnitude = induced cross-mechanism /
cross-cycle correlation + the CP-divisibility breaking (§0.2).

| source | mechanisms it co-modulates | predicted signature | class |
|---|---|---|---|
| **1/f drift (DF)** | ζ, Δ_q (→T2), Ω, spillover — ALL via the qubit frequencies | **correlated** slow drift of ζ/T2/detuning together (positive round-corr ~0.1, cf. TLF push) | (b) |
| **burst (BU)** | T1 (↑), frequency shift, possible LK trigger — multi-mechanism, multi-qubit | common-mode elevated error across mechanisms & neighbors in the same round | (b) |
| **shared TLS/phonon bath** | correlated dephasing on neighboring qubits | spatial dephasing correlation | (b) |

**Method:** one latent draw `→` fed into every affected `_drift_to_*` / `_burst_to_*` parameter map
(extend the burst shared-bath pattern). **Falsifying test:** shared-latent vs independent-per-mechanism
sampling must show the predicted correlation (round-corr, spatial-corr); independent sampling →
correlation collapses to 0 (the negative control).

---

## 5.1 Predicted non-Markovian signatures (theory-first, BEFORE the source build) — class (b)

Anchor: a single telegraph fluctuator (random telegraph noise, RTN) dephasing a qubit is EXACTLY
solvable — the source carries coupling `±v` (qubit frequency shift when the TLS flips) and switching
rate `γ_sw`. This gives sharp, falsifiable predictions for what the explicit source produces that the
non-negative-Markovian baseline cannot.

**Scales:** `v ≈ 2π·(0.01–1) MHz ≈ 6e-5–6e-3 rad/ns`; `γ_sw = 1/τ_sw`, `τ_sw ≈ µs–ms → 1e-3–1e-6 /ns`;
`t_cycle ≈ 1 µs = 1000 ns`.

**P1 — CP-divisibility breaking has a SHARP boundary at `v = γ_sw` (RTN exact result).**
Convention: `ξ(t)∈{±1}`, switching rate `γ_sw`, `⟨ξ(0)ξ(τ)⟩=e^{−2γ_sw|τ|}`, phase `φ=v∫ξ`;
exact coherence `L(t)=e^{−γ_sw t}[cosh μt+(γ_sw/μ)sinh μt]`, `μ=√(γ_sw²−v²)`.
- Slow/strong fluctuator (`v > γ_sw`, `μ` imaginary): coherence shows revivals → time-local dephasing
  rate transiently **NEGATIVE** → RHP non-Markovianity measure > 0. The baseline cannot represent it.
- Fast/weak (`v < γ_sw`, motional narrowing): pure exponential decay `Γ=v²/(2γ_sw)` → Markovian → the
  non-negative-rate baseline is RECOVERED exactly.
- **Falsifiable:** sweep `v/γ_sw`; the RHP measure / coherence revival turns on at `v ≈ γ_sw`. (A
  miss — e.g. non-Markovianity present below the crossover — is a finding.)

**P2 — cross-cycle (round-to-round) correlation ≈ the source autocorrelation at `t_cycle`.**
A slow source barely changes between rounds → consecutive-round error rates correlate as
`C(t_cycle) ≈ exp(-2γ_sw·t_cycle)` (RTN) [1/f: a log-tail, slower decay]. The factorized Markovian
baseline (independent per-round rates) gives round-corr **= 0**. Predict the emergent round-corr scales
with `γ_sw·t_cycle`; the validated TLF-1/f push (+0.133) is one point on this curve — register it as the
seed datum, predict the full `γ_sw`-dependence.

**P3 — the baseline matches the MARGINAL rate but misses the DISTRIBUTION.** A best-fit non-negative-
Markovian model can match the time-averaged dephasing exactly yet miss (a) the coherence revival (P1),
(b) the round correlation (P2), (c) the non-Gaussian/**bimodal** telegraph statistics (a single slow TLS
gives two-valued, not Gaussian, dephasing). Predict `TVD(true ‖ best-fit-factorized-Markovian)` grows
monotonically with the source correlation time `τ_sw` (→ 0 in the fast/motional-narrowing limit).

**P4 — decision payoff (the noise-twin spine).** Under a slow source, a DEM/decoder calibrated on the
MARGINAL (Markovian) rate is conditionally MISCALIBRATED given the source state → conditional-coverage
failure. The source-resolved twin predicts the conditional miscalibration; the baseline cannot. This is
the conditional-coverage-under-misspecification central bet (see the UQ-novelty line) made concrete: the
misspecification is precisely "factorized-Markovian fit to a non-Markovian source."

These four are the registered bets the source layer must produce (P1–P3 mechanism-level; P4
decision-level). All anti-circular: the source-resolved object is exact; the factorized-Markovian fit is
the approximation under test.

**REVISION (2026-06-26, after the un-led red-team).** The first wedge build measured P2/P3 on the
SYNDROME stream vs an i.i.d. baseline — which captures CLASSICAL round-CORRELATION (a Markov-k model
recovers most of it), NOT non-Markovianity. The contribution is therefore re-based on a **COHERENCE
observable** (Ramsey/echo `|L(t)|`): the only unforgeable non-Markovian signature is the `|L|` REVIVAL
(non-monotone ⇔ CP-divisibility breaking), invisible in phase-blind Z-syndromes (ties to
"coherence not identifiable from syndrome-only"). The baseline becomes the STRONGEST monotone-`|L|`/
CP-divisible competitor (multi-exp/isotonic/Markov-k), and a HARD new gate (ledger **C10**) requires the
wedge to COLLAPSE in the motional-narrowing limit `v<γ_sw` and turn on at `v=γ_sw`, co-located with the
RHP crossover — non-collapse ⇒ the wedge is not non-Markovianity and the P1↔wedge claim is retracted. See
ledger C5 (revised) + C10.

## 6. Falsifying tests (registered before the build)

For the joint-Lindbladian assembler:
1. **Positive controls (class a):** every §4.1 pair → composed == joint to ≤1e-12. Must hold exactly.
2. **Magnitude bands (class b):** every §4.2 pair → composed-vs-joint process-infidelity on the
   minimal cluster lands in the predicted `1−F` band (order of magnitude + the predicted scaling in
   Ω, ζ, t, c_x, g). A miss is a finding (e.g. DR×ZZ coming out 10× the band ⇒ revisit).
3. **Ranking holds:** DR×ZZ and LK×CZ are the top-2 instantaneous couplings; the SMALL pairs are
   ≤1e-5 infidelity (declared-bounded, composition retained for them).
4. **Axis-2 (class b):** shared-latent vs independent → predicted correlation appears / collapses.

Anti-circular: the joint propagator and the shared-latent sampler are the EXACT references, derived
independently of the composition/independent approximations they test.

---

## 7. Build plan (gated on this prediction)

**Priority follows §0: the contribution (non-Markovian, §5) is built; the concurrent-Markovian
joint-L (§4) is built only as the baseline/control.**

1. **explicit non-Markovian source layer (THE CONTRIBUTION)** — carry the noise source as a dynamical
   degree of freedom (TLS telegraph fluctuator / colored 1/f process with `S(f)∝1/f` / few-mode shared
   bath), feeding ONE shared latent into every co-modulated parameter map. Reduced qubit dynamics is
   non-Markovian by construction (transient negative time-local rates). Builds on the validated TLF-1/f
   push. Deliverable: the CP-divisibility-breaking measure (§0.2) + the cross-mechanism/cross-cycle
   correlation vs the factorized non-negative-Markovian baseline.
2. **non-negative-Markovian baseline (the OWNED control)** — the concurrent joint-L: full `{H_i, c_i}`
   catalog, group by sub-step, sum within sub-step, `expm(L_substep·t)` once (GPU
   `torch.linalg.matrix_exp`; time-dependent drives → Trotter/expm), compose across sub-steps. This
   reproduces the QMCtwin-class concurrent-Markovian couplings — explicitly the BASELINE, not claimed.
   Hilbert = window qutrit space (small feasible; dim⁴ wall → window-joint + cross-window seam,
   ADR 0008 / `plan3.md`).
3. **composed-vs-joint harness** — runs the §6 tests on the baseline: the positive-control zeros (§4.1)
   + the concurrent-Markovian cross-term magnitudes (§4.2), confirming the baseline is faithful to the
   owned class before the non-Markovian contribution is measured against it.
4. **wedge demonstration:** the §5 non-Markovian correlated coupling produces a prediction (correlated
   multi-mechanism / cross-cycle structure + CP-divisibility breaking) the §2 factorized baseline
   CANNOT — measured, not asserted. Map to a decision-relevant quantity (conditional coverage under
   drift; correlated burst/TLS multi-qubit events) per the noise-twin spine.

Each coupling carries its measured magnitude (class b) + the declared+bounded simplification for any
pair kept as composition (rule III). Mainline (`src/`) untouched + commit-gated.
