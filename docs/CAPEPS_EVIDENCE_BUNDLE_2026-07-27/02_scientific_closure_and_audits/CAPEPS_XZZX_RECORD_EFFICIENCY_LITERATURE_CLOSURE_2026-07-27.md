# CAPEPS XZZX Record-efficiency — literature closure packet

Date: 2026-07-27
Status: `OPEN_SPLIT_VERDICT`
Theory-first gate: `CODE_BLOCKED`
Scope: all-qubit CAPEPS, bounded coherent XZZX syndrome circuits, complete
classical raw/Record population law, selected conditional states, reset
checks, and a full-PEPS resource comparator

This packet asks whether the rewritten CAPEPS paper has enough source closure
to freeze and execute its central experiment. It does not authorize target
code, retrofit results, or promote the existing untruncated prototype.

The optimizer-only closure and preregistration are separate:

- [`CAPEPS_DISENTANGLER_THEORY_FIRST_CLOSURE_2026-07-27.md`](CAPEPS_DISENTANGLER_THEORY_FIRST_CLOSURE_2026-07-27.md)
- [`CAPEPS_EXACT_SMALL_DISENTANGLER_PREREGISTRATION_2026-07-27.md`](CAPEPS_EXACT_SMALL_DISENTANGLER_PREREGISTRATION_2026-07-27.md)

Those artifacts can permit an exact-small 20-versus-720 qubit catalogue test.
They do not permit the XZZX Record-efficiency target considered here.

## 1. Frozen question charter

### Decision and consequence

The decision question is:

> On a frozen bounded all-qubit coherent XZZX instrument, after full PEPS and
> CAPEPS pass the same preregistered correctness gate and evidence class, does
> CAPEPS reduce held-out candidate-execution runtime, with memory and bond
> ledgers reported separately?

A positive result would support only the frozen \(d=3\) fixtures, accuracy
gate, configuration grids, hardware, and runtime protocol. A negative or
unavailable result would show that the Clifford/residual split did not produce
a usable advantage in that regime. Neither result would establish an
asymptotic theorem.

### Proposed mechanism

CAPEPS defines

\[
|\Psi\rangle=C|\phi\rangle_{\mathrm{PEPS}},
\]

stores physical Clifford evolution in \(C\), and applies a pulled-back coherent
operator only to the PEPS residual:

\[
U=\sum_j\alpha_jP_j,
\qquad
UC|\phi\rangle
=C\left(\sum_j\alpha_jC^\dagger P_jC\right)|\phi\rangle.
\]

The candidate efficiency mechanism is that the residual PEPS need not
re-encode Clifford entanglement already represented by the tableau. This is a
project hypothesis, not a result inherited from GCAMPS.

### Scientific observable

The proposed population target is

\[
\mathcal O_{\mathrm{pop}}
=
\left(
P_{\mathrm{raw}},
P_{\mathrm{Record}},
\{\rho_h:h\in\mathcal H_{\mathrm{sel}}\},
\mathcal R_{\mathrm{reset}}
\right).
\]

The two population laws are complete over the declared terminal support.
\(\rho_h\) is checked only on a result-blind selected-history set.
\(\mathcal R_{\mathrm{reset}}\) is a to-be-frozen conjunction of structural
reset identities and reduced-state checks.

This is not the complete terminal classical–quantum instrument
\(\{w_h,\rho_h\}_{h\in\mathcal H}\), because conditional states are not checked
for every positive-mass history. The phrase “complete Record law” is allowed
only for the complete classical population law.

A sampled procedure

\[
\mathcal E_N(\mathcal O_{\mathrm{pop}})
\]

is evidence about the same population object. It may yield provisional
`PASS*`; it is not a second population law and cannot be described as an exact
complete-law result.

### Mechanism-to-observable bridge

For an exact complete frontier, selective instruments generate ordered raw
history masses. A deterministic classical fold

\[
r=f_{\mathrm{fold}}(m)=Fm\oplus r_0
\]

then gives

\[
P_{\mathrm{Record}}(r)
=
\sum_{m:f_{\mathrm{fold}}(m)=r}P_{\mathrm{raw}}(m).
\]

The empirical bridge under test is:

```text
Clifford frame
  -> lower residual complexity on the frozen histories
  -> lower candidate-execution cost
  -> while the same raw/Record/state/reset gate still passes.
```

No source proves either arrow for a PEPS residual in this XZZX workload.

### Predicted direction and scale

The direction “CAPEPS is faster” is the paper's hypothesis. No source-backed
effect size is available. A target preregistration must separately freeze a
class-(b) falsifiable magnitude band for that scientific prediction and a
class-(c) operational decision threshold \(\delta_T\). The minimum meaningful
speedup cannot substitute for a prediction band. Both need an uncertainty rule
before execution; this packet invents neither value.

### Required invariants

1. \(C|\phi\rangle\) is preserved under exact paired refactors and physical
   relayouts, up to global phase.
2. Complex Pauli coefficients and tableau signs are retained.
3. Every sibling branch is produced from an immutable parent.
4. Parent norm, child norms, paired complement, and positive-mass
   normalization are checked before division.
5. Structural-zero semantics are not replaced by a floating threshold.
6. Reset is an explicit instrument, not post-hoc state repair.
7. Complete terminal mass is validated before the Record fold.
8. The fold uses frozen absolute raw columns, XOR rows, offsets, and axis
   order.
9. Full PEPS and CAPEPS enter the resource comparison only after passing the
   same registered gate and evidence class.

### No-go and failure mechanisms

- a local physical projector can become a high-weight pulled-back Pauli word;
- the coherent projector sum can grow PEPS bonds even when each Pauli term is
  product across a cut;
- norm and Born-mass contractions can dominate frequent syndrome
  measurements;
- optimizer and routing cost can exceed any residual-bond reduction;
- a Clifford surface-code state may already have a compact graph-aligned PEPS;
- an all-data coherent rotation may spread residual complexity through many
  cuts;
- PEPS environment approximations can bias small branch masses and rare
  histories;
- a detector/observable fold can suppress a channel difference visible in the
  raw law.

### Bounded target

- \(d=3\): correctness plus the primary same-channel resource comparison;
- \(d=5\): optional fixed-envelope reachability only after every \(d=3\) gate;
- excluded: \(d=5\) complete-law transfer, asymptotic scaling, threshold,
  qutrit leakage, production readiness, and field-wide novelty.

## 2. Search and evidence procedure

The current artifact-verified corpus was queried first. During this closure a
mechanical orphan was found and repaired: the already source-only-reviewed
GCAMPS note was artifact-valid but absent from `CURRENT_CORPUS.toml`. After
independent source-only review, the Chang, Liu--Clark, and Harper hybrid-QEC
notes were also admitted. The manifest now binds 36 notes and 451 `paper_fact`
records, with corpus identity
`85f743dea97b67794d7a63040e3d7c6c20434a2a7ea4a20ea6b9727caa6847be`
and manifest-file SHA-256
`3c79de8e45e8345bde6e50aa834c2739ade911e8dbb69ae31a8b74a07416a544`.
RAG contains 451 fact chunks; KG contains 126 source-located edges and zero
dangling edges. `tests/test_literature_tools.py` passes all 64 tests.

Representative local searches:

- `Clifford augmented tensor network projective measurement reset`
- `PEPS surface code coherent noise measurement reset Record`
- `conditional Born branch mass tensor network measurement`
- `matched accuracy tensor network simulation benchmark runtime memory`
- `full joint detector observable Record law`
- `GCAMPS Clifford hybrid state non-Clifford Pauli expansion`

AnySearch academic disconfirmation searches included:

- `Clifford augmented PEPS tensor network quantum circuit simulation`
- `Clifford frame PEPS non-Clifford residual`
- `surface code coherent errors tensor network syndrome measurement reset record`
- `matrix product state surface code coherent non-Clifford crosstalk syndrome`
- `projected entangled pair states mid-circuit measurement reset surface code`

The search found CAMPS/GCAMPS MPS work, Clifford-augmented fermionic MPS work,
PEPS circuit simulators, and other coherent-QEC simulators. It did not locate a
primary source that implements the full combination

\[
C|\mathrm{PEPS}\rangle
+\text{selective reset instrument}
+\text{complete raw/Record law}
+\text{matched full-PEPS resource comparison}.
\]

This records a bounded local/external search for the claim rows below; it is
neither an exhaustive search nor a field-wide novelty theorem.

## 3. Source closure ledger

| Required row | Exact evidence | Status | Boundary |
|---|---|---|---|
| \(C|\mathrm{MPS}\rangle\) hybrid state | Harper et al., arXiv:2511.06672v2, Sec. 3 and Fig. 3, PDF p. 5 | `CLOSED` | MPS residual only |
| Clifford left update | GCAMPS Sec. 2.2 and Sec. 3, PDF pp. 3, 5 | `CLOSED` | no PEPS cost result |
| signed non-Clifford pull-through | GCAMPS Sec. 3; Eq. (5) phase reconstruction in Sec. 2.3.1, PDF pp. 4–5 | `CLOSED` | coefficient solver details remain source-local gaps but current qubit prototype has independent mechanics tests |
| exact paired refactor | GCAMPS Sec. 3, PDF p. 5 | `CLOSED` | exact state identity only; no optimizer optimality |
| \(C|\mathrm{PEPS}\rangle\) extension | no direct source found | `OURS_PROPOSED` | algebraic definition; PEPS correctness and efficiency are unproved |
| repeated coherent QEC precedent | Harper et al., arXiv:2605.29514v1, Secs. II–V | `CLOSED_ADJACENT` | \(C|\mathrm{MPS}\rangle\), rotated surface code, sampled logical-error observable |
| projective-measurement pull-through in adjacent hybrid QEC | Harper et al. 2605.29514v1, Sec. IV.A, PDF p. 4 | `CLOSED_ADJACENT` | no printed Born branch mass or complete law |
| selective Born probability and conditional state | Czajkowski and Grilo, arXiv:2101.08313v2, Sec. 2.2 Eq. (1), PDF p. 5 | `CLOSED` | general instrument primitive |
| ordered sequential outcome law | Czajkowski and Grilo, Sec. 3.1 Eq. (9), PDF p. 7 | `CLOSED` | not a PEPS accuracy theorem |
| fixed reset-to-\(|0\rangle\) component | Ghosh et al., arXiv:1306.0925v2, Fig. 1 and caption, PDF p. 2 | `CLOSED_COMPONENT` | not the complete CAPEPS instrument |
| XZZX check geometry | Bonilla Ataides et al., arXiv:2009.07851v3, Fig. 1, PDF p. 2; Darmawan et al., arXiv:2104.09539v2, Fig. 2, PDF p. 3 | `CLOSED` | no complete target schedule |
| consecutive-round defect | Bonilla Ataides Fig. 5, PDF p. 6; Darmawan Sec. II.B, PDF p. 3 | `CLOSED` | first/terminal anchors are not source facts |
| absolute raw columns and Record fold | hash-frozen neutral fixture and independent fold reconstruction | `PROJECT_INPUT_OPEN` | literature does not supply the target tables |
| finite open-boundary PEPS definition and algorithms | Lubasch et al., arXiv:1405.3259v2, Secs. II–III | `CLOSED_BACKGROUND` | no CAPEPS or Record theorem |
| exact PEPS worst-case limitation | Schuch et al., PRL 98, 140506, VOR pp. 2–3 | `CLOSED_LIMIT` | does not prove the \(d=3\) fixture is hard |
| whole-network fidelity objective | Evenbly, arXiv:1801.05390v2, Sec. V Eq. (12), PDF p. 6 | `CLOSED_DEFINITION` | approximate environment has no generic certified error bar |
| PEPS terminal sampling limitation | Rudolph and Tindall, arXiv:2507.11424v2, Sec. II and pathological construction | `CLOSED_LIMIT` | no intermediate reset or historical Record |
| finite-bond CAPEPS \(\to\mathcal O_{\mathrm{pop}}\) bound | no generic source found | `OPEN` | exact-small direct comparison is allowed; scalable certificate is not |
| CAPEPS \(\to\) full-PEPS resource advantage | no source or theorem found | `TARGET_TO_TEST` | must be result-blind and preregistered |
| coherent \(\to\) twirled observable difference | Harper et al. 2605.29514v1, Eq. (9), Figs. 5–6 | `CLOSED_ADJACENT` | logical-error observable, not automatically Record-TV |
| matched registered correctness-gate timing/memory estimand | project protocol | `OPEN_REGISTRATION` | requires owner, bands, splits, repetitions, CI, and corruption tests |
| field-wide novelty | search not sufficient for an exhaustive theorem | `OUT_OF_SCOPE` | use source-specific positioning only |

No `OURS_PROPOSED`, `PROJECT_INPUT_OPEN`, `TARGET_TO_TEST`,
`OPEN_REGISTRATION`, or `OPEN` row is treated as closed evidence.
`CLOSED_ADJACENT` closes only the cited prior-work row, not the CAPEPS target.

## 4. What the adjacent Harper source changes

The pinned arXiv:2605.29514v1 source materially narrows the paper's positioning.
It already supplies:

- repeated rotated-surface-code syndrome extraction;
- coherent non-Clifford crosstalk;
- a \(C|\mathrm{MPS}\rangle\) forward simulation;
- projective-measurement Pauli-sum pull-through;
- reset and measurement error-rate parameters;
- a coherent-versus-Pauli-twirled comparison;
- distances \(d=3,5,7,9\), \(d\) syndrome rounds, and an MPS bond cap of 32.

It does not supply:

- a PEPS residual;
- an outcome-resolved reset instrument;
- paired Born-mass or complete-frontier conservation checks;
- a complete raw or detector/observable Record law;
- conditional-state or Record-TV certification;
- a matched full-PEPS runtime/memory comparator.

It also supplies contrary evidence: the authors did not enable Clifford
optimization because its cost outweighed the bond reduction for their
workload. Their MPS truncation can bias logical error downward. PEPS is listed
only as future work.
The admission review additionally found that the printed Eq. (4)
\(e^{+i\theta ZZ}\) unitary is not reconstructible from the printed
CNOT--\(R_Z(\theta/2)\)--CNOT circuit without an unstated convention, and that
Table I, Eq. (5), and Secs. III.B/V.A do not give one consistent numerical
\(\theta\) parameter set. Those anomalies do not erase the high-level adjacent
precedent, but they forbid using this source as an exact noise-circuit oracle.

The full source-only audit is
[`HARPER_2605_29514_SOURCE_ONLY_AUDIT_2026-07-27.md`](HARPER_2605_29514_SOURCE_ONLY_AUDIT_2026-07-27.md).
The independently reviewed note is now admitted to the artifact-verified
current corpus:
[`../papers/reading_notes/harper_hybrid_surface_code_2605.29514v1_source_review.md`](../papers/reading_notes/harper_hybrid_surface_code_2605.29514v1_source_review.md).

## 5. Measurement–reset–Record attribution

The evidence roles must remain separate.

| Object | Evidence owner | Not owned by that source |
|---|---|---|
| XZZX stabilizer geometry | Bonilla Ataides; Darmawan | full target schedule, reset map, absolute fold |
| ordered local XZZX check shell | Darmawan | all absolute measurement columns |
| consecutive-round defect | Bonilla Ataides; Darmawan | first-round and terminal anchors |
| selective Born update | Czajkowski–Grilo | CAPEPS contraction accuracy |
| reset-to-zero component | Ghosh | full XZZX reset instrument |
| absolute raw columns, detector/observable rows, offsets | frozen project fixture | literature fact |
| raw-to-Record pushforward | project definition plus independent reconstruction | quantum-state or PEPS fidelity |

Therefore `[5,6]` in the current paper cannot jointly carry measurement,
fixed reset, and complete Record-fold semantics. The paper must cite or name
the separate owners above and label the absolute fold as a project input.

## 6. XZZX and coherent-noise coordinate fork

The target has not frozen whether its coherent \(R_Y\) layer is defined before
or after the local-H transformation used to relate surface-code and XZZX
coordinates.

Because

\[
HYH=-Y,
\qquad
H R_Y(\theta)H=R_Y(-\theta),
\]

a uniform physical-coordinate \(R_Y(+\theta)\) layer becomes sign-staggered in
a coordinate where only a subset of data qubits is Hadamard conjugated.

Two experiments are both legitimate but different:

1. **physical-uniform model:** define uniform \(R_Y(+\theta)\) before the
   local-H change, transform every gate and measurement, and obtain the
   required sign pattern afterward;
2. **transformed-uniform project fixture:** insert uniform
   \(R_Y(+\theta)\) directly in the transformed Stim fixture and make no claim
   of equivalence to physical-uniform XZZX noise.

The target preregistration must choose one, freeze the qubit subset and signs,
and independently reconstruct the schedule, state basis, and absolute fold.
The existing full-PEPS preregistration cannot silently decide this for
CAPEPS.

## 7. Disconfirmation surface

### 7.1 Full PEPS need not waste resources on Clifford structure

Polynomial tableau storage does not prove that a graph-aligned PEPS represents
the same Clifford state inefficiently. A target must include a
\(\theta=0\) Clifford-only resource control and report whether full PEPS
remains compact on the frozen circuit.

### 7.2 Measurement can reverse the expected advantage

In full PEPS, an ancilla projector is physical-local. In CAPEPS,
\(C^\dagger PC\) can be high weight, and

\[
\frac{I\pm C^\dagger PC}{2}
\]

is a coherent residual sum. Frequent syndrome measurement can make pulled-back
operator construction and norm contraction dominate the run.

### 7.3 The optimizer can be net harmful

The adjacent hybrid-QEC source explicitly reports that its
Clifford-optimization cost exceeded its MPS bond benefit. CAPEPS must measure
search time, candidate count, relayout, contraction, and compression inside
the candidate runtime boundary.

### 7.4 Selected states can hide law failure

High conditional-state fidelity on selected branches does not establish
prefix mass, terminal population law, or rare-history correctness. A selected
branch cannot rescue a raw/Record law failure.

### 7.5 The Record fold can suppress a coherent difference

The twirled channel is a different physical model, but the selected Record
coordinate may be insensitive to that difference on a degenerate fixture.
Coherent-versus-null and coherent-versus-twirled raw/Record non-degeneracy
controls must fire before the approximation comparison is interpreted.

## 8. Preregistration prerequisite ledger

The current paper contains a good protocol skeleton but not an executable
numerical preregistration. The following fields remain frozen only in form, not
in value.

### 8.1 Acceptance object

- decide whether \(P_{\mathrm{raw}}\) means terminal law only or also registers
  all positive-mass prefixes;
- freeze absolute support, columns, rows, offsets, axis order, and checkpoint;
- freeze result-blind \(\mathcal H_{\mathrm{sel}}\) and any rare/adversarial
  history set;
- freeze state basis, qubit order, normalization, and dtype;
- define \(\mathcal R_{\mathrm{reset}}\) as an explicit conjunction.

### 8.2 Numerical gates

- selected-state infidelity;
- per-step branch-probability error;
- cumulative log-mass error;
- raw-TV and Record-TV;
- parent/child norm, complement, and global-mass residual;
- reset trace distance and structural reset identity;
- contraction validity;
- structural-zero exact policy;
- sampled coverage or excluded-positive-mass policy;
- coherent/twirled non-degeneracy;
- resource effect threshold and confidence level;
- epistemic class for every row.

### 8.3 Population versus sampling

The preregistration must select population `PASS` or sampled provisional
`PASS*` for the primary target. If `PASS*` is selected, it must freeze:

- one-sample exact-reference or independent two-sample design;
- candidate and reference trajectory counts;
- joint support and familywise-\(\alpha\) allocation;
- concentration or interval formula;
- seeds, coupling, batching, and stopping rule;
- timeout, failed-sample, and excluded-mass treatment.

Empirical TV cannot be relabelled population TV.

### 8.4 Fixtures, splits, and selection

- byte- and hash-frozen circuits, rounds, angles, coordinate convention,
  operation order, measurement/reset columns, and fold;
- non-overlapping pilot, certification holdout, and timing holdout;
- route-specific configuration grids and equal tuning budget;
- selection method and tie-break;
- typed timeout, OOM, crash, nonfinite, and no-passing-configuration outcomes.

Already inspected full-PEPS and 25-qubit values are historical/pilot evidence
and cannot become the new independent holdout.

### 8.5 Runtime and memory

The current primary formula,

\[
\tau_r=\operatorname{median}T_r,
\qquad
\theta_T=\log\frac{\tau_{\mathrm{full\ PEPS}}}
{\tau_{\mathrm{CAPEPS}}},
\]

still needs:

- run population and repetition count;
- serial randomized route order;
- exact hardware, software, affinity, cache, warm-up, compilation, and device
  synchronization;
- timer boundaries and censoring rule;
- interval method and effect threshold;
- sampled-trajectory work required to reach the same registered evidence
  precision.
- a source-backed convention, or an explicit confirmed-standard-gap, for
  median runtime, log-ratio inference, selection-aware confidence intervals,
  process-tree RSS, and device high-water;
- registered project-defined owners and independent value tests for each metric.

The current endpoint excludes dense certification and pilot tuning. Until a
broader time-to-precision object is defined, the metric should be called
**held-out candidate-execution runtime**, not generic time-to-solution.

Memory needs a frozen owner and semantics for process-tree RSS, device
allocated/reserved pools, external workspaces, child processes, and sampling
frequency. It remains secondary and cannot replace the runtime decision after
results are seen.

### 8.6 Independent reference and corruptions

The dense reference needs a frozen owner, artifact schema, input firewall,
basis/order/checkpoint, projector/reset formulas, precision, and deliberate
corruptions for:

- gate order and Clifford composition direction;
- Pauli sign and outcome sign;
- axis permutation;
- reset omission and wrong reset map;
- raw-column or fold-row shift;
- structural-zero conversion;
- degraded contraction;
- coherent-to-twirled substitution;
- pilot leakage, holdout reuse, and post-hoc reselection.

Every required corruption must be shown to trip before target execution.

### 8.7 Required frozen tables

A minimal CAPEPS-specific preregistration must contain:

1. `FixtureAndSplit`
2. `AcceptanceObjectCoordinates`
3. `AccuracyGateMatrix`
4. `PASS_PASSstar_TruthTable`
5. `SamplingDesign`
6. `ConfigurationSelectionAndTiming`
7. `MemoryAndD5Reachability`
8. `ConstraintCorruptionLedger`

`FixtureAndSplit` must include a same-circuit \(\theta=0\) Clifford-only
resource control for full PEPS and CAPEPS. `ConstraintCorruptionLedger` must
register the expected disconfirmation signal if that control already makes
full PEPS compact or makes CAPEPS measurement pull-through more expensive.

The new metrics then require owners, independent value tests, epistemic
classes, and entries in `docs/METRICS.md` and `docs/service_status.json`.

## 9. Closure verdict

| Gate | Verdict |
|---|---|
| GCAMPS hybrid algebra | `CLOSED` |
| general selective-measurement law | `CLOSED` |
| XZZX geometry and consecutive defect | `CLOSED` |
| fixed reset component | `CLOSED_COMPONENT_ONLY` |
| adjacent repeated coherent hybrid-QEC source | `CLOSED_ADJACENT` |
| direct CAPEPS precedent | `NOT_FOUND` |
| absolute target fixture and coordinate | `OPEN` |
| complete CAPEPS raw/Record law | `OPEN` |
| finite-bond target-level error bridge | `OPEN` |
| matched full-PEPS/CAPEPS resource estimand | `OPEN_REGISTRATION` |
| target corruption gate | `OPEN` |
| numerical preregistration | `NOT_ELIGIBLE` |
| target code | `CODE_BLOCKED` |

The correct paper claim is therefore:

> CAPEPS is a GCAMPS-inspired \(C|\mathrm{PEPS}\rangle\) proposal with
> source-grounded hybrid algebra and general instrument components. Whether it
> preserves the frozen XZZX raw/Record law at finite bond and improves
> held-out candidate-execution runtime over full PEPS remains an empirical
> question requiring preregistration.

The exact next action is not target execution. It is:

1. choose the XZZX/local-H/\(R_Y\) coordinate;
2. freeze the eight preregistration tables, prediction band, and controls;
3. register the metrics and owners;
4. independently review the completed preregistration;
5. only then request the repository-required authorization for any
   `src/**` target implementation.

