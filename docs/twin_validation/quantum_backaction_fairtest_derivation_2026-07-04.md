# Quantum-back-action FAIR-TEST — derivation + predictions (predict-before-measure, 2026-07-04)

**Status: DERIVATION written BEFORE the run.** Committed script:
`outputs/twin_validation/quantum_backaction_fairtest.py`. The deepen (v1) FELL BACK to notion-2, but on an
INADEQUATE toy (user, 2026-07-04): (hole 1) the single-bath-qubit had M_mem=0 by construction — its `σz`
coupling CONSERVES the bath `σz` (a static classical offset, no cross-round dynamics), so it can never be a
memory-bearing quantum bath; (hole 2) `θ=0.01` is WEAK coupling and the effect-size cap is `θ`-dependent
(`N∝θ⁻²·²`... `N∝1/K²`, `K∝θ²` ⇒ `N∝θ⁻⁴`; feasible needs `θ` only ~7.5× larger). This fair-test fills BOTH
holes with a genuine memory-bearing **pseudomode bath** at **near-resonant / saturated** coupling (the
G0-quantum corner), reusing the pilot model [2506.10308]. Anchors: pilot
`outputs/coupled_pseudomode_pilot_v1_n2.py` + [[project-coupled-pseudomode-pilot-v1]]; G0-quantum M1 bracket
(Gao TLS `g̃/2π≈3 MHz`, `κ≈2.5 µs⁻¹`, CGF saturation at `gτ≈0.63`) [[project-quantum-bath-m1-m2]]; milz K.

## The model (memory-bearing pseudomode — fixes hole 1)

1 system qubit S (the data qubit) + 1 truncated-Fock pseudomode (`nmax≈4`), pure-dephasing coupling
(pilot Eq.2-3): `H = ζ b†b + σ_z^S · g(b+b†)`, collapse `c = √(2γ) b` (GKSL, exact CPTP). The mode
**PERSISTS across rounds** (never measured/reset); the system is measured each round in the **X-stabilizer
basis** (`M_S=σ_x`, the noncommuting-with-`σz` basis that detects dephasing errors — C4-analog v2). Because
the mode's free term `ζ b†b` does NOT commute with the coupling, the mode state EVOLVES between rounds ⇒
**genuine cross-round memory** (unlike the single-bath-qubit toy whose `σz` was conserved).

Round evolution: propagate `ρ` under `e^{Lτ}` (L = the GKSL Liouvillian) for round time `τ`, then projectively
measure `σ_x^S` (keep the mode). `K` and `M_mem` as in the deepen. Near-resonant/saturated regime: pilot
underdamped (`ζ=1, γ=0.15, g=0.5`) + a round time `τ` giving substantial per-round coupling (`gτ ~ O(1)`,
the CGF saturation corner) — NOT the weak `θ=0.01`.

## PREDICTIONS (predict-before-measure)

- **FT1 (a-exact — hole 1 filled):** the pseudomode gives **M_mem > 0** (the dynamic mode carries cross-round
  memory), AND **K(X) > 0** (σz-coupling noncommutes with the X measurement ⇒ invasive/coherent) ⇒ the
  **headline conjunction `K>0 ∧ M_mem>0` is realized** — the thing the single-bath-qubit toy could never show.
  Falsifier: if even the pseudomode gives M_mem=0, then a dephasing quantum bath genuinely leaves no record
  memory (a strong physics no-go, not a toy artifact) ⇒ notion-2 definitively.
- **FT2 (b — hole 2 filled):** at the near-resonant/saturated coupling (`gτ~O(1)`), K is near-max ⇒
  **N_detect(K) ≤ 1e6 (feasible)** — vs the weak-toy `5.6e7`. Report K, M_mem, N_detect vs coupling; find the
  coupling where it crosses feasibility.
- **FT-VERDICT:**
  - **FT1 ∧ FT2 pass** ⇒ the quantum-dephasing headline **STANDS in the near-resonant corner** (coherence +
    memory + feasible, judged with a REAL memory bath) — converges with G0-quantum GO-CORNER-ONLY ⇒ the
    **quantum-bath line is a real (corner-confined) result worth the roadmap**; notion-2 = control.
  - **either fails even with the real memory bath at saturation** ⇒ the quantum-dephasing headline is
    **definitively DEFERRED (physics, not toy inadequacy)** ⇒ **notion-2 is the answer, and the fallback now
    truly stands.**
- **Honest expectation (user):** likely **corner-only** — the headline feasible ONLY in the fragile
  near-resonant corner (consistent with G0-quantum's ratio-1.32 corner), sub-feasible at typical coupling.
  Either way it is a FAIR verdict (real memory bath), the load-bearing input to the roadmap decision.

## RESULTS (post-run 2026-07-04; predictions above INTACT)

Committed: `outputs/twin_validation/quantum_backaction_fairtest.py` (`python-exit=0`,
`content_hash=6021c1d138103862053ae78d5fab3dd7a0c302f23c0ffd437540ea0646e53b2a`,
`GATE_RESULT ... HEADLINE_STANDS_CORNER`). Fock-truncation CONVERGED (nmax→12: K=0.0591, M_mem=0.0283 stable
to 1e-6 by nmax=16 — the first run at nmax=5 was NOT converged and untrustworthy; caught + fixed).

| # | prediction | result | verdict |
|---|---|---|---|
| FT1 hole-1 (memory) | pseudomode gives M_mem>0 ∧ K>0 | g=0.5: **K=0.059, M_mem=0.028** (both >0) | **CONFIRMED — headline conjunction REAL** |
| FT2 hole-2 (effect-size) | feasible at saturation | headline-feasible (BOTH K,M_mem ≤1e6) for **g∈[0.2,0.7]** (gτ 0.4–1.4), peak g=0.35 N_det≈4.4e3 | **CONFIRMED — feasible in the corner** |
| corner vs broad | (honest expectation: corner) | sub-feasible at weak g≤0.1 (M_mem N_det 1e7–3e9); **CORNER-ONLY** | **corner-confined** |

**Grounded verdict: the quantum-dephasing headline STANDS but is CORNER-ONLY** (near-resonant/strong-coupling
gτ≈0.4–1.4), judged FAIRLY with a genuine memory-bearing pseudomode bath. **⇒ the deepen's fallback was a TOY
ARTIFACT** (my single-bath-qubit conserved its σz → M_mem=0; θ=0.01 was weak). Converges with G0-quantum
GO-CORNER-ONLY. **Honest caveat (adversarial self-check caught 2 bugs):** (i) the first run was Fock-truncation
UNconverged (fixed); (ii) I initially sized N_detect from K only — the binding constraint is N_detect(M_mem)
(memory is the load-bearing part), which flips "broadly" → "corner-only". Remaining declared limits: 1
system qubit + single-qubit σx stabilizer proxy (the deepen DM2 joint-parity twirl survived, carried);
pure-dephasing; rough single-statistic N sizing. ⇒ **roadmap input: notion-2 (classical memory) = broadly
achievable; quantum-dephasing headline = REAL but corner-confined (a bigger d3/multi-qubit build to
demonstrate; the corner-confinement is a genuine limitation, converging with G0-quantum).**

## Epistemic classes + declared

- **(a) exact:** the GKSL Liouvillian (hand-built, cross-check vs the pilot's construction if reused); K and
  M_mem from the exact 3-round distributions; FT1 M_mem>0 / K>0.
- **(b) band:** FT2 K, N_detect, the feasibility-crossing coupling.
- **(c) declared:** 1 system qubit (single-qubit `σ_x` stabilizer proxy — the multi-qubit joint-parity twirl
  survived in the deepen DM2, carried); `nmax` Fock truncation (convergence-checked); pure-dephasing coupling
  (`[H_S,σz]=0`, the exactly-benign case — the amplitude-damping/leakage arm is a separate, stronger axis);
  CPU exact-DM (tiny 8-dim feasibility check, same class as the CP-div/C4-analog checks — NOT the simulator's
  production GPU compute).
