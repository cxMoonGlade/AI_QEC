# notion-3 (quantum non-classicality on the passive record) — Pre-Registration (theory-first)

> **SUPERSEDED INTERPRETATION, 2026-07-13.** This prereg remains a historical experiment record,
> but its identification of `K=P_all-P_skip` with quantum-bath/quantum-memory certification is
> retracted. `K` compares two protocols and tests Kolmogorov consistency/non-invasiveness for that
> family; Markovian coherence-generating dynamics can also make it nonzero. See
> [`notion123_taxonomy_literature_closure_2026-07-13.md`](notion123_taxonomy_literature_closure_2026-07-13.md).

Status: PRE-REGISTRATION, 2026-07-05. Predictions written BEFORE the run; a miss is a finding, not a re-fit.

**Purpose.** The classical notion-2 legitimacy run PASSED (`corrected_multitime_observable_prereg.md` §8): the
passive record carries classical multi-time memory distinguishable from a Markov null. But that memory is
**Kolmogorov-CONSISTENT** — a classical HMM reproduces it (CCC/CFF; Srivastava 2510.13051). The **FINAL target**
([[project-coupling-nonmarkovian-is-the-contribution]]: "quantum GKSL bath = FINAL target") is **notion-3 =
non-classicality / discord = Kolmogorov VIOLATION**: a quantum bath leaves a record signature **no classical
process can reproduce**. This run puts classical and quantum on ONE footing to demonstrate the separation.

Scope: SIMULATOR record-char legitimacy instrument (does the quantum bath's non-classicality SURVIVE onto the
passive record, distinguishable from a classical process). NOT twin recovery. Reuses the FAIR-TEST anchor.

## 0. Grounding ledger (all read; reuse, don't rebuild)

| claim | anchor | reuse |
|---|---|---|
| historical `K` = Kolmogorov/non-invasiveness test for a measure/skip protocol family; not a process-level quantum-memory classifier | milz 1907.05807 Eq.9; Smirne *et al.* QST 4, 01LT01 | `quantum_backaction_fairtest.py::K_stat` (measure-all-marginalize vs skip) |
| classical incoherent dephasing ⇒ K=0 in BOTH bases (Kolmogorov-consistent) | C4-analog v2 (committed, a-exact) | re-verify as the classical arm |
| quantum σz-coupled pseudomode bath ⇒ K(X)>0 (survives via the noncommuting X-stabilizer), corner-confined | FAIR-TEST (HEADLINE_STANDS_CORNER) | `build_L`/`round_superop`/`distributions`/`K_stat`/`M_mem_stat`/`run_point` verbatim |
| memory beyond Markov-1 = the corrected absolute order test | `corrected_multitime_observable_prereg.md` §8; milz | exact CMI (KL) reconciled with the classical run's CMI/G² |
| classical multi-time memory is Kolmogorov-consistent (K=0) but real (CMI>0) | Srivastava 2510.13051 (CCC monotone-ASF) | the contrast |

## 1. Mechanism (anchored; reuse FAIR-TEST)

Exact-DM, 1 system qubit + 1 truncated pseudomode (Fock nmax, convergence-checked), system measured each round
in the **X-stabilizer basis** (the basis noncommuting with σz that detects dephasing). Two arms, SAME framework:
- **QUANTUM arm** (FAIR-TEST verbatim): coherent pseudomode bath `H = ζ b†b + σz·g(b+b†)`, collapse `√(2γ)b`;
  mode PERSISTS across rounds (dynamic `ζb†b` noncommutes with the coupling ⇒ cross-round memory). Pilot
  `ζ=1, γ=0.15`, `τ=2.0` (gτ~O(1) corner), swept `g`.
- **CLASSICAL arm** (NEW, the contrast): incoherent σz-dephasing with a TIME-CORRELATED classical rate from
  `OneOverFDriftSource` — `(1−q_t)ρ + q_t σz ρ σz`, `q_t` tracking the classical latent (memory in the latent,
  no coherence carry). Same X-measurement, same 3-round distribution machinery.

## 2. Observable (the RIGHT one — reconciled + the notion-3 discriminator)

Per arm, on the exact multi-round outcome distribution:
- **K (protocol-family Kolmogorov/non-invasiveness statistic, Milz Eq.9):** `K = Σ_{s1,s3} |Σ_{s2}
  P(s1,s2,s3) − P_skip(s1,s3)|` — measure-all-then-marginalize versus skip-measuring the intermediate.
  It is not a matched-marginal subtraction, but neither is it by itself a quantum-memory/origin witness.
- **Memory (beyond-Markov-1):** the exact CMI `I(s1;s3|s2)` (KL) — reconciled with the classical run's
  CMI/G² — AND `M_mem` (L1 to the Markov-1 factorization, FAIR-TEST continuity). Absolute order statistics.
- **N_detect** for each (`(3/x)²`, single-statistic order-of-magnitude, as FAIR-TEST); binding = max over the
  two required statistics.

## 3. Predicted behavior (falsifiable) + epistemic classes

- **Historical prediction, interpretation retracted:** CLASSICAL arm ⇒ **K=0** in the declared incoherent
  model; QUANTUM arm ⇒ **K>0**. This separates those two registered arms only. It does not establish that no
  classical/invasive or Markovian coherence-generating model can reproduce the statistic.
- **(a) exact — both have memory:** BOTH arms ⇒ **CMI>0 / M_mem>0** (classical latent memory AND quantum mode
  memory). So memory alone does NOT distinguish them — only K does (this is the whole point of notion-3).
- **(b) band — corner-confinement (FAIR-TEST):** the QUANTUM K (and the binding N_detect over K, M_mem) is
  feasible (≤1e6) ONLY in the near-resonant corner g∈[0.2,0.7] (gτ 0.4–1.4), sub-feasible at weak g≤0.1.
  Predict this reproduces. **Falsifier:** if the quantum K is broadly feasible or nowhere feasible, the
  corner-confinement verdict changes (a finding).
- **(c) gate:** Fock convergence (nmax to 1e-4); K>1e-6 ⇒ nonzero; classical K < 1e-8 (numerically zero).

## 4. Independent ground truth (non-circular)

- The GKSL Liouvillian cross-checked vs the pilot construction (`coupled_pseudomode_pilot_v1`); P_all
  normalized to 1e-8; Fock-convergence (nmax 4→20) — the FAIR-TEST's own controls, re-run.
- **The classical-arm K=0 is the KEY internal control**: it MUST come out ~0 (numerically) — if the classical
  incoherent dephasing gave K>0 it would mean the K statistic is not a clean notion-3 witness (a bug), so the
  classical arm doubles as the K-instrument's null/calibration. (C4-analog established K=0; re-verify here.)
- Positive control: a coherent Markovian σx drive (no bath) should give K>0 but M_mem=0 (coherence without
  memory) — confirming K and the memory statistic are independent axes (deepen DM2).

## 5. Bounded simplifications (declared; unbounded ⇒ STOP)

- **(c) 1 system qubit + single-qubit σx stabilizer proxy** (FAIR-TEST's declared limit; the ancilla-mediated
  multi-qubit stabilizer is the faithful upgrade — feasible few-ancilla exact-DM, dim 4·nmax — a follow-on,
  flagged not built here).
- **(c) pure-dephasing coupling** (`[H_S,σz]=0`, the exactly-benign case; amplitude-damping/leakage is a
  separate stronger axis).
- **(c) Fock truncation nmax** — convergence-checked (FAIR-TEST: converged by nmax≈12–16).
- **(c) CPU exact-DM** (tiny 8–40 dim; NOT the production GPU compute).
- **(c) rough single-statistic N_detect** (order-of-magnitude, as FAIR-TEST).

## 6. Verdict (provisional, pre-code)

GROUNDED: the notion-3 K witness (Milz), the memory-bearing pseudomode bath + the classical-contrast arm, and
the reconciled CMI all exist and are reusable. The load-bearing NEW result = the classical-vs-quantum K
separation (K=0 vs K>0) on one footing, with the corner-confinement re-confirmed under the corrected
observable. PROVISIONAL until measured; the corner-confinement or a K-separation miss are both real findings.

## 7. Build org (heavy ⇒ scouts + builder + un-led reviewer)

Reuse `quantum_backaction_fairtest.py` (K/M_mem/pseudomode) + the classical `OneOverFDriftSource` + the exact
CMI. Builder writes `outputs/twin_validation/notion3_quantum_vs_classical_run.py` (both arms, K + CMI + M_mem,
Fock convergence, coupling sweep, corner, the classical-K=0 control, the coherent-drive positive control),
scripted-execution + smoke. Un-led reviewer vs this prereg. Then serial CPU run (exact-DM, no GPU, no concurrency).

## 8. Post-run results (2026-07-05) — DECLARED-ARM `K` SEPARATION HOLDS (CORNER-ONLY; interpretation superseded)

`outputs/twin_validation/notion3_quantum_vs_classical_run.py` (FULL; `python-exit=0`; evidence
`notion3_quantum_vs_classical.json` sha256 `7bef2895…` over script+json bytes + sidecar). Built via workflow
(3 scouts → builder → un-led reviewer, `meets_spec=true`; reviewer re-derived K from scratch + proved the
classical K=0 is genuine non-invasiveness, not rigged); 2 smoke-only minors fixed. **GATE_RESULT:
NOTION3_SEPARATION_HOLDS_CORNER.**

**Historical headline — `K` separates the two declared arms; it does not classify all quantum vs classical processes:**

| arm | K (Kolmogorov violation) | CMI (bits) | M_mem |
|---|---|---|---|
| **classical** (incoherent σz + time-correlated 2-state latent) | **2.8e-17 (≈0)** — Kolmogorov-CONSISTENT | 0.0117 | 0.077 |
| **quantum** (memory-bearing pseudomode bath, g=0.5) | **5.9e-2 (>0)** — Kolmogorov VIOLATION | 0.00065 | 0.028 |

Thus the declared quantum-bath arm has `K>0` while the declared incoherent classical arm has `K≈0`, and both
carry record memory (CMI/M_mem>0). This is a valid comparison of those two models only. It does not exclude
invasive classical models or Markovian coherence-generating/detecting dynamics and therefore does not certify
process-level quantum memory.

**Controls (all fire, hard asserts):** independent-boson GT `|ρ_01(τ)|`=0.13312799 vs closed-form
0.5·e^{−4Γ}=0.13312799, |diff| 1.76e-10 (non-circular, Rule I); classical-K null 2.8e-17 < 1e-8 (and the
reviewer proved it non-vacuous: a *non-commuting* kick drives K to 0.05–0.35, a σx kick leaves K=0);
coherent-drive positive control K(Z)=0.75, M_mem 8.7e-18 (K⊥memory); Fock-converged nmax=12 (stable to 1e-9
at nmax=20); CMI exact↔sampled(400k) reconcile to ~1e-5.

**Corner-confinement (b, CONFIRMED — reproduces the FAIR-TEST on the corrected observable):** the quantum
K+memory conjunction is headline-feasible (both N_detect ≤ 1e6) only for **g∈[0.2, 0.7]** (gτ 0.4–1.4), with
the falsifier points present (g=0.05,0.1 sub-feasible — binding = N_det(M_mem) 3.4e9/1.3e7; g=1.0 sub-feasible,
both N_det > 1e6). Peak g=0.35, N_det≈4.4e3 — identical to the FAIR-TEST.

**Historical result, interpretation retracted 2026-07-13.** `K` separates the two declared arms and is
**CORNER-CONFINED** to near-resonant strong coupling. It does not prove quantum origin or process-level
quantum memory. Combined with the classical run: notion-2 record memory is broadly visible in the tested
models, while this protocol-family `K` statistic is fragile. At typical/weak coupling `K` is sub-feasible.
PROVISIONAL
until the faithful upgrades (ancilla-mediated stabilizer carrier — few-ancilla exact-DM; the amplitude-damping/
leakage axis, a stronger non-benign coupling); nothing built on it yet.
