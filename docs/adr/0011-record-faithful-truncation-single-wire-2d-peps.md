# ADR 0011 — Record-faithful truncation on the single-wire 2D PEPS carrier (amends ADR 0010 geometry; retracts the leak-ON FORK-B/C)

## Status

**Accepted (decision 2026-07-12, user).** **AMENDS ADR 0010** for the full `d×d` surface-code
geometry and the leakage truncation criterion; **does not overturn** ADR 0010's MCWF-trajectory
forward, per-round-independent (LRU) leakage model, or the certification ladder — those stand.
Grounded in: the zoom-out territory map (2026-07-12, wzb623wrz), the crux resolution
(`CRUX_RESOLVED_bond_is_gauge_artifact_2026-07-11`), the build_first ZMT f-gap diagnostic
(2026-07-12), and the mainline framing (`project-simulator-p0p4-plan-framing`,
`project-leakage-lru-const-memory-notion2shadow`). Theory-first: the load-bearing physics anchors
are (a)-exact or theorem-grade; the operational truncation gate is a registered prediction band.

## Context

- **ADR 0010 is superseded on two points that were written for the wrong geometry / wrong instrument.**
  ADR 0010 §Decision-4 registered the leakage scaling forward as a **thin-strip (w×d) MCWF-MPS snake**
  and **deferred full `d×d` as a research risk**. But the actual d5/d7 target is the **full `d×d` rotated
  surface code**, whose 2D geometry a 1D MPS cannot carry: snaking the full square into a 1D chain hits
  a bond wall `χ ~ 2^{2d}` ([[project-fulld-1dmps-wall-and-2dpeps]]) — MPS is **geometry-incompatible**
  with the full surface code. The doubled-wire **DM-PEPO** carrier was also **closed/archived**
  (F-SEL-1/F-REC-1: the compiled weight-4 √Eₛ POVM concentrates onto fresh path bonds via ket⊗bra
  squaring). The **single-wire 2D PEPS** pure-state trajectory carrier is the **survivor**, deliberately
  started as the full-`d×d` fix (`peps_singlewire_spike_contract`; d3 gates 28/28 green, committed). So
  "fall back to thin-strip MPS / defer full-2D" is **not a live option** — it regresses to something
  already ruled out.
- **The leak-ON per-edge-bond saga was mis-framed.** Many sessions were spent on: the single-wire PEPS
  leak-ON per-edge bond GROWS, the FET/ZMT truncator cannot cleanly cut it (weak coherent leakage
  `C_L~0.2, leak_mass~1e-3` smears the exactly-zero loop/gauge modes into a continuum), forcing a
  "FORK-B (stabilizer-frame carrier) vs FORK-C (bounded-larger bond)" decision. **Every literature
  search reshaped that decision** because it was **gated on the per-edge BOND** — a gauge-dependent
  representation-cost artifact that is not physical (over-counts loop+gauge directions), not the
  product's validity target (the multi-time syndrome RECORD is), and moves with the truncation policy.
  Optimizing a moving artifact has nothing to converge to. This violates the project's standing rule
  ([[feedback-simulator-not-decoder]], [[feedback-gate-on-record-not-carrier-artifact]]): the carrier
  bond / DEM / decoder / LER are **never** in the validity chain — the RECORD is.
- **The coherent leakage tail the bond fought to hold is not a record observable.** Four anchors:
  (i) **(a)-exact** — at d3 leakage-ON (WG_L1=5e-3, `C_L=0.199`) the carrier's exact `dense_psi` bipartition
  entropy `S_A = 2.00000` ebits, UNCHANGED across 6 trajectories and IDENTICAL to leak-off and to the
  independent GF(2) stabilizer baseline to 2e-16; the `|2⟩`-mass ~1e-3 inflates the Schmidt RANK (4→29)
  but adds **zero** bipartition entropy (leakage is a LOCAL channel). (ii) **which-branch** — the ancilla
  CZ+projective-Z is a leak-flag measurement, so the joint syndrome distribution is a classical mixture
  `|α|²P(·|unleaked)+|β|²P(·|leaked)`; the `C_L` off-diagonal never enters a syndrome-bit probability.
  (iii) **LRU/DQLR** resets `|2⟩` each cycle, dephasing the `|1⟩–|2⟩` coherence between rounds → a diagonal
  population flag (notion-2) only. (iv) **theorem-grade** — Behrends–Beri 2412.21055 (PRX Quantum): for any
  nonzero incoherent component the logical-noise coherence is **exponentially suppressed in code distance d**,
  so the tail is exp-small exactly at the d5/d7 the carrier targets. Corroborating: pauli_channels_from_syndrome
  (correlated-Pauli reachable, coherent-non-Pauli not), STA 2312.10277, QMCtwin 2606.19848. This is the
  same protocol boundary that fixes leakage's record content to **notion-2** ([[project-leakage-lru-const-memory-notion2shadow]]).

## Decision

1. **The full-`d×d` surface-code leakage scaling forward carrier = the single-wire 2D PEPS**
   (pure-state MCWF trajectory; dim-3 physical leg; per-round leakage Kraus). MPS is retained ONLY for
   genuine thin strips (ADR 0010's w×d regime, where χ is small/constant in d); **MPS-on-full-`d×d` and
   the DM-PEPO are CLOSED** (geometry wall / path-bond concentration). ADR 0010's MCWF-exactness,
   LRU leakage model, LPDO floor, and certification ladder are UNCHANGED.
2. **Leakage stays the per-round-independent local Kraus flavor, applied on the carrier's qutrit legs**
   (ADR 0010 §Decision-2/-3, [[project-leakage-lru-const-memory-notion2shadow]]). At d3 this is the fast
   dense SV kernel (`sv_traj_d3` loader); at d5/d7, where no dense state exists, the SAME per-round Kraus
   is applied on the PEPS legs. The coherent leakage tail is **not** a passive-record observable (Context iv).
3. **Leak-ON truncation on the carrier is RECORD-faithful, not state-/bond-faithful.** Because the
   coherent leakage tail carries **zero bipartition entanglement** and is **absent from the record**, the
   carrier **DROPS it** (aggressive truncation of the leakage-dressed continuum), keeping the per-edge bond
   bounded at the leak-OFF Clifford area-law scale. **Feasibility/faithfulness gates on the RECORD**
   (multi-time syndrome statistics: CMI `I(m_r;m_{r-2}|m_{r-1})` / G²-order / differentiable NLL vs a matched
   notion-2 null), **never on `bond=4`, never on state fidelity, never on 2-point TV.** The per-edge bond is
   a resource guard only.
4. **The leak-ON FORK-B (stabilizer-frame carrier + qutrit-Z₃ extension) / FORK-C (bounded-larger bond +
   saturation gate) decision is RETRACTED as mis-framed.** Both forks lived inside the mis-gated bond
   frame; the record-faithful-truncation criterion (Decision 3) dissolves the question. The stabilizer-frame
   and classical-flag/Pauli+ machinery (2403.08724 / 2511.06672 GCAMPS-qudit / Google Pauli+ 2207.06431 /
   the `leaky` lib) remain **parked contingencies**, unparked ONLY if Decision-3's record-null FAILS
   (the coherent tail proves record-reachable — see Validation).
5. **The leak-OFF Clifford d5/d7 per-edge-bond truncation is a parallel engineering item, not
   mainline-gating.** The Clifford backbone is area-law (bounded per-edge bond by construction), but the
   local simple-update truncation over-counts loop+gauge directions (SW-S6); the deterministic
   closed-loop gauge-fix / zero-mode truncation (Evenbly-2018 1801.05390 WTG; Sokolov–Dziarmaga
   2508.00338) replaces the stalling ALS. This is banked independently, gated on **S_A saturation**
   (physical entanglement), and a miss is adjudicated inside the registered WP1 menu, not a
   mainline-science reversal.

## Validation (the gate for Decision 3, before any d5/d7 claim)

- **The record faithfulness NULL (a P1 faithfulness-table cell + the fork-closer).** On d3 XZZX in the
  weak-LRU regime (`leak_mass~1e-3, C_L~0.2`), generate the record TWO ways — (A) the coherence-carrying
  qutrit forward (approximation-free oracle) and (B) the tail-dropped / classical-flag SV-kernel record —
  and score their **distinguishability on the RECORD observable** (CMI / differentiable NLL against a
  matched notion-2 null), NOT on 2-point TV and NOT on the carrier bond, via a committed script (asserts
  + printed evidence + `__main__` guard). **PASS** (predicted band, given Context i + iv) ⇒ dropping the
  coherent tail is record-faithful ⇒ Decision 3 licensed, the leak-ON fork CLOSED, all FET/ZMT/WTG
  leak-ON solver effort HALTED, return to the live science spine P2-ii (b)/(c) @ d3. **FAIL** (the tail is
  record-distinguishable) ⇒ Decision 4's parked contingency unparks and the coherent tail becomes a
  first-class carrier target.
- **Only re-opener:** if the product's declared observable expands from BINARY syndromes to per-round
  **soft/analog** readout, within-round `|1⟩–|2⟩` coherence becomes partially observable and Decision 3 is
  re-examined. The stated P1–P4 product is binary; scoping already measured terminal-soft ≈ 0.

## Alternatives considered (rejected, with reason)

- **MPS on the full `d×d` surface code** — 1D snake of the 2D square hits `χ~2^{2d}`; geometry-incompatible
  ([[project-fulld-1dmps-wall-and-2dpeps]]). Retained only for thin strips.
- **Doubled-wire DM-PEPO** — compiled weight-4 √Eₛ POVM concentrates onto fresh path bonds via ket⊗bra
  squaring (F-SEL-1/F-REC-1); closed/archived.
- **Hold the coherent leakage tail faithfully in a bounded per-edge bond (FORK-B / FORK-C)** — mis-framed:
  the tail is not a record observable, so no bounded-bond representation of it is required; drop it (Decision 3).
- **Gate feasibility on the per-edge bond (`bond=4`, ZMT f-gap, state fidelity)** — a gauge-dependent moving
  artifact, not the product's validity target; the RECORD is ([[feedback-gate-on-record-not-carrier-artifact]]).

## Consequences / open risks (honest)

- **The record-faithful-truncation premise is a registered PREDICTION BAND until the null passes.** "Dropping
  the coherent leakage tail leaves the record unchanged" is (b), not a theorem, despite the strong (a)-exact
  + theorem-grade priors; a miss is a finding that unparks Decision 4.
- **d5/d7 remains oracle-free / PROVISIONAL** (ADR 0010 Rung-d5/d7 unchanged): the record-faithful truncation
  is validated at d3 against the qutrit oracle, then extrapolated with internal χ-convergence + S_A-saturation
  self-consistency; no d5/d7 distributional claim is a premise.
- **The leak-OFF Clifford solver (Decision 5) is genuinely unresolved engineering** (WTG/zero-mode unread-into-src;
  ALS unreliable on long-range loop bonds) — but it is decoupled from the mainline and from the leak-ON question.
- **Binding the LRU / per-round-independence assumption to the specific R2-lite Google XZZX dataset**
  (residual-efficiency bound; carryover on platforms with weak DQLR) is a standing theory-first pin (ADR 0010
  open risk, unchanged).

## Epistemic-status audit

Coherent tail not-in-record: `S_A(leak-on)=S_A(leak-off)=2.0` **(a)-exact**; Behrends–Beri exp-suppression-in-d
**theorem-grade**; which-branch + LRU dephasing **(a)** physics. Leakage=per-round-independent Kraus **(a/b)**
(Miao 2211.04728 bound). Record-faithful-truncation-keeps-the-record **(b)** prediction band (the null).
Carrier/geometry/truncation-criterion **decisions** and thresholds **(c)** gates. All d5/d7 distributional
results **PROVISIONAL**. Supersedes ADR 0010 §Decision-4 (geometry/full-2D) and adds Decisions 3–5;
retains ADR 0010 §Decision-1/-2/-3 + constraint ledger + certification ladder.
