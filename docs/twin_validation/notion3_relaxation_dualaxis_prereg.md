# notion-3 on the GENUINELY-QUANTUM component: relaxation × dual-axis (X+Z) — Pre-Registration (theory-first)

> **SUPERSEDED INTERPRETATION, 2026-07-13.** The physical shared-mode model and historical run
> design remain useful, but `K=P_all-P_skip` is not a model-free quantum-memory certificate.
> Non-unital dynamics can be non-random-unitary while a fixed record still fails to identify the
> process-level origin; conversely, Markovian coherence-generating/detecting dynamics can yield
> `K>0`. Use
> [`notion123_taxonomy_literature_closure_2026-07-13.md`](notion123_taxonomy_literature_closure_2026-07-13.md)
> for the current taxonomy.

Status: PRE-REGISTRATION, 2026-07-05. Predictions written BEFORE the run; a miss is a finding, not a re-fit.

**DECISION (2026-07-05, user): the σ− relaxation is modelled as EMISSION INTO THE SHARED MODE**
`(g0^− σ−^{d0} + g1^− σ−^{d1}) b† + h.c.` on the SAME bosonic mode that carries the σz dephasing — the
fully-shared, correlated AND memory-bearing bath (chain_mapping 2407.10140), NOT a Markovian Lindblad σ−
collapse. This resolves the §1↔§5 ambiguity in favor of the fuller "non-Markovian correlated coupling is THE
contribution" model ([[project-coupling-nonmarkovian-is-the-contribution]]). Cost: one mode does double duty
(dephasing displacement + emission), so Fock convergence needs a larger nmax; still ONE mode ⇒ dim = 16·nmax
(2 data + 2 ancilla + mode), reduced-superop trick (idle on d0,d1,mode; both ancillas spectators) unchanged.
crow_joynt makes K>0 from this sector genuinely-quantum REGARDLESS of memory (amp-damp/emission is not
random-unitary), and the shared mode additionally makes it memory-bearing — so K∧M_mem are BOTH testable here.

**The reframe (why the prior notion-3 verdict was through a suppressing lens).** We characterized notion-3
(K = Kolmogorov violation = "no classical process reproduces the record") on a **pure σz-dephasing** shared
bath, measured **X-only**, on **|++>**. Two theorems say this is the wrong place to look:
- **crow_joynt 1309.6383 (PRA, a-exact):** single-qubit pure dephasing by ANY quantum bath is **CLASSICALLY
  SIMULABLE** (exact random-unitary / classical-field reproduction). ⇒ a pure σz bath's records carry almost NO
  non-classicality **by theorem** — the observed K fragility/sign-blindness/DFS-collapse is a *consequence of
  the classically-simulable component*, NOT evidence notion-3 is weak.
- The **genuinely-quantum, NON-classically-simulable** noise is **relaxation / amplitude-damping (σ−,
  non-unital, population-moving)** — crow_joynt's explicit out-of-scope class. notion-3 K should be ROBUST there.
- The relaxation component imprints on the **COMPLEMENTARY stabilizer** (C4-analog: amp-damp shows in both
  bases; σ− where σz-dephasing does not) ⇒ it needs **DUAL-AXIS (X+Z)** — exactly what real QEC measures.

So the faithful notion-3 test = a **multi-component shared bath (σz dephasing + σ− relaxation) measured on BOTH
X and Z stabilizers**, with the genuinely-quantum signal expected in the relaxation/complementary-axis sector.
Scope: SIMULATOR record-char faithfulness (is the QUANTUM contribution robust on the faithful carrier), NOT twin
recovery. This directly tests whether "notion-3 fragile" was intrinsic or a lens artifact.

## 0. Grounding ledger (all 精读)

| claim | anchor | role |
|---|---|---|
| pure dephasing / depolarizing = CLASSICALLY SIMULABLE (random-unitary), constructive classical field | crow_joynt 1309.6383 (a-exact theorem + Eq.13-15 field construction) | ⇒ σz-bath K limited BY THEOREM; the classical field = an OPERATIONAL independent-GT |
| relaxation / amp-damp / non-unital = NOT classically simulable (affine/population term has no random-unitary form) | crow_joynt PAGE 3 counterexample; the γ/2 non-unitality line ([[project-quantum-bath-m1-m2]]) | ⇒ relaxation = the genuinely-quantum component where K is robust |
| shared bath with BOTH σz-dephasing AND σ−-relaxation coupling is admissible + correlated | chain_mapping 2407.10140 (Eq.2, no restriction on O^(i)); t_tedopa 2606.30569 (cross-spectral matrix) | the multi-component bath MODEL; + an independent TN oracle option (≤6 qubits) |
| AD + PD microscopic Kraus + magnitudes (T1, Tφ) | arsenijevic 1606.01145; quiroz 2412.16092 (T1/Tφ realistic) | grounded component magnitudes |
| quantum bath survives via its COMPLEMENTARY (noncommuting) stabilizer; real QEC measures BOTH X+Z | C4-analog (committed, both-bases K: σz→X, σx→Z, amp-damp→both) | dual-axis necessity |
| K = Milz Kolmogorov / Budini DNI on the multi-time syndrome distribution | milz 1907.05807; budini 2301.02500/2411.13471 | the observable, applied to the joint (X,Z) record |

## 1. Mechanism (anchored)

Exact-DM: 2 data (d0,d1) + 2 ancillas (a_X, a_Z) + shared pseudomode(s). Shared bath couples BOTH:
- **dephasing** `(g0^z σz^{d0} + g1^z σz^{d1})(b+b†)` (Tφ — the classically-simulable sector), and
- **relaxation** `(g0^− σ−^{d0} + g1^− σ−^{d1}) b† + h.c.` — Jaynes-Cummings (RWA) EMISSION into the SAME mode
  (LOCKED, the §DECISION choice): each qubit de-excites (σ−) while creating a mode photon (b†), the mode loss
  √(2γ)b then carries the excitation away (Purcell-type relaxation). Non-unital (population-moving), correlated
  (shared mode), memory-bearing. NOT a Markovian σ− collapse.
Total shared-bath H on (d0,d1,mode): `H = ζ b†b + (g0^z σz0 + g1^z σz1)(b+b†) + [(g0^− σ−0 + g1^− σ−1) b† + h.c.]`,
collapse `√(2γ) b`. Per round: idle-evolve under this multi-component GKSL; extract **X_{d0}X_{d1} via a_X** AND
**Z_{d0}Z_{d1} via a_Z** SEQUENTIALLY (a_X entangle→Born-measure→reset, then a_Z entangle→Born-measure→reset —
X0X1 and Z0Z1 commute, so the joint per-round outcome m_r=(s_X,s_Z)∈{0,1,2,3} is a well-defined instrument, as
in a real surface-code cycle). Record = the joint (X,Z) syndrome stream M_t. Component knobs: dephasing-only
(g^−=0) / relaxation-only (g^z=0) / both; the σ− strength g^− and the ratio r=g1/g0 swept.

## 2. Observable (the RIGHT one — K on the FULL syndrome; per-component + per-axis)

- **K_joint** = Milz/Budini Kolmogorov violation on the **joint (X,Z) syndrome record** (the full real-QEC
  syndrome), NOT X-only. Plus the per-axis decomposition **K(X), K(Z)** and per-component (dephasing-only vs
  relaxation-only vs both).
- **C_pf** (budini memory axis) for context. N_detect for K_joint (feasibility).

## 3. Predicted behavior (falsifiable) + epistemic classes

- **(a) exact — the crow_joynt discriminator:** the DEPHASING-only sector is reproduced by an EXPLICIT classical
  random-unitary field (crow_joynt Eq.13-15) ⇒ its K → 0 (constructively, not by fiat). The RELAXATION sector is
  non-unital ⇒ NO such classical field ⇒ its K > 0 is genuinely quantum.
- **(b) THE headline:** on the multi-component bath measured DUAL-AXIS, **K is dominated by the RELAXATION
  component and is ROBUST — NOT corner-confined, NOT sign-blind, NOT DFS-collapsing** the way the pure-dephasing
  K was. Specifically: relaxation-only K(Z) (the complementary axis) is feasible across a BROAD coupling range
  (contrast the dephasing-only corner). **Falsifier (weighty):** if even the relaxation component gives
  fragile/corner-confined/vanishing K on dual-axis, then notion-3 IS intrinsically fragile on the faithful
  carrier — a strong, sobering finding (the lens was NOT the whole story).
- **(b) reproduce the prior:** dephasing-only, X-only ⇒ the fragile/sign-blind/DFS K we already measured
  (consistency bridge — confirms the reframe, not a new artifact).
- **(c) gates:** classical-field-reproduces-dephasing (K_deph → 0 under the crow_joynt construction);
  C4-analog both-bases sanity (σz→X, amp-damp→both); Fock/level convergence; no-bath flat.

## 4. Independent ground truth (non-circular — STRONGER than before)

- **crow_joynt classical-field construction = the operational independent-GT for "is it quantum" (constructive,
  NOT K=0-by-fiat).** The σz-only sector (g^−=0) is a collective PURE dephasing of the data pair by a Gaussian
  bosonic bath; the collective coupling S_z=g0σz0+g1σz1 commutes with itself at all times, so time-ordering drops
  (crow_joynt PAGE 2/3) and the reduced record equals a classical GAUSSIAN average of random σz-rotations
  exp(−i S_z φ_r) per round, with the per-/cross-round phase covariance Σ_{rs} MATCHED to the mode's symmetrized
  two-time correlation ⟨{(b+b†)(t),(b+b†)(t′)}⟩ integrated over the round windows (Σ_{rr} ties to Γ_unit(τ)=
  `n3._gamma_of_t`; Σ_{r≠s} is the persistent-mode cross-round memory). Each realization is a product of σz
  unitaries indexed by the Gaussian latent φ ⇒ a genuine classical stochastic process ⇒ **Kolmogorov-consistent
  ⇒ K=0 EXACTLY, by construction.** Two CONSTRUCTIVE gates make this non-vacuous (anti-toy Rule I; the null is a
  DIFFERENT method — classical random-unitary field, no bath): **(G-repro)** the field-null dual-axis record must
  REPRODUCE the quantum σz-only record's per-axis marginals + CMI/M_mem to tol (same reduced dynamics — else the
  field is mis-matched, not a valid null); **(G-K0)** its K ≈ 0. Then the HEADLINE: K(relaxation-only) and
  K(both) must EXCEED this null's K by a detectable margin.
- **Reconciliation of the prior σz "residual" (sakuldee trip-wire):** the prior lens measured a small NONZERO
  pure-σz K (~3.3e-4 at r=1, peak ~1.38× at |r|≈0.3). crow_joynt's theorem says a Gaussian pure-dephasing sector
  is random-unitary ⇒ K MUST be 0; K is a function of the record, so a matched classical field reproducing the
  record CANNOT have a different K. ⇒ predict (a-exact consequence): as Fock/quadrature convergence tightens, the
  quantum σz-only K collapses onto the field-null K≈0 (the residual is numerical, NOT a physical multi-round
  effect). Registered falsifier: if the σz-only K persists ABOVE the field-null after convergence AND the field
  reproduces the record, that is a genuine contradiction to investigate (measurement-instrument subtlety), not a
  headline.
- **chain_mapping / t-TEDOPA TN oracle (option):** the multi-component shared-bath dynamics has an INDEPENDENT
  exact TN oracle (≤6 qubits, explicit bath) — a different-blind-spot cross-check of the GKSL evolution if needed.
- **C4-analog both-bases anchor** (committed): σz→X-stab, σx→Z-stab, amp-damp→both — re-assert on the components.
- **build_L GT** (independent-boson closed form) for the dephasing part; a T1-decay closed form for the relaxation part.

## 5. Bounded simplifications (declared)

- **(c) 2 data + 2 ancillas (X & Z stab) + ONE shared mode** — dim = 2·2·2·2·nmax = 16·nmax. The σ− emission
  couples into the SAME mode (the §DECISION choice) so there is NO 2nd Fock mode; the reduced-superop trick (idle
  Liouvillian on d0,d1,mode = 4·nmax; both ancillas spectators, E_full = E_red ⊗ I_{a_X} ⊗ I_{a_Z}) keeps the
  built superop at (4·nmax)² sq exactly as v2. Declare the dim bound + OOM guard; the shared mode doing double
  duty (σz displacement + σ− emission) needs a LARGER nmax for Fock convergence — extend the ladder and the
  NMAX_HARD_CAP margin; STOP with a dim-wall report rather than OOM if convergence exceeds the cap.
- **(c) RWA (Jaynes-Cummings σ−b†) / single mode / σz + σ− components** — the two paradigmatic sectors
  (classically-simulable dephasing + genuinely-quantum emission); leakage is a further axis. Declared. The RWA
  (drop σ−b + σ+b† counter-rotating terms) is grounded in chain_mapping/weak-coupling; declared bound (c).
- **(c) CPU exact-DM, Fock nmax convergence.** As before.

## 6. Epistemic status (METRICS-ladder)

- **(a) exact:** crow_joynt dephasing = classically simulable (theorem); the explicit classical field; relaxation
  = non-unital ⇒ not random-unitary; K ≡ Milz/DNI; C4-analog both-bases.
- **(b) bands:** relaxation K robust vs dephasing K fragile (the headline); the broad-vs-corner contrast; K(Z)
  relaxation magnitude / N_detect.
- **(c) gates:** classical-field-null; convergence; both-bases sanity.
- **Provisional:** whether relaxation robustly rescues notion-3 is the OPEN question the run decides — both
  outcomes (robust ⇒ notion-3 was lens-suppressed; still-fragile ⇒ intrinsic) are real findings. Nothing built on it yet.

## 7. Build org (scouts light — reuse v2 carrier + add σ− + Z-ancilla + crow_joynt null; builder + un-led reviewer)

Reuse `notion3_ancilla_mediated_run.py` v2 (build_L2, reduced-superop idle apply, joint-parity extraction,
measure_reset, K_stat/M_mem/CMI, controls) — the shared-bath σz machinery is verbatim. Builder adds:
(1) the σ−-EMISSION coupling `(g0^− σ−0 + g1^− σ−1)b† + h.c.` INTO THE SHARED MODE in `build_L2` (the §DECISION
choice — one mode, non-unital, memory-bearing); (2) a SECOND ancilla a_Z with a Z_{d0}Z_{d1} extraction, the
SEQUENTIAL dual-axis per-round instrument (a_X then a_Z), and the joint 4-ary syndrome record m_r=(s_X,s_Z);
(3) generalized K_joint + per-axis K(X)/K(Z) (marginalized) + M_mem/CMI over the 4-ary alphabet, per-component
(dephasing-only g^−=0 / relaxation-only g^z=0 / both); (4) the crow_joynt Gaussian-field null (§4: matched-Σ
random-σz-rotation mixture, EXACT-in-Gaussian; gates G-repro + G-K0); (5) component/coupling/r sweeps + the
robust-vs-fragile contrast (relaxation K vs the field-null across a BROAD g/r range). CONTROLS carry over
(factorization GT now E_red⊗I_{a_X}⊗I_{a_Z}; extraction GT for BOTH axes; 2-qubit indep-boson GT for the σz
sector; a T1/emission closed-form GT for the σ− sector — reduced-qubit population decay vs the Purcell rate;
no-bath flat; non-degeneracy asserts on EACH axis). Un-led reviewer (problem+goal+artifact only, reproduce from
scratch): confirm the field-null is the genuine constructive crow_joynt (G-repro + G-K0, NOT K=0-by-fiat), K is
real Milz on the JOINT record, the dual-axis sequential instrument is a valid commuting-stabilizer measurement,
the σ− sector is genuinely non-unital (populations move), and the robust-vs-fragile contrast is honestly
supported (with N_detect feasibility). Then serial CPU run (capture python-exit INSIDE wsl; no GPU concurrency).

## 8. SMOKE FINDINGS + REGISTERED PREDICTION MISSES + CORRECTED DISCRIMINATOR (2026-07-05, pre-full-run)

The build (`notion3_relaxation_dualaxis_run.py`) is machinery-CERTIFIED (all controls green: factorization GT
5.6e-17, σ− emission GT vs the exact single-excitation amplitude ODE 5.6e-16 + non-unital, both extraction axes,
σz indep-boson GT, no-bath K=0, Σ/Γ crow_joynt covariance vs `_gamma_of_t` + Scout-A matrix). Smoke (nmax≤10,
GH n=16, coarse grids; the RELAXATION sector Fock-converges by nmax=8) surfaced two **registered
predict-before-measure MISSES** (a miss is a finding, never a silent re-fit) that CORRECTED the discriminator:

- **MISS 1 — "the crow_joynt field-null K → 0 constructively" (§3a, §4) is WRONG.** The dual (X,Z) measurement
  projects the data to the **Bell basis**, which differs from the σz-dephasing (Z-comp) basis, so a purely
  CLASSICAL σz field produces a small **GENUINE** K (~3e-4, all on X). crow_joynt's theorem guarantees the
  *channel* is classically simulable (random-unitary), **NOT** that the measured record's K is 0 under a
  non-commuting measurement. ⇒ the field null is the **classically-ACHIEVABLE dephasing-sector K**, not 0; its
  role is the G-repro independent confirmation (a classical σz field reproduces the quantum σz record, max|dP|
  ~1e-3), not a K=0 floor. The G-K0 gate is retired.
- **MISS 2 — "relaxation K robust ⇒ notion-3 lens-suppressed" (§3b) is a FALSE POSITIVE on K_Z.** An incoherent,
  **Markovian** amplitude-damping channel (non-unital, NO coherence, NO mode) **forges K_Z ≈ 0.25** — as large as
  the quantum emission's K_Z (0.20). Because non-unital ≠ random-unitary (crow_joynt), ANY non-unital channel's
  dual-axis record carries K (measurement-incompatibility). So **K alone is NOT a quantum-bath witness** (confirms
  the "deepen" lesson: K forgeable by a Markovian invasive control). Caught by the classical-AD null (the matched
  Markovian null the simulator discipline requires; [[feedback-simulator-is-goal-twin-is-next]] error-A).

- **CORRECTED DISCRIMINATOR (user 2026-07-05, strictest null).** Compare the quantum σ− emission against a GRID
  of incoherent-AD nulls — Markovian AD **and** classical NON-Markovian AD (AD + a 2-state classical latent = K
  AND memory). The signature that survives even the strictest is the **COHERENT complementary-axis imprint K_X**:
  every incoherent AD (Markovian or non-Markovian) gives **K_X ~ 9e-16 ≈ 0** (no coherence generation), while the
  quantum coherent emission gives K_X > 0. **Smoke result:** quantum relaxation K_X = 0.057 (N_det ≈ 2.8e3,
  feasible), incoherent-AD K_X ceiling 9e-16, irreducible record-distance to the best classical AD = 0.055
  (feasible) — genuine coherent K_X across **100 %** of the RWA-valid band (gm 0.1→0.35). ⇒ **notion-3 SURVIVES
  the strict matched nulls as the coherent K_X + record excess, NOT the forgeable K_Z bulk.** Epistemic classes:
  the AD-ceiling K_X≈0 and the σ− GT are (a)-exact; the coherent-K_X robustness/feasibility band is (b); the
  detectability thresholds are (c). The full run re-confirms at nmax→16, GH n=24, finer grids (gm 0.05–0.7, r
  0/0.5/1) before any conclusion is drawn.

## 9. THE K_X DISCRIMINATOR OF §8 IS ALSO WRONG — un-led reviewer + the corrected record-distance discriminator (2026-07-05)

**§8's "coherent K_X survives" was a SECOND false-positive, broken by the un-led adversarial reviewer** (who
reproduced the whole pipeline from scratch to 12 digits, then attacked the claim). ROOT CAUSE = circular
verification: the incoherent-AD null `_ad_channel_data` hard-coded amplitude damping in the **Z-basis only**, so
K_X ≈ 0 **by construction** — the control shared the engine's blind spot (anti-toy Rule I violation). The
reviewer built a legitimate counter-null: **X-basis AD** (relax toward |+⟩; equally CPTP, non-unital,
coherence-free) — it **FORGES K_X = 0.25**, and = 0.057 (the exact quantum value) at p≈0.19. The dual-axis
instrument is **basis-symmetric**: AD toward ANY Bloch axis forges K on that axis (Z→K_Z, X→K_X, Y→joint).
⇒ **K, K_X, K_Z are ALL forgeable by an incoherent AD — none is a quantum witness.** (Certified independently:
`notion3_axis_ad_selfcheck.py`; and directly reproduced by the reviewer.)

**CORRECTED DISCRIMINATOR (the only honest one) = model-free RECORD-DISTANCE (TV) minimized over the FULL
incoherent-AD family** — AD toward any Bloch axis (θ,φ), per-qubit-asymmetric, Markovian AND non-Markovian
(classical latent). Built `axis_ad_null_point` (general axis-AD) + `notion3_incoherent_null_search.py` (collective
grid + per-qubit scipy + non-Markovian scipy + global **differential_evolution** robustness pass). **RESULT
(adversarial, 4 independent search strategies agree the floor; DE did not beat the local optima):** the minimum
TV from the quantum σ− shared-mode relaxation record to ANY incoherent-AD null is **0.037 (gm=0.1) / 0.121
(gm=0.2) / 0.186 (gm=0.35)** — a LARGE irreducible residual, feasibly detectable at **N_detect = 1/TV² = 740 /
68 / 29 samples**. The non-Markovian latent (K∧memory incoherent null) gets closest yet still leaves TV≈0.19 at
the headline.

**VERDICT — SURVIVES_PROVISIONAL:** the shared-mode σ− emission's dual-axis record is **DISTINGUISHABLE from any
incoherent relaxation** (a coherence-free, population-only family cannot reproduce the coherent JC + mode-memory
joint (X,Z,time) record structure), robustly across the RWA-valid band. **SCOPE (honest, load-bearing):** this is
non-reproducibility w.r.t. the **tested incoherent-AD family**, NOT a proof against all classical/simulable
processes (NOT tested: coherent single-qubit unitary + AD, general Pauli/depolarizing channels). Because K itself
is forgeable, this is **anti-toy DISCRIMINABILITY from the incoherent matched null — the simulator's validity
criterion ([[feedback-simulator-is-goal-twin-is-next]]) — NOT a full model-free process-level
quantum-memory certification.** Epistemic: the "every-axis-K-forgeable" facts + the axis-AD CPTP/non-unitality
are (a)-exact; the min-TV floor + N_detect band are (b); the TV≥1e-3 feasibility threshold is (c). **arc LESSON:
two false-positives (K robust; K_X survives), BOTH caught by a from-scratch matched-null attack, never by "being
careful" — the null MUST be adversarially red-teamed before any survival claim.**

## 10. MIGRATION TO src + ATTRIBUTION (#2) + BROADENED NULLS (#1) — 2026-07-05

**MIGRATION (user "核心代码需迁移至 src 下").** The certified machinery is now the standalone package module
`src/error_coupling_simulator/quantum_bath/` (the designated P6 home — pseudomode-enlarged shared-bath GKSL):
`gksl` (Liouvillian) / `carrier` (dual-ancilla dual-axis instrument, `dual_point`) / `observables` (K/CMI/M_mem/TV)
/ `crow_joynt` (classical-field null + covariance) / `nulls` (incoherent-AD family + the broadened coherent null)
/ `ground_truth` (the anti-toy GTs). Verified by `tests/test_quantum_bath.py` (11 tests reproducing the certified
GTs THROUGH the package). Purely additive; CODE_MAP + code_status.json updated. The `outputs/` run scripts stay
frozen legacy; new experiments import the package.

**#2 ATTRIBUTION (`notion3_attribution_run.py`, GATE ATTRIBUTED).** Decomposes WHY the shared-mode record is
distinguishable, by ablating one physical feature at a time. **(C-sector):** the σ− (non-unital) sector is
IRREDUCIBLE (min-TV 0.25) while the σz (unital) sector is CLASSICALLY SIMULABLE — the crow_joynt field null
reproduces it (9e-3). **(A/B refined, scipy at the sweep endpoints):** the IRREDUCIBLE CORE is the COHERENCE of
the emission — even the SIMPLEST limits stay distinguishable from an incoherent AD (uncoupled r=0 → 0.037;
Markovian zero-memory γ=5 → 0.099, both feasible). The shared-bath COUPLING amplifies it ~5.5× (r=0→r=1); the
non-Markovian MEMORY amplifies it ~2.3× (γ=5→γ=0.05). **REGISTERED MISS on the pre-run prediction B: memory does
NOT CARRY the signature (the Markovian limit does NOT wash out) — it MODULATES a coherence-driven core.**

**#1 BROADEN THE NULL CLASS (`notion3_broaden_nulls_run.py` + `coherent_ad_null_point`, GATE
COHERENCE_DOMINANT_RESIDUAL_PROVISIONAL).** Tests whether a COHERENT classical process (per-qubit SU(2) + a ZZ
entangler + axis-AD + a classical latent, Markovian and non-Markovian; CPTP by construction, reduces to the
incoherent AD at U=I) reproduces the record. **Coherence is the DOMINANT driver (established):** adding it closes
**60 %** of the incoherent record-distance at r=1 (0.254 → 0.101) and **74 %** at r=0 (0.084 → 0.022) — confirming
#2. A feasibly-detectable RESIDUAL survives the best coherent null found (0.101 at r=1, N_det ≈ 97; 0.022 at r=0).
**PROVISIONAL — deliberately NOT claimed irreducible (this would be the 3rd survival claim on this arc):** the
residual MAY be the mode-mediated quantum correlation+memory a coherent CLASSICAL process cannot carry, OR a limit
of the FINITE coherent-null family + the non-convex 13–16-param scipy+DE search. **Established:** distinguishability
from INCOHERENT nulls (robust, §9), driven by the σ− sector's COHERENCE, amplified by coupling+memory. **Open:** a
richer coherent-classical family (per-round-varying unitaries, general correlations) + a heavier optimizer could
reduce the residual further. Still NOT a full model-free process-level quantum-memory certification.

## 11. THEORY-FIX literature closure (2026-07-05) — grounding + one correction

Ran the `theory-fix` literature-closure loop (RAG/KG + 精读) on the five conclusions. Papers: **maity 2601.01122**
(Jan 2026, "Non-Markovian and Thermodynamic Signatures in the Classicality Assessment via Kolmogorov
Consistency"), **budini 2301.02500** (PRA, DNI hallmark), **budini 2411.13471** (superclassical), **sakuldee
2204.11698** (multi-time classicality ≠ commutativity), **crow_joynt 1309.6383** (PRA, classical simulation).

- **maity 2601.01122 = direct grounding (independent blind spot: analytic single-qubit two-time vs our numeric
  multi-qubit three-time).** Its KCC-violation measure `viol=|Σ_{x1}P(x2,x1)−P(x2)|` (Eq. 2) IS our K, and it
  proves EXACTLY three headline points: (i) **viol ∝ the coherence amplitude** `|c(t2)|` (Eq. 15/A5, p.7) ⇒
  "coherence is the driver" [claim 3]; (ii) **viol=0 in the pointer basis, "manufactured" off-basis (sin θ)**
  (p.4) ⇒ "K forgeable / basis-dependent" [claim 1]; (iii) `viol=½ e^{−½M}|sin·sin| e^{+½N}` (Eq. 18) —
  **Markovian rates M SUPPRESS, non-Markovian backflow N ENHANCE** ⇒ "memory amplifies" [#2].
- **REGISTERED SHARPENING (trip-wire #2, rate-vs-observable): our K is the maity FIXED-basis object, NOT the
  budini POINTER-basis DNI witness.** Budini's DNI `I=Σ|P₃−P₂|` measures the intermediate round in the
  **state-diagonal (pointer) basis**, where **Markovian ⇒ I=0** and **unitary s-e coupling ⇒ violates I** (a
  CLEAN witness). We measure a **fixed Bell (X/Z-parity) basis** = off-pointer = the maity object ⇒
  coherence-proportional, basis-dependent, **forgeable by a Markovian AD**. The clean DNI witness EXISTS but needs
  **adaptive/active measurement** — unavailable on a PASSIVE fixed-stabilizer QEC record — which is precisely why
  we use the model-free **record-distance discriminability**, not a Kolmogorov certification. sakuldee grounds
  that multi-time K depends on the instrument (not just commutation) ⇒ a fixed non-commuting instrument gives K>0
  even for Markovian/simulable dynamics [claims 1, 4].
- **CORRECTION (softened):** "the IRREDUCIBLE CORE is coherence" (§10 #2) OVER-STATES — #1's own residual survives
  the coherent null, so coherence is the **DOMINANT driver**, not the sole irreducible core.
- **Verdicts:** claim 1 (K forgeable, basis-symmetric) **CORRECT + grounded** (maity/budini/sakuldee); claim 2
  (distinguishable from incoherent) **CORRECT with scope** (tested family; budini unitary-vs-non-unitary DNI
  separation grounds it); claim 3 (coherence irreducible core; ×5.5 coupling, ×2.3 memory) **PARTIAL** —
  coherence-dominant + memory-amplifies grounded by maity; "×5.5 coupling" is a `confirmed-literature-gap` (our
  multi-qubit finding, no single-qubit paper); "irreducible core" softened; claim 4 (field-null K≠0;
  channel-simulability ≠ record-K=0) **CORRECT + doubly-grounded** (crow_joynt + maity + sakuldee); claim 5
  (residual survives coherent nulls) **PROVISIONAL** (`confirmed-literature-gap`, correctly not over-claimed).
  **No conclusion falsified** at the theory-fix stage — but claim 3 IS falsified by Controls 1 & 2 (§12).

## 12. CONTROLS 1 & 2 (2026-07-05) — Claim 3 DECOMPOSED + FALSIFIED (memory + collective, NOT coherence)

Following the user's 15-paper Claim-3 literature sweep (`claim3_literature_synthesis_2026-07-05.md` + the 2026
tools), two controls decompose the TV residual. Both run on the migrated `quantum_bath` module.

**CONTROL 1 — the Luppi Φ_QRT/Φ_memory split across a γ-scan** (`notion3_control1_gamma_luppi_run.py`, GATE
`CLAIM3_MEMORY_DRIVEN`, sha a8c254fb). Added `dual_point_qrt` (Luppi 2605.06427 Eq.24: the SAME model with the
mode reset to vacuum each round = the reduced map Λ_S, no cross-round memory), so **ε_QRT = TV(exact, QRT) =
Φ_memory** — PARAMETER-FREE. RESULT (r=1): at the physical γ=0.15, **memory ε_QRT = 0.158 = 84 % of the total
residual**, and **VANISHES to 1.4e-8 at the Markovian γ=50 limit** (Luppi Φ_memory→0 exactly); the total residual
falls **13×** (0.188→0.0145). **NO standalone COHERENCE floor:** at r=0 (single qubit) the Markovian limit is
FULLY incoherent-reproducible (refined total 1e-8) ⇒ the "#1 r=0 coherence floor (0.022)" was finite-γ MEMORY,
confounded (as the synthesis §3 warned; the #2 ×5.5/×2.3 amplifications were flagged search-artifacts).

**CONTROL 2 — the Dicke collective-AD null** (`notion3_control2_collective_run.py`, GATE
`CLAIM3_COLLECTIVE_CONFIRMED`, sha 0996e45b). Added `collective_ad_null_point` (L=√Γ(σ⁻₀+σ⁻₁), incoherent,
memoryless; Fanchini 1301.3146: collective NM is super-additive, per-qubit AD cannot capture it). At r=1, γ=50
(memory~0 ⇒ the residual is PURE collective), the collective null **absorbs it to TV = 6e-5** where per-qubit
independent AD could not — confirming the Markovian-surviving r=1 residual IS the collective (shared-bath)
structure. At r=0 it does not help (no collective structure, single qubit).

**⇒ CLAIM 3 DECOMPOSED + CORRECTED. "Coherence is the dominant driver" is FALSIFIED (user's prior confirmed).
The TV residual = finite-γ multitime MEMORY (Luppi Φ_memory, DOMINANT ~84 % at the physical γ, vanishes
Markovian) + COLLECTIVENESS (Fanchini super-additive, the r=1 Markovian-surviving term) + COHERENCE
(subdominant/absent — no standalone floor).** Matches Milz 1907.05807 + Smirne CGD 1709.05267 (the non-Markovian
regime is memory/discord-driven, not coherence-driven). LESSON: the maity-grounded "viol ∝ coherence" was a
MAGNITUDE relation wrongly promoted to a DRIVER attribution; the Luppi parameter-free QRT-null decomposition is
the right tool. The collective term is reproduced by an INCOHERENT collective null, so it is classically-simulable-collective,
not genuinely-quantum. Whether the (dominant) finite-γ MEMORY is genuinely-quantum is answered by Control 3.

**CONTROL 3 — the Bäcker quantum-memory witness** (`notion3_control3_memory_witness_run.py` +
`quantum_bath/memory_witness.py`, GATE `CLAIM3_MEMORY_GENUINELY_QUANTUM`, sha e81cc6d9). Following the user's 2nd
Claim-3 sweep (memory quantum-vs-classical: Bäcker 2310.01205/2501.17660, Vieira 2402.16789, Yosifov 2507.21907,
Luppi 2512.18873). Implements **Bäcker PRL 132, 230401 Theorem 1**: `E#[χ(t1)] < E[χ(t2)] ⇒ quantum memory
REQUIRED` (no classical-memory realization), computed from single-time tomography of the reduced-qubit Choi state
(concurrence C + concurrence-of-assistance C#) — NO process tensor. Our JC σ⁻ emission into a VACUUM mode is
zero-T amplitude damping on the reduced qubit, where Bäcker: zero-T AD ⇒ quantum memory (concurrence revival).
**RESULT: at the physical γ=0.15 (UNDERDAMPED, g=0.35 > γ/2) the witness FIRES** (concurrence revival 0.044;
C#=0.859 < C=0.862 at t1=1.9, t2=4.0) ⇒ **the finite-γ MEMORY is GENUINELY QUANTUM (notion-3)** — no classical
realization exists. It does NOT fire in the OVERDAMPED/Markovian limit (γ ≥ 2g=0.7: no revival), crossover at the
predicted γ~2g. **RESOLVES the tension: Bäcker (zero-T AD ⇒ quantum) beats Yosifov (product-init ⇒ classical)** —
the reduced channel IS zero-T AD with a genuine revival. Scope: Bäcker Thm 1 is SUFFICIENT (fires ⇒ quantum,
rigorous), not necessary; the Markovian non-firing is "no memory" (ε_QRT~0), not merely inconclusive.

**⇒ FINAL (whole arc): K/K_X/K_Z are forgeable (not the witness); the model-free record-distance is
distinguishable; and its DOMINANT driver is a finite-γ multitime MEMORY that is GENUINELY QUANTUM (notion-3,
Bäcker-witnessed) — vanishing into the Markovian limit — plus a classically-simulable COLLECTIVE term, with
coherence subdominant/absent. THE genuine notion-3 signature of the shared-mode σ⁻ relaxation record is the
QUANTUM MEMORY, not the (forgeable) K nor coherence.** `test_quantum_bath.py`: 14 tests. Src additions (all in
`quantum_bath`): `dual_point_qrt`, `collective_ad_null_point`, `coherent_ad_null_point`, `memory_witness`.

**CONTROL 3b — the 2501.17660 witness + the FULL 2-QUBIT shared-bath extension** (`notion3_control3b_entropic_2qubit_run.py`,
GATE `CLAIM3_2QUBIT_MEMORY_GENUINELY_QUANTUM`, sha 2fb1a5c2). Two asks together. **THEORY-FIX CATCH:** the Bäcker
2501.17660 entropic form `S(χ₁) < S(χ₂)` as transcribed in this project's note is INCONSISTENT (note lines 61 vs
80) and, implemented, **fires trivially at every γ** — because the cumulative-Choi von-Neumann entropy INCREASES
monotonically under decoherence, so `S(χ₁)<S(χ₂)` is always true (contradicts the concurrence witness + the
Markovian=no-memory physics). Corrected to a **dimension-agnostic quantum-memory-REVIVAL witness = the NEGATIVITY
(a proper entanglement monotone for any d) of the reduced-channel Choi with a BACKFLOW (revival) signature** — the
direct d>2 analogue of the single-qubit concurrence revival, unambiguous. (Flag: verify the exact 2501.17660
criterion vs the paper if the entropic form becomes load-bearing; `von_neumann_entropy` retained as a diagnostic
only.) **RESULT: (A)** the negativity-revival witness fires on the SAME γ range as the concurrence witness
(γ<0.7 underdamped fire, γ≥0.7 silent) — an independent cross-check confirming Control 3. **(B)** the FULL 2-QUBIT
SHARED-BATH σ⁻ relaxation (r=1, both qubits → shared mode) **REQUIRES GENUINE QUANTUM MEMORY at the physical
γ=0.15** (negativity revival 1.37e-3), silent in the Markovian limit — so the notion-3 quantum-memory result is
NOT an artifact of the single-qubit reduction; it holds for the full correlated 2-qubit object real QEC measures.
The 2-qubit revival EXCEEDS the single-qubit (collective enhancement, Fanchini). Src additions: `negativity`,
`entropic_memory_witness_{single,two_qubit}` (negativity-revival), `von_neumann_entropy`; `test_quantum_bath.py`
15 tests.

**⚠ CONTROL 0b — FLAG 0 (the decisive negative control): the negativity-REVIVAL witness is NON-MARKOVIANITY, NOT
quantum memory ⇒ Control 3b's "genuinely quantum" (esp. the 2-qubit) is RETRACTED** (`notion3_control0b_classical_nm_negcontrol.py`,
GATE `CONTROL0B_REVIVAL_FORGEABLE_BACKER_SURVIVES`, sha 1590fd59; 2026-07-06). **User's Flag 0 (with a 3-source 2026
lit sweep):** a Choi entanglement/negativity REVIVAL (backflow) = RHP non-CP-divisibility = NON-MARKOVIANITY, and
classical non-Markovian noise (RTN dephasing) produces it too ⇒ "revival ⇒ quantum memory" is INVALID unless the
firing condition is Bäcker's `E♯[χ₁]<E[χ₂]` classical-bound violation (keeps the entanglement-of-assistance `♯`).
**DECISIVE NEGATIVE CONTROL (predict-before-measure, all 4 predictions hit):** run the ACTUAL src witnesses on
(A) classical RTN dephasing (manifestly classical, strong-coupling → backflow), (B) the quantum JC σ⁻ positive
control, (D) classical static-disorder AD (no backflow, silence sanity). **RESULT — split verdict:** (A) the
negativity/concurrence-REVIVAL witness (Control 3b) **FIRES** on classical RTN (neg-revival 0.061, conc 0.121) —
for dephasing C=|c(t)| revives while **C♯=1.0000 constant** — so it is an RHP NON-MARKOVIANITY witness (forgeable),
NOT quantum-memory. The genuine Bäcker `C♯(t₁)<C(t₂)` **stays SILENT** on it. (B) the JC Choi is EXACTLY rank-2 with
max(C♯−C)=2.5e-8 (genuinely zero-T AD; Bäcker Thm 1 applies to the single qubit) and `C♯<C` FIRES (0.8590<0.8622).
(D) both silent. **⇒ (3b FALSIFIED) the 2-qubit "genuinely quantum" rested ONLY on the bare revival (dropped `♯`;
C♯=C unproven for d>2; collective Dicke ⊄ Bäcker's single-qubit AD) — RETRACTED, no surviving witness. (3 SURVIVES)
single-qubit "genuine quantum memory" rests ONLY on Control 3 (`C♯<C`, sufficient-not-necessary), pending the
margin-3e-3 convergence + a C♯-definition verify.** LITERATURE (2026): **2601.18822** "backflow witnesses MEMORY, not
quantumness per se"; **1608.05970** (NM necessary-not-sufficient); **2510.19522** (Bäcker's own applied witness uses
E♯<E, not revival). src `memory_witness.py` docstrings/banner/`__init__` corrected to label the revival witnesses as
non-Markovianity/backflow diagnostics; `test_negativity_backflow_witness_is_nonmarkovianity_single_and_two_qubit`
renamed + de-claimed. **Flag #1 (does the quantum memory EXPRESS on the PASSIVE record, or is it only the ACTIVE
single-time-tomography channel object?) is now the crux.** Corrected-path literature (acquiring): 2601.18822 /
2510.19522 / Giarmatzi 1811.03722 (process-tensor, may close Flag 0+#1 together) / Taranto 2307.11905 (classical
multi-time memory = notion-2). **NEXT:** build the E♯<E form (negativity-of-assistance for d>2) and/or a
process-tensor quantum-memory witness; the passive-record expression test remains the final decider of whether
SURVIVES has a record-level quantum component.
