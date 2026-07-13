# SIMULATOR.md — binding spec for `error_coupling_simulator`

The authoritative contract for the project: **what the simulator is, its object, its
boundary, its carrier ladder, and the disciplines every change obeys.** When any other
doc disagrees with this file, this file wins.

## What it is

`error_coupling_simulator` is a **faithful, GPU-first simulator of QEC error mechanisms**
— coupling, leakage, and other non-Pauli / memory-ful noise. It takes a QEC circuit (a
rotated surface code — **XZZX** is the first target) plus a **specified noise process**,
and produces the **multi-time syndrome RECORD** (per-round detector bits +
logical-observable flips, emitted as Stim-compatible `.b8` / `.dem` artifacts). It is a
standalone, independently-releasable package, importable as `import error_coupling_simulator`.

The deliverable is the simulator itself. Its product is the **record** (and the LER read
off it under a frozen decoder); metrics are **instruments** on that record, never the
object.

## Object contract

- **A noise process = a noise model we SPECIFY** (not a fit to hardware). A noise process
  applies declared error mechanisms to the circuit and emits records, carrying its own
  ground truth (evaluator-only). It is the true generative process — richer than, and
  **not** identified with, a **DEM** (a DEM is a decoder-facing reduction of it).
- **Two noise axes:**
  - **Axis-1 — within-substep joint-Lindbladian coupling.** ZZ crosstalk, T1/T2,
    thermal excitation, fSim residual, readout dephasing, and leakage Hamiltonians are
    assembled into one joint generator per substep and exponentiated
    (`carrier/joint_lindbladian.py`); the frontend lowers a compiler schedule into these.
  - **Axis-2 — notion-2 classical multi-time record memory.** A shared classical latent
    trajectory `z_t` / `ξ(t)` (a microscopic 1/f bath or an RTN) conditions per-round
    error rates `p_r = clip(p₀(1+κ·ξ_r))` across QEC cycles (`source/`), leaving a
    **beyond-Markov signature in the passive syndrome record**. This is **classical**
    multi-time memory — Gaussian 1/f is CP-divisible (`γ=½∫C≥0`, RHP=BLP=0), so its
    legitimacy is **notion-2, not notion-1**. **notion-1** (CP-divisibility-breaking
    quantum non-Markovianity) is **not reachable** in the passive record — it is twirled
    out, appearing only as its notion-2 shadow — and is **not** a carrier target.
    **notion-3** (genuine quantum-bath backaction; the pseudomode/GKSL line) is **out of
    scope.**
- **Non-Pauli character (spans both axes).** The mechanisms are frequently non-Pauli — not
  just **leakage** (qutrit `|2⟩` / ququart `|3⟩` transport; WG leakage; LRU/DQLR reset),
  but also **drift** (slowly-varying coherent over/under-rotation / axis drift),
  **crosstalk** (coherent ZZ coupling, correlated errors), and **burst** (correlated-in-time
  error bursts). These carry coherence / structure a Pauli-rate vector cannot, and are
  **not DEM-reducible** — hence the coherence-capable channel object + the non-Pauli carrier.
- **The record is the product; the carrier is an implementation.** Feasibility and
  faithfulness gate on the **record** (multi-time syndrome statistics), **never** on a
  carrier bond dimension, state fidelity, or a 2-point TV. This is binding (ADR 0011).

## Boundary / disciplines (binding)

- **No physical ground truth.** A noise process is a model we specify; the oracles
  (QuTiP-derived channels, closed forms, the exact density-matrix engine) are **FORMAL
  bug-catchers** — implementation-correctness references, never "validated against
  reality." No claim of correspondence to a real device is made from a noise process.
- **Evaluator-side isolation.** The noise process's truth — source trajectory `z_t`, the
  channel field, per-substep mechanism params — is **evaluator-only** (reachable via
  `.truth` / `CertReport.truth`), and is **never** in the emitted record payload.
  `certify/` reads that truth to SCORE against independent anchors; nothing downstream of
  the record may see it.
- **GPU-first.** Model compute is GPU-only (no `cuda if available else cpu`); target
  workstation ≥ RTX 5090. CPU-only results are not evidence of a GPU-path failure.
- **Numerical floor.** `error_coupling_simulator.numerics` — `1e-12` for float
  floors/thresholds only; never for structural zeros (Pauli entries, bit values, integer
  indices, exact algebraic identities).

## Carrier ladder (forward propagation)

The forward engine scales through a ladder; the object + record contract are
backend-agnostic across it:

1. **Exact density matrix** (`carrier/exact/{qutrit_dm,circuit_sim}.py`) — feasibility-only
   (≤ ~15 qutrits; d3 DM ≈ 6.2 GB fits, d5 DM is dead). This is the **certification
   ORACLE**, not a scaling path.
2. **MPS MCWF, thin-strip** (`quimb`; snake/boustrophedon along the short dimension) —
   χ small and **constant in d** for a `w×d` strip (ADR 0010). Pure-state quantum
   trajectories; ensemble mean = the exact mixed evolution.
3. **2D PEPS, full `d×d`** (`carrier/peps/`) — the **active frontier** (ADR 0011). A 1D
   MPS **cannot** carry the full `d×d` surface code (snaking the square hits a bond wall
   `χ ~ 2^{2d}` — geometry-incompatible), so the full-code carrier is a single-wire 2D
   PEPS pure-state MCWF trajectory. The doubled-wire DM-PEPO (`carrier/pepo/`) is closed.

**Truncation is RECORD-faithful** (ADR 0011): the carrier drops what is absent from the
record (e.g. the coherent leakage tail carries zero bipartition entanglement and never
enters a syndrome-bit probability), keeping the per-edge bond at the Clifford area-law
scale. The per-edge bond is a resource guard only. **Current frontier problem:** the
FET/ALS truncator is unreliable on long-range (loop) correlations; the fix is the
deterministic Evenbly-2018 closed-loop gauge-fix (WTG) canonical-spectrum truncation
replacing the ALS (`carrier/peps/fet.py`; see `docs/nonpauli_teacher/HANDOFF_fet_*`).

## Certification / faithfulness

- **Independent ground truth (FAITHFULNESS_PROTOCOL rule I).** Verify a carrier against
  ground truth INDEPENDENT of its implementation (raw `.stim` artifact, a from-scratch
  reconstruction, a closed-form theorem, or the GF(2) stabilizer entropy) — never against
  the engine's own oracle.
- **Rung ladder** (`certify/`): channel-level Choi/PTM/CPTP → d3 record distribution vs
  the DM oracle (TVD/KL/marginals) → d3 Bayes floor vs DM → χ-convergence curve →
  **d5/d7 oracle-free internal checks only** (CPTP residual, structural pins,
  χ-convergence self-consistency).
- **Memory-axis faithfulness instrument (notion-2).** That the passive record carries the
  specified multi-time memory is scored by the record's **absolute multi-time Markov-order
  structure** vs a genuinely-Markov-order-k generative null — CMI `I(mᵣ;mᵣ₋₂|mᵣ₋₁)` +
  Anderson–Goodman `G²` + the `E(k)` residual-energy statistic. This is a **discriminability
  instrument, never a parameter-recovery learner** (fitting `θ` from the record is the
  active-QNS / recovery access class, out of scope).
- **Every d5/d7 distributional claim is PROVISIONAL** — reportable and usable for
  go/no-go gating, but never a premise for a definition, derivation, or further
  conclusion.
- **Negative controls are first-class and non-optional** (an inert control forces FAIL);
  feasibility is data (an anchor that would OOM reports `feasible=False` and the core
  routes to the carrier, never allocating the infeasible DM).

## Preserved architectural decisions

Folded in from the project's decision history (the surviving, still-load-bearing core):

- **GPU-first execution** — run *on* the GPU (quimb/torch/CUDA kernels), not
  hand-rolled kernels where a library suffices.
- **The channel object is a CPTP Stinespring-dilation channel** (Hermitian generator →
  isometry → Kraus), CPTP-by-construction, any `dim`, **non-Pauli / non-Clifford capable**
  (a Pauli-rate vector cannot carry coherence). The one backend-agnostic seam is the
  `field(t,i) → Kraus` callable, applied by an **arity-general** (`[i]` or `[i,j]`),
  **dim-general** local-apply kernel — adding 2-body edge DOF slots is a bounded wiring
  change, not a rebuild. The channel object + record contract survive a carrier swap.
- **The d5/d7 rotated surface-code target.** The end goal is a faithful d5/d7 XZZX
  surface-code noise process (d3 = 17q already exceeds the ~15q exact wall, d5 = 49q,
  d7 ≈ 97q), which is what puts the scalable carrier on the critical path. `do()` remains
  a channel-level, parameterization-independent transform scored on the record, never an
  edit of a mechanism-native parameter.
- **Field-standard metric ledger.** Score with the QEC-standard instruments — `ε_d`
  (logical error per round), `Λ` (error-suppression factor), detection-event fraction,
  pij-matrix agreement, held-out per-shot syndrome NLL, `%ΔLER` under a frozen named
  decoder (PyMatching) — never a silent non-standard stand-in (`docs/METRICS.md`).
- **Tool I/O contract.** Stim-native in (`.stim` / `.b8`), standard `.dem` out;
  pip-installable; no bundled decoder, no new formats.

## Frontend / product surface

`CodeSpec → CircuitIR`, imported Stim circuits, and hand-built `CircuitIR` all feed one
`Simulator.run(...)` surface (`frontend/`), which emits `.stim` / `.dem` / `.b8` /
manifest artifacts. Every artifact declares a `representability` class and **fails
closed** — Stim-Pauli noise, source-projection, joint-L channel evidence, and analog
schedule metadata are distinct, never silently conflated. `.stim`/`.dem` are not analog
joint-Lindbladian truth, leakage truth, or shared-source non-Markovian truth. XZZX is the
first target code spec, not a hard-coded simulator core.

## Working disciplines (every change obeys)

- **Theory-first** — the physics/math derivation and the predicted outcome (direction,
  scaling, threshold) are written down BEFORE the run; experiments verify predictions.
- **Faithfulness protocol** (`docs/FAITHFULNESS_PROTOCOL.md`) — independent ground truth;
  a constraint ledger + a falsifying test each, written before building; declare and
  BOUND every simplification (unbounded ⇒ STOP).
- **Epistemic-status declaration** (`docs/METRICS.md`) — every quantitative item is
  (a) exact / (b) prediction band / (c) heuristic gate; undeclared defaults to (c);
  provisional conclusions may gate but may not be built upon.
- **Metric discipline** — score every claim with a field-standard metric via the forced
  ladder in `docs/METRICS.md`.
- **Scripted-execution** — every code run is a committed script (precondition asserts +
  printed evidence + flushed output + `__main__` guard for multiprocessing); the only
  inline-shell exception is trivial read-only inspection.
- **Baseline discipline** — `external/baselines/` stays PRISTINE (never modified);
  adapters live in our tree.
- **`src/**` commits are explicitly user-confirmed**, one reviewed diff per phase.

## Notation

`d` code distance; `χ` bond dimension; `ε_cut = Σ_{i>χ} σ_i²` per-cut discarded weight;
`C_L` leakage coherence; `z_t` / `ξ(t)` the shared Axis-2 classical source trajectory; the
record = per-round `{detector bits, observable flips}`. A **noise process** = a specified
noise model that emits records (with evaluator-only truth); a **DEM** = the decoder-facing
detector-error-model reduction (never the object); an **anchor** = an independent
ground-truth reference; the **carrier** = the forward engine. **notion-1/-2/-3** = the
memory taxonomy (CP-div-breaking quantum / classical multi-time record / quantum-bath).

## Local reference tooling

- **RAG (literature search)** — `python -m qec_twin.rag.store --query "<q>"` (rebuild:
  `--build --force`); ChromaDB over the `docs/papers/reading_notes/` 精读 notes (~2230
  chunks). The query basis of the `theory-first` / `theory-fix` skills.
- **KG (knowledge graph)** — `python outputs/knowledge_graph/kg_query.py` (concept /
  relation traversal; `kg.json` / `kg_full.json`, local-only). The other `theory-first` /
  `theory-fix` grounding source.
- **Code map** — `docs/CODE_MAP.md` (AST-derived `src/` inventory + `code_status.json`
  status overlay); regenerate `python tools/gen_code_map.py` (staleness: `--check`).
- **Test codebook** — `tests/CODEBOOK.md`: the L0 structural / L1 property (Hypothesis) /
  L2 mutation (mutmut) coverage harness (`tests/harness/`). Read before touching a batch.

## Key documents

- **Architecture:** `docs/ARCHITECTURE.md`; per-module `src/error_coupling_simulator/**/README.md`;
  `docs/CODE_MAP.md` (generated inventory).
- **Decisions (live):** `docs/adr/0008` (scalable-carrier charter) · `0009` (Bayes-TN
  posterior spine) · `0010` (non-Pauli leakage MCWF-MPS carrier) · `0011` (record-faithful
  truncation on the 2D PEPS carrier).
- **Live working notes:** `docs/nonpauli_teacher/` (the PEPS/FET carrier line + handoffs).
- **Protocols:** `docs/FAITHFULNESS_PROTOCOL.md`, `docs/METRICS.md`.
- **Migration provenance:** `docs/error_coupling_simulator_MIGRATION.md` (how the package
  was consolidated).
