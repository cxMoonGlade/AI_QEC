# Restricted MCWF F2/F3 — Pre-Registration (theory-first, LITERATURE-GROUNDED)

Status: PRE-REGISTRATION, 2026-07-20. Predictions written before F2/F3 fixture, dense-worker,
registry, comparator, or corruption-test implementation and before any F2/F3 run. A miss is a
finding, not a re-fit.

Literature prerequisite:
`docs/simulator_validation/RESTRICTED_MCWF_F2_F3_LITERATURE_CLOSURE_2026-07-20.md`,
`closure_status: closed`.

## -1. Question charter (importance × attackability)

- Decision + consequence: decide whether the restricted two-qubit MCWF path reproduces two additional
  source-grounded Markovian mechanisms under the already declared ordered X/Z measurement/reset
  protocol. A passing result creates reusable neutral fixtures, an independent dense Record oracle,
  and a registry-driven differential gate; it does not upgrade the complete simulator claim.
- Plausible attack + independent anchor: two qubits make the density matrix, 16x16 Liouvillian,
  projectors, reset maps, and closed-form factorized Record law exactly reconstructible without the
  production compiler. Isolated QuTiP supplies a solver with different implementation blind spots.
- Alternative formulations + invariants: number-projector versus Pauli-Z dephasing; down/up Lindblad
  versus generalized amplitude damping; matrix-exponential versus closed-form law; density-matrix
  versus MCWF ensemble; unit-modulus collapse phase invariance. All equivalent formulations must agree
  after explicit coefficient conversion.
- Kill condition: stop the line if F2 cannot distinguish the missing-`sqrt(2)` collapse normalization;
  F3 cannot distinguish removal/exchange/misnormalization/mis-targeting of `sigma_+`; a neutral worker
  consumes a production compiled program or production operator/measurement helper; or any declared
  thermal rate ratio violates detailed balance.
- Selection warning: implementation difficulty, novelty, and favorable existing F1 output are not
  premises.

## 0. Grounding ledger (all primary sources full-text read and noted)

| sub-axis / mechanism | mechanism paper | observable paper | reading note | in-repo code to reuse |
|---|---|---|---|---|
| F2 pure dephasing | arXiv:1109.0954v1, Eqs. (1)–(4), (6)–(11); arXiv:1606.01145v1, Eqs. (48), (55)–(57); arXiv:2512.09189v1, Eqs. (1)–(4) | arXiv:2101.08313v2, Eq. (1), Eq. (9) | `oi_schirmer_pure_dephasing_1109.0954_source_review.md`; `arsenijevic_bankovic_damping_1606.01145_source_review.md`; `garner_thermal_relaxation_2512.09189_source_review.md`; `czajkowski_grilo_sequential_measurements_2101.08313_source_review.md` | neutral law/TV primitives in `scripts/external_baselines/qutip_mcwf_xz_protocol.py`; production path only behind a separate binding gate |
| F3 finite-temperature relaxation/excitation | arXiv:1606.01145v1, Eqs. (16)–(18); arXiv:2512.09189v1, Eqs. (1)–(2), (10), (15) | arXiv:2101.08313v2, Eq. (1), Eq. (9); reset channel in arXiv:2512.09189v1, Eq. (22) | same four source-only notes | same neutral protocol primitives; no reuse inside the independent matrix construction |
| Lindblad→MCWF ensemble | arXiv:2501.17913v2, Sec. II.B, Eqs. (12)–(13), App. A Eq. (A6) | ordered Record sources above | `sander_tensor_jump_2501.17913_source_review.md` | isolated QuTiP worker and public project MCWF route, compared rather than shared |

## 1. Mechanisms and frozen neutral fixture family

The new schema is `error_coupling_simulator.neutral.mcwf_xz_fixture.v2`. Each fixture file must be
byte-hashed and must contain exactly these semantic groups:

- `schema`, `fixture_id`, and the restricted `claim_boundary`;
- `num_qubits=2`, `local_dims=[2,2]`, `initial_levels=[0,1]`;
- an ordered `collapse_terms` array. Each entry has a unique `term_id`, `family`, `target`, and
  `generator_rate_per_ns`. Workers derive the collapse amplitude as the positive square root of this
  generator coefficient; no field may ambiguously mean both rate and amplitude;
- optional `thermal_metadata` containing `n_bar`, `gamma_base_per_ns`, and the exact declared
  detailed-balance ratio;
- two evolution segments of `10 ns`, separated by the ordered measurements below;
- an ordered measurement array equivalent to keys `[mx_before,mz_before,mx_after,mz_after]`, targets
  `[0,1,0,1]`, bases `[X,Z,X,Z]`, reset flags `[true,true,false,false]`, with reset states
  `X→|+>` and `Z→|0>`;
- `project_microstep_count=40`, `trajectory_count=2048`, distinct positive project/QuTiP/measurement
  seeds, `comparison_family_alpha=0.01`, and `numerical_zero=1e-12`;
- the deterministic two-level label-to-bit map. No evaluator-only process truth is emitted.

The three fixtures are frozen as follows. Every listed term is present on targets 0 and 1.

| fixture | declared generator terms | exact parameter choice | exact continuous-time scale |
|---|---|---|---|
| F1 `two_qubit_t1_ordered_xz_reset` | `gamma_down D[sigma_-]` | `gamma_down=ln(4)/10 ns`; no up/dephasing | population survival after 10 ns is `1/4`; coherence factor is `1/2` |
| F2 `two_qubit_pure_dephasing_ordered_xz_reset` | `D[sqrt(2 gamma_phi)n]`, `n=|1><1|` | `gamma_phi=ln(4)/10 ns`; no down/up | coherence factor after 10 ns is `1/4`; populations are invariant |
| F3 `two_qubit_thermal_ordered_xz_reset` | `gamma_down D[sigma_-]+gamma_up D[sigma_+]` | `n_bar=1/3`; `lambda=ln(4)/10 ns`; `gamma_down=4 lambda/5=0.11090354888959125/ns`; `gamma_up=lambda/5=0.027725887222397813/ns` | total population factor is `exp[-(gamma_down+gamma_up)t]=1/4`; equilibrium `p1*=1/5` |

F3 also records `gamma_base=3 lambda/5` and must satisfy exactly, before floating evaluation,
`gamma_down=gamma_base(n_bar+1)`, `gamma_up=gamma_base n_bar`, and
`gamma_up/gamma_down=1/4=exp(-beta hbar omega)`.

## 2. Metric binding (forced standard-metric ladder)

- Existing `docs/METRICS.md` entry: total variation over the complete schedule-ordered Record support,
  `TV(P,Q)=0.5 sum_x |P(x)-Q(x)|`, plus declared binary marginals. The full joint alphabet size is
  fixed at 16 even when a fixture has structural zeros; a binary marginal has size 2.
- One-sample sampled-to-dense gate for registry entry `j`:
  `TV(P_hat,P_dense) <= r(n,k,alpha_j)`, where
  `r=sqrt(log((2^k-2)/alpha_j)/(2n))`, capped at one.
- Two-sample QuTiP-to-project gate: the observed TV must not exceed the sum of the two one-sample
  radii, each evaluated at `alpha_j/2`.
- The comparison registry contains exactly five statistics per fixture and 15 total. It is sorted and
  content-hashed. `alpha_j=0.01/len(registry)` is derived from this frozen cardinality; no literal
  denominator is permitted inside comparison code.

Per fixture, the five entries are:

1. QuTiP sampled law versus dense exact full joint;
2. project sampled law versus dense exact full joint;
3. QuTiP sampled law versus project sampled full joint;
4. project sampled law versus dense exact mechanism-directed marginal A;
5. project sampled law versus dense exact mechanism-directed marginal B.

At `n=2048` and 15 registered entries, the frozen bands are:

- one-sample 16-bin joint radius `0.0670302388436366`;
- two-sample 16-bin joint simultaneous radius `0.1365617560712202`;
- one-sample two-bin marginal radius `0.04421175841273293`.

These numbers must be recomputed from the registry and formula and must match the pins within
`numerical_zero`; they are not independent hard-coded policy.

Forbidden proxies: jump count, final-state fidelity, one expectation value, a renormalized conditional
state without branch mass, finite-bond discarded weight, solver success, or agreement with the
production compiler's own oracle may not replace joint/marginal TV.

## 2a. Predicted observables (class (b) bands)

The exact dense law factorizes for these deliberately local, Hamiltonian-free fixtures. With record
order `(mx_before,mz_before,mx_after,mz_after)`, its Bernoulli parameters are frozen before execution:

| fixture | `P(mx_before=0)` | `P(mz_before=1)` | `P(mx_after=0)` | `P(mz_after=1)` | directed marginals |
|---|---:|---:|---:|---:|---|
| F1 | `1/2` | `1/4` | `3/4` | exact structural zero | `mz_before`, `mx_after` |
| F2 | `1/2` | exact structural one | `5/8` | exact structural zero | `mx_after`, `mz_after` |
| F3 | `1/2` | `2/5` | `3/4` | `3/20` | `mz_before`, `mz_after` |

The closed-form product law and the independently vectorized 16x16-Liouvillian law must agree at
every cell within `1000*numerical_zero`; declared structural-zero cells must be exactly zero before
normalization. Clean QuTiP/project samples are predicted to fall inside every registered confidence
band. No observed value may be used to widen a band.

Pre-frozen corruption separations:

- F1 replacing every declared `sigma_-` with `sigma_+` changes
  `P(mz_before=1)` from `1/4` to `1`, marginal TV `3/4`.
- F2 replacing `sqrt(2 gamma_phi)n` by `sqrt(gamma_phi)n` changes
  `P(mx_after=0)` from `5/8` to `3/4`, marginal TV `1/8`.
- F3 removing every `sigma_+` term changes `P(mz_after=1)` from `3/20` to zero,
  marginal TV `3/20`.
- F3 exchanging down/up rates changes `(P(mz_before=1),P(mz_after=1))` from
  `(2/5,3/20)` to `(17/20,3/5)`, TV `9/20` on either directed marginal.
- F3 multiplying every excitation collapse amplitude by `sqrt(2)` changes
  `P(mz_after=1)` to `0.27017847639540005`, separation `0.12017847639540005`.
- F3 moving the complete target-1 down/up pair to target 0 changes the target-1 marginals to
  `(1,0)`, separations `3/5` and `3/20`.

Every listed separation exceeds the frozen one-sample marginal radius. The applicable corruption must
fail a registered verdict, not merely produce a nonzero diagnostic.

## 2b. Disconfirmation surface

- Strongest competing explanation: agreement may come from sharing compiler/operator/measurement
  code rather than from the physical equations. The dense worker therefore imports only NumPy/SciPy
  and its neutral fixture parser; static and runtime import audits must reject production imports.
- Null mechanism: setting every generator rate to zero creates a plausible schedule-only law and must
  fail the directed target statistic for every fixture.
- Gauge competitor: multiplying a collapse operator by `-1` or any unit-modulus scalar must leave the
  dense law unchanged within `1000*numerical_zero` and must not be counted as corruption power.
- Unordered competitor: sorting or commuting the X/Z operations is prohibited. A deliberate schedule
  reorder must trip fixture identity or the ordered-law comparison before a clean verdict is accepted.
- Favorable agreement at one marginal does not rescue a failed full-joint entry, and full-joint
  agreement does not waive the two preregistered mechanism-directed power checks.

## 3. Independent ground truth (non-circular)

Primary ground truth is a new isolated NumPy/SciPy worker that:

1. hand-types `I`, `n`, `sigma_-`, `sigma_+`, X/Z projectors, and fixed-state reset matrices;
2. lifts operators by explicit Kronecker products in the declared target order;
3. forms each Lindblad superoperator directly under a documented column-vectorization convention;
4. exponentiates the summed 16x16 Liouvillian with `scipy.linalg.expm`;
5. propagates unnormalized 4x4 branches through the ordered projectors and reset maps;
6. takes branch traces before normalization and emits the exact 16-cell law plus declared marginals;
7. rejects importability or deserialization of the production compiled program and production
   operator/measurement/reset helpers.

Two additional independent anchors are required: a scalar closed-form law derived from the table in
§2a, and isolated QuTiP constructed from the same neutral fixture but not from the dense matrices or
project program. The project path is the candidate, never its own ground truth.

## 3a. Constraint ledger + corruption falsifiers

| theorem / invariant / raw-input constraint | exact assertion | planned falsifying test | deliberately broken input | evidence required before reading clean verdict |
|---|---|---|---|---|
| Dissipator coefficient/amplitude distinction | a term with `generator_rate=r` builds amplitude `sqrt(r)` exactly once | dense/fixture schema tests | interpret `r` as the collapse amplitude | schema/binding rejection or registered TV failure |
| F2 coherence-rate identity | `D[sqrt(2 gamma_phi)n]` gives `rho01(t)=e^(-gamma_phi t)rho01(0)` | F2 closed-form/dense/candidate tripwire | delete `sqrt(2)` | `mx_after` TV exceeds `0.04421175841273293` |
| F3 detailed balance | declared down/up ratio is `1/4`, equilibrium is `1/5` | fixture validator and dense stationary-state test | wrong excitation rate | validation rejection and doubled-up-rate corruption fails |
| Down/up direction | ground excitation needs `sigma_+`; excited relaxation needs `sigma_-` | F3 directed-marginal tests | remove or exchange `sigma_+` | registered marginal failure with pinned separations |
| Target/support identity | every neutral term binds exact family, target, and one-site support | project-binding and dense lifting tests | move the target-1 thermal pair to target 0 | fixture binding or both directed marginals fail |
| Complete positivity and trace preservation | `expm(tL)` preserves Hermiticity/trace and produces nonnegative branch masses within shared numerical tolerance | dense channel sanity tests | transpose one side of the dissipator | deterministic sanity failure before TV scoring |
| Structural zeros | source-declared impossible cells stay exact zero, not threshold-discovered | fixture-specific support tests | inject positive mass into F1/F2 final-Z-one cells | exact structural-zero failure |
| Selective branch mass | branch probability is `Tr(P rho P)` before conditional normalization | ordered-instrument tests | normalize before recording trace | closed-form/dense mismatch and joint failure |
| Reset semantics | reset maps the selected local state to the declared fixed state and preserves branch trace | reset-map known-answer tests | omit X reset or use the outcome state | deterministic reset residual and joint failure |
| Operation order | keys, targets, bases, and reset flags match the byte-pinned schedule | fixture hash/order tests | exchange the middle Z and final X operation | hash/identity rejection |
| Collapse gauge | `D[e^(i theta)L]=D[L]` | dense invariance control | global sign/phase | law must remain within `1000*numerical_zero`; it must not fail |
| Independent dense ownership | dense worker has no production imports or program input | static AST/import and runtime module audit | import a production operator builder | fail closed before execution |
| Registry-derived risk | registry count is 15 and every `alpha_j` is derived from its content | comparison registry tests | hard-code `/15` or delete one entry | hash/cardinality/alpha pin failure |
| Corruption power | every load-bearing mutation changes a registered verdict | parametrized corruption suite in the external-comparison tests | the six corruptions in §2a | every mutation must fail its named entry |

## 3b. Negative controls + non-degeneracy

- Inert controls expected to fail: the all-zero generator gives F1 `mz_before` separation `3/4`, F2
  `mx_after` separation `3/8`, and F3 directed-Z separations `3/5` and `3/20`; each must fail at least
  one registered project-to-dense marginal gate.
- Object movement: for every non-null fixture,
  `max_directed_marginal_TV(record(test),record(null)) > 0.04421175841273293`.
- Gauge control expected to remain inert: collapse sign/phase changes must pass deterministic
  invariance and are excluded from corruption-power counts.
- Strongest competing explanation: if dense, QuTiP, and project agree only after sharing any production
  construction, the run is invalid even when all TVs are small.

## 4. Bounded simplifications (unbounded implies STOP)

| simplification | class | bound against the declared faithful target |
|---|---|---|
| Two qubits, local independent Markovian terms, no Hamiltonian | (a) fixture definition | exact for this neutral target; authorizes no correlated, non-Markovian, control, calibration, or QEC-wide inference |
| Closed-form product factorization | (a) for these fixtures | must agree cellwise with the independently assembled 16x16 Liouvillian within `1000*numerical_zero` |
| Dense floating matrix exponential | (c) numerical gate | trace/Hermiticity/nonnegative-mass checks plus closed-form cellwise bound `1000*numerical_zero`; otherwise STOP |
| QuTiP solver tolerances | (c) differential gate | its sampled law must pass the preregistered dense joint band; a deterministic QuTiP master-equation projection must also match dense within `1000*numerical_zero` |
| Project finite-step `m=40` trajectory path | (c) go/no-go | no global-order claim; its complete joint and directed marginals must pass against the continuous dense law under the registered bands |
| Finite `n=2048` sampling | (c) confidence gate | overall family risk `0.01` allocated over the frozen 15-entry registry; no post-run denominator or band change |
| Deterministic two-level label-to-bit map | (a) fixture identity | exact bijection for labels 0/1 only; authorizes no leakage-label or readout-calibration claim |

## 5. Epistemic status

- (a) exact: source equations and coefficient conversions; detailed-balance identity; analytic fixture
  parameters; schedule/fixture/registry hashes; structural zeros; matrix/operator definitions; dense
  independence and provenance checks.
- (b) bands: the exact clean-law Bernoulli parameters and corruption separations in §2a. A miss is a
  finding and may not be rewritten.
- (c) gates: finite-sample TV radii, solver/dense floating tolerances, corruption go/no-go, and the
  restricted pass/fail verdict.
- The headline remains provisional and fixture-bound. Nothing in this preregistration supports a full
  QEC Record, finite-bond, calibrated-noise, production-scaling, or release claim.

## 6. Build organization

- Builder lane A: neutral v2 schema, three byte-pinned fixtures, registry, pure protocol math, and
  closed-form known answers.
- Builder lane B: isolated NumPy/SciPy dense worker and its independence/provenance envelope.
- Builder lane C: isolated QuTiP generalization, project binding/adaptation, comparison orchestration,
  and corruption suite.
- Review lane: source/fixture diff review first, then implementation diff review, then named-tmux
  focused tests. Terminal coverage/aggregate/mutation remain later goal stages and cannot be reused as
  this phase's evidence.
- No parallel subagent delegation is assumed by this preregistration; ownership lanes are sequential
  and file-disjoint unless the user later authorizes delegation.
- External CPU workers remain isolated; project execution remains GPU-only; every run is scripted;
  external baseline repositories remain pristine.

## Preregistration gate

`premises closed? yes | standard metric bound? yes | predictions frozen? yes | independent GT? yes | constraint falsifiers registered? yes | simplifications bounded? yes | controls registered? yes | preregistration gate: pass`

Theory-first downstream decision: implementation is permitted only for the F2/F3 neutral-fixture,
independent-dense, and 15-entry comparison scope frozen here. Any schema, parameter, metric, registry,
prediction-band, or corruption change requires a new preregistration before the changed result is read.
