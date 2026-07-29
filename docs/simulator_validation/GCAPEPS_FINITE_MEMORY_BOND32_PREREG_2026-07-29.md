# GCAPEPS finite-memory / non-Markovian-witness bond-32 benchmark — preregistration

Status: **FROZEN FOR INDEPENDENT REREVIEW; CODE REMAINS BLOCKED UNTIL A
PASSING REREVIEW AND THEORY-ONLY COMMIT, 2026-07-29.**

Grounding:
`GCAPEPS_FINITE_MEMORY_BOND32_LITERATURE_CLOSURE_2026-07-29.md`.

This is a bounded pure-state carrier experiment.  It is not a complete QEC
round, detector/observable Record, leakage model, or generic PEPS
faithfulness/scaling experiment.

The scientific object is a project-defined finite-dimensional
persistent-memory unitary dilation.  It is not Campbell et al.'s advancing
collision stream or their fixed-memory SWAP equivalence.  Source adjacency and
project inference are kept separate throughout this preregistration.

## 1. Repository and implementation boundary

The preregistration was written against:

| object | identity before implementation |
|---|---|
| parent repository commit | `736683c2a975e6eaad445024780fbe0c863fc6c9` |
| parent repository tree | `b8f1fd5f44cf4333ff643e9ed628b3c79816f113` |
| Quimb GCAPEPS fork commit | `e6cbe016f336843925e01a559db26f209fa9d37b` |
| Quimb GCAPEPS fork tree | `854ff4d5ef692497f017a57250cf8f440e47110f` |
| fork main environment lock | `external/forks/quimb-gcapeps/pixi.lock`, SHA-256 `854da99b417c69dbdca4118c2545656470ad4e0f276a606b1b8c3082f795db35` |

The new fork implementation will be opt-in.  Existing `exact_tree` and
`native_simple_update` meanings must not silently change.  The new strategy
name is frozen as:

```text
exact_tree_then_native_compress
```

It performs one exact tree-PEPO lowering, validates that pre-compression
construction, then compresses the affected routed edges with Quimb's native
two-site simple-update SVD by applying an identity operator in deterministic
route order.  That operator calls the controlled low-level PEPS split and must
not enter the circuit's physical `_gates` history.  The performance mode runs
the capped algorithm without an uncapped shadow.  The separate evidence mode
runs sequential no-shadow and instrumented-replay branches from byte-identical
fixtures and requires their canonical final-carrier hashes to match.  Only the latter
can claim a positive discarded tail.

The native compression call is made only on the raw gauged state
`candidate._psi.gate_simple_`; it never uses the gauge-absorbed `candidate.psi`
copy or the physical `_apply_gate`/`apply_gates` paths.  A validated copy of
the gate options removes `contract` and `propagate_tags` before the low-level
call so the native `reduce-split` path is not silently overridden.

Algorithm/performance mode disables the existing \(n\le10\) exact-tree dense
construction audit as well as uncapped shadows.  Evidence mode explicitly owns
both checks.  Gauge fusion must create every routing-label identity factor in
the existing gauge dtype.  Stored gauges and singular spectra must remain
finite, real, nonnegative, C-contiguous `float64`; a promoted `complex128`
gauge, even with zero imaginary part, fails rather than being silently cast.

## 2. Questions and registered hypotheses

### Q1 — reduced-system memory witnesses

Two exact-dense objects are registered and are never conflated.

#### Q1a — fixed carrier schedule

For the one frozen `CARRIER` mask shared by both candidate lanes and inputs,

\[
D_r^{\rm carrier}=\frac12\|\rho_{S,1}(r)-\rho_{S,2}(r)\|_1,
\qquad
W_{\rm BLP}^{\rm carrier}=\sum_{r=1}^{R}\max(0,D_r^{\rm carrier}-D_{r-1}^{\rm carrier}),
\qquad
\delta_{\max}^{\rm carrier}=\max_{1\le r\le R}(D_r^{\rm carrier}-D_{r-1}^{\rm carrier}).
\]

The registered pair differs by one central-system \(X\), uses the same memory
state and maps, and is orthogonal on the system at initialization.  Therefore
the initial value is frozen as \(D_0^{\rm carrier}=1\), subject to the numerical
trace-distance gate below.

#### Q1b — registered finite mask ensemble

For each \(p_{\rm event}\), a dense-only ensemble contains 32 equally weighted
mask paths \(m=0,\ldots,31\):

\[
\bar\rho_{S,a}(r)=\frac1{32}\sum_{m=0}^{31}\rho_{S,a,m}(r),
\qquad
\bar D_r=\frac12\|\bar\rho_{S,1}(r)-\bar\rho_{S,2}(r)\|_1,
\qquad
\bar W=\sum_{r=1}^{R}\max(0,\bar D_r-\bar D_{r-1}),
\qquad
\bar\delta_{\max}=\max_{1\le r\le R}(\bar D_r-\bar D_{r-1}).
\]

The average density matrices are formed before trace distance; averaging 32
pathwise distances is a registered corruption.  Identical masks at an endpoint
remain 32 equally weighted paths and are not deduplicated or reweighted.

For either named object, a witness requires its named maximum increment to be
greater than \(10^{-10}\).  The summed positive increments \(W\) are always
reported but never substitute for this gate.  The exact verdict names are
`BLP_WITNESSED_FIXED_MASK` and `BLP_WITNESSED_FINITE_32_MASK_ENSEMBLE`, with
the corresponding `NO_WITNESS_*_FOR_REGISTERED_PAIR` names in Section 14.
Neither no-witness result is a Markovian verdict, and neither object is the
input-pair-optimized BLP measure.  Candidates report only per-checkpoint
fixed-mask trace-distance errors against dense; candidate BLP-measure errors
and candidate-to-ensemble comparisons are forbidden.

### Q2 — round-dependent physical entanglement

The project hypothesis is defined only at the held-out stress cell
\((w,\mathrm{axis},p)=(7,3,p_\star)\), with the held-out `CARRIER` mask, for
exact dense trajectory 1 (the all-zero system and memory input).  Its terminal
system–memory entropy after the selected longest prefix is greater than after
the first round:

\[
H_E:\quad S_{\rm vN,1}^{\rm exact}(R_\star)>
S_{\rm vN,1}^{\rm exact}(1)+10^{-10}.
\]

This is explicitly not a monotonic-step hypothesis.  The full trajectory,
negative increments, revivals, maximum, terminal value, Rényi-2 entropy, and
Schmidt spectrum are all retained.  Other held-out cells are descriptive and
do not receive an \(H_E\) verdict.  A failure of \(H_E\) is a result, not a
reason to change the fixture.

### Q3 — capped carrier faithfulness

At the registered bond-32 stress cell define

\[
\Delta F=
\min_{a\in\{1,2\}}F_{\rm GC}^{(a)}(R_\star)
 - \min_{a\in\{1,2\}}F_{\rm plain}^{(a)}(R_\star).
\]

Every fidelity is the normalized squared overlap with the independent dense
state for the same input trajectory.  The directional project hypothesis
\(H_F\) and its numerical decision band are frozen as:

```text
supported        Delta_F >  1e-10
tie/inconclusive abs(Delta_F) <= 1e-10
falsified        Delta_F < -1e-10
```

The raw \(\Delta F\) is always reported.  The comparison does not assume equal
internal work: ordinary PEPS carries the full physical state, while GCAPEPS
carries a Clifford frame plus a residual PEPS.

### Q4 — bounded current-implementation timing

No speed direction is assumed.  Ratios are reported descriptively for every
completed held-out cell.  The primary \(Q4\) classification is only the stress
cell and uses the three measured primary-trajectory performance workers per
lane.  Its candidate-algorithm end-to-end wall time ratio is

\[
R_{T,\rm wall}=\operatorname{median}(T_{\rm GC})/
    \operatorname{median}(T_{\rm plain}),
\]

the project-only descriptive bands are:

```text
GC faster       R_T_wall < 0.80
same order      0.80 <= R_T_wall <= 1.25
GC overhead     R_T_wall > 1.25
```

The raw samples, median, MAD, CPU-time ratio, evidence-worker ratio, and
supervisor-launch ratio remain primary reported values.  These bands are not
field or asymptotic thresholds.

## 3. Geometry, state, and round semantics

For width \(w\), use a two-row ladder with \(2w\) qubits:

```text
S0 -- S1 -- ... -- S(w-1)
 |     |             |
M0 -- M1 -- ... -- M(w-1)
```

Site ids are `S_i=i` and `M_i=w+i`.  Horizontal edges and all vertical rungs
are declared at initialization.  The memory row is never discarded, reset, or
recreated inside a candidate trajectory.

The primary trajectory begins in

\[
|\psi_{1,0}\rangle
=|0\rangle_S^{\otimes w}|0\rangle_M^{\otimes w}.
\]

The second BLP trajectory changes only the central system qubit,

\[
|\psi_{2,0}\rangle
=X_{S_{\lfloor w/2\rfloor}}
 |0\rangle_S^{\otimes w}|0\rangle_M^{\otimes w}.
\]


The representation of input 2 is frozen.  Dense and plain-PEPS lanes initialize
the central physical system tensor directly in \(|1\rangle\); this preparation
is recorded but is not a physical-round gate.  Both GC residual PEPS inputs
remain the all-zero product.  GC input 1 starts with identity frame, while GC
input 2 starts with
`X(S_floor(w/2))` in an input-specific preparation transcript and live Stim
frame.  The shared chronological evolution ledger begins only after this
preparation and remains byte-identical across inputs and lanes.

Checkpoint zero requires the literal GC frame lift to equal the corresponding
dense/plain physical input and requires the input-specific frame/preparation
hashes to match the fixture.  Candidate initialization timing includes direct
plain tensor preparation or GC frame construction, respectively.  No
implementation may move the input-2 X from frame to residual, replay it as a
round gate, or omit it from SDIM/Stim prefix corroboration.
They are evolved with byte-identical round, gate, angle, and event-mask
ledgers.

Physical rounds are one-based, \(r=1,\ldots,R\), while site indices are
zero-based.  The same one-based \(r\) is encoded as `round_u64be` in the event
mask and used in every parity expression below; round index zero is reserved
for the initial checkpoint only.  One round has this frozen chronological
order:

1. apply \(H\) to every \(S_i\) with \((i+r)\bmod2=0\);
2. apply \(S\) to every \(S_i\) with \((i+r)\bmod2=1\);
3. apply horizontal `CX(S_i,S_{i+1})` first on
   \(i\bmod2=r\bmod2\), then on the complementary parity;
4. apply horizontal `CX(M_{i+1},M_i)` in the same two parity layers;
5. for every ascending \(i\) whose event bit is one, apply the complete
   axis-family-\(c\) collision in the axis order \(X,Y,Z\), skipping inactive
   axes.

Within every single-site or disjoint two-site parity layer, sites/bonds are
visited by ascending `i`; no implementation-dependent iteration order is legal.
All Clifford gates are physical gates in the plain lane and frame updates in
the GCAPEPS lane.  Every collision Pauli rotation is physical in both lanes;
GCAPEPS first pulls it through the live accumulated frame and applies the
result to the residual.

There is no unconditional cross-row gate.  Thus `p_event=0` contains no
system–memory interaction and is the registered negative control.  The two
oppositely directed vertical CNOT layers in the earlier draft were not inverse
operations and are expressly forbidden as a hidden background coupling.

`rounds` means repeated unitary collision layers on one persistent joint
state.  It does not mean syndrome extraction because measurement, reset,
branch mass, detector folding, and Record semantics are absent.

## 4. Axis families and stable project-defined event masks

The project-defined active-axis families are:

```text
axis family 1: Z
axis family 2: X,Y
axis family 3: X,Y,Z
```

They are categorical Hamiltonian families, not a monotonic complexity theorem.

Every active axis uses the same selected magnitude \(\gamma\) and the physical
rotation angle \(\theta=-\gamma\).  This sign is frozen from the positive-sign
partial-SWAP primitive printed in McCloskey--Paternostro Eq. (1) and the
cross-source algebra audit.  The Campbell post-Eq. (4) negative-sign sentence
is internally inconsistent with the preceding equations in that paper and is
not an implementation source.  Full-swap and Clifford-special angles are excluded.

Event bits are generated without a library RNG.  The **mask namespace** is
ASCII `CARRIER` or `BLPENSEMBLE`; it is distinct from the run-partition labels
`CALIBRATION` and `HELDOUT`.  Every integer is an unsigned 64-bit big-endian
value.  The exact payload is:

```text
payload =
    b"gcapeps-finite-memory-mask-v1\x00"
    || namespace_ascii || b"\x00"
    || seed_u64be || mask_index_u64be
    || width_u64be || round_u64be || site_u64be
h64 = uint64_big_endian(SHA256(payload)[0:8])
```

The requested probabilities are exact quarters `p_event=q/4`,
`q in {0,1,2,3,4}`.  The event rule is structural false for `q=0`, structural
true for `q=4`, and otherwise `h64 < q * 2**62`.  The requested round horizon
is absent from the payload, so every schedule is prefix-stable.  `p_event` is
absent deliberately, making the probability sweep nested.

The `CARRIER` mask uses `mask_index=0` and is byte-identical across both inputs
and both candidate lanes.  `BLPENSEMBLE` uses indices `0..31` with weight
exactly `1/32`; it is dense-only.  Every payload, digest, full mask,
eligible-collision count, realized event count/fraction, active-axis rotation
count, distinct-mask count, and multiplicity is persisted.  The finite
ensemble is the registered object; no infinite-ensemble or calibrated-device
probability claim is made.

The `p_event=0` probability-slice cell is an executable exact-dense negative
control, separately for the fixed `CARRIER` path and the 32-path
`BLPENSEMBLE`.  Every event bit and active-axis rotation count must be exactly
zero.  For both registered inputs and every physical-round prefix, the exact
system--memory entropies must satisfy

\[
S_1(r)\le10^{-12},\qquad S_2(r)\le10^{-12},
\]

and both the fixed-path and ensemble trace distances must satisfy
\(|D_r-1|\le10^{-12}\), hence no named maximum increment may cross
\(10^{-10}\).  Any failure is a negative-control failure, not a
non-Markovianity result.  Candidate outputs at this cell retain the ordinary
faithfulness and per-checkpoint trace-distance-error diagnostics only; they
never own a BLP verdict.

## 5. Numerical policies and the two candidates

Common policy:

```text
dtype = complex128
CUDA_VISIBLE_DEVICES = empty
PYTHONNOUSERSITE = 1
PYTHONDONTWRITEBYTECODE = 1
PYTHONHASHSEED = 0
TZ = UTC
OMP_NUM_THREADS = 1
OPENBLAS_NUM_THREADS = 1
MKL_NUM_THREADS = 1
NUMEXPR_NUM_THREADS = 1
BLIS_NUM_THREADS = 1
max_bond = 32
cutoff = 0
cutoff_mode = rel
method = svd
renorm = false
absorb = None
power = 1.0
gauge_smudge = 1e-12
equilibrate_every = None
contraction_optimize = greedy
PYTHONPATH = absent
```
The supervisor replaces, rather than merely supplements, these named child
environment values.  The physical CPU is
`min(os.sched_getaffinity(supervisor_pid))`; every child is pinned to that CPU
and records its id, model, allowed/final affinity, kernel/platform, CPU governor,
Python executable/version/hash, Quimb/NumPy versions, and NumPy BLAS/LAPACK
configuration.  Pinning uses exactly the transient-unit property
`CPUAffinity=<selected_cpu_decimal>`; `AllowedCPUs`, inherited multi-CPU
affinity, and a second CPU-placement mechanism are forbidden.  Preflight and
every worker require `os.sched_getaffinity(0)=={selected_cpu}` and re-read the
effective `CPUAffinity`.  Missing affinity or cgroup-v2 enforcement fails closed.

The only accepted high-level split-option keys are `max_bond`, `cutoff`,
`cutoff_mode`, `method`, `renorm`, `absorb`, `smudge`, and `power`.  Inherited
`contract` and `propagate_tags` are stripped; every other unknown key is
rejected.  Each split calls the pinned low-level `gate_simple_` reduce-split
path with a fresh `info={}`, explicit `contract="reduce-split"`,
`max_bond=32`, `cutoff=0`, `cutoff_mode="rel"`, `method="svd"`,
`renorm=False`, `absorb=None`, `power=1.0`, and `smudge=1e-12`.  The `info`
mapping is neither reused nor persisted between splits.  `gauge_smudge` is the
protocol field name; both it and the observed low-level `smudge` must equal
`1e-12`.


The shared nonzero smudge is the explicit Quimb conditioning policy, not a
probability floor.  A lane-specific smudge or hidden default is rejected.
Before every split, gauges must satisfy the frozen finite, real, nonnegative,
C-contiguous `float64` policy.  Enumerate only gauges the selected two-site
`tn_where` would consume (its inner bond plus outer bonds), in canonical
undirected-edge order.  A key must map to exactly one declared graph edge.
For each enumerated gauge containing an exact-zero component, call
`candidate._psi.gauge_simple_insert({index: gauge}, remove=False, smudge=0.0,
power=1.0)` on the full candidate and then delete that key from the live gauge
store.  This is symmetric half-absorption on an inner bond and has no inverse;
the subsequent split may emit a fresh live gauge.  Unrelated live gauges are
not scanned.  Every enumerated gauge left in the store is strictly positive;
a positive near-zero component does not trigger materialization.

The payload records configured smudge and `smudge_actually_used`.  The latter
is true iff, after zero preprocessing, at least one eligible **outer** gauge is
still present; the selected inner gauge does not use smudge in this Quimb path.
Configuration alone, an inner gauge alone, or an unrelated gauge cannot set it.

### Plain Quimb PEPS

`CircuitPEPSSimpleUpdate` applies the complete physical gate ledger directly
on the declared ladder graph.  Every two-site gate uses Quimb native
simple-update at `max_bond=32`.  Single-site gates are absorbed locally and
cannot by themselves establish a truncation event.

The performance worker uses this native capped path without an uncapped
shadow.  The evidence worker first runs a complete no-shadow trajectory and
releases it, then runs the separately instrumented complete trajectory from a
byte-identical initial fixture; their canonical final-carrier hashes must match.
Before each instrumented two-site gate, its uncapped shadow starts from the
immediate state after all earlier capped updates.  The plain worker imports no
GCAPEPS module.

### Tree-routed GCAPEPS

A Stim Clifford frame consumes the Clifford shell.  For each physical Pauli
rotation, `GCAPEPSState` computes the signed pulled-back Pauli word.  The
residual carrier then:

1. builds and validates the exact two-term tree-routed PEPO update;
2. records its representation-only construction ledger;
3. takes the deterministic routed-edge order from that ledger;
4. performs Quimb-native identity-operator simple-update compression on those
   edges at bond 32 through the low-level PEPS split without appending a
   physical circuit gate; and
5. commits the candidate only after all construction and compression
   validators pass.

The exact construction and compression ledgers are separate dataclasses.
Equation-(17)-style PEPO and refactor factors are never inferred from the
compression rows.  This experiment uses \(Q=I\), so every refactor factor is
one.

Each exact update starts from the currently represented, possibly approximate,
residual.  Its epoch-local construction row binds at least:

```text
input_bond, pepo_factor=2, refactor_factor=1, exact_precompression_bond
```

After successful compression, `construction_epoch` increments and the next
epoch's PEPO/refactor product maps reset to one on every edge.  Failed work
changes neither the epoch nor either map.  A lifetime product can be rebuilt
offline only as `counterfactual_diagnostic`; it is not an actual
post-compression bond bound, cannot drive a resource guard, and never shares a
field with `kept_bond` or discarded-weight data.

## 6. What proves positive truncation

An evidence worker first executes the complete no-shadow trajectory from the
registered initial fixture, computes its frame-aware canonical final-carrier
hash, freezes its base scalar/ledger/transcript/hash values in memory, and
releases that complete branch without constructing core bytes.  It then
executes a complete instrumented trajectory from a byte-identical copy of the
same registered initial fixture.  Within only that second branch, each candidate
two-site compression has an independently owned uncapped shadow created from
the immediate pre-split state after all earlier capped splits.  The two complete
branches must have identical frame-aware canonical final-carrier hashes; their
in-memory payload bytes need not be compared.  A row is a positive cap event
only when all conditions hold:

```text
full_bond_dimension > 32
kept_bond_dimension == 32
discarded_squared_weight > 1e-12
cause == "max_bond"
configured_max_bond == 32
```

Because `cutoff=0`, the generic native-ledger cause `both` is unreachable and
cannot pass this experiment even if a broader schema recognizes it.  Final
bond 32 alone is insufficient.  The
uncapped shadow must not mutate the actual candidate, caches, gauges, timing
spans, physical operation ledger, or construction ledger.

The stress cell is eligible for the two-trajectory minimum-fidelity hypothesis
only if all four evidence lanes — plain/GC crossed with trajectories 1/2 —
each contain at least one positive cap event under the same rule.  Events need
not occur at the same operation.  Local discarded squared weight is a causal
split diagnostic, not a complete-state error bound.  Other cells retain
descriptive metrics even when this shared-positive condition fails.

## 7. Independent dense reference and faithfulness metrics

A NumPy/stdlib-only reference process imports no Quimb, Stim, SDIM, GCAPEPS,
or ECS module.  It hand-constructs each one- and two-qubit matrix from the
frozen physical gate ledger and applies it directly to `complex128` vectors.
It executes both inputs for the fixed `CARRIER` mask in every registered cell.
Only held-out probability-slice cells additionally execute all 32 equal-weight
`BLPENSEMBLE` masks; calibration runs no ensemble.  Dense complete states,
reduced states, entropy, and the applicable BLP quantities are produced after every round.

Process ownership is deliberately split.  The dense-reference process emits
only independently generated reference artifacts.  Each plain/GC evidence
worker emits raw candidate vectors and their pre-metric validation fields,
candidate-only local guards, positive-tail/full-and-kept-spectrum rows,
algorithm bonds/resources, signed-pullback rows, and the canonical
final-carrier hash.  Every candidate vector has
`source_branch="instrumented_replay"`; a no-shadow or performance branch may
not be relabelled as its source.  A one-input evidence worker cannot form a
pair trace distance.  Each performance worker executes only the candidate algorithm and
core serialization surface.

Candidate inputs use a required discriminant `run_partition`:

- `CALIBRATION` forbids amendment/held-out identities and instead requires the
  theory-only commit/tree, closure/preregistration hashes, calibration
  gamma/round/seed/stage/attempt identities, fixture hash, implementation
  commits/trees, environment identities, and applicable inventory hash;
- `HELDOUT` requires the clean amendment commit/tree, exact amendment-file hash,
  exact amendment-bound cell/list/fixture identity, implementation
  commits/trees, environment identities, and applicable inventory hash.
  Performance workers are legal only in this partition.

Both variants reject every dense-reference/comparator path, file hash, vector,
reduced state, cross-artifact metric, verdict, or artifact locator.  Candidate
workers receive their sealed input in a fresh private process/mount namespace
while using the exact read-only `WorkingDirectory=<repo_abs>`; they emit only
the two registered stdout frames below.  Their fresh transient systemd unit
sets `InaccessiblePaths=` to the exact calibration or
held-out run-output root, and the supervisor verifies and records the effective
property before accepting the child.  Thus an already published Stage-A dense
artifact is mechanically unreadable during later calibration candidate work.
Failure to establish the inaccessible path fails closed.  A corruption process
must attempt the known absolute dense path and receive an access denial.
Candidate workers neither branch on nor validate against evaluator output.
Cross-artifact identity and value comparison occur only in the terminal
comparator.

The terminal NumPy/stdlib-only comparator
`scripts/external_baselines/compare_gcapeps_finite_memory_bond32.py` imports no
Quimb, Stim, SDIM, GCAPEPS, or ECS module; it reads the neutral fixture plus
separately published reference, candidate, and SDIM artifacts, checks their
frozen identities, and
alone computes `F_raw`, the roundoff correction, `F`, `D_pure`, trace distance,
`d_rel`, `d_norm`, raw and normalized `d2`/`dinf`, signed and absolute norm
errors, both entropy errors, checkpoint candidate-versus-dense fixed-mask
trace-distance errors, `Delta_F`, exact fixture/SDIM/Stim/GC key coverage and signed-value joins, and
final verdicts.  It compares already emitted pullback strings and imports none
of their generating libraries.  Thus no candidate worker owns its evaluator
truth, and reference/comparator time or memory never enters a candidate-lane
ratio.

The evidence no-shadow branch and each of the three measured performance
workers must independently emit the same canonical final-carrier hash.  It is
computed from the raw gauged `candidate._psi`, never the gauge-absorbed
`candidate.psi`.  For each ascending site id, transpose its tensor to physical
axis first followed by virtual axes in ascending neighboring-site order.  The
header lists the complete sorted declared graph-edge sequence
`(min_site,max_site)` and, for every edge, `gauge_present`; every present gauge
also has an array ordinal, NumPy `dtype.str`, and shape.  A missing gauge is
therefore explicit rather than silently skipped.

The canonical header bytes are exactly `json.dumps(header, ensure_ascii=True,
allow_nan=False, sort_keys=True, separators=(",", ":")).encode("utf-8")` with
no trailing newline.  The header records schema
`gcapeps-finite-memory-final-carrier-hash.v1`, lane, site/edge ids, axis roles,
tensor/gauge array ordinals, dtypes, and shapes, with no Quimb-generated index
name.  For GC the `frame` field is exactly an object with `kind` equal to
`stim_signed_images_v1`, integer `num_qubits=2*w`, and arrays `x_images` and
`z_images`, each of length `2*w` in ascending-q order.  Every image is exactly
`{"sign":s,"body":p}` with integer `s` in `{-1,+1}` and ASCII `p` of length
`2*w` over `IXYZ` in q0-to-q-last order; a `+/-i` image fails.  For plain,
`frame` is JSON null.  Both headers contain lower-case 64-hex fields
`input_preparation_transcript_sha256` and
`shared_evolution_transcript_sha256`.  Thus a wrong or omitted frame update
cannot pass by leaving residual tensors unchanged.

The SHA-256 input is the ASCII namespace
`gcapeps-finite-memory-final-carrier-hash-v1\0`, then the UTF-8 header and every
canonical C-order array, each independently prefixed by its unsigned 64-bit
big-endian byte length.  Array bytes are exactly `.tobytes(order="C")`; tensor
arrays precede present gauge arrays.  All three
performance hashes must be identical and equal to the evidence no-shadow hash
for the same lane, cell, and input.  The independently instrumented evidence
branch must match too; any mismatch is a control failure rather than timing
variance.

Every JSON result/report canonical projection is exactly
`json.dumps(value, ensure_ascii=True, allow_nan=False, sort_keys=True,`
`separators=(",", ":")).encode("utf-8")`, with no trailing newline, after
removing exactly `result_projection_sha256`; that field hashes those bytes.
Every persisted JSON artifact in this protocol uses one publication primitive.
The publisher holds the destination parent dirfd, creates a same-directory
mode-0644 temporary file with `O_CREAT|O_EXCL|O_NOFOLLOW`, writes the
already-canonical bytes, fsyncs the file, performs
`renameat2(...,RENAME_NOREPLACE)`, and fsyncs the parent.  It
then reopens the destination relative to the held dirfd with `O_NOFOLLOW`,
requires the expected device/inode/mode-0644/link-count-one identity, rereads exactly those
bytes, and externally records their byte length and SHA-256.  A publication
receipt uses the same primitive.  No artifact may weaken this sequence or
rewrite the destination after publication.
For every nonterminal artifact, the supervisor or parent externally computes
the complete published-file SHA-256; no JSON file claims its own complete-file
hash.  The terminal held-out report is the deliberate exception: it claims no
complete-file SHA and uses its internally verifiable
`result_projection_sha256` as its final persistent identity until a tracked
result note externally binds its complete bytes.

Every persisted NumPy array uses an exact `ndarray-v1` JSON object.  The object
below illustrates the exact key set; dtype, shape, and nbytes values remain
owning-schema-specific.  Decimal
JSON lists, real/imaginary pairs, a hash-only substitute, compression, or an
implementation-defined binary blob are forbidden.  The exact key set is

```json
{
  "encoding": "ndarray-v1",
  "dtype": "<c16",
  "shape": [1],
  "order": "C",
  "nbytes": 16,
  "data_sha256": "lower-case-64-hex",
  "data_base64": "canonical-padded-RFC4648"
}
```

`shape` contains only non-boolean nonnegative JSON integers.  `nbytes` is a
non-boolean integer equal to
`math.prod(shape) * np.dtype(dtype).itemsize`.  Each owning schema fixes the
allowed dtype, rank, and shape: complete vectors, reduced states, PEPS tensors,
and other registered complex arrays use exactly little-endian `"<c16"`;
registered gauges, singular spectra, and other real arrays use exactly
little-endian `"<f8"`.  The execution environment must be little-endian, and
the source arrays must already have the registered NumPy `complex128` or
`float64` dtype and C-contiguous storage.  Serialization may not cast,
byteswap, normalize, phase-fit, permute, or otherwise alter a value.

For array `a`, `raw` is exactly `a.tobytes(order="C")`;
`data_sha256=hashlib.sha256(raw).hexdigest()`; and `data_base64` is exactly
`base64.b64encode(raw).decode("ascii")`, including canonical `=` padding and
with no whitespace.  A decoder requires the exact object keys, registered
dtype/rank/shape, ASCII Base64 with `validate=True` followed by byte-for-byte
re-encoding equality, exact decoded length, and matching SHA-256 before it
constructs
`np.frombuffer(raw,dtype=np.dtype(dtype)).reshape(shape,order="C").copy(order="C")`.
It then rechecks dtype, shape, C contiguity, raw-byte equality, and all
registered finite-value gates.  Signed zero and every finite complex bit
pattern are preserved.  The comparator consumes these decoded raw values,
never the hash alone.

The coordinate convention is q0-most-significant-bit.  System qubits
`S_0..S_(w-1)` occupy the high-order axes and memory qubits
`M_0..M_(w-1)` the low-order axes.  For raw vector \(v\),

before any division, normalization, reduction, Schmidt decomposition, fidelity,
or entropy calculation, require an exact one-dimensional shape `(2**(2*w),)`,
exact dtype `complex128`, and finite real and imaginary parts.  Compute
`z=np.vdot(v,v)` in `complex128`, record the raw C-order byte hash,
`abs(imag(z))`, and `real(z)`, require `abs(imag(z))<=1e-12`, and require
finite `real(z)>0`.  This gate applies to every dense and candidate vector,
including every finite-ensemble path.  A wrong shape/dtype, zero norm,
nonfinite component, or excessive imaginary residual fails before any metric.
Every such vector is present as an `ndarray-v1` object, and its
`data_sha256` must equal the pre-metric raw C-order vector hash already recorded
for that checkpoint.
Only after it passes define

\[
A=\operatorname{reshape}_{C}(v;2^w,2^w),\qquad
\rho_S=AA^\dagger/\operatorname{Re}z.
\]

For every dense or candidate reduced state, define the max-entry residuals

\[
h_\rho=\max_{ij}|\rho_{ij}-\rho^*_{ji}|,\qquad
t_\rho=|\operatorname{Tr}\rho-1|,
\]

then require \(h_\rho,t_\rho\le10^{-12}\) before using the metric-local
Hermitian copy \(\rho_H=(\rho+\rho^\dagger)/2\).  With
\((\lambda,V)=\operatorname{eigh}(\rho_H)\), require

\[
\min_j\lambda_j\ge-10^{-12},\quad
e_{\rm pair}=\max_{ij}|(\rho_HV-V\operatorname{diag}\lambda)_{ij}|\le10^{-10},
\quad
e_{\rm recon}=\max_{ij}|(\rho_H-V\operatorname{diag}(\lambda)V^\dagger)_{ij}|\le10^{-10}.
\]

Values in \([-10^{-12},0)\) are clipped to zero only after recording
\(m_-=\sum_j\max(0,-\lambda_j)\) and requiring \(m_-\le10^{-12}\).
The clipped values are divided by their positive sum;
the sum, renormalization factor, and \(h_\rho/2\) Hermitization correction are
recorded.  No stored vector or density matrix is changed.  Entropies use these
metric-local normalized eigenvalues and base-2 logarithms, with
\(0\log_2 0=0\):

\[
S_1=-\sum_j\tilde\lambda_j\log_2\tilde\lambda_j,\qquad
S_2=-\log_2\sum_j\tilde\lambda_j^2.
\]

Trace distance is evaluated as
\(D(\rho_1,\rho_2)=\tfrac12\sum_j|\operatorname{eigvalsh}(
(\rho_{H,1}-\rho_{H,2}))_j|\).  The initial fixed-mask and ensemble
distances must equal one within \(10^{-12}\).

The normalized Schmidt values are the singular values of \(A\) divided by
\(\|v\|_2\); numerical rank counts values greater than
\(10^{-12}\) times the largest normalized value.

Candidate complete vectors are materialized outside performance timing at each
cell's checkpoints \(\{0,1,2,4,R_{\rm cell}\}\cap[0,R_{\rm cell}]\), with
\(R_{\rm cell}\) mandatory.  For the stress cell,
\(R_{\rm cell}=R_\star\).  The dense route remains every-round.
GCAPEPS constructs `QuimbPEPSCarrier` with
`contraction_optimize="greedy"`, immediately asserts the stored constructor
value is exactly `"greedy"`, calls `state_vector(max_qubits=14)`, then
applies the literal accumulated Clifford transcript gate by gate in
\(O(N_{\rm Clifford}2^{2w})\)
time.  It never constructs a \(2^{2w}\times2^{2w}\) Stim tableau unitary.
At every checkpoint a transcript-rebuilt Stim tableau must equal the live
tableau.  Exact-small controls compare literal and tableau-derived unitaries
only projectively because a tableau has no Clifford global phase.  Let `j` be
the first C-order matrix index where both magnitudes exceed `1e-12`; absence of
such an index fails.  Set `phi=(U_literal[j]/U_tableau[j]) / abs(...)`, require
`abs(abs(U_literal[j]/U_tableau[j])-1)<=1e-12`, and require
`max(abs(U_literal-phi*U_tableau))<=1e-12`.  The selected `j` and `phi` are
recorded.  This deterministic diagnostic phase is not optimized or reused and
does not relax the no-phase-fit rule for candidate/reference state metrics.
The reference uses separate matrices and helpers.

No stored reference or candidate vector is normalized, phase-fitted, cast, or
permuted.  First persist its raw hash and norm, then make an explicitly
metric-local normalized copy for reduced-state, entropy, normalized-distance,
and candidate fixed-mask checkpoint trace-distance diagnostics.  The payload
records:

```text
stored_vector_normalized_before_metric = false
metric_local_normalized_copy = true
phase_fit = false
coordinate_permutation = false
dtype_cast = false
```

For reference \(x\) and candidate \(y\), required metrics include

\[
F_{\rm raw}=\frac{|\langle x|y\rangle|^2}
{\langle x|x\rangle\langle y|y\rangle},
\]

\[
d_{\rm rel}=\frac{2\|x-y\|_2}{\|x\|_2+\|y\|_2},\qquad
d_{\rm norm}=\frac{2|\|x\|_2-\|y\|_2|}
{\|x\|_2+\|y\|_2}.
\]


Both norm-squared denominators and \(F_{\rm raw}\) must be finite; each
denominator must be strictly positive; and \(F_{\rm raw}<0\) fails.  Record
\(F_{\rm raw}\) and
`fidelity_roundoff_correction=max(0,F_raw-1)`.  Set
\(F=\min(1,F_{\rm raw})\) only when that correction is at most \(10^{-12}\);
a larger excess fails.

After that gate, \(D_{\rm pure}=\sqrt{1-F}\).  No square root or fidelity
clipping is evaluated before the gate passes.

Writing \(n_x=\|x\|_2\), \(n_y=\|y\|_2\),
\(\hat x=x/n_x\), and \(\hat y=y/n_y\), also record

\[
d_{2,\rm raw}=\|x-y\|_2,\qquad
d_{\infty,\rm raw}=\max_j|x_j-y_j|,
\]

\[
d_{2,\rm normalized}=\|\hat x-\hat y\|_2,\qquad
d_{\infty,\rm normalized}=\max_j|\hat x_j-\hat y_j|,
\]

\[
\Delta n_{\rm raw}=n_y-n_x,\qquad
e_{n,\rm raw}=|\Delta n_{\rm raw}|,\qquad
e_{S_k}=|S_k^{\rm candidate}-S_k^{\rm dense}|\quad(k=1,2).
\]

Evidence artifacts require raw candidate vectors and their raw-gate fields,
candidate-only local reduced-state/eigen diagnostics, tensor/gauge data,
candidate memory categories, full/kept spectra, discarded weight/fraction,
positive-event counts, and signed-pullback rows.  They may not contain any
reference vector/value/hash/locator or any candidate-versus-reference metric.
The terminal comparator alone requires every displayed cross-artifact distance,
both raw norms, signed/absolute raw norm error, both entropy errors, checkpoint
trace-distance errors, `Delta_F`, and the resulting verdicts.
Performance schemas intentionally omit complete vectors, full/kept spectra,
tails, positive-event fields, and all cross-artifact metrics rather than emit
null/zero placeholders; they retain algorithm bonds, logical/process memory,
final-carrier hash, and timing.  At every materialized checkpoint the comparator
reports only \(|D_r^{\rm candidate}-D_r^{\rm dense}|\) for fixed `CARRIER`.
Sparse-checkpoint increments are never summed or named a candidate BLP measure
or BLP-measure error; candidate-versus-ensemble BLP error is forbidden.
Local tails remain non-certifying.

Bond fields are `max_exact_precompression_bond` (GC only; null for plain),
`max_committed_bond`, and `final_committed_bond`.  The first includes the exact
tree transient before native compression; the latter two sample only committed
states.  Plain physical bonds and GC residual bonds remain separate resource
diagnostics and are never treated as semantically equal.

Candidate-owned logical bytes have four nonoverlapping base categories:

- `carrier_tensor_bytes`: raw `candidate._psi` tensor arrays, with
  `tensor_role=plain_physical` or `gc_residual`;
- `gauge_spectrum_bytes`: live gauge-store arrays only;
- `frame_bytes`: the live GC frame's canonical payload, exactly zero for plain;
- `ledger_bytes`: algorithm-owned physical, construction, compression,
  frame-update, and signed-pullback ledgers only.

Timing, memory-accounting, provenance, result, comparison, full/kept shadow
spectra, and tail rows are excluded from `ledger_bytes`.  Array counts walk to
unique underlying NumPy root buffers by object identity and count each root
`nbytes` once.  A root alias across categories is rejected; sharing inside one
category is deduplicated.  Frame and ledger bytes are UTF-8 lengths of canonical
JSON payloads with sorted keys, compact separators, and nonfinite values
rejected.  `total_owned_logical_bytes` is the sum of the four base categories.

Evidence owns two additional categories.  `evidence_auxiliary_array_bytes`
contains the entire instrumented complete branch's carrier/gauge arrays,
uncapped-shadow tensors/gauges, candidate vectors, and literal-lift arrays.
Every uncapped shadow is a complete carrier copy: all of its carrier/gauge
arrays belong to the auxiliary-array category and all of its independently
owned frame, history, and algorithm-ledger payload belongs to the auxiliary-
ledger category.  Any separately owned uncounted object fails.  The ledger
category also contains the complete instrumented branch's frame/algorithm
ledger, uncapped-tail/full/kept-spectrum rows, and candidate-only metadata.
At every evidence sample,

```text
evidence_owned_logical_bytes =
    current_base_total_owned_logical_bytes
    + evidence_auxiliary_array_bytes
    + evidence_auxiliary_ledger_bytes
```

Dense and comparator processes instead report disjoint
`dense_reference_array_bytes` and `comparator_array_bytes`; neither is
attributed to plain or GC.  Root-buffer alias rejection applies across all
concurrently owned categories in one process.

The evidence worker is sequential.  It first runs the canonical no-shadow base
algorithm from the registered initial fixture, computes all base algorithm
fields and the final-carrier hash, freezes those values in memory without
constructing core bytes, and releases the complete branch.  It then starts the
instrumented branch from a byte-identical
initial fixture.  The instrumented branch is evidence-only, including its whole
carrier, frame, history, and ledgers.  No two complete branches coexist unless
all of their arrays and ledgers are counted in the two auxiliary categories.
After no-shadow release and throughout the instrumented run,
`current_base_total_owned_logical_bytes=0`; only timing/provenance/result bytes
remain, excluded from algorithm logical totals but visible to RSS/cgroup.
Only the no-shadow branch defines `final_committed`, `max_committed`, and
`max_sampled_algorithm`; the instrumented branch only corroborates them and
supplies candidate vectors, signed pullbacks, spectra, events, and tails.


Algorithm and evidence workers report:

```text
final_committed_owned_logical_bytes
max_committed_owned_logical_bytes
max_sampled_algorithm_owned_logical_bytes
```

Evidence workers additionally report
`max_sampled_evidence_owned_logical_bytes`; performance workers omit that field
rather than emitting a zero placeholder.  Dense and comparator workers report
`max_sampled_dense_reference_array_bytes` and
`max_sampled_comparator_array_bytes`, respectively.

For the no-shadow base, sampling occurs after initialization; immediately after creation of every
uncommitted-candidate deep copy; before and after every named algorithm
substep; before commit while the old committed base and new candidate are both
owned; after successful commit; and after release of the predecessor.
`max_committed_owned_logical_bytes` is the maximum over a single current
committed carrier after predecessor release at each epoch;
`max_sampled_algorithm_owned_logical_bytes` includes old-committed plus
uncommitted-candidate coexistence.  Evidence workers additionally sample after
instrumented-branch creation, immediately after each shadow deep copy,
after the uncapped shadow finishes but before it is released, after each
candidate-vector or literal-lift materialization, and immediately before each
such auxiliary is released.  Dense-reference and comparator processes sample
after each state/reduced-state/ensemble or comparison-array materialization and
immediately before release.  Every **registered persistent** auxiliary crosses
one of these hooks and cannot evade the logical peak.

The algorithm maximum includes all concurrently owned committed-base and
uncommitted-candidate payloads at these ownership-transition samples.  Python
objects, allocator overhead, library caches, interpreter state, and ephemeral
library/SVD workspaces created and freed between explicit sample points are
excluded from logical bytes and visible only, if at all, in RSS/cgroup peaks.
On Linux, the child's post-root/pre-trailer
`resource.getrusage(resource.RUSAGE_SELF).ru_maxrss` sample is KiB and converts
to bytes by multiplication by 1024.  The supervisor-owned live pre-release
cgroup-v2 snapshot and retained systemd `MemoryPeak` are bytes and cover the
complete worker process including trailer/write and the handshake wait.
Those process peaks supplement but never replace a promised logical sample.
Plain frame bytes are exactly zero.

The project-only fidelity labels are:

```text
high       F >= 0.99
degraded   0.95 <= F < 0.99
low        F < 0.95
```

They classify only the bounded output and do not define generic acceptable
PEPS faithfulness.

## 8. Calibration firewall

Calibration is non-formal and cannot enter the target summaries.  It uses run
partition `CALIBRATION`, width \(w=7\), axis family 3,
\(p_{\rm event}=0.75\), seeds `0..3`, and the displayed ordinal candidate set:

```text
gamma_label       = (pi/11, pi/9, pi/7, pi/5)
gamma_float64_hex = (0x1.247426bd47de3p-2, 0x1.657184ae74487p-2,
                     0x1.cb91f3bbba140p-2, 0x1.41b2f769cf0e0p-1)
gamma_index       = (0, 1, 2, 3)
rounds            = (4, 6, 8, 10, 12)
rounds_index      = (0, 1, 2, 3, 4)
seed              = (0, 1, 2, 3)
```

The executable values are reconstructed with `float.fromhex`; no runtime
evaluation of symbolic \(\pi/d\) is allowed.  The physical rotation angle is
the exact binary64 sign flip of the selected gamma.

The displayed tuples define order.  Search order is lexicographic on
`(gamma_index,rounds_index,seed)`; labels and binary64 values are never
string-sorted or numerically re-sorted.  Each pair has global stage barriers;
interleaving A/B/C work from different seeds is forbidden:

1. **A — dense witness.** In seed order `0,1,2,3`, launch one dense-reference
   worker per seed; it executes both inputs with that seed's fixed `CARRIER`
   mask.  A seed is A-positive only when
   \(\delta_{\max}^{\rm carrier}>10^{-10}\); summed \(W\) is report-only.
   Finish all four Stage-A terminal dispositions before Stage B.
2. **B — plain cap probe.** Visit only A-positive seeds in ascending order.
   For each, launch plain input 1 and then plain input 2, even if input 1 is a
   completed no-cap scientific negative.  Each probe stops at its first positive
   cap event or trajectory completion.  A seed is B-positive only if both are
   positive.  Finish every applicable Stage-B disposition before Stage C.
3. **C — GC cap probe.** Visit only B-positive seeds in ascending order and
   launch GC input 1 then GC input 2 under the same no-short-circuit rule.  A
   seed is A--C-prequalified only if both GC probes are positive.  Finish every
   applicable Stage-C disposition before Stage D.
4. **D — full evidence and comparison.** Visit A--C-prequalified seeds in
   ascending order.  For each seed, launch full plain input 1, plain input 2,
   GC input 1, and GC input 2 evidence workers in that order, with no positive-
   event early stop.  Then launch one SDIM/independent-Stim corroboration child
   for both inputs and all prefixes, followed by the terminal comparator against
   the retained Stage-A dense artifact, four candidate evidence artifacts, and
   SDIM artifact.  Fidelity is reported but never selects a seed.

Stage-B/C probes have dedicated owners
`scripts/external_baselines/plain_quimb_finite_memory_cap_probe_worker.py` and
`scripts/external_baselines/gcapeps_finite_memory_cap_probe_worker.py`.
Their schemas are respectively
`error_coupling_simulator.external.gcapeps_finite_memory.plain_cap_probe_worker.v1`
and
`error_coupling_simulator.external.gcapeps_finite_memory.gcapeps_cap_probe_worker.v1`.
They accept only `run_partition="CALIBRATION"` and run one instrumented capped
trajectory; they do not run the full no-shadow/instrumented evidence pair.
Immediately before every two-site split, an uncapped shadow starts from that
split's immediate pre-state while the real candidate executes the pinned cap 32.
A probe validates and atomically commits the complete current physical operation
before it may stop.  If a positive row first appears at any split, the probe
finishes all remaining splits/validators for that operation, commits it, records
the first-positive locator and every row in that operation, then stops before the
next operation; otherwise it continues to trajectory completion.  For GC, one
physical rotation includes its complete exact lowering, all routed compression
splits, validation, and commit.  A probe emits cap rows, exact stop locator,
provenance, raw worker-root and launch-receipt durations, and late RSS/cgroup telemetry, but no
complete vector, cross-artifact metric, aggregate timing sample, fidelity, BLP,
or final scientific verdict.  It uses the evidence resource class of 24 GiB and
1800 seconds and consumes the Stage-B/C attempt counter.  Full Stage-D evidence
must re-establish every positive; probe-positive/full-negative is invalid.

A seed is **A--C-prequalified** only if its fixed-mask maximum increment crosses
the threshold and all four plain/GC-by-input probes have a positive cap event
under Section 6.  It is **Stage-D PASS** only when all conditions hold: the four
full evidence workers, SDIM child, and comparator all complete; all four evidence
runs again contain a positive cap event; and every algebra, byte-equality,
provenance, schema, and resource gate passes.  A
probe-positive/full-run-negative discrepancy is
`CALIBRATION_INVALID_CONTROL_FAILURE`, not a scientific negative.  A pair
qualifies when two distinct seeds reach Stage-D PASS.  The first two such seeds
in ascending order are frozen; immediately after the second PASS, all later
seeds and parameter pairs are forbidden.  If a pair cannot produce two PASS
seeds after all applicable work terminates, proceed to the next pair.  The
selected pair is therefore the first qualifying displayed ordinal pair;
\(p_\star=0.75\) is fixed, not selected from results.

Calibration has two additional hard ceilings: 12 hours of total supervisor wall
and 100 Stage-B/C candidate cap-probe launch attempts.  The wall root is
`time.perf_counter_ns()` captured immediately before the first Stage-A child;
the deadline is exactly root plus `12*60*60*10**9` ns.  The manager's ordinary
`TimeoutStartSec` remains exactly its 600/1800-second class.  Independently, the
supervisor owns a monotonic absolute-deadline watchdog: before every child it
requires positive remaining time, and at the first observation at or after the
deadline it sends a recorded control-group `SIGKILL` to any live unit.  The
watchdog initiator and issue/terminal offsets distinguish that censor from an
unexpected signal.  A unit may not qualify merely because its manager timeout
would occur later.

A selection is accepted only if the second Stage-D comparator PASS and the
atomic calibration-report commit both finish no later than the deadline.  The
commit endpoint is after temporary-file fsync, no-replace rename,
parent-directory fsync, destination reopen, and exact-byte rehash.  The same
rule applies to a complete-grid `NO_ELIGIBLE_BOND32_NONMARKOVIAN_CELL` report.
An incomplete/invalid audit report may commit later and cannot become eligible.
Whether commit was timely is recorded only by the post-commit publication
receipt below, never by the report being published.

One Stage-B/C lane--input attempt is one fresh worker.  Such a launch is allowed
iff the counter is below 100; the counter increments immediately before launch,
so attempt 100 may finish and may enable selection.  Only when required work
would need attempt 101 is the ceiling reached.  Launch failure, timeout, OOM,
or malformed/nonfinite return still consumes its attempt.  Stage-A, Stage-D,
comparator, and report work do not increment this counter but remain inside the
12-hour wall.  These ceilings cannot reorder, short-circuit, or widen the grid.

Failure classification follows the Section-10 terminal union.  Trusted
manager/supervisor facts are classified first: registered start timeout,
deadline kill, OOM/memory-limit event, launch-resource failure, required work
that cannot start before the deadline, or needed attempt 101 is
`CALIBRATION_INCOMPLETE_CENSORED`; no held-out work is then allowed.  Missing or
truncated frames are allowed only for such a bound external censor.  A clean
exit-zero worker is parsed canonically; a nonfinite JSON token, malformed or
extra frame byte, schema violation, or unexpected exit/signal is
`CALIBRATION_INVALID_CONTROL_FAILURE`.  A worker-reported internal nonfinite or
resource censor is incomplete only when its two finite frames and clean exit
validate.  If all required compute
terminals finished but an otherwise-PASS or complete-grid no-eligible report is
not atomically committed by the deadline, the publication receipt's unique
final class is instead
`CALIBRATION_INVALID_CONTROL_FAILURE`.  Other algebra, sign, payload-equality,
provenance, implementation-identity, probe/full-run, publication, and corruption
failures are likewise invalid.  Both classes stop all later calibration work.
Only a completed witness/no-cap outcome is a scientific negative and advances.
`NO_ELIGIBLE_BOND32_NONMARKOVIAN_CELL` is emitted only after the entire frozen
grid completes with no censor/control failure and no qualifying pair.  The
search is never widened.

The selected \(\gamma\), \(R_\star\), \(p_\star\), both qualifying calibration
seeds, exact per-seed operation counts, all rejected/failed attempts, and code
identities are written to the external artifact

```text
outputs/external_baselines/gcapeps_finite_memory_bond32/calibration_report.json
error_coupling_simulator.external.gcapeps_finite_memory.calibration.v1
```

The supervisor writes canonical JSON as UTF-8 with sorted keys, compact
separators, non-finite values rejected, and no trailing newline, then publishes
it atomically with no replacement.  The report records every attempted and
skipped stage/seed, launch counter before/after, wall deadline/root offsets,
child envelope/launch-receipt hashes, comparator results, and the
pre-publication compute disposition.  It does not claim that its own publication
has completed or contain its own complete-file SHA-256.

After temporary-file fsync, no-replace rename, parent-directory fsync,
destination reopen, and exact-byte rehash, the publisher captures
`publication_committed_offset_ns` from the calibration wall root.  Only then it
publishes, outside the 12-hour eligibility clock, the separate artifact

```text
outputs/external_baselines/gcapeps_finite_memory_bond32/calibration_publication_receipt.json
error_coupling_simulator.external.gcapeps_finite_memory.calibration_publication_receipt.v1
```

The receipt binds report path/schema/byte length/complete-file SHA-256,
pre-publication disposition, root/deadline, publication-start and committed
offsets, every fsync/rename/reread gate, `committed_by_deadline`, and the final
calibration class.  Its own publication is deliberately outside the tested
report-commit span.  A missing/invalid receipt forbids amendment and held-out
work; it cannot make a late report timely.  The later amendment records both
the report and receipt complete-file SHA-256 and recomputes both before use.
They are external outputs, not tracked source files.  A passing report/receipt
pair is the input to a target-amendment commit
that freezes the selected values and held-out fixture before any `HELDOUT`
worker is launched.  Calibration states, masks, timings, and fidelities are
excluded from target plots and aggregates.

The machine-readable amendment path and schema are frozen as

```text
docs/simulator_validation/GCAPEPS_FINITE_MEMORY_BOND32_TARGET_AMENDMENT.json
error_coupling_simulator.external.gcapeps_finite_memory.calibration_amendment.v1
```

The amendment must bind the calibration-report and publication-receipt
SHA-256 values; the current SHA-256 of
the closure, this preregistration, `docs/METRICS.md`, and
`docs/NUMERICAL_PROVENANCE.md`; the partial-SWAP sign audit and its independent
review hashes; the exact independent preregistration-rereview path/hash
`docs/simulator_validation/GCAPEPS_FINITE_MEMORY_BOND32_PREREG_INDEPENDENT_REREVIEW_2026-07-29.md`;
the theory-only commit/tree freezing those documents; final parent and fork
implementation commits/trees; main environment-lock identity; the SDIM
bootstrap declaration plus canonical full runtime-inventory schema/hash; the
manager-preflight receipt path/schema/projection/byte-length/complete-file SHA
and selected systemd build/manager cgroup/runner non-dumpability/dynamic-user/
repository-read-gid/security-property projection; fixture, held-out cell-list,
and every result-schema version; and the exact event-mask namespace version and
endpoint/nesting disposition.  Every child rehashes and verifies these bound
identities before computation.  It records the selected
gamma both as its symbolic grid label and `float64.hex()`, \(R_\star\),
`p_event_numerator=3`, `p_event_denominator=4`, and the two ascending qualifying
calibration seed ids.

Before the amendment is committed, the fixture emitter deterministically
materializes the complete sorted held-out cell list and its fixture hash from
those selected values.  The amendment binds that cell list, the unsigned
held-out seed, both registered input identities, all mask namespaces/indices,
and the held-out fixture SHA-256.  The held-out seed and cell list are not left
for a later runner default.

The amendment is committed by itself after calibration and before held-out
execution.  It cannot contain the commit/tree that contains itself.  Instead,
every held-out child and terminal result records, from outside the amendment,
the clean parent amendment commit/tree plus the exact amendment-file SHA-256,
and requires `run_partition="HELDOUT"`.  A missing/mismatched amendment hash,
dirty parent or fork tree, nonmatching fixture, or a calibration-partition child
in a held-out comparison aborts before any target metric is read.

The calibration report and amendment retain all attempts and dispositions.
They distinguish `PASS`, completed scientific-negative witness/no-cap outcomes,
`CALIBRATION_INCOMPLETE_CENSORED`, and
`CALIBRATION_INVALID_CONTROL_FAILURE`; neither censored nor invalid runs can be
relabelled as exhausted negative evidence.

## 9. Held-out sweep

The held-out run partition is `HELDOUT`; its seed is the unsigned big-endian integer
encoded by the first eight bytes of
`SHA256(b"gcapeps-finite-memory-heldout-v1")`.  It is independent of every
calibration seed.

Before the first held-out child, the runner read-only rechecks the amendment-
bound system-manager build/cgroup, controllers, repository-read gid, sandbox-
property capability, runner PID/start time, and `PR_GET_DUMPABLE==0`.  This is
not manager reselection: mismatch aborts, and user/alternative-manager fallback
is forbidden.  Each held-out unit still receives a fresh distinct DynamicUser
whose effective properties are compared with the amendment policy.

With the calibration-selected \(\gamma\), \(R_\star\), and
\(p_\star=0.75\), execute the union of these unique cells:

| slice | widths | rounds | axis family | \(p_{\rm event}\) |
|---|---|---|---|---|
| width | \(3,5,7\) | \(R_\star\) | 3 | \(p_\star\) |
| rounds | 7 | \(1,2,4,R_\star\) | 3 | \(p_\star\) |
| axis family | 7 | \(R_\star\) | \(1,2,3\) | \(p_\star\) |
| probability | 7 | \(R_\star\) | 3 | \(0,0.25,0.50,0.75,1.00\) |

The fixture represents every cell only as the integer tuple
`(width, rounds, axis_family, p_event_numerator, p_event_denominator)`, with
`p_event_denominator=4` even at 0 and 1.  It forms the set union by exact tuple
identity, then sorts lexicographically by those five integers.  Each row retains
`slice_membership`, sorted by the fixed enum order
`(width, rounds, axis_family, probability)`.  A row runs `BLPENSEMBLE` iff
`"probability" in slice_membership`.  The stress tuple belongs to all four
slices and therefore runs the ensemble.  The union has exactly 11 cells when
`R_star==4` and 12 otherwise.  The amendment binds the complete cell values,
memberships, order, cardinality, `run_blpensemble` flags, and canonical list
SHA-256; a runner may neither regenerate nor reorder it.

The complete held-out supervisor report is atomically published without
replacement at
`outputs/external_baselines/gcapeps_finite_memory_bond32/heldout_report.json`
under schema
`error_coupling_simulator.external.gcapeps_finite_memory.bond32_comparison.v1`
and binds every child envelope and launch receipt's complete-file SHA-256.  It
contains `result_projection_sha256` but recursively forbids its own
`complete_file_sha256` or `heldout_report_complete_file_sha256` field.

After no-replace rename and parent-directory fsync, the outer publisher reopens
the exact destination inode and computes its complete-file SHA-256 without
rewriting the report.  The persistent external owner is the later tracked note

```text
docs/simulator_validation/GCAPEPS_FINITE_MEMORY_BOND32_RESULT_2026-07-29.md
```

which records report path/schema/byte length/complete-file SHA-256 and the
pre-result implementation/amendment identities.  The note does not claim the
commit containing itself; its later Git commit/tree is the external integrity
owner.  Until that note is committed, the report is retained raw output but is
not terminal claim-bearing evidence.

Within each held-out cell the serial launch graph is fixed:

1. dense reference, including `BLPENSEMBLE` exactly when flagged;
2. plain evidence input 1, then input 2;
3. GC evidence input 1, then input 2;
4. performance warmups and the six measured launches in Section 10;
5. one SDIM corroboration child for both inputs and all registered prefixes;
6. the terminal comparator.

The following failure propagation is exhaustive and uses the Section-10
terminal precedence.  A registered external timeout/OOM/deadline/launch censor
is classified from trusted facts before partial bytes; otherwise a clean
exit-zero worker must supply exactly two canonical frames.  Noncanonical or
nonfinite JSON, malformed/extra bytes, schema failure, or an unexpected
exit/signal is invalid control.  An internal censor needs valid finite frames.

- identity, algebra, sign, schema, provenance, canonical-hash,
  `p_event=0` negative-control, or SDIM signed-equality mismatch yields
  `HELDOUT_INVALID_CONTROL_FAILURE`.  Stop all later launches in that cell and
  all later cells; retain completed rows; forbid BLP, \(H_F\), \(H_E\), and Q4
  classifications.
- a `supervisor_censor` backed by a registered external timeout, OOM,
  absolute-deadline, or launch-resource initiator, or a clean-exit-zero
  schema-valid finite `worker_censor` in dense, evidence, SDIM, or comparator,
  yields `INCOMPLETE_CENSORED` for that cell.  For any such scientific censor,
  every later node in the current cell is `SKIPPED_PREREQUISITE`, even if it
  could be run independently; continue only with the next fresh cell.  If SDIM
  censors after performance, completed raw performance rows remain, but the cell
  and its Q4 terminal classification are unavailable.  The sweep terminal is
  `HELDOUT_INCOMPLETE_CENSORED`, and missing values are never scientific
  negatives.  This all-later-node rule has only the performance-only exception
  below.
- a performance-worker timeout/OOM/nonfinite/resource censor, or a
  performance-only timing reconciliation failure, leaves independently
  completed state, BLP, \(H_F\), and \(H_E\) evidence intact.  Continue all
  registered performance launches and later nodes; only the affected timing
  ratio/band is `UNAVAILABLE`.

`case_workflow_supervisor_wall_ns` is `completed` only when all nodes required
by the frozen graph finish.  An early stop records the observed partial duration,
terminal node, and `partial` status and is excluded from aggregates of complete
workflow totals.

Here `width=3,5,7` is the ladder width, not surface-code distance and not
qudit dimension.  Every unique union cell runs the fixed `CARRIER` dense anchor
and candidate comparison.  In addition, every probability-slice cell runs the
32-path dense-only `BLPENSEMBLE`; other slices make no finite-ensemble claim.
At \(p_{\rm event}=0\), absence of system--memory interaction is the registered
negative control and shared positive truncation is not expected.

The stress cell is
`(width=7, rounds=R_star, axis_family=3, p_event=p_star)`.
It must independently satisfy positive truncation in all four held-out evidence
trajectories: plain/GC crossed with inputs 1/2.  If any one does not, retain all
observations but mark the head-to-head
bond-32 stress verdict `INELIGIBLE_NO_SHARED_POSITIVE_TRUNCATION`.

## 10. Layered timing contract

Timing schema:
`error_coupling_simulator.external.gcapeps_finite_memory.layered_timing.v1`.

Schema ownership is not inferred from parallel lists.  Each worker owns the
role-specific `core_scientific_payload` schema mapped in
`docs/NUMERICAL_PROVENANCE.md`.  Shared helper
`scripts/external_baselines/gcapeps_finite_memory_timing.py` owns nested
`layered_timing.v1` and
`error_coupling_simulator.external.gcapeps_finite_memory.late_telemetry_trailer.v1`.
The root runner owns
`error_coupling_simulator.external.gcapeps_finite_memory.manager_preflight_receipt.v1`,
`node_terminal.v1`, `launch_receipt.v1`, and
`calibration_publication_receipt.v1`; the declared `ExecStopPost` helper owns
`systemd_failure_snapshot.v1`.  Worker cores and trailers are transport frames;
the supervisor-published node artifact always validates as `node_terminal.v1`
and names exactly one role-specific core schema or null for an external censor.
Calibration, controls, held-out aggregate, and amendment documents retain their
distinct aggregate schemas.  No schema fallback or multi-row validation is
legal.

Worker wall timestamps use Python `time.perf_counter_ns()` and CPU timestamps
use `time.process_time_ns()`, i.e. process user-plus-system CPU rather than
thread CPU or elapsed wall time.  Each process captures one wall root and one
CPU root before its first span; all offsets are integer nanoseconds relative to
the corresponding root.  The payload records the literal clock identifiers
`time.perf_counter_ns` and `time.process_time_ns`.  A supervisor uses its own
`perf_counter_ns` root; clock values from different processes are never
subtracted or nested.

Every span records:

```text
span_id
parent_span_id
scope
lane
case_id
trajectory_id
round_index
operation_index
step_index
kind
status
wall_start_offset_ns
wall_end_offset_ns
wall_duration_ns
cpu_start_offset_ns
cpu_end_offset_ns
cpu_duration_ns
child_wall_ns
child_cpu_ns
unattributed_wall_ns
unattributed_cpu_ns
```

Physical `round_index` is one-based and checkpoint zero is literal zero;
`operation_index` and `step_index` are zero-based within their declared parent.
Any index inapplicable to an aggregate scope is JSON null, never `-1` or an
implementation sentinel.
Worker spans are strictly nested and sequential.  Every completed span obeys
`duration_ns=end_offset_ns-start_offset_ns` exactly for both clocks.  For every
completed parent:

```text
parent_wall_duration_ns = sum(direct_child_wall_duration_ns) + unattributed_wall_ns
parent_cpu_duration_ns  = sum(direct_child_cpu_duration_ns)  + unattributed_cpu_ns
```

Negative unattributed time, duplicate ids, missing parents, overlapping
siblings, or any nonzero integer reconciliation mismatch is a hard failure.
A leaf wall or CPU duration of zero is legal; a negative duration is not.  Only
a scope used as a ratio numerator/denominator or complete worker/root total must
be strictly positive.

The candidate worker timing trees are:

```text
performance_worker_total
├── setup_and_gate_mask_materialization
├── candidate_algorithm_case_e2e
│   ├── candidate_initialization
│   └── round[*]/physical_operation[*]/named_algorithm_substep[*]
└── serialization

evidence_worker_total
├── setup_and_gate_mask_materialization
├── candidate_algorithm_case_e2e
│   ├── no_shadow_candidate_initialization
│   └── no_shadow_round[*]/physical_operation[*]/named_algorithm_substep[*]
├── validation_and_evidence_materialization
│   └── instrumented_replay_total
│       ├── instrumented_candidate_initialization
│       ├── checkpoint[0]_evidence_materialization
│       └── instrumented_round[*]
│           ├── physical_operation[*]/named_instrumented_algorithm_substep[*]
│           ├── uncapped_shadow_replay[*]
│           └── checkpoint_evidence_materialization[if registered]
└── serialization
```

All scientific array materialization, freezing, pre-metric validation, and the
first raw C-order SHA-256 occur inside
`validation_and_evidence_materialization`.  The `serialization` leaf owns
re-reading each frozen array, checking the pre-metric hash, constructing every
`ndarray-v1` Base64 object, and constructing the canonical
`core_scientific_payload` bytes.  It owns no contraction, replay, metric, or
candidate validation.  That core deliberately excludes the timing
tree/root, late process telemetry, supervisor values, and stdout framing, so no
self-timing cycle exists.  The leaf starts immediately before encoding and ends
after those bytes exist; the worker root ends immediately afterward.
Outside the worker root, the child calls
`resource.getrusage(resource.RUSAGE_SELF)`, builds a small canonical telemetry
trailer containing the completed timing tree/root and this precisely labelled
post-root/pre-trailer `ru_maxrss` sample, and emits exactly
`u64be(len(core)) || core || u64be(len(trailer)) || trailer` to stdout.
Both frames use the Section-7 canonical encoder; the trailer binds the core
SHA-256.  Trailer construction and both frame writes are explicitly untimed by
the worker root and are included in supervisor launch wall and full cgroup peak.

Before loading any evaluator artifact, the root runner calls
`prctl(PR_SET_DUMPABLE,0)` and requires `prctl(PR_GET_DUMPABLE)==0`; its PID,
`/proc/<pid>/stat` start time, real uid/gid, and non-dumpable result are lineage
identities.  Before the one-off SDIM inventory and calibration wall root it runs
a no-scientific-input sacrificial preflight against exactly the noninteractive
system manager (`systemd-run --system --no-ask-password`).  User-manager
execution is forbidden because it cannot give the child a distinct host uid;
there is no manager fallback.

Every sacrificial/scientific service must obtain `DynamicUser=yes` with a host
uid different from the runner and every concurrently live service, plus only
the frozen numeric repository-read supplementary gid.  Its repository view is
read-only and its run-output root inaccessible.  The preflight proves systemd
major 255, unified cgroup-v2 memory/pids/cpu controllers, namespace creation,
the exact sandbox/resource properties below, raw-file standard I/O, self-stop
handshake, byte caps, evaluator-path and `/proc/<runner-pid>/{root,fd,mem}`
denials, denied `process_vm_readv`/ptrace, retained systemd `MemoryPeak`, raw
spool quarantine, and complete unit unload.  Any readable evaluator byte or
runner handle fails the manager rather than weakening the firewall.

The root runner publishes the exact attempted manager, sacrificial dispositions,
selected system scope or null, full systemd build, manager cgroup, runner
dumpability identity, dynamic-host-uid policy, repository-read gid,
`PrivateUsers` value, every effective property, and
`result_projection_sha256` at

```text
outputs/external_baselines/gcapeps_finite_memory_bond32/manager_preflight_receipt.json
error_coupling_simulator.external.gcapeps_finite_memory.manager_preflight_receipt.v1
```

The receipt recursively forbids its own complete-file digest.  Its publisher
holds the parent dirfd, fsyncs the temporary file, performs no-replace rename,
fsyncs the parent, reopens with `O_NOFOLLOW`, requires the destination
device/inode/mode/link identity, and externally computes byte length and
complete-file SHA-256.  The SDIM inventory collector and every later child bind
and rehash the receipt schema, projection hash, byte length, and complete-file
SHA; the calibration report and amendment bind the same manager/property
projection.  If the system-manager leg fails, the receipt records no selected
scope and the environment is invalid/ineligible; no resource rule is relaxed
and no inventory or science child starts.

Every child uses a never-reused transient service name derived from the
run-manifest prefix, node id, and monotonic launch ordinal.  The supervisor
proves `LoadState=not-found`, then invokes `systemd-run --system --no-block
--no-ask-password`; `--wait`, `--pipe`, and `--collect` are forbidden.  Every
unit sets exactly one `ExecStart`, `Type=oneshot`, `RemainAfterExit=yes`,
`Restart=no`, `DynamicUser=yes`, the frozen numeric `SupplementaryGroups`,
`PrivateUsers=yes`, `ProtectSystem=strict`, `ProtectHome=read-only`,
`ReadOnlyPaths=<repo_abs>`, `InaccessiblePaths=<run_output_abs>`,
`WorkingDirectory=<repo_abs>`, `NoNewPrivileges=yes`, `PrivateTmp=yes`,
`PrivateDevices=yes`, `PrivateNetwork=yes`, `RestrictSUIDSGID=yes`,
`CPUAffinity=<selected_cpu_decimal>`, `LimitCORE=0`,
`TimeoutStartFailureMode=kill`, `TimeoutStopSec=15s`,
`KillMode=control-group`, `MemoryAccounting=yes`, `TasksAccounting=yes`, and a
unique `RuntimeDirectory=gcapeps-fm-<launch_id>` with
`RuntimeDirectoryMode=0755` and `RuntimeDirectoryPreserve=no`; `<launch_id>` is
the same validated lowercase ASCII launch id used in the unit name.  The
directory contains no evaluator state, and the only failure-snapshot location
is the absolute path
`/run/gcapeps-fm-<launch_id>/failure_snapshot.json`.
`PYTHONDONTWRITEBYTECODE=1` is sealed in the child environment.  Every effective
property is read back verbatim.

Performance units set `MemoryMax=12884901888` and `TimeoutStartSec=600s`; every
other child sets `MemoryMax=25769803776` and `TimeoutStartSec=1800s`.  All set
`RuntimeMaxSec=infinity`, `MemorySwapMax=0`, and `TasksMax=32`.  Core/trailer and
per-file limits are exact bytes:

| role class | `core_max` | `trailer_max` | `LimitFSIZE` |
|---|---:|---:|---:|
| dense reference | 1073741824 | 16777216 | 1090519056 |
| plain/GC evidence | 268435456 | 16777216 | 285212688 |
| fixture, probe, performance, inventory, SDIM, comparator, control | 67108864 | 16777216 | 83886096 |

`raw.stderr` has a 1048576-byte post-write validation cap in addition to the
role-wide kernel `LimitFSIZE`; the trusted failure helper refuses to write and
the supervisor refuses to accept a snapshot above 1048576 bytes.  Ordinary
stdin is capped at 67108864 bytes and comparator stdin at 4294967296
bytes.  No cgroup counter is reset.  Native threads are permitted within
`TasksMax`; the barrier proves no live descendant process, while any earlier
short-lived descendant remains included in cgroup `cpu.stat` and is not claimed
absent from the complete lifecycle.

The supervisor holds a device/inode-sealed dirfd for one fixed mode-0700 spool
parent outside the denied run-output root but on the same filesystem.  Before
each launch its exact child set is empty; it then creates exactly one fresh
canonical absolute `spool_abs` and mode-0600
`fixture.stdin`, `raw.stdout`, `raw.stderr`, and `failure_snapshot.copy` using
dirfd-relative `O_CREAT|O_EXCL|O_NOFOLLOW`.  It records every
device/inode/mode/link/owner identity and keeps the parent dirfd.  The exact
unit properties are

```text
StandardInput=file:<spool_abs>/fixture.stdin
StandardOutput=file:<spool_abs>/raw.stdout
StandardError=file:<spool_abs>/raw.stderr
```

Relative targets, symlinks, owner/inode drift, extra spool entries, and paths
outside the sealed parent fail.  PID 1 opens these files before the distinct
DynamicUser executes; the worker receives only fd 0/1/2 and cannot traverse the
supervisor-owned spool.  Output files are initially empty, journald/text
transport is forbidden, and the frozen stdin-size cap is checked before launch.

`fixture.stdin` is the sole scientific/protocol input channel for every child;
argv contains only the role and non-secret launch id, and no child receives an
artifact path or auxiliary descriptor.  Its bytes use
`error_coupling_simulator.external.gcapeps_finite_memory.input_transport.v1`:

```text
u64be(manifest_len) || canonical_manifest ||
repeat in manifest entry order:
    u64be(artifact_len) || exact_artifact_bytes
```

The manifest is capped at 16777216 bytes and 64 entries and fixes the role,
ordered entry names, owning schemas, exact byte lengths, and SHA-256 values.
Before allocation, the child `fstat`s fd 0, enforces the role-specific total
stdin cap, reads only the eight-byte manifest prefix, checks the manifest cap,
uses checked integer arithmetic, and requires exact container-size equality and
unique allowlisted entry names.  It then hashes each bounded entry before
parsing it.  The manifest's role-specific `role_parameters` has an exact schema
and does not count as an artifact entry.  Define these exact ordered sequences:

```text
I_CAL  = (manager_preflight_receipt,
          sdim_inventory_envelope, sdim_inventory_launch_receipt)
I_HELD = I_CAL || (target_amendment,)
B_CAL  = I_CAL  || (neutral_fixture_envelope,
                    neutral_fixture_launch_receipt)
B_HELD = I_HELD || (neutral_fixture_envelope,
                    neutral_fixture_launch_receipt)
X      = (dense_envelope, dense_launch_receipt,
          plain_input1_envelope, plain_input1_launch_receipt,
          plain_input2_envelope, plain_input2_launch_receipt,
          gc_input1_envelope, gc_input1_launch_receipt,
          gc_input2_envelope, gc_input2_launch_receipt,
          sdim_envelope, sdim_launch_receipt)
```

Production artifact entry sequences are exactly:

| run partition | child role | ordered artifact entry sequence |
|---|---|---|
| bootstrap | sacrificial manager preflight | empty |
| bootstrap | SDIM inventory collector | `(manager_preflight_receipt,)` |
| calibration | neutral-fixture emitter | `I_CAL` |
| held-out | neutral-fixture emitter | `I_HELD` |
| calibration | dense reference / BLP ensemble | `B_CAL` |
| held-out | dense reference / BLP ensemble | `B_HELD` |
| calibration | plain or GC probe/evidence | `B_CAL` |
| held-out | plain or GC evidence/performance | `B_HELD` |
| calibration | SDIM computation | `B_CAL` |
| held-out | SDIM computation | `B_HELD` |
| calibration | terminal comparator | `B_CAL || X` |
| held-out | terminal comparator | `B_HELD || X` |

The four evidence pairs in `X` are always in the displayed order.  No
production wildcard, optional artifact entry, or other role exists.  A
corruption control uses a separately enumerated synthetic role and cannot add
an entry to a production role.  In particular, an SDIM computation receives no
dense, plain, GC/candidate, comparator, or performance bytes; a candidate
receives no dense, peer-candidate, SDIM-result, or comparator bytes; and only
the terminal comparator receives cross-role numerical evidence.

Before writing the container, the supervisor opens every source artifact with
`O_NOFOLLOW`, verifies its bound device/inode/schema/byte-length and externally
owned complete-file SHA-256, and copies those exact bytes without re-encoding.
It fsyncs `fixture.stdin` and the spool directory, reopens and fstats the sealed
stdin inode, reparses the complete container with the same bounds, and requires
every entry length/hash to equal both its bytes and its external source hash.
The final node envelope binds the container byte length/SHA-256 and ordered
entry name/source-SHA sequence.  Thus “reads an artifact” always means reading
its sealed stdin copy, never opening the run-output tree.  Missing, extra,
duplicated, reordered, oversize, hash-mismatched, or noncanonical input is
`invalid_control`.

This is the raw-byte-preserving transport for the binary frames.  A clean worker
writes exactly the two frames and empty stderr, flushes and `fsync`s stdout,
then sends uncatchable `SIGSTOP` to its own process before it can exit.

The supervisor requires `MainPID` live/stopped, `cgroup.procs` equal exactly
that one process, and every task in `cgroup.threads` stopped, so no live worker
task can append during inspection.  Before allocating or JSON-parsing, it
`fstat`s the sealed stdout/stderr inodes.  Stderr must be within 1048576 bytes
and exactly zero for a clean worker.  Stdout must be within its role's
`LimitFSIZE`.  The parser reads only the first eight bytes, checks unsigned
`L_core<=core_max`, uses checked integer addition to locate and read the second
eight-byte prefix, checks `L_trailer<=trailer_max`, and requires exactly

```text
8 + L_core + 8 + L_trailer == raw_stdout_st_size
```

before either bounded payload read.  Only then may it decode canonical JSON and
schemas.  Oversize, arithmetic overflow, short prefix, or an extra byte is
`invalid_control`, never a resource censor.

While the tasks remain stopped it reads `memory.peak/current/swap.current`,
every `memory.events` key, `pids.current`, `pids.peak`, every `pids.events` key,
and `cpu.stat` directly from the live ControlGroup.  A clean result requires
`memory.swap.current=0`, `memory.events[max]=memory.events[oom]=`
`memory.events[oom_kill]=memory.events[oom_group_kill]=0`,
`pids.events[max]=0`, and `pids.peak<=32`.  `cpu.stat[usage_usec]` is the
child-inclusive unit CPU diagnostic; worker `process_time_ns` remains explicitly
main-process-only.  The supervisor then sends `SIGCONT`.  Clean termination must
become `active/exited` with `Result=success`, `ExecMainCode=exited`,
`ExecMainStatus=0`, and `MainPID=0`.  At this pre-stop point retained systemd
`MemoryPeak` must equal the live barrier `memory.peak`; a separately named final
post-`ExecStopPost`, pre-unload systemd peak is recorded later and may be larger.
Post-exit cgroup files, `TasksCurrent`, and `MemoryCurrent` are not required.

Each unit configures repository-owned `ExecStopPost` helper
`scripts/external_baselines/gcapeps_finite_memory_systemd_snapshot.py`, schema
`error_coupling_simulator.external.gcapeps_finite_memory.systemd_failure_snapshot.v1`.
For non-success `$SERVICE_RESULT`, the helper uses its own `/proc/self/cgroup`
to create with `O_CREAT|O_EXCL|O_NOFOLLOW` mode 0644 the absolute
`/run/gcapeps-fm-<launch_id>/failure_snapshot.json`.  It records service/exit
fields and live memory current/peak/swap/events, pids current/peak/events, and
`cpu.stat` before the failed cgroup disappears.  The file must be at most
1048576 bytes and canonical under its schema.  The helper fsyncs both file and
runtime-directory fd, then sends uncatchable `SIGSTOP` to itself before exit.
A pre-existing file, wrong owner/inode/mode/link count, missing stopped
`ControlPID`, or helper failure is invalid.  Within a 10-second monotonic helper
barrier deadline (strictly inside `TimeoutStopSec=15s`), the supervisor opens
the snapshot with `O_NOFOLLOW`, verifies and hashes it, copies those exact bytes
into the sealed `failure_snapshot.copy` inode, fsyncs that copy, and binds both
identities.  It then sends `SIGCONT`, requires the helper to exit cleanly, and
requires systemd to remove the non-preserved runtime directory.  On success the
helper is a no-op and the copy remains empty.
This is supervisor infrastructure, not candidate output or a performance
sample.  A launch failure before any unit exists instead records explicit null
cgroup fields.

Trusted manager/supervisor facts are classified before child bytes.  A start
timeout is a supervisor censor only if neither the self-stop barrier nor
`SIGCONT` was reached; a timeout after either point is a lifecycle
`invalid_control`.  Registered external censors are limited to an absolute-
deadline kill with recorded initiator, OOM/oom-kill, nonzero
`memory.events[max]`, nonzero `pids.events[max]`, or a launch-resource event.
A pre-unit launch-resource event is exactly supervisor `OSError.errno` `EAGAIN`
or `ENOMEM`; after a unit exists it is exactly systemd `Result=resources` with
a valid failure snapshot.  Permission, executable, path, D-Bus identity,
unit-name collision, configuration, namespace, or property errors are invalid,
not censors.

For a registered external censor, absent/truncated stdout is retained as opaque
bounded bytes rather than parsed as a child claim.  The fstat/file caps still
apply; exactly two frames, when present, must be canonical, and any extra byte
is invalid.  Only a clean released exit-zero unit may produce a completed result
or finite worker censor.  Malformed/nonfinite/schema-invalid clean frames are
invalid.  An early PASS is overridden by any later external/resource/lifecycle
fact.  Unexpected exit code, signal, or core dump is invalid; `LimitCORE=0`
prevents evaluator state from entering systemd-coredump.  Property/inode drift,
snapshot failure, or publication/hash failure is also invalid.

The child-byte disposition is provisional until a bounded cleanup phase
finishes.  After capturing all live/failure evidence, the supervisor starts a
30-second monotonic cleanup deadline.  It stops a successful retained unit
(running the success no-op `ExecStopPost`) or stops/reset-failed a failed unit
only after copying its snapshot.  Before unload it records the final retained
systemd `MemoryPeak` including any helper.  It then requires
`LoadState=not-found`.  For a valid launch it atomically no-replace-renames the
sealed spool directory into `<run_output_abs>/raw_spools/<launch_id>`, fsyncs
source and destination parents, reopens every quarantined inode, and proves the
outside spool parent exact-set empty.  Thus no later child can see a prior raw
spool.  Cleanup, unload, or quarantine failure changes the final kind to
`invalid_control`; after the finite deadline an invalid terminal is still
published with the failed facts, no name is reused, and no later science child
may start.

Only after this cleanup/quarantine decision does the supervisor publish the
canonical final envelope under
`error_coupling_simulator.external.gcapeps_finite_memory.node_terminal.v1`, with
`terminal_kind` exactly one of `completed_result`, `worker_censor`,
`supervisor_censor`, or `invalid_control`.  A supervisor censor has null
core/trailer objects and binds bounded raw hashes/counts, unit facts, initiator,
failure snapshot, cleanup, and quarantine identities.  Completed and worker-
censor terminals bind validated core/trailer, post-root `RUSAGE_SELF`, barrier
cgroup snapshot, exit facts, final unit peak, cleanup, and quarantine.  No
terminal envelope contains its encompassing supervisor-launch duration.

The supervisor-launch clock ends immediately after final-envelope publication;
for a valid launch this is necessarily after unit unload and raw quarantine.
Only afterward the runner atomically publishes a `launch_receipt` under
`error_coupling_simulator.external.gcapeps_finite_memory.launch_receipt.v1`,
binding the envelope complete-file SHA-256, final terminal kind, cleanup/
quarantine facts, and `supervisor_launch_wall_ns`.  Receipt publication is
outside that span.  A missing/failed receipt publication is a root-level invalid
control and cannot be repaired by the earlier envelope; the calibration or
held-out parent report binds the receipt's complete-file SHA.

`validation_and_evidence_materialization` is absent from a performance payload;
it is never represented by a zero-duration placeholder.  Dense-reference and
terminal-comparator processes have independent roots and never appear as
children of either candidate tree.

Named plain substeps are single-site absorption and native two-site split.
Named GC substeps are frame composition, signed pullback, route planning, exact
PEPO lowering, construction validation, every native compression split,
compression validation, and candidate commit.  All validators, copies, route
construction, and commits actually executed by the candidate algorithm remain
inside `candidate_algorithm_case_e2e`; no implementation overhead is removed
because it is inconvenient.

The primary efficiency numerator/denominator is
`candidate_algorithm_case_e2e`, which includes candidate initialization and
every real algorithm update/validator but excludes evidence-only shadows,
dense reference, candidate vector materialization, physical transcript lift,
cross-artifact fidelity, entropy/BLP metrics, and serialization.  A performance
worker does not execute any excluded evidence work.  An evidence worker records
exactly its first canonical no-shadow trajectory in
`candidate_algorithm_case_e2e`; only that branch supplies base algorithm
timing, bond, committed-memory, and `state_update_only` fields.  After its
scalar, ledger, transcript, and final-carrier-hash fields are frozen in memory,
the complete carrier is released.

`validation_and_evidence_materialization` begins before initialization of the
second trajectory and contains the entire `instrumented_replay_total`: repeated
candidate initialization, every frame/tableau/PEPS update, validator and
commit, every uncapped shadow, every checkpoint contraction/literal lift,
candidate-only diagnostic, final-carrier-hash comparison, and auxiliary
release.  No part of that replay may enter `candidate_algorithm_case_e2e`,
`state_update_only`, or an unattributed gap.  Its arrays are the raw scientific
candidate artifacts and its frame-aware final-carrier hash must equal the
no-shadow hash.  A mismatch invalidates evidence rather than changing timing
ownership.  The singleton `evidence_worker_total` and `R_evidence` include both
complete trajectories and serialization.  Performance workers execute only
the no-shadow algorithm and never emit `instrumented_replay_total`.

`state_update_only` is a derived sum over the noncontiguous physical-operation
spans; it is not emitted as a fictitious overlapping interval.  Mandatory
reported scopes are:

- `state_update_only`;
- `evidence_worker_total`;
- `performance_worker_total`;
- `dense_reference_worker_total` and `terminal_comparator_total` in their own
  process payloads;
- supervisor launch wall around the complete fresh process;
- `case_workflow_supervisor_wall_ns`;
- each named sub-step above.

The supervisor launch clock is a distinct process root.  It begins immediately
before the fresh-unit absence check and ends only after live/failure telemetry,
bounded cleanup, unload decision, raw-spool quarantine decision, and final
terminal-envelope publication.  A valid launch necessarily has confirmed
unload and quarantine before that envelope.  It therefore includes process
creation, interpreter/import, worker execution, core serialization, untimed
trailer/write, exit, telemetry query, cleanup, quarantine, and publication.  It is not the
parent of worker CPU spans and is never reconciled as though it were.  It is
known only after the final envelope, is stored in the subsequent launch receipt rather than
the terminal envelope, and excludes that receipt's own publication.

The outer `case_workflow_supervisor_wall_ns` begins immediately before the dense
unit's absence check.  A complete cell ends immediately after the terminal
comparator launch receipt is atomically published, but before case-summary
encoding/publication.  It therefore covers the strictly
serial dense-reference, all plain/GC evidence, discarded/measured performance,
SDIM, and terminal-comparator launches, including any dense ensemble work.  For
a stopped cell it ends after the last launched node's launch receipt is
published and every required skip disposition is recorded.  Any
case-summary publisher duration is external and separately reported.
The workflow value is absolute and has no GC/plain ratio because it contains
both lanes.  Calibration and held-out workflows use separate roots and
aggregates; calibration time can never enter a held-out case total.


There is no fabricated standalone “SVD time” when the library exposes only an
atomic two-site split; that complete split is timed and bound to its ledger
row.

Each lane/cell has one evidence worker per input trajectory, one discarded
fresh-process warmup for the primary trajectory, and three measured
fresh-process primary-trajectory workers.  Warmup order is exactly `plain,gc`.
The six measured launches are exactly
`plain[0],gc[0],gc[1],plain[1],plain[2],gc[2]`.  Workers run serially on one
frozen physical core, with the Section-5 child environment, identical affinity,
and no concurrent benchmark worker.

The performance aggregation population key is exactly
`(case_id,lane,trajectory_id=1,scope,round_index,operation_index,step_index,kind)`.
For every key, retain raw wall/CPU values and compute median, unscaled
`MAD=median(abs(x-median(x)))`, minimum, and maximum across exactly measured
sample indices `0,1,2`; values are never pooled across round, operation, step, or
kind.  `state_update_only` is first summed within each worker and only then
aggregated across its three worker samples.  Evidence, dense, SDIM, comparator,
and case-workflow spans are single-run raw values and never receive fabricated
median/MAD/min/max fields.  Each final supervisor envelope, not the child core,
carries the precisely scoped post-root/pre-trailer `RUSAGE_SELF.ru_maxrss` and
the live pre-release cgroup snapshot, retained post-exit systemd `MemoryPeak`,
and event fields.  Each `R_launch` sample is read only from its launch receipt.
The primary input is trajectory 1.  Its four
named ratios, all in the direction `ratio_gc_over_plain`, are

\[
R_{T,\rm wall}=\frac{\operatorname{median}(T^{\rm algo,wall}_{\rm GC})}
 {\operatorname{median}(T^{\rm algo,wall}_{\rm plain})},\qquad
R_{T,\rm cpu}=\frac{\operatorname{median}(T^{\rm algo,cpu}_{\rm GC})}
 {\operatorname{median}(T^{\rm algo,cpu}_{\rm plain})},
\]

\[
R_{\rm launch}=\frac{\operatorname{median}(T^{\rm measured\ launch}_{\rm GC})}
 {\operatorname{median}(T^{\rm measured\ launch}_{\rm plain})},\qquad
R_{\rm evidence}=\frac{T^{\rm evidence\ worker}_{\rm GC}}
 {T^{\rm evidence\ worker}_{\rm plain}}.
\]

Here `R_{T,cpu}` is explicitly the main-worker-process
`time.process_time_ns()` ratio.  The barrier `cpu.stat[usage_usec]` for the
complete child cgroup is reported separately for every launch as a
child-inclusive diagnostic and is never mislabeled as that process-CPU ratio.

The first three ratios require exactly three completed measured performance
workers in each lane; no subset, timeout replacement, or warmup substitution is
allowed.  All three final-carrier hashes per lane must also equal their matching
trajectory-1 evidence no-shadow hash.  `R_evidence` uses the completed trajectory-1 evidence-worker wall
totals; trajectory-2 evidence totals and their same-direction ratio are
descriptive.  If any required sample is censored, missing, nonfinite, or
zero/negative, the affected ratio and classification band are `UNAVAILABLE`,
while every completed row and censor reason is retained.  Only
`R_{T,wall}` receives the Section-2 descriptive bands.

No `max(1,duration)` or other fabricated floor is permitted.  A warmup is not
described as warming a later fresh process; it is only a discarded first-launch
control.

## 11. SDIM Clifford-frame corroboration

SDIM 1.3.3 runs in a separate declared environment as a qubit-only, frame-only
corroboration lane.  Its bootstrap declaration is
`external/forks/quimb-gcapeps/environment-gcapeps-sdim.yml`, SHA-256
`64236e0cb6dc87a90f116dbebb8ee8a73882dc41d00619af8b7d3ccc35de3431`.
That YAML is a bootstrap, not a transitive lock or wheel-byte attestation.
After final parent/fork implementation identities and the bootstrap environment
are frozen, but before the calibration wall root and every Stage-A child, owner
`scripts/external_baselines/collect_gcapeps_finite_memory_sdim_inventory.py`
is launched exactly once with the evidence resource class.  The collector emits
its `.sdim_inventory.v1` core only through the standard two-frame stdout
protocol and self-stop barrier; it never opens the run-output tree.  After
cleanup/quarantine, its final supervisor envelope is atomically published at

```text
outputs/external_baselines/gcapeps_finite_memory_bond32/sdim_inventory.json
```

The file's top-level schema is `.node_terminal.v1`; its nested role-specific
core schema is `.sdim_inventory.v1`.  It is the collector's one ordinary final
envelope, not a second re-encoded core artifact.  The subsequent launch receipt
binds it.  Worker/launch duration is bootstrap engineering telemetry and enters
neither the 12-hour wall nor any candidate, case-workflow, or efficiency ratio.
The collector receives the preflight-receipt identity but cannot receive or
record its own envelope or launch-receipt complete-file SHA.

Its `inventory_state` records the YAML path/hash; Python executable
realpath/version/executable SHA-256; installed distributions sorted by the
lowercase name after replacing each maximal `[-_.]+` run by `-`, with duplicate
normalized names rejected; original/normalized name, version, distribution-info
realpath, and `direct_url.json` SHA-256 or null; Stim/SDIM/Quimb origins and
origin-file hashes; and editable Quimb commit/tree/clean status.
`inventory_state_sha256` hashes only canonical `inventory_state` bytes.  The
top-level envelope has `result_projection_sha256` and forbids any digest field
naming its own complete published bytes.  After no-replace rename and parent
fsync, the supervisor reopens it and externally computes the complete-file SHA.

Every subsequent calibration child binds the top-level/core schemas, state hash,
projection hash, envelope complete-file SHA, and launch-receipt complete-file
SHA.  Every SDIM launch additionally
reconstructs live `inventory_state` and requires byte-identical canonical state
before replay.  The calibration report and amendment bind all named identities;
every held-out launch rehashes the same file.  The inventory is never regenerated
between calibration and held-out execution; regeneration requires a fresh
calibration.  It is the declared installed state promised by the bootstrap, not
a claim that the YAML is a lock.  Missing/drifting state fails closed.  The SDIM
computation worker does not import Quimb/GCAPEPS; inventory inspection does not
make either a computational dependency.

The computation owner is
`scripts/external_baselines/gcapeps_finite_memory_sdim_worker.py`; its
role-specific core schema is `.sdim_frame_control.v1`; its top-level published
artifact remains `.node_terminal.v1`.
For each row it records exact cell id, input id, preparation-transcript hash,
round prefix, collision locator, physical Pauli, `sdim_sign`, `sdim_body`,
`stim_sign`, `stim_body`, and `sdim_equals_stim`.  In the same isolated worker it
computes the SDIM replay and a separately constructed Stim replay without
reading any GC evidence or candidate output; internal equality must pass before
publication.

Before any candidate/corroboration worker, the neutral fixture alone generates
the expected ordered sequence `sdim_pullback_requests` from the frozen input
preparations, event mask, and physical evolution ledger; it consumes no GC,
SDIM, or Stim output.  The exact join key is the canonical projection

```text
K = (run_partition, case_id, input_id,
     input_preparation_transcript_sha256,
     shared_evolution_transcript_sha256, round_prefix,
     collision_ordinal, round_index, site_index, axis_index,
     physical_pauli_body)
```

`round_prefix` and `round_index` are one-based.  `collision_ordinal`,
`site_index`, and `axis_index` are zero-based, with axis `0,1,2 = X,Y,Z`.
`physical_pauli_body` is the complete q0-to-last ASCII `IXYZ` word of length
`2*w`.  `case_id` is the exact fixture-owned held-out cell id or calibration
Stage-D pair/seed id.  No extra/coercible key field is legal.  Requests are
sorted lexicographically by this tuple and duplicate keys are forbidden.

Let `E` be that fixture sequence; `S` and `T` the SDIM and independent-Stim row
sequences; and `G_raw` the concatenation, without deduplication, of both GC
evidence row sequences.  Each source first rejects duplicate keys locally, and
the comparator rejects duplicates across the two GC artifacts.  Only then is
`G=sorted(G_raw)` formed.  Without reading GC evidence, the SDIM worker requires
`E == S == T` as exact sequences.  The terminal comparator independently reads
the neutral fixture and requires

```text
E == S == T == G
```

with equal cardinality and exactly one occurrence of every key before comparing
the signed `(sign,body)` value at each key.  `sdim_equals_stim=true` and an
inner-join intersection are not coverage evidence.  Missing, extra, duplicate,
reordered, cross-input, wrong-preparation, wrong-prefix, or wrong-collision rows
are hard invalid controls.  An empty sequence is legal only when fixture-owned
`E` is empty.  The comparator alone owns the four-set and signed-value verdict.

For every calibration Stage-D seed and held-out cell, both inputs, every round prefix, and every
actual collision Pauli word, SDIM independently replays the accumulated
Clifford.  Input 1 has identity preparation; input 2 has the central-system X in
its preparation frame; both then replay the identical shared physical-round
ledger.  Fixture/result keys include input id and preparation-transcript hash.
The canonical pullback is

\[
P_{\rm res}=C^\dagger P_{\rm phys}C=sP',
\]

where site/Pauli order is `q0..q(2*w-1)`, `P'` is ASCII `IXYZ`, and
`s in {-1,+1}`; a `+/-i` phase is rejected.  Only after exact four-set key
coverage passes, require for every key the three computed signed values to be
equal:

```text
SDIM pullback == independently replayed worker-Stim pullback
              == GC evidence artifact pulled_back_pauli
```

The GC evidence value is only the value under test and is never supplied to the
SDIM or independent Stim replay as an oracle.  A sign, support, target, order,
input-preparation, or round-prefix mismatch is a hard control failure.

The SDIM lane constructs no PEPS, residual state, complete state vector,
reduced density matrix, fidelity, entropy, or BLP value.  It is neither ground
truth nor part of any timing ratio.  It does not establish non-Clifford,
qutrit/prime-\(d\), composite-\(d\), leakage, or live SDIM-carrier correctness.

## 12. Resource and censoring envelope

Processes are serial.  Performance workers have a 12-GiB memory cap and
`TimeoutStartSec=600s`.  Evidence, cap-probe, reference, comparator, inventory,
and SDIM workers have a 24-GiB cap and `TimeoutStartSec=1800s`; all oneshot units
have `RuntimeMaxSec=infinity`.  Swap is forbidden.  A trusted external
OOM/timeout/deadline/launch terminal or clean finite worker censor is retained
as censored and never silently removed from a ratio.  A forbidden nonfinite
token, clean-exit frame/schema failure, unexpected crash, or protocol/telemetry
failure is instead invalid under the Section-10 precedence.

GC exact-lowering guards must admit a single post-cap rank-two update
(`bond 32 -> pre-compression bond at most 64`) while rejecting allocations
outside the declared process envelope.  The concrete element guards are
derived from shape arithmetic and committed in the implementation-phase diff;
they may not be fitted from target completion behavior.

## 13. Required implementation and corruption gates

Before calibration:

1. the existing exact-tree construction suite, native truncation suite, dense
   checks, and full fork suite pass;
2. a three-site \(0\!-\!1\!-\!2\) operator-basis reconstruction with a common
   nonidentity factor on routing vertex 1 passes against `to_dense()`;
3. a four-site companion covers a common nonidentity factor outside the
   routing tree;
4. an asymmetric gauge fixture names and enforces the \((i,\alpha)\),
   \(\alpha\)-fast fusion convention;
5. compression is atomic: any failed shadow, SVD, ledger validation, or
   resource check leaves the original carrier, physical gate history,
   construction epoch, and PEPO/refactor product maps unchanged;
6. exact-small untruncated
   `exact_tree_then_native_compress(max_bond=None)` equals existing
   `exact_tree`, a direct dense Pauli rotation, and all basis columns;
7. synthetic identity compression uses raw `_psi.gate_simple_`, strips
   `contract` and `propagate_tags`, never touches `candidate.psi` or the public
   physical-gate path, follows the exact routed-edge order, keeps every final
   graph bond within the cap, and on success increments the construction epoch
   and resets both product maps;
8. a second compressed update begins with epoch-local PEPO/refactor products
   equal to one rather than inheriting the historical rank product;
9. a forced-small cap produces a positive tail and an independently computed
   complete-vector error;
10. a bond-32 synthetic fixture proves `full_bond_dimension>32`,
    `kept_bond_dimension=32`, cause exactly `max_bond`, and positive discarded weight;
11. construction rows cannot contain compression values, compression rows
    cannot change PEPO/refactor factors, and any lifetime product is labelled
    counterfactual rather than an actual resource bound;
12. a refactor factor forged into the PEPO-only routed-rank product is
    rejected;
13. changing the fusion layout, routed-edge order, spectrum, cause, cap,
    epoch, or shadow pre-state is rejected;
14. the literal defective McCloskey Eq. (8), opposite Pauli-rotation sign,
    sum-instead-of-product partial-SWAP, removed global-phase firewall,
    different event masks, candidate restart between rounds, memory reset,
    axis-family permutation, averaging pathwise BLP distances, or adding an
    interaction at \(p_{\rm event}=0\) triggers its intended control;
15. corrupting the Stim frame, signed pullback, Clifford order, transcript
    rebuilt tableau, or literal physical lift changes the exact-small result;
    the deterministic projective-unitary control accepts only tableau global
    phase and rejects missing pivots, fitted/reused phases, or gross mismatch;
16. for both inputs, corrupting SDIM or independently replayed Stim sign,
    support, target, Pauli/site order, preparation frame, or round prefix breaks
    the equality with the GC evidence pullback and fails.  Dropping, adding,
    duplicating, reordering, or cross-input substituting a key in any of
    fixture/SDIM/Stim/GC makes the exact four-set sequence gate fail first;
17. `complex64`, wrong vector shape/dtype, zero/nonfinite norm, excessive
    `vdot` imaginary residual, silent stored-vector normalization, phase fitting,
    coordinate permutation, nonzero cutoff, hidden cap, and `PYTHONPATH` are
    rejected before any division or metric;
18. no-shadow and instrumented candidates must have byte-identical canonical
    final-carrier hashes; all three measured performance hashes must equal them.
    Tests independently corrupt raw `_psi` tensors, a present/missing gauge map,
    live frame, preparation/evolution transcript hash, array order/length prefix,
    and internal index names; all semantic corruptions fail while index renaming
    is inert;
19. timing tests require exact duration and parent/child integer equalities and
    reject missing leaves, overlaps, double counting, bad roots, negative
    durations, altered population keys/order, pre-aggregation operation pooling,
    supervisor/worker substitution, non-ascending within-layer gate order,
    wrong one-/zero-based indices, or a non-null aggregate sentinel.  A
    zero-duration leaf is accepted, but a nonpositive ratio denominator or
    complete worker/root total fails.  An evidence tree must contain exactly one
    `instrumented_replay_total` under
    `validation_and_evidence_materialization`; moving a repeated update, shadow,
    or checkpoint materialization into `candidate_algorithm_case_e2e`, omitting
    it, or leaving it unattributed fails;
20. the independent dense reference rejects shared candidate gate helpers or
    imports and pins the q0-MSB partial-trace convention; the terminal
    comparator independently rejects Quimb/Stim/SDIM/GC/ECS imports, reads only
    the neutral fixture and frozen dense/candidate/SDIM artifacts, and rejects mismatched child
    identities;
21. fixture controls pin mask prefix stability, nested probabilities, structural
    endpoints, 32 equal weights without deduplication, and
    ensemble-before-distance ordering; held-out controls additionally pin the
    five-integer tuple, exact deduplication, lexicographic order, cardinality,
    ordered `slice_membership`, and ensemble flag;
22. plain workers reject GC imports; evidence workers reject dense-reference
    and comparator imports and input fields.  `CALIBRATION` inputs forbid every
    amendment identity and require stage/attempt/theory identities; a
    calibration performance role or container is forbidden.  `HELDOUT`
    inputs require the clean amendment commit/tree/hash and exact cell/list;
    the held-out stdin entry is byte/hash-identical to that tracked amendment,
    while calibration containers reject it.
    Candidate transient units verify `InaccessiblePaths` for the exact output
    root, and a corruption child opening the known dense absolute path must be
    denied.  Performance workers additionally reject dense/comparator paths,
    hashes, values, locators, materialization, uncapped shadows, fidelity,
    entropy, and BLP paths and omit the evidence span entirely;
23. every case binds parent/fork commits, source/review hashes, corpus manifest,
    fixture/mask/gate-ledger hashes, main environment lock, SDIM bootstrap and
    runtime inventory, import origins, and `result_projection_sha256`; the
    supervisor/parent report binds every nonterminal complete-file SHA-256, and
    the tracked result note externally binds the terminal held-out report SHA.
    Tests pin `ensure_ascii=True`, `allow_nan=False`, sorted compact JSON, no
    newline, exact two-frame u64be framing/core hash, and the exact frame-image
    field encoding; noncanonical bytes, nonfinite tokens, bad length/order, or a
    self-referential complete-file hash are rejected.  `ndarray-v1` corruptions
    reject missing/extra keys, boolean dimensions, wrong endian/dtype/rank/shape,
    order/nbytes, noncanonical Base64 alphabet/padding/whitespace, decoded-length
    or SHA mismatch, nonfinite decoded values, hash-only artifacts, and one-bit
    payload changes.  A finite c128/f64 round trip preserves exact C-order bytes;
24. every result validates against the registered schemas and the metric and
    value-provenance owners in `docs/METRICS.md` and
    `docs/NUMERICAL_PROVENANCE.md`;
25. zero-based physical-round encoding or using a different round value for
    parity and the mask payload changes the fixture hash and fails;
26. promoted/non-`float64` gauges, non-C-contiguous gauges, negative or
    nonfinite gauges, ambiguous edge keys, and an unprocessed selected zero gauge
    fail.  Exact-zero inner/outer, strictly-positive near-zero, unrelated-gauge,
    `gauge_simple_insert(...remove=False,smudge=0,power=1)`, key deletion,
    fresh-gauge, and `smudge_actually_used` fixtures pin the native rule;
27. an independent small vector/matrix known-answer suite covers allowed tiny
    negative-eigenvalue clipping; gross negativity, non-Hermiticity, bad trace,
    eigenpair/reconstruction failures; zero/nonfinite vectors; and hand-computed
    `F`, `D_pure`, trace distance, `d_rel`, `d_norm`, raw/normalized `d2`/`dinf`,
    raw norm errors, and
    `S1/S2` errors.  A zero/nonfinite fidelity denominator, negative/nonfinite
    `F_raw`, or `F_raw-1>1e-12` fails before clipping;
28. summing sparse-checkpoint increments or naming them candidate BLP error
    fails; only per-checkpoint fixed-mask trace-distance error is accepted;
29. duplicate same-category roots are deduplicated, while cross-category aliases,
    Python-overhead inclusion, wrong `RUSAGE_SELF` sample point/KiB conversion,
    a partial shadow with uncounted frame/history/ledger, a nonzero base total
    after no-shadow release, or noncanonical frame/ledger sizing fails;
30. construction tests bind `contraction_optimize="greedy"` and
    `equilibrate_every=None` at the carrier, and reject an unsupported
    `state_vector(..., optimize=...)` call;
31. the low-level gate-option whitelist rejects unknown keys, strips inherited
    `contract`/`propagate_tags`, pins explicit `contract="reduce-split"`,
    `method="svd"`, cutoff/cap/renorm/absorb/smudge/power values, and proves a
    fresh empty `info` mapping per split; a dead `split_method` key fails;
32. the `p_event=0` exact control rejects any true event bit, active collision,
    per-round (S_1) or (S_2) above `1e-12`, trace distance outside
    `1 +/- 1e-12`, or named increment above `1e-10`;
33. logical-memory corruption tests force ownership-transition peaks for
    uncommitted candidates, the complete instrumented branch, shadows,
    vector/literal-lift arrays, and evidence-only ledgers; pin sequential base
    release; reject branch evasion and cross-category aliases; and keep
    dense/comparator bytes outside candidate-lane totals;
34. the first three performance-derived ratios reject anything other than three
    of three completed measured workers per lane; `R_evidence` is a singleton
    ratio.  Tests also reject altered warmup/measured order, population key,
    unscaled MAD, inverted GC/plain direction, operation pooling, or a censored
    sample silently dropped;
35. calibration controls pin displayed ordinal-index selection, launch-counter timing,
    attempt-100/101 boundary, compute-deadline versus late-publication classes,
    canonical-parser/nonfinite precedence, and incomplete-versus-invalid
    dispositions.  Dedicated plain/GC cap-probe owner/schema tests pin the
    immediate-pre-split shadow, full-current-operation commit-before-stop rule,
    first-positive locator, no-cap completion, evidence resource class, and
    probe-positive/full-negative failure.  Controls also pin the external
    calibration-report/publication-receipt hashes and amendment path/schema/content, including
    independent-rereview/theory identities; every held-out child binds the clean
    external amendment commit/tree and exact file hash;
36. the SDIM control pins the unique pre-wall collector exception, forbids its
    self-binding or regeneration, and binds bootstrap, canonical installed state,
    node/core schemas, state/projection/envelope/receipt hashes, normalized-name
    duplicate rejection, both inputs, prefixes, collision locators, independent
    SDIM/Stim values, and the
    comparator-owned exact `E == S == T == G` sequence/value gate.  It rejects
    treating YAML as a lock, supplying GC to either replay, and every
    missing/extra/duplicate/reordered key;
37. performance, evidence, dense-reference, comparator, SDIM, and supervisor
    import/process firewalls are exercised from fresh distinct-DynamicUser
    system services.  The runner is non-dumpable; corruption children attack
    the bound runner `/proc` root/fd/mem, ptrace, `process_vm_readv`, run-output
    root, and known quarantined prior-spool inode and must be denied.  Launches
    use read-only repo/home views, `PrivateUsers`, absolute file-backed paths, a
    supervisor-owned 0700 spool with exact current-only set, inode-sealed 0600
    stdin/stdout/stderr, no auxiliary FDs, and output-root quarantine before the
    next child.  Tests pin the exact partition-by-role stdin entry sequence,
    external source SHA alignment, write/fsync/reopen/reparse gates, whole-
    container hash binding, and exclusive comparator access to cross-role
    numerical bytes.  A child-created extra spool entry, same-host-uid service,
    retained evaluator fd/bytes, or forbidden SDIM/candidate input fails.  Any
    reference/comparator contribution to a candidate timing or memory ratio is
    rejected;
38. held-out corruption tests exercise every invalid-control, scientific-censor,
    performance-only-censor, all-later-node skip, next-cell continue/sweep stop,
    SDIM-after-performance, and partial-workflow branch, proving that only a
    performance-only censor permits later current-cell nodes;
39. performance schema rejects evidence-only vector/spectrum/tail/event fields,
    evidence schema requires raw candidate vectors/gates, candidate-only guards,
    spectra/tails/events/resources and signed pullbacks but rejects every
    reference/cross metric, while comparator schema alone requires the complete
    cross-artifact metric/error/verdict family and exact SDIM key/value gate; and
40. the complete child environment, CPU selection/provenance, thread limits,
    CUDA/PYTHONPATH policy, exact `CPUAffinity`, DynamicUser/sandbox properties,
    `LimitCORE=0`, per-role core/trailer/stdin/stderr/snapshot caps,
    `LimitFSIZE`, explicit 600/1800-second
    `TimeoutStartSec`, inert `RuntimeMaxSec=infinity`, failure mode, and absolute
    watchdog are asserted in fresh processes.  Tests pin manager preflight and
    no fallback; never-reused units; no wait/pipe/collect; raw binary capture;
    pre-allocation fstat/checked-length equality and oversize/huge-prefix
    rejection; self-stop/SIGCONT and stopped-task proof; memory/pids/cpu cgroup
    snapshot and exact event predicates; barrier-live descendants; worker versus
    cgroup CPU labels; pre-stop and final systemd peaks; exact 0755 non-preserved
    RuntimeDirectory and absolute failure snapshot; success/failure
    `ExecStopPost`, failure-helper file/dir fsync, stopped `ControlPID`, 10-second
    copy barrier, SIGCONT, and directory deletion; start-timeout phase and
    exact launch-resource allowlist; completed/worker-censor/supervisor-censor/
    invalid branches; early-PASS override; bounded cleanup/unload/raw-quarantine
    then final-envelope then launch-receipt endpoints; calibration publication
    receipt; and complete workflow endpoints.  Missing snapshot, stale name,
    cleanup/quarantine failure, or receipt self-timing fails.

## 14. Decision table and allowed claims

| condition | result class |
|---|---|
| calibration has timeout/OOM/launch/resource censor, a schema-valid internal-nonfinite censor, child/required-work deadline interruption, or needs attempt 101 | `CALIBRATION_INCOMPLETE_CENSORED`; heldout forbidden |
| calibration has algebra/sign/schema/provenance/control failure, emits a noncanonical/nonfinite token, or has otherwise eligible compute whose receipt records report commit after the deadline | `CALIBRATION_INVALID_CONTROL_FAILURE`; heldout forbidden |
| the complete ordered grid finishes without censor/control failure and no pair qualifies | `NO_ELIGIBLE_BOND32_NONMARKOVIAN_CELL`; heldout forbidden |
| held-out identity/algebra/sign/schema/provenance/hash/p=0/SDIM equality control fails | `HELDOUT_INVALID_CONTROL_FAILURE`; stop sweep; all scientific/timing classifications forbidden |
| held-out dense/evidence/SDIM/comparator worker is censored | affected cell `INCOMPLETE_CENSORED`; every later current-cell node skipped; sweep `HELDOUT_INCOMPLETE_CENSORED`; continue next cell only |
| only a performance worker or performance timing reconciliation is censored | independent scientific metrics retained; affected ratio/band `UNAVAILABLE`; every later node continues |
| held-out workflow stops before its graph completes | partial workflow duration retained but excluded from completed-workflow aggregates |
| fixed-`CARRIER` dense BLP increment is positive | `BLP_WITNESSED_FIXED_MASK` for that pair and unitary schedule only |
| fixed-`CARRIER` dense BLP has no positive increment | `NO_WITNESS_FIXED_MASK_FOR_REGISTERED_PAIR` |
| probability-slice 32-path dense BLP increment is positive | `BLP_WITNESSED_FINITE_32_MASK_ENSEMBLE` only |
| probability-slice ensemble has no positive increment | `NO_WITNESS_FINITE_32_MASK_ENSEMBLE_FOR_REGISTERED_PAIR` |
| \(p_{\rm event}=0\) violates any structural-zero, entropy, unit-distance, or no-increment gate | `HELDOUT_INVALID_CONTROL_FAILURE`; no held-out scientific verdict |
| any of four held-out stress evidence trajectories lacks a positive cap event | head-to-head truncation verdict ineligible; retain descriptive data |
| all four are eligible and \(\Delta F>10^{-10}\) | \(H_F\) supported on the bounded target |
| all four are eligible and \(|\Delta F|\le10^{-10}\) | \(H_F\) tie/inconclusive |
| all four are eligible and \(\Delta F<-10^{-10}\) | \(H_F\) falsified on the bounded target |
| stress-cell trajectory-1 exact terminal entropy exceeds round-1 entropy by \(>10^{-10}\) | \(H_E\) supported; no monotonic-step claim |
| the stress-cell inequality does not hold | \(H_E\) falsified |
| exactly three of three primary performance samples complete in each lane | report all ratios; classify only primary wall ratio with the frozen bands |
| any required ratio scope is censored/missing/nonpositive | affected ratio and band `UNAVAILABLE`; retain rows and reason; zero-duration leaves remain legal |

Allowed conclusions name the exact width/round/axis-family/probability cell,
bond cap, implementation commits, fidelity metric, witness object, and timing
scope.

Forbidden conclusions include:

- non-Markovianity from persistent memory, entanglement, bond, or a candidate
  revival alone;
- Markovianity from one registered pair with no revival;
- interpreting the finite 32-mask ensemble as an infinite Bernoulli process or
  calibrated device probability law;
- monotonic entanglement as a general property of non-Markovian noise;
- equal semantic meaning of ordinary physical PEPS bond and GC residual bond;
- local discarded weight as a generic whole-state/observable/Record bound;
- generic PEPS contraction efficiency, generic small bond, asymptotic scaling,
  or universal GCAPEPS speedup;
- measurement/reset/trajectory-probability/Record/LER correctness;
- qutrit, prime-\(d\), composite-\(d\), SDIM live-backend, or leakage
  correctness; and
- release acceptance of GCAPEPS as a canonical ECS Carrier.

