# ADR 0011 — Single-wire 2D-PEPS geometry; record-faithful truncation reopened

## Status

**Partially accepted (decision 2026-07-12; theory-fix reopened 2026-07-13).** The full `d×d`
geometry amendment remains accepted. Decisions 3 and 5 and the leakage truncation criterion are
**suspended**; ADR 0010's MCWF-trajectory forward, frozen per-round-independent (LRU) leakage model,
and certification ladder otherwise stand.
Historical inputs were the zoom-out territory map (2026-07-12, wzb623wrz), the now-reopened crux
predecessor (`CRUX_RESOLVED_bond_is_gauge_artifact_2026-07-11`), the build-first ZMT f-gap
diagnostic (2026-07-12), and the mainline framing (`project-simulator-p0p4-plan-framing`,
`project-leakage-lru-const-memory-notion2shadow`). Exact local artifact facts remain useful, but
their bridge to bounded-bond/full-record faithfulness is open; the operational truncation gate is a
registered prediction band, not theorem-grade.

> **THEORY-FIX REOPENED (2026-07-13): Decisions 3 and 5 are SUSPENDED.** The full literature audit
> is [coherent_leakage_longrange_truncation_literature_closure_2026-07-13.md](../nonpauli_teacher/coherent_leakage_longrange_truncation_literature_closure_2026-07-13.md).
> Published evidence does not support a universal coherent-tail record null, `L1/L2` sufficiency, or
> deterministic WTG top-spectrum truncation as a general loopy solver. The geometry decision and the
> rule “validate on the record, not the bond” remain useful; dropping coherence and replacing FET/ALS
> do **not** proceed until the exact instrument/record bridges close.

## Context

- **ADR 0010 is superseded on two points that were written for the wrong geometry / wrong instrument.**
  ADR 0010 §Decision-4 registered the leakage scaling forward as a **thin-strip (w×d) MCWF-MPS snake**
  and **deferred full `d×d` as a research risk**. But the actual d5/d7 target is the **full `d×d` rotated
  surface code**, whose 2D geometry can force a 1D snake to `χ=2^{Θ(d)}` across a square-code cut
  in the worst/project-estimate regime; this is a scaling risk rather than a universal exact formula
  ([binding carrier boundary](../SIMULATOR.md)). The doubled-wire **DM-PEPO** carrier was also **closed/archived**
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
  representation cost that can contain loop/gauge redundancy but may also be required for physical
  accuracy. It is not itself an observable or the product's validity target (the multi-time syndrome
  RECORD is), and it moves with the truncation policy.
  Optimizing a moving artifact alone has no claim-level acceptance target. The carrier bond and DEM
  are not validity substitutes; a frozen decoder/LER can be a downstream record metric, but cannot
  replace the distributional record-faithfulness ladder.
- **[REOPENED PRIOR ARGUMENT] The coherent leakage tail was assumed not to be a record observable.** Four earlier anchors were:
  (i) **artifact interpretation corrected 2026-07-13** — the d3 leakage-ON run requested
  `N_traj=6, R=4`, but all six trajectories raised `BondAbortError` after their sole recorded round.
  At R1 the exact `dense_psi` bipartition entropy was `2.000000369882518` ebits versus the codestate
  baseline `2.0`, a difference of about `3.70e-7`; the `2e-16` equality belonged to a different
  leak-off/GF(2) control. The artifact therefore shows a near-baseline **R1** value with Schmidt rank
  29, not zero added entropy, exact identity, or multi-round stability. Its embedded `CONFIRMED`
  verdict is invalidated by its own fields. (ii) **which-branch** — the ancilla
  CZ+projective-Z is a leak-flag measurement, so the joint syndrome distribution is a classical mixture
  `|α|²P(·|unleaked)+|β|²P(·|leaked)`; the `C_L` off-diagonal never enters a syndrome-bit probability.
  (iii) **LRU/DQLR** resets `|2⟩` each cycle, dephasing the `|1⟩–|2⟩` coherence between rounds → a diagonal
  population flag. A flag is notion-2 only if it induces multi-time dependence in the record. (iv)
  **bounded adjacent evidence, corrected 2026-07-13** — Behrends–Béri 2412.21055
  (PRX Quantum) reports numerical plus phenomenological exponential suppression of a
  **syndrome-conditioned logical-channel coherence** with code distance for a local independent
  single-qubit X-error product channel whenever an incoherent component is present. It is not a
  theorem about qutrit leakage, a noisy repeated-extraction record, physical 2D PEPS entanglement,
  or truncation error; it therefore does not imply that the d5/d7 coherent leakage tail is
  exponentially small. The `pauli_channels_from_syndrome`, STA 2312.10277, and QMCtwin 2606.19848
  sources likewise address different bounded objects rather than supplying that missing bridge.
  The earlier inference that this fixes all leakage record content to notion-2 is retracted:
  coherent leakage is first a channel→instrument→record reachability question, not a
  memory-taxonomy result.

## Decision

1. **The full-`d×d` surface-code leakage scaling forward carrier = the single-wire 2D PEPS**
   (pure-state MCWF trajectory; dim-3 physical leg; per-round leakage Kraus). MPS is retained ONLY for
   genuine thin strips (ADR 0010's w×d regime, where bounded χ is conditional on fixed width,
   evolution depth/noise regime, and accuracy); **MPS-on-full-`d×d` and
   the DM-PEPO are CLOSED** (geometry wall / path-bond concentration). ADR 0010's MCWF-exactness,
   LRU leakage model, LPDO floor, and certification ladder are UNCHANGED.
2. **Leakage stays the per-round-independent local Kraus flavor, applied on the carrier's qutrit legs**
   (ADR 0010 §Decision-2/-3; current reachability boundary in the
   [literature closure](../nonpauli_teacher/coherent_leakage_longrange_truncation_literature_closure_2026-07-13.md)). At d3 this is the fast
   dense SV kernel (`sv_traj_d3` loader); at d5/d7, where no dense state exists, the SAME per-round Kraus
   is applied on the PEPS legs. Per-round independence means this source is not notion-2 by itself.
   Whether its coherent tail is passive-record-reachable is **open and schedule/model dependent**
   (2026-07-13 closure packet), independently of the notion-1/2/3 taxonomy.
3. **[SUSPENDED 2026-07-13] Leak-ON truncation was proposed as RECORD-faithful rather than
   state-/bond-faithful.** The earlier inference that zero added bipartite entropy implies absence from
   the record is invalid: a local coherent channel can change a later measurement distribution without
   changing this entropy. The carrier therefore does **not yet have license to drop** the
   leakage-dressed continuum or keep the per-edge bond
   bounded at the leak-OFF Clifford area-law scale. **Faithfulness gates on the full joint RECORD law**
   using the Validation ladder below, **never on `bond=4`, state fidelity, or selected moments alone.**
   CMI/G²/`E(k)` are additional diagnostics only when a notion-2 memory claim is made; they cannot
   decide coherent-tail equivalence. The per-edge bond is a resource guard only.
4. **[REOPENED 2026-07-13] The leak-ON FORK-B (stabilizer-frame carrier + qutrit-Z₃ extension) /
   FORK-C (bounded-larger bond + saturation gate) decision remains unresolved.** Bond size alone is
   still the wrong scientific target, but suspended Decision 3 no longer dissolves the representation
   question. The stabilizer-frame
   and classical-flag/Pauli+ machinery (2403.08724 / 2511.06672 GCAMPS-qudit / Google Pauli+ 2207.06431 /
   the `leaky` lib) remain **parked contingencies** until the explicit physical-instrument comparison
   closes. The existing per-slice custom-statistic diagnostic is not that gate (see Validation).
5. **[REOPENED 2026-07-13] The leak-OFF Clifford d5/d7 per-edge-bond truncation is a parallel engineering item, not
   mainline-gating.** The Clifford backbone is area-law (bounded per-edge bond by construction), but the
   local simple-update truncation may over-count loop+gauge directions (SW-S6). Evenbly's WTG is a
   proven optimal direct truncation only at zero cycle entropy, with a heuristic near-optimal
   regime when it is small. At nonzero cycle entropy the direct argument fails and the paper
   proposes iterative FET; it does not prove FET is the unique possible solver.
   Sokolov–Zhang–Dziarmaga ZMT removes exact zero modes and supplies an initialization, followed in
   every example by variational optimization. Neither source licenses replacing ALS/FET or gating
   scientific validity on **S_A saturation**
   (physical entanglement), and a miss is adjudicated inside the registered WP1 menu, not a
   mainline-science reversal.

## Validation (the gate for Decision 3, before any d5/d7 claim)

- **The record faithfulness comparison (redesigned; prior “fork-closer” status withdrawn).** On d3 XZZX in the
  weak-LRU regime (`leak_mass~1e-3, C_L~0.2`), generate the record TWO ways — (A) the coherence-carrying
  qutrit forward (exact within the frozen, explicitly specified instrument model) and (B) the
  tail-dropped / classical-flag SV-kernel record —
  and score their **full joint `(detectors,obs)` record law** with exact-enumeration TV/KL where
  feasible, plus held-out generative NLL and frozen-decoder LER as separate rungs. CMI and selected
  detector/pair moments are diagnostics, not substitutes for distributional equality. The record
  coordinate must be verified at `R>=2`: raw syndrome `s` is folded into detector events
  `d[0]=s[0]`, `d[r]=s[r] XOR s[r-1]`, with a positive control and a deliberately unfurled/scrambled
  negative control ([metric guard](../METRICS.md)). The instrument
  must include or independently validate the physical ancilla/CZ/measurement dynamics, via a committed script (asserts
  + printed evidence + `__main__` guard). **PASS** licenses dropping the tail only for that frozen
  channel, schedule, metric ladder, and accuracy band; it is not a universal theorem and does not by
  itself classify notion-1 or notion-3. **FAIL** (the tail is
  record-distinguishable) ⇒ Decision 4's parked contingency unparks and the coherent tail becomes a
  first-class carrier target.
- **Binary output is not a no-go.** Published exact-vs-STA simulations already show coherent-channel
  differences in binary detector marginals/LER. Soft/analog readout would add access, but is not the
  only possible re-opener.

## Alternatives considered (rejected, with reason)

- **MPS on the full `d×d` surface code** — a 1D snake can require `χ=2^{Θ(d)}` across a
  square-code cut in the worst/project-estimate regime; retained only for thin strips unless a
  target-regime convergence study proves otherwise.
- **Doubled-wire DM-PEPO** — compiled weight-4 √Eₛ POVM concentrates onto fresh path bonds via ket⊗bra
  squaring (F-SEL-1/F-REC-1); closed/archived.
- **Hold or drop the coherent leakage tail** — unresolved until the frozen record bridge closes; neither
  bond growth nor an `L1/L2`-matched custom-moment result decides the physical carrier requirement.
- **Gate feasibility on the per-edge bond (`bond=4`, ZMT f-gap, state fidelity)** — a gauge-dependent moving
  artifact, not the product's validity target; the record gate above is the validity target.

## Consequences / open risks (honest)

- **The record-faithful-truncation premise is an open prediction.** The prior local experiment found a
  difference between two implemented channels, but its data-only compiled instrument, per-slice
  dephasing intervention, and selected-moment statistic do not make the result physically definitive.
- **d5/d7 remains oracle-free / PROVISIONAL** (ADR 0010 Rung-d5/d7 unchanged). Any future extrapolation
  first requires the redesigned d3 full-record gate; internal χ-convergence and `S_A` saturation alone
  cannot authorize it. No d5/d7 distributional claim is a premise.
- **The leak-OFF Clifford solver (Decision 5) is genuinely unresolved engineering.** The WTG/ZMT/FET
  literature boundaries are now read, but their mapping to the implementation and to a record certificate
  is unresolved; this remains decoupled from the leak-ON physical question.
- **Binding the LRU / per-round-independence assumption to the specific R2-lite Google XZZX dataset**
  (residual-efficiency bound; carryover on platforms with weak DQLR) is a standing theory-first pin (ADR 0010
  open risk, unchanged).

## Epistemic-status audit

The leak-on R1 value `S_A=2.000000369882518` versus baseline `2.0` is an **(a)-exact local artifact
fact**; all six requested R4 trajectories aborted after R1. It is neither an exact equality nor a
record theorem.
Behrends–Béri supplies published numerical + phenomenological evidence for logical-coherence
suppression in its X-only product-channel model, not a theorem or a leakage/record/truncation bridge;
which-branch/LRU arguments are schedule/model assumptions. “Leakage is a per-round-independent
Kraus draw” is class **(a)** only as a frozen model definition; its finite-sample record effect is a
separate class **(b)** quantity and is currently open.
Record-faithful truncation remains an **open (b) prediction**.
Carrier/geometry/truncation-criterion **decisions** and thresholds **(c)** gates. All d5/d7 distributional
results **PROVISIONAL**. Supersedes ADR 0010 §Decision-4 (geometry/full-2D) and adds Decisions 3–5;
retains ADR 0010 §Decision-1/-2/-3 + constraint ledger + certification ladder.
