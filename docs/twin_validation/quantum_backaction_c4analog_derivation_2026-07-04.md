# Quantum-back-action C4-analog — derivation + predictions (predict-before-measure, 2026-07-04)

**Status: DERIVATION written BEFORE the run.** Committed script:
`outputs/twin_validation/quantum_backaction_c4analog.py`. The DECISIVE evidence call (user 2026-07-04): does
genuinely-quantum measurement back-action / non-unitality survive the PASSIVE stabilizer syndrome record, or
is it twirled like the classical coherence revival was in the CP-div check's C4? This decides whether the
ancilla fixture carries a **quantum headline** (evidence-backed Option 3) or the **notion-2 classical-memory
control** (passive-record legitimacy ceiling; quantum → active/twin domain).

Anchors (read this session): milz 1907.05807 (Kolmogorov-consistency = classicality; measurement
non-invasiveness); noise_adapted 2411.09637 (non-unitality of the composite QEC channel); White-Pollock
2106.11722 (the passive record); the CP-div check C4 (classical revival twirled).

## The observable (grounded, milz) — Kolmogorov consistency of the syndrome record

Sequential per-round syndrome measurements `s_1,…,s_R` (fixed measurement basis = the stabilizer). milz Eq 9:
a process is **classical** iff marginalizing an intermediate outcome reproduces the lower-order distribution —
i.e. the measurement is **non-invasive**. The **a-exact Kolmogorov-violation statistic** (3-round):

$$ K \;=\; \sum_{s_1,s_3} \Big| \sum_{s_2} P_{\text{measure-all}}(s_1,s_2,s_3) \;-\; P_{\text{skip-2}}(s_1,s_3) \Big|, $$

where `P_measure-all` measures rounds 1,2,3 and `P_skip-2` measures 1,3 but **evolves through round 2 without
measuring**. `K=0` ⇔ non-invasive ⇔ **classical / reproducible by a classical stochastic process** (the record
carries at most notion-2 classical memory). `K>0` ⇔ **measurement-invasive** ⇔ genuinely quantum
(Leggett-Garg / discord, a signature NO classical process can forge). Second signature: **non-unitality** of
the per-round record channel (noise_adapted §V.A) — a classical dephasing record channel is unital.

## The models (minimal, exactly solvable — system qubit S ⊗ small bath)

Per round: unitary `U=e^{−iHt}` on S(⊗bath), then projective measurement of the syndrome observable `M_S` on S
(collapse); the bath PERSISTS across rounds (memory). Three models:
- **QC1 (control) — classical dephasing:** S under a classical dephasing channel (or `H=½β(t)σ_z^S` with a
  classical latent), syndrome `M_S=σ_z^S`. The coupling **commutes** with `M_S`.
- **QC2 (positive control, Leggett-Garg teeth) — coherent drive:** `H=(Ω/2)σ_x^S`, syndrome `M_S=σ_z^S`. The
  drive is **noncommuting** with `M_S` — the textbook Leggett-Garg / invasive-measurement setup.
- **QC3 (the decisive one) — quantum bath:** S ⊗ bath qubit B with a coupling that is **noncommuting** with
  the syndrome (exchange `H=g(σ_x^S σ_x^B)` / amplitude-damping-like Jaynes-Cummings — the noise_adapted /
  pseudomode regime, cf. the leakage axis ADR 0010), syndrome `M_S=σ_z^S`. Also a **commuting** quantum
  dephasing bath `H=g(σ_z^S σ_z^B)` as the contrast.

## PREDICTIONS (predict-before-measure)

- **QC1 (a-grounded):** classical dephasing → **K=0** (non-invasive; the syndrome commutes with the coupling).
  Record is a classical process — re-confirms C4 (classical → twirled). Channel unital.
- **QC2 (a-grounded, teeth):** coherent σx drive, σz measure → **K>0** (Leggett-Garg violation). Proves the
  statistic HAS teeth — quantum back-action IS passive-record-visible in principle. NON-vacuity control.
- **QC3 (the decisive call) — the answer hinges on [coupling, syndrome] commutation:**
  - **Commuting quantum dephasing bath** (`σ_z^S σ_z^B`, σz measure) → **K=0 (TWIRLED)** — even a genuinely
    quantum bath is twirled from the Z-syndrome record because the measurement commutes with the coupling
    (the syndrome is phase-blind; ties [[project-nonmarkovian-wedge-must-be-coherence]]).
  - **Noncommuting quantum bath** (exchange/AD `σ_x`-type, σz measure) → **K>0 (SURVIVES)** — the back-action
    is invasive; the quantum signature reaches the passive syndrome record.
- **⇒ THE PREDICTED FINDING:** the passive-syndrome quantum-legitimacy ceiling is **error-type-dependent**:
  **dephasing** (σz — our classical 1/f AND a quantum dephasing bath) is TWIRLED ⇒ notion-2 classical-memory
  ceiling; **relaxation / exchange / LEAKAGE** (noncommuting, ADR 0010 axis) can SURVIVE ⇒ a genuine quantum
  headline, but sited on the leakage/relaxation axis, NOT the dephasing axis. Falsifier: if the commuting
  dephasing bath gives K>0, the twirling picture is wrong; if the noncommuting bath gives K=0, the passive
  record cannot carry ANY quantum signature (a stronger no-go — everything is notion-2).

## Epistemic classes

- **(a) exact:** K from exact-DM 3-round measure-all vs skip-2 distributions; QC1 (K=0), QC2 (K>0), the
  commutation dependence.
- **(b) band/finding:** QC3 magnitudes; the error-type-dependence headline.
- **(c) declared:** minimal 1-system + 1-2-bath-qubit fixture; single-qubit syndrome `M_S=σ_z^S` as the
  stabilizer proxy (the multi-qubit stabilizer-basis twirl is a separate, stronger twirl — declared, and if
  even this minimal noncommuting case is twirled the multi-qubit case is too).

## RESULTS (post-run 2026-07-04; predictions above INTACT)

Committed: `outputs/twin_validation/quantum_backaction_c4analog.py` (`python-exit=0`, artifact
`quantum_backaction_c4analog.json`,
`content_hash=52fc36e52beb8a5be7a96baf61d68f06afb9d540bdcdb34755799a86aa53dbb2`,
`GATE_RESULT ... ERROR_TYPE_DEPENDENT`). `angle=π/3`, `p_deph=0.3`.

| model | commutes? | K | prediction | verdict |
|---|---|---|---|---|
| QC1 classical dephasing | yes | **0** | K=0 twirled | **CONFIRMED** |
| QC2 coherent drive (LG) | no | **0.75** | K>0 teeth | **CONFIRMED (statistic has teeth)** |
| QC3z quantum dephasing bath | yes | **0** | K=0 TWIRLED | **CONFIRMED** |
| QC3x quantum exchange bath | no | **0.75** | K>0 SURVIVES | **CONFIRMED** |
| QC3ad quantum amp-damp bath | no | **0.375** | K>0 SURVIVES | **CONFIRMED (weaker but >0)** |

**Grounded conclusion:** the passive-syndrome quantum-legitimacy ceiling is **ERROR-TYPE-DEPENDENT**, hinging
on `[coupling, syndrome]` commutation. **Dephasing** (our 1/f AND a quantum dephasing bath) is **twirled**
(K=0) ⇒ the passive-record ceiling on the dephasing axis is **notion-2 classical memory**; the quantum
dephasing contribution is active/coherence-probe (twin) domain, out of passive-simulator scope.
**Noncommuting relaxation / exchange / amplitude-damping / LEAKAGE** (ADR 0010) **survives** (K>0) ⇒ a genuine
quantum headline IS passive-record-legitimate, on the **leakage/relaxation axis**. Maps to the carriers: the
dense ancilla carrier (dephasing/notion-2) vs the MCWF/MPS qutrit-leakage carrier (quantum headline).

## RESULTS v2 — BOTH measurement bases (user question 2026-07-04: "what about the X axis?")

**The v1 flaw the user caught:** v1 measured ONLY `M_S=σ_z^S`. But a σz (dephasing) error is detected by the
**X-stabilizer** (`σ_x` measurement), and **σz anticommutes with σx**. So the twirling condition is NOT the
error type — it is `[coupling, measurement-basis]` commutation × **coherence**. v2 tests each coupling in BOTH
`M=σ_z` (Z-stabilizer) and `M=σ_x` (X-stabilizer).

**Corrected PREDICTIONS (predict-before-measure, v2):**
| coupling | M=σ_z (Z-stab) | M=σ_x (X-stab) | why |
|---|---|---|---|
| QC1 classical **incoherent** dephasing | K=0 | **K=0** | incoherent channel ⇒ twirled in EVERY basis (truly classical → notion-2) |
| QC2 coherent σ_x drive | K>0 | K=0 | survives in the noncommuting basis only |
| QC3z quantum σ_z⊗σ_z dephasing bath | K=0 | **K>0** | **σz coupling NONCOMMUTES with σx ⇒ SURVIVES via the X-stabilizer** (answers the user) |
| QC3x quantum σ_x⊗σ_x exchange | K>0 | K=0 | noncommutes with σz, commutes with σx |
| QC3ad quantum amp-damp / JC | K>0 | K>0 | σ±σ∓ noncommutes with both |

**Corrected headline (predicted):** the twirling condition is **INCOHERENCE, not error type.** CLASSICAL /
incoherent noise (our stochastic 1/f) is twirled in ALL stabilizer bases ⇒ notion-2 ceiling. A QUANTUM /
coherent bath of ANY type (dephasing σz OR bit σx OR leakage) **survives** via its complementary
(noncommuting) stabilizer — and real QEC measures BOTH X and Z stabilizers. ⇒ the quantum headline is
passive-record-legitimate for a quantum DEPHASING bath too (via the X-stabilizer), NOT only leakage — v1's
"quantum dephasing twirled" was a wrong-basis artifact. Falsifier: if QC3z gives K=0 in the X-basis too, the
commutation-coherence rule is wrong.

**v2 RESULTS (post-run 2026-07-04; predictions above INTACT).** Committed:
`outputs/twin_validation/quantum_backaction_c4analog.py` (`python-exit=0`,
`content_hash=b06fc97ba0d3e38c6968c0ded7aa0f478857fa77e164ef51b23a1c7e6cced6de`,
`GATE_RESULT ... INCOHERENCE_IS_TWIRLING`).

| model | K(Z-stab) | K(X-stab) | prediction | verdict |
|---|---|---|---|---|
| QC1 classical incoherent dephasing | 0 | ~0 | 0/0 | **CONFIRMED (twirled all bases → notion-2)** |
| QC2 coherent σx drive | 0.75 | 0 | >0/0 | **CONFIRMED (teeth)** |
| QC3z quantum σz dephasing bath | 0 | **0.75** | 0/>0 | **CONFIRMED — survives via X-stab** |
| QC3x quantum σx exchange bath | 0.75 | 0 | >0/0 | **CONFIRMED** |
| QC3ad quantum amp-damp | 0.375 | 0.75 | >0/>0 | **CONFIRMED** |

**CORRECTED headline (supersedes v1):** the twirling condition is **INCOHERENCE, not error type.**
CLASSICAL/incoherent noise (our 1/f) is twirled in ALL stabilizer bases (K=0) → **notion-2 ceiling**. A
QUANTUM/coherent bath **survives via its complementary (noncommuting) stabilizer** — the quantum DEPHASING
bath is twirled by the Z-stab but SURVIVES via the X-stab. Real QEC measures BOTH X and Z stabilizers ⇒ a
quantum bath of ANY type (dephasing / bit / leakage) is passive-record-legitimate, **on the same dense
ancilla carrier** (no separate leakage carrier needed). v1's "quantum dephasing twirled → leakage-only" was a
wrong-basis artifact (the user's catch). Declared bound (c): the multi-qubit ancilla-mediated stabilizer
measurement is a stronger twirl than the single-qubit σx toy — whether survival holds there is the deepen check.

## RESULTS v1 (Z-basis only — SUPERSEDED by v2; kept for the record)

**⚠ Honest caveat (secondary metric vacuous):** the `non_unitality` column came out ~1e-16 for ALL models —
because it was applied to `I/2`, which is a fixed point of the measure-and-forget channel (`ρ→I/2` is
invariant under unitary + Z-dephasing). So that metric is **uninformative as implemented** (not
wrong-concluding — the load-bearing `K` statistic is decisive; QC2's `K=0.75` proves the check has teeth). A
faithful non-unitality probe would use a non-maximally-mixed input / the bath-conditional channel — deferred,
not needed for this verdict.
