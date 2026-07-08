# STATUS + DECISION — non-Markovian passive-record legitimacy (consolidation, 2026-07-04)

**Consolidation of the 2026-07-04 session.** Everything below is docs/outputs + committed CPU checks;
**`src/` is untouched.** Purpose: tie the decisive chain + the carrier map + the two contract reviews + the
fair-test into one roadmap decision. Each committed check carries `python-exit=0` + a `content_hash`.

## 1. The decisive chain (all committed, predict-before-measure)

| step | committed evidence | finding |
|---|---|---|
| Track-1 Step-1 `N_detect` | `step1_shared_vs_off_lag2_Ndetect` (`5c3c92…`) | shared-vs-off absolute lag≥2 is VISIBLE at feasible N (pooled 5.85e4); retracted 1e10–1e15 sub-floor REFUTED (error A: exchangeable-null subtraction was the killer). Common-mode-dominated. |
| theory-first grounding | `theory_first_grounding_nonmarkovian_legitimacy` (11 papers read) | THREE distinct notions: CP-div breaking (RHP/BLP) / classical multi-time memory (Kolmogorov) / non-classicality (discord). Right observable = multi-time / differentiable syndrome NLL, NEVER 2-point (Kam §IV.C). Slow tail = drift (cross-shot, Bhardwaj). Site Class-1/2 (Kam). |
| CP-div check | `cpdiv_passive_record_check` (`5bc63d…`) | **our 1/f source is CP-DIVISIBLE (RHP=BLP=0)** — its signal is notion-2 (classical memory), NOT CP-div breaking (needs strong non-Gaussian RTN + is twirled from the passive record). |
| quantum C4-analog v2 (both bases) | `quantum_backaction_c4analog` (`b06fc97…`) | twirling condition = **INCOHERENCE, not error type**. Classical/incoherent → notion-2 (twirled all bases). Quantum/coherent bath → survives via its complementary stabilizer (dephasing via X-stab); QEC measures both X,Z. |
| deepen (K × M_mem) | `quantum_backaction_deepen` (`d6c2df…`) | K certifies COHERENCE not a non-Mkv bath (a coherent Markovian control forges K>0). Headline needs K>0 ∧ M_mem>0. **FALLBACK** — but on an inadequate toy (M_mem=0 by construction; θ=0.01 weak). |
| **fair-test (pseudomode)** | `quantum_backaction_fairtest` (`6021c1…`) | with a GENUINE memory-bearing pseudomode bath at saturation: **headline STANDS but CORNER-ONLY** (feasible g∈[0.2,0.7]/gτ 0.4–1.4, N_det~4e3–5e4; sub-feasible weak coupling). Converges with G0-quantum GO-CORNER-ONLY. Fallback WAS a toy artifact. |

**Net:** the classical 1/f source's passive-record legitimacy signal is **notion-2 (classical multi-time
memory)** — broadly achievable, measured multi-time / differentiable syndrome NLL, sited Class-1/2. The
**quantum-dephasing headline is a REAL but CORNER-CONFINED result** (near-resonant strong coupling), a bigger
d3/multi-qubit build to demonstrate; the corner-confinement is a genuine limit (converges with G0-quantum).

## 2. Carrier architecture (3-agent read-only map)

- **Dense Axis-1 carrier (4q/5q fixtures) ALREADY ancilla-resolved** — explicit ancilla, projective
  `measure_qubit_enumerate`, real reset, ancilla SPAM (`Axis1ReadoutResetInstrumentSpec`) at trajectory-mean.
  Faithful Class-1 = per-round SPAM seam (NOT a rebuild) + ancilla-aware exact-DM oracle.
- **Readout SPAM is a CLASSICAL post-measurement record flip** (`_branch_asymmetric_readout_flip`), reset is a
  quantum channel — a load-bearing distinction (info-disturbance, R≥2).
- **MCWF/MPS carrier = implicit projection, NO ancilla** → Class-1 infeasible; but it IS the leakage/qutrit
  carrier (a separate, noncommuting axis).
- **Scale (corrected, complex128):** at QUBIT level (leakage deferred) the ancilla-resolved exact-DM is
  `2^5=32` = trivially exact — the `3^n` OOM only bites at the DEFERRED qutrit/full-d3 world.

## 3. The faithfulness contract + two un-led reviews (both GO_WITH_CHANGES)

Contract: `ancilla_resolved_carrier_faithfulness_contract_2026-07-04.md`. Required changes before code
(merged from both reviewers):
1. **Scale bound** — rewrite for qubit-level (`2^5` trivially exact; `3^n` complex128 = deferred qutrit world);
   the notion-2 gate's exact-DM legitimacy IS certifiable at the minimal fixture. Resolve qubit-vs-qutrit.
2. **Oracle circularity** — forbid `AncillaAwareDMOracleAnchor` importing the emitter's SPAM/measurement
   primitives; re-derive projective-measure, quantum-reset, and the **classical-record-flip readout** model
   from scratch.
3. **Regression anchor** — byte-identity REQUIRED (cube + `content_hash`); delete the "OR bounded" escape hatch.
4. **T5 tautology → info-disturbance row** (classical-record-flip vs quantum-pre-flip, R≥2).
5. **T1 → coherent x0/X-check chain** (Z-diagonal fixture makes projective≡marginal); **T8 → closed-form
   2-qubit-depol algebra** (not the sibling oracle); **split T4** (CPTP quantum + column-stochastic classical).
6. **Add apply-every-gate row** (coherent CZ + DD echo survive Class-2 wiring).
7. **Stim dead leg** — `emit_clifford_slice` raises NotImplementedError; wire it or drop the leg.
8. **Restate scope** — "per-round instrument seam in the SEALED emitter (mirroring `params_for_substep`)",
   not "only plumbing"; pin protocol-surface ownership.
9. **DROP the dual-purpose claim** — the fair-test refuted the cheap-source-swap framing (quantum headline is
   corner-confined + a bigger build). notion-2 stands on its OWN merit.

## 4. Roadmap options (the decision)

- **(R1) notion-2 build** — revise the contract (§3) + build the classical multi-time memory gate on the
  dense ancilla carrier (per-round SPAM seam + ancilla-aware oracle + best-Markov-k / differentiable-NLL
  observable, Class-1/2). The BROADLY-achievable passive-record legitimacy result for the classical source.
  H6-gated; disjoint A/B/C.
- **(R2) quantum-bath line** — the corner-confined quantum headline: build a genuine memory-bearing bath
  (pseudomode/GKSL) into the carrier + multi-qubit stabilizer, demonstrate the corner at d3. Bigger; a real
  but corner-limited result (converges with G0-quantum). The quantum-bath M1/M2 line already exists
  ([[project-quantum-bath-m1-m2]]).
- **(R3) original Track-1 Step-2** — the GPU empirical confirm of Step-1 on the real `emit()` (shared-vs-off,
  the corrected multi-time observable), which the whole detour deferred.

## 5. Open items (carried)

- The notion-2 gate's OWN internals (best-Markov-k forgeability null + 1/f power-law E(k)/NLL residual +
  independent C_z GT) — a separate contract (the earlier forgeability red-team's required form).
- The deepen/fair-test are single-qubit toys; the multi-qubit-stabilizer + real-carrier demonstration is the
  deferred bigger build for BOTH notion-2 (Class-1/2) and the quantum corner.
