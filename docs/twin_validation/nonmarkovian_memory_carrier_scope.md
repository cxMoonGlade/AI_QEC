# SCOPE (theory-first, NO build) — the non-Markovian memory carrier (axis1 status B)

> **HISTORICAL CLAIM FRAME SUPERSEDED, 2026-07-13.** Preserve the explicit-bath implementation scope,
> but do not use the source/reduced-map/record implications below as current authority. BLP/RHP do not
> identify a quantum bath; conditioned GKSL steps do not determine the averaged multi-time map; and
> record reachability needs an instrument-specific bridge. Current authority:
> [`notion123_taxonomy_literature_closure_2026-07-13.md`](notion123_taxonomy_literature_closure_2026-07-13.md).

**Date 2026-07-03. Status: scope-only.** Ratified this round (user, emphatic): the classical
`CoupledCycleTeacher` slice (one classical shared source `z_t` modulating ζ×γφ) **IS AND CAN ONLY
BE SCAFFOLDING**; the **quantum GKSL bath is THE FINAL TARGET** of the coupling simulator. This
document fixes the quantum carrier's scope so its round starts at a prereg, not a search.
**Nothing here licenses code.** The next-round entry step is a full theory-first prereg
(literature pass + registered bands) per the standing discipline; this scope only pins the object,
the boundary, and the gates that prereg must contain.

**Epistemic frame (binding — user correction, 2026-07-03).** There is NO ground truth in this
project: everything produced is **simulation**. The teacher is a noise model we **specify** (we set
its parameters — "controlled" ✓, "known ground truth" ✗). QuTiP / independent-boson closed forms /
the pilot's `mcsolve` are **formal Oracles** — independent REFERENCE COMPUTATIONS of the same
specified model, whose only job is to catch implementation bugs (break circular verification);
they never certify correspondence to physical reality. What the gates certify is (a) the simulator
computes the specified (enlarged-GKSL) model correctly and (b) the records carry that model's
structure — never "records = nature." Physical correspondence enters ONLY at phase C (real Google
data), and even that is data-matching. The simulator's PRODUCT is **LER**; `1−F_e`/RHP/BLP/TV are
internal instruments, not the deliverable.

## 1. The boundary this round establishes (declared, binding on claims)

`CoupledCycleTeacher` (this round) carries **classical parameter memory**: one memoryful classical
source `z_t` (a finite sum of RTNs) modulating per-cycle rates. Its records can show cross-cycle
correlation. Conditional per-step GKSL form does not, by itself, determine CP-divisibility of the
averaged multi-time map; a stochastic source has no reduced-map status before a coupling is declared.
Likewise, coherence revival/CP-indivisibility can occur in classical-noise reduced-map models and is not
an unforgeable quantum-origin signature. No generic “non-Markovian simulator” or quantum-memory claim
may ride on either the classical or explicit-bath teacher without the appropriate map/instrument bridge.

## 2. The object (what the carrier IS)

A carrier whose within-window dynamics couples the register to an **explicit quantum memory** so
the reduced window dynamics breaks CP-divisibility:

- **Form:** pseudomode-enlarged GKSL — window ⊗ (1..M pseudomodes), joint Lindbladian
  `L = -i[H_win + H_mode + H_int, ·] + Σ D[c]` on the ENLARGED space. Key architectural fact: the
  enlarged dynamics is again GKSL, so it is propagated by the **existing, G2-certified**
  `forward.joint_lindbladian.assemble_substep_channel` with no new propagator — the new work is the
  mode register + the interaction grounding, not a new engine.
- **Dissipative-correlation arm:** the M12 Phase-B 2-site joint-collapse seam (built, certified)
  already covers collective/correlated relaxation; the carrier adds the memory-ful (mode-mediated)
  version.
- **Validated methodology to reuse:** the coupled-pseudomode pilot v1 (memory
  `project-coupled-pseudomode-pilot-v1`; `coupled_pseudomode_pilot_prereg.md`) — collective pure
  dephasing embedding GPU-certified vs the independent-boson closed form (2.5e-8) — is the
  embedding+oracle template. The quantum-bath M1/M2 chain (`quantum_bath_slot_prereg.md`) supplies
  the TLS/near-resonant grounding (s_T1 sub-share brackets, D_matched floors, KMS checks) and the
  1q+1-mode → stabilizer-unit build path already sketched in
  `HANDOFF_coupling_simulator_2026-07-02.md` §3.

## 3. Gates the next-round prereg MUST register (theory-first; no run before these are written)

1. **Wedge observable = coherence revival on the source-layer probe first** (G3b machinery,
   `nm_divisibility.rhp_measure`/`blp_measure` + the wedge harness): RHP/BLP > 0 with onset at the
   registered coupling point; a plain Markovian control reads 0.
2. **Motional-narrowing collapse control (hard):** the registered wedge → 0 in the fast-bath limit
   — the pass criterion that kills a mislabeled classical imitator.
3. **Classical-imitator null:** a matched-BCF classical-field twin (the T-L2 instrument line) must
   NOT reproduce the registered discriminator; the discriminator must live where Prop IW-1 permits
   passive records to see it (records are EVEN in the commutator sector; expected home =
   outcome-resolved cross moments / conditional statistics, NOT first-order marginals — the
   observability calculus is a REGISTERED derivation duty of the prereg, not an assumption).
4. **Independent oracles:** independent-boson closed form + JC/`mcsolve` (in-repo, already used by
   the pilot) — never the carrier's own path.
5. **Cost gate:** dense window⊗mode DM cost declared up front (dim 2^n·d_mode per branch); the
   over-cap route (MCWF/MPS arm or window+seam) named BEFORE build, fail-closed otherwise.

## 4. Open questions the prereg must answer (not answered here)

- Mode count / spectral-density bracket (Gao TLS brackets; Dutta–Horn 1/f vs near-resonant TLS —
  which slice-2 mechanism carries the first wedge).
- Attachment point (data-idle T1 sub-share vs CZ-adjacent), per the M1 budget rows.
- Record-level visibility: how much of the source-layer revival survives into `{det,obs}` at
  feasible N (the G0-style pre-build effect-size gate, quantum edition — MANDATORY before any
  teacher-level claim; the classical round's G0 lesson binds).
- Whether the classical `CoupledCycleTeacher` becomes the CONTROL arm of the quantum carrier's
  ablation (shared-classical vs quantum-memory at matched marginals) — the natural G6 upgrade.

**Trigger:** opens after this round's teacher lands (H6-committed) and its gate suite is green.
Sequencing discipline: trigger-gated, not dropped.
