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
   production-scaling backends. `max_bond` is either `None` or a strictly positive integral value;
   booleans, floats, strings, zero, and negative values are rejected rather than coerced. A finite cap
   on a supported two-site unitary is applied through the pinned Quimb actual-split adapter: every
   forward-swap, operator, and reverse-swap SVD is ledgered, the conditional-state norm is restored
   only after its raw loss is recorded, and the resulting local discarded fractions are explicitly
   not a global state/record bound. Exact-branch ledgers weight path-local evidence by the incoming
   branch probability; sampled ledgers average path totals over the declared trajectory count, with
   trajectories that had no truncation event contributing zero. Each gate occurrence authenticates
   full sampled-trajectory coverage or unit exact-branch mass; incomplete coverage makes the ledger
   and acceptance fail closed. Once actual loss occurs, restricted finite-bond acceptance requires
   both explicit worst-cut and path-total discarded-weight gates; an observed lossless capped run
   needs no such gates. These
   gates remain heuristics, never production error bounds. Kraus/no-jump/jump operators remain
   uncapped because their raw norm carries physical branch probability; that probability is not a
   truncation score. Capped multi-site MCWF Hamiltonian clusters fail closed.
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
validated. A fresh-process replay must authenticate that result, and a primary-literature bridge must
still connect the local FET objective to the QEC entropy and complete record-law observables. Local
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
Torch/CUDA runtime. Independent CPU files use bounded concurrency constrained by `MemAvailable`,
host-memory/BLAS-heavy CPU files run serially, and GPU files run serially while holding the
cross-process GPU lock only for that phase. CUDA-Q is routed to its isolated environment.

This process topology is part of the runtime contract. A monolithic pytest process is not equivalent:
native-library lifetime interactions can outlive individual test groups. Fresh execution, verified
process-group cleanup, immutable plans, single-writer aggregation, and atomic summaries remain
mandatory even when all tests are otherwise green.

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
