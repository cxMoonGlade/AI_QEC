# CAPEPS paper architecture and final figure source

Companion to
[`CAPEPS_XZZX_PAPER_FULL_REWRITE_2026-07-27.md`](CAPEPS_XZZX_PAPER_FULL_REWRITE_2026-07-27.md). The source-located formula spine is
[`GCAMPS_2511_06672_FORMULA_IMPLEMENTATION_AUDIT_2026-07-27.md`](GCAMPS_2511_06672_FORMULA_IMPLEMENTATION_AUDIT_2026-07-27.md).

Recommended paper title:

> **Clifford-Augmented PEPS for Coherent XZZX Syndrome Circuits: Untruncated Mechanics and a Record-Faithfulness Protocol**

The title reports bounded untruncated mechanics and names Record faithfulness
as a protocol, not an observed result. The current
worktree implements the green untruncated-mechanics slice below. The amber
optimization and Record layers, and every red target verdict, remain open.

The paper has one protagonist:

\[
\boxed{\text{GCAMPS-inspired CAPEPS}+\text{QEC instrument}
+\text{Record correctness}}.
\]

## 1. Figure 1 — two GCAMPS state cycles, one branching instrument, and one terminal reducer

```mermaid
flowchart TB
  L0["Residual-carrier typing<br/>G_h = (V_h,E_h); bijection ell_h: circuit qubits Q ↔ PEPS vertices V_h<br/>one physical leg per qubit; E_h is only the virtual-contraction graph"]
  S["Branch candidate<br/>|Psi_hat_h> = C_h |phi_hat_h><br/>mass estimate w_hat_h; raw history h; graph G_h; map ell_h"]
  O{"Next ordered quantum operation?"}

  subgraph U["GCAMPS upper state cycle — Clifford frame"]
    U1["Physical Clifford G"]
    U2["Left-compose frame<br/>C_h ← G C_h<br/>residual and ell_h unchanged"]
    U1 --> U2
  end

  subgraph L["GCAMPS lower state cycle — coherent residual update and tail"]
    N1["Physical coherent U<br/>small-local Pauli expansion U = sum_j c_j P_j"]
    N2["GCAMPS Eq. 5 phase ledger and signed pullback<br/>U_tilde = sum_j c_j C_h† P_j C_h"]
    A["Shared residual-operator kernel<br/>apply one unnormalized coherent operator to a parent-isolated residual copy<br/>return the candidate and its pre-normalization norm"]
    T0["Shared lower-cycle tail"]
    T1["Target frozen qubit-Clifford Q search<br/>candidate set, PEPS objective, cadence, and tie-break"]
    T2["Implemented paired physical-ray-exact refactor<br/>C_h ← C_h Q†; |phi_h> ← Q |phi_h>"]
    T3["Target paired relayout and finite-bond compression<br/>restore conditional-state norm; keep Born mass separate;<br/>record approximation and every intermediate peak"]
    N1 --> N2 --> A
    T0 --> T1 --> T2 --> T3
  end

  subgraph I["Branching QEC instrument route"]
    I1["Typed operation<br/>M(P): Hermitian Pauli measurement<br/>MR_Z(q): measure Z_q and prepare |0>"]
    I2["Pull P through C_h and build both coherent projectors<br/>Pi_b = (I + (-1)^b P)/2, b in {0,1}"]
    I3["Target atomic paired certificate, before normalization or lower-tail optimization<br/>save the common parent norm and both child raw norms; compute p_hat_0,p_hat_1"]
    I4["Paired-mass gate<br/>finite and nonnegative; complement consistency;<br/>structural zeros require a certificate, never a probability floor"]
    I5["Fork positive parent-isolated children<br/>w_hat_hb = w_hat_h p_hat_b; normalize each child"]
    I6["For MR_Z(q), left-compose physical X_q^b<br/>then append b to its frozen absolute raw column"]
    I1 --> I2
    I3 --> I4 --> I5 --> I6
  end

  F["Terminal raw frontier<br/>{w_hat_h, ordered absolute raw row m_h}<br/>no further quantum operation"]
  F0["Target terminal-frontier validity gate<br/>declared branch/column completeness; finite nonnegative masses;<br/>global mass residual and structural-zero certificate; never post-hoc renormalize"]
  R["Frozen classical Record reducer<br/>apply declared detector/observable XOR rows and offsets"]
  Z["Aggregate masses of equal detector/observable rows<br/>emit the Record law only after the frontier gate passes"]
  X0["On gate failure<br/>typed UNAVAILABLE plus candidate diagnostics only"]

  L0 -.->|types| S
  S --> O
  O -->|"Clifford"| U1
  U2 --> S
  O -->|"coherent non-Clifford U"| N1
  A -->|"operator was U"| T0
  T0 -->|"current untruncated path: skip target optimization"| S
  T3 --> S
  O -->|"M(P) or MR_Z(q)"| I1
  I2 --> A
  A -->|"operators were Pi_0 and Pi_1"| I3
  I6 --> T0
  O -->|"no operation remains"| F
  F --> F0
  F0 -->|pass| R --> Z
  F0 -->|fail| X0

  classDef exact fill:#e4f4ea,stroke:#397b55,color:#163725;
  classDef proposed fill:#fff0cf,stroke:#a36c13,color:#493107;
  classDef target fill:#f7e1e1,stroke:#a53f3f,color:#4a1717;
  classDef invariant fill:#e9e7f6,stroke:#6857a0,color:#281f45;
  class L0,S,O invariant;
  class U1,U2,N1,N2,A,T2,I1,I2,I5,I6 exact;
  class T0,T1,T3,I3,I4,F proposed;
  class F0,R,Z,X0 target;
```

**Caption.** The two state-return cycles follow the algorithmic organization
of GCAMPS Fig. 3. A physical Clifford returns through the upper frame cycle.
A coherent non-Clifford operator returns through Pauli expansion, signed
pullback, residual application, and an optional lower-cycle optimization
tail. The QEC instrument is a branching extension of that state machine, not
a third tensor representation: both projector branches use the same coherent
residual-operator kernel, and every surviving child uses the same lower tail.
Outcome-specific Born masses are evaluated on parent-isolated, unnormalized
projector candidates before branch normalization or optional finite-bond
compression. The current green path computes those outcome probabilities; the
atomic common-parent/two-child certificate shown in amber remains target work.

A PEPS physical leg remains in one-to-one correspondence with a circuit
qubit. The residual graph controls virtual contraction only and need not equal
the XZZX hardware-adjacency graph. A physical-axis permutation \(R_h\) is
state preserving only under the paired update
\((C_h,|\phi_h\rangle)\mapsto(C_hR_h^\dagger,R_h|\phi_h\rangle)\) and a
consistent update of \(\ell_h\); changing virtual connectivity alone is not a
qubit permutation.

`M(X_q)` is the X-measurement special case of `M(P)`. The implemented reset
surface is specifically `MR_Z(q)`: measurement of physical \(Z_q\), followed
by \(X_q^b\) to prepare \(|0\rangle\). The figure makes no generic `MR`
claim. GCAMPS reports 20 and 90 inequivalent two-site entanglers for local
dimensions two and three, respectively; this all-qubit paper may use only an
independently reconstructed and frozen qubit catalogue. The qutrit count 90
is neither an implementation target nor a CAPEPS result.

The current prototype implements the green untruncated mechanics and paired
exact-refactor primitive. Q selection, paired relayout, finite-bond control,
structural-zero certification, the terminal-frontier gate, and the Record law
remain open. The Record reducer is terminal and classical: it consumes a raw
frontier only after the global validity gate passes, applies the frozen
detector/observable map, and has no return edge into the quantum state machine.
A failed gate emits typed `UNAVAILABLE` and diagnostics, never a renormalized
Record law.

**Drawing rule.** Draw exactly two state-return cycles: the Clifford frame
cycle above and the coherent residual cycle below. Attach measurement/reset
as a branch-producing route that calls the same residual kernel and lower
tail. Put the Record reducer after a terminal raw frontier, outside every
quantum loop. Color denotes evidence status, not software ownership.

## 2. Figure 2 — one frozen instrument, four headline routes, one mechanism control

```mermaid
flowchart TB
  F["Hash-frozen neutral XZZX instrument<br/>geometry, ordered operations, coherent rotations,<br/>M(P)/MR_Z(q) schema, absolute detector/observable rows"]
  W["Frozen scientific acceptance coordinates<br/>same circuit instances, support, output schema, horizon, and target precision;<br/>route-specific enumeration/sampling/reference roles are preregistered"]
  B["Full-PEPS/CAPEPS resource protocol<br/>same candidate execution task, precision, hardware, timing boundary,<br/>selection rule, repetitions, synchronization, and uncertainty rule"]

  D["Independent dense exact reference<br/>complete small-law and selected complete physical states"]
  P["Full PEPS comparator<br/>same coherent channel; one PEPS carries the full state"]
  C["CAPEPS candidate<br/>tableau frame plus residual PEPS"]
  T["Pauli-twirled tableau approximation<br/>different stochastic channel"]
  CM["Planned C|MPS> mechanism control<br/>same coherent channel; preregistered 1D orderings<br/>not the existing restricted MPS service"]

  APC["Primary-pair correctness scoring<br/>enumerable tracer: complete raw and Record law;<br/>d=3: selected states/mass/reset plus enumerated PASS<br/>or sampled provisional PASS* Record gate"]
  GPC["Headline passing configurations<br/>full PEPS and CAPEPS only; select with frozen inference;<br/>no pass means no matched-correctness efficiency value"]
  E["Primary efficiency estimand<br/>selection-aware end-to-end time-to-solution<br/>full PEPS versus CAPEPS"]
  M["Secondary resource report<br/>peak host RSS; peak device memory; completion;<br/>bond and approximation ledgers remain diagnostics"]

  ACM["Optional control scoring<br/>dense reference; CAPEPS and C|MPS> under the same gates;<br/>match frame/operator logic, orderings, compression/search budgets"]
  GCM["Control conjunction<br/>both CAPEPS and C|MPS> pass the same registered gate"]
  H["Implementation-level topology-sensitive ablation<br/>not causal isolation of PEPS topology<br/>and not the headline winner"]

  Q["Different-channel diagnostic<br/>coherent-versus-twirled Record error<br/>and separately reported twirled resources"]
  V["Bounded primary-pair verdict<br/>d=3 correctness and matched-accuracy efficiency"]
  VH["Bounded mechanism-control report<br/>qualified by ordering and implementation confounders"]
  VQ["Separate approximation verdict<br/>twirl error/resource trade-off; never a same-channel winner"]

  F --> D
  F --> P
  F --> C
  F --> T
  F -.-> CM
  W --> D
  W --> P
  W --> C
  W --> T
  W -.-> CM
  B --> P
  B --> C
  B -.-> CM

  D --> APC
  P --> APC
  C --> APC
  APC --> GPC
  GPC --> E
  GPC --> M
  E --> V
  M --> V

  D -.-> ACM
  C -.-> ACM
  CM -.-> ACM
  ACM --> GCM --> H --> VH

  D --> Q
  T --> Q
  Q --> VQ

  classDef fixture fill:#e9e7f6,stroke:#6857a0,color:#281f45;
  classDef reference fill:#fff0cf,stroke:#a36c13,color:#493107;
  classDef approximation fill:#e5edf8,stroke:#496d9b,color:#182a42;
  classDef verdict fill:#f7e1e1,stroke:#a53f3f,color:#4a1717;
  classDef control fill:#f1f1f1,stroke:#666,color:#222,stroke-dasharray: 5 5;
  class F,W,B fixture;
  class D,P,C,APC,GPC,E,M reference;
  class T,Q,VQ approximation;
  class CM,ACM,GCM,H,VH control;
  class V verdict;
```

**Caption.** The four headline routes independently lower the same neutral
scientific fixture. Dense is the correctness referee and lies outside
candidate timing; it need not run on the candidate hardware. Full PEPS and
CAPEPS are the only pair entering the primary same-channel efficiency
estimand. Their comparison uses the separate frozen resource protocol and is
admissible only after both pass the registered accuracy gate. The measured
scope includes route-specific lowering, tableau work, tensor operations,
branch copies, refactor/compression, measurement/reset, synchronization, and
Record aggregation; it excludes neutral-fixture construction and dense-referee
execution.

The Pauli-twirled route deliberately changes the channel. Its Record error and
resources form a separate approximation trade-off and cannot enter the
same-channel CAPEPS-versus-full-PEPS winner rule. Branchwise coherent
pure-state fidelity is not a valid twirled-route gate.

The dashed \(C|\mathrm{MPS}\rangle\) route has a disjoint scoring path and
therefore cannot enter the primary estimand. Even after CAPEPS and this control
both pass, the output is only an implementation-level topology-sensitive
ablation: ordering, canonicalization, compression, and optimizer choices can
remain confounders. A stronger topology attribution would require
preregistered matched frame/operator logic, multiple 1D orderings, comparable
search/compression budgets, and explicit sensitivity analysis.

## 3. Figure 3 — correctness-first evidence staircase

```mermaid
flowchart TB
  B["Completed bounded context<br/>25-qubit full-PEPS pure-state baseline<br/>no measurement, reset, Record, or CAPEPS"]
  C1["Completed bounded mechanics context<br/>18 untruncated all-qubit mechanics tests<br/>dense and strip-shaped PEPS fixtures; not genuine 2D evidence"]

  G0["Gate 0<br/>CAPEPS-specific literature closure,<br/>metric registration, and preregistration"]
  G1["Gate 1<br/>frozen algebra/schema/axis and lowering-trace checks;<br/>absolute-fold and corruption controls"]
  G2["Gate 2<br/>genuine 2D mechanics tracer, at least 2x2<br/>horizontal/vertical updates, a loop, M(P)/MR_Z branches,<br/>layout/permutation checks, and dense complete-state truth"]
  G3["Gate 3<br/>complete multi-step enumerated instrument tracer<br/>all branches, mass conservation, structural zeros, MR_Z,<br/>absolute raw columns, terminal-frontier gate, and Record fold"]
  G4["Gate 4<br/>d=3 same-channel correctness<br/>selected states, branch masses, reset, and Record certification:<br/>enumerated population PASS or sampled provisional PASS*"]
  G5["Gate 5<br/>matched-accuracy d=3 resource comparison<br/>frozen grids/workload/hardware and selection-aware inference;<br/>primary time-to-solution and secondary memory"]
  G6["Optional post-d=3 Gate 6<br/>d=5 resource reachability<br/>same frozen implementation and resource envelope"]

  V["Allowed d=3 conclusion<br/>fixture-bounded primary-pair efficiency result;<br/>Record wording follows PASS versus PASS* status"]
  V6["Separate allowed d=5 report<br/>fixed-envelope reachability only"]
  X["Stopping boundary<br/>no d=5 complete Record law, scaling, threshold,<br/>qutrit leakage, or production claim"]

  B -.->|baseline context only| G0
  C1 -.->|bounded context only| G0
  G0 --> G1 --> G2 --> G3 --> G4 --> G5 --> V
  G5 -.->|only after d=3 gates| G6
  G6 --> V6
  G3 -.-> X
  G4 -.-> X
  G6 -.-> X

  classDef done fill:#e4f4ea,stroke:#397b55,color:#163725;
  classDef gate fill:#fff0cf,stroke:#a36c13,color:#493107;
  classDef verdict fill:#e5edf8,stroke:#496d9b,color:#182a42;
  classDef stop fill:#f7e1e1,stroke:#a53f3f,color:#4a1717;
  class B,C1 done;
  class G0,G1,G2,G3,G4,G5,G6 gate;
  class V,V6 verdict;
  class X stop;
```

**Caption.** Existing algebra tests and pure-state data are bounded context,
not permission to skip closure/preregistration, the frozen schema/corruption
gate, a genuine two-dimensional tracer, or the Record gate. A
\(1\times N\) or \(N\times1\) PEPS cannot discharge Gate 2; the genuine-2D
fixture also exercises measurement/reset branching. Gate 3 preserves and
validates the complete enumerated branch frontier before the deterministic
Record fold.

Gate 4 distinguishes two evidence classes. Enumeration compares population
laws and can yield the registered population-law `PASS`. Sampling folds every
sampled trajectory and uses a preregistered reference/uncertainty construction;
it yields only provisional `PASS*`, not an unqualified complete-law verdict.
Resource results are interpreted only after the applicable correctness status.
The d=3 verdict does not require a d=5 run. Optional \(d=5\) execution starts
only after the d=3 gates and establishes reachability under a fixed envelope,
not correctness transfer from \(d=3\).

## 4. Paper-to-figure map

| paper section | visual object | purpose |
|---|---|---|
| Introduction | one-line invariant and Figure 1 thumbnail | state the resource-allocation hypothesis |
| Background | no new architecture figure | distinguish prior \(C\lvert\mathrm{MPS}\rangle\) and hybrid QEC work from the CAPEPS extension |
| Method | Figure 1 | define the two GCAMPS state cycles, shared residual transaction/tail, branching instrument, and terminal Record reducer |
| Correctness | Figure 3 | show that branch mass and Record precede resource claims |
| Experiments | Figure 2 | show four independent headline lowerings, the mechanism control, frozen workload, and primary efficiency estimand |
| Results | Figure 3 plus result tables | separate observed mechanics/baseline from `PENDING` targets |
| Limitations | cut-geometry inset from Figure 1 | emphasize operator-Schmidt rank across PEPS cuts, cut geometry, and residual diffusion rather than Pauli weight alone |

## 5. Metric, estimand, and claim contract

The proposed target state-and-Record acceptance object, to be registered before execution, is

\[
\mathcal O=
\left(
P_{\mathrm{raw}},
P_{\mathrm{Record}},
\{\rho_h:h\in\mathcal H_{\mathrm{sel}}\},
\mathcal R_{\mathrm{reset}}
\right).
\]

It contains population raw/Record laws, selected conditional states, and
to-be-registered reset checks. It is not the full terminal classical--quantum
instrument over every conditional state. A sampled protocol estimates only a
declared projection of this object and receives a distinct provisional status.

| object | required metric or gate | forbidden substitute |
|---|---|---|
| untruncated mechanics | physical-ray equality and signed-Pauli identities against a separately formulated dense construction | test count alone |
| genuine 2D tracer | complete-vector fidelity on a PEPS with both dimensions greater than one, including horizontal/vertical updates, a loop, `M(P)`, and `MR_Z` | \(1\times N\) or \(N\times1\) strips |
| selected conditional state | complete-vector fidelity for aligned same-channel branches | local overlap or tensor residual |
| selected branch mass | per-step probability error, cumulative log-mass error, and explicit structural-zero agreement | normalized conditional state or probability flooring |
| paired measurement | real finite parent norm strictly greater than zero; real finite nonnegative child norms; complement consistency; parent isolation | division before validation, clipping, or post-hoc renormalization |
| reset | structural `MR_Z` identity and one-site trace distance to \(\lvert0\rangle\langle0\rvert\) | post-hoc state repair |
| enumerated terminal frontier | declared branch/column completeness, finite nonnegative masses, total-mass residual, and structural-zero certificate | silently dropped branches or global renormalization |
| population raw/Record law (`PASS`) | raw-TV and joint detector/observable Record-TV under the frozen absolute fold | selected paths, one realized row, or raw-syndrome TV |
| sampled Record certification (`PASS*`) | per-trajectory fold, preregistered one- or two-sample reference design, joint support, confidence band, and coverage/excluded-mass policy | population TV or an unqualified complete-law verdict |
| primary same-channel pair | selection-aware candidate-execution time-to-solution at matched `PASS`, or explicitly provisional matched `PASS*` | “runtime or memory,” whichever looks favorable |
| secondary resources | peak process-tree host RSS, a frozen device-memory owner/semantics, completion, and the route-specific work ledger | maximum bond alone |
| mechanism control | CAPEPS versus \(C\lvert\mathrm{MPS}\rangle\) under matched gates, orderings, frame/operator logic, and budgets | causal attribution to PEPS topology from one ordering |
| twirled approximation | coherent-versus-twirled Record error plus separately reported resources | same-channel fidelity or winner status |
| d=5 reachability | completion under the fixed envelope after the d=3 gates pass | a d=5 correctness, scaling, or threshold claim |

The formulas below define a protocol skeleton, not an executable
preregistration. Accuracy bands, workload instances, configuration grids,
repetition count, confidence allocation, and effect threshold remain `OPEN` and
must receive hash-frozen values before target execution.

For each primary route
\(r\in\{\mathrm{full\ PEPS},\mathrm{CAPEPS}\}\), freeze a pilot/selection set,
an independent certification-and-timing holdout, a grid \(\mathcal C_r\), an
equal tuning budget, and a deterministic selection rule. Before pilot inspection,
freeze one evidence class
\(e\in\{\mathrm{PASS},\mathrm{PASS}^{\ast}\}\) for both primary routes:
\(e=\mathrm{PASS}\) is enumerated population certification and
\(e=\mathrm{PASS}^{\ast}\) is sampled provisional certification. Define

\[
\mathcal C_{r,\mathrm{sel}}^{e}
=
\{c\in\mathcal C_r:\mathcal G_{\mathrm{sel}}^{e}(r,c)=e\},
\qquad
c_r^\dagger
=
\arg\min_{c\in\mathcal C_{r,\mathrm{sel}}^{e}}
\widehat\tau_{r,\mathrm{sel}}(c).
\]

with a frozen tie-break and simultaneous or otherwise selection-valid
inference across the grid. If the evidence-class set is empty, the route is typed
`UNAVAILABLE`. The chosen configuration is then frozen; no reselection is
allowed after holdout inspection.

Conditional on \(\mathcal G_{\mathrm{hold}}^{e}(r,c_r^\dagger)=e\) on the
independent holdout, define the run-protocol population runtime target

\[
\tau_r
=
\operatorname{median}_{s\sim\Pi_{\mathrm{run}}}
T_r(W_{\mathrm{hold}},c_r^\dagger;s),
\qquad
\theta_T
=
\log\frac{\tau_{\mathrm{full\ PEPS}}}{\tau_{\mathrm{CAPEPS}}}.
\]

Here \(\Pi_{\mathrm{run}}\) is the frozen fresh-process/run-order protocol, not
the observed finite sample. The timing holdout estimates \(\tau_r\) and
\(\theta_T\) with a selection-independent confidence procedure. If
\(\delta_T\) is the preregistered minimum fractional speedup, the log-scale
threshold is \(\Delta_{\log T}=\log(1+\delta_T)\); an advantage requires the
lower confidence bound for \(\theta_T\) to exceed \(\Delta_{\log T}\).

Timing measures end-to-end **candidate execution after configuration
selection**. It includes route-specific lowering, tableau work, operator
construction/routing, tensor contractions, branch copies, internal
candidate search and rejected candidates, compression, synchronization,
measurement/reset, and Record aggregation. Neutral-fixture construction,
offline pilot tuning, and dense certification are excluded by definition but
reported separately with an amortization analysis; this endpoint is not total
research cost. Prefix memoization, batching, branch/state reuse,
contraction-plan reuse, compilation/cache policy, CPU/thread affinity, device
synchronization, run order, and fresh-process boundaries must be frozen.

Peak process-tree host RSS and device high-water are secondary. The
preregistration must name the device-memory owner and whether allocated,
reserved, external workspace, child-process, and cache memory are included.
Memory is reported at the primary-selected configurations and in a registered
Pareto table; it does not replace the primary endpoint.

The completed 25-qubit pure-state sweep belongs in a compact baseline table.
It is not evidence for measurement, reset, Record, CAPEPS, or QEC-instrument
correctness.

After an enumerated population-law `PASS`, the terminal positive sentence may
be:

> On the frozen all-qubit XZZX acceptance object and stated hardware/resource
> envelope, CAPEPS met the preregistered selected-state, branch-mass, reset,
> raw-law, and detector/observable Record population gates; its
> selection-aware time-to-solution and secondary memory measurements were the
> reported values relative to full PEPS.

After sampled `PASS*`, the wording must instead say “provisional performance
under preregistered sampled Record certification” and must not claim complete
population-law Record faithfulness. Until numerical preregistration and target
execution, the central efficiency question remains open.
