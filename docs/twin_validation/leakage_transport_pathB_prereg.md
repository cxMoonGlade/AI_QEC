# Path-B — Leakage-transport `edge_field` — Pre-Registration (theory-first, LITERATURE-GROUNDED)

Status: PRE-REGISTRATION, 2026-06-25. Predictions written BEFORE the run; a miss is a finding, not a re-fit.
Scope: model form-4 of the crosstalk taxonomy — **leakage transport** (spatial leakage spreading via the
diabatic CZ), the dominant non-ZZ crosstalk, currently DEFERRED in the carrier (`edge_field=None`). This
closes the undeclared-simplification gap (faithfulness protocol) by BUILDING it and MEASURING the
approximation error, not assuming. Sequenced BEFORE the UQ layer (user, 2026-06-25).

## 0. Grounding ledger (corresponding papers — 精读 status)
| sub-item | mechanism paper | observable/validation paper | reading note | status |
|---|---|---|---|---|
| transport rates + 0.65π phase | Miao 2211.04728 (Google, Nature 2023) | Miao Fig 2b/2e/S7 (fractions, phase, p̄) | `miao_overcoming_leakage_scalable_2211.04728.md` | 精读 ✓ (⚠ g_eff/fraction labels → step-0 re-verify) |
| implementable qutrit channel + the |2>-vs-|3> GAP | Varbanov 2002.07119 (DM Surface-17, quantumsim) | Varbanov §II + App D (defect-prob, pd≈0.5) | `varbanov_leakage_detection_surface_2002.07119.md` | 精读 ✓ |
| Google |3>-transport + DQLR-on-|3> (deployed regime) | Willow 2408.13687 (Google, Nature 2025) | Willow SI IV (time correlations) | — | **step-0 精读 (downloaded; deep-research-extracted)** |
| CZ itself is qutrit-faithful (no |3>) | Barends 1907.02510 | — | (deep-research) | confirmed |
| taxonomy + adversarial verdicts | deep-research wf_dc2e46de (105 agents, 18/7) | — | `tasks/w60mu255o.output` | done |

## 1. The mechanism — TWO ARMS (build both, measure the gap)
The decisive deep-research verdict: |3>-necessity for transport is **contested** (no theorem-grade |2>-vs-|3>
bound; 5/5 strong claims refuted/split), so we DO NOT pick by assumption — we **build both arms and MEASURE
the gap on the d3 DM oracle**.

- **Arm 1 — |2>-only (qutrit, local dim 3):** the Varbanov channel — leakage exchange `|11>↔|02>` (rate L1) +
  **randomized** leakage-conditional phases `φ_L^stat=φ02−φ12`, `φ_L^flux=φ20−φ21` + the weak direct
  `|12>↔|21>` mobility `L_m`. (Varbanov §I-A.)
- **Arm 2 — |3>-faithful (ququart, local dim 4):** + the |3>-mediated transport — `|12>↔|03>` superleakage
  (`L3`, coupling √3 J1), the |3>-enhanced `|12>↔|21>` via the on-resonance `|03>↔|21>` exchange (Varbanov
  Eq H4, ≈2.6 MHz), and Miao's `|30>↔|12>`/`|31>↔|22>` resonances (`P_t=sin²(g_eff·t)`).

**Channel DERIVATION = QuTiP** (decided 2026-06-25): build the 2-transmon multi-level Duffing Hamiltonian +
diabatic flux pulse (Varbanov Eq H1 params), `mesolve`/propagator → `to_kraus` → the per-CZ Kraus. Arm 1 =
QuTiP truncation dim 3; Arm 2 = dim 4. (QuTiP-CPU, mature, one-time, 16-dim — avoids the diffrax-complex-WIP
risk; GPU not needed for the channel.) **NEVER freeze** the device-specific params (phase, transport
fractions, η, t_g) — SWEEP as bands.

## 2. Predicted observables (class (b) bands — falsifiable, ANCHORED)
- **The GAP (headline):** `Gap(Arm2 − Arm1)` on the d3 DM oracle (LER + the moment fingerprint). PREDICTION
  (Varbanov App I, grounded): the transport is **2nd-order in the leakage population** → `Gap ≈ 0 at low
  leakage (L1 ~ 1e-3, DQLR-deployed)` and **GROWS with the leakage population** (toward Miao's un-removed
  dominance). A miss (e.g. large gap at low L1) is a finding.
- **Detector fingerprint (decode-independent):** (i) **non-local time correlation** `p̄_{t,t'} > 1%` at
  `|t−t'| > 1` (Miao S7; iid-Pauli gives 0 there) — the cleanest non-Pauli signal; (ii) **neighbour
  defect-probability increase** + **pd≈0.5** on weight-3 anti-commuting checks (Varbanov §II/App D) —
  NECESSARY not transport-unique (Kam 2410.23779: 2-point can't grade severity), so pair (i)+(ii).

## 3. Independent ground truth (non-circular)
- The QuTiP-derived channel is validated against **Miao's MEASURED transport fractions** (Fig 2b, ~18-19% /
  ~58-61% — labels step-0-verified) + the **analytic `g_eff = −(2g)(√3 g)/η = −2√3 g²/η`** (Miao SI S1;
  `g_{|21-|12}=2g` deep-research-verified, step-0-confirm). QuTiP (our Hamiltonian sim) vs Miao
  (hardware-measured) + the closed form = NON-circular.
- The engine (torch QutritDM apply-Kraus) is the SCORING substrate, separate from the channel source (QuTiP)
  and from the validation (Miao/closed-form/Stim) — no check-vs-own-oracle.

## 4. Bounded simplifications (declared; unbounded ⇒ STOP)
- **|2>-only (Arm 1) = a declared 2nd-order approximation**, error BOUNDED EMPIRICALLY by the Arm2−Arm1 gap
  measurement (§2) — valid (small) only in the low-leakage regime (Varbanov App I); the teacher is RESTRICTED
  to that regime unless Arm 2 is used. (class (b)/(c).)
- **|3> truncation (Arm 2): no |4>+** — Miao notes hints of `|42>↔|33>`; declared, bounded by checking the
  |4> population stays < a set tolerance in the QuTiP channel (step-0).
- **Per-CZ-injected leakage rate** (Stim parses structure only; not ns-integrated) — inherited carrier
  simplification; the QuTiP channel carries the within-CZ dynamics, so this is tighter than before.
- **Phase randomization** (Varbanov's own treatment) — a swept band, not a frozen value.

## 5. Epistemic status (METRICS ladder)
- **(a) exact:** the DM-oracle Gap measurement (exact on d3 sub-codes); channel CPTP (`Σ K†K=I` to NUMERICAL_ZERO);
  the apply-Kraus engine correctness (R2-validated `apply_channel_2site` 5.6e-17).
- **(b) bands:** the gap-scaling prediction (2nd-order in L1); the transport fractions/phase (swept).
- **(c) gates:** the fingerprint thresholds (`p̄>1%` at `|t-t'|>1`; pd≈0.5); the |4>-tolerance.
- Headline verdict stays PROVISIONAL (convergence + independent oracles).

## 6. Build org + architecture (the decided platform)
**Architecture (data-driven, 2026-06-25):** QuTiP (channel) → torch-GPU `QutritDM` engine (apply-Kraus;
benchmarked GPU 4× @ dim729, 20× @ dim2187 vs CPU — `engine_slice_gpu_vs_cpu.py`) → d3 sub-code gap test.
- **Step 0 (pre-code verifications):** (a) 精读 Willow 2408.13687 leakage SI; (b) re-verify Miao SI S1 `2g` +
  the 18%/61% fractions + the |30-12 vs |21-03 labels vs ar5iv (deep-research flagged a 1-2 label split);
  (c) QuTiP channel reproduces Miao fractions + analytic g_eff (the GT check) + |4>-tolerance.
- **Builders (disjoint):** (A) QuTiP channel module (dim 3/4, swept, → Kraus); (B) carrier `edge_field`
  integration (apply via `apply_channel_2site`; Arm 2 needs the engine extended to local dim 4 — the
  ququart cost); (C) the gap-test + fingerprint harness on the DM oracle.
- **Verification (non-QuTiP, non-circular):** Stim (Clifford slice) + analytic/closed-form + the torch DM
  oracle cross-check; an **un-led reviewer** (problem+goal+artifact only).
- **Discipline:** GPU bounded + serial (no concurrent GPU — the 2026-06-25 OOM); scripted-execution; carrier
  mainline changes COMMIT-GATED (user commits); 精读 not delegated.

## 7. The kill / null controls
- **DQLR-removal null:** at full leakage removal (DQLR regime), the transport headroom must VANISH (Miao Fig
  4a leakage≈Pauli) — the positive/negative control pair.
- **iid-Pauli foil:** `p̄_{t,t'} = 0` at `|t−t'|>1` for the iid foil (the fingerprint's teeth).
