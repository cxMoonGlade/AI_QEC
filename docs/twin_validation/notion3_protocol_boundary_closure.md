# notion-3 (quantum non-classicality of memory) on the passive QEC record — PROTOCOL-BOUNDARY CLOSURE

**Status: CLOSED (literature-grounded protocol boundary), 2026-07-06.** This retires the *notion-3 quantum-memory
**witness** line* (can we certify, on the passive dual-axis syndrome record, that the shared-bath σ⁻ relaxation carries
**genuinely quantum** memory?). The answer is **no — and not because we failed to measure it, but because two
independent, literature-nailed facts make it out of reach at the protocol layer.** Retiring it is a *principled
scope boundary*, and it **sharpens** the simulator's target rather than shrinking it.

This document is a decision/closure record. It builds on nothing new experimentally; it fuses the in-house result
(Control 0b) with two literature premises into a scope conclusion. Epistemic classes per `docs/METRICS.md`:
each premise below is `[paper]` (transcribed) or `[ours]` (project inference); the conclusion is a **(c) heuristic
gate** (a scope/STOP rule), NOT an (a) premise anything is built on.

---

## The question being closed

Does the **passive** dual-axis (X+Z) syndrome **record** produced by our shared-bath GKSL carrier carry a signature
of **genuinely quantum** memory (notion-3), distinguishable from *any* classical multi-time (notion-2) process?

Prior arc state (all recorded in `notion3_relaxation_dualaxis_prereg.md` + memory
[[project-notion3-relaxation-dualaxis-Kz-forgeable]]): the Kolmogorov-violation K and its axis components are
forgeable; the negativity/concurrence **revival** (Control 3b) is RHP **non-Markovianity**, forged by classical RTN
dephasing (**Control 0b**, GATE `CONTROL0B_REVIVAL_FORGEABLE_BACKER_SURVIVES`, sha 1590fd59) and a published fact
(2601.18822: backflow "originates from the kernel's mathematical structure rather than from quantumness per se"). The
only surviving genuine quantum-memory witness is Bäcker's `C♯(t₁) < C(t₂)` (Control 3, single-qubit) — but it is a
**single-time channel-tomography (ACTIVE)** quantity, not a record quantity. So the open question reduced to Flag #1:
**is the quantum memory expressed on the passive record, or only in the active channel object?**

Two premises answer it.

---

## Premise (A) — witnessing quantum memory REQUIRES active interventions; passive observation cannot. `[paper]`

Every literature-grade quantum-memory witness reads an **active, instrument-varying** object, never a passive
outcome record (established in the Flag-0 literature closure, synthesis note
`docs/papers/reading_notes/flag0_quantum_memory_witness_synthesis_prereg.md`):

- **Giarmatzi & Costa, Quantum 5, 440 (2021) [1811.03722]** — quantum memory ⟺ the **process tensor / process
  matrix `W` is entangled** across the temporal cut `A_I | A_O B_I`; a classical-memory process is a **separable**
  `W`. Measuring the witness "only requires performing the CP maps … and does not require full process tomography"
  — but it **still requires performing the interventions**: "an experimenter can intervene on the system, e.g. by
  measuring or transforming it. Each operation can be represented by a completely positive map." A passive record —
  with no output wire being re-prepared/propagated — yields only a classical multi-time **outcome distribution**,
  never `W`.
- **Taranto, Quintino, Murao, Milz, Quantum 8, 1328 (2024) [2307.11905]** — the classical-memory class (CM) is
  defined by **entanglement-breaking (measure-and-prepare) channels inserted between the experimenter's operations**,
  whose classical outcomes are **fed forward** to condition future dynamics; the whole CM-vs-QM distinction is a
  property probed by **varying instruments**. At `N=2` the classical-memory distinction even **collapses**
  (`CM = CDC`) — the genuine separation is an `N≥3`, active phenomenon.
- **Bäcker, Palaparthy, Strunz [2510.19522]** (the applied IBM witness) confirms the direction: its `C♯<C` witness is
  computed from **active state tomography** of a Bell-prepared ancilla-coupled Choi state, and it explicitly **defers
  process-tensor tomography** to future work while conceding the process tensor is "more sensitive in detecting
  quantum memory."

`[ours]` **No source supplies a theorem that a passive multi-time record inherits the CM/QM separation** (Taranto's
`N=2` collapse is evidence *against* it being free). Certifying quantum memory on the passive record is UNGROUNDED —
the standing active-vs-passive gap.

## Premise (B) — standard QEC syndrome extraction PAULI-TWIRLS the noise, erasing coherent + non-unital structure. `[paper]`

The physical readout channel of a stabilizer code — repeated projective stabilizer measurement + reset + Pauli-frame
tracking — is a **restricted, Pauli-twirling instrument**. What it twirls away is exactly the non-classical
structure a quantum-memory witness would need:

- **QMCtwin — Shen et al. [2606.19848]** (`shen_qmctwin_syndrome_blindspots_2606.19848.md`,
  `qmctwin_master_equation_digital_twin_2606.19848.md`): Pauli-twirled Clifford (Stim) syndrome models have **blind
  spots for correlated/coherent noise** — "phase accumulation during the interferometric Z-check measurement is
  **invisible to Pauli twirling**"; "nonunital drift produce[s] ancilla-signal bias/shrinkage that **Pauli twirling
  erases**"; the surviving structure is "**absent or strongly suppressed in the Pauli-twirled Clifford baseline**."
  (User-verified verbatim from the paper: "Pauli twirling diagonalizes the Pauli-transfer representation … erasing
  coherent phase information and phase-sensitive interference"; "For nonunital channels such as amplitude damping, it
  also removes affine drift terms.")
- **Kattemölle, Gulácsi, Burkard [2602.08464]** ("Non-Markovianity induced by Pauli-twirling"): twirling is **NOT a
  clean Markovianizer** — it "both measurement-twirls the coherence AND can **INDUCE** non-Markovianity" (a
  Markovian channel generically acquires a negative Pauli-Lindblad `λ_a` after twirling). So even the residual
  "non-Markovianity" on a twirled record can be a **twirl artifact**, not a physical quantum signature.
- **Wagner, Kampermann, Bruß, Kliesch, "Pauli channels can be estimated from syndrome measurements", Quantum 6,
  809 (2022) [2107.14252]** — a stabilizer code estimates a correlated **Pauli** channel **passively** from its own
  routine syndromes ("uses only measurements that do not destroy the logical information"), but **Pauli-ONLY by
  construction** (the estimand is a Pauli/stochastic channel; coherent / non-Pauli / non-unital structure is
  "outside scope and not syndrome-reachable"). This is the direct statement that the passive syndrome record
  certifies the classical-stochastic (Pauli) description and, by the same token, only that.
- **"The surface code beyond Pauli channels", PRX Quantum 6, 040350 (2025) [2412.21055]** — for the coherent-error
  axis: for any nonzero incoherent component the **logical** noise coherence `⟨|γ_L|⟩ → 0 exponentially in code
  distance d` ("the logical noise thus becomes increasingly incoherent with d"), the post-syndrome effective channel
  is an `X_L` **Pauli** channel, and passive-ensemble measures "cannot detect a conventional QEC error threshold" in
  the coherent limit — i.e. coherent structure is not freely accessible from the passive syndrome record. (Scope:
  general single-qubit X-error / **unital**; the non-unital axis is carried by QMCtwin's affine-drift erasure + the
  σ⁻/leakage notes.)

## Conclusion (C) — the passive QEC syndrome record carries only classical (Pauli / notion-2) noise structure. `[ours, (c) gate]`

From (A) + (B): genuine quantum memory (notion-3) is unreachable at the QEC-protocol layer — **twirled out by the
extraction instrument (B), and, in principle, not passively observable even if present (A).** This is a **protocol
boundary**, not a measurement failure. Our Control 0b + the Flag-0 literature independently reach the same place from
the witness side (every witness is active). **Registered STOP gate: do NOT claim quantum memory is expressed on the
passive syndrome record on the strength of any witness; the notion-3 quantum-witness line is CLOSED.**

---

## Why this SHARPENS the simulator (the boundary is the point)

The same QMCtwin section that establishes the twirl washout (B) also shows the syndrome **retains** structure the
stochastic-Pauli baseline misses: "correlated/coherent-noise proxies … **absent or strongly suppressed in the
Pauli-twirled Clifford (Stim) baseline**," yielding a **positive KL gap** vs the Pauli-twirled model at every
detuning. So the two halves of the record split cleanly:

- **Twirled OUT = notion-3** (coherence / non-unital / quantum memory) → out of the protocol's reach → **legitimately
  parked** (this closure).
- **Retained = notion-2** (classical multi-time correlations / bias / drift the Pauli baseline underweights) →
  **exactly what a faithful simulator must reproduce and a stochastic-Pauli baseline misses.**

`[ours]` The simulator's job is **faithful generation** (including coherent + non-unital mechanisms that shape the
pre-twirl physics and hence the *classical* correlations that survive), **NOT witnessing quantum-ness on the passive
record** — two different things. Its **validity criterion** is therefore, and was always meant to be, **notion-2**:
the passive record's classical multi-time correlations, distinguishable from a matched Markovian/CP-divisible null,
that a stochastic-Pauli baseline cannot reproduce ([[project-cpdiv-notion-hierarchy-passive-record]],
[[feedback-simulator-is-goal-twin-is-next]]). This closure supplies external, literature-grade backing that
**notion-2 is the correct target and notion-3 a principled boundary** — not a gap we failed to fill.

---

## What is retained vs retired

**Retired (this closure):**
- The notion-3 quantum-memory **witness** line on the passive record — CLOSED as a protocol boundary.
- Control 3b's "genuinely quantum" (single-qubit cross-check + 2-qubit) — already RETRACTED (Control 0b): the
  negativity/concurrence **revival** is a non-Markovianity/backflow **diagnostic only**, forgeable by classical NM.

**Retained (still valid, correctly scoped):**
- **Control 3** (`quantum_memory_witness`, `C♯(t₁)<C(t₂)`): a genuine Bäcker witness of quantum memory in the
  **active single-qubit channel object** (rank-2 zero-T AD, C♯=C to 2.5e-8; sufficient-not-necessary; margin ~3e-3
  unverified). A true statement about the *channel*, NOT the record. Not load-bearing for the simulator's record-level
  validity.
- **`quantum_bath/` module**: retained as **forward-simulation infrastructure** — it generates the coherent + σ⁻/
  non-unital shared-bath physics faithfully (the simulator's actual job). The `entropic_memory_witness_*` /
  `_revival_fire` / `negativity` / `von_neumann_entropy` functions (RETRACTED-as-quantum-memory 2026-07-06) were
  **RETIRED 2026-07-07** — removed from the reachable package (record: `retired/quantum_bath/`), a bare backflow
  revival being non-Markovianity, not quantum memory. The genuine `quantum_memory_witness` (C♯<C) stays.
- The record-distance distinguishability (min-TV 0.037–0.19 vs incoherent nulls): valid, but re-labeled as
  **non-Markovianity + collective structure (notion-2)**, not quantum memory.

---

## Next (mainline pivot)

Return to the corrected **notion-2 multi-time legitimacy** line on a realistic source: does the passive syndrome
record's *classical multi-time* structure (differentiable-syndrome NLL / p_ij / process-tensor **outcome** statistics)
exceed a matched Markovian/CP-divisible + stochastic-Pauli baseline? That is the simulator's real validity claim, now
with a literature-grounded boundary on what is legitimately in scope (notion-2) vs out (notion-3). See
[[project-coupled-cycle-teacher-build-state]] (07-04 corrected path) / G1.

## References

- `docs/papers/reading_notes/giarmatzi_witnessing_quantum_memory_process_tensor_1811.03722.md` — premise (A).
- `docs/papers/reading_notes/taranto_hierarchy_multitime_classical_memory_2307.11905.md` — premise (A), N≥3 hierarchy.
- `docs/papers/reading_notes/backer_revealing_quantum_nature_memory_2510.19522.md` — premise (A), witness is active.
- `docs/papers/reading_notes/shen_qmctwin_syndrome_blindspots_2606.19848.md` +
  `qmctwin_master_equation_digital_twin_2606.19848.md` — premise (B), twirl washout + retained notion-2 correlations.
- `docs/papers/reading_notes/kattemolle_nonmarkovianity_pauli_twirling_2602.08464.md` — premise (B), twirl artifacts.
- `docs/papers/reading_notes/pauli_channels_from_syndrome_measurements_q2022_809.md` [2107.14252] — premise (B),
  passive syndrome estimates a correlated Pauli channel and, by construction, only the Pauli part.
- `docs/papers/reading_notes/surface_code_beyond_pauli_2412.21055.md` [PRX Quantum 6, 040350 (2025)] — premise (B),
  coherent axis: logical noise Pauli-izes exponentially in d; passive measures miss the coherent threshold.
- `docs/papers/reading_notes/phase_diagrams_information_backflow_2601.18822.md` — revival = kernel/memory, not quantum.
- `docs/papers/reading_notes/flag0_quantum_memory_witness_synthesis_prereg.md` — the Flag-0 synthesis.
- `outputs/twin_validation/notion3_control0b_classical_nm_negcontrol.py` (sha 1590fd59) — the in-house documented kill.
- `docs/twin_validation/notion3_relaxation_dualaxis_prereg.md` — the arc pre-registration.
