# No-cutoff structure census — Pre-Registration

Status: **ACTIVE PRE-REGISTRATION, CODE_BLOCKED**, 2026-08-03.  Predictions and
decision rules below were written before any target census execution.  The
linked literature packet is closed, both new source notes passed independent
source-only review, and independent design review passed the exact
pre-activation SHA-256
`c8aa9cc1dbd37007d8c70b76249964985cd4f9ba25b0cf3f4187b7e221358d40`.
Activation authorizes only the bounded census test/instrument outside `src/**`;
new solver work remains `CODE_BLOCKED`.  Known paper benchmark cells are
calibration values, never held-out findings.

## -1. Question charter (importance × attackability)

- **Decision and consequence.** Determine which exact representation candidate
  first becomes structurally untenable for a complete multi-round QEC Record
  under persistent coherent declared error.  The reusable outputs are a neutral
  fixture, a route-qualified metric schema, an executable falsifier, and a
  fail-closed `CODE_BLOCKED` gate.  No new solver is authorized.
- **Plausible attack and independent anchor.** Clifft and SymFT expose separate
  compile-time active widths without allocating the monolithic dense vector.
  Clifft owns the headline frame burden; SymFT's monolithic burden and current
  product-component capacities are route-qualified diagnostics. Exact integer pair/DD
  counts and treewidth certificates can in principle be collected without
  numerical coefficient truncation.  A tiny exact-SymPy tracer will qualify
  algebraic-zero, full-law TV, and decision-diagram accounting independently of
  the target adapters.
- **Alternative formulations and invariants.** The same neutral physical
  definition must be expressible as (i) two fixed-sign circuit branches mixed
  with exact weight `1/2`, and (ii) one latent variable with deterministic
  transition `m_{r+1}=m_r`.  Both must give the same complete Record law.
  Route counts may differ, but the detector/observable support, circuit hashes,
  latent marginal, and full law must agree.
- **Kill condition.** Apply the frozen finite-grid rule to the representation
  burden—not directly to a width.  Structure and faithfulness have separate
  dispositions: an exact or certified burden meeting all three growth
  inequalities is `KILL_STRUCTURE` for that pinned representation only, while
  a missing/censored/proxy burden is `INDETERMINATE`.  The target-law
  certification is reported independently and keeps `solver_permission` at
  `CODE_BLOCKED`; structural rejection neither certifies a Record law nor kills
  every algorithm in the architecture family.
- **Selection warning.** Existing `k_max` values are known calibration data.
  The routes were selected before this run because they charge for distinct
  structures: dense active coordinates, sparse Pauli pairs, repeated Record
  subfunctions, and factor-graph separators.

## 0. Grounding ledger

| sub-axis / mechanism | mechanism paper | observable paper | reading note | in-repo code (reuse) |
|---|---|---|---|---|
| Exact active-coordinate route | Clifft arXiv:2604.27058v2; SymFT arXiv:2607.28600v1 | same sources define route-qualified peak active width and general `2^k` cost; SymFT Sec. 6 defines its current component backend | `chase_labib_clifft_2604.27058v2_source_review.md`; `fang_lou_li_symft_2607.28600v1_source_review.md` | pinned pristine external compilers; project adapters to be added after activation |
| Tensor contraction width | Markov–Shi arXiv:quant-ph/0511069v4 | Secs. 2–4 define treewidth, elimination width, contraction complexity, and exponential-width cost; Sec. 6 bounds adaptive sequential sampling | `markov_shi_tensor_contraction_quant_ph_0511069v4_source_review.md` | NetworkX heuristic decompositions may supply diagnostics only; no exact retained-Record owner exists |
| Full joint Record TV | repository scientific contract | registered field-standard total variation convention | `docs/METRICS.md` | `certify.core.total_variation` convention; independent exact tracer will not import it |
| Persistent latent law | controlled project mechanism; no device magnitude claimed | complete detector/observable Record | closure packet and `CONTEXT.md` Axis-2 boundary | reuse `RTNSource(gamma_per_cycle=0)` semantics as a pattern, not its evaluator-only payload |
| Exact pair and DD counts | no selected paper defines the proposed complete-Record meters | project-defined metric debt, frozen below | closure packet | no current owner; stubs must report `UNAVAILABLE`, never a proxy |

Literature packet:
`docs/simulator_validation/NO_CUTOFF_STRUCTURE_CENSUS_LITERATURE_CLOSURE_2026-08-03.md`.

## 1. Controlled mechanism and target grid

### 1.1 Neutral QEC fixture

For every cell

```text
distance d in {3, 5}
rounds   R in {1, 3, 5, 7}
```

construct Stim **1.16.0**'s `surface_code:rotated_memory_z` circuit with only
`after_clifford_depolarization=0.001` enabled to enumerate declared error
locations.  In its canonical flattened text, replace each `DEPOLARIZE1` or
`DEPOLARIZE2` row by one `R_Z(a)` instruction on the identical ordered target
list; remove no ideal Clifford, reset, measurement, detector, or observable
instruction.  The depolarizing channel is a location scaffold and does not
remain in the target error model.  No reset-flip, measurement-flip, or
before-round stochastic noise is enabled.

The declared coherent primitive is frozen algebraically.  With `t=1/100`,

\[
c=\frac{1-t^2}{1+t^2}=\frac{9999}{10001},\qquad
s=\frac{2t}{1+t^2}=\frac{200}{10001},\qquad
U_{m,Z}=cI-i m sZ=e^{-i m\phi Z},\qquad
\phi=\operatorname{atan2}(s,c)=2\arctan(t).
\]

For the external convention `R_Z(a)=exp(-i*pi*a*Z/2)`, the exact conversion
chain is therefore

\[
U_{m,Z}=R_Z(m a),\qquad
a=\frac{2\phi}{\pi}=\frac{4\arctan(t)}{\pi}
  =\frac{2\operatorname{atan2}(s,c)}{\pi}.
\]

The rational pair, not a floating angle, owns the scientific fixture.  The
external circuit is a **binary64 structural shadow used only for compile-time
structure**; it is not an exact-rational equivalent Record law and cannot own
TV, pair, DD, or algebraic-zero claims.

Parser bytes are frozen rather than regenerated through the host `libm`:

| control | exact `t` | positive binary64 hex | unique parser decimal |
|---|---:|---|---|
| primary | `1/100` | `0x1.a13383a84979bp-7` | `0.012731971059633021` |
| nonzero invariance | `1/10^20` | `0x1.e1042c3d96d7fp-67` | `1.2732395447351627e-20` |
| inert | `0` | `0x0.0p+0` | `0` |

The negative branch is the same decimal prefixed by `-`, except that inert
`-0.0` is canonicalized to the bytes `0` and hex `0x0.0p+0`.  An independent
256-bit evaluation of `4*atan(t)/pi` must lie strictly inside the
round-to-nearest-ties-to-even interval of the frozen hex before use; parsing the
frozen decimal must reproduce that hex exactly.  Every report binds the
serializer source hash, CPython/SymPy/mpmath identities used for this check,
the parser identity, and the exact circuit bytes.  The primary value is
controlled, not calibrated, and is not asserted to reproduce the papers'
`R_Z(0.02)` benchmark circuit.

The canonical source bytes are
`str(circuit.flattened()).rstrip(LF)+LF`.  Build a site-map JSON array by
zero-based `enumerate(circuit.flattened())`, selecting exactly
`DEPOLARIZE1|DEPOLARIZE2` in encounter order.  Each entry has exactly

```text
instruction_index: the zero-based flattened instruction integer
source_gate: the exact instruction name
source_args: gate_args_copy() in order, each formatted with `.17g`
targets: targets_copy() in order, each required to be a qubit target and
         encoded by its integer `.value`
```

Encode that array with
`json.dumps(allow_nan=False,indent=2,sort_keys=True)+LF`; extra keys or target
normalization are forbidden.  All eight source/site/shadow identities are
frozen in
`NO_CUTOFF_STRUCTURE_CENSUS_FIXTURE_MANIFEST_2026-08-03.json`, whose SHA-256 is
`40474ca0beab8341d53bfa41da5438e052744bb83ae6af2632e1bfe273c53c74`.
The generator must reproduce that complete manifest before any adapter runs.
For exact rational `t=0`, omit every replacement `R_Z` row while retaining the
unchanged location/site manifest.  For **every** exact `t!=0`, including
`1/10^20`, emit every replacement row.  This numerator-equals-zero branch is
the only allowed magnitude-dependent generation rule and must never be widened
to a floating tolerance.

### 1.2 Persistent coherent declared error

At the start of a shot, draw one evaluator-only latent sign

\[
m\in\{-1,+1\},\qquad \Pr(m=-1)=\Pr(m=+1)=\tfrac12,
\]

and keep it fixed exactly:

\[
\Pr(m_{r+1}=m_r)=1
\]

for every round and every declared error location.  The exact declared error at
each scaffold target is `U_(m,Z)` above.  The compile-only shadow contains both
`R_Z(+a)` and `R_Z(-a)` circuit texts plus the exact mixture weight; an adapter
may not resample the sign per gate or use those binary64 texts as a probability
oracle.  The latent sign is evaluator truth and must not appear in
detector/observable output or estimator input.

This is a caller-declared error process.  It is not a bath Hamiltonian, reduced
dynamical map, process-tensor reconstruction, or claim about a device.

### 1.3 Record object

The target object is the chronological tuple of every declared detector bit
followed by the logical-observable bit in canonical Stim declaration order.
Raw measurement bits, selected branches, postselection survivors, states, and
DEMs are diagnostics or reductions and are not the target.

Known published cells `(3,1)`, `(3,3)`, `(5,1)`, and `(5,5)` are calibration
checks for the external positive-sign circuit family.  Because this fixture
removes the published stochastic reset/measurement/data errors, equality with
published counts is not assumed; any comparison must state the circuit hash.

## 2. Metric binding

Every target row contains all five metric families, each with a status from
`EXACT`, `CERTIFIED_INTERVAL`, `BOUNDS`, `UNAVAILABLE`, or
`CENSORED_RESOURCE`; the active-coordinate family contains separate Clifft and
SymFT observations. Missing keys, `NaN`, sentinel zero, and bare proxy fields
are schema failures.

### 2.1 Route-qualified operationalization of \(k_{\max}\)

- Headline `k_max_clifft_squeeze_no_peephole` is
  `max(program.active_k_history)` from pristine Clifft commit
  `2c1dfa6029c4f0573c499e938e9a88106a6801b3`, with the empty history defined as
  zero.  Its exact compile policy is `normalize_syndromes=False`, an explicit
  `HirPassManager` containing **only** `StatevectorSqueezePass`, and
  `bytecode_passes=None`.  The squeeze pass only commutes/reorders HIR
  operations; `PeepholeFusionPass` and every default/bytecode pass are absent.
  Its frozen route burden is
  `B_frame_clifft = 2 ** k_max_clifft_squeeze_no_peephole`; no `State`, sample,
  probability, or amplitude vector is constructed.  Require
  `len(active_k_history)==program.num_instructions` and
  `max(history,default=0)==program.peak_rank`.
- Clifft's public default optimizer is a **supplemental cutoff-contaminated
  diagnostic**, because the pinned `PeepholeFusionPass` demotes rotations within
  `1e-12` of selected angles.  It may be reported as
  `k_max_clifft_public_default_cutoff_contaminated` with source locators and
  `headline_eligible=false`, but it may not receive the primary/tiny
  invariance verdict or enter any structure disposition.
- Supplemental `k_max_symft` is the exact integer `max_active_qubits` from
  `symft_plan` at pristine SOFT/SymFT commit
  `bc9a8d2e33b1e03d411c4088f8255299c80a51eb`. Report
  `B_frame_symft_monolithic = 2 ** k_max_symft` only as the source's general
  monolithic burden. Also report the planner's selected component mode,
  component count, peak live/allocated component dimensions, and work
  estimates; do not use the monolithic burden to kill the whole SymFT route.
- Each identity includes positive/negative circuit hashes, external commit,
  compiler/planner options and pass-manifest/source hashes, instruction count,
  optimizer counters, and a hash
  of deterministic structural output with timings/RSS excluded. Both sign
  branches must return the same structural fields.
- The two widths are not interchangeable, and neither is an
  architecture-independent lower bound. They are two observations of the same
  active-coordinate hypothesis under different compilers.  A Clifft refusal at
  its compile-time `k>=60` guard or a SymFT refusal at its `k>=62` machine-index
  guard is `CENSORED_RESOURCE` with the exact guard receipt and no numeric
  headline, never a completed width.

### 2.2 One exact recurrence and sparse \(N_{\rm pair}\)

Freeze one hash-bound atomic event stream `e_1,...,e_T`: flattened
instructions are split into ordered scalar target events; each `DETECTOR`
declaration appends its folded detector bit, and the logical observable is
appended only at finalization.  At checkpoint `j`, after the event has fully
completed, define

\[
K_j=C^L_j\times C^R_j\times\{-1,+1\}\times F_j
    \times\{0,1\}^{r(j)},\qquad A_j:K_j\rightarrow\mathcal A,
\]

where `C^L`, `C^R`, and `F` are the canonical left/right Pauli cosets and
symbolic Clifford/measurement frame, and `r(j)` is the number of retained
Record bits emitted so far.  The exact transition is

\[
A_{j+1}(k')=\sum_k T_j(k',k)A_j(k),
\]

followed by the same frozen coset/frame canonicalization, exact coefficient
addition, and exact algebraic-zero deletion.  For this fixture
`A = Q(sqrt(2), i)`; canonical coefficient bytes are four reduced rationals for
`a+b*sqrt(2)+i(c+d*sqrt(2))`, each with positive denominator.  Leaving this
field is an amendment/schema failure, never permission to fall back to float.

The sparse headline is

```text
n_pauli_pair_states_peak = max_j |support(A_j)|
B_pair = n_pauli_pair_states_peak
```

after every atomic event, not merely after a detector declaration.  Ket/bra
order is never exchanged.  A future owner must bind the canonical RREF coset
bases and frame manifest described below.  No floating magnitude test is
permitted.  SOFT `r_max`, perturbative order, Pauli weight, raw branch count,
and the existing BLP quantity named `N_pair` are forbidden substitutes.  There
is currently no owner, so target rows must say
`UNAVAILABLE/NO_EXACT_PAIR_OWNER` until a reviewed route amendment exists.

### 2.3 `n_exact_pair_add_nodes_peak` — operationalization of \(N_{\rm DD}\)

The headline DD represents the **same dynamic coefficient map `A_j`**, not only
the final Record PMF.  Each checkpoint has a reachability-independent injective
bit codec for every canonical key.  Invalid and padded codes totalize to the
exact zero terminal.  The primary bit order is

```text
L.x[q increasing], L.z[q increasing],
R.x[q increasing], R.z[q increasing],
latent m (0=-1, 1=+1),
canonical frame fields in manifest path/row-major order,
d_0, ..., d_(r(j)-1), then o only at finalization
```

Pauli representatives use deterministic GF(2) RREF with columns
`x_0,...,x_(n-1),z_0,...,z_(n-1)` and leftmost pivots; global phase is excluded.
The frame codec is fixed-width, injective, padded from a circuit-derived layout,
and hash-bound in a codec manifest.  Discovery-order/reachable-state ordinals,
coefficient-dependent encodings, and sparse-frontier dictionaries are
forbidden.  The identity binds the event stream, qubit order, every checkpoint
RREF basis, frame layout, and variable order.

At checkpoint `j`, build the unique reduced ordered exact ADD for this total
function.  There is one interned terminal per exact `A` value and exactly one
zero terminal; tiny nonzero values remain distinct.  An internal node is the
tuple `(level, low_id, high_id)`; identical children reduce to that child, and
all other exact tuples share one unique-table entry.  Weighted/complemented
edges, gauges, normalization, and tolerance merging are forbidden.  After each
event, complete exact reduction, mark from the single root, discard all
unreachable nodes/caches/old roots, and canonically renumber bottom-up:
terminals sort by exact coefficient bytes, then nodes at descending levels sort
by child IDs.

Define `n_exact_pair_add_nodes(j)` as all reachable internal and terminal nodes
after that canonical GC, root included; the all-zero function has count one.
The headline and burden are

```text
n_exact_pair_add_nodes_peak = max_(j=0,...,T) n_exact_pair_add_nodes(j)
B_DD = n_exact_pair_add_nodes_peak
```

Report internal/terminal splits, the peak event ID, full-history hash, and
codec/order/node-table hashes.  Allocator high-water, apply caches, transition
relation nodes, simultaneous old/new roots, coefficient bit length, and wall
time are implementation diagnostics, not this semantic structural count.  The
direct backend consumes only its current root, codec, and exact event through
exact substitution/relational product and sum-abstraction; it may not enumerate
or first materialize the sparse frontier.  A test poisons sparse iteration.

After finalization, a separate readout/trace functional may marginalize the
non-Record state and build a chronological Record-only exact MTBDD.  Its name is
`n_record_pmf_mtbdd_nodes_final`; it must reconstruct a nonnegative normalized
PMF and bind its order/table/PMF hashes.  It is a supplemental output-compression
diagnostic, not \(N_{\rm DD}\), not a direct pair backend, and cannot drive the
structure gate.  Existing `probability_node_count`, a final PMF MTBDD, an
unreduced tree, tolerance-merged terminals, or another variable order may never
populate the headline.  There is currently no target owner, so emit
`UNAVAILABLE/NO_EXACT_DYNAMIC_ADD_OWNER`.

### 2.4 Retained-boundary tensor metric — operationalization of \(tw\)

The complete-Record route is a **factorized retained-boundary** network
`G_boundary`, not a materialized rank-`n_record_bits` output tensor and not a
fixed-Record scalar.  Density-wire indices have domain size four; every
classical raw/sign/parity/Record index has domain size two.  A labelled
degree-one `KEEP` stub terminates every detector/observable leg, whose index
vertex belongs to the non-eliminable boundary set `O`.

The local lowering is frozen in the computational basis.  A density index is
the row-major pair `(ket,bra)` encoded as `2*ket+bra`.  Every declared qubit has
an initial `|0><0|` unary factor and a final trace factor
`1[ket=bra]`.  Expand `R`, `H`, `M`, `MR`, and each replacement `R_Z` target in
listed order, and expand `CX` as consecutive listed `(control,target)` pairs;
`QUBIT_COORDS` and `TICK` are hash-bound event markers but add no tensor.
The only allowed local tensors are:

- `H` and control-first `CX` computational-basis unitaries lowered as the exact
  density superoperator
  `S[(a,b),(c,d)] = U[a,c] * conjugate(U[b,d])`, with two-qubit basis order
  `|00>,|01>,|10>,|11>`;
- the coherent controlled channel using
  `U_m=diag(c-i*m*s,c+i*m*s)` in the same rule;
- `R(q_in,q_out)=1[q_in.ket=q_in.bra] * 1[q_out=(0,0)]`;
- `M(q_in,b,q_out)=1[q_in=(b,b)] * 1[q_out=(b,b)]`;
- `MR(q_in,b,q_out)=1[q_in=(b,b)] * 1[q_out=(0,0)]`.

These definitions retain measurement collapse, reset trace, and every live
post-measurement wire.  Encountering any other operation is
`UNAVAILABLE/UNSUPPORTED_CANONICAL_TN_LOWERING`, never permission to silently
drop it or infer a tensor from an external compiler.

The factorization itself is part of the route identity:

- raw-measurement reuse is a chronological degree-three COPY chain whose
  consumers sort by `(Record declaration ordinal, operand ordinal)`: for
  producer bit `r_0` and `n>0` consumers, factor `j` is
  `COPY(r_(j-1), consumer_j, r_j)=1[all three equal]`, and `r_n` ends in an
  all-ones unary factor.  With no consumer, `r_0` goes directly to that unary
  terminal; the one-consumer case still has one ternary COPY factor;
- each detector/observable parity starts from an explicit zero accumulator and
  uses a fixed left-associated ternary-XOR chain
  `XOR(acc_previous, raw_bit, acc_next)=1[acc_next=acc_previous xor raw_bit]` in
  resolved absolute Stim-record order; multiple `OBSERVABLE_INCLUDE(0)` rows
  feed the same final accumulator, and any other observable index is rejected;
- persistent sign is an MPO-like chronological equality chain over every
  elementary coherent-error occurrence in flattened instruction/target order.
  With prior `pi(z_0)=1/2`, occurrence `j` contains
  `C_j(z_(j-1), mu_j, z_j)=1[z_(j-1)=mu_j=z_j]` and a controlled density channel
  `E_j(q_in,q_out,mu_j)`, followed by a terminal all-ones factor on `z_L`.

This contracts exactly to the half-weighted two-fixed-sign mixture.  Replacing
the chain by one high-degree sign variable, fusing COPY tensors, pre-unifying
indices, reordering occurrences, or value-pruning `t=0` defines a different
route/hash.

Build the labelled index primal graph `P`: vertices are individual indices
(parallel indices stay distinct), and two vertices are adjacent exactly when
they occur on one tensor.  Let \(I=V(P)\setminus O\).  For an order `pi` of
**only** `I`,
replay filled-graph elimination.  Immediately before eliminating `x`, let
`N_pi(x)` be its current neighbors and let the bucket scope be
`S_pi(x)={x} union N_pi(x)`; clique `N_pi(x)` and delete `x`.  Boundary vertices
are never eliminated.  At termination the surviving factors over subsets of
`O` remain a product; multiplying them into one dense joint tensor is a
different, explicitly materialized route with a `2**|O|` terminal burden.

With `w_0` the maximum initial tensor scope size minus one, define the
project-specific requested-width metric

\[
\operatorname{tw}^{\rm project}_{\partial}
=\min_{\pi\in\operatorname{Perm}(I)}
 \max\!\left(w_0,\max_{x\in I}|N_\pi(x)|\right).
\]

Its schema name is `record_boundary_constrained_induced_width`; the display
alias `tw_record_boundary_constrained_project` may be used, but bare `tw` may
not.  This is not ordinary `tw(P)`, not `cc(G)`, and not Markov--Shi's
all-edge-contraction identity.

For the mixed-domain burden, set `a(v)=log2(domain_size(v))`, hence two for a
density index and one for a classical index.  Let

\[
\lambda_0=\max_{F\ {\mathrm{initial}}}\sum_{v\in\operatorname{scope}(F)}a(v),
\qquad
\lambda_\partial^*=\min_\pi\max\!\left(
\lambda_0,\max_{x\in I}\sum_{v\in S_\pi(x)}a(v)\right),
\]

and freeze

```text
tn_record_boundary_peak_dense_entries_log2 = lambda_boundary_star
B_TN = tn_record_boundary_peak_dense_entries = 2 ** lambda_boundary_star
terminal_record_representation = "factorized_boundary_factors"
```

The unweighted and weighted optima are minimized separately because their
orders can differ.  The growth gate uses `B_TN`, never `2**raw_tw`.  This meter
counts exact dense bucket-table capacity; coefficient bit complexity and a
sparsity-aware tensor route are out of scope.

An `EXACT` value requires a replayable minimizing order and a matching checked
lower-bound proof.  A complete subset-DP table is acceptable: after eliminating
`S subset I`, form the torso graph `H_S`; the recurrence minimizes the maximum
of the prior DP value and the exact next bucket weight (and analogously neighbor
count for the unweighted width).  An order alone is only an upper bound.
Graph/factor/domain/boundary/sign-chain hashes, both order hashes, and both proof
hashes are mandatory.  NetworkX 3.6.1 min-fill/min-degree results are optional
upper-bound diagnostics only.  A separate source-backed diagnostic
`tw_line_fixed_record_scalar` may clamp every Record leg and use Markov--Shi;
it can never populate the complete-Record headline or burden.  Until the
canonical graph builder and matching certificates exist, emit
`UNAVAILABLE/NO_CANONICAL_RETAINED_RECORD_TN_OWNER`.

### 2.5 `delta_tv_cert` — operationalization of \(\Delta_{\rm TV}^{\rm cert}\)

Use the registered complete joint Record convention

\[
\Delta_{\rm TV}(p,q)=\frac12\sum_x|p(x)-q(x)|
\]

over the entire declared detector/observable support.  Report either an exact
algebraic value or a certified interval with a derivation-bound hash.  One side
must independently reconstruct the neutral schedule and XOR folds; two lanes
consuming one compiler-sealed payload are not independent.  Sample estimates,
marginal TV, selected-branch errors, state fidelity, discarded weight, DEM
distance, or `0` inserted for missing data are forbidden.

The current d=3/5 grid has no independent complete-law oracle.  Every target row
therefore must emit `UNAVAILABLE/UNANCHORED_FULL_RECORD`, which is itself a
passing fail-closed schema result and leaves every route `CODE_BLOCKED`.

## 2a. Predicted observables

These are prospective class-(b)/(c) architecture bets, not literature facts.

| route | preferred hypothesis | strongest rival | discriminating observation |
|---|---|---|---|
| active coordinates | repeated coherent rotations promote active coordinates faster than syndrome measurements demote them, so `B_frame_clifft` is exponential-consistent in rounds | periodic measurements produce a bounded or cycling active set | exact Clifft history and three equal-spacing burden ratios; separate SymFT monolithic/component diagnostics |
| Pauli pairs | preserving every nonzero long-tail interference term makes `B_pair` grow exponential-consistently | exact stabilizer-coset merging collapses repeated coherent paths | exact canonical prefix counts with a no-threshold tiny-positive control |
| dynamic exact pair ADD | repeated rounds and one persistent latent sign create reusable state subfunctions, keeping `B_DD` sub-exponential on the grid | chronological Record retention and nonidentical exact coefficients defeat reduction | canonical live-node peak after every event; final Record PMF MTBDD is supplemental only |
| retained-boundary tensor factors | spatial locality, resets, and factorized output boundary keep exact weighted buckets controlled | temporal output reuse and the persistent-sign equality chain widen buckets with rounds | certified project boundary width and mixed-domain peak dense entries; fixed-Record or heuristic widths are ineligible |
| correctness | exact routes have zero complete-law TV up to a certified arithmetic interval | shared compiler/fold bugs let two wrong lanes agree | independent construction plus detector-fold corruption |

No route is preregistered as the winner.  `UNAVAILABLE` is an expected current
outcome for `N_pair`, dynamic `N_DD`, the retained-boundary tensor metrics, and
target-grid `delta_tv_cert`; it is not evidence for good scaling.

## 2b. Disconfirmation surface and growth rule

For one pinned route and one fixed distance with burdens at rounds
`(1,3,5,7)`, define

\[
q_1=B_3/B_1,\quad q_2=B_5/B_3,\quad q_3=B_7/B_5.
\]

The route is **finite-grid exponential-consistent** at fixed distance iff all
three exact ratios are at least `2`.  With certified intervals, transition
`R -> R+2` is proved doubling only when

\[
L(B_{R+2})\ge 2U(B_R),
\]

and is proved non-doubling only when

\[
U(B_{R+2})<2L(B_R).
\]

Any overlap is indeterminate.  For the tensor burden `B_TN=2**lambda`, the
first inequality is evaluated exactly as
`lambda_lower(next) >= lambda_upper(previous)+1`.  Record the first proved
doubling transition as descriptive metadata, but evaluate disposition only
after round 7.  This is a finite-grid representation gate, not an asymptotic
theorem; a polynomial can mimic these ratios.

Structure eligibility requires only:

1. every input to that route burden is identity/version qualified and `EXACT`
   or a deterministic `CERTIFIED_INTERVAL` that decides the inequality;
2. the metric-specific exact-small qualification and corruption tripwires pass;
3. no required row is `BOUNDS`, `CENSORED_RESOURCE`, `UNAVAILABLE`, sampled, or
   populated by a forbidden proxy.

The three independent output axes are frozen as

```text
structure_disposition =
    KILL_STRUCTURE | NOT_KILLED_ON_FROZEN_GRID | INDETERMINATE
faithfulness_disposition = CERTIFIED | REFUTED | INDETERMINATE | UNAVAILABLE
certification_verdict = PASS | FAIL | UNANCHORED
solver_permission = CODE_BLOCKED
```

`KILL_STRUCTURE` means all three doubling inequalities are proved on the
complete slice and rejects only that pinned representation.  If every input is
eligible and at least one transition is proved non-doubling, report
`NOT_KILLED_ON_FROZEN_GRID`, never “scalable”.  Otherwise—including a missing,
censored, upper-bound-only, or interval-overlap row—report `INDETERMINATE`.
Target `delta_tv_cert` does **not** veto this structural disposition; it owns
`faithfulness_disposition` instead.  `CERTIFIED` requires exact zero, or a certified
interval wholly inside a nonzero numerical band frozen by a future amendment.
Exact positive TV or a certified lower bound above that band is `REFUTED`; an
interval overlapping the acceptance boundary is `INDETERMINATE`; absence of an
independent complete-law oracle is `UNAVAILABLE`.  Merely containing zero is
not certification.  The binding `docs/FAITHFULNESS_PROTOCOL.md` verdict maps a
fully controlled exact-zero result to `PASS`, an exact invariant/control
failure to `FAIL`, and reference absence/infeasibility to `UNANCHORED` **only
when no feasible independent reference exists**.  A
reference that runs but yields an overlapping interval, `BOUNDS`, or a resource
censor is project-`INDETERMINATE`; the binding protocol has no inconclusive
verdict for it.  Such a target-TV outcome is therefore forbidden from the v1
claim-bearing report and produces a separate incomplete/non-claim failure
receipt with no `certification_verdict` until the protocol is amended.  It may
not be relabelled `UNANCHORED`.  No nonzero target band is registered in this
version, so only exact zero could certify.  Because the frozen run has no
feasible target oracle at all, its mandatory pair is
`faithfulness_disposition=UNAVAILABLE` and
`certification_verdict=UNANCHORED`, and `solver_permission` remains
`CODE_BLOCKED` even if a representation is structurally killed or not killed.

The aggregate route disposition is `KILL_STRUCTURE` if either complete
fixed-distance slice is killed; otherwise it is not-killed only if both slices
are eligible and not killed, and is indeterminate in every other case.  The
earliest transition may rank already-killed routes descriptively but cannot
replace the all-three gate.  Comparing only `d=3` with `d=5` cannot trigger a
round-growth disposition.  SymFT's monolithic diagnostic is never an aggregate
kill meter for its product-component backend.

### 2c. Fail-closed report schema

The canonical report schema is
`error_coupling_simulator.external.no_cutoff_structure_census.v1`.  Its cells
are exactly the eight `(distance, rounds)` pairs in lexicographic order and each
cell has exactly these five headline family keys:

```text
k_max
n_pair
n_dd
tw
delta_tv_cert
```

`k_max` contains separately qualified `clifft` and `symft` observations;
Clifft alone supplies the headline frame burden.  `tw` is only the family
container: its named values must be
`record_boundary_constrained_induced_width` and
`tn_record_boundary_peak_dense_entries[_log2]`, never a bare scalar called
`tw`.  Every leaf carries a status and route identity.  `EXACT` carries an
exact integer or canonical algebraic encoding; `CERTIFIED_INTERVAL` carries
exact lower/upper values and a derivation hash; `BOUNDS` is diagnostic and
ineligible.  `UNAVAILABLE` carries a nonempty reason code and
`CENSORED_RESOURCE` carries a reason plus resource receipt.  The latter two
statuses forbid `value`, `lower`, `upper`, `estimate`, `NaN`, and sentinel zero.

The report also binds the active preregistration path/SHA-256, exact fixture and
shadow hashes, external source/build/runtime identities, per-distance and
aggregate structure dispositions, `faithfulness_disposition`, the binding
`certification_verdict`, and `solver_permission`.  Evaluator-truth names such as `latent_sign`,
`selected_sign`, or `process_truth` are forbidden recursively.  Headline proxy
names `r_max`, `probability_node_count`, `tw_exact`, state fidelity, discarded
weight, DEM distance, and sampled TV are schema failures.  A qualified
heuristic width or final-PMF MTBDD may appear only below `supplemental` with
`headline_eligible=false`; no validator promotion path exists.

The current mandatory missing-owner reasons are
`NO_EXACT_PAIR_OWNER`, `NO_EXACT_DYNAMIC_ADD_OWNER`,
`NO_CANONICAL_RETAINED_RECORD_TN_OWNER`, and
`UNANCHORED_FULL_RECORD`.  A failed external preflight uses an explicit
adapter/provenance reason; a resource limit uses `CENSORED_RESOURCE`, never a
partial count.  Missing cell/family/status/identity fields, extra target cells,
duplicate cells, noncanonical order, or a numeric unavailable field invalidate
the whole report before any disposition is read.

`structure_dispositions` has exactly four route keys:

```text
clifft_frame
exact_pair
dynamic_add
retained_boundary_tn
```

Each route contains exactly `distance_3`, `distance_5`, and `aggregate`; each
entry carries the frozen disposition enum plus its burden identity and
decidable-transition evidence (or explicit indeterminate reasons).  SymFT has
no structure-disposition key: its monolithic and component observations remain
supplemental diagnostics and cannot be silently promoted.

## 3. Independent ground truth

- A test-only exact-SymPy tracer starts in `|0>`. Each round applies
  `U_M=cI-i M sY`, then `R_Y(pi/2)`, measures `Z`, and does not reset. Here
  `M` is fixed across rounds and the primary rational pair is
  `(c,s)=(9999/10001,200/10001)`. Under the standard
  `R_Y(theta)=exp(-i theta Y/2)` convention, this pair has
  `t=tan(theta/4)=1/100` and `theta=4*atan(1/100)`. With raw result `x_r`, define
  `d_r=x_r xor x_(r-1)`, `x_(-1)=0`, and `o=x_(R-1)`. Conditional on `M`, the
  flips are IID with
  `q_M=(1+2*M*c*s)/2`; the persistent complete law is the exact equal mixture
  of the two Bernoulli-product laws. A separate SymPy matrix-branch enumeration
  must equal that recurrence exactly.
- The matched-marginal rival resamples `M` independently each round. It has the
  same one-round law but a different multi-round joint law. Records violating
  `o = xor_r d_r` are exact structural zeros. At `R=2`, with
  `delta=2*c*s`, the exact diagnostic
  `TV(P_persistent,P_iid)=delta**2/2 > 0`; this persistence falsifier is not the
  candidate-versus-independent-oracle `delta_tv_cert`, whose current exact-route
  acceptance object is exact zero; a future nonzero certified band requires a
  preregistered amendment.
- The no-cutoff tail atom is separately and completely frozen before code.  Use
  `t=3/7`, hence `(c,s)=(20/29,21/29)`, at `R=8`, with detector string
  `d=11110000` and `o=0`.  Its exact positive probability is

  \[
  \left(\frac{1-(2cs)^2}{4}\right)^4
  =\frac{1681^4}{1682^8}
  =\frac{7984925229121}{64063097262168921289605376},
  \]

  which is strictly in `(0, 10**-12)`.  The identical detector string with
  `o=1` is an exact structural zero.  Evaluate both atoms directly from the
  closed form, without enumerating all Records.  The choice is immutable; no
  post-result search for a smaller atom is allowed.  This tail fixture and the
  primary tracer qualify exact arithmetic, persistence, fold, TV, and DD
  accounting only; neither is a d=3/5 oracle.
- SymFT planner outputs are independently checked against source-reported
  calibration cells only when the circuit hashes match.  Published counts do
  not certify this new persistent-mixture Record.
- A future d=3/5 candidate cannot certify itself.  At least one oracle must
  rebuild schedule and detector/observable folds from the neutral physical
  definition without importing the candidate's lowered payload.
- Because that oracle is absent now, target `delta_tv_cert` stays unavailable.

## 3a. Constraint ledger and corruption falsifiers

| theorem / invariant / raw-input constraint | exact assertion | falsifying test | deliberately broken input | evidence test trips |
|---|---|---|---|---|
| Structural zero | exact zero and positive algebraic values are distinct | exact-SymPy frozen `t=3/7`, `R=8` tail atom | replace every exact value `<1e-12` by zero | PMF hash, normalization, MTBDD terminals, and TV change |
| Persistent latent law | one sign is reused at every target location and round | persistent-vs-IID exact tracer | resample a matched-marginal sign each round | multi-round full Record law differs while one-round marginal agrees |
| Evaluator firewall | latent sign never appears in Record/schema | fixture and report validator | add `latent_sign` to emitted row/record payload | schema rejects report |
| Sign/amplitude structural invariance | primary `t=1/100`, both signs, and tiny nonzero `t=1/10^20` give identical route-qualified structure | compile-only planner control | change one sign branch or introduce `t=0` | circuit hash or normalized structural fields/history differ |
| Pair key semantics | ket/bra order, phase/coset normalization, memory, symbolic frame, and Record prefix are all bound | exact-small pair corruption | swap left/right or drop memory/frame/prefix from key | exact-law or count hash differs |
| Dynamic ADD canonical reduction | only exact equal terminals or identical child IDs merge | exact-small dynamic ADD corruption test | tolerance-merge two distinct tiny terminals, skip a level, or retain dead cache nodes | reconstructed coefficient map, live-history, or canonical node hash differs |
| DD variable order | dynamic key-code order is primary; Record-only order qualifies only the supplemental PMF MTBDD | codec manifest and reversed-Record-order diagnostic | use discovery IDs or reverse detector variables | direct-backend contract fails, or final PMF stays equal while its supplemental order/hash/count changes |
| Retained-boundary width exactness | exact upper order and independent subset-DP/BnB lower proof match for unweighted and weighted optima | certificate verifier | eliminate a KEEP boundary, change one domain size, remove an incidence, or falsify one DP entry | graph/factor/domain/proof check fails |
| Detector/observable fold | canonical raw-to-Record XOR map is independent and chronological | full-law fold corruption | permute one detector row or reverse one XOR operand index mapping | complete-law TV becomes positive |
| Full joint TV half factor | `TV=0.5*L1` on complete support | existing and tracer tests | omit the half factor or one structural-zero support cell | pinned value/support assertion fails |
| Unavailable is not zero | absent owner/oracle has explicit reason code and no numeric value | schema mutation test | serialize `0`, `NaN`, sampled estimate, or omitted metric | validator rejects row |
| External provenance | planner commit, pristine tree, circuit hashes, and output hash are bound | adapter preflight | dirty clone, wrong commit, in-tree build, or changed circuit | adapter fails before planning |

All corruption tripwires must be demonstrated before a target result can be
interpreted.

## 3b. Negative controls and non-degeneracy

- **Inert control.** `t=0` must use canonical positive zero and produce the
  exact tracer's uniform valid-Record law: every detector string has probability
  `2**(-R)` at `o=xor(d)`, while the opposite observable remains an exact
  structural zero.  Persistent and per-round-IID tracer laws coincide at this
  point.  The neutral target-shadow generator algebraically omits every
  replacement row exactly when the rational numerator is zero; active compilers
  must report this separately frozen inert history.  This compile-shadow fact is
  distinct from the tracer law.  The
  retained-boundary graph route deliberately retains the declared scaffold and
  labels this as `no_value_pruning=true`; its unchanged graph is not a claim of
  nonzero physical error.  No inert result may be substituted for a nonzero
  census cell.
- **Object movement.** On the exact primary tracer,
  `TV(P_persistent,R=2, P_iid,R=2) = (2*c*s)^2/2 > 0` exactly, and the designated positive tail
  is strictly between zero and `1e-12`.
- **Matched-marginal rival.** Persistent and per-round-IID signs share the same
  sign marginal.  Their multi-round exact tracer laws must differ; otherwise
  the fixture does not exercise persistence.
- **Compiler invariance.** For every target cell, positive and negative sign
  branches and the alternate nonzero magnitude must have identical Clifft
  active histories and identical normalized SymFT structural fields. A mismatch
  makes the corresponding structural meter ineligible.

## 4. Bounded simplifications

- The d=3/5 target census initially compiles structure only; it does not sample
  shots or allocate a `2^k` active vector.  This is exact for the reported
  planner structure but does not certify a Record law.
- NetworkX min-fill/min-degree widths are deterministic, versioned upper-bound
  diagnostics. They never populate
  `record_boundary_constrained_induced_width`, the weighted exact burden, or a
  route disposition.
- The finite-grid growth rule is class (c), bounded to the eight frozen cells.
  It makes no asymptotic or neighboring-fixture claim.
- Binary64 half-turn arguments are used only to instantiate the external parser. The
  structural invariance control and pinned optimizer semantics must establish
  that no magnitude cutoff determines `k_max`.  All exact-small probability,
  pair, DD, and TV controls use exact SymPy arithmetic.
- Any resource abort leaf is `CENSORED_RESOURCE` with a nonempty reason and
  resource receipt and with no numeric value/bound/estimate.  Its structure
  disposition is `INDETERMINATE`; if it prevents complete-law evidence, its
  faithfulness disposition is `INDETERMINATE` and v1 claim-report publication
  is deferred with a non-claim failure receipt; it does not automatically earn
  a binding verdict.  `UNANCHORED` is allowed only if the evidence establishes
  that no feasible independent reference exists.  `UNAVAILABLE` is reserved
  for an absent owner, oracle, or preflight dependency.  A timeout is not a
  numerical cutoff and is not a count.

No unbounded approximation is permitted in a headline metric.  Introducing a
coefficient cutoff, top-`k` truncation, sampled full-law proxy, or uncertified
treewidth halts the route and requires a new preregistration.

## 5. Epistemic status

- **(a) exact:** fixture hashes and latent transition law; integer route counts;
  exact route-burden transforms; exact-SymPy tracer law/TV/final PMF MTBDD;
  exact dynamic ADD histories; exact project boundary width and weighted burden
  only with matching certificates; structural-zero and corruption assertions.
- **(b) bands:** a future `delta_tv_cert` interval whose derivation and complete
  support are independently bound.  No band is currently registered for the
  target grid.
- **(c) gates:** finite-grid exponential-consistent rule, route disposition,
  external-resource preflight, and heuristic treewidth upper bounds.
- **Headline status:** `solver_permission=CODE_BLOCKED` until all five target
  metric families have eligible non-missing values on all rows and required
  certifications/corruptions pass.  `KILL_STRUCTURE` is informative finite-grid
  rejection, not a scientific scaling theorem.  `NOT_KILLED_ON_FROZEN_GRID` is
  not evidence of scalability.

## 6. Organization of pair + DD and build ownership

The future “1+2” route is organized vertically, not as two solvers that can
silently disagree:

```text
neutral physical fixture
  -> independent Clifford pullback / ExactPairSemantics
  -> canonical (left coset, right coset, latent, symbolic frame,
                Record-prefix) transitions
  -> two direct storage backends of the same exact recurrence
       A. explicit frontier census: N_pauli_pair_states_peak
       B. dynamic exact ADD: N_exact_pair_add_nodes_peak
  -> exact readout/trace marginalization
       -> supplemental final Record PMF MTBDD
  -> independently reconstructed complete Record PMF and TV certificate
```

The dynamic DD layer may share the neutral input and mathematical recurrence,
but it consumes only its current root, codec, and event; it may not iterate or
materialize the explicit frontier.  The independent SymPy tracer and later
neutral full-law oracle own correctness.  Shared compilation/fold payloads are
treated as a common-mode blind spot.  A final Record PMF MTBDD is downstream
and cannot retroactively become the dynamic DD headline.

Planned file ownership after this draft activates:

- fixture/schema/compile-only adapter:
  `scripts/external_baselines/no_cutoff_structure_census.py`;
- exact-small independent oracle and supplemental final-PMF MTBDD qualifier:
  `scripts/external_baselines/no_cutoff_structure_census_exact_oracle.py`;
- public behavior, corruption, provenance, and fail-closed tests:
  `tests/test_external_no_cutoff_structure_census.py`;
- metric debt and acceptance map: `docs/METRICS.md` and `tests/CODEBOOK.md`.

External repositories remain pristine; SymFT and Clifft are built out of tree.
No `src/**` file changes. Target execution is orchestrator-driven only after
the closure packet is `closed_for_preregistered_falsifier` and this status
changes from draft to active pre-registration.
