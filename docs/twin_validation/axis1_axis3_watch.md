# Axis-3 Watch — effects provably outside Axis-1 (same-substep joint GKSL) AND Axis-2 (cross-cycle / source / memory)

> **NON-MARKOVIANITY CORRECTION, 2026-07-13.** Historical statements below that a classical
> mixture cannot produce coherence revival, or that revival identifies quantum memory, are too broad.
> Classical RTN reduced-map diagnostics can show BLP backflow. Keep the carrier separation as an
> implementation taxonomy only; quantum-origin claims require process/instrument evidence. Current
> authority: [`notion123_taxonomy_literature_closure_2026-07-13.md`](notion123_taxonomy_literature_closure_2026-07-13.md).

**Status: NOT STARTED — DOCUMENTED ONLY.** This is the finish-plan Step 9 deliverable
(`outputs/axis1_review/CONSOLIDATED_FINISH_PLAN.md` §9; codex round-1 §10; opus round-2 VERDICT).
It records, on the record, each physical effect that **no** Axis-1 construction and **no** Axis-2
construction can represent, and **why** — so the boundary is logged without starting or designing Axis-3.
**No Axis-3 design, no code, no metric, no schedule is opened by this document.**

**Axis definitions used here (from the prereg/ledger trail, verbatim scope):**
- **Axis-1** = the *same-substep instantaneous joint Lindbladian* on the *declared system Hilbert space*:
  one time-local GKSL generator `L = −i[Σᵢ Hᵢ, ·] + Σ_k D[c_k]` per positive-duration substep, with
  **non-negative rates**, applied as one `exp(L·dt)` after Steps 1–5 connected-cluster joining
  (`forward/joint_lindbladian.assemble_substep_channel`; `axis1_mcwf_mps_unraveling_policy_prereg.md` §1).
- **Axis-2** = an *explicit source process* carried as a dynamical degree of freedom (1/f, RTN/TLS,
  phase-burst, temporal-storm HMM), feeding **current-parameter snapshots** into the per-substep
  `Θ(z_t)` fan-out across cycles; cross-cycle / shared-timeline / classical memory
  (`axis2_source_process_prereg.md`; `nonmarkovian_coupling_constraint_ledger.md`). **FROZEN.**

The wall both axes share — and the Axis-3 candidate steps over — is precise and is stated by the
project's own primary source. QMCtwin (arXiv:2606.19848, p.3–4, cached
`docs/papers/.../qmctwin_master_equation_digital_twin_2606.19848.txt:196–203`): a time-local generator
*with temporarily negative rates* "is then no longer in Lindblad form with nonnegative rates, and the
evolution is **not CP-divisible** [44]. An arbitrary such time-local generator need not produce a
completely positive dynamical map [57]." Axis-1 is non-negative-rate GKSL ⇒ **CP-divisible by
construction**. Axis-2 carries a *classical* source DOF ⇒ each realization is still non-negative-rate
GKSL, and the cycle-averaged map is a convex mixture of CP maps (still CP). **Genuine non-CP-divisibility
that survives both is the watch.**

Literature anchors (all cached in-repo; no fetch performed):
- **RHP** — Rivas, Huelga, Plenio, *Rep. Prog. Phys.* (QMCtwin ref [44]; CP-divisibility = Markovianity
  criterion; the RHP non-Markovianity measure). The CP-divisibility definition.
- **BLP** — Breuer, Laine, Piilo, Vacchini, *Rev. Mod. Phys.* 88, 021002 (QMCtwin ref [57]; BLP
  distinguishability-revival measure; "need not produce a completely positive map"). The Markovianity-as-
  information-backflow criterion.
- **Jaschke–Montangero–Carr** arXiv:1804.09796 (`reading_notes/jaschke_..._1804.09796.md`): the Lindblad
  form is *derived* under the **Born–Markov + secular** approximations (§ derivation, txt:82,168–169) —
  i.e. GKSL *presupposes* a memoryless bath; intra-gate bath memory violates the derivation's premise.
- **Gao et al.** arXiv:2605.23385 (`reading_notes/gao_..._2605.23385.md`): a coupler-hosted TLS produces
  *coherent vacuum-Rabi exchange* with the qubit(s) — the concrete physical origin of a structured,
  back-reacting quantum environment on the gate timescale (g̃ up to ~10 MHz, enhanced exactly during 2-q
  gates). Used here only to ground that the candidate is physical, not as an Axis-3 design input.
- **Fowler** arXiv:1308.6642 (`reading_notes/fowler_..._1308.6642.md`): cited only to *exclude* leakage —
  leakage persistence is Hilbert-space enlargement (Axis-1 qutrit/ququart) + cross-cycle (Axis-2), NOT this
  wall.

---

## Candidate A (LEADING) — genuinely non-CP-divisible *intra-gate* bath memory (coherent in-gate environment revival)

**(1) Name.** Within a *single gate* (one substep), the qubit coherently exchanges amplitude/phase with a
structured quantum environment (e.g. a near-resonant TLS in the coupler, Gao 2605.23385) and **partially
re-absorbs it before the gate ends** — an *information backflow* inside the substep. The reduced
system map `E(0→t)` is then **not CP-divisible** on `(0, dt_gate)`: `E(0→t) = V(s→t)∘E(0→s)` requires a
*non-CP* intermediate propagator `V` (RHP/BLP). On binary syndromes this also shows as a
*non-monotone coherence* `|L(t)|` *revival within one gate* (the `nonmarkovian_coupling_constraint_ledger.md`
C5/C10 non-Markovianity witness, here at the *intra-gate* timescale rather than cross-cycle).

**(2) Why Axis-1's time-local GKSL joint generator cannot represent it.** Axis-1 is a *non-negative-rate*
GKSL generator on the *system alone*. By the QMCtwin statement above + RHP, a non-negative-rate GKSL map is
**CP-divisible**, and CP-divisible dynamics are **monotone-contracting** (no distinguishability/coherence
revival). A coherent intra-gate revival *requires* a temporarily-negative rate, whose generator "need not
produce a completely positive map" — outside the Axis-1 admissible set *by definition*. Connected-cluster
joining (Steps 1–5) only widens the *system* support `Σᵢ Hᵢ` / `{c_k}`; it cannot manufacture backflow,
because joining stays non-negative-rate GKSL. Jaschke 1804.09796 makes the same point structurally: the
Lindblad form is derived under **Born–Markov** (memoryless bath); an in-gate revival violates that premise,
so no Lindblad generator on the system Hilbert space reproduces it. (Faithful representation would need the
bath *in* the simulated Hilbert space — a different object, not an Axis-1 generator.)

**(3) Why Axis-2 (cross-cycle parameter snapshots) cannot either.** Axis-2 carries a **classical** source
`z_t` and feeds **per-cycle parameter snapshots** into `Θ(z_t)`. Two independent reasons it misses A:
(i) **Timescale** — Axis-2 is *cross-cycle* (the snapshot is constant within a substep/cycle); A lives
*within one gate*, below the snapshot's resolution, so no current-parameter value reproduces an in-substep
revival. (ii) **Statistics** — even a non-Markovian *classical* Axis-2 source (1/f/RTN) is, per realization,
still non-negative-rate GKSL, and the observed channel is a **convex mixture of CP maps over the source
distribution** (the ledger's C1 "CPTP at all times" + C8a/C8b construction) ⇒ **still CP**, and its
coherence envelope is the *average* of monotone `|L(t)|`'s. Candidate A's revival is **coherent quantum
back-action** (system↔bath amplitude return), not a classical modulation average; a classical mixture
cannot produce a single-realization coherence revival the bath's quantum memory creates. Hence A is outside
the Axis-2 admissible set *as well* — it is the part of "non-Markovianity" the explicit-classical-source
ledger (C2/C4/C5) explicitly does **not** claim to reach (that ledger covers non-Markovian *dephasing from
a carried classical fluctuator*, a strictly weaker object).

**(4) Literature anchor.** RHP (QMCtwin [44]) + BLP (QMCtwin [57]) for the CP-divisibility / backflow
criterion; QMCtwin 2606.19848 p.3–4 for the in-repo statement that the non-CP-divisible time-local case is
*excluded* from its (and our) non-negative-rate GKSL simulations; Jaschke 1804.09796 for the Born–Markov
derivation premise; Gao 2605.23385 (coupler-TLS coherent exchange) for physical provenance only.

**(5) NOT STARTED — documented only. Trigger to justify opening Axis-3.** Open Axis-3 **only if** Steps 0–8
close with a *certified* residual that (a) **survives** Axis-1 connected-cluster joining at the finest
finite-step policy (so it is not the Step-5 finite-step artifact below) **and** (b) **survives** an Axis-2
explicit-source snapshot fit, **and** (c) is **witnessed as a genuine non-CP-divisibility** by an
*independent* RHP/BLP detector (a `|L(t)|`/distinguishability **revival within a single gate**, with a
Markovian/monotone-source **negative control reading ≤ floor** — the ledger C10 false-positive guard,
re-applied intra-gate), **and** (d) the effect is **certified material to decoder-facing records (ΔLER /
record-TV / NLL)** on the declared device, not merely present in the channel. All four must hold; any single
miss keeps the effect inside Axis-1∪Axis-2 or below the materiality floor, and Axis-3 stays closed.

---

## NOT Axis-3 (explicitly excluded — log so they are never mis-filed)

- **Strongly-noncommuting overlapping-support finite-step error (the Step-5 concern, NOT Axis-3).**
  Continuous-time / adaptive jump-time MCWF unraveling for strongly-noncommuting overlapping terms is an
  **Axis-1 finite-step-policy choice** (`CONSOLIDATED_FINISH_PLAN.md` Step 5; `axis1_mcwf_mps_unraveling_
  policy_prereg.md` §2). The *exact* same-substep object is the joint `exp(L·dt)`; any residual is a
  **numerical convergence** issue (Trotter/jump-time error → 0 as microsteps→∞ / event-time exact), **not**
  a physical effect outside the generator. It is CP-divisible at every step. Do not promote it to Axis-3.

- **Leakage persistence across rounds.** Within a gate, leakage is Hilbert-space enlargement (qutrit/
  ququart) — **Axis-1** (`axis1_mcwf_mps_unraveling_policy_prereg.md` §1, `local_dims`). Across rounds, its
  persistence/decay is **Axis-2** (Fowler 1308.6642 multi-round signature; QMCtwin/Suchara cross-cycle).
  Neither is the Candidate-A wall; logged only to prevent mis-filing.

- **Classical non-Markovian source memory (1/f, RTN, temporal-storm, phase-burst).** Coherence revivals /
  temporal correlations *from a carried classical stochastic source* are the **Axis-2 source-layer**
  (`nonmarkovian_coupling_constraint_ledger.md` C2/C4/C5/C10; `axis2_source_process_prereg.md`). Each
  realization is CP, the mixture is CP — representable by Axis-2 snapshots. Distinct from Candidate A's
  *quantum* intra-gate back-action.

---

**Bottom line.** One physical effect is provably outside both axes: **non-CP-divisible intra-gate bath
memory (coherent in-gate environment revival)** — excluded from Axis-1 because non-negative-rate GKSL is
CP-divisible (cannot back-flow within a substep; Born–Markov premise violated), and from Axis-2 because a
*classical*-source snapshot — at the wrong timescale and as a convex mixture of CP maps — cannot reproduce a
*quantum* coherent revival. **NOT STARTED — documented only.** The four-part trigger (survives Step-5
joining; survives Axis-2 snapshot fit; independent intra-gate RHP/BLP revival with Markovian negative
control; decoder-material) is the *only* condition under which opening Axis-3 is warranted.
