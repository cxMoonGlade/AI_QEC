# G0-quantum — record-level effect-size PRE-REGISTRATION (theory-first, LITERATURE-GROUNDED)

> **HISTORICAL INTERPRETATION, NARROWED 2026-07-13.** Preserve the preregistered comparison and
> effect-size arithmetic, but a record difference between the declared quantum model and a bounded
> classical imitator does not exclude all classical latent-history models or certify quantum memory.
> Reduced-map CP-indivisibility also does not transfer to `{det,obs}` without the missing bridge.
> Current authority:
> [`notion123_taxonomy_literature_closure_2026-07-13.md`](notion123_taxonomy_literature_closure_2026-07-13.md).

Status: PRE-REGISTRATION, 2026-07-03. Predictions written BEFORE any run; a miss is a FINDING, not a
re-fit. This is the **mandatory pre-build effect-size gate** for the quantum-bath teacher (handoff §1,
`nonmarkovian_memory_carrier_scope.md` §4 "record-level visibility"). It decides ONE thing:

> **Does the quantum coherence-revival / CP-divisibility wedge survive into surface-code `{det,obs}`
> records at feasible N under a FAIR (marginal-matched) comparison against the classical imitator?**
> GO ⇒ a record-level quantum-vs-classical wedge is reachable ⇒ the executed classical record foil
> (the "A′" suite) is worth running. NO-GO ⇒ the wedge is capped at the source/channel layer ⇒ the
> classical record round lands as "B" and the source/channel-layer matched-BCF imitator (M2 dual-arm)
> is the control.

**Binds to:** `involuntary_w_check_2026-07-03.md` (Prop IW-1 — the source→record map, a-class,
16/16 machine-verified), `quantum_bath_slot_prereg.md` (M1 physical bracket + the unitality theorem),
`coupled_teacher_round_gates_prereg.md` §1 (the classical G0-v2 cautionary anchor),
`docs/METRICS.md` (BLP/RHP/TV/D_Choi ledger rows), `docs/FAITHFULNESS_PROTOCOL.md`,
`nonmarkovian_memory_carrier_scope.md` (BINDING scope).

**Epistemic-class rule (METRICS.md, binding):** every quantitative item is tagged **(a) exact**
(theorem/identity/zero-tolerance — the only class anything may be built on), **(b) registered
prediction band** (a miss is a FINDING, never later citable as fact), or **(c) heuristic
gate/decision rule** (go/no-go only; never a premise). Undeclared ⇒ (c).

**Predict-before-measure discipline (binding).** The effect-size sizing below (§3) is a DERIVATION
from committed constants + Prop IW-1's machine-verified coefficient; the committed-constant script
`outputs/twin_validation/g0_quantum_feasibility_from_constants.py` (CPU-only, §8) is the
predict-before-measure artifact — it COMPUTES N_detect from the physical bracket, it does not fit
anything. The eventual GPU verification (measuring the wedge on full surface-code records) is a LATER
step, gated by this prereg's GO verdict.

---

## 0. Grounding ledger (the corresponding papers — all 精读 + noted)

| sub-axis / mechanism | mechanism paper | observable paper | reading note | in-repo code (reuse) |
|---|---|---|---|---|
| Quantum-memory bath = pseudomode-enlarged GKSL (CPTP, few-mode) | arXiv:2506.10308 (Huang-Park-Chan-Lin; Eq. 2 coupled-Lindblad, Eq. 3 `C^c=g†e^{-iKt}g`, S2 matrix-`g` shared bath) | — (mechanism) | `coupled_lindblad_pseudomode_2506.10308.md` | `carrier/joint_lindbladian.py` (assemble_substep_channel, G2-cert); `outputs/coupled_pseudomode_pilot_v1_n2.py` |
| Near-resonant TLS energy exchange (the physical slot: g̃, κ, δ, N̄) | arXiv:2605.23385 (Gao; g̃/2π=1.4–10.4 MHz, T2R≈0.4 µs, T2E≈16 µs, TLS T1=44.7 µs) | — | `gao_nonlocal_nonmarkovian_tls_2605.23385.md` | `outputs/quantum_bath_m2_dual_arm.py`, `pilot3_relaxation_block_vs_unitary.py` |
| **The source→record map (THE observability calculus)** | **Prop IW-1 (ours, a-class, 16/16 machine-verified)** — passive real machine is EVEN in the commutator sector; wedge lives ONLY in outcome-resolved cross-moments; `W₁₂ ≈ −8κ²` | Prop IW-1 §5b | `involuntary_w_check_2026-07-03.md` | `outputs/involuntary_w_check_v{1,2}.py`, `cgf_probe_v1.py` |
| Source-layer wedge metric = CP-divisibility breaking | arXiv:0911.4270 (RHP; `I=−2∫_{γ<0}γ dt`), arXiv:0908.0238 (BLP; `N(Φ)` trace-distance backflow) | same | `rhp_nonmarkovianity_measure_0911.4270.md`, `blp_nonmarkovianity_measure_0908.0238.md` | `outputs/coupled_pseudomode_pilot_v1_revival_robustness.py`, `wedge_effect_size_2q_shared_mode.py` |
| Classical-1/f record-effect BRACKET (QEC markovianizes 1/f) | arXiv:2507.08713 (Gravier; QEC → Markovian logical noise, quartic `T_L∝T_phys⁴`) | — | `nonmarkovian_noise_resilience_silicon_spin_2507.08713.md` | — |
| 2-point detector autocorr is INSUFFICIENT (don't headline it) | arXiv:2410.23779 (Kam; data-qubit temporal corr = Class-0 benign; 2-point `p̄_{t,t'}` cannot discriminate) | — | `kam_nonmarkovian_surface_code_2410.23779.md` | — |

Foundational anchors (pre-2022, cited as foundational per the recency policy): motional-narrowing /
fast-fluctuation limit = **Kubo–Anderson stochastic lineshape** (Anderson 1954 J. Phys. Soc. Jpn 9,
316; Kubo 1954 ibid 935) — the wedge → 0 as bath correlation time → 0 at fixed integrated power;
instantiated numerically in the pilot (below).

---

## 1. The mechanism (anchored; reuse where it exists)

The quantum-bath teacher couples the data-qubit register to an explicit **quantum memory** (a
pseudomode-enlarged GKSL, arXiv:2506.10308) so the reduced window dynamics breaks CP-divisibility.
Two physically-grounded slots, both with the SAME record-visibility structure (§2):

- **Dephasing slot (Z-coupling):** `H_SB = (g/2) Z ⊗ (a+a†)`, the near-resonant/low-frequency
  memory-ful dephasing. Exactly the Prop IW-1 minimal-cell coupling. Source-layer wedge measured:
  `N_BLP = 0.11`, RHP `I = 2·ΔΓ = 0.36 @γ≈0.05`, `D_Choi(vs best-Markov) = 0.20`
  (`wedge_effect_size_2q_shared_mode.py`; robustness sweep `..._revival_robustness.py`).
- **Relaxation/T1 slot (transverse JC coupling):** `H_SB = g(σ⁺b + σ⁻b†)`, the near-resonant TLS
  energy exchange. NON-unital ⇒ the M1 unitality theorem (`quantum_bath_slot_prereg.md` §4, a-exact):
  a classical Gaussian field + arbitrary deterministic control is UNITAL, so T1 relaxation is
  classically unrepresentable AT THE CHANNEL LEVEL, first order in γ (`D_matched ≥ γ/2`). Measured
  channel wedge: `D_matched` resonant 0.4336, dispersive 0.0706 (`quantum_bath_m2_dual_arm.py` v3).

**Reuse (do NOT rebuild):** the enlarged dynamics is again GKSL ⇒ propagated by the G2-certified
`carrier/joint_lindbladian.assemble_substep_channel`; the embedding + independent-boson/JC oracle by
the pilot scripts; the matched-BCF classical imitator by the M2 dual-arm's classical arm. Swept
ranges (M1 bracket, all class (c)): `g̃/2π ∈ [1.4,10.4] MHz` rep 3; `κ=2λ ∈ [0.0625,2.5] µs⁻¹`
rep 2.5; `δ ∈ [0,500] MHz·2π`; `τ_idle ∈ [0.5,0.7] µs` rep 0.66; `γ=τ/T1 ∈ [1e-2,3e-2]`;
`N̄_eff ∈ [6e-6,1e-2]`; `s_T1 ∈ [0.25,0.67]` rep 0.4.

---

## 2. The source→record map = the observable (Prop IW-1 — the RIGHT one, NOT invented)

**This is the registered derivation duty (handoff §1 items 1–2 + scope §3.3), and it is DISCHARGED by
an existing a-class machine-verified theorem — Prop IW-1 (`involuntary_w_check_2026-07-03.md` §5b,
16/16 gates PASS).** We do NOT assume a source→record map; we inherit the proven one.

**Prop IW-1 (record evenness in the commutator sector), a-exact.** For a real passive machine
(X-parity projectors, resets, `|+⟩` entries all real) + a zero-mean Gaussian bath with real quadratic
`H_b` and real linear coupling `(a+a†)`-form, the record law is invariant under the global flip
`Im K → −Im K` at fixed `Re K`. Consequences (all machine-verified):

1. **(a) The passive record is LINEARLY BLIND to the commutator (non-Markovian/coherence) sector.**
   The quantum imprint can enter only through EVEN powers of the cross-window commutator integral
   `κ := −∫_{leg2}∫_{leg1} Im K(t₂−t₁) dt₁dt₂ = |α₁|² sin ωτ`.
2. **(a) Outcome-discarded moments are EXACTLY classical (all orders in g).** `E[m₁]`, `E[m₂]` equal
   the classical cosh law to ≤ 1.3e-13. ⇒ **first-order / marginal detector statistics carry ZERO
   quantum-vs-classical wedge.**
3. **(a) The ONLY quantum-vs-classical record imprint lives in the outcome-RESOLVED cross-moment
   `E[m₁m₂]`:** `W₁₂ = a(n̄, ReGram)·κ² + O(κ⁴)`, with `a → −8` (n̄-independent), machine-verified
   slope **3.998 ⇒ κ² ⇒ g⁴** in the coupling; coefficient stable ±0.12%.

**The registered observable (the RIGHT one).** The G0-quantum discriminator is the **outcome-resolved
cross-window cross-moment wedge**
```
W_rec := E_quantum[m_c,r · m_c,r+ℓ] − E_classical-imitator[m_c,r · m_c,r+ℓ]   (matched marginals),
```
per stabilizer `c`, cross-window lag ℓ, pooled over `(c, r)`. Leading order `W_rec ≈ 8κ²` per pair.

**Statistics the literature proves INSUFFICIENT — NOT the headline (registered exclusions):**
- **First-order / marginal detector rates** — Prop IW-1 (a): *exactly* classical, zero wedge. A
  discriminator built on them is vacuous by theorem.
- **2-point detector autocorrelation `p̄_{t,t'}`** — Kam arXiv:2410.23779 §IV.C proves it cannot
  discriminate benign from catastrophic temporal correlation; excluded as the headline.
- **LER / ΔLER** — A8-forbidden in the validity chain (SIMULATOR-not-decoder, memory
  `feedback-simulator-not-decoder`).

**Why "matched marginals" is mandatory (the crux, connecting to the classical G0-v2 lesson).** A fair
record-level ablation matches first-moment marginals (as G6/G0-v2 do). Under matched marginals:
- the dephasing slot's wedge is `W_rec ≈ 8κ²` (Prop IW-1, g⁴) directly;
- the relaxation slot's first-order non-unitality (channel `D_matched` up to 0.43) is a per-round
  POPULATION bias that a marginal-matched classical arm (its readout/reset marginals) ABSORBS; the
  residual is again the measurement-modulated, outcome-resolved, **g⁴** part. This is EXACTLY the
  CGF-probe two-component decomposition (`project-quantum-bath-m1-m2`): (i) theorem-pinned channel
  non-unitality 0.172 terminal = measurement-INDEPENDENT = marginal-absorbed; (ii) measurement-
  modulated asymmetry, slope 3.62 ≈ **g⁴** = the surviving record residual.
- ⇒ **under the fair comparison, BOTH slots force the quantum record wedge to second order (g⁴)** —
  the quantum analogue of the classical "matched marginals force the memory discriminator to second
  order" (G6-A1). An UNFAIR control (pure-dephasing classical arm with no population bias) would make
  the relaxation non-unitality first-order-visible, but that is a strawman control and is NOT
  registered as the discriminator.

---

## 3. The effect-size derivation + N_detect band (class (b); the decision statistic)

**Per-pair record wedge (a-anchored coefficient, b-anchored magnitude):** `W_rec ≈ 8κ²`, with `κ` the
cross-window commutator integral of the physical bath (§1 bracket). `κ` inherits the coupling scale:
`κ ∝ (g_eff)²` where `g_eff` is the per-window effective coupling (resonant `g̃τ`; dispersive
`g̃²τ/δ`). So `W_rec ∝ g_eff⁴` — the machine-verified slope-4.

**Sampling floor + pooling.** `W_rec` is a shift in a bounded (±1) cross-moment ⇒ per-pair SE ≈ 1/√N.
Pooling over `P` approximately-independent (stabilizer × round) cross-window pairs gives a √P SE gain
(declared (c) — the effective independent-pair count is bounded by the detector graph, and the
common-mode cancels in the quantum−classical difference, cf. G6-A1). Detection at 3σ:
```
N_detect(pooled) ≈ ( 3 / (√P · W_rec) )² = 9 / (P · (8κ²)²) = 9 / (64 P κ⁴).      (c-formula)
```

**Fold-attenuation (measured anchor).** The CGF probe measured the record floor "heavily
fold-attenuated ~O(10²)" relative to the channel wedge (`project-quantum-bath-m1-m2`) — the
projective-measurement fold that turns the channel-level `D_matched` (0.07–0.43) into the record-level
per-cell `W_rec ~ 1e-3…4e-3` at the near-saturation pilot regime (`g̃τ ~ 0.6`). At the physically
typical DISPERSIVE operating point (large δ, drift-driven near-resonance rare), `g_eff` is far smaller
and `W_rec ∝ g_eff⁴` collapses further.

**Registered N_detect band (b; the sizing script §8 computes the number from committed constants).**
- **P-G0Q-1 (b) — the headline.** Under the fair matched-marginal comparison, the pooled record wedge
  `N_detect(pooled)` for the physical bracket (§1) is **≫ feasible N** (registered feasible cap
  `N_feasible = 1e7`, one order above the classical 1e6 to be generous to the quantum arm). Predicted
  band: `N_detect(pooled) ∈ [1e8, 1e14]` across the (dispersive ↔ near-resonant) × (weak ↔ strong-κ)
  bracket, with the near-resonant strong-κ corner the only one approaching the cap. Basis: `W_rec ~
  8κ²` g⁴-suppressed + O(10²) fold-attenuation + finite pooling `P ≲ n_stab·R ~ 10²–10³`. A point
  reaching `N_detect(pooled) ≤ 1e7` is a registered FINDING (GO — the record wedge is reachable).
- **P-G0Q-2 (b) — the qualitative sign discriminator.** The outcome-resolved cross-moment carries a
  SIGN (CGF-probe P4: quantum emission anti-bunching `−4.1e-2` vs classical common-cause `+3.3e-3`).
  Registered: the quantum wedge sign is OPPOSITE the classical-imitator sign in the near-resonant
  relaxation slot. This does NOT lower `N_detect` (a sign still needs `N ~ 1/W_rec²`) but is the
  categorical signature IF a GO point exists.
- **P-G0Q-3 (b) — Gravier consistency bracket.** The classical-1/f record effect is itself
  markovianized by QEC (arXiv:2507.08713: quartic `T_L`, low-frequency whitening); the quantum wedge,
  being g⁴-suppressed AND confined to outcome-resolved cross-moments, is a-fortiori smaller than the
  (already record-benign) classical 1/f effect at matched marginals. Consistent with NO-GO.

**Registered expectation (predict-before-measure, class (b)): NO-GO** — the fair record-level quantum
wedge is sub-detectable at feasible N, capped at the source/channel layer. This MIRRORS the classical
G0-v2 STOP and shares its structural cause (matched marginals → second order). A GO would be a
surprise FINDING (the fold-attenuation or pooling is more favorable than derived) — reportable, not
suppressed.

---

## 4. The motional-narrowing collapse control (a hard control; already grounded)

The wedge MUST vanish in the fast-bath (motional-narrowing / Kubo–Anderson) limit — the criterion
that kills a mislabeled classical imitator (scope §3 gate 2).

- **(a) Derivable from κ.** `κ = |α₁|² sin ωτ`, `α₁ = −i(g/2)∫₀^τ e^{iωt}dt`. As the bath correlation
  time `τ_c → 0` (fast/broad bath, `κ_bath = 2λ → ∞` at fixed integrated power `∫J`), the leg
  displacement `α₁` decorrelates within the window and `κ → 0` ⇒ `W_rec = 8κ² → 0`. Foundational
  anchor: Kubo–Anderson fast-fluctuation lineshape (Anderson 1954; Kubo 1954).
- **(a/numerically-confirmed) Pilot-demonstrated.** `wedge_effect_size_2q_shared_mode.py` +
  `..._revival_robustness.py`: the source-layer wedge collapses `N_BLP: 0.11 → 0` as `γ → 5`
  (fast bath), and the overdamped wedge = 0 exactly — the registered positive control that the
  non-Markovian signal is REAL, not spurious.
- **Registered control C-MN (c):** in the sizing (§8) and any eventual run, the fast-bath corner
  (`κ_bath ≥ 4g`, overdamped) must give `W_rec` consistent with 0 within SE. A non-vanishing wedge in
  the motional-narrowing limit = a mislabeled-imitator bug ⇒ STOP.

---

## 5. Independent ground truth (Rule I, non-circular)

- **The source→record map (Prop IW-1)** rests on TWO independent computation routes already run to
  agreement ≤ 1e-9 (dense qubit⊗Fock evolution vs exact conditional-displacement path sum) + the
  exact-classicality closed form (cosh law) + a from-scratch check — NOT the carrier's own oracle.
- **The source-layer wedge magnitude** is certified vs the independent-boson closed-form oracle
  (2.5e-8, pilot v1) and the N=400 unitary-discretization oracle (pilot-3) — genuinely different
  objects (Hamiltonian diagonalization, no master equation).
- **The classical imitator floor** is the M2 dual-arm's matched-BCF arm, anchored to `D_matched ≥ γ/2`
  (the a-exact unitality theorem) — a lower bound independent of the record-N problem.
- **Anti-circular rule:** the quantum arm is NEVER scored against a pseudomode-derived reference; the
  classical imitator is NEVER its own sampler moments alone.

---

## 6. Bounded simplifications (Rule III; unbounded ⇒ STOP)

| # | simplification | class | bound / honesty statement |
|---|---|---|---|
| S1 | Prop IW-1 minimal cell (1 qubit, 2 legs) → full surface-code record | (c) | the cross-moment structure is per-(stabilizer, cross-window) pair; the FULL-record sizing folds in the pooling factor `P` (declared, upper-bounded by the detector graph) — the per-pair `8κ²` is the a-anchored unit |
| S2 | `a = −8` coefficient (n̄-independent limit) | (b) | machine-observed to −7.997/−7.994 at g=0.025; the closed-form derivation is an open remark, NOT load-bearing (only the SLOPE-2/κ² and the O(10²) fold are load-bearing for N_detect order-of-magnitude) |
| S3 | Pooling `P` independent pairs (√P SE gain) | (c) | OPTIMISTIC on N (over-counts independence) ⇒ true N_detect ≥ the sized value ⇒ a NO-GO verdict is CONSERVATIVE; a GO must survive a correlated-pair penalty |
| S4 | O(10²) fold-attenuation from the CGF-probe regime | (b) | measured at `g̃τ~0.6`; the dispersive operating point is MORE attenuated ⇒ NO-GO conservative; the near-resonant strong corner is the only GO candidate and is sized explicitly |
| S5 | Gaussian bath (pseudomode) | (c) | inherited carrier scope; non-Gaussian single-TLS (telegraph saturation) bracketed OUT (2506.10308 boundary) |
| S6 | `N_feasible = 1e7` cap | (c) | one order above the classical 1e6 — generous to the quantum arm; declared, not physical |

---

## 7. Epistemic status (METRICS-ladder)

- **(a) exact:** Prop IW-1 (record evenness; outcome-discarded moments exactly classical; wedge =
  `8κ²`) — 16/16 machine-verified; the M1 unitality theorem (`D_matched ≥ γ/2`); the RHP/BLP closed
  forms; the motional-narrowing κ→0 derivation.
- **(b) bands:** P-G0Q-1 (N_detect ≫ feasible), P-G0Q-2 (sign discriminator), P-G0Q-3 (Gravier
  bracket); the `a=−8` coefficient; the O(10²) fold. A miss is a FINDING, never later citable as fact.
- **(c) gates/brackets:** the physical bracket (§1); the pooling model; `N_feasible=1e7`; C-MN control.
- **The headline verdict (GO vs NO-GO) stays PROVISIONAL** until the §8 committed-constant sizing runs
  (`python-exit=0`) and — if GO — the eventual GPU record measurement confirms. Nothing is built on
  (b)/(c) items; the A′-vs-B decision is a go/no-go GATE, the licensed use of a (c)-verdict.

---

## 8. The decision rule + the committed-constant sizing (predict-before-measure artifact)

**Script (to write + run, CPU-only, NO GPU, NO model code):**
`outputs/twin_validation/g0_quantum_feasibility_from_constants.py` (runner
`outputs/run_g0_quantum_feasibility.sh`; artifact `..._g0_quantum_feasibility.json`). It computes,
from the §1 committed constants + Prop IW-1's `a=−8` + the pooling/fold model:
1. `κ(g_eff)` per operating point (resonant `g̃τ`; dispersive `g̃²τ/δ`) across the bracket;
2. `W_rec = 8κ²` per pair; the O(10²) fold; the pooled `N_detect = 9/(64 P κ⁴)`;
3. the motional-narrowing corner check (`W_rec → 0` as `κ_bath ≥ 4g`);
4. a positive control (a planted large-κ point where `N_detect ≤ 1e7`, confirming the sizing CAN
   return GO) and a from-scratch cross-check of `W_rec` at one point (independent of the formula).

**P-G0Q-DECISION (c) — THE decision rule.**
- **GO** ⇔ ∃ a physically-admissible operating point (inside the §1 bracket, passing C-MN) with
  `N_detect(pooled) ≤ N_feasible = 1e7`. ⇒ a record-level quantum-vs-classical wedge is reachable ⇒
  **run the classical record foil (A′): the CoupledCycleTeacher is the executed matched-marginal
  record control, ready for the record-level ablation.**
- **NO-GO** ⇔ no such point. ⇒ the wedge is capped at the source/channel layer ⇒ **the classical
  record round lands as B** (STOP-as-finding, no executed record suite); the quantum round's control
  is the source/channel-layer matched-BCF imitator (M2 dual-arm, RHP=I=0 by construction), which is
  independent of the classical record round. The record-level classical foil is NOT built (it would
  be insurance for a wedge that does not reach records).

---

## 9. Registered-predictions summary table

| id | class | statement (short) | miss handling |
|---|---|---|---|
| Prop IW-1 | a | record even in commutator sector; wedge = `8κ²` in outcome-resolved cross-moments only | proof error ⇒ STOP (already 16/16 verified) |
| P-G0Q-1 | b | pooled `N_detect ∈ [1e8,1e14] ≫ 1e7` under matched marginals | FINDING (a GO point is a reportable surprise) |
| P-G0Q-2 | b | quantum cross-moment sign opposite classical (near-resonant) | FINDING |
| P-G0Q-3 | b | Gravier bracket: quantum wedge < classical-1/f record effect (already benign) | FINDING |
| C-MN | c | wedge → 0 in motional-narrowing (fast-bath) limit | STOP (mislabeled imitator) |
| P-G0Q-DECISION | c | GO (≤1e7 point exists) ⇒ A′; else NO-GO ⇒ B | go/no-go GATE |

---

## 10. What this prereg does NOT license

- No model code beyond the CPU committed-constant sizing (§8) until the verdict + user confirmation.
- No claim that the source/channel-layer wedge is small — it is LARGE and certified (N_BLP=0.11,
  D_Choi=0.20–0.43, RHP ΔΓ=0.36). This gate is ONLY about whether that wedge survives to RECORDS at
  feasible N under a fair comparison.
- No retraction of the frame: a NO-GO SHARPENS it (the quantum contribution lives at the source/channel
  layer, where the classical imitator is provably RHP=I=0 and cannot forge the wedge) exactly as the
  classical G0-v2 STOP sharpened it.

---

## 11. RESULTS (post-sizing, 2026-07-03) — predict-before-measure outcome

**Sizing run:** `outputs/twin_validation/g0_quantum_feasibility_from_constants.py` via
`outputs/run_g0_quantum_feasibility.sh` (`python-exit=0`); evidence
`outputs/twin_validation/g0_quantum_feasibility.json`, log `outputs/logs/g0_quantum_feasibility.log`.
CPU-only committed-constant arithmetic; NO GPU, NO model code. Controls: anchor check PASS
(closed-form W_rec 7.68e-3 vs machine-measured 6.94e-3, rel-dev 0.107 = the expected a=8↔n̄-shifted-7.2
gap; from-scratch quadrature 2.4e-11), motional-narrowing PASS (collapse ratio 1.6e-7), positive
control PASS.

**VERDICT = GO-CORNER-ONLY** (`GATE_RESULT G0_quantum_effectsize GO-CORNER-ONLY`).

**CORRECTION (2026-07-03, user-caught — a real error, retracted).** An earlier read of this run claimed
the quantum wedge is "~9–10 orders LARGER than the classical G6 memory (4.7e-2 vs 5.6e-12)". **That
comparison was WRONG** — a unit + coupling-regime mismatch: it put the quantum wedge at *saturation*
(dimensionless `8κ²=4.7e-2`) against the classical memory at *realistic weak* coupling (`Δγ=5.6e-12`
in **γφ² units**, needing a `(0.5·τ_eff)²` conversion). The arithmetic (κ formula) was fine — the CLAIM
was not. First-order IS matched-equal for BOTH (Prop IW-1 outcome-discarded exactly classical); both
wedges are SECOND order, so at comparable coupling they MUST be comparable — a 10-order gap was the tell.

**Apples-to-apples (same dimensionless record-covariance units, matched realistic coupling):**
- CLASSICAL (G6, realistic weak γφ): `Δ_record = 7.06e-8`, N ~ 1.8e15.
- QUANTUM (typical dispersive `g_eff≈0.075`, syndrome fold 100): `W_rec = 9.32e-8`, N ~ 1.0e15.
- **Ratio = 1.32 — SAME ORDER.** At the typical operating point the quantum record wedge ≈ the (dead)
  classical memory; both are sub-feasible by ~8–9 orders.

**Where the quantum DOES exceed classical — the near-resonant/strong CORNER only:** at saturated coupling
(`g_eff ≥ 0.63`, e.g. a near-resonant TLS episode) `W_rec` saturates ~`4.7e-2` (unfolded) / `4.7e-4`
(fold 100), giving `N_detect(pooled) ≈ 4.6e5 ≤ 1e7` — GO. But (i) this is a favorable, physically-real-
but-RARE regime (drift-driven near-resonance, M1 §3 S3 "favorable-instance"); (ii) `N_single ≈ 4.0e7`,
so even the corner GO leans on the √P pooling gain; (iii) `N_detect ∝ g_eff⁻⁸` below saturation, so the
reachable region is a NARROW strong-coupling corner (a factor-2 in coupling ⇒ factor-256 in N). `f_crit
≈ 467` (with pooling), so the corner stays GO only if the true syndrome fold ≤ f_crit.

**P-G0Q-1 partial MISS (recorded, not re-fit).** My registered NO-GO band `[1e8,1e14]` is CORRECT for the
typical operating point (~1e15) but not for the narrow near-resonant corner (~1e5–1e7). The honest
verdict is neither a clean NO-GO nor the (retracted) categorical GO: it is **GO only in a fragile
favorable corner, ≈ classical (dead) at typical coupling.**

**DECISION (P-G0Q-DECISION) — RE-OPENED for the user.** The corrected picture substantially WEAKENS the
earlier "A′ clearly worth running": the quantum record wedge is NOT categorically better than the
classical — it is comparable (dead) at typical coupling and only borderline-reachable in a rare
strong-coupling corner. So the robust quantum contribution stays at the SOURCE/CHANNEL layer (where the
wedge is large & certified: N_BLP=0.11, D_Choi=0.20–0.43, RHP ΔΓ=0.36 — and the classical imitator is
provably RHP=I=0 there). Whether the fragile near-resonant record corner justifies building the executed
record foil (A′) vs landing the classical round as B is a **scope call for the user**, no longer a clear
A′ win. This is a DERIVATION verdict; the GPU record measurement stays the pending check; PROVISIONAL.
