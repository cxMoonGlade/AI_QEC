# GCAPEPS n=8, r=3 equal-status candidate differential — pre-registration

Status: **FROZEN AS A DESIGN BEFORE IMPLEMENTATION AND TARGET EXECUTION,
2026-07-29; EFFECTIVE IN THE FIRST COMMIT CONTAINING THIS PACKET.**

This freeze becomes effective only at the first commit containing this packet,
its closure, `CONTEXT.md`, `docs/service_status.json`, `docs/METRICS.md`, and
`docs/NUMERICAL_PROVENANCE.md`, with no experiment code or target output in
that commit. Every earlier checkout remains `CODE_BLOCKED`.

Closure packet:
`docs/simulator_validation/GCAPEPS_N8_R3_DUAL_CANDIDATE_DIFFERENTIAL_LITERATURE_CLOSURE_2026-07-29.md`.

Primary execution route: **two equal-status candidate state-action lanes on
one bounded fixture, plus one untimed NumPy-only exact-small anchor**. Once
implemented and passing, the planned anchor may qualify exactly one n=8
input-state action and never enters any
efficiency numerator, denominator, timing sample, or RSS ratio. Neither
candidate is an ECS registered Carrier/Record service, and this is not
canonical ECS Record acceptance.

## -1. Question charter

- **Decision:** determine whether ordinary Quimb PEPS and GCAPEPS produce the
  same physical complete vector for one frozen n=8, active-rank-3 update, and
  measure their current implementation time and representation cost.
- **Plain lane:** `plain_quimb_direct_sum_pepo_on_peps`; the Clifford stream is
  physically applied to the PEPS and the full signed physical Pauli sum is one
  native Quimb direct-sum PEPO applied without compression.
- **GCAPEPS lane:** the same Clifford stream updates a Stim tableau; the same
  physical rank-three sum is signed-pulled back and tree-routed into the
  residual Quimb PEPS.
- **Interpretation:** the two state-action lanes remain symmetric performance
  candidates. A planned third NumPy-only path will independently build the closed-form
  input and literal state action. Once implemented and passing, it permits only
  `BOUNDED_EXACT_SMALL_STATE_ACTION_ANCHORED`; neither lane becomes Quimb
  truth, an oracle, or a generic Carrier.
- **Efficiency:** report raw samples plus robust summaries for update time,
  vector materialization, process memory, bonds, tensor elements, gauges, and
  logical bytes. Interpret ratios only after differential `AGREE`, anchor
  `PASS`, and SDIM-frame `PASS`, and only
  for this fixture, machine, fork commit, and lowering.
- **Kill condition:** different fixture bytes, coordinates, physical gate
  streams, dtype, truncation policy, optimizer, resource envelope, or process
  treatment; a plain worker importing `quimb.experimental.gcapeps`; an anchor
  importing Quimb, Stim, SDIM, or GCAPEPS; a candidate worker seeing any other candidate or anchor
  output before sealing its own; hidden phase fitting/normalization/permutation;
  an inert corruption; or any unqualified Record, scaling, generic-correctness,
  or generic-speed claim.

## 0. Grounding ledger

| sub-axis | source/derivation | local object |
|---|---|---|
| hybrid state and signed pull-through | Harper et al., Sec. 3/Fig. 3, PDF p. 5 | `StimCliffordFrame`, `GCAPEPSState` |
| tree-routed PEPO | project Lemma 3 and Eqs. (9), (11), (13), (16), (17) | `QuimbPEPSCarrier.apply_coherent_pauli_sum` |
| ordinary PEPO-on-PEPS | public Quimb core APIs in the frozen fork | `PEPO_product_operator`, `add_PEPO`, `PEPO.apply(..., contract=True, compress=False)` |
| independent exact-small anchor | current faithfulness protocol and finite-dimensional construction | closed-form input, literal bitwise Pauli action, and literal complex128 gate replay with no simulator imports |
| complete-state pair metric | Evenbly Sec. V Eq. (12), PDF p. 6, plus project phase/norm companions | symmetric comparator |
| exact-contraction boundary | Schuch et al., VOR PDF pp. 2–3 | fixture-only claim boundary |

The frozen project-theorem SHA-256 is
`7f5ec9c7c3dac2da7c377c0958f7eafc104d2da19b59350e1a7c336cc1cc10dc`;
the implementation-correspondence SHA-256 is
`b33c2fff6fcf7f6e7c934dceeeb47a7680a60be0d928670c5043b8a414f6642d`,
with status `SCOPED_ENGINEERING_GREEN__GENERIC_EQUIVALENCE_OPEN`.

## 1. Frozen neutral fixture

Fixture schema:
`error_coupling_simulator.external.gcapeps_n8_r3_fixture.v1`.

### 1.1 Coordinate and graph

- `n_qubits=8`, `active_rank=3`.
- Logical qubits are `(0,1,2,3,4,5,6,7)`. The Quimb site map is
  `q -> (q // 4, q % 4)`, with frozen site order
  `((0,0),(0,1),(0,2),(0,3),(1,0),(1,1),(1,2),(1,3))`.
- Open 2-by-4 graph, shown in logical-qubit edge order:

  ```text
  (0,1), (1,2), (2,3),
  (4,5), (5,6), (6,7),
  (0,4), (1,5), (2,6), (3,7)
  ```

- Local basis is `[|0>, |1>]`.
- Complete-vector axes are `[q0,q1,...,q7]`.
- `q0` is the most-significant flat-vector bit:
  `flat_index=sum_q bit(q)*2**(7-q)`.
- Matrix rows are output and columns are input.
- Every tensor and complete vector is NumPy `complex128`; gauges are
  `float64` or `complex128` only. No silent cast is permitted.

### 1.2 Residual-state preparation

Starting at \(|0^8\rangle\), execute in order:

```text
H 0
CX 0 1
CX 1 2
CX 2 3
H 4
CX 4 5
CX 5 6
CX 6 7
CX 1 5
```

This block is the zero-based chronological target-order ledger (rows 00..08).
For every `CX`, the first written target is control and the second is target.
Both Quimb candidates lower all nine preparation Cliffords only as explicit
dense complex128 raw gates. For each row,
`coordinate_targets=tuple(frozen_site_map[q] for q in logical_targets)` and
the call is `Gate.from_raw(U, qubits=coordinate_targets)`. Named or special
Quimb gate paths are forbidden. The anchor codes the same mathematical
matrices independently and must reproduce the frozen hashes below.

The frozen algebraic preparation invariant is

\[
|\phi\rangle
=\frac12\sum_{a,b\in\{0,1\}}
|a\,a\,a\,a\,b\,(a\oplus b)\,b\,b\rangle .
\]

Before any coherent sum:

- exactly four amplitudes are nonzero and equal \(1/2\);
- \(\|\phi\|_2=1\) and \(\|\phi\|_\infty=1/2\);
- both independently executed lane preparations must agree with each other and
  with the four-amplitude invariant on all 256 amplitudes;
- the PEPS constructor is explicitly configured with
  `max_bond=None`, `cutoff=0.0`, `renorm=False`, `gauge_smudge=0.0`,
  `equilibrate_every=None`, `dtype="complex128"`, `to_backend=None`, and
  `convert_eager=True`;
- complete contraction uses `contraction_optimize="greedy"`. `greedy`
  chooses an exact contraction order; it is not a boundary/environment
  approximation.

Expected preparation bonds are:

| edge | \(D_e\) before coherent update |
|---|---:|
| `(0,1)`, `(1,2)`, `(2,3)`, `(4,5)`, `(5,6)`, `(6,7)`, `(1,5)` | 2 |
| `(0,4)`, `(2,6)`, `(3,7)` | 1 |

Expected site tensor element counts are
`(4,16,8,4,4,16,8,4)`, total `64`.

### 1.3 Residual coherent unitary

The three raw and canonical terms are:

| coefficient | unsigned Pauli body | word phase |
|---:|---|---:|
| \(-0.8i\) | `XXYIZZXZ` | \(+1\) |
| \(-0.48i\) | `YXYZIZXZ` | \(+1\) |
| \(-0.36i\) | `ZXYZZZXI` | \(+1\) |

Thus

\[
U_{\rm res}=-i(0.8P_0+0.48P_1+0.36P_2).
\]

The three Pauli bodies square to identity and pairwise anticommute. Since
\(0.8^2+0.48^2+0.36^2=1\),

\[
U_{\rm res}^\dagger U_{\rm res}=I.
\]

This exact test-side certificate is recorded as
`pairwise_anticommuting_pauli_linear_combination_unitary`. Production must
still report its actual generic nonzero-validation route; the test-side proof
must not be relabelled as a production certificate.

The exact algebraic coefficient \(L_1\) norm is
\(C_{1,\mathrm{ideal}}=41/25=1.64\). The emitted binary64 value is recorded
separately and is not required to equal that decimal literal bit-for-bit.

### 1.4 Clifford frame and physical operator

The logical prefix contains `CX 5 7`, which is not a graph edge. Both
candidates consume the same exact graph-local expansion, in this zero-based
chronological target-order ledger:

```text
00 H     0
01 S     1
02 CX    0 4
03 H     3
04 CZ    2 6
05 S_DAG 7
06 SWAP  5 6
07 CX    6 7
08 SWAP  5 6
09 SWAP  1 2
```

The three-gate middle subsequence is exactly logical `CX 5 7`. Thus the
logical prefix has eight gates and the canonical graph-local stream has ten.
The canonical fixture token and Stim instruction at row 05 are exactly
`S_DAG`; `SDG` is forbidden in fixture and Stim payloads. The plain candidate
uses no named phase-dagger gate: it supplies the raw dense complex128 SDG
matrix

\[
U_{\rm SDG}=S^\dagger=\begin{bmatrix}1&0\\0&-i\end{bmatrix}
\]

through `Gate.from_raw`. Every plain preparation and prefix Clifford,
including every `SWAP`, uses logical targets from the canonical ledger, maps
them with
`coordinate_targets=tuple(frozen_site_map[q] for q in logical_targets)`, and
calls `Gate.from_raw(U, qubits=coordinate_targets)`. Named/special Quimb gate
paths and hidden nonlocal fallbacks are forbidden.

Raw matrices are C-contiguous little-endian NumPy `<c16`, with rows as outputs,
columns as inputs, and bases `[0,1]` / `[00,01,10,11]`. For `CX`, targets are
ordered `(control,target)`. Matrix-family SHA-256 values are:

| canonical token | shape | `<c16` C-order SHA-256 |
|---|---:|---|
| `H` | 2x2 | `b8a0541aa80b1a09f1847692e688d8f59e6f7b27904794cb34e3a00547af4cc1` |
| `S` | 2x2 | `1ea2137ca5d78fbfcef3cfa04052cd34575f5e62ee440b714e6397cc6614322b` |
| `S_DAG` (plain raw SDG) | 2x2 | `ccdbdd050e820173b78aad0ea053b667a57470bece9c154274926d4192add3a8` |
| `CX` | 4x4 | `8147eeddb2b56869f494b2194eb43a7926d1bb5edb4d4f35c6fa9e9633dd4bf8` |
| `CZ` | 4x4 | `411d2854573bf05718bccb74b2bea00f6180dd0104861c8f112aa0295ea85b45` |
| `SWAP` | 4x4 | `0fe211d0be6e5908155c70589905d5f91f528440f5a2ddcd39a477b25fd7e70d` |

`H` uses `float64(1)/sqrt(float64(2))`. Every matrix must be finite and satisfy
`max(abs(U.conj().T @ U - I)) <= 8*eps_float64`. Occurrence streams serialize
one UTF-8 line per row as
`{index:02d}|{canonical_token}|{comma_joined_targets}|{matrix_sha256}\n`.
Frozen hashes are
`preparation_gate_stream_sha256=e42a195ba2736164700fcf86c1f5949f5a49d39c1932cfd9ee6b8cf6efab3538`
and
`clifford_gate_stream_sha256=aeb75e08b6ac4a592d31199c2eafe9ed0c968465e50d05fa45b7d139a397e50c`.
The canonical fixture, Stim, and anchor ledgers retain logical integer
targets, and the stream hashes above cover those logical targets. The plain
Quimb ledger additionally reports the mapped coordinate targets for every row.
The fixture emitter, both candidates, literal c128 physical lift, and anchor
must report their applicable per-row token/target/matrix ledgers, both stream
hashes, and every unitarity residual before comparison is eligible.

Writing the resulting Clifford as \(C\), define

\[
U_{\rm phys}=C U_{\rm res}C^\dagger .
\]

The signed physical terms are frozen as:

| coefficient | unsigned Pauli body | word phase | pullback |
|---:|---|---:|---|
| \(-0.8i\) | `IXYIZIYZ` | \(-1\) | `+XXYIZZXZ` |
| \(-0.48i\) | `YXYXXIYZ` | \(+1\) | `+YXYZIZXZ` |
| \(-0.36i\) | `YXYXYZYI` | \(+1\) | `+ZXYZZZXI` |

Coefficient and word phase remain separate. No implementation may absorb the
first minus sign into the coefficient and also retain `word_phase=-1`.

The two equal-status lane outputs are

\[
y_{\rm plain}=U_{\rm phys}C|\phi\rangle,
\qquad
y_{\rm gca}=C U_{\rm res}|\phi\rangle.
\]

The experiment tests their pairwise equality and does not designate either as
ground truth.

## 1.5 Frozen dependence and routing

\[
W=(0,3,4,7),\qquad W_U=(0,1,2,3,4,5,6,7).
\]

Expected deterministic route:

```text
root     = 0
vertices = (0,1,2,3,4,7)
edges    = ((0,1),(0,4),(1,2),(2,3),(3,7))
```

The fixture deliberately contains:

- common nonidentity factors `X`,`Y` at
  \(T\setminus W=\{1,2\}\);
- common nonidentity factors `Z`,`X` at
  \(V\setminus T=\{5,6\}\).

The five routed edges must transform as:

| edge | before | after |
|---|---:|---:|
| `(0,1)` | 2 | 6 |
| `(0,4)` | 1 | 3 |
| `(1,2)` | 2 | 6 |
| `(2,3)` | 2 | 6 |
| `(3,7)` | 1 | 3 |

The five off-tree edges `(4,5)`, `(5,6)`, `(6,7)`, `(1,5)`, and `(2,6)`
must remain respectively `2,2,2,2,1`.

For every routed edge:

```text
operator_bond = 3
pepo_rank_factor = 3
routed_rank_product: 1 -> 3
refactor_operator_schmidt_factor = 1
refactor_rank_product: 1 -> 1
total_bond_growth_product: 1 -> 3
compressed = false
```

Every off-tree factor and product remains one.

### 1.6 Exact GCAPEPS resource preflight and plain-PEPO ledger

All seven `GCAPEPSResourceLimits` are supplied explicitly:

| resource | cap |
|---|---:|
| maximum local operator elements | 36 |
| total operator elements | 176 |
| maximum local candidate-state elements | 144 |
| total candidate-state elements | 336 |
| maximum predicted PEPS bond | 6 |
| maximum routed PEPO-rank product | 3 |
| maximum total bond-growth product | 3 |

The constructor is frozen exactly as:

```python
GCAPEPSResourceLimits(
    max_local_operator_elements=36,
    max_total_operator_elements=176,
    max_local_candidate_tensor_elements=144,
    max_total_candidate_tensor_elements=336,
    max_predicted_bond_dimension=6,
    max_routed_rank_product=3,
    max_total_bond_growth_product=3,
)
```

Logical complex128 payloads are:

- operator: `176` elements / `2816` bytes, largest local block `36` /
  `576` bytes;
- state before: `64` elements / `1024` bytes;
- state after: `336` elements / `5376` bytes, largest site `144` /
  `2304` bytes.

These are logical tensor payloads, not peak process RSS, contraction
workspace, allocator usage, or a performance claim.

The ordinary lane constructs three bond-one product PEPO terms with public
Quimb primitives and combines them as one native direct-sum PEPO. Its frozen
operator prediction is bond dimension three on every one of the ten graph
edges, total operator elements `576`, maximum local operator elements `108`,
and logical complex128 payload `9216` bytes. The worker must recompute these
from tensors. Plain state bonds/elements after the physical Clifford prefix and
after PEPO application are observed exact integer ledgers, not pre-tuned
values. No resource outcome is a correctness proxy.

## 2. Symmetric differential and efficiency metrics

Let \(y_q\) be the ordinary Quimb physical PEPS vector and \(y_g\) be the
GCAPEPS physical vector reconstructed by applying the frozen literal
complex128 ten-gate lift to the residual PEPS vector. Stim tableau
`to_unitary_matrix` is forbidden for this row because it is complex64 and
defined only up to global phase. Both must be finite one-dimensional length-256
`complex128` arrays in q0-MSB order. Before evaluating

\[
d_\infty=\|y_g-y_q\|_\infty,\qquad d_2=\|y_g-y_q\|_2,
\]

\[
d_{\rm rel}=\frac{2d_2}{\|y_g\|_2+\|y_q\|_2},\qquad
d_{\rm norm}=\frac{2|\|y_g\|_2-\|y_q\|_2|}
{\|y_g\|_2+\|y_q\|_2},
\]

\[
F_{\rm pair}=\frac{|\langle y_q|y_g\rangle|^2}
{\langle y_q|y_q\rangle\langle y_g|y_g\rangle},
\]

both norms and every denominator must be finite and strictly positive. No
phase fit, normalization, dtype cast, or coordinate permutation is permitted.
Absolute \(d_\infty\) and \(d_2\) are always reported. The fixture differential
bands are

```text
d_rel  <= 2e-11
d_norm <= 2e-11
1 - F_pair <= 1e-12
abs(fidelity_roundoff_correction) <= 1e-12
```

They are pairwise c128 agreement bands, not physical error bars or generic
correctness bounds. Absolute `d_inf` and `d_2` are report-only; `AGREE` gates
exactly `d_rel`, `d_norm`, and infidelity. Define
`fidelity_roundoff_correction=max(0.0,F_pair_raw-1.0)` and use
`F_pair=min(1.0,F_pair_raw)` only when that correction is at most `1e-12`.
The same pair metric family is evaluated after the Clifford prefix and after
the final rank-three update. The after-Clifford GC vector is
`C_gate_list_c128 @ phi_residual`; the final one is
`C_gate_list_c128 @ y_residual_after`.

The untimed anchor independently constructs \(a_{\rm res}\) from the
closed-form \(\phi\) and literal bitwise residual Pauli action. It also
constructs \(a_{\rm phys}\) from \(|0^8\rangle\), literal complex128
preparation/Clifford gates, and literal bitwise signed physical Pauli action.
These formulations must agree after the same literal lift. GC residual is
graded against \(a_{\rm res}\); plain physical and lifted GC physical vectors
are separately graded against \(a_{\rm phys}\), with the same bands and no
phase fit, normalization, or permutation. The anchor imports no Quimb, Stim,
SDIM, or GCAPEPS; it qualifies only this one n=8 input-state action and enters
no timing/RSS sample, numerator, or denominator.

A normalized overlap, bond dimension, retained-weight product, local singular
value, norm alone, Stim/SDIM match, or one lane's internal dense audit may not
replace this complete-vector pair.

### 2.1 Efficiency observations

Each fresh worker reports integer nanoseconds from `perf_counter_ns` for:

- preparation;
- plain physical Clifford or GC tableau prefix;
- plain PEPO construction or GC coherent-IR construction;
- plain PEPO application or GC carrier application;
- residual/physical complete-vector materialization;
- GC literal complex128 gate-list lift separately;
- worker computation total, excluding process launch/import.

The primary current-implementation update samples are

```text
plain_update = physical_clifford + pepo_build + pepo_apply
gcapeps_update = tableau_prefix + coherent_ir_build + carrier_apply
```

The GC sample explicitly has
`includes_exact_small_internal_dense_and_norm_checks=true`; it is not a pure
carrier-kernel timing. Materialization time is never folded into update time.

For each lane use one discarded fresh-process warmup and six measured fresh
workers. Measured pairs alternate launch order `plain,gcapeps` then
`gcapeps,plain`, repeated three times. Every raw sample is retained. Report
median and median absolute deviation (MAD), with

\[
R_{\rm update}=\frac{\operatorname{median}(t_{\rm plain})}
{\operatorname{median}(t_{\rm gca})},\qquad
R_{\rm RSS}=\frac{\operatorname{median}(\mathrm{RSS}_{\rm plain})}
{\operatorname{median}(\mathrm{RSS}_{\rm gca})}.
\]

The preregistered directional hypothesis is `R_update > 1`. It is not an
acceptance gate. A contrary result is reported unchanged. Ratios are
interpretable only if the final differential is `AGREE`, the anchor is
`PASS`, and the SDIM-frame verdict is `PASS`.

Each lane also reports, at preparation, after Clifford/frame, and after the
rank-three update: every graph-edge state bond, maximum bond, tensor count,
total and maximum-site state elements, gauge elements, logical tensor bytes,
and fresh-process `ru_maxrss` with platform units plus cgroup `MemoryPeak` when
available. Plain PEPO and GC tree-PEPO elements, maximum local elements, bonds,
and bytes remain separate. GC reports tableau dimensions/revision separately;
residual-only bytes are never labelled total GCAPEPS memory.

### 2.2 Frozen planned owners

| role | frozen path |
|---|---|
| canonical fixture emitter/validator | `scripts/external_baselines/emit_gcapeps_n8_r3_fixture.py` |
| ordinary Quimb worker | `scripts/external_baselines/plain_quimb_n8_r3_worker.py` |
| independent dense anchor | `scripts/external_baselines/gcapeps_n8_r3_dense_anchor.py` |
| GCAPEPS/Stim worker | `scripts/external_baselines/gcapeps_n8_r3_worker.py` |
| symmetric comparator | `scripts/external_baselines/compare_gcapeps_n8_r3_differential.py` |
| signed SDIM frame differential | `scripts/external_baselines/gcapeps_n8_r3_sdim_worker.py` |
| corruption/fairness controls | `scripts/external_baselines/run_gcapeps_n8_r3_controls.py` |
| fresh-worker supervisor/publication | `scripts/external_baselines/run_gcapeps_n8_r3_differential.py` |
| independent contract tests | `tests/test_external_gcapeps_n8_r3_differential.py` |

Before target execution, `docs/METRICS.md`,
`docs/NUMERICAL_PROVENANCE.md`, and `tests/CODEBOOK.md` must name the actual
implemented owners, formulas, bands, schemas, and tests. A planned path is not
a current owner.

### 2.3 Claim-bearing value provenance ledger

| value/object | kind | allowed interpretation | forbidden interpretation |
|---|---|---|---|
| n=8, active rank 3, 2x4 graph and gate streams | `project-design` | frozen differential fixture | scaling/workload representativeness |
| `(0.8,0.48,0.36)` and signed physical words | `project-design` | synthetic unitary stressor | calibrated noise/rate |
| `2e-11`, `1e-12` pair bands | `numerical-only` | fixture c128 agreement rule | physical error bar/correctness certificate |
| NumPy dense anchor | `independent-reference` | one n=8 input-state action | generic PEPS truth/operator equality |
| six measured workers and median/MAD | `convenience-default` | bounded timing protocol | benchmark standard/asymptotic evidence |
| raw wall ns, RSS, MemoryPeak | `observed` | this machine/process envelope | portable performance |
| bond/tensor elements and logical bytes | `numerical-only` | exact representation ledger | contraction cost or accuracy proof |
| 300 s, 8 GiB, 32 tasks | `numerical-only` | fail-closed resource envelope | performance claim |
| Python/NumPy/Quimb/Stim/SDIM identities | `convenience-default` | runtime provenance in stated scope | scientific truth |

### 2.4 Disconfirmation surface

The benchmark distinguishes wrong signed pullback, wrong sum-versus-product,
route/fusion value defects, coordinate/phase/scale mismatches, truncation, and
misreported resource/timing fields. The NumPy anchor catches a shared
Quimb-core defect when it changes this frozen complete state. It still shares
fixture semantics and cannot establish generic PEPS truth, all-input operator
equality, or scalable contraction.

## 3. Equal-status candidate state-action execution; no candidate truth

There are two equal-status candidate state-action lanes. Each worker seals its
own payload before the supervisor exposes the other candidate output or the
anchor. The supervisor validates schemas/provenance first and only then invokes
the symmetric comparator and separate anchor grader. Neither candidate is
designated truth.

### 3.1 Common preparation and fairness contract

Both candidate workers receive the same canonical fixture bytes/hash. Each first
builds `psi0=qtn.PEPS.product_state({coord: c128_zero_vector, ...},
cyclic=False)`, then passes that true 2D PEPS plus the frozen coordinate edges
to `CircuitPEPSSimpleUpdate(psi0=psi0, edges=..., max_bond=None,
cutoff=0.0, renorm=False, gauge_smudge=0.0, equilibrate_every=None,
dtype="complex128", to_backend=None, convert_eager=True)`. Starting from only
integer-labelled generic TN sites is forbidden because it is not a stable
PEPO-on-PEPS interface. No compression, finite boundary, or approximate
contraction is allowed. Both preparation vectors/hashes must agree with the
anchor preparation before timing is interpretable.

The supervisor pins every worker to the same lowest CPU allowed by its own
process affinity, fixes BLAS/OpenMP thread counts to one, uses the same cgroup
envelope and empty CUDA visibility, and alternates launch order as registered.
Import/process-launch time is recorded by the supervisor but excluded from both
lane update samples.

### 3.2 Independent NumPy exact-small anchor

This untimed worker starts from the closed-form four-amplitude \(\phi\), applies
literal residual Pauli terms by computational-basis bit action with
`Y|b> = i*(-1)**b |b xor 1>`, and emits \(a_{\rm res}\). A second formulation
starts at \(|0^8\rangle\), replays independently written literal complex128
preparation and ten-gate Clifford matrices, applies the signed physical Pauli
terms by the same explicit bit rule, and emits \(a_{\rm phys}\). The residual
result lifted through the literal ten-gate circuit must agree with the physical
formulation before the anchor is eligible. The module is statically scanned and
runtime-guarded against imports of Quimb, Stim, SDIM, and GCAPEPS. It receives
no Carrier output and is excluded from all timing/RSS ratios.

### 3.3 Ordinary Quimb lane

The worker imports public Quimb core and NumPy only; importing
`quimb.experimental.gcapeps` or calling `build_global_direct_sum_reference` is
a hard provenance failure. Starting from its prepared PEPS it:

1. physically applies the ten frozen graph-local Clifford gates, after all
   nine preparation gates were applied by the same raw path. Each logical
   target row is mapped with
   `coordinate_targets=tuple(frozen_site_map[q] for q in logical_targets)`,
   then passed to `Gate.from_raw(U, qubits=coordinate_targets)`; row 05 uses
   the raw SDG matrix while the canonical fixture remains `S_DAG`;
2. for each signed physical Pauli term, creates a bond-one
   `PEPO_product_operator` from literal local I/X/Y/Z matrices, multiplying
   `coefficient * word_phase` exactly once into the q0 local factor;
3. combines terms only by the instance-method chain
   `pepo01 = term_pepos[0].add_PEPO(term_pepos[1])` then
   `pepo = pepo01.add_PEPO(term_pepos[2])`; module-level `add_PEPO`, in-place
   mutation, sequential application, multiplication, and sampling are forbidden;
4. applies that one PEPO once with `contract=True, compress=False`;
5. constructs
   `physical_inds=tuple(plain_state.site_ind(site) for site in frozen_coordinate_order)`,
   calls `plain_state.to_dense(physical_inds, to_qarray=False,
   to_ket=False, optimize="greedy")`, requires the returned array already has
   dtype `complex128`, and only then reshapes it to the q0-MSB length-256 vector.

This lane is named `plain_quimb_direct_sum_pepo_on_peps_at_frozen_fork_commit`.
It is a pure-state experimental state-action baseline using Quimb operator
PEPO-on-PEPS APIs. It is **not** the registered ECS density-matrix
`carrier/pepo` service, is not a registered ECS Carrier, and is not claimed to be
the optimal representative of every Quimb/PEPS method.

### 3.4 GCAPEPS lane

The worker constructs the same prepared PEPS circuit, creates the exact
`GCAPEPSResourceLimits` object frozen in §1.6, and calls
`QuimbPEPSCarrier(circuit, site_order=frozen_coordinate_order,
contraction_optimize="greedy", resource_limits=limits)`, then creates
`GCAPEPSState(StimCliffordFrame(8), carrier)`. It:

1. starts with frame revision zero and no routing events, then calls
   `GCAPEPSState.apply_clifford(stim.Circuit(one_gate_text))` exactly once per
   chronological row; batching is forbidden and row 05 is exactly `S_DAG 7`;
2. requires ten returned `clifford_frame_update` events, columns `0..9`,
   `frame_revision_before=i`, `frame_revision_after=i+1`, unchanged residual
   revision/gate count/bond, final frame revision `10`, and
   `len(state.events)==10`;
3. constructs the same three signed physical terms as one `CoherentPauliSum`;
4. calls `GCAPEPSState.apply_coherent_pauli_sum`, requiring the frozen signed
   pullback and tree/resource ledger; its coherent event is separate from the
   ten required Clifford events/revision increments;
5. contracts the residual PEPS exactly and applies the frozen literal c128
   ten-gate lift gate-by-gate in chronological order, requiring every §1.4
   matrix hash, target-order row, stream hash, and unitarity bound. Stim
   `Tableau.to_unitary_matrix` remains forbidden for grading.

The state vector is physical only after the literal gate-list lift. Residual
and physical hashes are both retained. Stim remains authoritative only for
signed pullback. Raw routing/tree/edge rows are retained in coordinate-site
space; the worker also normalizes them through the frozen inverse site map to
logical q=0..7 before checking the integer expectations in §1.5. The
carrier's n<=10 internal same-IR dense and norm checks remain required engineering gates, and their time
remains inside `carrier_apply`; they are not independent evidence. The project
correspondence remains
`SCOPED_ENGINEERING_GREEN__GENERIC_EQUIVALENCE_OPEN`: this fixture tests a
frozen construction but does not close generic Eq. (9)/(11) implementation
equivalence.

### 3.5 Stim/SDIM frame differential

A separately provisioned SDIM 1.3.3 qubit worker consumes only the frozen
Clifford stream and signed physical words. It must reproduce Stim's signed
pullbacks term by term. It never receives a PEPS/vector, contributes no timing ratio, is not ground
truth, and is not qutrit evidence. Its verdict never changes the pair or anchor
metrics, but a non-`PASS` result makes state-action qualification and efficiency
interpretation `INELIGIBLE`.

### 3.6 Required controls

All controls run before measured target workers. They use independent copies and
cannot modify frozen target bytes.

| control | required result |
|---|---|
| fixture hashes differ across lanes | `INELIGIBLE` before timing comparison |
| anchor imports a forbidden simulator module or its two formulations disagree | anchor `INELIGIBLE`; no state-action certification |
| plain or GC output is perturbed identically | pair may agree but at least one anchor comparison must fail |
| plain lane omits one of the two routing SWAPs | after-Clifford pair metric becomes `MISMATCH` with movement `>1e-8` |
| plain lane multiplies the three Pauli terms instead of direct-sum addition | final pair becomes `MISMATCH`, movement `>1e-8` |
| only one lane flips first physical word phase | final pair becomes `MISMATCH`, movement `>1e-8` |
| GC signed pullback expectation is corrupted | exact signed-word check rejects it |
| one GC route/common-factor/fused-layout/tensor-value construction is corrupted | existing exact-small fork construction tests must trip; their selected test IDs are recorded |
| only one exported vector swaps q0/q7 axes | pair becomes `MISMATCH` |
| one vector is multiplied by exactly `1j` | fidelity remains within `1e-12` of one while phase-sensitive rows fail |
| one vector is multiplied by `1+1e-6` | fidelity remains near one while direct/norm rows fail |
| one vector element receives `1e-6+0j` | complete-vector differential fails while copied structural metadata can remain unchanged |
| nonfinite/wrong dtype/wrong shape vector | hard schema failure before metrics |
| timing is zero/negative, sample count differs, or launch order differs | efficiency interpretation is `INELIGIBLE` |
| SDIM first sign is flipped | signed-frame differential fails |

The shared-corruption control demonstrates why the anchor is required: a
common perturbation can leave pair agreement green while anchor comparison
fails. Even full anchored agreement remains limited to this one input-state
action and cannot certify generic PEPS contraction or all-input operator
equality.

## 4. Bounded simplifications

- Exactly one eight-qubit pure-state update is studied. Measurement, reset,
  branches, detector/observable Records, leakage, trajectories, and multi-round
  history are excluded.
- Both lanes are complex128 and untruncated. Any finite bond cap, compression,
  smudge, approximate environment, or unavailable complete vector makes the
  run `INELIGIBLE`.
- `greedy` selects a finite exact contraction order; it is not a generic PEPS
  certificate.
- Plain Quimb and GCAPEPS are compared at the same fork commit. The ordinary
  PEPO lane is one explicit public-API baseline, not the best possible Quimb
  algorithm.
- Current GCAPEPS update timing includes exact-small internal dense and norm
  checks. No claim about a stripped carrier kernel is allowed.
- A single state-action pair is not operator equality. The NumPy anchor may
  qualify only this one input action; pair agreement alone remains insufficient.
- Resource caps and observed ratios bind this process envelope only. They are
  neither accuracy bounds nor scaling evidence.
- The coherent unitary is synthetic and uncalibrated; there is no physical
  error-rate or realism claim.

## 5. Epistemic classes and terminal semantics

- **(a) exact:** fixture bytes/hash; graph/site/coordinate; preparation
  invariant; Pauli algebra and signed physical/residual mapping; graph-local
  Clifford equivalence; `W`, `W_U`, route; frozen GC and plain operator
  ledgers; dtype/shape/finiteness; anchor eligibility; exact Stim/SDIM signed
  pullback; schema and fairness identities. Plain post-Clifford/post-PEPO state
  resources are observed integer diagnostics, not preregistered expected rows.
- **(b) predictions:** each candidate output versus the independent exact-small
  anchor; after-Clifford and final pairwise c128 agreement bands; and the
  directional fixture hypothesis `R_update > 1`. Timing direction is never an
  acceptance condition.
- **(c) engineering gates/diagnostics:** internal same-IR checks, fidelity
  roundoff, corruption movement threshold, time/memory/task/payload caps, raw
  timing/RSS samples, median/MAD, and derived efficiency ratios.

Terminal fields are:

```text
differential_verdict = AGREE | MISMATCH | INELIGIBLE
anchor_verdict = PASS | FAIL | INELIGIBLE
sdim_frame_verdict = PASS | FAIL | INELIGIBLE
state_action_qualification_status =
    BOUNDED_EXACT_SMALL_STATE_ACTION_ANCHORED | FAILED | INELIGIBLE
efficiency_interpretation =
    ELIGIBLE_ONLY_IF_DIFFERENTIAL_ANCHOR_AND_SDIM_AGREEMENT | INELIGIBLE
```

`AGREE` requires both complete-vector stages to meet the pair bands. Anchor
`PASS` requires anchor self-consistency, GC residual versus anchor residual,
and both physical lane vectors versus anchor physical to meet the frozen bands.
SDIM-frame `PASS` requires term-by-term signed pullback agreement and its
registered sign-flip control. It does not alter `differential_verdict` or
`anchor_verdict`. The bounded state-action qualification is issued only when
differential, anchor, and SDIM verdicts all pass together with exact
map/structure, provenance, controls, environment, and publication. A non-PASS
SDIM verdict makes state-action qualification and efficiency `INELIGIBLE`. An
observed mismatch is reported without changing the fixture or bands.

There is no unqualified “correct candidate,” generic faithfulness, Record, or
scaling verdict. Efficiency ratios may be discussed only when differential,
anchor, and SDIM-frame verdicts all pass, with fixture, machine, fork commit, lowering, and
current-internal-check qualifiers attached.

## 6. Execution, environment, provenance, and publication

### 6.1 Main paired candidate environment

- Fork: `external/forks/quimb-gcapeps`, exact commit
  `6fbbf74cd36686ed30a4d8865697ce46e47056c1`, tree
  `ffdfdf421fbe4d9674c2c88029710042fd18ae14`.
- Environment: Pixi `testpymid`, Python 3.13; frozen
  `pyproject.toml` SHA-256
  `c8b48e06ee8595be41cc5dff6d4f8e768a9064d5a0f84efaec5ff12a7e8aa344`
  and `pixi.lock` SHA-256
  `854da99b417c69dbdca4118c2545656470ad4e0f276a606b1b8c3082f795db35`.
- Pixi is exactly `0.72.2`; the selected executable SHA-256 is
  `2f301e44ac4caa9e137d505e5d0606fd029182d4df6f9e3add80bc077effea87`.
- Stim must be exactly `1.16.0`.
- The imported `quimb.__file__` must resolve inside the frozen fork checkout.
- `PYTHONPATH` is forbidden.
- Claim-bearing parent files and the development fork commit/tree must be
  tracked, clean, and committed. The existing development checkout may retain
  unrelated ignored developer artifacts; it is never an execution checkout
  and is not mutated or cleaned by this benchmark.
- The supervisor materializes the frozen fork commit into a fresh temporary
  execution checkout. That checkout must be ignored-inclusive pristine: exact
  output from `git status --porcelain=v1 --untracked-files=all --ignored` is
  empty immediately after materialization, before controls, before target
  workers, and after the run. Ordinary status that omits ignored files is
  insufficient.
- Pixi provisioning is detached from that temporary checkout via a
  process-local config outside it, with
  `detached-environments` set to an absolute private directory outside the
  checkout.
  Environment prefix, Pixi home/cache/config, logs, bytecode, and coverage all
  resolve outside the checkout. Execution uses the frozen manifest with
  locked/frozen semantics and may not rewrite `pixi.lock`; any ignored path in
  the temporary execution checkout makes the run `INELIGIBLE`.
- Both plain and GCAPEPS workers run from this exact environment and fork
  commit. The plain worker has a prohibited-import scan for
  `quimb.experimental.gcapeps`; the GC worker records its exact import origins.
- Each sealed lane payload binds fixture hash, worker source hash, Quimb import
  origin, fork commit/tree, settings, CPU affinity, and thread environment.

### 6.2 SDIM differential lane

- Environment definition:
  `external/forks/quimb-gcapeps/environment-gcapeps-sdim.yml`.
- Python `3.12.13`, Stim `1.16.0`, SDIM `1.3.3`.
- The YAML is a bootstrap, not a transitive lock or wheel-byte attestation;
  the complete installed distribution state, import origins, fork commit,
  source hashes, and environment-file hash must be recorded at runtime.
- SDIM carries only the signed dimension-two qubit-frame pullback. It never
  receives or emits a PEPS, state vector, fidelity, or state-action verdict.
  Its report is required corroboration but cannot independently issue the
  carrier differential verdict or support qutrit evidence.

### 6.3 Fresh-process envelope

The committed parent supervisor remains outside the resource cgroup so it can
publish a failure envelope after a worker OOM or timeout. Each target worker
runs fresh under:

```text
MemoryMax = 8 GiB
MemorySwapMax = 0
RuntimeMaxSec = 300 s
TasksMax = 32
```

Thread counts are fixed to one for OMP, OpenBLAS, MKL, NumExpr, and BLIS.
`PYTHONNOUSERSITE=1`, `PYTHONDONTWRITEBYTECODE=1`, `PYTHONHASHSEED=0`,
`TZ=UTC`, and an empty `CUDA_VISIBLE_DEVICES` are recorded.

The installed systemd 255 user manager and cgroup-v2 filesystem are capability
preflight requirements. Unavailability makes the efficiency comparison
`INELIGIBLE`; it does not relax the envelope. Before any worker, the supervisor
resolves one exact CPU id as the minimum of its allowed affinity and pins every
child to that same id. Warmups run strictly serial in frozen order
`plain,gcapeps` and are discarded. Twelve measured children then run strictly
serial, each fully completed/reaped before the next, in pair order
`plain,gcapeps`; `gcapeps,plain`, repeated three times. Each reports frozen
timing segments, process user/system time, `ru_maxrss` with platform units, and
cgroup `MemoryPeak`. Logical tensor payload, RSS, and cgroup memory remain
distinct fields. Plain after-PEPO gauges are
`UNAVAILABLE_NATIVE_PEPO_RESULT_NOT_VIDAL_GAUGED` with `gauge_elements=null`;
old circuit gauges may not be reused. GC representation gauges are reported
separately and are not a symmetric accuracy metric.

### 6.4 Report schema and no-replace atomic publication

Terminal schema:
`error_coupling_simulator.external.gcapeps_n8_r3_candidate_state_action_differential.v1`.

The report binds parent/fork Git identities and hashes; the canonical fixture;
environment and import identities; separately sealed anchor/plain/GCAPEPS vector hashes;
both update and structural ledgers; all raw timing samples and launch order;
every metric, gate, corruption, timing,
resource value, and excluded claim.

The destination parent must already exist. The supervisor freezes the absolute
lexical destination, opens and holds the parent directory fd, seals its
`st_dev/st_ino`, and performs both collision-preservation and success probes
for `renameat2(..., RENAME_NOREPLACE)` on the actual target filesystem before
workers run.

Artifacts are written through a private stage-directory fd. Every artifact is
flushed, file-fsynced, hash-checked, and exact-set validated. The manifest is
written and fsynced last; the stage directory is then fsynced. The bundle is
still only prepared at this point. Final publication uses the held parent fd
and `renameat2(..., RENAME_NOREPLACE)`, followed by parent-directory fsync and
published-inode/path rechecks. `os.replace` and unlink-then-rename are
forbidden. An existing destination is never replaced. If rename succeeds and a
later check fails, the published destination is preserved and failure
propagates.

The bundle cannot self-attest events that occur after its bytes are sealed.
Successful function return and the outer supervisor's observation are the only
confirmation that rename, parent fsync, and final identity checks completed.
The sealed payload contains exactly these publication fields:

```json
{
  "publication_status": "prepared_for_atomic_publication",
  "claims_offline_durability_confirmation": false,
  "target_filesystem_collision_probe_passed": true,
  "target_filesystem_noreplace_success_probe_passed": true,
  "artifact_file_fsync_success_attested_in_bundle": false,
  "staging_directory_fsync_success_attested_in_bundle": false,
  "final_staged_set_revalidation_success_attested_in_bundle": false,
  "rename_noreplace_success_attested_in_bundle": false,
  "parent_directory_fsync_success_attested_in_bundle": false,
  "published_destination_identity_recheck_success_attested_in_bundle": false,
  "successful_supervisor_return_is_only_publication_confirmation": true
}
```

## 7. Build organization and pre-execution order

1. Commit the closure, preregistration, `CONTEXT.md`,
   `docs/service_status.json`, `docs/METRICS.md`, and
   `docs/NUMERICAL_PROVENANCE.md` together before experiment/comparator code.
2. Implement the canonical fixture, untimed independent NumPy anchor, plain
   Quimb worker, GCAPEPS worker, anchor grader, and symmetric comparator at the
   frozen differential paths in §2.2.
3. Implement tests first and demonstrate every preregistered corruption,
   fairness, schema, and common-map structural control before target execution.
4. Implement the frame-only SDIM differential and fresh-worker AB/BA
   supervisor with no-replace publication.
5. Synchronize `docs/METRICS.md`, `docs/NUMERICAL_PROVENANCE.md`, and
   `tests/CODEBOOK.md` to actual owners/formulas/classes/tests.
6. Review the complete implementation phase diff; commit all claim-bearing
   code/contracts and require clean parent and fork heads.
7. Materialize and preflight the locked main and SDIM environments, systemd
   user manager, cgroup v2, CPU affinity, thread controls, and publication
   filesystem.
8. Run controls only.
9. If and only if every control/preflight passes, execute the frozen target
   supervisor once. That one supervisor contains the preregistered warmups and
   measured fresh-worker population; no result may tune fixture or bands.

## 8. Prerequisite gate

| gate | status |
|---|---|
| literature/mechanism premises | pass for bounded equal-status candidate design |
| symmetric complete-vector metric | pass by design |
| fixture, literal c128 gate ledgers, and pair/anchor bands | frozen |
| ordinary Quimb candidate | pure-state public direct-sum PEPO-on-PEPS; not registered ECS density-matrix `carrier/pepo` |
| GCAPEPS candidate | per-gate Stim frame updates plus tree-routed residual |
| independent exact-small anchor | frozen by design; implementation pending; NumPy-only, untimed, one n=8 input-state action only |
| SDIM frame corroboration | frozen by design; implementation pending; required for qualification and efficiency but never enters their numeric ratios |
| fairness and corruption controls | registered; must execute before target |
| efficiency interpretation | conditional on differential, anchor, and SDIM-frame agreement |
| generic implementation equivalence | open: `SCOPED_ENGINEERING_GREEN__GENERIC_EQUIVALENCE_OPEN` |
| generic Carrier/Record/scaling correctness | excluded and open |
| **differential preregistration gate** | **PASS AS A DESIGN; EFFECTIVE IN THE FIRST COMMIT CONTAINING THIS PACKET** |

Any checkout that does not yet contain the freeze commit remains `CODE_BLOCKED`.
`CODE_PERMITTED` becomes effective only at the first commit that already
contains the renamed differential closure and preregistration plus matching
`CONTEXT.md`, `docs/service_status.json`, `docs/METRICS.md`, and
`docs/NUMERICAL_PROVENANCE.md` authority updates, with no experiment code or
target output preceding that commit. Target execution remains forbidden until
committed controls, owner-ledger sync, ignored-inclusive fork cleanliness,
detached locked environments, fairness/provenance checks, reviewed phase diff,
and no-replace publication preflight all pass. Once implemented and passing
its controls, the anchor may qualify only this
one n=8 input-state action; it cannot promote `AGREE` to generic PEPS, Carrier,
contraction, Record, or scaling correctness.
