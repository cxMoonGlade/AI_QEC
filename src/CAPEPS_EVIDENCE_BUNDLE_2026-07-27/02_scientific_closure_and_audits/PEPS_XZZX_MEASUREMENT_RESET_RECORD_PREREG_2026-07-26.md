# PEPS XZZX measurement/reset/Record bridge — preregistration

Status: **FROZEN, 2026-07-26.** No tracer, d3, or d5 target result
described here has been run or inspected. The first commit adding this file is
the freeze point. A miss is a finding; fixture identities, bands, or branch
rules must not be changed after seeing a target result.

Literature prerequisite:
`PEPS_XZZX_MEASUREMENT_RESET_RECORD_LITERATURE_CLOSURE_2026-07-26.md`,
with `closure_status: closed` for this bounded all-qubit experiment.

## -1. Question charter

- **Decision and consequence:** determine whether a finite-bond, explicit-
  ancilla Quimb PEPS can preserve the probability/state semantics of two
  XZZX extraction rounds closely enough to justify further two-dimensional
  trajectory work. A passing tracer and d3 gate permits d5. A d5 pass remains
  research evidence for one conditioned all-qubit trajectory.
- **Importance x attackability:** d3 has a complete dense oracle, while d5 has
  the requested 25 data qubits plus 24 measured/reset ancillas and remains
  representable by an independent Aer MPS with an explicit, audited bond cap.
- **Reusable object/test:** one exact small-law tracer, two hash-bound
  Stim-derived fixtures, a shared selective-instrument protocol, independent
  dense/Aer truth, complete-vector fidelity, and registered
  physical/semantic corruptions.
- **Alternative formulations/invariants:** dense and Aer complete vectors
  must agree on d3; dense and Aer branch states and
  conditional probabilities must agree; reset state and absolute XOR fold are
  structural invariants.
- **Kill condition:** target execution is forbidden if the tracer full law
  fails, dense/Aer disagree on d3, any required corruption is inert, the
  d3 usefulness gate fails, Aer applies a hidden MPS cap/truncation, or d5
  fidelity is replaced by a local/boundary proxy.

Primary route: **external carrier/baseline evidence**. No `src/**` change,
production promotion, or simulator claim is authorized.

## 0. Grounding ledger

| sub-axis | source | bound object |
|---|---|---|
| XZZX geometry and local-H equivalence | Bonilla Ataides et al., Fig. 1, PDF p. 2 | fixture family |
| ordered ancilla check shell | Darmawan et al., Fig. 2, PDF p. 3 | tracer and interpretation of the Stim-derived shell |
| consecutive-round defect | Bonilla Ataides et al., Fig. 5, PDF p. 6; Darmawan et al., Sec. II.B, PDF p. 3 | temporal detector semantics |
| selective Born mass and poststate | Czajkowski and Grilo, Sec. 2.2, Eq. (1), PDF p. 5 | measurement/reset operator |
| ordered outcome law | Czajkowski and Grilo, Sec. 3.1, Eq. (9), PDF p. 7 | branch-mass ledger |
| fixed reset to zero | Ghosh et al., Fig. 1, PDF p. 2 | `MR` instrument |
| normalized whole-state overlap | Evenbly, Sec. V, Eq. (12), PDF p. 6 | exact state fidelity |
| finite-PEPS diagnostics and terminal limits | Rudolph and Tindall, Sec. II, PDF pp. 3-4 and 9 | proxy firewall and no-go |
| exact complexity boundary | Schuch et al., VOR PDF pp. 2-3 | fixed-size claim boundary |
| coordinates, schedule, and absolute rows | committed neutral XZZX emitter and its corruption-tested d7 fixture | exact engineering input, not a literature premise |

## 1. Frozen fixtures

All JSON identities use UTF-8 encoding of
`json.dumps(payload, allow_nan=False, indent=2, sort_keys=True) + "\n"`.

### 1a. Exactly enumerable tracer

The tracer is the same parameterized Stim-derived family at `distance=2`,
`rounds=2`, not a hand-designed substitute.

- schema:
  `error_coupling_simulator.external_xzzx_record_peps.fixture.v1`;
- 4 data qubits, 3 syndrome ancillas, 7 active qubits;
- 57 base operations, 6 measured/reset ancilla events, 10 raw measurements,
  5 detectors, and 1 observable;
- detector arities `{1:1,2:3,5:1}` and observable arity `2`;
- transformed Stim SHA-256
  `18492ad9bc8b286d1cf9f97f45546fac40552a10d83be9ef61fa892a941cb671`;
- canonical base JSON SHA-256
  `dbf2a0979c9a4cd0a95f2afe393083d97a27ea1e90720596352a191010beb0f5`;
- data ids `[0,2,3,5]`;
- absolute detector rows
  `[[1],[3,0],[4,1],[5,2],[9,8,7,6,4]]`;
- absolute observable row `[[7,6]]`.

After each block of three `MR` events, insert `RY(0.02)` on the four data ids
in ascending order. The enumeration-spec schema is
`error_coupling_simulator.external_xzzx_record_peps.enumeration_spec.v1`;
its canonical SHA-256 is
`02aef76a65383fbfec9a2f3e0b62a7dd0691a574ee739a4b6b33326ba13681ca`.
The exact object before pretty serialization is:

```json
{"base_fixture_sha256":"dbf2a0979c9a4cd0a95f2afe393083d97a27ea1e90720596352a191010beb0f5","distance":2,"intervention":{"after_rounds":[0,1],"angle_radians":0.02,"gate":"RY","placement":"after_each_complete_syndrome_round_before_the_next_base_operation","targets":"all_data_qubits_in_ascending_dense_id_order"},"reference":{"method":"dense_complete_enumeration","raw_outcome_count":10,"support_size":1024},"rounds":2,"schema":"error_coupling_simulator.external_xzzx_record_peps.enumeration_spec.v1","stim_circuit_sha256":"18492ad9bc8b286d1cf9f97f45546fac40552a10d83be9ef61fa892a941cb671"}
```

All 1024 raw strings are enumerated, including structural-zero branches. The
raw ten-bit trajectory law and the folded five-detector/one-observable Record
law are scored separately.

### 1b. Stim-derived d3/r2 and d5/r2 base fixtures

Schema:
`error_coupling_simulator.external_xzzx_record_peps.fixture.v1`.

The base emitter reuses the existing local-H transformed Stim construction but
is a separate parameterized entry point; it must not change the existing d7
emitter's bytes or frozen hashes. The parent emitter source at freeze time has
SHA-256
`132fdc2d1eb56bf3791ad320bbb65b558e37350575e6174d4bd874cedb2c058d`.

| field | d3/r2 | d5/r2 |
|---|---:|---:|
| data qubits | 9 | 25 |
| syndrome ancillas | 8 | 24 |
| active qubits | 17 | 49 |
| raw measurements | 25 | 73 |
| measured/reset ancilla events | 16 | 48 |
| detectors | 16 | 48 |
| observables | 1 | 1 |
| operations before inserted `RY` | 154 | 490 |
| detector arities | `{1:4,2:8,3:2,5:2}` | `{1:12,2:24,3:4,5:8}` |
| observable arity | 3 | 5 |
| transformed Stim SHA-256 | `7067b1241251bd7558e7dc85b2f84bc13a45c1217a49f8fcfa2e51205879ecb0` | `be26b8708efe36a027bcf79074bc936de552b1a5d22b35b627d7d9cdbb27f008` |
| canonical base JSON SHA-256 | `3b2bf7d81f7241e0a3b6abb14c76474c362e696cf374c55e20e3d121946bbf3c` | `659fda875a91f2a6e3c64f8f03487b5a431edecb9849dd897bf2e6f390583495` |

The fixture's dense qubit ids, coordinates, data ids, checkerboard-H-frame
ids, operation order, measurement columns, reset flags, and absolute XOR rows
are immutable inputs.

### 1c. Frozen non-Pauli intervention and branch seeds

After each complete block of `d^2-1` syndrome `MR` events, and before the next
base operation, apply to every data qubit in ascending dense-id order

```text
RY(0.02) = [[cos(0.01), -sin(0.01)],
            [sin(0.01),  cos(0.01)]].
```

This occurs after syndrome rounds `0` and `1`; the second insertion is before
terminal data closure. The angle is a controlled project value in radians,
not hardware calibration.

The canonical run-spec identities are:

| distance | Aer `seed_simulator` | run-spec SHA-256 |
|---:|---:|---|
| 3 | `2026072603` | `11e86c8d205899d51440a7fab32dc31f046e723a047c4c7bc8fe9fed3f7e15b9` |
| 5 | `2026072605` | `092353542f2e9e329f4d3ed735d0e6a10caa88bc048478ee15cc06aefc60ef23` |

Each run spec uses schema
`error_coupling_simulator.external_xzzx_record_peps.run_spec.v1`, binds the
base and Stim hashes, sets `rounds=2`, requests one Aer-MPS shot, and contains
the intervention placement above.

The exact two payload objects, before the canonical pretty serialization
defined at the start of this section, are:

```json
{"base_fixture_sha256":"3b2bf7d81f7241e0a3b6abb14c76474c362e696cf374c55e20e3d121946bbf3c","distance":3,"intervention":{"after_rounds":[0,1],"angle_radians":0.02,"gate":"RY","placement":"after_each_complete_syndrome_round_before_the_next_base_operation","targets":"all_data_qubits_in_ascending_dense_id_order"},"reference_branch":{"sampler":"qiskit_aer_matrix_product_state","seed_simulator":2026072603,"shots":1},"rounds":2,"schema":"error_coupling_simulator.external_xzzx_record_peps.run_spec.v1","stim_circuit_sha256":"7067b1241251bd7558e7dc85b2f84bc13a45c1217a49f8fcfa2e51205879ecb0"}
```

```json
{"base_fixture_sha256":"659fda875a91f2a6e3c64f8f03487b5a431edecb9849dd897bf2e6f390583495","distance":5,"intervention":{"after_rounds":[0,1],"angle_radians":0.02,"gate":"RY","placement":"after_each_complete_syndrome_round_before_the_next_base_operation","targets":"all_data_qubits_in_ascending_dense_id_order"},"reference_branch":{"sampler":"qiskit_aer_matrix_product_state","seed_simulator":2026072605,"shots":1},"rounds":2,"schema":"error_coupling_simulator.external_xzzx_record_peps.run_spec.v1","stim_circuit_sha256":"be26b8708efe36a027bcf79074bc936de552b1a5d22b35b627d7d9cdbb27f008"}
```

### 1d. Basis and operation semantics

- Local basis is `[|0>,|1>]`.
- Qubit ids are the physical-site labels in both the arbitrary-graph PEPS and
  the reference.
- Dense flat-vector order is the fixture's complete ordered id list, with the
  first id the most-significant tensor axis.
- Two-qubit basis is `[|00>,|01>,|10>,|11>]`; the first listed qubit is the
  left Kronecker factor.
- `R` is reset to `|0>`; `RX` is reset to `|0>` then `H`; `MX` is `H` then
  Z measurement; `MR` uses the selective reset instrument below.
- `CX` control and target are exactly the listed first and second qubits.
- Operations execute in ascending list position. No commutation or layer
  reordering is allowed.

For an `MR` outcome `b`,

```text
A_b = I_rest tensor |0><b|
p_b = <psi|A_b^dagger A_b|psi>/<psi|psi>
|psi_b> = A_b|psi>/sqrt(p_b <psi|psi>).
```

Candidate and reference are conditioned on exactly the same raw outcomes.
Terminal measurements do not reset.

## 2. PEPS and reference controls

### 2a. Candidate PEPS

Use the pristine, commit-bound Quimb clone already isolated in
`ecs-baseline-quimb-peps`. `CircuitPEPSSimpleUpdate` is constructed on the
undirected set of all unique two-qubit fixture interactions, with one tensor
per active qubit; no dummy lattice sites are added.

- dtype: complex128;
- tracer/d3 state bonds: `D in [1,2,4,8]`;
- d5 state bonds: `D in [1,2,4]`, with `D=8` a predeclared optional resource
  leg that cannot replace the primary `D=4` point;
- simple-update singular-value cutoff: exactly `0.0`;
- d5 measurement-RDM graph radii: `0,1,2,3`;
- the tracer and d3 use the complete graph, verified by equality between the
  selected tensor-id set and the entire tensor network rather than by assuming
  that a guessed radius is complete;
- gauges and state-bond diagnostics are retained but cannot determine the
  verdict;
- because the high-level `partial_trace` and `sample` methods are unsupported,
  the audited public composition is `get_state(absorb_gauges="return")`,
  `partial_trace_cluster`, a rank-one local tensor gate, and reconstruction of
  `CircuitPEPSSimpleUpdate`;
- each run is a fresh process and binds clone commit/tree, installed source
  bytes, environment lock, fixture/run-spec hashes, and repository inputs.

### 2b. Independent dense d3 reference

A repository-owned NumPy worker reads only neutral JSON and hand-builds
`H`, `RY`, `CX`, `CZ`, projectors, and reset operators. It applies gates by
explicit tensor-axis permutation to a complete complex128 vector and imports
neither Quimb nor Qiskit.

It owns:

- all 1024 tracer raw paths and their folded laws;
- the selected d3 branch probabilities and cumulative mass;
- the complete normalized d3 state immediately after the round-1 `RY` and
  before terminal data measurements;
- terminal conditional probabilities and the exact raw/absolute fold.

### 2c. Independent Aer-MPS reference

Use Qiskit Aer `method="matrix_product_state"` in the isolated
`ecs-baseline-aer` environment and pristine clone identity already present in
the repository.

- precision is double;
- MPS truncation threshold is exactly `0.0`;
- `matrix_product_state_max_bond_dimension` is explicitly `65536`;
- `mps_log_data=True`; the effective option value, every logged bond
  dimension, positive discarded value, and saved Schmidt-vector length are
  retained;
- returned Aer metadata must exactly echo cap `65536`, threshold `0.0`, and
  the presence of `MPS_log_data`; a missing or changed value makes the
  reference `UNAVAILABLE`;
- the reference is `UNAVAILABLE` unless the maximum across logged bond
  dimensions and saved Schmidt-vector lengths is strictly less than `65536`,
  `discarded_value_count == 0`, and `discarded_value_sum == 0.0`;
- one shot and the frozen seed select the primary branch;
- no retry or reseed is allowed;
- the MPS is saved immediately after the second `RY` and before terminal data
  measurements;
- each measurement writes one separately addressed classical bit, so the
  worker reads columns individually rather than parsing a backend-formatted
  aggregate bitstring; the explicit column map is independently tested;
- every returned MPS tensor, Schmidt vector, physical-index convention, norm,
  and maximum realized bond is recorded.

Aer and dense NumPy must agree on d3 before Aer can serve as the d5 reference.
The candidate never consumes Aer tensors, gauges, Schmidt values, or
contraction paths; it consumes only the frozen raw branch bits.

Forced-bit equality makes the realized fold a plumbing invariant, not
Record-law evidence. Only the enumerated tracer owns Record-law TV.

### 2d. Alternate d3 branch

Besides the frozen sampled branch, d3 executes one deterministic alternate:

1. copy the primary outcome at every earlier column;
2. scan only the measured/reset (`MR`) columns in ascending order, excluding
   all terminal data measurements;
3. at the first scanned column whose opposite outcome has dense conditional
   probability at least `1e-8`, choose that opposite outcome;
4. for every later `MR` and terminal column choose the larger dense
   conditional probability, breaking an exact tie toward zero.

If no such column exists, the alternate leg is `UNAVAILABLE` and d5 is
blocked. The alternate must pass the same `D=8` complete-state fidelity,
complete-graph probability-error, log-mass, reset, and realized-fold bands as
the primary d3 branch. The rule is frozen; a favorable branch may not be
hand-selected.

### 2e. Strongest competitor and disconfirmation surface

The strongest competing explanation for an apparently successful PEPS state
is that simple update preserves a high normalized state overlap while the
finite-cluster measurement path misestimates conditional Born mass. The
distinguishing observation is therefore conjunctive: state fidelity and the
registered probability/log-mass/reset gates must all pass. In particular,
`F>=0.99` with either mass band failing is frozen as
`state-useful/mass-unresolved`, never a conditioned-trajectory pass. A
dense/Aer d3 mismatch instead diagnoses the reference translation and makes
the d5 reference unavailable; a proxy overlap cannot rescue either failure.

## 3. Registered metrics

### 3a. Full-law total variation

For the tracer,

```text
TV(p,q) = 0.5 * sum_x |p(x)-q(x)|.
```

It is evaluated separately on the raw ten-bit support and on the complete
folded detector/observable support. Folded TV is the existing
`docs/METRICS.md` full joint Record quantity. Raw-trajectory TV uses the same
formula on a different declared object; before target execution it must be
added as a bounded research diagnostic with its own owner, support-order test,
half-factor test, normalization test, and a firewall preventing it from being
labelled `Record`.

### 3b. Complete-vector d3 fidelity

Immediately before terminal data measurement,

```text
F = |<psi_ref|psi_candidate>|^2
    / (<psi_ref|psi_ref><psi_candidate|psi_candidate>).
```

Both d3 operands are complete one-dimensional complex128 vectors in the
frozen basis, so the registered external finite-PEPS formula and decision
bands apply. A new XZZX per-point owner must bind this fixture/checkpoint and
pass the existing formula, dtype/shape, order, identity, phase, non-finite,
and proxy-firewall tests before any target value is accepted.

The existing `compare_peps_d5_complete_states.py` owner is specific to the
older square-lattice fixture and schemas. Only its normalized-overlap formula
is reusable. It is not an owner for either XZZX target.

### 3c. Complete 25-data-vector d5 fidelity

At the preterminal checkpoint, every one of the 24 syndrome ancillas has just
undergone a rank-one reset. The exact state therefore factorizes as

```text
|Psi> = |psi_data> tensor |0>^24.
```

The Quimb candidate must first demonstrate that every reset ancilla
physical-`1` tensor slice is a structural zero. The Aer reference instead
demonstrates the gauge-invariant condition
`Tr(rho_ancilla |1><1|)<=1e-10` from an exact one-site reduced density matrix;
an individual Aer MPS tensor slice is not a valid gauge-invariant check. Both
paths then project every ancilla physical leg onto zero and exactly contract
the complete data state into all `2^25` complex128 amplitudes, ordered by
ascending fixture `data_qubits`. One such vector occupies exactly 512 MiB.

No boundary compression, contraction bond, tensor truncation, sampled
amplitude estimator, or partial vector is permitted during this extraction.
The resulting reference and candidate are complete vectors for the declared
25-data pure state, so the registered normalized complete-vector formula
applies. The same XZZX per-point owner must bind the structural-reset
projection and sorted data-axis convention.

If either complete data vector or an exact contraction path cannot be produced
inside the resource gate, d5 fidelity is `UNAVAILABLE`. An exact direct
MPS/PEPS scalar overlap is mathematically valid but is not admitted here unless
it is separately registered in `docs/METRICS.md` and independently shown to
match complete-vector fidelity within `1e-10` on tracer and d3. Finite-boundary
overlap remains forbidden.

### 3d. Branch-mass and reset metrics

For each measurement column `k`, retain the reference and candidate
conditional probability of the forced bit. Report:

```text
max_probability_error = max_k |p_candidate,k-p_reference,k|
log_branch_mass_error =
    |sum_k log(p_candidate,k)-sum_k log(p_reference,k)|.
```

A selected outcome with reference probability below `1e-12`, or zero candidate
probability for the selected bit, is a hard branch error. No probability floor
is allowed. Every reported Bernoulli pair must also satisfy
`abs(p0+p1-1)<=1e-10`. Approximate d5 cluster probabilities are labelled by
their graph radius and never described as an exact branch-law certificate.

After every `MR`, the measured ancilla's normalized one-site density matrix
must have trace distance from `|0><0|` at most `1e-10` for tracer/d3 and
`1e-8` for d5. Its physical-`1` tensor slice must be a structural zero at the
preterminal Quimb snapshot. At the Aer checkpoint, the projected
physical-`1` sector weight must instead be at most `1e-10`. These are reset
checks, not global-state metrics.

### 3e. Metric owners required before target execution

The XZZX bridge adds one owner,
`scripts/external_baselines/compare_xzzx_record_peps.py`, with these
single-object metric registrations in `docs/METRICS.md`:

| metric object | epistemic class | independent tests required |
|---|---|---|
| XZZX complete-vector fidelity at a hash-bound checkpoint | (c) for usefulness verdicts | formula, complex128 shape/order, identity, global phase, orthogonality, non-finite input, and proxy rejection |
| tracer raw-trajectory TV on the declared ten-bit support | (b) | support order, half factor, normalization, structural-zero support, and non-Record label firewall |
| selected-branch maximum conditional-probability error | (c) | maximum over aligned columns, boundary values, column mismatch, and non-finite rejection |
| selected-branch absolute log-mass error | (c) | independent product/log-sum equality, zero-probability hard error, omission detection, and non-finite rejection |
| post-reset one-site trace distance to `|0><0|` | (a) | Hermiticity/trace checks, analytic diagonal and coherent controls, thresholds, and tensor-slice-versus-RDM representation firewall |

These registrations and tests are target-blocking. The owner must bind the
fixture/run-spec hashes, exact checkpoint, probability-column order, branch
bits, data-axis order, and reference/candidate identities. No old-fixture
schema is accepted through compatibility coercion.

## 4. Frozen predictions and decision bands

| object | frozen gate or band | class |
|---|---:|---|
| tracer dense probability sum | `abs(sum p-1) <= 1e-12`, structural-zero branches retained | (a) |
| tracer Quimb probability sum at `D=8`, cutoff 0, verified-complete graph | residual `<=1e-10` | (a) |
| tracer Quimb raw-law TV at the same point | `<= 1e-8` | (b) |
| tracer Quimb folded-Record TV at the same point | `<= 1e-8` | (b) |
| tracer non-Pauli nondegeneracy | `TV_Record(RY=0.02,RY=0) > 1e-6` | (c) |
| dense vs Aer d3 complete-state fidelity | `1-F <= 1e-10` | (a) |
| dense vs Aer d3 per-step probability error | `<= 1e-10` | (a) |
| dense vs Aer d3 log-branch-mass error | `<=1e-9` | (a) |
| d3 useful PEPS primary and alternate points, each at `D=8` | `F>=0.99`, complete-graph maximum probability error `<=5e-3`, log-mass error `<=1e-1`, all reset checks and realized fold exact | (c) go/no-go |
| d3 marginal state result | `0.95<=F<0.99` | (c), blocks d5 |
| d3 low state result | `F<0.95` | (c), blocks d5 |
| d3 bond sweep | `F(D)` nondecreasing within `1e-8` | (b), reported finding rather than invariant |
| d3 bond-knob nondegeneracy | `abs(F(D=8)-F(D=1)) > 1e-4` | (c), otherwise adapter knob is not evidenced |
| d5 useful conditioned trajectory, primary `D=4` | complete-data-vector `F>=0.99`, radius-3 maximum probability error `<=1e-2`, radius-3 log-mass error `<=5e-1`, reset and realized-fold checks exact | (c) |
| d5 state-useful / mass-unresolved | exact `F>=0.99` but either mass band fails | (c), not a trajectory pass |
| d5 marginal state | exact `0.95<=F<0.99` | (c) |
| d5 low state | exact `F<0.95` | (c) |
| d5 complete 25-data vector absent | `UNAVAILABLE` | fail-closed |

Increasing `D` and graph radius is predicted to reduce error but is not an
invariant of simple update. Nonmonotonicity is reported and does not authorize
discarding an unfavorable point.

Per candidate/bond resource gate:

- wall time `1800 s`;
- peak host RSS `64 GiB`;
- peak device allocation `28 GiB`;
- exact complete-vector contraction path/intermediate must stay within those
  limits;
- one fresh process per point;
- points execute in ascending `D`, and an unavailable larger point does not
  erase a completed smaller point.

## 5. Constraint ledger and corruption falsifiers

| invariant | deliberate corruption | required trip before d5 |
|---|---|---|
| canonical fixture and run-spec identity | change one byte, distance, seed, intervention placement, or absolute row | hash/schema validator rejects |
| existing d7 fixture remains frozen | route d3/d5 through an edit of the d7 emitter | d7 byte/hash regression fails |
| local-H XZZX frame | delete the first data-frame `H` pair around an entangler | d3 complete-state or probability corruption is nonzero by more than `1e-8` |
| `CX` direction | swap control and target at the first non-symmetric tracer `CX` | tracer raw or folded TV exceeds `1e-8` |
| reset erases the branch | replace the first `MR` by measurement without reset | tracer raw or folded TV exceeds `1e-8`; post-reset state check fails |
| reset map itself | replace `A_1=|0><1|` by `|1><1|` | post-reset structural-zero/RDM check fails |
| coherent non-Pauli intervention | set every `RY` angle to zero | tracer folded-Record TV exceeds `1e-6` |
| intervention sign | replace `0.02` by `-0.02` | d3 complete-state or probability corruption exceeds `1e-8` |
| intervention placement | move both `RY` blocks after terminal measurement | tracer/d3 state or law corruption exceeds `1e-8` |
| measurement basis | omit the `H` implementing the first X readout | tracer/d3 probability or state corruption exceeds `1e-8` |
| Born normalization | on the fixed synthetic state `sqrt(0.8)|0>+exp(i*pi/7)sqrt(0.2)|1>`, choose zero but normalize by the other outcome probability | norm/mass invariant fails by more than `1e-8` |
| projector completeness | multiply one measurement projector by `0.9` | `p0+p1` residual exceeds `1e-10` |
| cumulative path mass | on the fixed synthetic selected probabilities `[0.8,0.3]`, omit the first factor | log-mass ledger differs from the independent product by more than `1e-8` |
| absolute Record rows | replace one terminal arity-five row by a rectangular two-column XOR | synthetic raw-vector fold and at least one enumerated tracer event disagree |
| qubit/amplitude order | reverse axes in one operand of the fixed asymmetric two-qubit vector proportional to `[1,2i,3+4i,5]` | complete-vector identity test fails and d5 extractor order test fails |
| exact d5 fidelity | return retained-weight product, cluster overlap, finite-boundary overlap, partial vector, or sampled estimator | metric validator returns `UNAVAILABLE`/rejects; no numeric fidelity verdict |
| Aer cap firewall | run a Bell-pair control with MPS maximum bond one and `mps_log_data=True` | a positive discarded weight or cap saturation must be logged and the reference rejected |
| global phase invariance | multiply one complete vector by unit-modulus phase | fidelity changes by at most `1e-12` |
| independent reference | import Quimb in dense truth or reuse candidate gauges/tensors in Aer truth | static/process isolation test fails |

Every corruption must be demonstrated in tests or a pre-target control run.
An inert corruption blocks target execution; it is not silently removed from
the ledger.

## 6. Bounded simplifications and epistemic limits

| simplification | exact bound relative to declared target | excluded inference |
|---|---|---|
| two-level qubits only | zero representation error for the declared all-qubit circuit | unbounded relative to retained leakage/qutrit/Kraus dynamics |
| no stochastic noise channel | exact for the declared coherent fixture | no hardware, threshold, decoder, LER, or leakage claim |
| exactly two syndrome rounds plus terminal closure | exact schedule match for the fixtures | no long-time or round-scaling claim |
| fixed `RY(0.02)` | exact controlled intervention | no physical calibration or generic non-Pauli-noise claim |
| sampled/alternate d3 branches | exact conditional checks for those branches | no d3 full-law claim beyond the tracer |
| one sampled d5 branch | exact branch identity | no d5 full-law, rare-event, or worst-branch claim |
| finite simple-update `D` | explicitly swept approximation | bond dimension is not an error bound |
| finite-radius d5 measurement RDM | selected-prefix empirical trajectory gate at each declared radius | not an exact full branch-law or Record-TV certificate |
| complete d5 data-vector contraction subject to resources | exact if all `2^25` amplitudes are produced after structural ancilla reset, otherwise unavailable | no approximate-overlap substitution |

The no-Kraus simplification is allowed because the user's immediate gate is
whether an all-qubit d5 can run at useful fidelity. It does **not** resolve the
larger leakage-reconstruction claim.

### 6a. Disjoint build and review ownership

At least three owners work on non-overlapping implementation surfaces. No
owner may validate its own target artifact:

| role | exclusive build surface |
|---|---|
| fixture/dense owner | parameterized emitter, exact dense instrument, branch enumeration, and fold tests |
| Aer owner | isolated Qiskit translation, classical-column map, MPS/log metadata, and reference extraction tests |
| Quimb owner | PEPS gate/reset/RDM adapter, graph coverage, bond/radius runs, and candidate extraction tests |
| metric/verdict owner | XZZX comparator, schemas, `docs/METRICS.md`, boundary/corruption tests, and verdict assembly |
| artifact-only reviewer | read-only recomputation of hashes, schema/object identities, acceptance bands, corruptions, process isolation, and final evidence; edits and target execution forbidden |

The artifact-only reviewer is not led by any build owner and receives only
committed inputs plus immutable output artifacts. Missing ownership,
cross-consumption of private tensors/gauges, or reviewer participation in an
implementation makes the corresponding target result unavailable.

## 7. Execution and stopping rule

1. Commit this preregistration and its closed literature packet.
2. Add tests first for fixture hashes, instruments, folding, metric firewalls,
   reference isolation, and all registered corruptions.
3. Implement neutral emitters/workers only under
   `scripts/external_baselines/`; preserve external clones.
4. Run the tracer full-law gate in fresh processes.
5. Run dense/Aer d3 agreement, then the two d3 branches and
   `D=[1,2,4,8]`; `D=8` is the primary gate.
6. If and only if every mandatory tracer/reference/corruption gate passes and
   both d3 branches are useful at the primary `D=8` point, run d5 at
   `D=[1,2,4]` in ascending order. `D=8` remains an optional resource leg.
7. Do not inspect or tune around d5 while a point is running. Stop a point at
   the resource gate and record `UNAVAILABLE`.
8. Persist immutable JSON evidence under ignored `outputs/` with input/output
   hashes, runtime/environment/clone identity, peak resources, exact versus
   approximate labels, and the terminal verdict.

## 8. Preregistration gate

| prerequisite | status |
|---|---|
| literature closure | pass for the bounded all-qubit experiment |
| question/mechanism/observable frozen | pass |
| fixture, intervention, and seeds frozen | pass |
| full-Record TV and complete-vector fidelity formulas/bands | registered |
| XZZX complete-vector per-point owner | fixture/checkpoint/order and inherited independent metric tests required before target |
| raw-trajectory TV diagnostic | owner and independent object/support/firewall tests required before target |
| selected-branch probability/log-mass owners | named registrations and independent formula/alignment/zero tests required before target |
| reset trace-distance owner | named registration and analytic/RDM representation tests required before target |
| d5 complete 25-data-vector extraction | exact structural-reset/projection/order tests required before target; proxy use forbidden |
| independent truth | dense d3 plus isolated Aer MPS design fixed |
| disjoint build/review ownership | four non-overlapping builders plus one artifact-only reviewer fixed; audit required before target |
| constraints and corruptions | registered; demonstrations required before target |
| simplifications bounded | pass for all-qubit two-round scope |
| leakage/full-law/scaling boundaries | explicit exclusions |
| `src/**` authority | not granted and not required |
| **code gate** | **CODE_PERMITTED for scripts/tests/docs only** |
| **d5 target gate** | **BLOCKED until tracer, corruptions, metric tests, dense/Aer d3, and useful d3 PEPS all pass** |
