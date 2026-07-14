# SIMULATOR.md — binding spec for `error_coupling_simulator`

The authoritative contract for the project: **what the simulator is, its object, its
boundary, its carrier ladder, and the disciplines every change obeys.** When any other
doc disagrees with this file, this file wins.

## What it is

`error_coupling_simulator` defines and builds toward a **faithful, GPU-first simulator of QEC error mechanisms**
— coupling, leakage, and other non-Pauli / memory-ful noise. It takes a QEC circuit (a
rotated surface code — **XZZX** is the first target) plus a **specified noise process**,
and produces the **multi-time syndrome RECORD** (per-round detector bits +
logical-observable flips, emitted as `.b8` shot data or represented by its joint law). A `.dem`
is an optional decoder-facing reduction/model artifact, not the record. The package is importable
as `import error_coupling_simulator` and has no inward runtime dependency on `qec_twin`.
Built wheel/source archives are allowlisted to this package alone and export no legacy entry
point. The repository still keeps outward `qec_twin` compatibility shims and the local
`qec_twin.rag` literature tool for existing workspace consumers; neither is shipped or imported
by the simulator distribution.

The deliverable is the simulator itself. Its product is the **record** (and the LER read
off it under a frozen decoder); metrics are **instruments** on that record, never the
object.

**Product non-goals.** The simulator does not fit a channel/noise model from records, choose
between model classes, define a calibration-probe ladder, recover hidden parameters, or construct
parameter-uncertainty/identifiability bands. Those are downstream inference tasks and cannot serve
as simulator acceptance gates. The Bayes decoding floor and decoder-headroom analysis are likewise
downstream analysis: their implementations remain under `legacy/qec_twin/audit/`, are not shipped,
and are not a simulator certification rung. Evaluator-only parameters exist to define and certify
the specified generative process; they are not targets of an in-package learner.

## Object contract

- **A noise process = a noise model we SPECIFY** (not a fit to hardware). A noise process
  applies declared error mechanisms to the circuit and emits records, carrying its own
  ground truth (evaluator-only). It is the true generative process — richer than, and
  **not** identified with, a **DEM** (a DEM is a decoder-facing reduction of it).
- **Detector semantics are enforced at the active package boundary.** The record uses temporal
  detector events, not raw stabilizer outcomes. `carrier.records.RecordBatch.det` is the common
  emitted-record contract. The PEPS packed carrier keeps raw round-major syndromes only as its
  internal byte layout; `PackedShotBatch.to_det_obs()` / `.to_record_batch()` apply the pinned
  `R>=2` temporal XOR fold, while `.to_raw_syndrome_obs()` is the explicit diagnostic accessor.
  The old `qec_twin` `ShotSet` remains a legacy, nonconforming type and is not the package record
  boundary. See `docs/METRICS.md` and `docs/NUMERICAL_PROVENANCE.md`.
- **Two noise axes:**
  - **Axis-1 — within-substep joint-Lindbladian coupling.** ZZ crosstalk, T1/T2,
    thermal excitation, fSim residual, readout dephasing, and leakage Hamiltonians are
    assembled into one joint generator per substep and exponentiated
    (`carrier/joint_lindbladian.py`); the frontend lowers a compiler schedule into these.
  - **Axis-2 — notion-2 classical multi-time record memory (core simulator service).**
    `source/` owns a replayable classical latent timeline, its `Theta(z_t)` mechanism-parameter
    fan-out, and matched-marginal controls. `OneOverFDriftSource` is a finite-band construction:
    a finite sum of log-spaced independent RTNs whose sum-of-Lorentzians PSD approximates 1/f
    over the declared band. It is a **classical stochastic non-Markovian record-memory model**,
    not a microscopic or quantum bath. The source conditions per-round error rates
    `p_r = clip(p₀(1+κ·ξ_r))` across QEC cycles, designed to leave a **beyond-Markov signature
    in the declared passive record policy**. The positive-exponential-covariance **Gaussian surrogate** is
    CP-divisible by project algebra (`γ=½∫C≥0`, RHP=BLP=0), but the production
    `OneOverFDriftSource` is an explicit finite sum of eight RTNs, not that Gaussian reduced
    map. Neither the source timeline nor its 1/f label carries a CP-divisibility or
    quantum-bath claim. Under two separately declared
    free-induction diagnostic lifts (continuous CTMC and cycle-held), an exact registered and
    independently reproduced product/256-state gate finds BLP backflow for the defaults. Its first
    run preceded the prediction document's Git commit, so it is not audit-pristine preregistration.
    Production instead fans `z_t`
    into several mechanism parameters, so its coupled QEC map and syndrome record still have
    **no notion-1 verdict without the missing channel/instrument bridge**. Only the frozen
    fixed-horizon record policy has current notion-2 evidence; this is not a generic process-wide or
    causal-family certificate. No notion-1-zero or notion-1-positive claim is made for the production path.
    This statement does not cover every process called Gaussian or 1/f. Here
    **notion-1** groups reduced-map divisibility (RHP) and distinguishability backflow
    (BLP), which are distinct diagnostics; neither is itself a quantum-bath certificate, and
    the fixed record does not identify it without an explicit channel-to-instrument bridge.
    **notion-3** means quantum memory/backaction at the environment/process-tensor level;
    certifying it generally requires instrument-varying/active access and is out of scope.
    Neither boundary says that every coherent or non-unital mechanism is twirled out of a
    fixed syndrome record; physical reachability remains channel- and schedule-dependent. See
    `docs/twin_validation/notion123_taxonomy_literature_closure_2026-07-13.md` and
    `docs/twin_validation/finite_rtn_exact_cpdiv_result_2026-07-13.md` for the
    claim-by-claim evidence gate and bounded diagnostic result.
    **Current implementation boundary (2026-07-13):** the dense production process lowers only
    source-modulated `zz_zeta_radns` and `gamma_phi_per_ns` into the per-round channel. Its
    readout/reset probabilities are formed from the whole-horizon trajectory mean, so the current
    record is a fixed-horizon, path-conditioned policy rather than a demonstrated causal,
    prefix-consistent notion-1 map family. The static data-qutrit XZZX leakage process is a separate
    implementation island. Their complete bridge is `open / CODE_BLOCKED`; see
    `docs/twin_validation/production_rtn_and_leakage_bridge_split_literature_closure_2026-07-13.md`.
- **Non-Pauli character (spans both axes).** The mechanisms are frequently non-Pauli — not
  just **leakage** (qutrit `|2⟩` / ququart `|3⟩` transport; WG leakage; LRU/DQLR reset),
  but also **drift** (slowly-varying coherent over/under-rotation / axis drift),
  **crosstalk** (coherent ZZ coupling, correlated errors), and **burst** (correlated-in-time
  error bursts). These can carry coherence / structure a fixed nonnegative Pauli-rate vector cannot,
  and are **not in general exactly/losslessly representable by a fixed nonnegative Pauli DEM** —
  hence the coherence-capable channel object + the non-Pauli carrier. Special channel-, schedule-,
  or instrument-specific reductions remain possible and must be proved rather than assumed.
- **The record is the product; the carrier is an implementation.** Feasibility and
  faithfulness gate on the **record** (multi-time syndrome statistics), **never** on a
  carrier bond dimension, state fidelity, or a 2-point TV. This is binding (ADR 0011).

## Boundary / disciplines (binding)

- **No physical ground truth.** A noise process is a model we specify; the oracles
  (QuTiP-derived channels, closed forms, the exact density-matrix engine) are **FORMAL
  bug-catchers** — implementation-correctness references, never "validated against
  reality." No claim of correspondence to a real device is made from a noise process.
- **Numerical provenance is mandatory.** Every claim-bearing physical number must declare
  one provenance kind: `paper-measured`, `paper-derived`, `dataset-measured`,
  `calibrated-to-paper`, `project-design`, `convenience-default`, or `numerical-only`.
  A paper-backed row carries an exact page/figure/table/equation pointer, units and scope;
  a transformed value additionally carries the complete conversion/calibration chain. A
  cross-paper or cross-device tuple is a **literature-scale composite benchmark**, never a
  "physical/realistic device cell." `project-design`, `convenience-default`, and
  `numerical-only` values may drive sweeps, tests, or resource gates but may not support a
  real-device claim. Missing provenance fails closed. Current audit and exceptions:
  `docs/NUMERICAL_PROVENANCE.md`.
- **Evaluator-side isolation.** The noise process's truth — source trajectory `z_t`, the
  channel field, per-substep mechanism params — is **evaluator-only** (reachable via
  `.truth` / `CertReport.truth`), and is **never** in the emitted record payload.
  `certify/` reads that truth to SCORE against independent anchors; nothing downstream of
  the record may see it.
- **GPU-first.** Model compute is GPU-only (no `cuda if available else cpu`); target
  workstation ≥ RTX 5090. CPU-only results are not evidence of a GPU-path failure.
- **Self-contained code, explicit external inputs.** Self-contained means that every simulator
  runtime module is owned by this distribution; it does not mean that third-party circuit or
  independently generated oracle data are bundled. The Google r01/r10 `.stim` + metadata files
  are caller-supplied circuit/geometry/schedule inputs only, never package data and never noise
  parameters. Ququart transport requires exactly one explicit channel source: `CZParams` for
  package-owned in-process Hamiltonian-to-channel derivation, an in-memory channel (including a
  Kraus stack),
  or a serialized derived-channel cache. Kraus operators are a derived channel representation,
  and a serialized Kraus artifact is an optional cache—not external scientific data. There is no
  default path into repository scratch. Missing or ambiguous inputs fail closed. Historical
  `qec_twin.*` values may remain only as frozen schema
  identifiers for artifact compatibility; active manifest owner fields (`backend`, `source`,
  `oracle`, `assembled_by`, and equivalents) must name the installed
  `error_coupling_simulator` owner.
- **Distribution acceptance is an isolated-wheel gate.** A release candidate must build the real
  checkout as sdist, build the wheel from that sdist, install it into an isolated target, remove
  the repository root and `src/` from import resolution, and pass package import plus core runtime
  smokes. The same gate must prove that no `qec_twin` package, old console entry point, or
  repository-only scratch asset entered either archive. An editable-install smoke is not a
  substitute for this gate.
- **Aggregate service acceptance is process-isolated.** The complete service matrix must run through
  `python tests/harness/service_acceptance.py`, which expands the unique acceptance files declared in
  `docs/service_status.json`, and runs every file in a fresh exec process. The catalog assigns each
  file to exactly one resource lane: independent `cpu_light` files use bounded concurrency subject
  to CPU and `MemAvailable` caps; host-memory/BLAS-heavy `cpu_exclusive` files run serially; and
  `gpu_serial` files run serially while one cross-process GPU `flock` is held only for that phase.
  CUDA-Q remains routed to the retained `aiqec` environment. The supervisor must not import
  Torch/CUDA or reuse a CUDA-initialized fork worker; each child exit is the allocator/lifetime reset.
  A single long-lived pytest process is not an equivalent gate: it shares native lifetime state
  across Torch, QuTiP/cuQuantum/CuPy, fused CUDA extensions, and the isolated CUDA-Q plugin and has
  reproduced exit 139 even though the same service groups pass in clean processes. GPU ownership
  cannot be lock-free across independent runners; within the supervisor, the plan is immutable and
  result aggregation has one owner. This execution policy changes no physical model, numerical
  tolerance, or evidence bar.
- **CUDA-Q is an isolated optional plugin, not core runtime.** The public noiseless-Grover adapter
  remains available through the `cudaq-grover` extra, but it runs in the retained `aiqec` plugin
  environment and a separate process. It is deliberately absent from canonical `ecs` and must not
  share a process with the fused simulator extension.
- **Precision is bound to run purpose and carrier.** Only the active
  `FusedWithinCycleSampler` / `sv_traj_d3_wc` path may execute an optimization run in c64;
  its artifact is `screening_only`. Final and certification runs use c128 and are only
  `c128_candidate` until the owning scientific gates pass. A c64 artifact is never promoted to
  evidence; a candidate conclusion requires a separate frozen c128 replay. PEPS and the restricted
  Axis-1 MPS executors remain c128-only and must reject c64 metadata. WG channels, codestates,
  channel composition, and CPTP
  checks are constructed in c128; only the checked complex execution tables may be cast at the
  fused-SV boundary. This policy does not authorize tolerance or FET changes.
- **Numerical floor.** `error_coupling_simulator.numerics` — `1e-12` for float
  floors/thresholds only; never for structural zeros (Pauli entries, bit values, integer
  indices, exact algebraic identities).

## Carrier ladder (forward propagation)

The forward engine scales through a ladder; the object + record contract are
backend-agnostic across it:

1. **Exact density matrix** (`carrier/exact/{qutrit_dm,circuit_sim}.py`) — feasibility-only.
   A complex128 qubit DM reaches roughly 16 GiB at 15 qubits; a qutrit DM scales as `9^n`, so the
   current d3 9-qutrit array is already about 5.77 GiB and 15 qutrits would be about 2.93 PiB.
   This is the **certification
   ORACLE**, not a scaling path.
2. **Restricted Axis-1 one-dimensional MPS execution** (`frontend/axis1_mcwf_mps_execution.py`,
   `frontend/axis1_qt_mps_execution.py`) — shipped `quimb`/Torch-CUDA verification paths. The
   MCWF path executes fixed-microstep pure-state trajectories for declared local dimensions; the
   QT/MPS path is a narrower computational-subspace/product-formula slice. Both fail closed outside
   their declared support and neither claims production-scalable, full-record, or full-`d×d`
   completion. The old XZZX thin-strip driver remains under `legacy/` and is not distributed.
3. **2D PEPS, full `d×d`** (`carrier/peps/`) — the **active frontier** (ADR 0011). A 1D
   MPS can require `χ=2^{Θ(d)}` across a full-square cut in the worst/project-estimate regime,
   so the full-code carrier candidate is a single-wire 2D
   PEPS pure-state MCWF trajectory. The doubled-wire DM-PEPO (`carrier/pepo/`) is closed.

**Truncation must be certified on the RECORD, but record faithfulness is not yet
established** (ADR 0011, reopened 2026-07-13). Zero added bipartition entropy, a small
local/environment objective, or a bounded per-edge bond does not prove equality of the
multi-round record. In particular, whether computational/leakage coherence reaches the
record is channel-, schedule-, and instrument-dependent. The per-edge bond remains a
resource guard only. **Current frontier problems are separate:** diagnose the FET/ALS
implementation, and close the physical long-range/record bridge. Evenbly's direct
top-WTG truncation has a source-backed optimality claim at zero cycle entropy and only a
heuristic near-optimal claim when it is small. At nonzero cycle entropy that direct
optimality is lost; Evenbly proposes iterative FET, not a uniqueness theorem. ZMT is an
initializer followed by variational refinement in the source examples. No
deterministic WTG replacement or leakage-tail deletion is currently authorized. See
`docs/nonpauli_teacher/coherent_leakage_longrange_truncation_literature_closure_2026-07-13.md`.

## Certification / faithfulness

- **Independent ground truth (FAITHFULNESS_PROTOCOL rule I).** Verify a carrier against
  ground truth INDEPENDENT of its implementation (raw `.stim` artifact, a from-scratch
  reconstruction, a closed-form theorem, or the GF(2) stabilizer entropy) — never against
  the engine's own oracle.
- **Rung ladder** (`certify/`): channel-level Choi/PTM/CPTP → d3 record distribution vs
  the DM oracle (TVD/KL/marginals) → carrier-appropriate approximation convergence
  (bond/microstep/trajectory controls, always scored on the record) → **d5/d7 oracle-free
  internal checks only** (CPTP residual, structural pins, convergence self-consistency). Bayes-floor
  and decoder-headroom calculations are downstream legacy analysis, not a simulator rung.
- **Memory-axis faithfulness instrument (notion-2).** That the passive record carries the
  specified multi-time memory is scored by the record's **absolute multi-time Markov-order
  structure** vs a genuinely-Markov-order-k generative null. Full-history/order tests are
  required for a process-wide claim; lag-local CMI `I(mᵣ;mᵣ₋₂|mᵣ₋₁)`, Anderson–Goodman
  `G²`, and `E(k)` are diagnostics. This instrument measures record structure; it does **not** fit
  or recover source/channel parameters. Any separate parameter-recovery analysis, passive or
  instrument-varying, is outside the simulator product and cannot replace the full-record
  carrier-faithfulness ladder.
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
- **Metric ledger.** Use field-standard QEC operational instruments — `ε_d`, `Λ`,
  detection-event fraction, `p_ij`, and frozen-decoder LER — plus explicitly labeled
  **project d3 certification choices** such as joint-record TV/KL and generative NLL.
  Never present a project choice as a universal QEC standard (`docs/METRICS.md`).
- **Tool I/O contract.** Stim-native in (`.stim` / `.b8`), standard `.dem` out;
  pip-installable; no bundled decoder, no new formats. Core record emission must not depend on
  decoder installation: `Simulator.run(..., decoder=None)` is the default, while the optional
  external PyMatching reduction runs only when explicitly requested. The default Stim artifact
  path preserves non-graphlike DEM hyperedges (`decompose_errors=false`); graphlike decomposition
  is requested only for explicit PyMatching decoding.

## Frontend / product surface

The frontend has one common **emitted-record contract**, not yet one universal executor.
`CodeSpec → CircuitIR`, imported Stim circuits, and hand-built `CircuitIR` feed the
Stim-representable `Simulator.run(...)` surface, which emits `.stim` / `.dem` / `.b8` /
manifest artifacts and exposes the actual detector/observable records as `RecordBatch` without a
decoder. Passing `decoder="pymatching"` additionally emits prediction and decoder-summary artifacts
through the optional `[hw]` dependency. Without that request, the corresponding manifest entries
use `file=null` and `omitted_reason="decoder_not_requested"`; they are never fabricated. Axis-1
record evidence and PEPS trajectories use their own bounded runners but now also return/wrap
`RecordBatch`; they do not silently route through Stim. Unifying those execution inputs behind one
facade remains open frontend work.
Every artifact declares a `representability` class and **fails closed** — Stim-Pauli noise,
source-projection, joint-L channel evidence, and analog schedule metadata are distinct, never
silently conflated. `.stim`/`.dem` are not analog joint-Lindbladian truth, leakage truth, or
shared-source non-Markovian truth. XZZX is the first target code spec, not a hard-coded simulator
core.

## Working disciplines (every change obeys)

- **Theory-first** — the physics/math derivation and the predicted outcome (direction,
  scaling, threshold) are written down BEFORE the run; experiments verify predictions.
- **Number-first provenance** — before a claim-bearing run, freeze the value-level provenance
  record required above. A literature equation grounds a functional form, not silently the
  chosen amplitude; a test fixture or numerical tolerance is not a physical parameter.
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
ground-truth reference; the **carrier** = the forward engine. **notion-1/-2/-3** are three
non-exclusive object labels: reduced-map divisibility/backflow / observed-record memory or
order / process-tensor memory carrier. They are not a strength ladder and do not determine
classical-versus-quantum origin without an explicit access and identifiability argument.

## Local reference tooling

- **RAG (literature search; repository-only, not distributed)** —
  `python -m qec_twin.rag.store --query "<q>"` (rebuild:
  `--build --force`); ChromaDB over the `docs/papers/reading_notes/` 精读 notes (~2230
  chunks). The query basis of the `theory-first` / `theory-fix` skills.
- **KG (knowledge graph)** — `python outputs/knowledge_graph/kg_query.py` (concept /
  relation traversal; `kg.json` / `kg_full.json`, local-only). The other `theory-first` /
  `theory-fix` grounding source.
- **Service catalog + code map** — `docs/service_status.json` is the machine-readable installed
  service/support/exclusion contract and complete flow; `docs/CODE_MAP.md` is generated from it plus
  the AST-derived `src/` inventory and `code_status.json`. The generator reverse-checks every shipped
  Python module, including namespace facades, so an unclassified module is a hard failure. Regenerate
  with `python tools/gen_code_map.py` (staleness/contract check: `--check`). Both files ship with the
  wheel under `share/doc/error-coupling-simulator/`.
- **Test codebook** — `tests/CODEBOOK.md`: the L0 structural / L1 property (Hypothesis) /
  L2 mutation (mutmut) coverage harness (`tests/harness/`). Read before touching a batch.

## Key documents

- **Architecture:** `docs/ARCHITECTURE.md`; per-module `src/error_coupling_simulator/**/README.md`;
  `docs/service_status.json` (service contract); `docs/CODE_MAP.md` (generated complete inventory and
  flow).
- **Simulator decisions:** `docs/adr/0008` (scalable-carrier charter) · `0010` (historical
  non-Pauli carrier design, amended by the current package boundary) · `0011`
  (record-faithful truncation on the 2D PEPS carrier). ADR `0009` governs downstream
  inference/decoder research and is not a simulator-product decision.
- **Live working notes:** `docs/nonpauli_teacher/` (the PEPS/FET carrier line + handoffs).
- **Protocols:** `docs/FAITHFULNESS_PROTOCOL.md`, `docs/METRICS.md`.
- **Migration provenance:** `docs/error_coupling_simulator_MIGRATION.md` (how the package
  was consolidated).
