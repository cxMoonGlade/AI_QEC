# CF-WR — Windowed-Reconstruction Feasibility Verdict (ADR 0008 C1 Carrier)

> **This file is the single entry point for CF-WR.** Build/analysis sub-agents need only read this README + `registration.md`
> (+ `P2_derivation.md` when required); **no need to touch the M1–M4 history in `metric_results.md`**.
> Status: **registration frozen (2026-06-14); build pending launch.**

## 0. One sentence

Exact 2×2 windows + principled gluing: can the **exact global noise-channel Choi state** be reconstructed; where does it break down as bunching strength R̂ grows and the 2D seam is line-shaped — and is K1's ABSTAIN wall a **wrong gluing rule (mean-field) or a fundamental limit**?
Route M4's PROVISIONAL negative result into either a **way out (GO)** or a **PROVISIONAL ceiling for this correlation class (NO-GO)**. No "wasted run" branch.

## 1. Why this experiment

- True hardware W1 (counterfactual unverifiable) + scale (exact backend ≤15q, cannot fit surface code) dual constraint; Markov/bunching already claimed by the frontier.
- Converges to the one unoccupied position: **controlled verification with ground truth × real data × measuring the sim-to-real seam**.
- CF-WR is the first block: at ≤15q **with exact ground truth**, adjudicate the feasibility of windowing + gluing, **and classify the K1 wall as artifact or fundamental limit**.

## 2. Spec at-a-glance (full text → `registration.md`; frozen in `docs/metric_results.md` `### CF-WR PRE-REGISTRATION`)

| Item | Value |
|---|---|
| **Teacher** | 12q 2D nearest-neighbour lattice toy (3×4), logical distance ≥ 2, **not surface-faithful** (d3 = 17q does not fit ≤ 15q); captures 2D seam geometry |
| **R̂ knob** | **Non-unital local CPTP** along the T-B curve (signed δ′ = p10 − p01, both sides); R̂ ∈ {1, 2, 3, **5.3**, 8, 12} (5.3 = hardware-match core) |
| **φ knob (optional)** | Independent coherent edge (R-EDGE), **carries no R̂** |
| **Arms** | G0 mean-field · **G1 Petz (certified)** · G2 GNN-learned-BP (anchored to G1, (c)) |
| **co-primary** | D_Choi = ½‖J − J_glue‖₁ (bound `√(I_nats)`) **and** E_do = `knob_dler_error`; **τ_D = 0.5√(I_nats), τ_E = 0.1\|ΔLER_true\|** |
| **Sanity gates** | S-markov (explicit ≤4q QMC) · S-impl (R̂ = 1 ≤ 1e-3) · S-trivial · S-monotone |
| **Seed** | 20260614; **sim/teacher-only, zero hardware/held-out/escrow** |

## 3. Predicted outcomes (confidence; see conversation log for detail)

| Item | Prediction | Confidence |
|---|---|---|
| Sanity gates / P2.1 G0 slope-1 | Pass / confirms linear (K1 measured 0.973) | ~90–95% |
| P2.2 c < 1 (Petz wins) | likely | ~75%; **c ≤ 0.5 only ~40%** |
| Breakdown tail R̂ ∈ {8, 12} | Both arms break down (defines ξ*) | ~90% |
| **Headline GO/NO-GO @ R̂ ≈ 5.3** | **~50/50, genuinely uncertain** (hardware point sits in the uncertainty band) | —— |

Most likely outcome: **MIXED / bounded** — reconstruction up to some ξ*, Petz wins slightly, breakdown at R̂ 5–8. ξ* above 5.3 = GO; below 5.3 = NO-GO (nails M4 as ceiling).

## 4. Reporting discipline (guard against "good result ≠ true capability")

- **Raw numbers take priority over gates**: RESULTS headline is **absolute D_Choi(R̂) / ξ* / c**; GO/NO-GO is a derived label only.
- **τ_D is half a loose upper bound** ⇒ passing the gate = necessary but not sufficient; true quality is read from absolute D_Choi and c.
- **Bounded claim nailed down**: 12q-GO only proves "gluing mechanics + error law correct at the verifiable scale"; **does not prove d5/d7 carrier works** (toy lacks long boundary + uncharacterisable quality); GO never transfers across to scale/hardware.

## 5. Build plan (heavy work, pending launch)

4 scripts, each **≥ 3 sub-agents + reviewer, run serially**, scripted-execution (assertions + printed evidence + spawn `__main__` guard) + 65 GB memguard, GPU-only model compute:
1. `outputs/cf_wr_teacher.py` — 3×4 tile + non-unital T-B noise field + δ′ → R̂ calibration + do() target (assert |ΔLER_true| ≥ 5 × floor) + exact J(E)/ρ + sha256 freeze;
2. `outputs/cf_wr_windows.py` — 2×2 / 2×3 / strip window partitioning + per-window exact Born-NLL fit (+ optional A warm-start, bit-identical gate);
3. `outputs/cf_wr_glue.py` — G0 mean-field / G1 Petz / G2 GNN-BP (anchored to G1);
4. `outputs/cf_wr_score.py` — D_Choi / E_do / CMI / sanity gates / P1–P5 fit.
Run → `docs/cf_wr/RESULTS.md` + metric audit + rigor audit.

## 6. Red-lines

Sim/teacher-only (no hardware / held-out 05–09 / escrow 15–19 touched); white-box core exact (G1 Petz), **G2/A tagged (c), anchored to exact objects, never entering the (a) trunk/premise** (ADR 0008); registration text frozen (τ / c < 1 as (b) / R̂ grid / seed / teacher-sha256); theory-first (prediction band frozen before run); commit on completion (no push, no co-author).

## 7. Pointers

- **This suite**: [registration.md](registration.md) (full design) · [P2_derivation.md](P2_derivation.md) (P2 (a)-grounding) · `RESULTS.md` (to be produced).
- **Of-record stub + global ledger**: `docs/metric_results.md` `### CF-WR PRE-REGISTRATION` (stub) · `docs/METRICS.md` (D_Choi row).
- **Upstream**: `docs/adr/0008-scalable-carrier-feasibility-study.md` (C1 architecture) · `docs/.reports/adr0008_panel/` (K1 seam ABSTAIN, T-B theorem, composed.py G0) · `metric_results.md` M3/M4 (bunching R̂ ≈ 5.3, M4 negative result).
