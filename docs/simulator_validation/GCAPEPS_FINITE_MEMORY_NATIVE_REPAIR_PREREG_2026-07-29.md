# GCAPEPS finite-memory native-path repair — preregistration

Status: **FROZEN BEFORE NATIVE FINITE-MEMORY TARGET EXECUTION, 2026-07-29.**

Grounding:
`GCAPEPS_FINITE_MEMORY_NATIVE_REPAIR_LITERATURE_CLOSURE_2026-07-29.md`.

This is a development-only implementation and thread-determinism regression.
It does not modify or silently satisfy the frozen formal
`GCAPEPS_FINITE_MEMORY_BOND32_PREREG_2026-07-29.md`. A formal held-out sweep
requires a separate amendment after this repair passes.

## -1. Question charter

- Decision and consequence: retire capped
  `exact_tree_then_native_compress` from the finite-memory development
  candidate and select the existing `native_simple_update` path only if it
  passes exact-small, frame,
  shadow-isolation, and thread-invariance falsifiers.
- Importance x attackability: the legacy path turns internal representation
  differences into physical differences, while the replacement can be tested
  on complete vectors in bounded fresh processes.
- Reusable objects: a 2x3 branching full-basis fixture, a nontrivial-frame
  state-action fixture, and a four-round operation-100 thread differential.
- Alternatives: uncapped exact tree construction; capped native physical-gate
  compilation; future full-environment/variational compression.
- Invariants: exact untruncated unitary action; literal Clifford lift; raw
  complete-vector and norm agreement without fitting or normalization;
  identical compiler transcript and high-level operation ledger.
- Kill condition: any failed exact identity, shadow mutation, corruption
  falsifier, or one-versus-four-thread physical-state band blocks the native
  finite-memory lane.

The already observed legacy operation-100 divergence and the existing
one-/four-thread native unit-suite passes are diagnostic inputs, not target
predictions. T3--T5 are therefore post-result engineering regressions, not
held-out tests, and have no independent-ground-truth or scientific-claim
status.

## 0. Bound identities

| Object | Identity before repair code |
|---|---|
| parent commit | `6d37d9b6753279bdfc26227ad6812f9647085031` |
| parent tree | `7f40ba760ff182ec625b164dcf6ec99a6895722b` |
| Quimb fork commit | `d90bb5ea210e666cbd7ecf8a8b7fa02390519baf` |
| Quimb fork tree | `f7cd3496c48ec69f1800d41eabcaa8d53cab3b5b` |
| finite-memory neutral fixture owner | `scripts/external_baselines/emit_gcapeps_finite_memory_fixture.py` |
| dense owner | `scripts/external_baselines/gcapeps_finite_memory_dense_reference.py` |
| current GC adapter | `scripts/external_baselines/gcapeps_finite_memory_engine.py` |
| existing native compiler/executor | fork `quimb/experimental/gcapeps/native.py` |

The implementation commit and final fork identity must be recorded after code
exists. No output from an implementation whose identity differs from the
recorded repair identity is eligible even as development evidence.

## 1. Mechanism

For

\[
|\psi\rangle=C|\phi\rangle,\qquad Q=C^\dagger PC=s\bar Q,
\]

the residual update is compiled as

\[
U_Q(\theta)=
B^\dagger V^\dagger R_Z(s\theta)VB
=e^{-i\theta Q/2}.
\]

`B` consists only of local basis gates, `V` consists only of declared
graph-edge SWAP/CNOT gates, and every borrowed dirty router is restored before
the next terminal. The frame remains Stim; Clifford operations do not enter
the residual PEPS. The finite cap is applied by the same Quimb
`CircuitPEPSSimpleUpdate` one-/two-site machinery used by the ordinary PEPS
lane.

The legacy `exact_tree_then_native_compress` path remains callable only under
an explicit diagnostic name. It must not be the default or selected
finite-memory development lane.

## 2. Metric binding

Reuse the current raw complete-state entries in `docs/METRICS.md`. Inputs
\(x,y\) must be equal-shape, finite, one-dimensional `complex128` arrays in
the registered coordinate order. No fitting, normalization, dtype cast, or
coordinate permutation is permitted. Define

\[
d_\infty^{\rm vec}=\max_j|x_j-y_j|,\qquad
d_2=\|x-y\|_2,
\]

\[
d_{\rm rel}=
\frac{2\|x-y\|_2}{\|x\|_2+\|y\|_2},\qquad
d_{\rm norm}=
\frac{2\left|\|x\|_2-\|y\|_2\right|}
{\|x\|_2+\|y\|_2},
\]

\[
F_{\rm raw}=
\frac{|\langle x|y\rangle|^2}
{\langle x|x\rangle\langle y|y\rangle}.
\]

Both norms, their sum, both masses, the fidelity denominator, the overlap,
and every reported metric must be finite; the norm sum, masses, and fidelity
denominator must be strictly positive. Any non-finite value or zero
denominator fails closed. Record

\[
\Delta_F=\max(0,F_{\rm raw}-1).
\]

If \(F_{\rm raw}<0\), is non-finite, or \(\Delta_F>10^{-12}\), the comparison
fails before clipping. Only after that guard passes set
\(F=\min(1,F_{\rm raw})\). Raw \(d_2\), \(d_\infty^{\rm vec}\), both norms,
\(F_{\rm raw}\), \(\Delta_F\), and \(F\) are retained.

For two reconstructed matrices \(A,B\), the operator diagnostic is explicitly

\[
d_\infty^{\rm mat}=\max_{i,j}|A_{ij}-B_{ij}|.
\]

It is not a vector metric and must not be substituted for the per-column
complete-vector gates.

Local singular spectra, kept dimensions, and discarded fractions are
class-(c) cause/resource diagnostics. They never substitute for complete-state
metrics and do not supply a global truncation bound.

## 3. Registered pre-code tests

### T1 — branching-tree complete operator identity

Use the 2x3 ladder

```text
0 -- 1 -- 2
|    |    |
3 -- 4 -- 5
```

with edge order
`(0,1),(1,2),(3,4),(4,5),(0,3),(1,4),(2,5)`, site order
`0,1,2,3,4,5`, word

\[
Q=-X_0Y_2Z_4,
\]

and \(\theta=\pi/7\). The deterministic route must contain a branching dirty
router and the compiler transcript must be identical across all basis
columns. With `max_bond=None`, reconstruct all 64 computational-basis columns
and compare the resulting 64x64 operator with an independently written
bitwise Pauli-rotation action.

Pass bands:

```text
operator d_inf_matrix <= 1e-12
every column d_rel <= 1e-12
every column d_norm <= 1e-12
every column 1-F <= 1e-12
every column fidelity_roundoff_correction <= 1e-12
```

### T2 — nontrivial Clifford-frame state-action identity

On the same graph, initialize residual \(|010101\rangle\). Apply the physical
frame preparation `H 0` followed by `CX 0 1`. Apply the physical Pauli
rotation

\[
P=Z_1Z_2Z_4,\qquad \theta=\pi/7.
\]

The production side uses Stim pullback plus the native residual compiler. The
independent side applies hand-written dense `H`, `CX`, and bitwise \(P\)
rotation directly in the physical coordinate. Compare the raw complete
physical vectors with the T1 per-vector bands, without fitting. The pulled
word, sign, support, route, and plan digest are retained.

### T3 — fresh-process BLAS thread invariance at the known boundary

This is a post-result regression registered from an already observed defect.
It is not held out, has no independent ground truth, and cannot support a
scientific or faithfulness claim.

Freeze the existing neutral finite-memory cell:

```text
width = 7
n_qubits = 14
rounds = 4
axis_family = 3
p_event = 3/4
seed = 2
gamma_index = 2
input_id = 2
stop_after_operation = 100
max_bond = 32
cutoff = 0
dtype = complex128
selected_gc_strategy = native_simple_update
```

Run two fresh subprocesses with all five variables
`OMP_NUM_THREADS`, `OPENBLAS_NUM_THREADS`, `MKL_NUM_THREADS`,
`NUMEXPR_NUM_THREADS`, and `BLIS_NUM_THREADS` set uniformly to 1 and 4,
respectively. Both set `CUDA_VISIBLE_DEVICES=""`, `PYTHONHASHSEED=0`, and
have no `PYTHONPATH`.

Materialize complete physical vectors immediately after high-level operations
99 and 100. For 1-thread vector \(x\) and 4-thread vector \(y\), require at
both checkpoints:

```text
d_rel <= 1e-9
d_norm <= 1e-10
1-F <= 1e-10
fidelity_roundoff_correction <= 1e-12
```

Also require exact equality of the neutral fixture hash, high-level operation
prefix, physical Pauli request, signed pulled word, native plan digest,
canonical gate transcript, route, configured cap/cutoff, and kept bond
dimensions. Do not require equality of raw carrier hashes, tensor bytes,
gauge hashes, generated index names, SVD vectors, or individual singular
values.

For report-only development diagnosis, pair each operation-99 and
operation-100 native vector with the registered complete dense development
reference and emit the same raw metrics separately for the one-thread and
four-thread children. These dense-paired rows have no acceptance band, are
not independent ground truth for T3, and must never be labelled or consumed
as faithfulness evidence.

### T4 — no-shadow versus evidence isolation

At one thread, run the same T3 prefix once with native shadow evidence
disabled and once with it enabled. The disabled run injects a throwing
shadow-builder sentinel and must report exactly

```text
shadow_builder_call_count = 0
shadow_span_count = 0
shadow_evidence_bytes = 0
```

Any sentinel invocation fails immediately. Require the final raw complete
physical vectors and norms from the disabled and enabled runs to satisfy the
T3 bands. Require the same native plan transcripts, two-site step identities,
configured cap/cutoff, and candidate kept dimensions. The disabled run must
label every unobserved cause `not_observed_without_shadow` and leave
full-spectrum, full-dimension, discarded-tail, and dimension-reduction fields
null; it must
not infer a truncation cause from the kept dimension alone. Only the enabled
evidence run may report causes from its uncapped shadow, and the T3
non-degeneracy witness is read only from that run. The enabled evidence run is
emitted as a separate `shadow_enabled` row with its call count, spans, bytes,
and timing; none of those quantities may be merged into the disabled row or
algorithm time. Evidence-only shadows must not enter the committed carrier.

### T5 — legacy fail-closed selection

The finite-memory development runner must not select
`exact_tree_then_native_compress` by default. Any explicit request to use it
must label the lane
`gcapeps_exact_tree_compress_diagnostic_only`, set
`formal_claim_eligible=false`, and remain ineligible for faithfulness or
performance classification. The old formal runner remains fail-closed rather
than silently switching strategies.

Under the exact T3 environment, fixture, checkpoints, cap, and metric
implementation, the explicit legacy diagnostic must violate at least one T3
band at operation 100. This required RED regression is bound to
`docs/simulator_validation/GCAPEPS_LEGACY_THREAD_DIVERGENCE_DIAGNOSTIC_2026-07-29.md`,
SHA-256
`275264ab2e9d32cbf3615eb5ce6a652a7a06d2116ae246a0fc2085a34b7feb81`.
The note contains historical localization values only; the committed
regression must recompute the raw metrics and cannot copy those values.

## 3a. Constraint and corruption ledger

| Invariant | Clean assertion | Deliberately broken input | Required trip |
|---|---|---|---|
| Pauli sign is retained | T1 full operator matches \(-X_0Y_2Z_4\) rotation | drop the minus sign from root angle | operator comparison fails |
| dirty router is restored | all 64 T1 columns match | omit one reverse SWAP | at least one column fails |
| uncompute order is exact | T1/T2 complete vectors match | execute terminal uncompute in forward order | operator or frame fixture fails |
| Clifford/residual bridge | T2 physical vectors match | use \(CPC^\dagger\) instead of \(C^\dagger PC\) | T2 fails |
| shadow is read-only | T4 candidates match | execute the capped candidate from the shadow object | T4 fails or ownership test trips |
| thread setting is isolated | child receipt reports exactly one uniform setting | leave one BLAS variable inherited | worker fails before evolution |
| raw norm cannot be hidden | `d_norm` is checked separately | normalize one output before comparison | corruption test fails schema/provenance or raw-norm assertion |
| metric domain is guarded | vectors, norms, denominators, overlap, and outputs are finite; denominators are positive | inject `NaN`, infinity, a zero vector, or a zero denominator | comparator fails before classification |
| fidelity clipping is ordered | record \(F_{\rm raw}\) and require \(\Delta_F\le10^{-12}\) before clipping | force \(F_{\rm raw}=1+2\times10^{-12}\) or clip before testing the excess | comparison fails closed or clipping-order mutation test trips |
| disabled shadow is absent | T4 sentinel has zero calls, spans, and bytes | invoke the sentinel or emit a disabled-run evidence span/byte | T4 fails |
| no-shadow evidence is honest | cause is `not_observed_without_shadow` and every shadow-derived field is null | with no shadow, infer a cause from kept dimension/configuration or fill any full-spectrum, full-dimension, tail, or reduction field | T4 schema/comparator fails |
| relative tail is scale invariant | the registered 33-value known answer equals \(1/33\) at all three scales | square the unscaled singular values before summing | overflow/underflow or known-answer mutation test trips |
| selected strategy is explicit | T5 exact lane name | restore the legacy hard-coded default | selection test fails |

Every corruption test must be observed to fail before this preregistration is
reported as implemented.

## 3b. Negative controls and non-degeneracy

- Uncapped native T1/T2 are exact controls; they must fail if any compiler
  step is omitted or reordered.
- The legacy capped tree-identity operation-100 fixture is retained as a known
  RED diagnostic and must not be relabeled as the repaired candidate.

For every full singular spectrum with full dimension \(D\) and kept dimension
\(k\), freeze the scale-stable discarded fraction as

\[
\widehat\sigma_i=\sigma_i/\sigma_0,\qquad
f_{\rm disc}=\frac{\sum_{i=k}^{D-1}\widehat\sigma_i^2}
{\sum_{i=0}^{D-1}\widehat\sigma_i^2}.
\]

All singular values must be finite, nonnegative, and nonincreasing, with
positive \(\sigma_0\), \(1\le k\le D\), and a finite positive denominator;
otherwise the ledger fails closed. The result must be finite and in \([0,1]\).

T3 must contain at least one selected native two-site split with \(D>32\),
\(k=32\), truncation cause exactly `max_bond`, and
\(f_{\rm disc}>10^{-12}\). Absence of that witness fails non-degeneracy.

The scale-invariance known answer is \(D=33\), \(k=32\), and all 33 singular
values equal to one, giving \(f_{\rm disc}=1/33\). Multiplying the whole
spectrum by \(10^{200}\) or \(10^{-200}\) must reproduce \(1/33\) within
absolute \(10^{-15}\). A mutated raw-square implementation must fail through
overflow/underflow, a non-finite guard, or known-answer disagreement.

## 4. Declared simplifications; whole-state validity remains unbounded

- The declared engineering object is deterministic execution of the selected
  finite-cap `native_simple_update` algorithm. The finite cap is part of that
  algorithm's definition, not an approximation of some external truth within
  this engineering claim. There is no simplification relative to that declared
  engineering object.
- All complete-vector comparisons here use at most 14 qubits.
  This is exponentially bounded and is not a scalable contraction method.
- `native_simple_update` is a local PEPS approximation. No generic
  gauge-invariance, accumulated-error, or whole-state certificate is claimed.
- The four-round operation-100 fixture is a prefix of one development cell,
  not a QEC Record, held-out sweep, or device model.
- CPU thread counts 1 and 4 are the only registered execution variants. GPU
  remains a separate future environment/backend task.
- No measurement, reset, branch probability, detector fold, leakage, qutrit,
  composite-\(d\), or LER conclusion is permitted.
- Whole-state faithfulness is a separate, explicitly excluded object. The
  execution restrictions do not bound the local-PEPS approximation or provide
  independent ground truth for T3--T5. Whole-state faithfulness therefore
  remains unbounded and code-blocked; these tests cannot support a scientific
  or faithfulness claim.

## 5. Epistemic classes and predictions

- Class (a): Clifford conjugation, native no-truncation unitary identity, exact
  fixture/transcript equality, structural corruption trips.
- Class (b): none. No physical or speed direction is predicted by this repair.
- Class (c): thread-invariance bands, shadow-isolation bands, local tail and
  resource diagnostics, development timing.

A passing repair establishes only that the selected development
implementation no longer exposes the diagnosed thread-sensitive legacy
bridge on the registered tests. It does not prove generic PEPS truncation
correctness.

## 6. Execution and timing

- Every nontrivial run is a committed script with a `__main__` guard.
- T3 children are fresh processes and may run concurrently; no process changes
  BLAS variables after importing NumPy/Quimb.
- Record total wall and CPU time per child plus initialization, frame
  composition/pullback, native compile, basis changes, parity
  compute/uncompute, root rotation, native two-site split, validation,
  checkpoint contraction, evidence shadow, and publication/accounting spans.
- Performance excludes uncapped shadows and checkpoint materialization from
  algorithm time but reports both separately.
- Raw timings carry no directional pass/fail prediction.

## 7. Prerequisite gate

```text
premises_closed = yes
standard_metrics_bound = yes
predictions_frozen = yes
independent_ground_truth = yes, for T1 and T2 only
metamorphic_without_independent_ground_truth = T3 and T4
constraint_falsifiers_registered = yes
engineering_object = deterministic execution of selected finite-cap algorithm
engineering_object_simplifications = none
simplifications_bounded = yes_for_declared_engineering_object
whole_state_faithfulness_simplification_bounded = no
whole_state_faithfulness_CODE_PERMITTED = no
faithfulness_claim = no
negative_controls_registered = yes
preregistration_gate = pass_for_engineering_repair_only
formal_bond32_prereg_amended = no
CODE_PERMITTED = engineering implementation repair only
```

