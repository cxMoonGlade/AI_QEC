# Scoping result — leakage's decodable headroom over the deployed frontier is largely OWNED (d3)

**Status: consolidated scoping / honest-negative result (2026-06-22).** Consolidates ⑦ (binary), the
soft-readout comprehensive review (terminal-soft), and the cross-round/space-time analytic gate, plus
the prior Pauli-DEM frontier finding, into one defensible boundary, and repositions the program's claim.
Epistemic discipline (METRICS.md): every conclusion below is classified; the headline is **PROVISIONAL**
(convergent evidence, not theorem-grade — see §5), and the honest residuals (§4) bound it so it is not
over-claimed.

---

## 1. The claim (precise + scoped)

> At distance-3 (and, per Miao's simulation, d5/d7), **over the *deployed* surface-code frontier**
> — hardware leakage removal (DQLR/LRU) + correlation-aware matching (corrMatch) + learned priors (RL)
> — the candidate non-Pauli **leakage-decoding** levers we examined do **not** show material decodable
> logical-error headroom. The leakage *signal* is real and raises the optimal LER; the part that is
> *decodably recoverable over the deployed stack* is **largely owned**.

"Owned" = over the DEPLOYED frontier. Against *weaker* baselines (plain MWPM, no-LRU) the headroom is
real — but beating those is not the project's contribution bar (`project-decoder-gate-and-frontier`:
beat the shipped frontier).

## 2. Evidence ledger (each finding: what it shows, its class)

| Lever | Finding | Class | What it does NOT show |
|---|---|---|---|
| **Binary readout (⑦)** | Leakage RAISES the optimal LER (`ΔF>0`, 8/8 exact, z→7.69 — solid); but **no decodable non-Pauli headroom over the best moment-matched Pauli** (capped, \|z\|<2). | ΔF (a) exact; capped (c)/provisional | Ran at R≤5 / sub-register (small-R) — the large-R cross-round case is addressed by the gate, not by ⑦. |
| **Soft-analog, terminal (review)** | The genuine `hard-3→soft` analog leakage contribution at the terminal is **~0 at realistic rates** (independent d3 stim+MWPM, 3M shots, McNemar p=0.67) and **geometry-knob-set**; the real lever is the discrete erasure flag (NOT analog, deployed). **Terminal-soft = toy.** | (a) measured (independent sim) | Terminal only; not the per-round soft-syndrome channel. |
| **Cross-round / space-time (gate)** | **Owned by deployed DQLR.** Miao's own measurement: DQLR decorrelates leakage to Pauli-like (Fig 5c: `1/Λ` LINEAR in `P_L`, d3 AND d5/d7-sim) → correlated-excess = 0 → no cluster-aware headroom over corrMatch+DQLR. Headroom non-zero only WITHOUT/partial removal. | (b)/(c) Miao-anchored ANALYTIC (not our sim) | We did not run a from-scratch large-R sim (gated out); it is a Miao read-off, not our measurement. |
| **Leakage detection** | The erasure-flag benefit (hard-2→hard-3) is REAL but **deployed** (DQLR/LRU, Miao). | (a)/literature | — |
| **Pauli-DEM (prior)** | The better-Pauli-DEM contribution is **capped**; the frontier clears predominantly via off-the-shelf TN-MLD on Google's RL DEM. | prior, reviewer-confirmed | — |
| **Coherence (prior)** | Not identifiable from binary syndromes (~2% of the NLL gain). | prior | — |

**The convergence:** every leakage-decoding sub-axis examined — detection, binary, terminal-analog,
cross-round/space-time, Pauli-DEM — comes back owned or capped *over the deployed frontier*.

## 3. Why (the one-line mechanism)

Hardware leakage removal (DQLR/LRU) is the field's chosen solution and it is **decoder-side
self-defeating for our thesis**: by removing `|2⟩` every round it (a) eliminates the detection need,
(b) kills the temporal persistence (cross-round correlations), and (c) decorrelates the spatial spread
→ "leakage ≈ Pauli" (Miao). The residual is then captured by the deployed correlation-aware matcher
(corrMatch on `pij`) + learned prior (RL). So a richer leakage-aware decoder has little left to recover.

## 4. Honest residuals — what is NOT owned / NOT shown (the anti-over-claim boundary)

The negative is **scoped**, not absolute. Genuine residuals where headroom may exist:
1. **Systems WITHOUT good hardware leakage removal** (non-DQLR platforms): the cross-round/space-time
   headroom is real and R-growing there (gate). A real but **niche** contribution (competes with
   "deploy DQLR in hardware").
2. **d5/d7 MEASURED** (not Miao-sim): the owned conclusion at d5/d7 rests on Miao's *simulation*
   (PROVISIONAL); a measured large-d surprise is not excluded.
3. **Per-round soft-syndrome** was not directly simulated by us (the estimate was stopped at the
   redirect); the gate's logic (DQLR decorrelates) strongly implies it is also owned, but it is inferred.
4. **The large-R cross-round case** was settled by a Miao-anchored ANALYTIC gate, not a from-scratch
   sim — a strong read-off, not our direct measurement.
5. **Generic soft-readout** (Ali 6.8%) is real — just generic `|0⟩/|1⟩` softness, not leakage-specific,
   and not over the deployed frontier.

## 5. Epistemic status of the headline (PROVISIONAL, not theorem-grade)

The "leakage-decoding over the frontier is largely owned" headline is a **PROVISIONAL conclusion**
(METRICS.md provisional-conclusion corollary): well-supported by *convergent* evidence (⑦ + an
independent terminal sim + a Miao-anchored gate + the prior Pauli-DEM/frontier finding), but **not
theorem-grade** — the large-R cross-round and d5/d7 cases are analytic/sim-inferred, not directly
measured by us (§4.2–4.4). It is **usable for go/no-go gating** (stop building leakage-decoding levers
over the frontier) but **must not be cited as a proven impossibility**, and nothing is built on it as a
premise. The component findings ⑦-`ΔF` and the terminal-soft `~0` ARE measured (a)-class.

## 6. Repositioning the program's claim

- **OLD (over-optimistic) framing:** a non-Pauli leakage teacher-learner + a richer decoder beats the
  frontier's LER by recovering leakage headroom binary/Pauli decoders miss.
- **REPOSITIONED (honest):** *over the deployed frontier, leakage's decodable headroom is owned* — so
  the program's contribution is **not** "beat the frontier's LER via leakage-aware decoding." The
  candidate unowned seam to examine next is the project's **original** differentiator: a **calibrated,
  uncertainty-quantified DEM with honest bands/CPTP** (the finance↔QEC calibration isomorphism) — which
  the deployed **point-estimate** decoders (corrMatch/TN-MLD/RL-prior) do **not** provide. That axis
  must pass the SAME prevent-toy bar (real-question + effect-size + is-it-genuinely-unowned) before any
  code — it is a candidate, not an assumed win. **(Next-axis selection deferred — this doc closes the
  leakage-decoding question; it does not open the next one.)**

## 7. What this result IS (so it reads as a finding, not a give-up)

A rigorous, scoped negative obtained by the prevent-toy discipline — it (i) kills three toy/owned
directions before they were built into the codebase (terminal-soft was caught + reverted; the
cross-round sim + Phase-1b carrier were gated out by the analytic check), (ii) is grounded in the
field's own measurements (Miao), and (iii) repositions the program onto an honest footing. "Slow is
fast": the cost was three analytic/estimate passes; the saving was a built-and-then-discarded
leakage-decoding pipeline.
