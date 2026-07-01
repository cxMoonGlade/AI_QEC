# Axis-1 rebuild — completion + grounding/metric/rigor audit

Date: 2026-06-30. The capstone for the from-scratch, physics-correctness-first Axis-1 rebuild
(`axis1_rebuild_plan.md`). Every kept mechanism cleared the **hard ≥2-DIRECT-physical gate**
(uniform across all groups), is CPTP/operator-exact, certified against **independent** ground truth
(closed-form / hand-typed / from-scratch — never the engine's own oracle), and independently reviewed.

## 1. KEPT — **15 mechanisms with ≥2-DIRECT-physical** + **M23 as a (c)-class Cartan component** (16 operators total)

> **Count reconciliation (2026-06-30, 5-model review):** the ≥2-DIRECT-*physical* set is **15** (the
> rows below excluding M23). **M23 is re-tiered OUT** of that set into an explicit (c)-class
> Cartan-component row (it has 0 isolated-pure-YY device refs; physical home = M10). Total kept
> operators = 16. DOIs verified.

| # | mechanism | carrier form | DIRECT-physical refs (verified DOIs) | cert |
|---|---|---|---|---|
| M4 | amplitude damping (T1) | collapse √γ₁σ⁻ | Krantz 1904.06560 + Place 2003.00024 | `cert_m4_m5_m24` ✓ |
| M5 | dephasing (T2) | collapse √(2γφ)n | Krantz (Γ2=Γ1/2+Γφ) + Place (T2 meas) | `cert_m4_m5_m24` ✓ |
| M24 | thermal excitation | collapse √γ↑σ⁺ | Jin 1412.2772 + Wenner 1209.1674 | `cert_m4_m5_m24` ✓ |
| M6 | Rx over-rotation | 1q H (X) | Sheldon 1504.06597 + Lazăr 2212.01077 | ledger ✓ |
| M7 | Rz over-rotation | 1q H (Z) | McKay 1612.00858 + Sheldon 1504.06597 | ledger ✓ |
| M20 | Ry over-rotation | 1q H (Y) | Sheldon 1504.06597 + Lazăr 2212.01077 | ledger ✓ |
| M8 | ZZ (cross-Kerr) | 2q H ζ\|11><11\| | Pettersson-Fors 2408.15402 + Mundada 1810.04182 | `cert_m8_zz` ✓ |
| M22 | XX | 2q H (coeff/4)XX | Geller 1405.1915 (**isolated** pure-XX gmon, DIRECT) + Sung 2011.01261 (XX **component** of exchange, 10.1103/PhysRevX.11.021058) | ledger ✓ |
| M10 | XX+YY (exchange) | 2q H | Foxen 2001.08343 (10.1103/PhysRevLett.125.120504) + Sung | cert ✓ |
| M29 | ZX (cross-resonance) | 2q H (coeff/4)ZX | Magesan 1804.04073 + Sheldon 1603.04821 | ledger ✓ |
| M11 | spectator crosstalk (ZZ/RZ) | extended-support H | Sarovar 1908.09855 + Mundada / Song 2606.02440 | `cert_m11` ✓ (3q cluster-join) |
| M12 | correlated relaxation (Dicke) | 2-site joint collapse | Mlynek 10.1038/ncomms6186 + Cattaneo (Ann.Phys.533,2100038) | `cert_m12` ✓ (Phase-A **channel-only; carrier trajectory deferred → task #11**) |
| M17 | reset-to-1 bias | reset-substep channel | McEwen 10.1038/s41467-021-21982-y + Reed APL 96,203110 (**reading note now committed**) | `cert_m17` ✓ (**channel-only; biased-reset carrier wiring deferred**) |
| M21 | leakage-conditional phase (**carrier `LEAK_COND_PHASE`; ≠ catalog-M21 qubit-CPHASE — naming caveat**) | 2-site diag H (qutrit) | Miao Nat.Phys.19,1780 (10.1038/s41567-023-02226-w) + Varbanov 10.1038/s41534-020-00330-w | carrier test ✓ |
| M34 | leakage seepage/relaxation | qutrit ladder collapse | Wood-Gambetta 10.1103/PhysRevA.97.032306 + McEwen | `cert_m34` ✓ (WG closed-form) |

**(c)-class Cartan component — re-tiered OUT of the ≥2-DIRECT-physical 15 (per 5-model review):**

| op | form | grounding | status |
|---|---|---|---|
| **M23** ⚠ | 2q H (coeff/4)YY | **0 isolated-pure-YY device refs** (Geller's coupler has no YY). Sung/Foxen exhibit YY only as the **component** of the device-real XX+YY exchange; Zhang/Kraus-Cirac are **operator-algebra only**. | **(c)-class Cartan idealization; physical home = M10.** Operator ledger ✓; kept per user decision, NOT counted among the 15. |

## 2. CUT by the hard gate (9) — could not produce ≥2 device-direct refs
- **M15, M19** — non-physical stress surrogates (no physical-mechanism paper by design).
- **M27** — coherent over-rotation about the arbitrary `(X+Z)/√2` axis (the specific axis is a (c)
  catalog choice with no DIRECT physical ref; Rx/Ry/Rz survive as M6/M20/M7).
- **M28 (XY), M30 (ZY), M31 (XZ), M32 (YZ), M33 (YX)** — off-Cartan directional couplings; KAK-
  equivalent to the Cartan set, **no device exhibits the standalone term** (CR gives ZX not XZ;
  exchange gives XX+YY not XY). No device home at all.
- **M18** — prep over-rotation; operator-identical to M6 (`rx_unitary`), no distinct device-direct
  coherent-prep grounding → "M6 sited at prep," merged into M6.
(Carrier surgery removed `COH_H/XY/ZY/XZ/YZ/YX`; survivors green.)

## 3. Verification (serialized GPU; independent GT throughout)
- **Per-mechanism certs ALL PASS** (operator identities exact; CPTP/CP; closed-form dynamics;
  genuine falsifiers trip). Anti-circular: GT is closed-form / hand-typed / from-scratch Lindbladian,
  never `assemble_substep_channel`/`leakage_channel_super`/`_collapse_operator` as the *operator
  oracle* (those are the objects under test or generic GKSL machinery).
- **Regression: 392 passed** (213 kept ledgers + carrier suite; 179 simulator schedule incl. M21/M34
  carrier execution), 7 skipped, 0 fail — after all deletions + carrier surgery.
- **Independently re-run by the 5-model review panel (serial GPU): 424 passed / 1 skipped** (a superset
  of the 392 above — surgery broke nothing), and **all 6 cert scripts ALL PASS** on their run
  (op-diffs 0.00e+00; M11 join 4.44e-16; anti-circular guards hold) — the "missing run-log" finding
  resolved. After the qt fail-closed fix below, the qt schedule suite re-passes (179).

## 4. Honest caveats (not hidden)
- **M23 (pure YY):** the one mechanism kept only as a **Cartan component** of the device-real XX+YY
  exchange (Sung+Foxen measure the YY component, but **no paper exhibits isolated pure-YY**; Geller's
  coupler has no YY). Kept per user decision (2026-06-30) as an honest (c)-class Cartan idealization;
  M10 (XX+YY) covers it. Pending a final user cut/keep call.
- **Deferred carrier-execution seams** (physics certified at channel level; MCWF/MPS-trajectory wiring
  deferred): **M12 Phase-B** (2-site joint-collapse trajectory seam — the one genuine new-carrier-code
  piece) and **M17** (p-biased reset wiring into the carrier reset substep; carrier reset is currently
  a clean projective reset). M11's schedule-level spectator *emission* is likewise deferred (its
  physics runs on the carrier via the cluster machinery).
- **qt verification-path COH_* silent-drop (5-model review, glm PT1 — pre-existing, NOT introduced by
  the surgery): FIXED.** `axis1_qt_mps_execution.py::_apply_hamiltonian_terms` accepted COH_* (via
  `_is_supported_hamiltonian_term`) but had no apply branch → silently dropped coherent terms on the qt
  (c)-class verification path (the **MCWF carrier — the primary path — was unaffected**; it lowers COH_*
  via the cluster join). Now **fail-closed**: raises on COH_* rather than dropping (confirmed at
  runtime — the review's own check now raises; qt schedule suite re-passes 179). The earlier audit
  "no survivor dropped" claim held for MCWF but was false for qt — corrected.
- **Magnitudes** are (b) prediction-band / (c) swept throughout (T1/T2/T_eff, ζ, η, leakage rates,
  crosstalk c) — none frozen as fact; the *operators/forms* are the (a)-exact load-bearing claims.

## 5. Metric audit (METRICS.md ladder)
Every quantitative cert score is field-standard: process/entanglement infidelity `1−F_e` via the
project-standard `_choi_state_from_kraus`+`_state_fidelity` (Schumacher-Nielsen); Wood-Gambetta L1/L2
leakage/seepage metrics (M34); steady-state populations / detailed balance (M24); reset-bias residual
P(|1>) (M17). No non-standard stand-ins. (One cert proxy was caught in review and switched to the
standard observable — M12.)

## 6. Rigor audit (theorem-backed vs provisional)
- **(a)-exact (theorem-grade, load-bearing):** all operator identities (the carrier emits the
  hand-typed generator/collapse op), CPTP/CP, and the closed-form dynamics (sin²(ε/2), sin²(ε/4),
  (3/4)sin²(ζt/2), e^{−t/T1}, e^{−γφt}, p∞=γ↑/(γ↑+γ↓), Dicke L†L spectrum, WG L1/L2). Verified to
  ≤1e-9 (matrix_exp/Choi roundoff) or exact (0.0) for operator identities.
- **(b)-band:** magnitudes (swept, bracketed to the cited measurements).
- **(c)-gate:** numeric tolerance tiers; conventions (n-vs-Z √2, cross-Kerr-vs-Pauli-ZZ, J_rz=coeff/2,
  /4 two-site); the M23 Cartan-component idealization; deferred-seam scope choices.
- **PROVISIONAL:** any "Axis-1 complete" claim is provisional until the deferred seams (M12 Phase-B,
  M17 wiring) land; the channel-level physics is theorem-backed.

## 7. Adversarial-verification catches (the gate + reviews doing real work)
- Fabricated/wrong citations caught & fixed: Wenner title; `1510.06262` (astronomy paper, not
  Sheldon); Reed "PRL 105,173601"→APL 96,203110; "DiVincenzo & Yang" (fully fabricated, deleted);
  the Miao/Willow Nature-638 conflation in the repo reading note (my prereg was the *correct* one —
  reviewer flag inverted, resolved via ADS bibcode 2023NatPh..19.1780M).
- Non-CPTP bugs caught: old M15 & M17 Kraus (now fixed/verified).
- Circular certs caught & replaced: M34 leakage (house Lindbladian → WG closed-form + from-scratch);
  M11/M12 oracle wording.
- Unreadable extraction caught: Ithier cond-mat/0508588 → substituted Place.
- Self-caught: the M12 §3 λ-mapping slip (→ λ=1−e^{−2γφt}); the cert metric proxy → standard.

## 8. Completeness statement
The simulator's Axis-1 error-mechanism coupling is **evidence-complete at the channel level and
physically correct** for the 15-mechanism device-grounded set above — each ≥2-DIRECT-physical (DOIs),
CPTP/operator-exact, independent-GT certified, reviewed; regression green (392 local; 424 panel). Per
the project's engine-never-self-declares-"complete" principle, the headline is **PROVISIONAL pending
(a) the deferred carrier seams and (b) your sign-off** — it is not a self-asserted "done." **Remaining
for full carrier execution:** M12 Phase-B (2-site joint-collapse trajectory seam) + M17 biased-reset
wiring — both gated, careful builds with the channel-level certs as oracle and a hard no-regression
gate on the 1-site collapse / projective-reset paths.

## 9. 5-model independent review (2026-06-30) + fixes applied
Panel: opus, codex (gpt-5.5), sonnet, glm-5.2, deepseek — full repo+Bash agents on a per-point brief,
read-only, CUDA hidden (orchestrator ran all GPU serially). Verdict: **4× SOUND-WITH-FIXES + 1×
NOT-YET (codex, on M23 gate-semantics + the count)**. Consensus: the certified channel-level physics
is correct and genuinely anti-circular (independently reproduced + GPU-verified); residuals are
accounting/labeling + one pre-existing qt bug. Artifacts: `outputs/twin_validation/rebuild_review/`.

Fixes applied in response:
1. **[MAJOR, FIXED] qt-path COH_* silent-drop** — `axis1_qt_mps_execution.py` now fail-closed (raises);
   confirmed at runtime; qt suite re-passes 179 (§4).
2. **[MAJOR, FIXED] M23 mis-tier + mislabel** — re-tiered OUT of the ≥2-DIRECT-physical 15 into the
   explicit (c)-class Cartan-component row (§1); m23 prereg's Zhang/Kraus-Cirac "DIRECT"→"ALGEBRA-DIRECT
   (not device-physical)"; 15-vs-16 count reconciled (15 + M23).
3. **[MAJOR, FIXED] M17 gate-short** — committed the Reed reading note
   (`reed_fast_reset_purcell_1003.0142.md`); M17 now 2 note-backed (McEwen + Reed). M17/M12 rows
   relabeled "channel-only; carrier-execution deferred".
4. **[MINOR, FIXED] M22 Sung-as-component** — Geller = isolated pure-XX DIRECT; Sung = exchange component.
5. **[MINOR, FIXED] M21 naming caveat** — added to the §1 table.
6. **[MINOR, FIXED] "complete" wording** — §8 now "evidence-complete (channel-level), PROVISIONAL".
7. **[RESOLVED] cert run-logs** — generated by the panel (all ALL PASS); local run-logs for M12/M17/M34.
8. **[OPEN — forward/ scope] catalog.py stale groupings** (M18/M28/M30-33 in `RZZ_FAMILY_IDS` etc.) —
   the *forward/* subsystem (plan §2 exempted forward/); forward/-cleanup follow-up, not the Axis-1 carrier.
9. **Panel cross-check refuted 2 reviewer errors** (diversity working): sonnet's "M29 has Sung's DOI"
   (false — PhysRevX is on Sung@M22); glm's "M21 L1 structural" (false — genuine hand-typed 9×9 cert).
   The panel's own "Miao DOI wrong" flag was **inverted** — re-verification (ADS 2023NatPh..19.1780M)
   showed *my* citation correct and the repo reading note wrong (now fixed).

**Net:** no review finding corrupted the certified physics; all accounting/labeling fixes applied; the
one code bug (qt silent-drop, pre-existing) is fail-closed. M23 cut-vs-keep + the deferred carrier
seams remain your calls.
