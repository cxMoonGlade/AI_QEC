# No-cutoff minimal exact owners — pre-registration

Status: **ACTIVE PRE-REGISTRATION, MICRO-OWNERS ONLY, CODE_BLOCKED**,
2026-08-03.  Independent review approved the prediction-bearing
pre-activation SHA-256
`1b34446e58b763627cc3a028765839b66cd564995bea8f19beeddb4194cc55de`
with no remaining blocking findings.  Activation changes only this status and
review receipt; the predictions below are unchanged.

This packet freezes qualification tests for three deliberately small research
instruments: an exact sparse pair recurrence, a dynamic exact ADD over the same
recurrence, and an exact retained-boundary mixed-domain elimination meter.  It
does not amend the active d=3/5 census, qualify the target QEC lowering, create a
product solver, or change `solver_permission=CODE_BLOCKED`.

Implementation is authorized only outside `src/**`, after independent review
and activation of this packet.  The expected values below are predictions,
fixed before owner code or owner output exists.

## 1. Question and claim boundary

The question is narrower than route viability:

> Can repository-owned, cutoff-free, exact-small implementations own the
> literal semantics of the three currently missing meters on corruption-
> sensitive microfixtures?

A pass establishes only `MINIMAL_OWNER_QUALIFIED`.  It does not establish any
of the following:

- canonical lowering of the frozen d=3/5 Stim circuit into pair states or
  retained-boundary factors;
- target-grid values for `N_pair`, dynamic `N_DD`, or the retained-boundary TN
  burden;
- complete-Record TV, faithfulness, scaling, or asymptotic behavior;
- replacement of the historical `UNAVAILABLE` cells in
  `NO_CUTOFF_STRUCTURE_CENSUS_RESULT_2026-08-03.md`;
- permission to add or run a solver under `src/**`.

The terminal permission must remain:

```text
target_lowering = UNAVAILABLE
target_d3_d5_metrics = UNAVAILABLE
delta_tv_cert = UNAVAILABLE/UNANCHORED_FULL_RECORD
solver_permission = CODE_BLOCKED
```

## 2. Shared exact algebra and serialization

All coefficients belong to

\[
\mathcal A=\mathbb Q(\sqrt 2,i)
=\{a+b\sqrt2+i(c+d\sqrt2):a,b,c,d\in\mathbb Q\}.
\]

The owner representation is exactly four `fractions.Fraction` values in the
order `(a,b,c,d)`.  A canonical scalar serialization is a JSON array of four
`[numerator, positive_denominator]` arrays with no float conversion.  Addition,
subtraction, multiplication, equality, zero deletion, terminal interning, and
sorting all use these exact values.  No magnitude tolerance, coefficient
normalization, weighted/complemented edge, or binary64 surrogate is allowed.

Every canonical JSON object in this qualification uses UTF-8 bytes from
`json.dumps(..., sort_keys=True, allow_nan=False, ensure_ascii=False,
separators=(",",":"))`, with no trailing line feed.  Reload rejects an
unreduced rational, a non-positive denominator, any alternate spelling of
zero, a float, or bytes that are not already canonical.  Scalar, key/map,
codec, event/relation, ADD node-table, factor/graph/domain/boundary, order,
proof, oracle, and report hashes all use this one rule.

An independent SymPy 1.14.0 oracle may translate a scalar to
`a+b*sqrt(2)+I*(c+d*sqrt(2))`, but SymPy's internal algebraic-number encoding is
not the owner serialization.  The report must bind both the owner algebra test
history and the independent-oracle history.

## 3. Pair recurrence qualification fixture

### 3.1 Key and codec

The canonical key is

```text
(L.x, L.z, R.x, R.z, latent_m, frame_f, record_prefix)
```

where all Pauli/frame/Record coordinates are bits, `latent_m` is `-1` or `+1`,
and `record_prefix` is either `()` or `(d0,)`.  Ket/left and bra/right are never
exchangeable.  The injective bit codec is

```text
L.x, L.z, R.x, R.z, m_bit, frame_f, then d0 when emitted
m_bit = 0 for -1; m_bit = 1 for +1
```

The qualification suite separately includes key pairs differing only in each
of `L`, `R`, `m`, `frame_f`, and `d0`; their encodings must be distinct.  A
missing field, left/right exchange, reachable-state ordinal, or changed order
must fail the frozen codec identity rather than silently define another owner.

These one-bit labels deliberately qualify only the generic exact algebra,
canonical-key, and recurrence mechanics.  They use trivial rank-zero coset
bases and do not qualify nontrivial stabilizer-coset RREF canonicalization,
circuit-derived frame lowering, or any target QEC key builder.

### 3.2 Initial map and event E1

At checkpoint `j=0`, for each `m in {-1,+1}`,

```text
A0[(0,0,0,0,m,0,())] = 1/2
```

and every other valid or padded code maps to exact zero.

Event `E1_BRANCH` maps each initial key to four keys.  The following five-bit
patterns list `(L.x,L.z,R.x,R.z,frame_f)`; `m` is preserved and the Record is
still empty:

| label | pattern | transition multiplier | resulting A1 coefficient |
|---|---|---|---|
| `a_m` | `10000` | `1` | `1/2` |
| `b_m` | `01101` | `sqrt(2)/2` | `sqrt(2)/4` |
| `c_m` | `11011` | `i` | `i/2` |
| `d_m` | `00110` | `-i*sqrt(2)/2` | `-i*sqrt(2)/4` |

Thus `|support(A1)|=8`.

### 3.3 Event E2, exact cancellation, and long tail

Freeze `delta=2^-40`.  For each preserved `m`, define

```text
y_m = (1,0,1,0,m,1-m_bit,(m_bit,))
z_m = (0,1,0,1,m,m_bit,(1-m_bit,))
```

Event `E2_INTERFERE_AND_EMIT` has exactly these rows:

| input | output | multiplier |
|---|---|---|
| `a_m` | `y_m` | `1` |
| `b_m` | `y_m` | `-sqrt(2) + delta` |
| `c_m` | `z_m` | `1` |
| `d_m` | `z_m` | `sqrt(2)` |

Therefore, for each `m`,

\[
A_2(y_m)=\frac12+\frac{\sqrt2}{4}
(-\sqrt2+2^{-40})=\frac{\sqrt2}{2^{42}},
\qquad
A_2(z_m)=\frac i2-\frac{i\sqrt2}{4}\sqrt2=0.
\]

The tail is strictly nonzero and has magnitude below `1e-12`; the `z_m` terms
are exact algebraic zeros and must be deleted.  The frozen support history is

```text
[2, 8, 2]
n_pauli_pair_states_peak_micro = 8
peak_event = E1_BRANCH
```

Transition-row ordering is not semantic.  Reversing all row lists must leave
every checkpoint map and canonical hash unchanged.

## 4. Dynamic exact ADD qualification fixture

The dynamic ADD owns the same total functions `A0,A1,A2` and the same codec
orders.  Invalid and padded codes map to the one exact zero terminal.

At each checkpoint:

- one terminal is interned per distinct exact scalar;
- an internal node is `(level,low,high)`;
- equal children reduce to the child;
- every other identical tuple is unique-table merged;
- the root is marked, all unreachable nodes and caches are discarded, and
  canonical IDs are reassigned with terminals sorted by exact scalar bytes,
  then internal nodes sorted at descending levels by child IDs;
- the count includes every reachable internal and terminal node, including the
  root; an all-zero function has one node.

The dynamic interface must have the semantic shape

```text
advance(root, input_codec, output_codec, exact_transition_relation_root)
    -> canonical_reachable_root_and_table
```

Before `advance`, the finite relation clauses are compiled into an exact ADD
without consulting the current root.  The combined relation order is exactly
all input-codec bits followed by all output-codec bits: `6+6` levels for E1 and
`6+7` levels for E2.  The combined order and canonical reachable relation table
are hash-bound.
`advance` must lift the current root, multiply it by that relation, sum-abstract
every input bit, rename the output levels, reduce exactly, retain only nodes
reachable from the new root, and canonically renumber.  It must not accept,
call, iterate, or first materialize a sparse map, nonzero-assignment iterator,
or pair frontier.  The test suite poisons the pair-owner and sparse-export entry
points while running the ADD owner.

`advance` and every transitive owner helper must operate recursively on an
opaque root/node table.  They may not call a bulk truth-table/evaluate-all
operation, enumerate every code, or materialize a dictionary keyed by complete
bit assignments, canonical pair keys, or nonzero frontier states.  Recursive
memo tables, unique tables, and canonical node-ID maps are allowed, but may
never be exposed or iterated as a frontier.  The relation compiler may enumerate
only the frozen literal relation clauses and is call-spied to prove it does not
read the current root.  Public-call spies plus an AST guard enforce recursive
node-table multiply and sum-abstraction and reject forbidden bulk or sparse
paths.

The hand-derived reduced tables have these values:

| checkpoint | internal | terminals | total |
|---|---:|---:|---:|
| `A0` | 5 | 2 | 7 |
| `A1` | 15 | 5 | 20 |
| `A2` | 9 | 2 | 11 |

Hence

```text
n_exact_pair_add_nodes_history_micro = [7, 20, 11]
n_exact_pair_add_nodes_peak_micro = 20
peak_event = E1_BRANCH
```

The final count `11` is intentionally not the peak.  A tolerance merger that
maps `sqrt(2)/2^42` to zero would instead collapse `A2` to the one-node zero
function and must fail.  Reversed relation-row order must preserve root, table,
history, and peak hashes.  A final Record-PMF MTBDD, raw recursion count, or
sparse-frontier serialization is not accepted by this owner.

As a fixed-order corruption, the `A1` function under the ineligible order
`L.x,R.x,L.z,R.z,m,frame_f` has 13 internal plus 5 terminal nodes, total 18;
it must not be accepted in place of the frozen total 20.

At every checkpoint, an independent sparse recurrence and an exhaustive
truth-table evaluator must agree exactly with ADD evaluation on every bit code.
Only the tests may perform that exhaustive comparison.

## 5. Retained-boundary TN qualification fixture

### 5.1 Frozen graph

This fixture qualifies only the generic graph/metric/certificate owner; it does
not qualify the target QEC factor builder.

Eliminable indices are

```text
I = (d0, d1, c0, c1, d2)
```

and non-eliminable output indices are

```text
O = (o0, o1)
```

Each output has an explicit unary `KEEP:o0` or `KEEP:o1` factor.  All remaining
factors are binary, with scopes

```text
d0-d1, d0-c1, d0-o0,
d1-d2, d1-o1,
c0-c1, c0-d2, c0-o1,
c1-o1,
d2-o0
```

Domain sizes are

```text
d0=4, d1=4, d2=4,
c0=2, c1=2, o0=2, o1=2.
```

Thus the log2 weights are two on density indices `d0,d1,d2` and one on every
classical/Record index.  `w0=1`, while the largest initial log2 factor capacity
is `lambda0=4`.

Boundary indices must never appear in an elimination order.  Removing a KEEP
factor, eliminating a boundary vertex, changing an incidence/domain, fusing
parallel identities, or accepting a heuristic value is a schema failure.

### 5.2 Exact metrics and certificates

Replay filled-graph elimination exactly as in Section 2.4 of the active census
preregistration.  Unweighted width and mixed-domain bucket burden are optimized
independently.

The predicted exact optima are:

```text
record_boundary_constrained_induced_width_micro = 3
lexicographically_selected_unweighted_order = (d1,c0,c1,d0,d2)
that order's (width, lambda) = (3,7)

tn_record_boundary_peak_dense_entries_log2_micro = 6
tn_record_boundary_peak_dense_entries_micro = 64
lexicographically_selected_weighted_order = (d0,c1,d2,d1,c0)
that order's (width, lambda) = (4,6)
```

There are predicted to be 12 unweighted-optimal orders and 16 weighted-optimal
orders, with empty intersection.  An independent `5! = 120` permutation oracle
must confirm all four statements.

The headline owner uses complete subset DP over the 32 subsets of `I`.  For
each subset it serializes the exact optimal value and lexicographically selected
order.  The complete table is the lower/equality proof; the selected full order
is the upper witness.  A separate verifier reconstructs every torso, checks
every recurrence cell and tie-break, replays the final order, and binds graph,
factor, domain, boundary, order, and proof hashes.  An order without this checked
table is only an upper bound and must not be reported `EXACT`.

With subset-mask bit order `(d0,d1,c0,c1,d2)`, freeze the tie-break alphabet as
the same ordinal order `d0 < d1 < c0 < c1 < d2`.  Every subset cell chooses the
lexicographically smallest complete prefix under these ordinals among equal
values.  The predicted DP value arrays
for masks `0..31` are frozen as

```text
D_width =
[1,3,3,4,3,3,3,4,
 3,4,3,4,3,4,3,3,
 3,3,4,4,4,4,4,4,
 3,4,4,4,4,4,3,3]

D_lambda =
[4,6,7,7,5,6,7,7,
 5,6,7,7,6,7,7,7,
 6,6,7,6,6,6,7,6,
 6,6,7,6,7,6,7,6]
```

Deleting either edge `d0-d1` or `d1-d2`, or changing `d1` from domain four to
domain two, is predicted to lower the weighted optimum from six to five.  These
are mandatory corruption controls.  Clamping/removing both KEEP vertices would
instead produce the ineligible fixed-output pair `(width,lambda)=(2,5)`;
changing `c0` from domain two to four raises the weighted optimum to seven.
Deleting only a unary KEEP factor does not change the primal graph and must fail
schema validation before any metric is emitted; the `(2,5)` diagnostic requires
explicitly clamping/removing `o0,o1` and their incident scopes.

## 6. TDD acceptance sequence

Implementation proceeds in three red-green slices.  Each test observes only a
public research-script interface.

1. Pair owner: exact algebra, key/codec witnesses, maps, support history, tail,
   zero deletion, row-order metamorphism, and SymPy agreement.
2. ADD owner: direct-root execution with poisoned pair entry point, exact
   truth-table agreement, canonical counts/tables/hashes, fixed order, row-order
   metamorphism, tiny-terminal survival, and peak-versus-final separation.
3. TN owner: graph/KEEP validation, replay, separate subset DPs, proof checker,
   brute-force agreement, disjoint optimum sets, and edge/domain/proof
   corruptions.

Additional fail-closed tests must reject non-finite or floating coefficients,
non-positive rational denominators, duplicate/non-injective codec fields,
unknown variables, invalid domains, incomplete elimination orders, and any
boundary vertex in an order.

All independent paths are implementation-separated.  The SymPy sparse and
truth-table oracle reconstructs the literal pair/ADD fixture without importing
or calling owner transition, codec, serialization, or hash helpers.  The TN
proof verifier and the 120-order oracle independently reconstruct literal
factor scopes/domains/KEEP vertices and do not import or call owner torso,
fill, replay, objective, serialization, or hash helpers.  Equality is checked
only after both sides have produced their independently serialized values.

## 7. Required report and disposition

The owner CLI emits canonical finite JSON and revalidates it after reload.  It
must bind:

- this active preregistration path and SHA-256;
- source/test SHA-256 values and exact Python/dependency versions;
- every fixture, codec, event, graph, factor, domain, boundary, history, table,
  order, proof, and independent-oracle hash;
- explicit `MICRO_QUALIFICATION_ONLY` scope on all three owner results;
- the unchanged target unavailable reasons and `solver_permission=CODE_BLOCKED`.

Passing status is exactly

```text
report_status = VALID_MINIMAL_EXACT_OWNER_QUALIFICATION_CODE_BLOCKED
pair_micro_owner = QUALIFIED
dynamic_add_micro_owner = QUALIFIED
retained_boundary_tn_micro_owner = QUALIFIED
target_pair_owner = UNAVAILABLE/NO_TARGET_QEC_PAIR_LOWERING
target_dynamic_add_owner = UNAVAILABLE/NO_TARGET_QEC_DYNAMIC_ADD_LOWERING
target_retained_boundary_tn_owner = UNAVAILABLE/NO_TARGET_QEC_TN_LOWERING
solver_permission = CODE_BLOCKED
```

Any mismatch, missing proof, proxy field, or failed corruption control is a
fail-closed qualification failure.  No route is killed or promoted by this
microfixture.
