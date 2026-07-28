# PEPS XZZX measurement/reset/Record bridge — preregistration v2

Status: **FROZEN PRE-REGISTRATION, 2026-07-27. Predictions are written before
the run; a miss is a finding, not a re-fit. The first commit adding this file
is the v2 freeze point.**

Supersedes the execution route, but not the observed results, of
`PEPS_XZZX_MEASUREMENT_RESET_RECORD_PREREG_2026-07-26.md`. V1 was killed
before formal target execution by the hidden Aer-MPS truncation documented in
`PEPS_XZZX_PRETARGET_IMPLEMENTATION_AUDIT_2026-07-27.md`. No v1 tracer, d3, or
d5 output is admissible. The v1 file and hash remain unchanged.

Literature prerequisite:
`PEPS_XZZX_MEASUREMENT_RESET_RECORD_LITERATURE_CLOSURE_2026-07-26.md`,
`closure_status: closed` for the bounded all-qubit two-round experiment.
Leakage, Kraus noise, d5 full-Record faithfulness, decoded LER, and scalable
exact PEPS remain outside that closure.

## -1. Question charter

- **Decision and consequence:** determine whether a finite-bond, explicit-
  ancilla Quimb PEPS preserves the probability, reset, conditioned-state, and
  absolute-fold semantics of two XZZX extraction rounds well enough to
  justify further two-dimensional trajectory work.
- **Plausible attack and independent anchor:** d2 has a complete 1024-path
  law; d3 has two independent exact formulations; d5 has only 25 data qubits
  at the fidelity checkpoint and admits a complete `2^25` exact
  data-projector reference after analytic ancilla elimination.
- **Reusable objects:** hash-bound d2/d3/d5 fixtures, an exact data-only
  stabilizer-projector instrument, a PEPS selective-reset adapter, full-law
  and complete-vector metric owners, and target-isolated provenance bundles.
- **Alternative formulations and invariants:** complete active-qubit dense
  evolution and data-projector evolution must agree at d2/d3; direct
  rank-one reset and its one-site RDM must agree; raw outcomes and the
  absolute detector/observable XOR fold must agree.
- **Kill condition:** stop if any structural zero is threshold-inferred, any
  positive probability is dropped, exact dense/projector d2/d3 equivalence
  fails, a corruption is inert, reset is repaired by a tolerance-authorized
  projector, candidate branches share a conversion cache, d3 misses its
  frozen usefulness gate, or d5 fidelity uses anything except both complete
  `2^25` vectors.

Difficulty, fashion, and prestige are not evidence of importance.

Primary route: **external carrier/baseline evidence**. No `src/**` change,
production promotion, leakage claim, or simulator claim is authorized.

## 0. Grounding ledger

| sub-axis | exact source / project object | bound statement |
|---|---|---|
| XZZX geometry | Bonilla Ataides et al., arXiv:2009.07851v3, Fig. 1, PDF p. 2; Darmawan et al., arXiv:2104.09539v2, Sec. II and Fig. 2(a), PDF p. 3 | XZZX check shell up to the stated spatial/local-H convention |
| consecutive defect | Bonilla Ataides et al., Fig. 5, PDF p. 6; Darmawan et al., Sec. II.B, PDF p. 3 | detector event from consecutive stabilizer signs; fixture anchors/closure remain project definitions |
| selective instrument | Czajkowski and Grilo, arXiv:2101.08313v2, Sec. 2.2 Eq. (1), PDF p. 5; Sec. 3.1 Eq. (9), PDF p. 7 | ordered Born probabilities and normalized selected poststates |
| reset component | Ghosh et al., arXiv:1306.0925v2, Sec. I and Fig. 1, PDF p. 2 | repeated ancilla reset to `|0>` |
| normalized overlap | Evenbly, arXiv:1801.05390v2, Sec. V Eq. (12), PDF p. 6 | complete pure-state fidelity |
| PEPS diagnostic boundary | Rudolph and Tindall, arXiv:2507.11424v2, Sec. II Eqs. (1)-(2), PDF p. 3 and terminal-sampling discussion, PDF pp. 4, 9 | retained weights and finite-boundary objects are not global state/Record fidelity |
| exact-complexity boundary | Schuch et al., *PRL* 98, 140506, VOR PDF pp. 2-3 | no scalable general exact-contraction inference |
| schedule/fold | hash-frozen neutral fixtures plus independent reconstruction | exact engineering input, not attributed to the papers |
| v2 reference identity | Clifford conjugation plus complete NumPy vector, independently checked against the full dense d2/d3 route | from-scratch exact ground truth, no Quimb or Qiskit import |

The source notes and fact IDs remain those bound in the closed literature
packet. The reference-route change introduces no new physical premise,
observable, or metric.

## 1. Frozen fixture and mechanism

### 1a. Unchanged fixture identities

| object | d2/r2 | d3/r2 | d5/r2 |
|---|---|---|---|
| active qubits | 7 | 17 | 49 |
| data / reset ancillas | 4 / 3 | 9 / 8 | 25 / 24 |
| raw measurements | 10 | 25 | 73 |
| reset events | 6 | 16 | 48 |
| detector / observable bits | 5 / 1 | 16 / 1 | 48 / 1 |
| Stim SHA-256 | `18492ad9bc8b286d1cf9f97f45546fac40552a10d83be9ef61fa892a941cb671` | `7067b1241251bd7558e7dc85b2f84bc13a45c1217a49f8fcfa2e51205879ecb0` | `be26b8708efe36a027bcf79074bc936de552b1a5d22b35b627d7d9cdbb27f008` |
| fixture SHA-256 | `dbf2a0979c9a4cd0a95f2afe393083d97a27ea1e90720596352a191010beb0f5` | `3b2bf7d81f7241e0a3b6abb14c76474c362e696cf374c55e20e3d121946bbf3c` | `659fda875a91f2a6e3c64f8f03487b5a431edecb9849dd897bf2e6f390583495` |

The d2 enumeration-spec hash remains
`02aef76a65383fbfec9a2f3e0b62a7dd0691a574ee739a4b6b33326ba13681ca`.
All raw strings, including exact structural-zero strings, remain in the
declared support.

V2 does not redefine the three base fixtures or their Stim sources. Their
byte identities are inherited from the independently reviewed v1 freeze;
the prereg-only reviewer must verify exact equality to v1 rather than infer
new fixture bytes from the abbreviated table above. Before target execution,
the committed emitter must materialize the canonical neutral JSON and Stim
text for all three distances. The artifact-only reviewer independently
recomputes every stated hash from those bytes and rejects any mismatch. The
reproducible source call remains
`stim.Circuit.generated("surface_code:rotated_memory_z", distance=d,
rounds=2).flattened()` followed by the v1-frozen dense-ID and local-H
transformation. This inheritance is not permission to change a fixture.

### 1b. Unchanged non-Pauli intervention

Apply

```text
RY(0.02) = [[cos(0.01), -sin(0.01)],
            [sin(0.01),  cos(0.01)]]
```

to every data qubit in ascending dense ID order after each complete syndrome
round. The second block is after the second reset shell and before terminal
data measurements. There are exactly two syndrome rounds. No stochastic
noise, leakage level, Kraus channel, decoder, or calibration is present.

### 1c. Exact selective reset

For computational outcome `b`,

```text
A_b = |0><b|
p_b = ||A_b psi||^2 / ||psi||^2
psi_b = A_b psi / ||A_b psi||.
```

For X readout the fixture's explicit H is applied first. Path mass is the
ordered product of conditional probabilities and is never inferred from the
renormalized poststate. A floating tolerance may reject a result but may not
create a structural zero or authorize another projector.

## 2. V2 branch-selector specs

The d3 and d5 primary branches are selected by the independent exact
data-projector reference, not by Aer. At measurement column `k`, with the
already selected literal prefix bits:

```text
D = ascii("ECS-XZZX-DATA-ONLY-BRANCH-V2") || 0x00
    || seed.to_bytes(8, "big")
    || k.to_bytes(4, "big")
    || bytes(prefix)
h = int.from_bytes(SHA256(D), "big")
(num, den) = p0.as_integer_ratio()
bit = 0 iff h*den < num*2^256, otherwise 1
```

Each prefix bit is one literal byte `0x00` or `0x01`, and `k` must equal the
prefix length. The integer comparison defines `u=h/2^256` without floating
division and compares it against the exact rational value of the binary64
`p0`.
There is one shot, no retry, no reseed, and no branch inspection before
selection. If a selected reference probability is below `1e-12`, the point is
`UNAVAILABLE`; another branch is not chosen.

Canonical pretty JSON (`sort_keys=True`, indent two, trailing newline) yields:

| distance | seed | run-spec schema | run-spec SHA-256 |
|---:|---:|---|---|
| 3 | `2026072603` | `error_coupling_simulator.external_xzzx_record_peps.run_spec.v2` | `7dfa0a8ef9620712e6ea190aeda651c681295f9841963ce77686640255cc22a9` |
| 5 | `2026072605` | same | `06151ea1244495475259d40bf6ca7ad16cbdaf5f8184ee61b344fb2e81b413a4` |

The exact d3 and d5 objects, before the canonical pretty serialization, are:

```json
{"base_fixture_sha256":"3b2bf7d81f7241e0a3b6abb14c76474c362e696cf374c55e20e3d121946bbf3c","distance":3,"intervention":{"after_rounds":[0,1],"angle_radians":0.02,"gate":"RY","placement":"after_each_complete_syndrome_round_before_the_next_base_operation","targets":"all_data_qubits_in_ascending_dense_id_order"},"reference_branch":{"sampler":"numpy_exact_data_projector","selector":{"algorithm":"sha256_prefix_born_v1","comparison":"bit_0_iff_h_times_den_lt_num_times_2_pow_256_for_p0_as_integer_ratio","domain_separator_ascii":"ECS-XZZX-DATA-ONLY-BRANCH-V2","domain_separator_terminated_by_zero_byte":true,"hash_integer_encoding":"sha256_full_digest_unsigned_big_endian","measurement_column_encoding":"uint32_big_endian_equal_to_prefix_length","prefix_encoding":"one_byte_per_bit_0x00_or_0x01","seed":2026072603,"seed_encoding":"uint64_big_endian"},"shots":1},"reference_state":{"checkpoint":"after_round_1_ry_before_terminal_data_measurements","method":"numpy_exact_data_projector","probability_floor":null,"truncation":null},"rounds":2,"schema":"error_coupling_simulator.external_xzzx_record_peps.run_spec.v2","stim_circuit_sha256":"7067b1241251bd7558e7dc85b2f84bc13a45c1217a49f8fcfa2e51205879ecb0"}
```

```json
{"base_fixture_sha256":"659fda875a91f2a6e3c64f8f03487b5a431edecb9849dd897bf2e6f390583495","distance":5,"intervention":{"after_rounds":[0,1],"angle_radians":0.02,"gate":"RY","placement":"after_each_complete_syndrome_round_before_the_next_base_operation","targets":"all_data_qubits_in_ascending_dense_id_order"},"reference_branch":{"sampler":"numpy_exact_data_projector","selector":{"algorithm":"sha256_prefix_born_v1","comparison":"bit_0_iff_h_times_den_lt_num_times_2_pow_256_for_p0_as_integer_ratio","domain_separator_ascii":"ECS-XZZX-DATA-ONLY-BRANCH-V2","domain_separator_terminated_by_zero_byte":true,"hash_integer_encoding":"sha256_full_digest_unsigned_big_endian","measurement_column_encoding":"uint32_big_endian_equal_to_prefix_length","prefix_encoding":"one_byte_per_bit_0x00_or_0x01","seed":2026072605,"seed_encoding":"uint64_big_endian"},"shots":1},"reference_state":{"checkpoint":"after_round_1_ry_before_terminal_data_measurements","method":"numpy_exact_data_projector","probability_floor":null,"truncation":null},"rounds":2,"schema":"error_coupling_simulator.external_xzzx_record_peps.run_spec.v2","stim_circuit_sha256":"be26b8708efe36a027bcf79074bc936de552b1a5d22b35b627d7d9cdbb27f008"}
```

Each canonical object contains the unchanged base-fixture and Stim hashes,
the unchanged intervention object, the selector algorithm, domain separator,
integer encodings, exact comparison, seed and one-shot count, and:

```json
{
  "reference_state": {
    "checkpoint": "after_round_1_ry_before_terminal_data_measurements",
    "method": "numpy_exact_data_projector",
    "probability_floor": null,
    "truncation": null
  }
}
```

The emitter's canonical-object test must independently recompute both hashes.

The d3 alternate rule is unchanged except that its parent is the v2 exact
primary artifact: copy the primary until the first `MR` column whose opposite
exact probability is at least `1e-8`, flip there, then choose the exact
larger-probability bit for every later `MR` and terminal column, with an exact
tie toward zero. The artifact binds the parent file hash, parent branch hash,
and flip column. No alternate means d5 is blocked.

## 3. Metric binding

The registered owner is
`scripts/external_baselines/compare_xzzx_record_peps.py`; the independent
formula and proxy-firewall tests are
`tests/test_external_xzzx_record_metrics.py`.

- **Complete-vector fidelity:**
  `F=|<ref|cand>|^2/(<ref|ref><cand|cand>)`.
- **Tracer raw-law and folded-Record TV:**
  `TV=0.5*sum_x |p(x)-q(x)|` on their separately declared complete supports.
- **Selected branch probability error:**
  `max_k |p_candidate,k-p_reference,k|`.
- **Selected branch log-mass error:**
  `|sum_k log p_candidate,k - sum_k log p_reference,k|`.
- **Post-reset one-site trace distance:**
  `0.5*||rho-|0><0|||_1`.

Complete vector means every amplitude in complex128 and the hash-bound axis
order. Retained weight, local truncation loss, finite-boundary overlap,
partial vector, sampled amplitude, RDM fidelity, and Aer-MPS output are
forbidden substitutes. Raw-trajectory TV is not folded-Record TV.
Reference Bernoulli rows require `abs(p0+p1-1)<=1e-12`; candidate rows require
`<=1e-10`. Every selected probability is logged before multiplication. If a
strictly positive product underflows binary64, the scalar product field is
marked underflow/unavailable while the finite sum of logs remains the mass
metric; underflow is never a structural zero.

## 4. Independent exact ground truth

### 4a. Full dense d2/d3 route

The existing NumPy route hand-builds gates, projectors, and resets on all
7/17 active qubits. It owns the d2 complete law and one independent d3
formulation. It imports neither Quimb nor Qiskit.

### 4b. Exact data-projector route

For each syndrome round, propagate every measured ancilla `Z_a` backward
through the neutral Clifford shell. The accepted algebraic form is exactly

```text
U_round^dagger Z_a U_round = + Z_a S_a,
```

with no non-Z operator on any input reset ancilla. All `S_a` must be
Hermitian, phase `+1`, data-only after removing `Z_a`, and pairwise commuting.
Both round tableaus must agree. The actual interleaved shell and an
independently grouped ancilla shell must have equal tableaus.

The formal NumPy worker derives `S_a` directly from the neutral operation
ledger and imports neither Stim, Quimb, nor Qiskit. Every CX touching `a` must
use one orientation throughout that round. Its base data Pauli is X when the
ancilla is control and Z when it is target; membership of the data site in
`hadamard_frame_data_qubits` swaps X and Z. Supports are sorted `(data_id,
Pauli)` pairs. Mixed orientations, duplicates, an unexpected two-qubit gate,
wrong MR grouping/order, unequal rounds, or an empty check fail closed.
Test-only Stim tableau conjugation independently verifies every parsed check,
sign, ancilla factor, commutator, and interleaved/grouped equivalence.

For selected syndrome bit `b`, apply to the complete data vector

```text
v_b = (psi + (-1)^b S_a psi) / 2
p_b = real(vdot(v_b, v_b))
psi_b = v_b / sqrt(p_b).
```

Compute both outcomes from their projected vectors; do not substitute
`(1 +/- <S>)/2`, whose subtraction can erase near-structural probabilities.
The positive real square root fixes normalization; no post-hoc phase
canonicalization is permitted. Then apply the frozen RY block. Terminal Z/X
measurements use the same formula with `S=Z_q` or `X_q`. No probability
floor, singular-value decomposition, tensor compression, or approximate
contraction occurs.

`data_order=fixture.frame.data_qubits` must be unique and strictly ascending.
The initial local factor is `|+>` exactly for a
`hadamard_frame_data_qubits` site and `|0>` otherwise; left-to-right Kronecker
order makes the first data axis most significant. The frozen d5 order is
`[0,2,3,5,6,7,9,11,13,15,18,20,22,24,26,27,29,31,33,35,38,40,42,44,46]`.
The d3 all-active vector is the reverse embedding with the data vector in the
all-ancilla-zero slice and exact zeros elsewhere.

Before any target output:

- d2 and d3 must agree with the full active-qubit dense route on every tested
  per-column `p0/p1` within `1e-12`;
- phase-aligned checkpoint vectors must have `1-F <= 1e-12`;
- selected-branch log-mass disagreement must be `<=1e-9`;
- the pretarget fixed control set is d2
  `0000000000`, `0001100100`, `1001000000`, `1011011111`, and d3
  `0000000000000000011101101`,
  `1000000010000000000000000`,
  `0010010000100100110110101`,
  `0010000000100000101101101`,
  `1000000110000001011011000`;
- the formal d3 v2 primary and its derived alternate must also pass the same
  three dense/projector gates before any PEPS verdict is accepted;
- the d3 data vector is embedded with each reset ancilla at exact zero to
  produce the frozen all-active axis order;
- the d5 output is exactly `2^25` amplitudes in ascending
  `fixture.frame.data_qubits` order.

This route is independent of candidate tensors, gauges, RDMs, probabilities,
and contraction plans.

### 4c. Quimb PEPS candidate

- `CircuitPEPSSimpleUpdate` on the frozen interaction graph;
- complex128, simple-update cutoff exactly `0.0`;
- d2/d3 verified-complete graph RDM;
- d5 RDM graph radius `0,1,2,3`;
- d2 tracer `D=8`;
- d3 `D=[1,2,4,8]`;
- d5 exactly `D=[1,2,4]`; no optional/post-hoc D is authorized;
- direct normalized `A_b` gate on a copied branch;
- exact physical-one tensor-slice zero immediately after every reset and at
  the checkpoint; a nonzero entry rejects the point;
- RDM Hermiticity, trace, PSD, probability normalization, and reset trace
  distance checked separately;
- no reconstruction through `psi0` and no corrective `P0`;
- copied branches have isolated backend-conversion caches;
- the rank-one one-site gate preserves every existing simple-update gauge
  key, shape, dtype, and byte value; there is no reset-time gauge refresh.

The preserved gauges are declared heuristic environments for later
simple-update gates, not postmeasurement Schmidt spectra. This deterministic
choice avoids both the `psi0` reconstruction smudge and division by exact-zero
gauges. Its approximation is included in the measured d3/d5 state and mass
errors. Before target, Bell and d2/d3 tests must show that the absorbed
physical state matches the exact rank-one poststate with
`1-F<=1e-12` and maximum phase-aligned amplitude error `<=1e-12`, the
physical-one slice is an exact zero, gauge bytes are unchanged by the reset
itself, and subsequent complete-graph/high-D evolution remains finite and
satisfies the exact-reference gates above. Every candidate reset RDM must have
trace distance to `|0><0|` at most `1e-10` for d2/d3 and `1e-8` for d5.
The realized detector/observable fold must match as exact binary lists.
Failure makes the PEPS route unavailable; it does not authorize a later gauge
policy.

## 5. Frozen predictions and decision bands

These are unchanged from v1.

| object | frozen gate or band | class |
|---|---:|---|
| dense tracer mass | `abs(sum p-1)<=1e-12`; full structural-zero support retained | (a) |
| Quimb tracer mass at `D=8`, complete graph | residual `<=1e-10` | (a) |
| tracer raw-law TV | `<=1e-8` | (b) |
| tracer folded-Record TV | `<=1e-8` | (b) |
| tracer RY nondegeneracy | `TV_Record(RY=0.02,RY=0)>1e-6` | (c) |
| full-dense vs data-projector d3 fidelity | `1-F<=1e-12` | (a) |
| full-dense vs data-projector d3 per-step probability error | `<=1e-12` | (a) |
| full-dense vs data-projector d3 log-mass error | `<=1e-9` | (a) |
| candidate reset trace distance | d2/d3 `<=1e-10`; d5 `<=1e-8`, plus exact physical-one slice zero | (a) |
| d3 PEPS primary and alternate at `D=8` | `F>=0.99`, max probability error `<=5e-3`, log-mass error `<=1e-1`, reset/fold pass | (c), d5 gate |
| d3 marginal / low | `0.95<=F<0.99` / `F<0.95` | (c), blocks d5 |
| d3 bond sweep | `F(D)` nondecreasing within `1e-8` | (b), report a miss |
| d3 bond-knob movement | `abs(F(D=8)-F(D=1))>1e-4` | (c) |
| d5 primary `D=4`, radius 3 useful | complete-vector `F>=0.99`, max probability error `<=1e-2`, log-mass error `<=5e-1`, reset/fold pass | (c) |
| d5 state-useful/mass-unresolved | exact `F>=0.99` but a mass gate fails | (c), not trajectory pass |
| d5 marginal / low | exact `0.95<=F<0.99` / `F<0.95` | (c) |
| either d5 complete vector absent | `UNAVAILABLE` | fail closed |

Increasing D/radius is a prediction, not an invariant. Nonmonotonic points
remain in the report.

## 6. Constraint and corruption ledger

Every row must trip on its deliberately broken input before target execution.

| invariant | deliberate corruption | required trip |
|---|---|---|
| fixture/spec identity | change one canonical byte, seed, intervention, or absolute row | hash/schema rejection |
| d7 isolation | route d2/d3/d5 through an edit of the d7 emitter | d7 byte/hash regression |
| exact reference check map | change one propagated Pauli/sign or accept a noncommuting pair | tableau/projector equivalence failure |
| exact selector | change the SHA domain/field encoding, prefix, or exact integer comparison | synthetic boundary/known-hash test failure |
| CX direction/local-H frame | swap first non-symmetric CX or delete first local-H pair | d2 law or d3 state/probability changes by `>1e-8` |
| reset erasure | replace first `MR` by `M` | law changes and post-measurement physical-one state fails |
| reset map | replace `|0><1|` by `|1><1|` | exact slice/RDM reset failure |
| no tolerance repair | contaminate physical-one slice below the RDM tolerance | exact-slice check rejects before extraction |
| no probability floor | inject a finite positive probability near `1e-28` | branch is propagated or point becomes unavailable, never zeroed |
| probability validity | inject negative/greater-than-one/non-PSD RDM | fail closed, no clamp |
| branch cache isolation | reuse transient gate IDs across CUDA sibling copies | requested and applied gates remain byte-equal |
| reset gauge policy | mutate, refresh, smudge, or reinterpret a gauge during rank-one reset | byte-identity/policy test rejects |
| two RY blocks | set sign to `-0.02`, zero both, or remove only the second | registered state/law controls move by `>1e-8` |
| X readout | omit first readout H | probability/state corruption moves by `>1e-8` |
| Born normalization | normalize a fixed synthetic selected state by the other probability | norm/mass test fails by `>1e-8` |
| cumulative mass | omit first factor from `[0.8,0.3]` | log-mass ledger differs by `>1e-8` |
| absolute fold | replace a ragged terminal row by consecutive XOR | synthetic and tracer fold disagree |
| axis order | reverse the fixed asymmetric vector axes | fidelity/order test fails |
| complete d5 fidelity | return any proxy/partial vector | validator rejects or returns `UNAVAILABLE` |
| bits-only firewall | add reference probability/tensor/gauge fields to candidate branch | exact field-set validator rejects |
| independent reference | import Quimb/Qiskit or accept candidate probabilities/tensors/gauges in the exact-data worker | static AST, isolated-process, and exact input-schema tests reject |
| global phase | multiply one complete vector by a unit phase | fidelity changes by at most `1e-12` |
| output immutability | alias outputs, precreate a target, or race publication | fail without modifying existing bytes |

## 7. Negative controls and disconfirmation surface

- `RY=0` must fail the non-Pauli nondegeneracy threshold.
- D must move d3 fidelity by the registered amount; otherwise the advertised
  approximation knob is not evidenced.
- A high state fidelity with wrong conditional/log mass is reported
  `state_useful_mass_unresolved`, never promoted.
- A passing selected d5 branch does not imply a d5 law, worst-branch result,
  leakage result, or scalable PEPS algorithm.
- The strongest competitor is that finite-D simple update preserves the
  selected normalized state while finite-radius RDMs distort branch mass.
  The separate fidelity and mass verdicts distinguish it.

## 8. Bounded simplifications

| simplification | exact bound and excluded inference |
|---|---|
| two-level all-qubit model | exact for this fixture; no leakage/Kraus/hardware claim |
| exactly two rounds | exact schedule; no long-time/round-scaling claim |
| fixed coherent `RY(0.02)` | exact intervention; no calibration/generic-noise claim |
| d2 full law only | exact enumerated scope; no d3/d5 full-law claim |
| selected d3/d5 branches | exact branch identity; no average/worst/rare-event claim |
| finite-radius d5 RDM | labelled approximate branch-mass diagnostic; not state fidelity or Record TV |
| exact d5 complete vector | exact if all amplitudes materialize inside resources; otherwise unavailable |
| finite D | reported candidate approximation; no theorem that any tested D is sufficient |
| gauges preserved across one-site reset | deterministic simple-update environment heuristic whose full error remains in the independent state/mass comparison; no Schmidt-spectrum claim |

## 9. Execution, resources, and stopping

Each point is a fresh isolated subprocess with committed, byte-clean inputs.
Every artifact binds repository HEAD and source blobs, external clone
commit/tree/cleanliness, environment-lock and installed-source identity,
fixture/spec/parent-branch bytes, runtime versions, wall time, peak host RSS,
peak device allocation, and output hashes. Outputs are exclusive, immutable,
and atomically published.

Per point:

- wall time `1800 s`;
- peak host RSS `64 GiB`;
- peak device allocation `28 GiB`;
- no `PYTHONPATH`;
- points in ascending D and d5 radii in ascending order;
- a larger unavailable point does not erase a smaller completed point.

Order:

1. commit this preregistration after independent prereg-only review;
2. implement and run all unit/corruption controls without target outputs;
3. commit the implementation;
4. give only committed inputs to a new un-led artifact-only reviewer;
5. run d2 dense/Quimb full-law tracer;
6. run exact full-dense/data-projector d3 agreement;
7. generate the one-shot v2 d3 primary, derive its alternate, and run
   `D=[1,2,4,8]`;
8. only if the complete d2 tracer law/nondegeneracy gates, every registered
   corruption trip, every exact-reference equivalence gate, d3 bond-knob
   nondegeneracy, and both d3 `D=8` PEPS points all pass conjunctively,
   generate the one-shot exact d5 primary and run exactly `D=[1,2,4]`,
   radii `0,1,2,3`;
9. do not inspect or tune around a running d5 point;
10. classify absent complete vectors as `UNAVAILABLE`.

## 10. Build organization and preregistration gate

| role | disjoint ownership |
|---|---|
| fixture/full-dense owner | neutral fixtures, immutable input artifacts, full d2/d3 dense controls |
| exact-data owner | Clifford check extraction, exact vector/projectors, selector, d5 reference |
| Quimb owner | PEPS state/RDM/reset/gauge/cache path and candidate artifacts |
| metric/runner owner | schema-only comparison, process/resource supervisor, terminal verdict |
| artifact-only reviewer | read-only review of committed inputs and immutable outputs; no implementation or target execution |

Gate:

| requirement | status |
|---|---|
| premises closed | pass for bounded all-qubit two-round scope |
| standard metrics bound | pass |
| predictions frozen without relaxation | pass |
| independent ground truth | pass in design; implementation equivalence tests required |
| constraint falsifiers registered | pass in design; every trip required before target |
| simplifications bounded | pass |
| controls/nondegeneracy registered | pass |
| formal result contamination | none; plumbing smoke and non-primary greedy reset-policy control excluded |
| prereg-only independent review | pass, 2026-07-27 |
| **preregistration gate** | **PASS; byte-freeze at the first commit adding this file** |

This document does not authorize experiment code or execution. The
theory-first orchestrator may permit scripts/tests/docs only after the
preregistration gate passes. A later miss is a finding and never permission
to change a band, branch rule, D/radius list, or claim boundary.
