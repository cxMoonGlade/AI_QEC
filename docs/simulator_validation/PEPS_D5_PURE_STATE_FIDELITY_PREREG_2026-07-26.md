# PEPS d5 pure-state fidelity — pre-registration

Status: **READY TO FREEZE, 2026-07-26.** No d5 target result has been run.
Predictions, fixture, controls, and decision bands become frozen only after
this document and every verdict-driving owner are committed. A miss is a
finding, not a reason to change the fixture or band.

## -1. Question charter

- **Decision and consequence:** determine whether at least one maintained
  finite-PEPS implementation can complete a 25-qubit 5-by-5 coherent
  non-Pauli circuit with global state fidelity at least `0.99` at an attainable
  state bond. Passing permits design of a separate d5 measurement/Record
  experiment. Failing redirects effort to MPS/isoTNS or a shallower bounded
  carrier; it does not permit lowering the band.
- **Importance x attackability:** d5 is the first data-register size beyond
  the current dense d3 carrier evidence, while `2^25` complex128 amplitudes
  remain directly materializable for an independent reference.
- **Reusable object/test:** one canonical gate-list fixture, dense reference,
  four isolated upstream adapters, a bond sweep, and physical corruptions.
- **Alternative formulations/invariants:** Torch tensor-axis and independent
  NumPy computational-basis bit-index replay on d3; unit norm; exact gate
  matrices; fixed row-major site/basis order; exact per-edge rank-growth
  ceiling.
- **Kill condition:** no candidate can materialize or independently contract
  the complete state within the declared resource envelope; the reference
  routes disagree on d3; a corruption is inert; or any claimed fidelity uses a
  local discarded-weight proxy.

Primary execution route: **Carrier/baseline evidence**, not a product-service
or `src/**` phase.

## 0. Grounding ledger

| sub-axis | mechanism / observable source | reading note | reused object |
|---|---|---|---|
| finite circuit PEPS update | Rudolph and Tindall, Sec. II, Eqs. (1)-(2), PDF p. 3 | `rudolph_tindall_gpu_peps_2507.11424.md` | pristine upstream implementations |
| finite open PEPS and contraction bond | Lubasch et al., Secs. II-III, Fig. 2, PDF pp. 2-3 | `lubasch_finite_peps_1405.3259_source_review.md` | 5-by-5 open square graph |
| normalized full-state fidelity | Evenbly, Sec. V, Eq. (12), PDF p. 6 | `evenbly_closed_loop_truncation_1801.05390_source_review.md` | new external-baseline metric owner |
| nonmonotonic approximate behavior | Patra et al., Appendix A, PDF p. 6 | `patra_gpeps_ibm_processors_2309.15642.md` | finding semantics |
| general exact no-go | Schuch et al., VOR PDF pp. 2-3 | `schuch_peps_complexity_prl_98_140506_source_review.md` | fixture-only claim boundary |

Closure packet:
`docs/simulator_validation/PEPS_D5_PURE_STATE_FIDELITY_LITERATURE_CLOSURE_2026-07-26.md`.

## 1. Frozen mechanism and fixture

The neutral fixture schema is
`error_coupling_simulator.external.peps_d5_pure_state_fixture.v1`.

- Lattice: open `5 x 5`; sites are row-major integers
  `q = 5 * row + column`.
- Complete-vector convention:
  - local basis is `[|0>, |1>]`;
  - tensor axes are `[q0, q1, ..., q24]`;
  - q0/axis 0 is the most-significant flat-vector bit, so
    `flat_index=sum_q bit(q)*2^(24-q)`;
  - a two-site gate uses basis `[|00>, |01>, |10>, |11>]`, and
    `targets[0]` is the left Kronecker factor/more-significant local bit;
  - matrix rows are outputs and columns are inputs;
  - operations execute by ascending index as `psi <- U_operation psi`.
- Initial state:
  - checkerboard-X sites `(row+column) mod 2 = 0`: `|0>`;
  - checkerboard-Z sites `(row+column) mod 2 = 1`: `|+>`.
- Ordered edge colors in every cycle:
  1. horizontal edges whose left column is even;
  2. horizontal edges whose left column is odd;
  3. vertical edges whose top row is even;
  4. vertical edges whose top row is odd.
  Within a horizontal color, serialization is ascending row then left column;
  within a vertical color it is ascending top row then column. Edges in one
  color are disjoint and may execute in parallel, but this is their canonical
  JSON order.
- On every ordered nearest-neighbour edge `(i,j)`, apply
  `U_ij(theta_c)=exp(-i theta_c P_i tensor P_j / 2)`, with `P=X`
  on the X sublattice and `P=Z` on the Z sublattice.
- After all four edge colors, apply `RY(phi_c)` to every site, with
  checkerboard sign `(-1)^(row+column)`, where
  `RY(phi)=exp(-i phi Y/2)=[[cos(phi/2),-sin(phi/2)],
  [sin(phi/2),cos(phi/2)]]`.
- Four cycles use, in order:

| cycle | `theta_c` | `phi_c` |
|---:|---:|---:|
| 0 | `0.17` | `0.11` |
| 1 | `0.23` | `-0.07` |
| 2 | `0.31` | `0.13` |
| 3 | `0.37` | `-0.19` |

`H=[[1,1],[1,-1]]/sqrt(2)`. All angles are radians and all gate matrices are
complex128. These are
controlled-fixture values, not calibrated hardware parameters. Every edge is
acted on exactly four times by an operator-Schmidt-rank-two gate, so the
direct, untruncated construction proves that an exact representation exists
with per-edge structural ceiling `D<=16`. This does not prove that every
simple-update implementation is lossless at `D=16`; that remains a frozen
prediction conditional on its reporting that no rank was discarded.

This is a coherent non-Pauli **d5 data-patch geometry benchmark**. It is not a
surface-code syndrome-extraction round and contains no ancillas, measurement,
reset, Kraus channel, leakage, detector fold, logical observable, or decoder.

## 2. Metric binding

Primary metric:

```text
F = |<psi_dense | psi_candidate>|^2
    / (<psi_dense|psi_dense> <psi_candidate|psi_candidate>)
```

The source convention is the normalized whole-network pure-state fidelity in
Evenbly Eq. (12). Values are accumulated in complex128; a reported value
outside `[0,1]` by more than `1e-10`, a non-finite norm, or a nonpositive norm
is a hard failure.

`docs/METRICS.md` registers this quantity only as an external pure-state
research diagnostic. The per-point metric owner is
`scripts/external_baselines/compare_peps_d5_complete_states.py`; the terminal
sweep/verdict owner is
`scripts/external_baselines/run_peps_d5_complete_state_sweeps.py`.
Independent formula, phase-invariance, dtype/shape, non-finite, identity, and
proxy firewall tests are in
`tests/test_external_peps_d5_pure_state_fidelity.py`. It is not a simulator
Record metric.

Forbidden substitutes:

- product of per-gate retained weights;
- local squared-singular-value tail;
- maximum bond dimension;
- BP/CTM/boundary-MPS residual;
- state norm alone;
- terminal sample agreement alone.

## 2a. Frozen predictions and decision bands

The primary target is cycle depth four.

| prediction | frozen band | class |
|---|---:|---|
| exact dense self-comparison | `1-F <= 1e-12` | (a) exact/numerical |
| d3 independent reference-route agreement | `abs(F_route_A-F_route_B) <= 1e-10` | (a) numerical |
| d5, `D=16`, complex128, authenticated no-rank-discard ledger | `F >= 1-1e-10`; otherwise `not_evaluable` | (b) conditional prediction |
| d5 primary useful result at any `D <= 16` | `F >= 0.99` | (c) go/no-go |
| d5 marginal result | `0.95 <= F < 0.99` | (c) classification |
| d5 low-fidelity result | `F < 0.95` | (c) classification |
| bond sweep | `F(D)` nondecreasing within `1e-8` for `D=1,2,4,8,16` | (b) prediction, not invariant |

If an implementation cannot run complex128, its result is a separate
precision leg and cannot satisfy the primary `D=16` prediction.

Resource gate per candidate/bond point:

- hard wall time: `1800 s`;
- peak host RSS: `64 GiB`;
- peak device allocation: `28 GiB`;
- full dense candidate payload: exactly `2^25` complex128 amplitudes in the
  declared basis. A library that cannot materialize this vector is
  `UNAVAILABLE`; no finite-boundary or approximate-overlap alternative is
  admitted to the primary gate.

A resource rejection is `UNAVAILABLE`, not low fidelity.

## 2b. Disconfirmation surface

The strongest competing explanation is that a high local retained-weight
product or stable contraction residual masks poor global state overlap on the
loopy square lattice. The complete dense overlap distinguishes that
explanation directly. Nonmonotonic `F(D)`, a high proxy with `F<0.95`, or
failure of the no-truncation `D=16` leg is a finding against the proposed
adapter or its semantics.

The Schuch result prevents promotion of a successful fixed-size run into a
general exact/scalable claim.

## 3. Independent ground truth

The production-under-test is each pristine external PEPS library. The
reference is a repository-owned dense worker that:

1. reads only the neutral JSON fixture;
2. hand-builds `X`, `Z`, `RY`, and the two-site exponential;
3. applies the ordered gates directly to a length-`2^25` complex128 vector;
4. imports no upstream PEPS package and consumes no candidate tensors,
   messages, gauges, contractions, or truncation diagnostics.

A second NumPy computational-basis bit-index implementation checks every d3
amplitude against the primary Torch tensor-axis replay before d5 execution.
The external-library d3 candidate is an integration control, not an
independent reference premise. The d5 reference and candidate dense vectors
are persisted only under ignored `outputs/`, with SHA-256, shape, dtype,
complete amplitude convention, fixture hash, environment identity, and
runtime metadata.

## 3a. Constraint ledger and corruption falsifiers

| invariant | exact assertion | deliberately broken input | required trip |
|---|---|---|---|
| fixture identity | canonical JSON hash, 25 sites, 40 unique edges, four appearances per edge, 160 two-site gates | delete operation 156: `cycle=2`, `targets=[11,12]`, `paulis=[Z,X]`, `theta=0.31` | semantic gate-ledger failure even with pinned-hash checking disabled, plus hash failure when enabled |
| gate unitarity | every gate satisfies `max|U^dagger U-I| <= 1e-12` | perturb element `[0,0]` of operation 156's matrix by `1e-3` | unitarity residual exceeds `1e-12` |
| half-angle convention | operation 156 equals `cos(0.31/2) I4-i sin(0.31/2)(Z tensor X)` elementwise within `1e-12` | construct it with `cos(0.31)` and `sin(0.31)` | closed-form equality fails |
| site/basis order | row-major site-to-axis map is exact and round-trips | swap axes 11 and 12 in candidate export | fidelity must fall by more than `1e-4` |
| dense reference independence | NumPy and primary dense routes agree on all d3 amplitudes within `1e-12` | reverse one route's two-qubit basis order | d3 comparison fails |
| physical-map sensitivity | correct candidate is compared with the exact same gate list | flip the sign of operation 156's `theta=0.31` in a separately replayed dense fixture | correct-versus-corrupted dense fidelity must fall by more than `1e-4` |
| truncation knob moves the object | `D=1` is the product-state control and `D=16` is the structural representation ceiling; candidate no-rank-discard must be separately authenticated | force every candidate bond to one | `F(D=16)-F(D=1) > 1e-4`; the conditional exactness prediction remains `not_evaluable` without the rank ledger |
| norm and finiteness | both norms finite and positive; dense reference norm residual at most `1e-12` | inject one NaN amplitude | hard failure before fidelity |
| proxy firewall | headline value is recomputed from complete states | replace it by retained-weight product | focused test rejects schema/source kind |

Each corruption must be demonstrated before the target result may receive a
verdict.

## 3b. Negative controls and non-degeneracy

- Multiplying either complete state by a unit-modulus global phase must change
  `F` by at most `1e-12`; a gate that rejects this inert control fails.
- Removing or sign-flipping the registered physical gate must reduce fidelity
  by more than `1e-4`.
- The bond knob is non-degenerate only if the `D=1` control is separated from
  `D=16` by more than `1e-4`.

## 4. Bounded simplifications

- The claimed object is exactly the pure-state fixture above. Missing Kraus,
  measurement, reset, leakage, and Record semantics are excluded regimes, not
  approximations to a claimed full-QEC result.
- Dense reference floating error is bounded operationally by d3 dual-route
  agreement, unitary/norm checks, and complex128 execution. No hardware-noise
  claim is made.
- Finite PEPS state-bond error is measured by the complete-state fidelity.
- Any finite contraction/environment approximation that prevents exact
  materialization of the complete candidate vector makes that leg
  `UNAVAILABLE`. No contraction-bond sweep is admitted as a substitute in
  this preregistration.
- The four-cycle fixture establishes no depth, distance, or random-circuit
  scaling law.

## 5. Epistemic status

- **(a) exact:** fixture identity, gate matrices, edge/rank ledger, basis map,
  dense-vector dimension, normalized-fidelity formula, corruption identities.
- **(b) predictions:** no-truncation numerical fidelity and bond-sweep
  direction.
- **(c) gates:** `0.99/0.95` usefulness bands and resource ceilings.
- Any d5 result remains provisional external baseline evidence. It is not
  simulator Record faithfulness, a product Carrier promotion, or evidence for
  d7.

## 6. Build organization and gate

- Builder A: `pepsy` full clone/environment/API adapter.
- Builder B: `TensorNetworkQuantumSimulator.jl` full
  clone/environment/API adapter.
- Builder C: YASTN/Quimb comparator and independent reference review.
- Root orchestrator: neutral fixture, dense workers, target execution,
  provenance, and final result packet.
- External source trees remain pristine; adapters live under
  `scripts/external_baselines/`.
- `compare_peps_d5_complete_states.py` owns a nonterminal per-point metric.
  Before the first external candidate,
  `peps_d5_physical_corruption_control.py` must compare the pinned reference
  with an intentional sign flip of operation 156 and demonstrate
  `1-F>1e-4`.
  `run_peps_d5_complete_state_sweeps.py` is the terminal owner for the exact
  `D=[1,2,4,8,16]` sweep, `1800 s` fresh-process timeout, `64 GiB` host and
  `28 GiB` device caps, monotonicity prediction, bond-knob nondegeneracy, and
  usefulness verdict. Its `--controls-only` mode must first pass the independent
  d3 Torch/NumPy reference and both commit-bound external D16 adapters before
  any d5 execution. A direct worker or comparator invocation cannot issue a
  terminal benchmark verdict.
- No `src/**` change is authorized by this phase.

Prerequisite gate:

| gate | status |
|---|---|
| premises closed | pass |
| standard metric bound | pass: Evenbly normalized whole-state fidelity |
| metric owner and independent tests | pending until committed |
| predictions frozen | pending until committed |
| independent ground truth | pass by design; must pass d3 before target |
| constraint falsifiers registered | pass by design; must demonstrate trips |
| simplifications bounded | pass for the frozen pure-state object |
| controls registered | pass |
| **preregistration gate** | **BLOCKED UNTIL COMMIT + d3/falsifier gate** |

Theory-first verdict: owner code may be completed and tested, but **d5 target
execution is prohibited until a scoped freeze commit exists and every d3 and
corruption control passes from committed code.**
