# Simulator contract

This is the binding product and scientific boundary for `error_coupling_simulator`. When another
document disagrees with this file, this file wins. Exact installed owners, entry points, dependencies,
outputs, and acceptance files are machine-readable in `docs/service_status.json`.

## Product

`error_coupling_simulator` is a GPU-first specified-noise simulator for quantum error-correction
circuits. A caller supplies a circuit or schedule and a declared noise process. The product is the
multi-time syndrome record: temporal detector bits and logical-observable flips, represented directly
or emitted as `.b8`. A `.dem` is an optional decoder-facing reduction; it is not the simulated object.

The package owns one runtime namespace, `error_coupling_simulator`. Distribution artifacts contain no
retired package, entry point, schema fallback, or compatibility layer. External circuits, optional
decoder inputs, explicit derived-channel caches, and the isolated CUDA-Q adapter are declared inputs
or plugins rather than hidden repository dependencies.

The simulator does not infer an unknown device model from records. Calibration, model selection,
parameter recovery, identifiability analysis, and decoder-headroom estimation are downstream
estimator tasks and are not simulator services or acceptance gates.

## Record contract

- `carrier.records.RecordBatch` is the common detector/observable record type.
- Detector coordinates are temporal events, not raw stabilizer outcomes. For raw round-major
  syndrome bits `s`, the required fold is `d[0]=s[0]` and `d[r]=s[r] XOR s[r-1]` for `r>=1`.
- Packed records accept only the declared byte layout and current schema. Payloads are binary,
  versioned, immutable after construction, and validated before any dtype narrowing.
- Structural probability zeros remain zero. Invalid states or non-probability payloads fail closed;
  numerical floors may not manufacture probability mass.
- Every emitted artifact names its representability class. Stim-Pauli records, reduced source
  projections, analog joint-Lindbladian evidence, leakage records, and research-carrier outputs are
  distinct and must not be silently relabeled.

## Implemented routes

The current routes are deliberately not one universal executor:

1. **Stim-representable frontend (CORE).** `CodeSpec`, `CircuitIR`, or an imported Stim circuit is
   compiled and executed through `frontend.Simulator`. Record emission is decoder-free by default;
   optional PyMatching output is requested explicitly.
2. **Axis-1 dense joint-Lindbladian route (CORE).** A compiled substep schedule is lowered into
   local Hamiltonian and collapse terms, assembled into one channel per substep, and executed on the
   supported small-register carrier.
3. **Classical finite-RTN source route (CORE).** Replayable finite-RTN timelines, including the
   finite-band sum-of-Lorentzians approximation, feed an explicit source-to-parameter map and matched
   controls. This is a classical latent-source model of multi-time record memory, not a microscopic
   bath or a reduced-map divisibility claim.
4. **Restricted one-dimensional MPS routes (CORE verification surfaces).** The MCWF/MPS and QT/MPS
   executors are finite-step, fail-closed verification paths. They are not universal full-record or
   production-scaling backends. `carrier/mps` is an execution-mechanics library for restricted
   verification routes. It makes no state-, Record-, or LER-faithfulness claim.
   It is not a registered scientific Carrier. PEPS remains the trajectory-carrier frontier.
   PEPO remains the retained research Carrier. `max_bond` is either `None` or a strictly positive integral value;
   booleans, floats, strings, zero, and negative values are rejected rather than coerced. A finite cap
   on a supported two-site unitary is applied through the pinned Quimb actual-split adapter: every
   forward-swap, operator, and reverse-swap SVD is ledgered, the conditional-state norm is restored
   only after its raw loss is recorded, and the resulting local discarded fractions are explicitly
   not a global state/record bound. Each split reports `actual_kept_bond_dimension`, the retained
   bond-index size. It is not a numerical rank; thresholded rank diagnostics must separately declare
   their threshold. Exact-branch ledgers weight path-local evidence by the incoming
   branch probability; sampled ledgers average path totals over the declared trajectory count, with
   trajectories that had no truncation event contributing zero. Each gate occurrence authenticates
   full sampled-trajectory coverage or unit exact-branch mass; incomplete coverage makes the ledger
   and acceptance fail closed. Once actual loss occurs, restricted finite-bond acceptance requires
   both explicit worst-cut and path-total discarded-weight gates; an observed lossless capped run
   needs no such gates. These
   gates remain heuristics, never production error bounds. Kraus/no-jump/jump operators remain
   uncapped because their raw norm carries physical branch probability; that probability is not a
   truncation score. Capped multi-site MCWF Hamiltonian clusters fail closed. Uncapped connected
    three-to-five-site MCWF unitaries instead use the bounded `carrier/mps` execution-mechanics
    helper: both dense-to-MPO decomposition and MPS/MPO compression carry an explicit zero cutoff,
    the source is changed only after a finite unitary candidate preserves its norm, and support is
    rejected before dense allocation above five sites, Hilbert dimension 256, or 65,536 dense
    elements. Those ceilings are numerical-only resource guards. MCWF option
    `symmetric_hamiltonian_first_order_collapse` records two Hamiltonian half-passes separately and
    in order as `hamiltonian_pass_index=0,1`; both carry the scheduled half-step duration and must be
    present in the authenticated occurrence ledger. The intervening normalized collapse update is
    first-order, so this option is neither named nor claimed as Strang or second-order. The retired
    MCWF value is rejected before CUDA; QT retains its separate genuine Strang option.
    Both restricted MPS
    Adapters parse the compiler-sealed schedule once, before CUDA or trajectory execution, into an
    immutable Record layout that fixes boundaries, keys, targets, bases, per-target reset flags,
    global slices, and detector/observable XOR columns. Trajectories fill outcome bits only; they
    cannot discover or mutate the Record schema. QT exact and sampled routes support all declared
    measurement boundaries and enforce the frozen width. MCWF grouped measurement/reset applies the
    reset mask per target. Its public `measurement_keys`, `measurement_targets`,
    `measurement_bases`, and `reset_after` lists are equal-length and schedule-ordered one per Record
    column; `measurement_basis` is exactly `none`, `X`, `Z`, or `mixed_pauli`. X measurement rotates
    into Z for carrier sampling and rotates a non-reset conditioned state back; X reset prepares
    `|+>`, while Z reset prepares `|0>`. The direct child, Carrier, auto-router, and certifier each
    rebind those fields to the sealed schedule, so a reordered and rehashed payload is rejected.
    The auto-router also requires exact Carrier/state/Record/direct-summary field sets, binds caller
    options, initial levels, local Hilbert dimensions, declared-basis readout policy, sampling seed,
    state machine, policy v7, and transitive direct
    v8 schema/hash, and accepts only a sorted unique normalized empirical histogram with canonical
    blocked summaries. Evaluator-only field families are rejected recursively at the public seam.
    Before the dense comparator may authorize restricted execution, it compares every present
    production Hamiltonian/collapse term against the isolated hand-typed NumPy/Pauli definitions in
    `certify/mcwf_operator_reference.py`. The frozen inventory covers 51 Hamiltonian and seven
    collapse families, requires the declared support arity and local levels, preserves exact padded
    structural zeros, and uses `NUMERICAL_ZERO` only for the final floating matrix difference.
    Missing, unknown, non-finite, wrong-shape, or mismatched definitions make certification
    unavailable and reject the run, including when the chosen initial state and Record would be
    insensitive to the damaged operator. The dense joint-L oracle itself consumes those isolated
    reference matrices; only the carrier-under-test consumes production builders/grouping.
    `CORR_RELAX` is routed as the declared two-site collective collapse on both sides of the channel
    comparison. This closes the software self-reference seam but remains implementation-definition
    evidence, not source closure or hardware calibration for every physical family.
    The execution Adapter now compiles each production Hamiltonian and collapse tensor once, before
    mass-residual evaluation or trajectories, and constructs every connected Hamiltonian group gate from
    those same frozen term tensors. The first-order mass preflight, no-jump/jump competition, and both
    symmetric Hamiltonian passes consume that immutable artifact set; no later production-builder call may
    redefine the executed dynamics. The preflight bounds the sampler's actual sequential no-jump
    product, including multi-collapse cross terms, rather than replacing it by one factor built from
    the summed collapse rate. Its diagnostic recommendation search is capped at signed 64-bit for
    artifact interoperability and reports the smallest count within that search that clears a
    positive budget. Requests that need a larger recommendation are rejected without emitting a
    type-changed blocked artifact; this reporting cap is not an input maximum. The public
    MCWF seam accepts only a positive finite budget (or `None` for a diagnostic
    run); zero is rejected before CUDA because no active finite step can satisfy it exactly. This is
    an exact-arithmetic raw-candidate-mass bound evaluated in floating point as a deterministic
    preflight; the separately observed runtime residual remains the final acceptance gate. It is not
    a global convergence-order or production error bound.
    Before execution, the certifier independently reconstructs every
    frozen term, connected-component partition, group support/order, and group gate using its hand-typed
    NumPy definitions plus SciPy `expm`. Declared structural-zero entries must remain exactly zero;
    per-term floating differences use `NUMERICAL_ZERO`, while cross-backend group-gate comparison uses
    `1000 * NUMERICAL_ZERO` to cover the measured Torch-CUDA/SciPy matrix-exponential floor. The
    `mcwf_dynamics_artifact_reference_certification.v2` packet binds complete substep/term/group counts,
    local dimensions, microstep/order policy, Carrier-program and artifact hashes, and five current
    source hashes: reference operator, certifier, carrier operator, transitive ideal-control generator,
    and transitive selection-family owner. It also requires a post-execution artifact-integrity check.
    The certifier recomputes the canonical artifact
    hash from the matrices and metadata it actually inspected; a caller-supplied but unrelated SHA-256 is a
    failed packet. Restricted policy acceptance requires the packet to be current and passing. Carrier and
    auto seams rebuild the artifact authority from sealed inputs. In addition, an accepted seeded auto route
    independently replays the public direct MCWF call and requires its direct hash, canonical Record summary,
    and restricted policy to match exactly. This replay is an integrity measure, not a scalability claim.
    `CORR_RELAX` support currently begins only when that family is already present in the internal sealed
    Carrier program; there is no public source/schedule compiler lowering for it yet. The current literature
    source-closure reset is still OPEN. Neither the isolated formula code nor the frozen-artifact gate closes
    that literature gap, establishes hardware calibration, or promotes this slice to production/scalable use.
    The dense comparator independently uses declared-basis projectors and reset instruments rather
    than the carrier rotation helper. It preserves every finite positive Born branch, skips only
    exact structural zero,
    normalizes every finite positive post-measurement reset trace, and fails closed on negative or
    non-finite branch mass and nonpositive or non-finite reset trace.
    When a schedule has no measurement columns, the executor still validates the canonical
    `[[]]` Record sentinel and its count/probability identity, but certification is exactly
    `unavailable` with
    `mcwf_normalized_candidate_law_has_no_registered_linear_channel_metric`. The normalized
    finite-step candidate law has input-state-dependent total mass and is generally nonlinear, so it
    cannot be promoted to a CPTP Choi/process metric. MCWF channel-process gates and their former
    comparison identity are not part of the current policy; only registered X/Z Record metrics may
    authorize restricted MCWF evidence.
    MCWF pre-readout `level_records`/counts/probabilities and `jump_family_counts` are hidden
    unraveling diagnostics under `evaluator_only_diagnostics.v2`; they are not emitted binary Records
    or downstream estimator inputs. Their registered semantics are declared-basis local measurement
    eigenlabels: X columns use `0=|+>,1=|->`, Z columns use computational local levels, and leaked
    labels `>=2` remain explicit. Certification compares both those hidden labels and the emitted
    binary Record under
    `measurement_basis_level_and_emitted_binary_record_populations`: the reported value is the
    maximum of the two TVs and acceptance requires both gates. The binary oracle applies a
    certifier-local hand-typed readout kernel to the dense label law, so corrupting the production
    level-to-bit mapping is verdict-driving even when the hidden-label distribution is unchanged.
    This is not a claim that X labels are computational-level populations or that the complete QEC
    Record is faithful. Caller-declared `local_dims`, `initial_levels`, and
   `leaked_readout_b` remain configuration, not evaluator truth. `certify/axis1_mps.py` consumes the
   immutable execution evidence and owns dense References, metrics, and final restricted acceptance.
   Reset substeps carrying evolution and evolution-bearing substeps without finite positive duration
   fail as structured preflight blockers. QT sampled measurement is sequential conditional
   single-site binary sampling. It emits only lexicographically sorted outcomes observed in the
   declared trajectories, with no zero-frequency rows; QT exact execution still emits the full
   binary Record support. Seed-sweep and dense-reference comparisons align the union of emitted
   supports and assign probability zero to a missing outcome. The v2 Record-materialization
   preflight remains pre-CUDA and fail closed: for measurement width `m`, exact execution uses the
   upper bound `2**m`, while sampled execution uses `min(2**m, trajectory_count)`. The conditional
   sampler changes RNG draw order, so distributional checks replace compatibility with the old
   per-trajectory bit sequence.
   Exact execution artifacts do not report an observed hidden branch count. They report only
   `static_branch_count_upper_bound_after_substep`, a numerical resource bound recomputed exactly
   from the authenticated carrier program and `max_branches`; the legacy
   `branch_count_after_substep` field is rejected. QT resource probes are exact-shape authenticated
   against the evidence bundle, policies, claims, verdicts, and hashes. Their process-memory
   counters are authenticated observations from the producing run, not an independent second
   measurement.
   These are execution/schema guarantees, not a canonical Record backend or a Record-faithfulness
    upgrade. The direct QT/MPS manifest is v6 and direct MCWF/MPS is v8; QT bond sweep, seed sweep,
    evidence bundle, and resource probe are v4. Carrier execution and auto-routed execution are v5,
    the routing decision remains v3, the MCWF restricted-acceptance policy is v7, and the public frozen
    dynamics-artifact reference-certification packet is v2.
   No earlier
   direct-execution or aggregate compatibility fallback is retained. A completed true-over-cap run
   with no registered independent Record oracle remains diagnostic execution
   evidence: certification is `unavailable`, restricted acceptance is false, and the verdict is
   `fail`. Empirical Record normalization, a fixed RNG seed, or backend completion cannot promote
   that run into certification.
   External comparisons remain role-scoped. Aer checks its own finite-circuit MPS against an
   independent hand-written dense state; YASTN checks a product-MPS raw MCWF candidate-mass family;
   isolated CPU QuTiP checks one frozen two-qubit T1 fixture with ordered X/Z measurement/reset
   boundaries against public GPU direct and Carrier MCWF Record histograms under Bonferroni
   two-sample TV gates. In addition to the joint Record comparisons, directed X-after binary
   marginals must pass; the fixture fixes survival to `s=0.25`, so the load-bearing
   `sqrt(s) -> s` coherence-rate mutation lies outside the registered simultaneous radius and must
   fail. That QuTiP fixture also requires real jumps, independently verifies X reset to `|+>` and Z
    reset to `|0>`, and includes a verdict-driving final-Z-bit corruption. The same neutral fixture
    also has a certifier-local finite-step scalar recurrence at
   `m=10,20,40,80`: joint/Z and X-after TV biases must decrease and approximately halve on that
   frozen grid, and the public `m=40`, `n=2048` GPU histogram must lie within one-sample Weissman
   radii of the finite-step law. This is fixture-bound Record convergence, not a global order or
    linear-channel convergence claim. The isolated worker binds the
   pristine QuTiP commit/tree, installed-distribution content identity, Python/NumPy/SciPy versions,
   explicit MCWF integrator controls, worker/protocol hashes, and canonical report hash. The v2 worker
   shape is recursively exact-field checked and its semantic invariants are recomputed. Strict JSON
   parsing rejects duplicate/non-finite values and coercible non-integer Record bits/counts; a separate
   transport envelope binds the immutable worker payload plus its construction-time raw-byte hash/size
   and process outcome, and requires those bytes to decode to that payload. The direct worker launch
   strips every inherited `CONDA_*`/`_CE_*` marker plus CUDA-toolkit, virtual-environment, and
   dynamic-library-path markers; the worker rejects leakage and records the fixed marker set's absence.
   Worker and outer targets first invalidate and directory-`fsync` any stale file, then file-`fsync`,
   replace, and directory-`fsync` the completed artifact; a failed post-replace durability step removes
   the destination before propagating the error. The service
   checkpoint separately binds the external clone HEAD/tree plus the installed NumPy/SciPy/QuTiP
   trees. The nested worker directly uses the isolated environment's Python and remains in the
   supervisor-owned process group, so outer cancellation cannot strand a private session. Quimb's
   public leg checks wiring against the repository's actual-split adapter while NumPy owns the
   independent state math. These comparisons do not establish a complete QEC Record law,
   trajectory-by-trajectory coupling, qutrit/leakage behavior, PEPS faithfulness, scalability, or
   production readiness, and none is itself the restricted-acceptance oracle. Canonical service
   acceptance opts into the isolated Aer, YASTN, and QuTiP subprocess runs rather than executing
   only their helper tests.
   The restricted-MPS performance instrument is engineering-only. It binds every production owner
   by file hash and requires each workload's declared public outcome. In particular, the lossy QT
   cap-one fixture must remain `rejected`, and the over-cap MCWF fixture must remain `unavailable`;
   benchmark `passed=true` means those outcomes matched the catalog, not that either candidate is a
   safe truncation. A tiny CPU-only cache stores immutable Stim two-qubit Tableau matrices, but every
   call creates an independent Torch tensor; no Torch/CUDA tensor, RNG state, split result, or
   truncation decision is cached.
5. **Qutrit leakage and ququart transport (CORE bounded channels).** Current owners expose physically
   named leakage/channel operations and explicit parameter objects. Synthetic defaults and sweeps do
   not become device calibration through naming or citation.
6. **Density-matrix PEPO (RESEARCH, retained).** `carrier/pepo` is a current, tested two-dimensional
   qutrit density-matrix carrier. It is not the canonical record backend and does not have established
   finite-truncation full-record or d5/d7 faithfulness.
7. **Single-wire PEPS (RESEARCH).** `carrier/peps` is the current full-geometry trajectory-carrier
   frontier. It emits packed records through the current record adapter, but complete multi-round
   finite-truncation faithfulness remains open.
8. **Quantum-bath models (RESEARCH).** The pseudomode-enlarged GKSL surface provides bounded formal
   comparisons. It is not evidence that a passive record certifies quantum environmental memory.

The source-conditioned dense-qubit process and the static data-qutrit XZZX leakage process are
separate implementation routes. There is no current integrated source-to-qutrit-XZZX record product.
No document may describe that missing bridge as implemented or literature-closed.

## Carrier and reference boundary

Exact density-matrix execution is a feasibility reference, not a scaling route. A complex128 qubit
density matrix reaches roughly 16 GiB at 15 qubits; the current nine-qutrit d3 array is approximately
5.77 GiB. Larger-code work therefore uses bounded MPS verification and two-dimensional research
carriers, while exact d3 routes remain implementation references.

Carrier validity is judged on the declared record law, never on bond dimension, state fidelity, local
entropy, or a truncation objective alone. A state-level or local-environment check can validate a
local invariant without certifying the complete multi-round record.

The PEPS environment-aware truncation mutation boundary is now engineering-hardened: only an
authenticated, finite, target-meeting rank reduction may write both endpoints; rejected candidates
are no-ops; a partial or failed absorption rolls both tensors back; and solver perturbations use a
declared private RNG rather than advancing ambient CPU/CUDA streams. This closes the known mutation,
transactionality, and RNG-control defects, not the scientific claim. At the strict registered
``eps_fid``, the d3 entropy equality currently occurs with zero accepted rank-reducing write-backs;
the explicit FET non-degeneracy gate is therefore RED and the pruning path is not scientifically
validated. The committed fresh-process replay bound to `c8c553e` authenticates the all-noop split
verdict: scoped replay, fallback contract, RNG neutrality, and entropy pass, while solver health and
non-degeneracy remain RED. A primary-literature bridge must still connect the local FET objective to
the QEC entropy and complete record-law observables. Local
environment, entropy, or dense-reference checks cannot individually certify full-record faithfulness,
and no tolerance, target, or algorithm substitution may be chosen merely to manufacture a pass.

Current carrier status and exact evidence paths are recorded in:

- `docs/simulator_validation/PEPO_VALIDATION.md`
- `docs/simulator_validation/PEPS_FET_VALIDATION.md`
- `docs/simulator_validation/LEAKAGE_PROCESS_VALIDATION.md`
- `docs/simulator_validation/COHERENT_LEAKAGE_TRUNCATION_EVIDENCE.md`

## Scientific claim boundary

- A specified noise process is a model, not physical ground truth. Closed forms, QuTiP, exact density
  matrices, and independent reconstructions are reference oracles for implementation checks.
- Evaluator-only process truth never enters the emitted record or downstream estimator input.
- A source timeline alone has no reduced-dynamical-map status. Record memory, reduced-map
  divisibility/backflow, and process-tensor memory are different objects and require different access.
- PTM off-diagonal entries establish basis-specific non-Pauli structure. They do not, without an
  additional argument, identify coherent error as the cause.
- Every d5/d7 distributional result is provisional because no independent full-record oracle exists at
  those sizes. It may guide engineering but may not serve as a scientific premise.
- Every retained scientific statement must bind a physical name, formula, implementation owner,
  current falsifier, and primary source or complete project derivation. Missing any element is a gap,
  not an implied fact.

The finite-RTN free-induction diagnostic is a separate post-result reconstruction with a clean current
contract. It does not transfer a divisibility verdict to the production source, channel, or record.
See `docs/simulator_validation/finite_rtn_free_induction_literature_closure_2026-07-15.md` and
`docs/simulator_validation/finite_rtn_free_induction_diagnostic_contract_2026-07-15.md`.

## Numerical and precision rules

- `error_coupling_simulator.numerics.NUMERICAL_ZERO == 1e-12` is for floating thresholds only, never
  structural zeros, bit values, indices, counts, or exact identities.
- Qutrit leakage channels, codestates, channel composition, and CPTP checks are constructed in
  complex128.
- PEPO, PEPS, and the restricted MPS verification routes are complex128-only.
- Only `FusedWithinCycleSampler` may use complex64, and only for an optimization run labeled
  `screening_only`. Final or certification candidates require an independent complex128 replay.
- A numerical tolerance, resource cap, or local solver objective is not physical evidence.
- Claim-bearing values follow `docs/NUMERICAL_PROVENANCE.md`; metrics follow `docs/METRICS.md`; all
  faithfulness claims follow `docs/FAITHFULNESS_PROTOCOL.md`.

## Schema and environment hard cut

Current artifacts use `error_coupling_simulator.<owner>.<artifact>.vN`. Unsupported schemas are
rejected by normal validation; there is no fallback reader.

Current environment variables are:

- `ECS_DISABLE_NATIVE_KERNELS`
- `ECS_FORCE_UNFACTORIZED_AXIS1`
- `ECS_D3_DATA_ROOT`
- test-only `ECS_D3_MASK`

JIT and custom-operation names use the `error_coupling_simulator` namespace.

## Acceptance execution

`python tests/harness/service_acceptance.py` is the canonical aggregate engineering gate. It expands
the service catalog and starts every acceptance file in a fresh process. The parent imports no
Torch/CUDA runtime. CPU children are CUDA-hidden and use one thread per declared BLAS/OpenMP runtime;
independent CPU files use at most four concurrent processes, further constrained by `MemAvailable`,
while host-memory-heavy CPU files run serially. GPU files run serially while holding exactly one
cross-process GPU lease for that phase; they never inherit CPU concurrency. CUDA-Q is routed to its
isolated environment.

The restricted-MPS mutation gate is a narrow exception to service-file GPU serialism, not a change
to service acceptance. Its five GPU shards still run one after another under one root lock and one
leased, pinned device. Within one shard, `jobs` may be one through four; the configured gate uses
four independent fresh pytest children for concurrent clean admission and then fixed waves of at
most four mutant children on that same device. Every child is host-thread-limited and has a unique
log, completion sentinel, and pytest temporary directory; inherited pytest/xdist expansion is
disabled, and the shared generated tree is read-only for the worker phase. The checkpoint binds the
sanitized child environment plus the leased GPU UUID and driver version. Startup may recover a
real, symlink-free generated tree left read-only by an abrupt process or host exit by making only
its directories owner-deletable and removing the entire disposable tree; a root/internal symlink
or surviving path fails closed. Only the coordinator may
commit an authenticated contiguous prefix. One narrow timeout class is a terminal killed mutant: a
GPU mutant child whose identity-bound completion sentinel proves pytest exit code 1 before the
supervisor deadline, whose log proves no host/CUDA resource exhaustion, and whose process-group
cleanup is verified. The supervisor may terminate that already-completed wrapper, but the
authenticated row remains resumable. Clean-admission timeouts, CPU-lane timeouts, missing or
inconsistent sentinels, resource exhaustion, unverified cleanup, child errors, and all other timeouts
are non-resumable: they cancel current-wave siblings, stop later admission, and never improve the
score. Automatic child timeouts multiply the single-worker dynamic budget by the admitted in-shard
concurrency, so four-way CUDA startup and runtime contention cannot consume a serially estimated
deadline; an explicit operator timeout is literal and is not scaled. The coordinator records the first
completed non-resumable outcome as the failure trigger while retaining only the safe plan-ordered
prefix. Direct batches honor the suite lock, so aggregate publication and checkpoint retirement cannot
race a same-tag run.

Before a worker row can enter a checkpoint, its completed log file and containing directory are
`fsync`-durable and the digest is computed from that same open inode. Checkpoints and terminal JSON
are written to a same-directory temporary file, flushed and `fsync`ed, atomically replaced, and
followed by a directory `fsync`. A durability failure is non-resumable and is never downgraded to a
killed mutant.

Semantic mutation scoring is machine-authoritative. The v2 AST catalog may exclude only a proven
non-contractual exception-prose mutation; the v2 human disposition file is authenticated annotation
and cannot change a mutant's kind, criticality, denominator membership, or pass result. Raw counts
must equal semantic counts plus machine exclusions both globally and for every canonical status.
Batch and suite result schemas are v3, GPU checkpoints are v4, and legacy records are rejected. Merge
reauthenticates required score fields, canonical status domains, critical-mutant identities, module
rates, configured bars, raw aliases, and conservation before recomputing the aggregate verdict.

This process topology is part of the runtime contract. A monolithic pytest process is not equivalent:
native-library lifetime interactions can outlive individual test groups. Fresh execution, verified
process-group cleanup, immutable plans, single-writer aggregation, and atomic summaries remain
mandatory even when all tests are otherwise green. Every child removes inherited `PYTHONPATH` and
sets `PYTHONNOUSERSITE=1`. The supervisor fingerprints the resolved Conda executable plus Conda/pip
metadata and import hooks for every direct and nested runtime declared by the catalog.

Long acceptance runs use one root lock and an atomic, authenticated, lane-major checkpoint. A
resumable row must match the frozen repository snapshot, semantic task plan, execution policy,
runtime fingerprints, task-specific log name and log hash, and verified process-group cleanup.
Ordinary terminal pytest outcomes and the narrowly authenticated, resource-clean GPU mutant timeout
defined above may advance only a contiguous prefix; all other timeouts, missing cleanup, worker
errors, and non-pytest/native-fatal exits do not. Fatal GPU evidence closes the run as `FAIL` without
admitting another GPU task. A lingering checkpoint beside an already published terminal summary is
reconciled from the authenticated summary instead of rerunning completed work.

The service catalog and generated code map define the exact current inventory; historical module and
test counts are intake evidence, not targets.

## Authority and trust

Current authority is limited to this file, `CONTEXT.md`, `docs/ARCHITECTURE.md`,
`docs/service_status.json`, `docs/CODE_MAP.md`, the owning module READMEs, and current tests. The
cleanup ledger is an operational record, not scientific authority. The pre-cleanup formula ledger,
old project narratives, old output verdicts, and the existing literature retrieval cache are
untrusted discovery material until their respective reset phases close.

No local RAG or knowledge graph is a trusted evidence source during the reset. Scientific claims must
return to the primary paper and exact equation/figure/table locator; project inference belongs in a
separate claim or audit packet.
