# notion-3 on the passive QEC record — REOPENED universal claim; retained access/scope boundary

> **REOPENED AND NARROWED, 2026-07-13.** The universal physical claim below is retracted.
> A Pauli-twirled simulator baseline is not the physical syndrome instrument, and Pauli-only
> estimability does not prove that every coherent/non-unital mechanism is absent from the record.
> The defensible boundary is an **access/scope** statement: one fixed instrument gives only a
> restricted process, while general classical-versus-quantum memory certification uses a process-level
> tester family. `K` is a measure/omit Kolmogorov comparison, not a quantum-memory certificate. The
> corrected authority is
> [`notion123_taxonomy_literature_closure_2026-07-13.md`](notion123_taxonomy_literature_closure_2026-07-13.md).
> Premise B and Conclusion C below are retained only as historical provenance.

**Historical status (superseded): CLOSED, 2026-07-06.** The text below originally retired the *notion-3 quantum-memory
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

## Narrowed premise (A) — general process-memory identification uses an intervention/tester family `[paper]`

The reviewed process-level quantum-memory witnesses read an **instrument-varying** process object rather than
only one fixed outcome law (established in the Flag-0 literature closure, synthesis note
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

`[ours]` The reviewed sources do not transfer their full CM/QM classification to this project's one fixed
syndrome instrument. That is an **unclosed identifiability bridge**, not a theorem that every possible restricted
record witness is impossible. Process-tensor entanglement is sufficient evidence in the Giarmatzi–Costa scope,
not a complete `iff` classification.

## RETRACTED premise (B) — “standard syndrome extraction universally Pauli-twirls the noise”

> **Retracted 2026-07-13.** The sources below concern Pauli-twirled baselines, Pauli-channel
> estimands, or model-specific/asymptotic logical channels. None proves that the physical syndrome
> extraction instrument universally erases coherent and non-unital structure. Marshall–Kafri and
> Manabe–Suzuki–Darmawan provide published QEC counterexamples in which incoherent approximations
> change detector/LER observables.

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
  outside the estimator's scope). The old text incorrectly converted this estimator boundary into a converse
  theorem about physical syndrome reachability.
- **"The surface code beyond Pauli channels", PRX Quantum 6, 040350 (2025) [2412.21055]** — for the coherent-error
  axis: for any nonzero incoherent component the **logical** noise coherence `⟨|γ_L|⟩ → 0 exponentially in code
  distance d` ("the logical noise thus becomes increasingly incoherent with d"), the post-syndrome effective channel
  is an `X_L` **Pauli** channel, and passive-ensemble measures "cannot detect a conventional QEC error threshold" in
  the coherent limit — i.e. coherent structure is not freely accessible from the passive syndrome record. (Scope:
  general single-qubit X-error / **unital**). This asymptotic logical-channel result does not prove exact finite-d
  record invisibility and does not cover coherent leakage/non-unital dynamics.

## RETRACTED conclusion (C) — “the passive record carries only Pauli/notion-2 structure”

**Historical inference, no longer valid:** From (A) + (B), the old text concluded that genuine quantum memory (notion-3) is unreachable at the QEC-protocol layer — **twirled out by the
extraction instrument (B), and, in principle, not passively observable even if present (A).** This is a **protocol
boundary**, not a measurement failure. Our Control 0b + the Flag-0 literature independently reach the same place from
the witness side (every witness is active). **Registered STOP gate: do NOT claim quantum memory is expressed on the
passive syndrome record on the strength of this fixed-record/protocol-family evidence. Process-level
classification remains out of scope here, not theoremically impossible.**

---

## Historical rationale (not an active theorem)

The QMCtwin comparison shows that its physical model and Pauli-twirled baseline give different syndrome
statistics; it does not establish that the physical extraction itself performs that twirl. The model **retains** structure the
stochastic-Pauli baseline misses: "correlated/coherent-noise proxies … **absent or strongly suppressed in the
Pauli-twirled Clifford (Stim) baseline**," yielding a **positive KL gap** vs the Pauli-twirled model at every
detuning. So the two halves of the record split cleanly:

- **Retracted mapping:** `twirled OUT = notion-3` is not established. Coherence/non-unital reachability and
  process-level quantum-memory certification are different questions.
- **Retained project target:** notion-2 record memory remains one specified Axis-2 target, to be tested against
  declared baselines rather than assumed to be missed universally.

`[ours]` The simulator's job is **faithful generation** of the declared mechanisms and record, not certification
of quantum origin. Notion-2 memory is an additional Axis-2 observable, not the simulator's entire validity
criterion and not a substitute for full-record faithfulness. Keeping notion-3 certification out of scope is a
product boundary; coherent/non-unital mechanisms may still need to be preserved when they affect the record.

---

## What is retained vs retired

**Current scope decision:**
- General notion-3 process-memory certification remains out of the simulator product scope because it would
  require a richer declared access class. This is a scope choice, not a universal physical no-go theorem.
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
