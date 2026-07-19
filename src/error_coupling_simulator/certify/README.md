# certify — compare a controlled noise process with independent formal anchors

**Evaluator-side boundary.** Scores a controlled noise process's emitted records (or the
scalable carrier that produces them) against **independent, exact-or-declared-reduction ground-truth
anchors**, and returns an epistemic ledger + a single verdict.

**Design (locked).** A common-caller spine over an
`Anchor` capability-descriptor **port**. The core is BLIND to whether a DM oracle, a stim Clifford
slice, or a closed-form identity answered; the port carries a *capability descriptor* so OOM-routing
is **data**: an anchor that would OOM reports `feasible=False`, the core routes to the carrier-MCWF for
scale and never allocates the infeasible density matrix. Closed-form identities ride as an analytic
**sidecar** (the `SCALAR_FUNC` statistic), not as peers in the distributional comparison.

- `types.py` — the interface: `Regime`, the `Anchor` / `Control` /
  `ControlledNoiseProcess` ports, and the
  epistemic ledger (`CertReport` / `LedgerRow` / `Verdict`). Pure value types; no GPU.
- `core.py` — the implemented route → controls-first → score → ledger engine.
- `anchors/` — the implemented DM / Stim / closed-form adapters plus corrupt-stabilizer and
  record-shuffle negative controls (each **wraps** an existing package/wheel route, never
  reimplements physics).
- `facade.py` — the implemented `certify_noise_process` entry point.
- `axis1_mps.py` — evaluator-side dense Reference construction, metric evaluation, and
  fail-closed restricted-acceptance policy for immutable QT/MCWF MPS execution evidence. The
  frontend composes this result into the final evidence manifest; the execution mechanics do not
  certify themselves. The independent oracle never imports QT execution policy, MCWF grouping, or
  the production MCWF term builders. `mcwf_operator_reference.py` freezes all 51 supported
  Hamiltonian and seven collapse families as certifier-local hand-typed NumPy/Pauli matrices. Before
  any dense metric can authorize restricted execution, every present production term must agree
  with that reference within the shared `NUMERICAL_ZERO` floating threshold; unknown, wrong-arity,
  non-finite, wrong-shape, and mismatched operators fail closed. The dense oracle then uses the same
  isolated reference matrices with `assemble_substep_channel`, while the carrier side continues to
  use its production grouping and builders. Hamiltonian and collapse zero-builder corruptions,
  including outcome-insensitive `CTRL_Z` and dark-state `T2` cases, are verdict-driving. This is an
  implementation-definition gate, not proof that every declared physical mechanism is source-closed
  or hardware-calibrated. The production Adapter compiles every Hamiltonian/collapse tensor once and
  derives every connected Hamiltonian-group gate from that frozen inventory before either the mass
  preflight or trajectories consume it. `axis1_mps.py` independently reconstructs the term matrices,
  connected-component grouping, support/order, and group gates with the isolated operator formulas and
  SciPy `expm`. Reference-declared structural-zero entries remain exact; term differences use
  `NUMERICAL_ZERO`, while the Torch-CUDA/SciPy group-gate comparison uses
  `1000 * NUMERICAL_ZERO`. The public
  `error_coupling_simulator.certify.mcwf_dynamics_artifact_reference_certification.v1` packet binds full
  substep/term/group coverage, local dimensions, microstep/order controls, Carrier-program and frozen
  artifact hashes, all current reference/certifier/carrier source hashes, and the post-execution artifact
  integrity result. The packet builder independently recomputes the canonical artifact hash from the
  matrices and metadata it certifies; it rejects an unrelated caller-supplied digest.
  `restricted_acceptance_policy` requires a current passing packet; Carrier and auto authentication rebuild
  the same artifact authority from sealed inputs. Accepted seeded auto evidence also replays the public
  direct MCWF execution and exact-binds its direct hash, Record summary, and policy.
  Stateful builder, state-insensitive wrong-grouping, group-gate, structural-zero, stale-source, packet,
  and post-execution mutation falsifiers must therefore remain verdict-driving.

  `CORR_RELAX` is covered when it is already present in an internal sealed Carrier program. There is no
  public source/schedule compiler lowering for that family yet, and the literature source-closure reset
  remains OPEN. Formula isolation and artifact integrity do not close that gap or create hardware,
  full-Record, production, or scalability evidence. The dense level-measurement path preserves
  every finite positive Born branch and skips only exact zero; a post-measurement reset is normalized
  for every finite positive trace, while negative/non-finite branch mass and nonpositive/non-finite
  reset trace fail closed. Before scoring MCWF measurement evidence, it requires equal-length,
  type-exact, schedule-ordered `measurement_keys`, `measurement_targets`, `measurement_bases`, and
  `reset_after`, then binds all four to the sealed Carrier program. Public MCWF bases are X/Z only.
  The independent NumPy reference uses direct X/Z eigenprojectors and hand-typed reset instruments:
  X reset prepares `|+>` and Z reset prepares `|0>`. Its evaluator-only v2 labels are explicitly
  declared-basis outcomes (`0/1` means `|+>/|->` for X). The registered comparison object is
  `measurement_basis_level_and_emitted_binary_record_populations`: it computes separate TVs for
  those labels and the emitted binary Record, reports their maximum, and requires both to pass. A
  certifier-local hand-typed readout kernel marginalizes leaked labels with the declared `b`, so this
  gate does not reuse the production label-to-bit sampler. It neither reinterprets X outcomes as
  computational local-level occupation nor claims complete QEC Record faithfulness.

**Invariants.** Negative controls are first-class + non-optional (an inert control forces FAIL);
feasibility is data (cannot OOM); every row carries its epistemic class (a)/(b)/(c) (METRICS.md);
anchors must be INDEPENDENT of the carrier's implementation (anti-circular).
For the fused within-cycle SV-MC carrier, certification accepts only a c128
`c128_candidate` header; callers must use `carrier.c128_evidence_record_batch(...)` before reducing
the self-describing packed batch to a `RecordBatch`. A c64 optimization artifact is permanently `screening_only`; replaying
the frozen run in c128 creates a separate candidate artifact and does not promote the c64 artifact.

**Boundary.** Certification may read evaluator-only process truth to score the declared process, but
that truth never enters emitted records. Anchors wrap package-owned exact-DM, Stim, and closed-form
references; no physics is reimplemented here. Downstream decoder-headroom analysis is not a
simulator certification layer.
The facade requires a caller process that implements its declared capability protocols. It is not
an automatic `RecordBatch -> certificate` transform: the current `CoupledCycleNoiseProcess` has no
DM replay callback and its Clifford-slice method is still an explicit open bridge.
