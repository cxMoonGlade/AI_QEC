# MPS/PEPS carrier roles and evidence-gated improvement route — 2026-07-16

## Outcome

The implementations are not alternative versions of one tensor-network task.

- The restricted MPS paths are one-dimensional Axis-1 verification executors. The MCWF path samples
  pure-state quantum trajectories; the QT path enumerates or samples branches of an approximate product
  channel. Neither is the production full-record backend, and both default to **no bond cap**.
- The PEPS path is a finite, open-boundary, two-dimensional data-qutrit pure-state trajectory carrier for
  the compiled QEC schedule. It performs selective measurements and emits the declared packed record, but
  it has separate state-truncation and Born-contraction approximations and its end-to-end entropy gate is
  currently red.
- Aer and ITensorMPS are useful one-dimensional circuit/state comparators. YASTN is the closest external
  finite-PEPS update and environment comparator. variPEPS is a periodic infinite-PEPS ground-state and
  CTMRG implementation. None is a direct oracle for the multi-round detector/observable record.

Therefore the designs must differ. MPS Schmidt truncation, PEPS environment-aware truncation, stochastic
branch-mass preservation, and approximate Born reads solve different numerical problems and require
different ledgers and acceptance gates.

Current verdict:

- `LITERATURE_ROLE_CLOSED`
- `ARCHITECTURE_ROLE_CLOSED`
- `CODE_ROLE_CLOSED`
- `RECORD_BRIDGE_OPEN`
- `PRODUCTION_PRUNING_CODE_BLOCKED`

## 1. Binding output and architecture

The simulator product is the multi-time detector/observable record, not an internal state, energy, or
local observable (`docs/SIMULATOR.md:9-12`). Carrier acceptance is explicitly defined on this record law;
state fidelity, bond dimension, local entropy, and local truncation objectives are insufficient by
themselves (`docs/SIMULATOR.md:69-84`).

The service architecture intentionally separates the two carriers:

| Carrier | Architecture status | Declared input | Declared output | Scientific boundary |
|---|---|---|---|---|
| Restricted Axis-1 MPS | `CORE` verification surface | sealed one-dimensional schedule, dimensions, explicit approximation controls | restricted execution/evidence manifest and sampled frequencies | finite-microstep verification, not production full-record (`docs/service_status.json:407-427`) |
| Single-wire PEPS | `RESEARCH` full-geometry carrier | XZZX schedule and explicit complex128 run specification | packed shots plus state/contraction ledgers | record interface is implemented, but finite-truncation full-record fidelity is open (`docs/service_status.json:430-455`) |

“Single wire” in the PEPS name means one physical ket leg of local dimension three at each data site; it
does not mean a one-dimensional chain. The state is a grid PEPS with one rank-at-most-five site tensor and
no tracked global canonical gauge (`carrier/peps/state.py:43-44,102-148`).

## 2. What each local implementation actually computes

### 2.1 Restricted MCWF/MPS

Scientific object: one stochastic pure-state trajectory under a finite-step quantum-jump approximation
to the compiled Axis-1 schedule.

Code evidence:

- `max_bond=None` is the default; the implementation explicitly describes itself as a finite-step
  quantum-jump approximation (`frontend/axis1_mcwf_mps_execution.py:109-132`).
- A supplied cap is applied to multi-site Hamiltonian gates and accompanied by a shadow Schmidt-tail
  diagnostic (`frontend/axis1_mcwf_mps_execution.py:1305-1347`).
- Joint no-jump and jump candidates deliberately use `max_bond=None`; their squared norms are read as
  physical branch probabilities before the chosen branch is normalized
  (`frontend/axis1_mcwf_mps_execution.py:1350-1444`).
- Multilevel projective measurement likewise computes each candidate norm before selection and
  normalization (`frontend/axis1_mcwf_mps_execution.py:1713-1795`).

This separation is mathematically necessary: a high fidelity between normalized conditional states can
coexist with a wrong pre-normalization branch mass.

### 2.2 Restricted QT/MPS

Scientific object: exact enumeration or stochastic sampling of the branches of the **declared finite-step
product formula**, not exact propagation of an arbitrary joint Lindblad generator.

Code evidence:

- `max_bond=None` is again the default; discarded-weight gates are opt-in
  (`frontend/axis1_qt_mps_execution.py:80-116`).
- A supplied cap is applied to two-site Hamiltonian gates. The diagnostic first forms an uncapped shadow
  state and calculates dense Schmidt tails across the affected cuts
  (`frontend/axis1_qt_mps_execution.py:2125-2258`).
- Collapse branches retain `weight * probability`; exceeding `max_branches` raises rather than dropping
  low-weight branches (`frontend/axis1_qt_mps_execution.py:2509-2535`).

The branch-count cap is therefore a fail-closed resource guard, not probability pruning. The current
Schmidt ledger is a separately reconstructed shadow diagnostic; it is not yet an authenticated event from
the actual Quimb split.

### 2.3 Finite qutrit PEPS trajectory

Scientific object: a pure-state trajectory on the two-dimensional data-register geometry, with local
qutrit leakage operations, repeated selective stabilizer measurements, terminal readout, and temporal
record folding.

Code evidence:

- Local Kraus outcomes use a boundary/exact RDM read to obtain branch probabilities, then apply and
  normalize the chosen branch (`carrier/peps/trajectory.py:406-444`).
- A stabilizer measurement first reads its Born probability, applies a selective tensor-train branch,
  truncates the grown path bonds, and renormalizes (`carrier/peps/trajectory.py:447-530`).
- Rounds execute the compiled pre-measure, measurement, and post-measure operations; terminal output is
  converted to the packed record interface (`carrier/peps/trajectory.py:600-669`).
- Boundary-MPS contraction is a separate approximation used to read norms and Born values
  (`carrier/peps/contraction.py:3-27`).

PEPS therefore has two independent approximation axes:

1. changing the represented trajectory state by cutting state bonds;
2. approximating contractions used to evaluate a branch probability or normalization.

Converging only the first axis cannot validate the second.

## 3. What the external implementations compute

The frozen code-navigation map is `docs/external_baselines/TENSOR_NETWORK_CODE_MAP.md`. Its role split is
supported both by upstream code and by the publications admitted to the current literature corpus.

| Implementation | Primary object and target | Useful comparison | Non-transferable assumption |
|---|---|---|---|
| Qiskit Aer MPS | qubit circuit executor with MPS gate updates and measurement sampling | qubit gate/sampling fixtures, SVD policy, state comparison | no qutrit PEPS, shared trajectory law, or full QEC record oracle |
| ITensorMPS | canonical MPS/MPO algorithms, apply/truncate/TDVP | actual canonical split callbacks, Schmidt spectra, alternate integrators | one-dimensional bridge semantics do not transfer to PEPS loops |
| YASTN MPS | finite OBC MPS for DMRG, TDVP, compression, expectations, and sampling | canonical/variational MPS compression and ledger design | general state algorithms do not automatically reproduce the Axis-1 trajectory object |
| YASTN fPEPS | finite/infinite square-lattice PEPS, NTU/cluster/full update, boundary MPS and CTM | closest independent state-update and environment comparator | its update metric and observables are not the detector/observable record |
| variPEPS | periodic unit-cell iPEPS, CTMRG, energy/gradient optimization | CTMRG convergence, SVD retry, environment-dimension diagnostics | thermodynamic-limit ground-state optimization is not finite OBC selective-measurement evolution |

Upstream code anchors and pinned commits are listed at
`docs/external_baselines/TENSOR_NETWORK_CODE_MAP.md:35-146`. In particular, the map routes finite PEPS
evolution to YASTN and periodic CTMRG to variPEPS, and records that none provides the full multi-round
record directly (`docs/external_baselines/TENSOR_NETWORK_CODE_MAP.md:11-18`).

## 4. Why the designs must differ: triple-evidence matrix

| Design distinction | Literature | Local code | Architecture/contract | Consequence |
|---|---|---|---|---|
| MPS cut is a bridge with Schmidt semantics | Paeckel, Secs. 2.4–2.6, Eqs. (13)–(18) | QT shadow reconstructs dense Schmidt tails (`axis1_qt_mps_execution.py:2219-2258`) | MPS is restricted one-dimensional verification | Schmidt discarded weight is a valid state diagnostic, but still needs a record bridge |
| PEPS internal edge lies in a loop | Evenbly, Secs. II–V, Eqs. (1)–(12); Lubasch, Sec. III.B.2 | `PepsState` tracks no global canonical form (`peps/state.py:102-113`) | PEPS is full two-dimensional geometry | Do not read a local PEPS spectrum as physical Schmidt weight; use environment-aware proposals |
| Unnormalized trajectory norm is probability mass | Jaschke, Sec. III.B, Eqs. (24)–(27); Sander, Eqs. (6)–(11), (42)–(45) | MCWF and PEPS read squared norms or Born weights before renormalization | product is a sampled record distribution | Ledger branch mass and conditional-state distortion separately |
| Finite bond is outside the available trajectory theorem | Sander, Theorem 2 and Eqs. (57)–(58) | bond cap is optional and changes Hamiltonian gate updates | MPS route is not production scaling | No theorem-backed universal `max_bond` threshold exists here |
| PEPS environment has its own approximation dimension | Lubasch, Sec. III.A; Naumann, Sec. 2.2 | boundary-MPS Born reads are separate from state cutting | PEPS emits both truncation and contraction ledgers | Sweep state rank and read-environment controls independently |
| Exact-cluster metric is not exact global evolution | Dziarmaga, Eqs. (2)–(5) | current FET uses a bond environment and sequential writes | local objectives cannot certify the full record | NTU/FET are comparator candidates, not acceptance oracles |
| External targets differ | Rams, Sec. 2.3; Naumann, Sec. 2 | external code map separates Aer, ITensor, YASTN, and variPEPS | external repositories are pristine reference inputs | Exchange frozen neutral fixtures; never import an upstream claim wholesale |

The full source identities, hashes, exact locators, disconfirmation checks, and gap ledger are in
`docs/simulator_validation/TENSOR_NETWORK_CARRIER_LITERATURE_AUDIT_2026-07-16.md`.

## 5. Premise correction: current dependence on pruning

The current verified MPS defaults are **uncapped**, as documented in
`docs/NUMERICAL_PROVENANCE.md:175-176` and implemented in both entry points. MPS pruning is a necessary
future scaling problem and an opt-in diagnostic today, not a currently accepted dependency of the
verified route.

The PEPS route does materially depend on bounded state and contraction resources. Its resource caps and
FET parameters are explicitly numerical-only (`docs/NUMERICAL_PROVENANCE.md:179-180`), and the end-to-end
entropy mismatch remains `0.10860941571062639` versus `2.0` (`docs/SIMULATOR.md:80-84`).

This asymmetry matters: the MPS task is to introduce caps without losing its existing uncapped reference;
the PEPS task is to recover a trustworthy bounded route while preserving exact d3 and independent read
references.

## 6. Concrete code finding before any algorithm change

The current PEPS FET contract and fallback behavior disagree:

- the module and function contract say that if no rank qualifies, the full identity insertion must be
  retained (`carrier/peps/fet.py:30-37,390-394`);
- the debug and ordinary paths instead return the best lossy candidate when no candidate clears the bar
  (`carrier/peps/fet.py:433-438,448-455`);
- the trajectory then applies whatever map is returned without a second acceptance check
  (`carrier/peps/trajectory.py:302-318`).

This is a fail-closed contract defect, not evidence that FET itself is the wrong algorithm. It should be
the first implementation correction after a separate `src/**` authorization, accompanied by a regression
test that corrupts every candidate and proves that the state remains unchanged.

## 7. Evidence-gated improvement route

### Phase 0 — make errors observable without changing production pruning

1. Authenticate actual MPS split events from the executing backend; retain the uncapped shadow only as an
   independent comparator.
2. Split every ledger into integrator, state truncation, environment contraction, sampling, and record
   folding components.
3. For stochastic paths, record raw branch mass before compression, compressed branch mass, conditional
   normalized-state distance, and whether branch selection changed under the paired uniform.
4. Make FET no-qualifier, nonfinite, indefinite-metric, and nonconverged outcomes identity/no-op
   transactions.

Acceptance: no scientific result changes; deliberate ledger corruption is detected; failed proposals do
not mutate state.

### Phase 1 — freeze lossless cross-library fixtures

1. MPS: compare small qubit gate/state/measurement fixtures across the uncapped local path, Aer,
   ITensorMPS, and YASTN.
2. PEPS: compare finite open-boundary qutrit one-gate and one-selective-measurement fixtures against the
   exact d3 state and exact contraction before any rank reduction.
3. Freeze index order, precision, boundary condition, gate convention, normalization convention, and RNG
   uniforms in neutral manifests executed in fresh isolated processes.

Acceptance: full-rank states, raw branch masses, outcome maps, and record folding agree inside declared
precision; a sign/index/order corruption is detected.

### Phase 2 — MPS cap experiment

1. Apply a candidate cap only after forming the uncapped branch operator result.
2. Gate separately on branch-mass distortion and conditional-state error; a normalized-state SVD tail is
   not allowed to hide probability loss.
3. Compare direct gate/SVD compression with a TDVP or variational-compression candidate on the same frozen
   fixtures. Treat Paeckel's error taxonomy as ledger structure, not a preferred winner.
4. Sweep cap, time step, and trajectory count independently.

Acceptance: exact small-system joint record TV and branch table pass a preregistered bound, paired-uniform
branch choices are stable, and convergence is monotone enough for a fail-closed selection policy. Aer,
ITensorMPS, and YASTN remain state-level comparators only.

### Phase 3 — PEPS state-update experiment

1. Compare lossless, current FET, and exact-cluster NTU proposals on the same frozen one-cut and
   selective-update fixtures.
2. Record Hermiticity residual, minimum metric eigenvalue, condition number, pseudo-inverse cutoff,
   restart outcome, objective residual, and identity fallback.
3. Sweep PEPS state bond and boundary-MPS or CTM environment bond independently.
4. Use YASTN finite fPEPS as the closest update comparator. Use variPEPS only for CTMRG convergence,
   gauge, SVD failure, and environment-dimension engineering.

Acceptance: exact d3 state and branch-probability checks pass; larger-environment improvement is verified
against an independent read, not assumed from the local objective.

### Phase 4 — record-law certification

For both carriers, approval is based on the complete detector/observable record, not the candidate local
metric:

1. no-truncation or full-rank reference first;
2. exact small-system joint record and per-prefix branch-table comparison;
3. cap/rank, environment-rank, time-step, and sampling sweeps kept separate;
4. paired seeds and uncertainty bounds for sampled TV;
5. adversarial repeated measurement, nonlocal gate, leakage, near-zero branch, and high-entanglement
   fixtures;
6. mandatory corruption falsifiers for probability normalization, record fold, gauge/index order, and
   truncation ledger.

Only after this phase may a local diagnostic be promoted into a bounded acceptance proxy, and only for the
regime empirically or analytically linked to the record gate.

## 8. Remaining literature prerequisite

The current source set closes role and algorithm semantics but not a local-error-to-sequential-instrument
bound. Before implementation of production pruning, a separate closure packet must examine quantum
instrument continuity, trace-distance data processing under adaptive measurements, and telescoping error
accumulation with branch-probability control.

Until that packet either produces a usable bound or formally selects the independent full-record oracle as
the only acceptance route, the status remains `RECORD_BRIDGE_OPEN / PRODUCTION_PRUNING_CODE_BLOCKED`.

No `src/**` change is authorized or made by this document.
