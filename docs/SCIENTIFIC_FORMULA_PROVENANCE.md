# Simulator Scientific Formula Provenance Ledger

> Audit state: **IN PROGRESS — NOT A SCIENTIFIC ACCEPTANCE CERTIFICATE.**
>
> This is the sole coordinator-owned deliverable for the sequential, read-only simulator formula
> audit defined by
> `docs/twin_validation/HANDOFF_simulator_scientific_formula_audit_2026-07-14.md`.
> All `src/**` and `tests/**` files are evidence only and remain unmodified. Every human checkbox
> stays unchecked until a human explicitly adjudicates it.

## 0. Frozen audit snapshot

### 0.1 Repository identity

| field | frozen value | audit meaning |
|---|---|---|
| repository root | `/home/cx/AI_QEC/AI_QEC` | only this live checkout is audited |
| freeze date | `2026-07-14` (`America/Vancouver`) | audit snapshot date |
| Git HEAD | `844d211a6fba28784b890c1638884a1efa4377be` | live code identity; supersedes the stale handoff header snapshot |
| worktree at freeze | clean | no pre-existing tracked or untracked delta at Batch 0 freeze |
| service catalog | `docs/service_status.json` | installed-service and support-module authority |
| service catalog SHA256 | `f0159cd1d2fc1a8a1678a0aff7c642cc9c6e43bf3cf2905ab27ace126e7b5878` | catalog integrity |
| code map | `docs/CODE_MAP.md` | discovery map, not scientific evidence |
| code-map SHA256 | `80b0ab178d6db7f017ebd81ffbf875a406d2fa81a2087218218bd4d0518d5a4d` | map integrity |
| code-map input SHA256 | `d32bb846743cdd403c581a5d2769a0fba580281eecf07dd6811e75d09f08e131` | generated-map input identity |
| audit contract SHA256 | `ccfb86583909fdd11f4066532b8d7ca465b6996158e625502f921f135be309b2` | handoff integrity |
| test codebook SHA256 | `c29572f47230e7902da1fec95272315c0c9e866aeea0108f8bfd8393bfa9bb5` | test-index integrity |

`python tools/gen_code_map.py --check` passed at freeze. Its generated header still prints an older
HEAD because the checker does not treat HEAD metadata as an input; the live Git identity above is
therefore recorded independently.

### 0.2 Scope count reconciliation

| surface | frozen count | precise interpretation | manifest SHA256 |
|---|---:|---|---|
| installed Python modules | **109** | every `*.py` under `src/error_coupling_simulator/`; 96 non-`__init__` plus 13 `__init__.py` | `9feb60b7d8bb33f3618dd6fb99ba3f732b39a7afed7e6766519dc8db5d2e3366` |
| installed native source files | **4** | one `.cpp` and three `.cu`; no installed `.cuh` or `.hpp` | `614e7b9f607e10d20c58834c96addc107e1e0929f69dd7a3a0f1a8c5807fd3cf` |
| installed implementation union | **113** | 109 Python plus 4 native files | `42c7557c05cae70961bb36571a347ed82940f4518bd4a544ea7366fe094a0656` |
| canonical acceptance files | **52** | 63 service references deduplicate to 52 existing files: 26 `cpu_light`, 6 `cpu_exclusive`, 20 `gpu_serial` | catalog-derived |
| all Python files under `tests/` | **143** | includes harness/support and noncanonical tests | `854f17e2397f7cc8458ffc9bf74c5a4d350d5b86a4b3a301bc335706768c1428` |
| pytest-named files | **131** | every `tests/**/test_*.py` | included above |
| broader executable verification files | **132** | 131 pytest-named files plus `tests/harness/proc_selftest.py` | included above |

Aggregate manifest SHA256 values are reproducible as: sort paths bytewise; compute lowercase
SHA256 for each file; serialize each record as `<hash><two spaces><path><newline>`; then SHA256 the
concatenated records. Per-file hashes are expanded in Sections 11--13.

Count conclusion: **109 Python modules and 4 native files are the complete installed simulator
source distribution at this freeze. 52 is the complete unique canonical acceptance set, but it is
not the complete test tree.** Batch 12 therefore audits the 52 canonical files and classifies the
remaining verification/harness surface so no scientific oracle, gate, or formula is silently
omitted.

The 109 Python modules reconcile exactly as 81 unique service-owned modules plus 28 support
modules, with no missing, stale, or overlapping catalog entries. The four native files are:

- `src/error_coupling_simulator/carrier/kernels/fused_kraus_local.cpp`
- `src/error_coupling_simulator/carrier/kernels/fused_kraus_local.cu`
- `src/error_coupling_simulator/carrier/kernels/qutrit_mcwf_ops.cu`
- `src/error_coupling_simulator/carrier/kernels/sv_traj_d3.cu`

Ignored mutant copies and third-party native sources under external dependencies are outside the
installed distribution and do not increase the four-file count.

### 0.3 Audit boundary

Included: every scientific formula, discretization, normalization, convention, placement rule,
mechanism-to-observable bridge, metric, anchor, bound, and scientific threshold used by the 113
installed source files; shipped ARCHIVED PEPO service; compatibility seams; canonical acceptance
oracles; and any current noncanonical gate that supplies independent scientific evidence.

Excluded with an explicit later disposition: downstream `legacy/` inference/calibration/hardware
analysis, retired thin-strip driver, repository-only experiments not used by a current service,
third-party internals, frozen schema strings, and docs-only historical proposals. Numerical-only
software controls may be classified non-scientific, but a threshold deciding a scientific claim
remains in scope.

## 1. Binding audit semantics

### 1.1 Provenance statuses

Every formula receives exactly one status:

| status | closure rule | mandatory visible marker when open |
|---|---|---|
| `DIRECT` | verified full text contains the same or strictly equivalent formula, object, and assumptions | none |
| `DERIVED` | fully replayable `[ours-derived]` chain from `DIRECT` premises with no hidden edge | none |
| `COMPOSITE-UNCLOSED` | components are sourced but composition, placement, or mechanism-to-observable bridge is not | `高危无出处（组合公式整体无直接出处）` |
| `ADJACENT-ONLY` | only neighboring, secondary, summary, note, RAG, or KG evidence exists | `高危无出处（仅有邻近/二手证据）` |
| `NO-SOURCE` | recorded searches found no exact verifiable source | `高危无出处` |
| `CONTRADICTED/MISAPPLIED` | source and implementation/use conflict, or source assumptions fail | immediate high-risk finding |

If literature supports only the mathematical form, not its coefficient, normalization, slicing,
or placement, the row must additionally show `高危无出处（文献仅支持形式）`.

### 1.2 Independent verdict axes

```text
formula_correctness: correct | incorrect | unresolved
application_fit: matched | mismatched | bridge-open
value_provenance: complete | project-design | incomplete
human_verdict: unchecked
```

Provenance is not correctness. Correct algebra can be applied to the wrong object or schedule;
values can remain project design even when a form is direct; test agreement can share the same
formula and therefore fail to be independent evidence.

### 1.3 Evidence discipline

- Local RAG, KG, reading notes, docstrings, tests, and generated code maps are discovery or
  verification aids, never exact-source closure by themselves.
- A closing source needs bibliographic/version identity, local PDF and SHA256, exact printed and
  PDF-page locator, visual equation-page verification, symbol/basis/unit mapping, assumptions, and
  frozen code/call-path mapping.
- Each adapted formula is reconstructed as a graph from primary equation through convention,
  unit conversion, discretization, approximation, composition, schedule placement, instrument,
  record transform, and metric.
- Missing evidence remains visibly open. The audit does not infer correctness from availability,
  test passage, or conventionality.

## 2. Sequential batch gate

| batch | scientific surface | extractor | independent reviewer | coordinator merge | state |
|---:|---|---|---|---|---|
| 0 | freeze manifests, reconcile scope, create ledger skeleton | n/a | n/a | complete | frozen |
| 1 | numerical conventions; channel algebra; exact-qubit DM; record fold | 1A, 1B1 (`cptp_channel.py`), 1B2a1 (`channels.py:415-521,770-784`), and 1B2a2 (`channels.py:522-604,724-769`) extractors complete; remaining 1B2/1C pending | 1A, 1B1, 1B2a1, and 1B2a2 independent adversarial reviews complete; remaining 1B2/1C pending | 1A + 1B1 + 1B2a1 + 1B2a2 rows merged, schema/source/reverse coverage checked | in progress |
| 2 | frontend noise/compile/schedule; Stim; record I/O; DEM; optional decoder | pending | pending | pending | not started |
| 3 | Axis-1 Hamiltonians, controls, collapses, Lindbladian, dense record evolution | pending | pending | pending | not started |
| 4 | RTN, finite-band 1/f, PSD/correlation, burst/storm/HMM, fan-out, coupled cycle | pending | pending | pending | not started |
| 5 | exact-qutrit DM, WG leakage/seepage, instrument, ququart CZ transport | pending | pending | pending | not started |
| 6 | dense MCWF, fused execution, native mirrors, Grover, CUDA-Q plugin | pending | pending | pending | not started |
| 7 | restricted Axis-1 MCWF/MPS and QT/MPS product-formula verification | pending | pending | pending | not started |
| 8 | active single-wire PEPS carrier and truncation diagnostics | pending | pending | pending | not started |
| 9 | shipped ARCHIVED PEPO and reused PEPO-to-PEPS formulas | pending | pending | pending | not started |
| 10 | quantum-bath GKSL/pseudomode/QRT/null/memory-witness suite | pending | pending | pending | not started |
| 11 | certification, anchors, diagnostics, metrics, bands, negative controls | pending | pending | pending | not started |
| 12 | independent verification formulas and current gates | pending | pending | pending | not started |
| 13 | reverse coverage, duplicate/risk propagation, source-manifest closure | pending | pending | pending | not started |

No later batch starts until the current extractor has stopped, a fresh independent reviewer has
searched for omissions and contrary evidence, and the coordinator has merged the disposition.
Large batches may be split into named sub-batches while retaining that strict sequence.

## 3. Compact formula index

| formula ID | short name | role | owning service/module | provenance | formula correctness | application fit | value provenance | risk marker | detailed section |
|---|---|---|---|---|---|---|---|---|---|
| ECS-NUM-001 | shared \(10^{-12}\) numerical zero | bound/convention | shared numerical support | NO-SOURCE | unresolved | bridge-open | project-design | 高危无出处 | ECS-NUM-001 |
| ECS-NUM-002 | positive floor | bound/helper | channel algebra support | NO-SOURCE | unresolved | bridge-open | project-design | 高危无出处 | ECS-NUM-002 |
| ECS-NUM-003 | probability floor/cap | physical-parameter transform | channel algebra support | NO-SOURCE | unresolved | mismatched | project-design | 高危无出处 | ECS-NUM-003 |
| ECS-REC-001 | canonical binary \(\{det,obs\}\) object | instrument/record | record contract | CONTRADICTED/MISAPPLIED | incorrect | mismatched | project-design | contract violation | ECS-REC-001 |
| ECS-REC-002 | round-major flat geometry | record-transform | record contract | NO-SOURCE | correct | mismatched | project-design | 高危无出处 | ECS-REC-002 |
| ECS-REC-003 | consecutive-round XOR | record-transform | record contract | DIRECT | correct | matched | complete | none | ECS-REC-003 |
| ECS-REC-004 | first-round zero-prior boundary | record-transform | record contract | DIRECT | correct | bridge-open | complete | conditional-source warning | ECS-REC-004 |
| ECS-REC-005 | prefix-XOR inverse | record-transform | record contract | DERIVED | correct | bridge-open | complete | none | ECS-REC-005 |
| ECS-REC-006 | LSB raw-shot pack | serialization | record contract/PEPS/fused | NO-SOURCE | correct | mismatched | project-design | 高危无出处 | ECS-REC-006 |
| ECS-REC-007 | packed-shot inverse/canonicality | serialization | record contract | NO-SOURCE | correct | mismatched | project-design | 高危无出处 | ECS-REC-007 |
| ECS-REC-008 | packed raw-to-product bridge | instrument/composition | record contract/PEPS/fused | COMPOSITE-UNCLOSED | incorrect | mismatched | project-design | 高危无出处（组合公式整体无直接出处） | ECS-REC-008 |
| ECS-REC-009 | raw-syndrome prefix bytes | compatibility transform | record contract | NO-SOURCE | correct | bridge-open | project-design | 高危无出处 | ECS-REC-009 |
| ECS-CPTP-NUM-001 | complex128/float64 precision policy | numerical convention | channel algebra | NO-SOURCE | unresolved | bridge-open | project-design | 高危无出处 | ECS-CPTP-NUM-001 |
| ECS-CPTP-001 | Hermitian projection | numerical channel postprocess | channel algebra/exact carriers | NO-SOURCE | correct | bridge-open | complete | 高危无出处 | ECS-CPTP-001 |
| ECS-CPTP-002 | Hermitian-domain Kraus action | channel | channel algebra/exact carriers | DIRECT | correct | matched | complete | domain restriction | ECS-CPTP-002 |
| ECS-CPTP-003 | floored Z-measurement distribution | instrument/composition | exact-qubit/Axis-1 evidence | COMPOSITE-UNCLOSED | incorrect | mismatched | incomplete | 高危无出处（组合公式整体无直接出处） | ECS-CPTP-003 |
| ECS-CPTP-004 | Frobenius TP residual | diagnostic | channel algebra/tests | DERIVED | correct | matched | complete | none | ECS-CPTP-004 |
| ECS-CPTP-005 | C-order/SWAP Choi matrix | channel representation | channel algebra/tests | DERIVED | correct | bridge-open | complete | external-convention warning | ECS-CPTP-005 |
| ECS-CPTP-006 | exponential Stinespring parameterization | channel parameterization | channel algebra | DERIVED | correct | matched | project-design | finite-precision caveat | ECS-CPTP-006 |
| ECS-CPTP-007 | Gaussian Stinespring initializer | numerical/channel initializer | channel algebra test surface | NO-SOURCE | correct | bridge-open | project-design | 高危无出处 | ECS-CPTP-007 |
| ECS-CPTP-008 | single-qubit IXYZ PTM | channel representation | channel algebra/teachers | DERIVED | correct | matched | complete | none | ECS-CPTP-008 |
| ECS-CPTP-009 | PTM off-diagonal non-Pauli witness | diagnostic | channel algebra | DERIVED | correct | matched | complete | none | ECS-CPTP-009 |
| ECS-CPTP-010 | PTM off-diagonal coherence certificate | diagnostic claim | channel algebra | CONTRADICTED/MISAPPLIED | incorrect | mismatched | incomplete | nonunital counterexample | ECS-CPTP-010 |
| ECS-CHAN-001 | Pauli-generator rotations | unitary/channel primitive | channel algebra | DERIVED | correct | matched | complete | finite-domain restriction | ECS-CHAN-001 |
| ECS-CHAN-002 | commuting RXX/RYY composition | unitary composition | channel algebra | DERIVED | correct | matched | complete | mechanism-parameter bridge pending | ECS-CHAN-002 |
| ECS-CHAN-003 | conditional-state phase | unitary/mechanism primitive | channel algebra | DIRECT | correct | bridge-open | complete | catalog placement deferred | ECS-CHAN-003 |
| ECS-CHAN-004 | three-point drift mixture | channel/composition | channel algebra | COMPOSITE-UNCLOSED | incorrect | mismatched | project-design | 高危无出处（组合公式整体无直接出处） | ECS-CHAN-004 |
| ECS-CHAN-005 | arbitrary-axis rotation with norm floor | unitary/mechanism primitive | channel algebra | CONTRADICTED/MISAPPLIED | incorrect | mismatched | project-design | accepted-domain counterexamples | ECS-CHAN-005 |
| ECS-CHAN-006 | floored stochastic-Pauli Kraus set | channel/mechanism primitive | channel algebra | CONTRADICTED/MISAPPLIED | incorrect | mismatched | project-design | structural-zero and TP contradiction | ECS-CHAN-006 |
| ECS-CHAN-AD-001 | floored amplitude damping | channel/mechanism primitive | channel algebra | CONTRADICTED/MISAPPLIED | incorrect | mismatched | project-design | mechanism-off contradiction | ECS-CHAN-AD-001 |
| ECS-CHAN-PD-001 | floored stochastic-Z dephasing | channel/mechanism primitive | channel algebra | CONTRADICTED/MISAPPLIED | incorrect | mismatched | project-design | source-domain and TP contradiction | ECS-CHAN-PD-001 |
| ECS-CHAN-PD-002 | floored canonical phase damping | channel/mechanism primitive | channel algebra | CONTRADICTED/MISAPPLIED | incorrect | mismatched | project-design | endpoint coherence/TP contradiction | ECS-CHAN-PD-002 |
| ECS-CHAN-THERM-001 | zero-temperature exponential T1/T2 composite | channel/composition | channel algebra | CONTRADICTED/MISAPPLIED | incorrect | mismatched | project-design | accepted-time/domain contradiction | ECS-CHAN-THERM-001 |
| ECS-CHAN-EXC-001 | floored upward excitation | channel/mechanism primitive | channel algebra | CONTRADICTED/MISAPPLIED | incorrect | mismatched | project-design | mechanism-off contradiction | ECS-CHAN-EXC-001 |
| ECS-CHAN-RESET-001 | partial replacement/reset surrogate | channel/composition | compatibility channel algebra | ADJACENT-ONLY | incorrect | mismatched | project-design | 高危无出处（仅有邻近/二手证据） | ECS-CHAN-RESET-001 |
| ECS-CHAN-LEAKSUR-001 | qubit AD-after-Z leakage surrogate | channel/composition | compatibility channel algebra | CONTRADICTED/MISAPPLIED | incorrect | mismatched | project-design | 高危无出处（文献仅支持形式） | ECS-CHAN-LEAKSUR-001 |
| ECS-CHAN-CUSTOM-001 | fixed rotation then amplitude damping | channel/composition | compatibility channel algebra | COMPOSITE-UNCLOSED | correct | bridge-open | project-design | 高危无出处（组合公式整体无直接出处） | ECS-CHAN-CUSTOM-001 |
| ECS-CHAN-DEP2-001 | floored 15-Pauli two-qubit depolarizing | channel/mechanism primitive | compatibility channel algebra | CONTRADICTED/MISAPPLIED | incorrect | mismatched | project-design | endpoint TP contradiction | ECS-CHAN-DEP2-001 |
| ECS-CHAN-CORRREL-001 | legacy pair-loss labeled correlated relaxation | channel/mechanism primitive | compatibility channel algebra | CONTRADICTED/MISAPPLIED | incorrect | mismatched | project-design | 高危无出处（文献仅支持形式）; current-M12 object contradiction | ECS-CHAN-CORRREL-001 |
| ECS-CHAN-WEAK4-001 | fixed-unitary I/X/Z synthetic mixture | channel/composition | compatibility channel algebra | COMPOSITE-UNCLOSED | incorrect | mismatched | project-design | 高危无出处（组合公式整体无直接出处） | ECS-CHAN-WEAK4-001 |
| ECS-CHAN-READOUT-001 | asymmetric binary assignment matrix | classical channel/instrument bridge | compatibility channel algebra | NO-SOURCE | incorrect | bridge-open | project-design | 高危无出处 | ECS-CHAN-READOUT-001 |

## 4. Formula audit rows

Rows are merged here only after the extractor-reviewer gate. Distinct normalizations, regimes, and
placement rules receive distinct IDs. Batch 1A is the first closed code-enumeration gate; literature
gaps and implementation failures remain open findings rather than being normalized away.

## ECS-NUM-001 — Shared numerical-zero constant

### Formula and role
- Normalized formula: $$\epsilon_{\mathrm{num}} = 10^{-12}.$$
- Literal code realization: `NUMERICAL_ZERO = 1e-12`;
  `NUMERICAL_FLOOR = NUMERICAL_ZERO`.
- Role: bound | numerical convention | scientific threshold input
- Scientific object: one scalar is reused as an absolute zero test, relative singular-value cutoff,
  probability floor, Choi-mass gate, trace guard, rank guard, and denominator guard.
- Upstream inputs: project source constant only.
- Downstream consumers: channel algebra, Stinespring construction, exact qutrit DM, Axis-1 channel
  assembly, PEPO/PEPS truncation and normalization, source coupling, frontend interop/\(p_{ij}\),
  quantum-bath gates, and their verification surfaces.

### Code usage
| frozen file:line | qualname | service/call path | runtime/oracle/test | responsibility |
|---|---|---|---|---|
| `src/error_coupling_simulator/numerics.py:3-4` | module constants | shared support -> many installed services | runtime | defines the shared value |
| multiple consumers, frozen separately in Sections 11-13 | per-use formulas | each owning service | runtime/oracle/test | assign incompatible absolute/relative/physical meanings; audited again at each use |

### Symbols, domains, and conventions
| symbol | meaning | shape/domain | units | basis/order | source symbol |
|---|---|---|---|---|---|
| \(\epsilon_{\mathrm{num}}\) | project numerical-zero value | positive real scalar | changes by consumer; often dimensionless | n/a | none found |

### Evidence verdict
- provenance_status: `NO-SOURCE`
- required visible risk marker: **高危无出处**
- formula_correctness: unresolved
- application_fit: bridge-open
- value_provenance: project-design
- epistemic_class: project numerical convention; not a universal physical or numerical theorem

### Exact literature sources
| source ID | publication/version | PDF/hash | exact locator | visually checked page | source says | source does not say |
|---|---|---|---|---|---|---|
| none closing | recorded local/external search | n/a | Search `S-B1A-NUM-001` | n/a | standard channel sources require valid probabilities and CPTP normalization | no source selects \(10^{-12}\) for all of the code's heterogeneous uses |

### Source-to-code mapping
| source expression | code expression | transformation | exact/approximate | assumption | status |
|---|---|---|---|---|---|
| none | `1e-12` | project choice | n/a | one value is adequate across float64/complex128 and multiple scales | open |

### Operation replay / derivation
| input | transformation | assumption | output | source locator or derivation step | status |
|---|---|---|---|---|---|
| decimal literal \(10^{-12}\) | bind two aliases to the same float | IEEE-754 binary64 representation is adequate | shared scalar | code lines 3-4 | exact code replay; scientific choice unclosed |

### Composite compatibility
| component | source | object/device/regime | composition bridge | compatible? | risk |
|---|---|---|---|---|---|
| absolute residual test | none exact | dimensionless residual | same value reused | unresolved | scale dependence |
| relative singular cutoff | none exact | spectrum relative to leading singular value | multiply by \(s_0\) at consumers | unresolved | not the same object as an absolute floor |
| physical probability floor | none exact | stochastic probability | same scalar inserted as mass | no general justification | changes the simulated channel |

### Parameter/value provenance
| parameter | value/units | provenance kind | exact locator | transform | allowed claim | forbidden claim |
|---|---|---|---|---|---|---|
| \(\epsilon_{\mathrm{num}}\) | \(10^{-12}\), consumer-dependent units | project-design | `numerics.py:3` | none | frozen implementation convention | literature-derived accuracy, universal error bound, or physical probability |

### Assumptions and correct-place audit
- Assumptions: binary64/complex128 roundoff and all consumer scales make \(10^{-12}\) conservative.
- Simplifications and error bounds: no global forward-error derivation or scale audit was found.
- Failure regime: rescaled matrices, float32 paths, tiny physical probabilities, and scientific
  conclusions made by comparing a value to the same shared threshold.
- Why this formula belongs here: it changes pruning, branch survival, pass/fail gates, and physical
  channels rather than serving only display formatting.
- Schedule/instrument/record bridge: consumer-specific; open until each downstream row is audited.
- Alternative formulation/invariant: dimensional/relative error budgets derived per operation and
  precision, plus exact zero where the scientific model requires zero.
- Verdict: bridge-open

### Independent checks
| invariant/reference | independent route | falsifier | shared blind spot? | result |
|---|---|---|---|---|
| use inventory | repository-wide symbol reference scan | an unlisted scientific consumer | no | many heterogeneous uses confirmed |
| literature closure | local RAG/KG plus AnySearch academic query | an exact source selecting the same scalar for all uses | search-index blind spots possible | none found; remains open |

### Human verification
- [ ] formula transcription checked
- [ ] exact source page checked
- [ ] symbol/unit convention checked
- [ ] derivation replayed
- [ ] application location checked
- [ ] composite bridge accepted
- Human verdict: unchecked
- Notes: every use-specific scientific formula must carry its own tolerance/value audit; this row
  does not pre-clear any consumer.

## ECS-NUM-002 — Positive floor

### Formula and role
- Normalized formula: $$F_+(x)=\max(\epsilon_{\mathrm{num}},x).$$
- Literal code realization: `return max(NUMERICAL_ZERO, float(value))`.
- Role: bound | normalization guard | physical-coefficient helper
- Scientific object: scalar clamping map used before square roots and denominators.
- Upstream inputs: arbitrary Python-float-coercible value.
- Downstream consumers: principally `carrier.channels`; additional consumers use the base constant
  directly.

### Code usage
| frozen file:line | qualname | service/call path | runtime/oracle/test | responsibility |
|---|---|---|---|---|
| `src/error_coupling_simulator/numerics.py:7-10` | `positive_floor` | channel_algebra -> channel constructors | runtime | replaces values below \(10^{-12}\) |

### Symbols, domains, and conventions
| symbol | meaning | shape/domain | units | basis/order | source symbol |
|---|---|---|---|---|---|
| \(x\) | input coefficient | documented only as float; implementation accepts nonfinite values | inherited | n/a | none |
| \(F_+(x)\) | floored coefficient | \([\epsilon,\infty]\), with NaN mapped to \(\epsilon\) by Python operand order | inherited | n/a | none |

### Evidence verdict
- provenance_status: `NO-SOURCE`
- required visible risk marker: **高危无出处**
- formula_correctness: unresolved
- application_fit: bridge-open
- value_provenance: project-design
- epistemic_class: project numerical helper with physical downstream effects

### Exact literature sources
| source ID | publication/version | PDF/hash | exact locator | visually checked page | source says | source does not say |
|---|---|---|---|---|---|---|
| none closing | search ledger `S-B1A-NUM-001` | n/a | local and academic search | n/a | no exact hit | no source authorizes replacing negative, zero, or NaN physical coefficients by \(10^{-12}\) |

### Source-to-code mapping
| source expression | code expression | transformation | exact/approximate | assumption | status |
|---|---|---|---|---|---|
| none | `max(1e-12, float(x))` | direct clamp | exact code | invalid values need not fail closed | open |

### Operation replay / derivation
| input | transformation | assumption | output | source locator or derivation step | status |
|---|---|---|---|---|---|
| \(x\) | float coercion, then ordered Python `max` | finite real expected | \(F_+(x)\) | code lines 7-10 | replayed |

### Composite compatibility
| component | source | object/device/regime | composition bridge | compatible? | risk |
|---|---|---|---|---|---|
| clamp | none exact | numerical stabilization | feeds physical Kraus amplitudes | unresolved | numerical repair becomes model mass |

### Parameter/value provenance
| parameter | value/units | provenance kind | exact locator | transform | allowed claim | forbidden claim |
|---|---|---|---|---|---|---|
| lower floor | \(10^{-12}\) | project-design | `numerics.py:3,10` | \(\max\) | implementation behavior | physical lower bound or derived stability guarantee |

### Assumptions and correct-place audit
- Assumptions: inputs are finite, nonnegative, and a positive replacement is preferable to rejection.
- Simplifications and error bounds: none stated.
- Failure regime: \(x<0\), \(-\infty\), or NaN silently becomes \(\epsilon\); \(+\infty\) remains infinite.
- Why this formula belongs here: downstream square-root coefficients can change a channel.
- Schedule/instrument/record bridge: deferred to the channel rows in Batch 1B.
- Alternative formulation/invariant: validate the physical domain; use exact zero where allowed; use
  a local numerical guard only for a derived denominator with an error bound.
- Verdict: bridge-open

### Independent checks
| invariant/reference | independent route | falsifier | shared blind spot? | result |
|---|---|---|---|---|
| edge-case table | live calls on \(-\infty,-1,0,10^{-15},\mathrm{NaN},+\infty\) | fail-closed behavior | no | negative/zero/NaN -> \(10^{-12}\); \(+\infty\) unchanged |

### Human verification
- [ ] formula transcription checked
- [ ] exact source page checked
- [ ] symbol/unit convention checked
- [ ] derivation replayed
- [ ] application location checked
- [ ] composite bridge accepted
- Human verdict: unchecked
- Notes:

## ECS-NUM-003 — Probability floor and cap

### Formula and role
- Normalized formula:
  $$F_p(p)=\min\!\left(1,\max(\epsilon_{\mathrm{num}},p)\right).$$
- Literal code realization: `return min(1.0, positive_floor(float(value)))`.
- Role: channel | physical-parameter transform | numerical guard
- Scientific object: map from caller-supplied probability to the probability used in channel
  construction.
- Upstream inputs: mechanism probabilities and rates already converted to per-application
  probabilities.
- Downstream consumers: stochastic Pauli, amplitude/phase damping, leakage, reset, readout,
  crosstalk, and two-qubit channel constructors in `carrier.channels`.

### Code usage
| frozen file:line | qualname | service/call path | runtime/oracle/test | responsibility |
|---|---|---|---|---|
| `src/error_coupling_simulator/numerics.py:13-16` | `probability_floor` | channel_algebra -> many Kraus constructors | runtime | floors zero/invalid-low values and caps high values |
| `tests/test_carrier_channels_units.py:119-125,537-544` | independent literal copy and pinned floor test | channel_algebra acceptance | test | explicitly requires absent Pauli terms to acquire \(10^{-12}\) mass |

### Symbols, domains, and conventions
| symbol | meaning | shape/domain | units | basis/order | source symbol |
|---|---|---|---|---|---|
| \(p\) | requested probability | physically \([0,1]\); implementation accepts any float-coercible value | dimensionless | mechanism-specific | conventional \(p\) |
| \(F_p(p)\) | probability used in code | \([\epsilon,1]\) | dimensionless | mechanism-specific | none for the floor |

### Evidence verdict
- provenance_status: `NO-SOURCE`
- required visible risk marker: **高危无出处**
- formula_correctness: unresolved
- application_fit: mismatched
- value_provenance: project-design
- epistemic_class: unsourced physical-parameter rewrite, not a numerical-only tolerance

### Exact literature sources
| source ID | publication/version | PDF/hash | exact locator | visually checked page | source says | source does not say |
|---|---|---|---|---|---|---|
| none closing | search ledger `S-B1A-NUM-001` | n/a | exact floor/coefficient search | n/a | standard Kraus formulas retain \(p=0\) as zero error mass | no exact source inserts \(10^{-12}\) into every zero probability or maps NaN to a valid probability |

### Source-to-code mapping
| source expression | code expression | transformation | exact/approximate | assumption | status |
|---|---|---|---|---|---|
| physical \(p\in[0,1]\) | \(\min(1,\max(10^{-12},p))\) | unsourced clamp | model-changing | every zero/invalid input should become a live event | open/mismatched |

### Operation replay / derivation
| input | transformation | assumption | output | source locator or derivation step | status |
|---|---|---|---|---|---|
| missing or zero Pauli component | substitute \(\epsilon\), then square-root in consumer | negligible mass is harmless | nonzero Kraus branch | code + acceptance test | replayed; no error budget |
| NaN/negative | ordered `max` maps to \(\epsilon\) | invalid input should not fail | apparently valid probability | live edge-case check | contradicted with fail-closed scientific input discipline |

### Composite compatibility
| component | source | object/device/regime | composition bridge | compatible? | risk |
|---|---|---|---|---|---|
| standard channel probability | mechanism-specific primary source, audited Batch 1B | exact zero may represent mechanism off | global floor inserted before Kraus construction | no general bridge | changes ideal/no-mechanism controls and normalization |

### Parameter/value provenance
| parameter | value/units | provenance kind | exact locator | transform | allowed claim | forbidden claim |
|---|---|---|---|---|---|---|
| lower probability | \(10^{-12}\) | project-design | `numerics.py:3,16` | clamp | exact current code behavior | source-derived physical floor or exact mechanism-off channel |

### Assumptions and correct-place audit
- Assumptions: \(10^{-12}\) changes no claim-bearing observable and invalid inputs should be repaired.
- Simplifications and error bounds: no diamond/TV/record-law bound across repeated uses was found.
- Failure regime: exact controls, sparse Pauli channels, sums at one, invalid/nonfinite input, and long
  schedules where injected mass accumulates.
- Why this formula belongs here: it changes physical Kraus weights; it is not a reporting tolerance.
- Schedule/instrument/record bridge: repeated channel placements can accumulate the artificial mass;
  quantified propagation remains for Batch 1B/11.
- Alternative formulation/invariant: validate \(0\le p\le1\), preserve exact zero, and stabilize only
  derived divisions/eigendecompositions with an explicit error budget.
- Verdict: mismatched

### Independent checks
| invariant/reference | independent route | falsifier | shared blind spot? | result |
|---|---|---|---|---|
| edge-domain behavior | live table over negative, zero, NaN, \(>1\), infinities | invalid input rejected and zero preserved | no | falsified: invalid/zero silently rewritten |
| acceptance independence | test recomputes identical clamp | a source-independent physical oracle | yes, same formula is pinned | behavior confirmed, scientific validity not checked |

### Human verification
- [ ] formula transcription checked
- [ ] exact source page checked
- [ ] symbol/unit convention checked
- [ ] derivation replayed
- [ ] application location checked
- [ ] composite bridge accepted
- Human verdict: unchecked
- Notes: downstream channel rows must quantify the actual TP/channel/record impact rather than call
  \(10^{-12}\) negligible by assertion.

<!-- BATCH-1A-RECORD-ROWS -->

## ECS-REC-001 — Canonical binary record object and enforcement

### Formula and role
- Normalized formula:
  $$D\in\mathbb F_2^{N\times n_D},\qquad
    O\in\mathbb F_2^{N}\ \text{or}\ \mathbb F_2^{N\times n_O},\qquad
    \dim_0 D=\dim_0 O=N.$$
- Literal code realization: `_binary_array`, `RecordBatch.__post_init__`, and
  `RecordBatch.to_det_obs`.
- Role: instrument | record-transform | scientific object
- Scientific object: the simulator product \(\{det,obs\}\), with evaluator-only process truth
  excluded from learner-visible provenance.
- Upstream inputs: carrier-emitted detector events and terminal logical-observable flips.
- Downstream consumers: metrics, optional DEM/decoder reduction, artifact I/O, and every
  record-bearing service.

### Code usage
| frozen file:line | qualname | service/call path | runtime/oracle/test | responsibility |
|---|---|---|---|---|
| `src/error_coupling_simulator/carrier/records.py:36-46` | `_binary_array` | all `RecordBatch` construction | runtime | intended binary/domain validation |
| `src/error_coupling_simulator/carrier/records.py:49-84` | `RecordBatch` | frontend/Axis-1/packed carriers -> product | runtime | shape, shot, visibility, and payload contract |
| `src/error_coupling_simulator/carrier/__init__.py:11-18,31-48` | facade | public carrier API | runtime facade | re-export only; no independent formula |

### Symbols, domains, and conventions
| symbol | meaning | shape/domain | units | basis/order | source symbol |
|---|---|---|---|---|---|
| \(N\) | shots | nonnegative integer | shots | outer/row index | history sample count |
| \(D\) | temporal detector events | binary matrix | bits | shot-major; detector coordinate defined by compiler/carrier | source detector history \(\mathbf x\) |
| \(O\) | logical-observable flips | binary vector/matrix | bits | shot-major | optional terminating logical measurement is only adjacent |

### Evidence verdict
- provenance_status: `CONTRADICTED/MISAPPLIED`
- required visible risk marker: none for this status; the exact combined \(\{det,obs\}\) product
  remains a separate source-closure gap.
- formula_correctness: incorrect
- application_fit: mismatched
- value_provenance: project-design
- epistemic_class: binding project object contract whose implementation does not preserve its domain

### Exact literature sources
| source ID | publication/version | PDF/hash | exact locator | visually checked page | source says | source does not say |
|---|---|---|---|---|---|---|
| SRC-BKY-DEM-v1 | Blume-Kohout & Young, *Estimating detector error models from syndrome data*, arXiv:2504.14643v1 (2025), preprint | `docs/papers/qec_dem_estimation_syndrome_2504.14643.pdf`; `5e821a6a951a4ef342ddb80caf53e62bd8869af25a4f39ad5d6de8f4b8336bbd` | PDF index 1 / printed p.2, Sec. 1.2; index 2 / printed p.3, Fig. 1 | yes | detector histories are binary arrays; logical measurement may be included | does not specify this project's one-/multi-observable array API, provenance firewall, or custom composition |

### Source-to-code mapping
| source expression | code expression | transformation | exact/approximate | assumption | status |
|---|---|---|---|---|---|
| binary detector history | `np.asarray -> np.uint8 -> out > 1` | validation after narrowing conversion | not equivalent on accepted integer domain | source values are already 0/1 and arrays never mutate | contradicted |
| optional logical measurement | `obs` flip field | project reduction to flip bit(s) | adjacent only | terminal instrument defines same logical object | bridge-open |

### Operation replay / derivation
| input | transformation | assumption | output | source locator or derivation step | status |
|---|---|---|---|---|---|
| integer 256, 257, -256, -255 | cast to `uint8` first | narrowing is harmless | 0,1,0,1 accepted | live adversarial replay | failed contract |
| valid contiguous uint8 array | `np.ascontiguousarray` may alias input; returned arrays remain writable | frozen dataclass implies immutable scientific record | caller can mutate a bit to 7 after validation | live adversarial replay | failed contract |
| evaluator-only truth key | recursive key scan | all forbidden objects use enumerated spellings/container types | rejection | code lines 345-359 | partial project guard; not a formula closure |

### Composite compatibility
| component | source | object/device/regime | composition bridge | compatible? | risk |
|---|---|---|---|---|---|
| detector bits | SRC-BKY-DEM-v1 | binary detector history | code binary validator | no over public accepted inputs | modulo-256 alias |
| observable flips | adjacent only | terminal logical instrument | unchanged alongside detector fold | open | object/visibility mapping is project-specific |
| frozen record | project dataclass choice | scientific artifact | mutable NumPy payload | no | post-validation corruption |

### Parameter/value provenance
| parameter | value/units | provenance kind | exact locator | transform | allowed claim | forbidden claim |
|---|---|---|---|---|---|---|
| binary alphabet | \(\{0,1\}\) | direct for detector history; project for combined API | SRC-BKY-DEM-v1 p.2 + code docstring | uint8 | intended record alphabet | claim that runtime enforcement guarantees it |

### Assumptions and correct-place audit
- Assumptions: upstream always supplies immutable 0/1 arrays and never mutates returned storage.
- Simplifications and error bounds: none; invalid values alias exactly into valid records.
- Failure regime: public/manual construction, corrupt integer payloads congruent to 0/1 modulo 256,
  writable-array reuse, and any downstream artifact trusting validation.
- Why this formula belongs here: it defines the scored scientific product.
- Schedule/instrument/record bridge: detector and observable instruments are audited in owning
  batches; this row only fixes the shared output domain.
- Alternative formulation/invariant: validate the original array before narrowing, reject
  non-byte/nonbinary values, copy or expose read-only payloads, and independently validate serialized
  records on load.
- Verdict: mismatched

### Independent checks
| invariant/reference | independent route | falsifier | shared blind spot? | result |
|---|---|---|---|---|
| binary-domain enforcement | reviewer-devised inputs 256, 257, -256, -255 | any accepted nonbinary input | no | falsified; all four alias to valid bits |
| post-validation stability | mutate `RecordBatch.det` in place | observed value no longer binary | no | falsified; value 7 is returned |
| canonical acceptance | `test_record_batch_units.py` | adversarial pre-cast/mutation case | yes, only normal-domain cases | does not cover finding |

### Human verification
- [ ] formula transcription checked
- [ ] exact source page checked
- [ ] symbol/unit convention checked
- [ ] derivation replayed
- [ ] application location checked
- [ ] composite bridge accepted
- Human verdict: unchecked
- Notes: source and tests are read-only; no fix is made in this audit.

## ECS-REC-002 — Round-major flat geometry

### Formula and role
- Normalized formula:
  $$i(r,j)=r\,n_{\mathrm{stab}}+j,\quad
    0\le r<R,\quad0\le j<n_{\mathrm{stab}},\quad
    n_{\mathrm{bits}}=R\,n_{\mathrm{stab}}.$$
- Literal code realization: reshape final axis to \((R,n_{\mathrm{stab}})\); header and stride
  geometry use the product \(R n_{\mathrm{stab}}\).
- Role: record-transform | serialization convention
- Scientific object: mapping between temporal/stabilizer coordinates and flat record coordinates.
- Upstream inputs: \(R,n_{\mathrm{stab}}\), flat raw syndrome array.
- Downstream consumers: temporal fold, packing, prefix access, native/PEPS record bridges.

### Code usage
| frozen file:line | qualname | service/call path | runtime/oracle/test | responsibility |
|---|---|---|---|---|
| `carrier/record_fold.py:18-32,46-53` | `s_to_det`, `det_to_s` | public fold | runtime | reshape/coordinate order |
| `carrier/records.py:119-125,203-210,248-261` | unpack/from_raw/header geometry | packed record service | runtime | width and stride geometry |

### Symbols, domains, and conventions
| symbol | meaning | shape/domain | units | basis/order | source symbol |
|---|---|---|---|---|---|
| \(r\) | round index | integers \(0,\ldots,R-1\) | rounds | outer coordinate within shot | time index |
| \(j\) | stabilizer index | integers \(0,\ldots,n_{\rm stab}-1\) | checks | inner coordinate | syndrome-bit index |
| \(i\) | flat index | \(0,\ldots,Rn_{\rm stab}-1\) | bits | C-order round-major | source flattens to an \(N\)-bit string but does not pin this storage layout |

### Evidence verdict
- provenance_status: `NO-SOURCE`
- required visible risk marker: **高危无出处**
- formula_correctness: correct
- application_fit: mismatched
- value_provenance: project-design
- epistemic_class: project coordinate convention with an unenforced public domain

### Exact literature sources
| source ID | publication/version | PDF/hash | exact locator | visually checked page | source says | source does not say |
|---|---|---|---|---|---|---|
| SRC-BKY-DEM-v1 | arXiv:2504.14643v1 | local PDF/hash above | printed p.2: \(M\times(n-k)\); printed p.3: first-SEC bits followed by second-SEC bits in example | yes | a time-by-check detector history and a flattened \(N=M(n-k)\) string | no general byte, NumPy reshape, stabilizer schedule, or package index contract |

### Source-to-code mapping
| source expression | code expression | transformation | exact/approximate | assumption | status |
|---|---|---|---|---|---|
| \(M\times(n-k)\) history | \((R,n_{\rm stab})\) C-order reshape | rename \(M\to R,n-k\to n_{\rm stab}\); choose within-round order | exact geometry; order project-defined | compiler and carrier share stabilizer order | form adjacent, order open |

### Operation replay / derivation
| input | transformation | assumption | output | source locator or derivation step | status |
|---|---|---|---|---|---|
| flat width \(R n_{\rm stab}\) | NumPy C-order reshape | \(R,n_{\rm stab}\) are positive integers | round-major matrix | code | exact for valid domain |
| \(R=1.9,n=1.2\) | `int` coercion | numeric coercion means integral validation | \(R=n=1\), accepted | live adversarial replay | domain enforcement failed |

### Composite compatibility
| component | source | object/device/regime | composition bridge | compatible? | risk |
|---|---|---|---|---|---|
| temporal dimension | direct/adjacent | detector histories | rename to \(R\) | yes |
| stabilizer order | compiler schedule | device/circuit-specific | flat inner index | pending Batch 2/6/8 | wrong order changes every observable |

### Parameter/value provenance
| parameter | value/units | provenance kind | exact locator | transform | allowed claim | forbidden claim |
|---|---|---|---|---|---|---|
| order | round-major, stabilizer-inner | project-design | code/docstrings | reshape | frozen package convention | literature-universal order |

### Assumptions and correct-place audit
- Assumptions: geometry values are exact positive integers and the upstream schedule supplies the same
  stabilizer order.
- Simplifications and error bounds: none; a permutation is an exact but scientifically different
  coordinate map.
- Failure regime: float-like geometry silently truncated; carrier/compiler order mismatch.
- Why this formula belongs here: metrics and decoders attach meaning to each detector coordinate.
- Schedule/instrument/record bridge: cross-service order checks remain open for owning batches.
- Alternative formulation/invariant: strict integral validation plus explicit stabilizer-ID layout in
  the artifact.
- Verdict: mismatched

### Independent checks
| invariant/reference | independent route | falsifier | shared blind spot? | result |
|---|---|---|---|---|
| reshape index law | hand-built index table | any \(i\ne rn+j\) | no | passes valid inputs |
| positive-integer domain | fractional geometry | accepted truncation | no | falsified |

### Human verification
- [ ] formula transcription checked
- [ ] exact source page checked
- [ ] symbol/unit convention checked
- [ ] derivation replayed
- [ ] application location checked
- [ ] composite bridge accepted
- Human verdict: unchecked
- Notes:

## ECS-REC-003 — Consecutive-round detector XOR

### Formula and role
- Normalized formula:
  $$d_{r,j}=s_{r,j}\oplus s_{r-1,j},\qquad r=1,\ldots,R-1.$$
- Literal code realization: `det[..., 1:, :] = sr[..., 1:, :] ^ sr[..., :-1, :]`.
- Role: record-transform
- Scientific object: temporal change events for one stabilizer across consecutive rounds.
- Upstream inputs: binary raw syndrome outcomes in matched round/stabilizer order.
- Downstream consumers: canonical `RecordBatch.det`, record metrics, DEM/decoder reduction.

### Code usage
| frozen file:line | qualname | service/call path | runtime/oracle/test | responsibility |
|---|---|---|---|---|
| `carrier/record_fold.py:15-37` | `s_to_det` | packed raw syndrome -> product record | runtime | forward XOR |
| `carrier/records.py:274-306` | `PackedShotBatch.to_record_batch` | fused/PEPS -> product | runtime | places fold at package boundary |

### Symbols, domains, and conventions
| symbol | meaning | shape/domain | units | basis/order | source symbol |
|---|---|---|---|---|---|
| \(s_{r,j}\) | stabilizer measurement bit | \(\mathbb F_2\) | bit | fixed check \(j\), round \(r\) | \(S_j(t_r)\) |
| \(d_{r,j}\) | detector/change bit | \(\mathbb F_2\) | bit | same coordinate | \(x\) / detector parity |
| \(\oplus\) | XOR/addition modulo two | \(\mathbb F_2\) | n/a | n/a | XOR |

### Evidence verdict
- provenance_status: `DIRECT`
- required visible risk marker: none
- formula_correctness: correct
- application_fit: matched
- value_provenance: complete
- epistemic_class: direct detector-history identity on the declared binary domain

### Exact literature sources
| source ID | publication/version | PDF/hash | exact locator | visually checked page | source says | source does not say |
|---|---|---|---|---|---|---|
| SRC-BKY-DEM-v1 | Blume-Kohout & Young, arXiv:2504.14643v1 (2025) | local PDF/hash above | PDF index 1 / printed p.2, Sec. 1.2; index 2 / printed p.3, Fig. 1 | yes | XOR of consecutive syndrome measurements is a detector/change event | not every possible Stim detector is restricted to this two-measurement form |
| SRC-FOWLER-LEAK-v1 | Fowler, *Coping with qubit leakage in topological codes*, arXiv:1308.6642v1; Phys. Rev. A 88, 042308 (2013), DOI 10.1103/PhysRevA.88.042308 | `docs/papers/fowler_leakage_topological_codes_1308.6642.pdf`; `8450cca9581beb0cb1a6d3d990a47808bc2177e30402b3129b7a09d7abfaf59a` | PDF index 0 / printed p.1 and index 1 / printed p.2, Sec. I, Figs. 2-3 | yes | a change from the previous measurement is a detection event | no general first-boundary or package layout equation |

### Source-to-code mapping
| source expression | code expression | transformation | exact/approximate | assumption | status |
|---|---|---|---|---|---|
| \(S_j(t_{r-1})\oplus S_j(t_r)\) | `sr[...,1:,:] ^ sr[...,:-1,:]` | vectorize shots, rounds, checks | exact | binary inputs and identical check/order at both times | closed |

### Operation replay / derivation
| input | transformation | assumption | output | source locator or derivation step | status |
|---|---|---|---|---|---|
| \((s_{r-1,j},s_{r,j})\) | four-case XOR table | \(\mathbb F_2\) | 1 iff the syndrome changes | source p.2 | closed |

### Composite compatibility
| component | source | object/device/regime | composition bridge | compatible? | risk |
|---|---|---|---|---|---|
| consecutive syndrome parity | SRC-BKY-DEM-v1 | repeated QEC checks | vectorized package fold | yes for current packed carriers | public API domain validation is handled by REC-001/002 |

### Parameter/value provenance
| parameter | value/units | provenance kind | exact locator | transform | allowed claim | forbidden claim |
|---|---|---|---|---|---|---|
| no continuous value | n/a | complete | source | n/a | exact valid-domain identity | correctness for nonbinary inputs or arbitrary detector definitions |

### Assumptions and correct-place audit
- Assumptions: same stabilizer meaning/order across rounds; binary hard outcomes; no omitted
  measurement term in the declared detector.
- Simplifications and error bounds: exact over \(\mathbb F_2\).
- Failure regime: adaptive/changing checks, nonbinary soft records, arbitrary Stim parity detectors,
  or invalid inputs accepted by the public function.
- Why this formula belongs here: the packed carriers store raw \(s\), while the product is \(d\).
- Schedule/instrument/record bridge: matched for fused and PEPS raw-syndrome paths; compiler-specific
  detector definitions are re-audited in Batch 2.
- Alternative formulation/invariant: a sparse parity-check matrix over measurement records; this row
  is its two-consecutive-measurement specialization.
- Verdict: matched

### Independent checks
| invariant/reference | independent route | falsifier | shared blind spot? | result |
|---|---|---|---|---|
| linear-map identity | hand-built block lower-bidiagonal GF(2) matrix | mismatch on any state | no shared code | all \(2^{12}=4096\) states pass at \(R=4,n=3\) |
| canonical tests | explicit examples/round trip | wrong XOR or order | shares declared formula | 3 tests pass; not source-independent |

### Human verification
- [ ] formula transcription checked
- [ ] exact source page checked
- [ ] symbol/unit convention checked
- [ ] derivation replayed
- [ ] application location checked
- [ ] composite bridge accepted
- Human verdict: unchecked
- Notes:

## ECS-REC-004 — First-round detector boundary

### Formula and role
- Normalized formula:
  $$d_{0,j}=s^{\mathrm{prior}}_j\oplus s_{0,j};
    \qquad\text{code fixes }s^{\mathrm{prior}}_j=0,\text{ hence }d_{0,j}=s_{0,j}.$$
- Literal code realization: `det[..., 0, :] = sr[..., 0, :]`.
- Role: record-transform | boundary condition
- Scientific object: initialization-sensitive first detector event.
- Upstream inputs: first measured syndrome; implicit a-priori syndrome.
- Downstream consumers: every packed carrier record and prefix/multitime metric.

### Code usage
| frozen file:line | qualname | service/call path | runtime/oracle/test | responsibility |
|---|---|---|---|---|
| `carrier/record_fold.py:33-35` | `s_to_det` | packed carriers -> canonical record | runtime | hardcodes zero prior |
| `carrier/within_cycle.py:821-850` | `FusedWithinCycleSampler.build_codestate` | fused source -> fold | runtime upstream | verifies stabilizer \(+1\) codestate, supporting zero prior |
| `carrier/peps/trajectory.py:779-815` | PEPS codestate/trajectory | PEPS source -> fold | runtime upstream | begins from code state and emits raw syndromes |

### Symbols, domains, and conventions
| symbol | meaning | shape/domain | units | basis/order | source symbol |
|---|---|---|---|---|---|
| \(s^{\rm prior}_j\) | syndrome value before recorded measurements | \(\mathbb F_2\) | bit | same stabilizer \(j\) | \(S_j(t_0)\) in source |
| \(s_{0,j}\) | first recorded measurement | \(\mathbb F_2\) | bit | round 0 | \(S_j(t_1)\) |

### Evidence verdict
- provenance_status: `DIRECT`
- required visible risk marker: none
- formula_correctness: correct
- application_fit: bridge-open
- value_provenance: complete
- epistemic_class: direct conditional identity; application requires an explicit initialization bridge

### Exact literature sources
| source ID | publication/version | PDF/hash | exact locator | visually checked page | source says | source does not say |
|---|---|---|---|---|---|---|
| SRC-BKY-DEM-v1 | arXiv:2504.14643v1 | local PDF/hash above | PDF index 1 / printed p.2 Sec. 1.2 and footnote 2; index 2 / printed p.3 Fig. 1 | yes | a-priori \(t=0\) values are combined by XOR; zero if initialized into a code state; initializing SEC results can instead replace them | does not license unconditional \(d_0=s_0\) for arbitrary histories |

### Source-to-code mapping
| source expression | code expression | transformation | exact/approximate | assumption | status |
|---|---|---|---|---|---|
| \(x_1=S_j(t_0)\oplus S_j(t_1)\) | `det[...,0,:]=sr[...,0,:]` | substitute \(S_j(t_0)=0\) | exact conditional | code state with known \(+1\) stabilizers | source-closed condition; API bridge implicit |

### Operation replay / derivation
| input | transformation | assumption | output | source locator or derivation step | status |
|---|---|---|---|---|---|
| prior 0, first bit \(s_0\) | \(0\oplus s_0\) | initialized code state | \(d_0=s_0\) | source Fig. 1 | closed |
| prior 1, first bit \(s_0\) | code omits prior | generic input allowed | wrong first detector | source footnote contrary case | failure regime |

### Composite compatibility
| component | source | object/device/regime | composition bridge | compatible? | risk |
|---|---|---|---|---|---|
| zero prior | SRC-BKY-DEM-v1 conditional | initialized code state | fused codestate check | yes |
| zero prior | same conditional | PEPS codestate | PEPS construction | likely yes; full instrument reviewed Batch 8 |
| public `s_to_det` / `from_raw_syndromes` | no explicit prior parameter | arbitrary caller history | implicit zero | not closed | silent boundary mislabel |

### Parameter/value provenance
| parameter | value/units | provenance kind | exact locator | transform | allowed claim | forbidden claim |
|---|---|---|---|---|---|---|
| \(s^{\rm prior}=0\) | binary zero | direct conditional + current codestate design | source p.2-3; within-cycle code | substitution | current initialized-carrier path | arbitrary histories or initialization-by-measurement path |

### Assumptions and correct-place audit
- Assumptions: recorded round 0 follows preparation in the \(+1\) eigenspace of every measured
  stabilizer and the check set/order is unchanged.
- Simplifications and error bounds: exact if the assumption holds; otherwise a deterministic bit
  error, not a small approximation.
- Failure regime: histories beginning after an initializing SEC, nontrivial known prior syndromes,
  changing stabilizers, or generic callers.
- Why this formula belongs here: the first coordinate affects every full-record metric and decoder.
- Schedule/instrument/record bridge: concrete fused path verifies \(+1\) stabilizers; the public
  record API does not carry or assert the prior, so the general bridge remains open.
- Alternative formulation/invariant: accept explicit `prior_syndrome` or artifact metadata and
  compute \(s^{prior}\oplus s_0\).
- Verdict: bridge-open

### Independent checks
| invariant/reference | independent route | falsifier | shared blind spot? | result |
|---|---|---|---|---|
| source condition | visual footnote and Fig. 1 | nonzero/replaced prior | no | unconditional form falsified; conditional form verified |
| installed fused precondition | codestate expectation checks | stabilizer not \(+1\) | code shares project assumptions but not fold implementation | supports current fused path |

### Human verification
- [ ] formula transcription checked
- [ ] exact source page checked
- [ ] symbol/unit convention checked
- [ ] derivation replayed
- [ ] application location checked
- [ ] composite bridge accepted
- Human verdict: unchecked
- Notes:

<!-- BATCH-1A-RECORD-ROWS-2 -->

## ECS-REC-005 — Prefix-XOR inverse

### Formula and role
- Normalized formula:
  $$s_{r,j}=s^{\mathrm{prior}}_j\oplus\bigoplus_{k=0}^{r}d_{k,j};
    \qquad\text{code fixes }s^{\mathrm{prior}}_j=0.$$
- Literal code realization: `np.bitwise_xor.accumulate(dr, axis=-2)`.
- Role: record-transform
- Scientific object: invert the temporal detector history back to raw syndrome history.
- Upstream inputs: binary detector bits, geometry, and implicit prior.
- Downstream consumers: public compatibility API and exact-record reconstruction checks; current
  product path uses the forward direction.

### Code usage
| frozen file:line | qualname | service/call path | runtime/oracle/test | responsibility |
|---|---|---|---|---|
| `carrier/record_fold.py:40-54` | `det_to_s` | public carrier/PEPS/PEPO compatibility | runtime support | prefix inverse |
| `carrier/__init__.py:11,42` | facade | public API | facade | re-export only |

### Symbols, domains, and conventions
| symbol | meaning | shape/domain | units | basis/order | source symbol |
|---|---|---|---|---|---|
| \(d_{k,j}\) | detector bit | \(\mathbb F_2\) | bit | round/check | source detector \(x\) |
| \(\bigoplus\) | prefix XOR | finite GF(2) sum | n/a | increasing round | derived |

### Evidence verdict
- provenance_status: `DERIVED`
- required visible risk marker: none
- formula_correctness: correct
- application_fit: bridge-open
- value_provenance: complete
- epistemic_class: [ours-derived] algebraic inverse of direct detector XOR

### Exact literature sources
| source ID | publication/version | PDF/hash | exact locator | visually checked page | source says | source does not say |
|---|---|---|---|---|---|---|
| SRC-BKY-DEM-v1 | arXiv:2504.14643v1 | local PDF/hash above | printed p.2 Sec. 1.2; printed p.3 Fig. 1 | yes | forward consecutive XOR with explicit prior | does not print this prefix-inverse implementation |

### Source-to-code mapping
| source expression | code expression | transformation | exact/approximate | assumption | status |
|---|---|---|---|---|---|
| \(d_k=s_{k-1}\oplus s_k\) | `xor.accumulate(d, axis=round)` | telescope over GF(2) | exact | same zero-prior boundary | closed [ours-derived] |

### Operation replay / derivation
| input | transformation | assumption | output | source locator or derivation step | status |
|---|---|---|---|---|---|
| \(\oplus_{k=0}^{r}d_k\) | substitute \(d_0=s_0\), \(d_k=s_{k-1}\oplus s_k\); cancel every interior \(s_k\) twice | GF(2), zero prior | \(s_r\) | algebraic telescoping | closed |

### Composite compatibility
| component | source | object/device/regime | composition bridge | compatible? | risk |
|---|---|---|---|---|---|
| forward fold | REC-003/004 | binary record | inverse accumulate | yes on valid domain | inherits implicit-prior and validation gaps |

### Parameter/value provenance
| parameter | value/units | provenance kind | exact locator | transform | allowed claim | forbidden claim |
|---|---|---|---|---|---|---|
| prior | zero bit | conditional direct | REC-004 | telescoping | inverse for zero-prior records | inverse for arbitrary hidden prior |

### Assumptions and correct-place audit
- Assumptions: binary inputs, strict integral geometry, zero prior, identical check order.
- Simplifications and error bounds: exact on domain.
- Failure regime: nonbinary values, fractional geometry, or nonzero prior.
- Why this formula belongs here: downstream oracle paths may reconstruct raw histories from detector
  records.
- Schedule/instrument/record bridge: no explicit prior is carried; therefore general application is
  bridge-open even though valid-domain round trips pass.
- Alternative formulation/invariant: include \(s^{prior}\) explicitly.
- Verdict: bridge-open

### Independent checks
| invariant/reference | independent route | falsifier | shared blind spot? | result |
|---|---|---|---|---|
| two-sided inverse | hand-built GF(2) matrix/exhaustive enumeration | either composition not identity | no shared code | 4096/4096 states pass |
| prefix property | independent cumulative XOR | mismatch at any prefix | same algebra, different implementation | passes |

### Human verification
- [ ] formula transcription checked
- [ ] exact source page checked
- [ ] symbol/unit convention checked
- [ ] derivation replayed
- [ ] application location checked
- [ ] composite bridge accepted
- Human verdict: unchecked
- Notes:

## ECS-REC-006 — LSB-first packed raw-syndrome layout

### Formula and role
- Normalized formula:
  $$B=\left\lceil\frac{R\,n_{\mathrm{stab}}}{8}\right\rceil,\qquad
    b_{n,k}=\sum_{q=0}^{7}2^q\,s_{n,8k+q},\qquad
    \mathrm{stride}=B+1,$$
  where out-of-range padding bits are zero and byte \(b_{n,B}=o_n\in\{0,1\}\) stores the
  logical flip as a whole trailing byte.
- Literal code realization: `np.packbits(..., bitorder="little")` followed by concatenating
  `flips[:, None]`.
- Role: record-transform | serialization
- Scientific object: reversible byte representation of raw syndrome histories plus observable flips.
- Upstream inputs: binary raw syndromes in REC-002 order and one logical flip per shot.
- Downstream consumers: PEPS carrier directly; fused native carrier must mirror it; artifact bytes.

### Code usage
| frozen file:line | qualname | service/call path | runtime/oracle/test | responsibility |
|---|---|---|---|---|
| `carrier/records.py:87-100` | `pack_raw_syndrome_shots` | PEPS -> `PackedShotBatch` | runtime | Python packing |
| `carrier/records.py:192-238` | `PackedShotBatch.from_raw_syndromes` | public constructor | runtime | geometry/header + packing |
| `carrier/peps/trajectory.py:792-851` | `PepsSampler.sample` | peps_single_wire | runtime | principal Python producer |
| `carrier/within_cycle.py:960-1038` | native fused output bridge | fused_within_cycle | runtime | consumes native bytes under same declared layout; mirror audited Batch 6 |

### Symbols, domains, and conventions
| symbol | meaning | shape/domain | units | basis/order | source symbol |
|---|---|---|---|---|---|
| \(s_{n,i}\) | raw syndrome bit | \(\mathbb F_2\) | bit | shot, round-major flat index | none for byte layout |
| \(b_{n,k}\) | packed byte | integer 0..255 | byte | LSB-first within byte | none |
| \(o_n\) | logical-observable flip | \(\mathbb F_2\) stored as byte | bit/byte | trailing | none |

### Evidence verdict
- provenance_status: `NO-SOURCE`
- required visible risk marker: **高危无出处**
- formula_correctness: correct
- application_fit: mismatched
- value_provenance: project-design
- epistemic_class: custom project serialization that affects scientific coordinate identity

### Exact literature sources
| source ID | publication/version | PDF/hash | exact locator | visually checked page | source says | source does not say |
|---|---|---|---|---|---|---|
| none closing | project contract plus NumPy behavior only | n/a | `records.py` docstring/header | n/a | no primary paper was found for this exact byte protocol | detector literature does not specify LSB packing, padding, or a trailing whole observable byte |

### Source-to-code mapping
| source expression | code expression | transformation | exact/approximate | assumption | status |
|---|---|---|---|---|---|
| binary history + logical bit | round-major `packbits(little)` + trailing byte | custom serialization | exact on valid inputs | host/native and every reader share layout | source-open |

### Operation replay / derivation
| input | transformation | assumption | output | source locator or derivation step | status |
|---|---|---|---|---|---|
| eight bits \(s_{8k:8k+8}\) | weighted LSB sum | binary bits, zero padding | byte \(b_k\) | NumPy behavior + manual replay | passes valid domain |
| 256,257,-256,-255 inputs | `_binary_array` narrows before validation | original values binary | 0,1,0,1 and accepted bytes | reviewer falsifier | contract failed |

### Composite compatibility
| component | source | object/device/regime | composition bridge | compatible? | risk |
|---|---|---|---|---|---|
| round-major bits | REC-002 | Python/PEPS | LSB pack | yes on valid domain | public wrap bug |
| native fused bytes | native source audited Batch 6 | CUDA kernel | declared same stride/order | bridge-open | a mirrored convention is not yet independently checked |
| logical byte | terminal instrument audited carrier-by-carrier | qubit/qutrit readout | appended unchanged | bridge-open | source-specific observable meaning |

### Parameter/value provenance
| parameter | value/units | provenance kind | exact locator | transform | allowed claim | forbidden claim |
|---|---|---|---|---|---|---|
| bit order | little/LSB-first | project-design | `records.py:99`, header lines 224-227 | pack | frozen current layout | standard/literature layout |
| trailing observable | one whole byte | project-design | `records.py:100` | concatenate | current single-observable carrier | general multi-observable format |

### Assumptions and correct-place audit
- Assumptions: binary validated before cast, unused padding zero, one observable flip, and all native
  producers mirror the layout.
- Simplifications and error bounds: exact serialization on the valid domain.
- Failure regime: modulo-256 input aliases, multi-observable records, native/order drift, corrupt
  padding, and callers mistaking raw \(s\) for detector \(d\).
- Why this formula belongs here: a byte-order error permutes the scientific record.
- Schedule/instrument/record bridge: raw syndrome is deliberately stored; REC-008 owns conversion to
  detector product.
- Alternative formulation/invariant: self-describing schema with strict byte validation and
  host/native round-trip vectors.
- Verdict: mismatched

### Independent checks
| invariant/reference | independent route | falsifier | shared blind spot? | result |
|---|---|---|---|---|
| byte formula/stride | manual weighted-sum packer, no `np.packbits` | any byte mismatch | no | sweep \(R=1..4,n=1..9\) passes valid inputs |
| adversarial domain | wide signed integers | any nonbinary accepted | no | falsified |
| canonical test | expected byte `0x2D` | wrong normal-case order | shares project convention | passes but misses invalid domain/native mirror |

### Human verification
- [ ] formula transcription checked
- [ ] exact source page checked
- [ ] symbol/unit convention checked
- [ ] derivation replayed
- [ ] application location checked
- [ ] composite bridge accepted
- Human verdict: unchecked
- Notes:

## ECS-REC-007 — Packed-shot inverse and canonicality

### Formula and role
- Normalized formula:
  $$s_{n,i}=\left(b_{n,\lfloor i/8\rfloor}\gg(i\bmod8)\right)\mathbin{\&}1,
    \qquad o_n=b_{n,B},\qquad i<Rn_{\mathrm{stab}}.$$
- Literal code realization: `np.unpackbits(..., bitorder="little")[:, :bits]`; trailing byte
  returned as `flips`.
- Role: record-transform | deserialization
- Scientific object: decode custom raw-syndrome/observable bytes.
- Upstream inputs: declared packed-byte matrix and geometry.
- Downstream consumers: `to_raw_syndrome_obs`, then REC-008.

### Code usage
| frozen file:line | qualname | service/call path | runtime/oracle/test | responsibility |
|---|---|---|---|---|
| `carrier/records.py:103-133` | `unpack_raw_syndrome_shots` | packed carrier -> raw arrays | runtime | byte decode |
| `carrier/records.py:263-272` | `to_raw_syndrome_obs` | `PackedShotBatch` | runtime | geometry-bound accessor |

### Symbols, domains, and conventions
| symbol | meaning | shape/domain | units | basis/order | source symbol |
|---|---|---|---|---|---|
| \(b\) | byte payload | intended uint8 matrix | bytes | shot-major, LSB-first | none |
| padding | unused high bits in final syndrome byte | intended zero for pack output | bits | ignored by decoder | none |

### Evidence verdict
- provenance_status: `NO-SOURCE`
- required visible risk marker: **高危无出处**
- formula_correctness: correct
- application_fit: mismatched
- value_provenance: project-design
- epistemic_class: exact project inverse on pack outputs; permissive/noncanonical public decoder

### Exact literature sources
| source ID | publication/version | PDF/hash | exact locator | visually checked page | source says | source does not say |
|---|---|---|---|---|---|---|
| none closing | project serialization only | n/a | REC-006 | n/a | n/a | no paper defines this byte inverse/canonical padding policy |

### Source-to-code mapping
| source expression | code expression | transformation | exact/approximate | assumption | status |
|---|---|---|---|---|---|
| REC-006 project pack | `unpackbits(...little)[:,:bits]` | inverse bit extraction | exact for pack outputs | byte dtype, canonical padding, valid flip | code-derived; source-open |

### Operation replay / derivation
| input | transformation | assumption | output | source locator or derivation step | status |
|---|---|---|---|---|---|
| canonical pack output | extract bits/truncate padding | REC-006 domain | original \(s,o\) | manual sweep | passes |
| integer payload \([256,257]\) | cast to uint8 before semantic validation | values already bytes | syndrome 0, flip 1 accepted | live falsifier | failed domain |
| one-bit syndrome byte `0xFE` | ignore seven nonzero padding bits | padding need not be canonical | same raw bit as `0x00` | live falsifier | many-to-one accepted representation |

### Composite compatibility
| component | source | object/device/regime | composition bridge | compatible? | risk |
|---|---|---|---|---|---|
| Python pack | REC-006 | canonical output | inverse | yes on valid output | no load-time canonicality |
| persisted/native payload | later batches | external/corrupt/wide input | permissive cast | not closed | silent alias/canonicalization |

### Parameter/value provenance
| parameter | value/units | provenance kind | exact locator | transform | allowed claim | forbidden claim |
|---|---|---|---|---|---|---|
| padding truncation | ignore unused high bits | project-design | `records.py:130-132` | slice | decode pack output | unique/corruption-detecting artifact representation |

### Assumptions and correct-place audit
- Assumptions: input is the exact output of a trusted producer.
- Simplifications and error bounds: exact for that image; no integrity/canonicality check outside it.
- Failure regime: wide integer/floating payloads, nonzero padding, and corrupted persisted artifacts.
- Why this formula belongs here: deserialization decides the scored detector/observable record.
- Schedule/instrument/record bridge: geometry is header-derived; header integrity is not literature
  evidence.
- Alternative formulation/invariant: require uint8, verify trailing flip and zero padding before any
  cast, and re-pack equality-check on load.
- Verdict: mismatched

### Independent checks
| invariant/reference | independent route | falsifier | shared blind spot? | result |
|---|---|---|---|---|
| left/right inverse on valid domain | manual packer and sweep | mismatch | no | passes |
| canonical representation | inject nonzero padding | accepted alias | no | falsified |
| dtype/domain | wide integer payload | silent wrap | no | falsified |

### Human verification
- [ ] formula transcription checked
- [ ] exact source page checked
- [ ] symbol/unit convention checked
- [ ] derivation replayed
- [ ] application location checked
- [ ] composite bridge accepted
- Human verdict: unchecked
- Notes:

<!-- BATCH-1A-RECORD-ROWS-3 -->

## ECS-REC-008 — Raw packed record to canonical detector product

### Formula and role
- Normalized formula:
  $$\mathcal R(b;R,n_{\mathrm{stab}})
    =\left(F\!\left(U_s(b;R,n_{\mathrm{stab}})\right),\,U_o(b)\right),$$
  where \(U\) is REC-007 and \(F\) is REC-003/004.
- Literal code realization: `to_raw_syndrome_obs` -> `s_to_det(raw["syndrome"], rounds,
  n_stab)` -> `RecordBatch(det=..., obs=...)`.
- Role: instrument | record-transform | composition bridge
- Scientific object: package boundary converting carrier-internal raw syndrome bytes into the
  product \(\{det,obs\}\).
- Upstream inputs: packed fused/PEPS shots, header geometry/provenance.
- Downstream consumers: `to_det_obs`, metrics, certification, optional decoder/DEM.

### Code usage
| frozen file:line | qualname | service/call path | runtime/oracle/test | responsibility |
|---|---|---|---|---|
| `carrier/records.py:248-272` | `_header_geometry`, `to_raw_syndrome_obs` | packed record | runtime | decode geometry/raw payload |
| `carrier/records.py:274-311` | `to_record_batch`, `to_det_obs` | fused/PEPS -> product | runtime | fold and expose product |
| `carrier/within_cycle.py:1023-1038` | `execute_marshaled` return | fused_within_cycle -> bridge | runtime | native producer |
| `carrier/peps/trajectory.py:843-851` | `PepsSampler.sample` return | peps_single_wire -> bridge | runtime | Python producer |

### Symbols, domains, and conventions
| symbol | meaning | shape/domain | units | basis/order | source symbol |
|---|---|---|---|---|---|
| \(b\) | packed raw carrier payload | byte matrix | bytes | REC-006 | none |
| \(U_s,U_o\) | unpacked syndrome/observable | binary arrays intended | bits | REC-002 | adjacent |
| \(F\) | temporal detector fold | GF(2) map | bits | REC-003/004 | detector XOR |

### Evidence verdict
- provenance_status: `COMPOSITE-UNCLOSED`
- required visible risk marker: **高危无出处（组合公式整体无直接出处）**
- formula_correctness: incorrect
- application_fit: mismatched
- value_provenance: project-design
- epistemic_class: project composition of a direct detector identity and unsourced serialization

### Exact literature sources
| source ID | publication/version | PDF/hash | exact locator | visually checked page | source says | source does not say |
|---|---|---|---|---|---|---|
| SRC-BKY-DEM-v1 | arXiv:2504.14643v1 | local PDF/hash above | printed p.2-3, Sec. 1.2/Fig. 1 | yes | raw syndromes plus a-priori values map to detector histories by XOR | no packed bytes, trailing logical-flip byte, header/provenance merge, native/PEPS placement, or combined package object |

### Source-to-code mapping
| source expression | code expression | transformation | exact/approximate | assumption | status |
|---|---|---|---|---|---|
| consecutive syndrome XOR | `unpack -> s_to_det -> RecordBatch` | add custom serialization and object wrapper | exact only on valid domain | trusted bytes, zero prior, fixed order, correct observable | composite open |

### Operation replay / derivation
| input | transformation | assumption | output | source locator or derivation step | status |
|---|---|---|---|---|---|
| trusted REC-006 bytes | REC-007 then REC-003/004 | all component preconditions | detector product | component replay | passes |
| floating `shots=[[0.9,0.9]]` | `PackedShotBatch.__post_init__` casts directly to uint8 | packed input is a byte array | accepted all-zero \(\{det,obs\}\) | live adversarial replay | contradicted |
| valid record then mutation | writable arrays returned | frozen dataclass sufficient | product can become nonbinary | live replay | contradicted |

### Composite compatibility
| component | source | object/device/regime | composition bridge | compatible? | risk |
|---|---|---|---|---|---|
| serialization | REC-006/007, no source | Python/native payload | unpack | mismatched public domain | aliases/corruption |
| detector fold | SRC-BKY-DEM-v1 | initialized repeated checks | zero-prior fold | concrete fused path supported; generic API open | first-boundary risk |
| observable | carrier-specific later rows | terminal readout | pass through trailing byte | open | observable meaning/instrument differs by carrier |
| provenance firewall | project rule | learner/evaluator visibility | recursive key filter | partial | spelling/container bypass surface not exhaustively proved |

### Parameter/value provenance
| parameter | value/units | provenance kind | exact locator | transform | allowed claim | forbidden claim |
|---|---|---|---|---|---|---|
| `record_semantics` | `temporal_detector_events` | project label | `records.py:294-300` | metadata insertion | declared intent | proof that payload obeys it |

### Assumptions and correct-place audit
- Assumptions: trusted canonical bytes; consistent header; zero known prior; binary immutable output;
  observable byte is the correct terminal logical flip; no evaluator truth leaks.
- Simplifications and error bounds: serialization/fold are exact under assumptions; violations are
  discrete, not bounded small errors.
- Failure regime: public/manual/corrupt payloads, nonzero prior, header/order drift, and carrier
  instrument mismatch.
- Why this formula belongs here: it is the only active bridge preventing raw syndromes from being
  mislabeled as detector events.
- Schedule/instrument/record bridge: concrete fused codestate supports the boundary; full native and
  PEPS instrument equivalence remains for Batches 6 and 8.
- Alternative formulation/invariant: strict canonical-load validation, explicit prior/layout IDs,
  immutable arrays, and independent native/host golden vectors.
- Verdict: mismatched

### Independent checks
| invariant/reference | independent route | falsifier | shared blind spot? | result |
|---|---|---|---|---|
| valid normal path | manual pack + GF(2) matrix | record mismatch | no shared pack/fold code | passes swept valid cases |
| public payload domain | floating/wide/padding adversarial inputs | any silently accepted alias | no | falsified |
| canonical acceptance | normal byte vectors | invalid/corrupt artifacts | yes | passes normal path only |

### Human verification
- [ ] formula transcription checked
- [ ] exact source page checked
- [ ] symbol/unit convention checked
- [ ] derivation replayed
- [ ] application location checked
- [ ] composite bridge accepted
- Human verdict: unchecked
- Notes:

## ECS-REC-009 — Raw-syndrome prefix byte projection

### Formula and role
- Normalized formula:
  $$P_r(b)=\operatorname{Pack}_{\mathrm{LSB}}
    \left(U_s(b)[:,\,0:r\,n_{\mathrm{stab}}]\right),\qquad0\le r\le R,$$
  returned shot-major with no trailing observable byte.
- Literal code realization: byte-aligned raw slice or unpack/truncate/repack for mid-byte prefixes.
- Role: record-transform | compatibility/streaming support
- Scientific object: raw-syndrome, not detector, prefix serialization.
- Upstream inputs: materialized `PackedShotBatch`, prefix round count.
- Downstream consumers: no installed runtime consumer found; legacy/noncanonical tests only.

### Code usage
| frozen file:line | qualname | service/call path | runtime/oracle/test | responsibility |
|---|---|---|---|---|
| `carrier/records.py:316-331` | `PackedShotBatch.syndrome_prefix_bytes` | public compatibility API | runtime support | raw prefix extraction |
| `tests/test_shotset_records.py`, `tests/test_shotset_units.py` | hand-prefix tests | noncanonical verification | test | pins project byte convention |

### Symbols, domains, and conventions
| symbol | meaning | shape/domain | units | basis/order | source symbol |
|---|---|---|---|---|---|
| \(r\) | number of raw rounds retained | integer \(0..R\) | rounds | prefix | none |
| \(P_r\) | concatenated per-shot prefix bytes | bytes | byte string | shot-major, LSB | none |

### Evidence verdict
- provenance_status: `NO-SOURCE`
- required visible risk marker: **高危无出处**
- formula_correctness: correct
- application_fit: bridge-open
- value_provenance: project-design
- epistemic_class: unused current compatibility serialization, not a validated detector-prefix instrument

### Exact literature sources
| source ID | publication/version | PDF/hash | exact locator | visually checked page | source says | source does not say |
|---|---|---|---|---|---|---|
| none closing | no exact primary source found | n/a | search and call-site scan | n/a | n/a | no source defines this byte projection or licenses it as a detector-history prefix |

### Source-to-code mapping
| source expression | code expression | transformation | exact/approximate | assumption | status |
|---|---|---|---|---|---|
| none | raw unpack/slice/repack | custom project projection | exact on valid payload | caller explicitly wants raw \(s\), not \(d\) | open |

### Operation replay / derivation
| input | transformation | assumption | output | source locator or derivation step | status |
|---|---|---|---|---|---|
| byte-aligned prefix | take complete syndrome bytes per shot | no partial byte | prefix bytes | code lines 327-328 | passes |
| nonaligned prefix | unpack raw, slice \(rn\) bits, re-pack LSB | canonical desired | prefix bytes | code lines 329-331 | passes |

### Composite compatibility
| component | source | object/device/regime | composition bridge | compatible? | risk |
|---|---|---|---|---|---|
| raw prefix | REC-006/007 | carrier internal \(s\) | byte projection | yes valid-domain | can be mistaken for detector prefix |
| temporal causality | detector source | product \(d\) | no fold applied | not applicable unless explicitly raw | naming/consumer risk |

### Parameter/value provenance
| parameter | value/units | provenance kind | exact locator | transform | allowed claim | forbidden claim |
|---|---|---|---|---|---|---|
| prefix layout | raw round-major, no obs | project-design | code lines 316-331 | slice/repack | byte compatibility | causal detector-record or scientific prefix likelihood |

### Assumptions and correct-place audit
- Assumptions: trusted payload and an explicitly raw-syndrome consumer.
- Simplifications and error bounds: exact byte projection; omits detector fold and observable.
- Failure regime: use as a product-record prefix, corrupt payload, or inferred causality claims.
- Why this formula belongs here: public compatibility semantics can otherwise be mistaken for the
  scientific record.
- Schedule/instrument/record bridge: no current installed runtime consumer; therefore application is
  not established.
- Alternative formulation/invariant: name the output `raw_syndrome_prefix_bytes` in every artifact
  and expose detector prefixes as a separately validated object.
- Verdict: bridge-open

### Independent checks
| invariant/reference | independent route | falsifier | shared blind spot? | result |
|---|---|---|---|---|
| prefix bytes | manual per-shot LSB packer across aligned/nonaligned widths | any mismatch | no | \(R=1..4,n=1..9,r=0..R\) passes |
| current-use scan | repository call-site search | installed runtime consumer | no | tests only; no current runtime scientific use |

### Human verification
- [ ] formula transcription checked
- [ ] exact source page checked
- [ ] symbol/unit convention checked
- [ ] derivation replayed
- [ ] application location checked
- [ ] composite bridge accepted
- Human verdict: unchecked
- Notes:

<!-- BATCH-1A-ROWS-END -->

## ECS-CPTP-NUM-001 — Complex128/float64 precision policy

### Formula and role
- Normalized formula: $$\rho,K,H,U,J,R\in\mathbb C_{128},\qquad
  x_{\mathrm{generator}}\in\mathbb R_{64}.$$
- Literal code realization: `CDTYPE = torch.complex128`; `RDTYPE = torch.float64`.
- Role: numerical convention | claimed-accuracy premise
- Scientific object: arithmetic precision used by the differentiable small-scale channel algebra.
- Upstream inputs: caller tensors and Stinespring parameters.
- Downstream consumers: Kraus action, Choi/PTM/TP diagnostics, exact density-matrix carriers, and
  Stinespring tests.

### Code usage
| frozen file:line | qualname | service/call path | runtime/oracle/test | responsibility |
|---|---|---|---|---|
| `src/error_coupling_simulator/carrier/cptp_channel.py:30-43` | module precision policy | channel_algebra -> exact/Axis-1 callers | runtime | selects double real/complex arithmetic and supports the prose claim “high-precision”; not exact arithmetic |

### Symbols, domains, and conventions
| symbol | meaning | shape/domain | units | basis/order | source symbol |
|---|---|---|---|---|---|
| \(\mathbb C_{128},\mathbb R_{64}\) | IEEE binary64 component precision | finite machine numbers plus nonfinite values | inherited | all matrix conventions below | none |

### Evidence verdict
- provenance_status: `NO-SOURCE`
- required visible risk marker: **高危无出处**
- formula_correctness: unresolved
- application_fit: bridge-open
- value_provenance: project-design
- epistemic_class: project precision policy; not a proof of exactness or a global forward-error bound

### Exact literature sources
| source ID | publication/version | PDF/hash | exact locator | visually checked page | source says | source does not say |
|---|---|---|---|---|---|---|
| none closing | search `S-B1B1-CPTP-001` | n/a | local code/paper search | n/a | channel sources state exact algebraic identities | no source proves complex128 makes all implemented paths “exact” or gives a global error budget |

### Source-to-code mapping
| source expression | code expression | transformation | exact/approximate | assumption | status |
|---|---|---|---|---|---|
| exact channel algebra | complex128/float64 evaluation | finite-precision implementation | approximate | conditioning and accumulated roundoff remain below claim thresholds | open |

### Operation replay / derivation
| input | transformation | assumption | output | source locator or derivation step | status |
|---|---|---|---|---|---|
| binary64 real/imaginary components | Torch complex128 operations | delegated kernels preserve dtype | rounded channel objects | code lines 42-43 | code behavior exact; accuracy claim unbounded |

### Composite compatibility
| component | source | object/device/regime | composition bridge | compatible? | risk |
|---|---|---|---|---|---|
| analytic CPTP identities | SRC-HANTZKO-PTM-v2 | exact finite-dimensional maps | machine matrix exponential/einsum/norm | only to roundoff | “CPTP by construction” can drift numerically |

### Parameter/value provenance
| parameter | value/units | provenance kind | exact locator | transform | allowed claim | forbidden claim |
|---|---|---|---|---|---|---|
| real/complex dtype | float64/complex128 | project-design | `cptp_channel.py:42-43` | none | frozen precision choice | exact arithmetic, universal error \(<10^{-12}\), or hardware fidelity |

### Assumptions and correct-place audit
- Assumptions: small matrices, finite well-conditioned inputs, and stable Torch complex128 kernels.
- Simplifications and error bounds: no per-operation or end-to-end rounding analysis was found.
- Failure regime: ill-conditioned exponentials, near-zero eigenvalues, long compositions, nonfinite input,
  or gates judged at the shared \(10^{-12}\) boundary.
- Why this formula belongs here: dtype is invoked as a scientific-fidelity premise and controls diagnostic residuals.
- Schedule/instrument/record bridge: consumer-specific and still open.
- Alternative formulation/invariant: convergence across precisions plus condition-aware residual/error bounds.
- Verdict: bridge-open

### Independent checks
| invariant/reference | independent route | falsifier | shared blind spot? | result |
|---|---|---|---|---|
| precision claim | compare c64/c128 and, where possible, higher-precision independent arithmetic | claim-bearing result shifts materially | no run in this batch | untested; source remains open |

### Human verification
- [ ] formula transcription checked
- [ ] exact source page checked
- [ ] symbol/unit convention checked
- [ ] derivation replayed
- [ ] application location checked
- [ ] composite bridge accepted
- Human verdict: unchecked
- Notes: “intentionally exact” in the module prose is accepted only as design intent, not an audit verdict.

## ECS-CPTP-001 — Hermitian projection after channel operations

### Formula and role
- Normalized formula: $$\Pi_H(A)=\frac12(A+A^\dagger).$$
- Literal code realization: `0.5 * (rho + rho.conj().transpose(-1, -2))`.
- Role: numerical postprocess | channel/instrument support
- Scientific object: projection of a matrix onto the Hermitian subspace after channel or unitary action.
- Upstream inputs: nominal density matrices or nominal Hermitian channel outputs.
- Downstream consumers: `apply_kraus`, exact qubit/qutrit state evolution, and fused CUDA mirrors.

### Code usage
| frozen file:line | qualname | service/call path | runtime/oracle/test | responsibility |
|---|---|---|---|---|
| `carrier/cptp_channel.py:49-50,66` | `hermitianize`; `apply_kraus` | channel_algebra -> exact carriers | runtime | discards the anti-Hermitian component |
| `carrier/accel.py:190,212`; `carrier/exact/qutrit_dm.py:383,486,565` | fused/exact mirrors | native/exact carrier paths | runtime | reuse the same convention |
| `tests/test_qutrit_dm_memlean.py:81-96` | blocked mirror test | exact_qutrit_dm | test-reference | checks implementation equality, not physical applicability |

### Symbols, domains, and conventions
| symbol | meaning | shape/domain | units | basis/order | source symbol |
|---|---|---|---|---|---|
| \(A\) | candidate state/operator | \((...,d,d)\), complex | inherited | computational matrix order | none |
| \(\Pi_H\) | Frobenius-orthogonal Hermitian projection | same shape | inherited | adjoint on last two axes | none |

### Evidence verdict
- provenance_status: `NO-SOURCE`
- required visible risk marker: **高危无出处**
- formula_correctness: correct
- application_fit: bridge-open
- value_provenance: complete
- epistemic_class: elementary linear-algebra projection; source and roundoff-only application premise remain open

### Exact literature sources
| source ID | publication/version | PDF/hash | exact locator | visually checked page | source says | source does not say |
|---|---|---|---|---|---|---|
| none closing | search `S-B1B1-CPTP-001` | n/a | local formula search | n/a | no exact selected artifact | no source authorizes applying the projection to arbitrary operator inputs while calling the result the exact channel action |

### Source-to-code mapping
| source expression | code expression | transformation | exact/approximate | assumption | status |
|---|---|---|---|---|---|
| intended Hermitian output \(A=A^\dagger\) | \((A+A^\dagger)/2\) | remove anti-Hermitian residual | exact projection | residual is numerical error, not signal | open application bridge |

### Operation replay / derivation
| input | transformation | assumption | output | source locator or derivation step | status |
|---|---|---|---|---|---|
| \(A=H+S\), \(H^\dagger=H,S^\dagger=-S\) | average with adjoint | complex matrix | \(H\) | direct algebra | correct |
| \(E_{01}\) under identity Kraus | apply identity, then project | caller may use general operator | \((E_{01}+E_{10})/2\) | independent reviewer hand calculation | falsifies general linear-map interpretation |

### Composite compatibility
| component | source | object/device/regime | composition bridge | compatible? | risk |
|---|---|---|---|---|---|
| Kraus map | SRC-HANTZKO-PTM-v2 Eq.12 | linear map on all operators | unconditional projection | yes only for Hermitian inputs or pure roundoff | breaks complex linearity outside the state/Hermitian basis domain |

### Parameter/value provenance
| parameter | value/units | provenance kind | exact locator | transform | allowed claim | forbidden claim |
|---|---|---|---|---|---|---|
| coefficient \(1/2\) | dimensionless | algebraically fixed | code line 50 | Hermitian/anti-Hermitian decomposition | exact projection | empirically calibrated error correction |

### Assumptions and correct-place audit
- Assumptions: input should be Hermitian and any anti-Hermitian component is only roundoff.
- Simplifications and error bounds: the discarded norm is not reported or bounded.
- Failure regime: non-Hermitian operator bases, superoperator reconstruction, gradients whose true adjoint is not
  Hermitian, or upstream bugs producing a material anti-Hermitian part.
- Why this formula belongs here: it changes runtime state/operator values and defines the fused-kernel mirror.
- Schedule/instrument/record bridge: matched for density-state paths; open for every general-operator reuse.
- Alternative formulation/invariant: assert/report \(\|A-A^\dagger\|\) before projection; do not project general basis operators.
- Verdict: bridge-open

### Independent checks
| invariant/reference | independent route | falsifier | shared blind spot? | result |
|---|---|---|---|---|
| state-domain identity | hand calculation for Hermitian \(A\) | projection changes \(A\) | no | unchanged exactly |
| general-domain linearity | identity channel on \(E_{01}\) | maximum entry difference nonzero | no | difference \(0.5\); general linear-map claim rejected |

### Human verification
- [ ] formula transcription checked
- [ ] exact source page checked
- [ ] symbol/unit convention checked
- [ ] derivation replayed
- [ ] application location checked
- [ ] composite bridge accepted
- Human verdict: unchecked
- Notes:

## ECS-CPTP-002 — Kraus action on Hermitian inputs

### Formula and role
- Normalized formula: $$\Phi(\rho)=\sum_{e=1}^{r}K_e\rho K_e^\dagger.$$
- Literal code realization: two `einsum` paths followed by ECS-CPTP-001.
- Role: channel | carrier primitive
- Scientific object: completely positive map applied to one density matrix or a shot/batch of density matrices.
- Upstream inputs: \(\rho\in\mathbb C^{d\times d}\) or \(\mathbb C^{S\times d\times d}\);
  \(K\in\mathbb C^{r\times d\times d}\).
- Downstream consumers: exact qubit/qutrit carriers, Axis-1 comparisons, PTM construction, and native mirrors.

### Code usage
| frozen file:line | qualname | service/call path | runtime/oracle/test | responsibility |
|---|---|---|---|---|
| `carrier/cptp_channel.py:53-66` | `apply_kraus` | channel_algebra -> exact carriers/PTM | runtime | implements unbatched/batched operator-sum action and projects Hermitian |
| `carrier/exact/circuit_sim.py:87-96` | `apply_local_channel` | exact_qubit_circuit_dm | runtime | embeds local \(K_e\), then calls this action |
| `tests/test_joint_lindbladian.py:276-283,384-390` | independent density-state comparisons | Axis-1 joint channel | test-reference | compares valid Hermitian-state actions with QuTiP/SciPy routes |

### Symbols, domains, and conventions
| symbol | meaning | shape/domain | units | basis/order | source symbol |
|---|---|---|---|---|---|
| \(K_e\) | Kraus operator | \(d\times d\), complex | dimensionless map amplitude | output row, input column | \(K_i\) |
| \(\rho\) | Hermitian input state/operator | \(d\times d\) or batch | trace one for states | computational | \(\rho\) |
| \(e\) | Kraus/environment index | \(0,\ldots,r-1\) | none | leading axis | \(i\) |

### Evidence verdict
- provenance_status: `DIRECT`
- required visible risk marker: none
- formula_correctness: correct
- application_fit: matched
- value_provenance: complete
- epistemic_class: standard Kraus action, conditional here on Hermitian input because of the appended projection

### Exact literature sources
| source ID | publication/version | PDF/hash | exact locator | visually checked page | source says | source does not say |
|---|---|---|---|---|---|---|
| SRC-HANTZKO-PTM-v2 | Hantzko, Binkowski & Gupta, arXiv:2411.00526v2; Phys. Scr. 100, 075125 (2025) | `outputs/papers/2411.00526.pdf`; `dd0421cc45fcb0e95caf803ee568720aefec6319c9015f18f5c8e6f1ef812d0a` | PDF index 2 / printed p.3, Eq.12 | yes | \(\mathcal E(\rho)=\sum_iK_i\rho K_i^\dagger\) and TP completeness | no unconditional Hermitian projection or project dtype/error bound |

### Source-to-code mapping
| source expression | code expression | transformation | exact/approximate | assumption | status |
|---|---|---|---|---|---|
| \(\sum_eK_e\rho K_e^\dagger\) | `einsum("eij,jk,ekl->il", K,rho,K†)` | index contraction; optional batch \(s\) | exact before roundoff | matching square dimensions/basis | direct |
| source output | ECS-CPTP-001 | numerical projection | identity on exact Hermitian inputs | \(\rho=\rho^\dagger\), map Hermiticity-preserving | conditional |

### Operation replay / derivation
| input | transformation | assumption | output | source locator or derivation step | status |
|---|---|---|---|---|---|
| \(K_{eij},\rho_{jk},K^\dagger_{ekl}\) | sum over \(e,j,k\) | \(K^\dagger_{kl}=K^*_{lk}\) encoded by transpose | \(\Phi(\rho)_{il}\) | Eq.12 -> einsum | exact mapping |
| batch index \(s\) | leave \(s\) uncontracted | common Kraus stack | \(\Phi(\rho_s)\) | code line 65 | exact extension |

### Composite compatibility
| component | source | object/device/regime | composition bridge | compatible? | risk |
|---|---|---|---|---|---|
| operator-sum action | SRC-HANTZKO-PTM-v2 | arbitrary operators | project result Hermitian | yes for states/Paulis; no for arbitrary non-Hermitian bases | public docstring overstates generality |

### Parameter/value provenance
| parameter | value/units | provenance kind | exact locator | transform | allowed claim | forbidden claim |
|---|---|---|---|---|---|---|
| none | n/a | complete structural formula | source Eq.12 | einsum only | channel action on declared Hermitian domain | general complex-linear superoperator action after projection |

### Assumptions and correct-place audit
- Assumptions: matching devices/dimensions, finite values, Hermitian input, and valid caller-supplied Kraus stack.
- Simplifications and error bounds: no validation of CP/TP, dimensions, PSD, or trace; projection hides anti-Hermitian residual.
- Failure regime: non-Hermitian canonical bases, malformed Kraus stacks, or a material anti-Hermitian upstream error.
- Why this formula belongs here: it is the common local-channel action used by multiple carriers.
- Schedule/instrument/record bridge: schedule placement is owned by downstream batches.
- Alternative formulation/invariant: expose a raw complex-linear operator action and separately validate/project state paths.
- Verdict: matched on the actual Hermitian-state/Pauli call domain

### Independent checks
| invariant/reference | independent route | falsifier | shared blind spot? | result |
|---|---|---|---|---|
| density-state action | QuTiP/SciPy comparisons in `test_joint_lindbladian.py` | action mismatch | third-party conventions still shared at matrix level | matched on valid Hermitian states |
| general operator | hand identity-channel \(E_{01}\) case | raw output changed | no | appended projection changes it; scope restriction required |

### Human verification
- [ ] formula transcription checked
- [ ] exact source page checked
- [ ] symbol/unit convention checked
- [ ] derivation replayed
- [ ] application location checked
- [ ] composite bridge accepted
- Human verdict: unchecked
- Notes: source closure applies to the operator-sum core, not to ECS-CPTP-001.

## ECS-CPTP-003 — Floored computational-basis measurement distribution

### Formula and role
- Normalized formula:
  $$q_i=\max(\epsilon_{\mathrm{num}},\operatorname{Re}\rho_{ii}),\qquad
    p_i=\frac{q_i}{\sum_jq_j},\qquad\epsilon_{\mathrm{num}}=10^{-12}.$$
- Literal code realization: real diagonal -> `torch.clamp(..., min=NUMERICAL_ZERO)` -> row normalization.
- Role: instrument | sampling distribution | physical-parameter transform
- Scientific object: probabilities used for computational/Z-basis sampling.
- Upstream inputs: nominal density matrix, possibly batched.
- Downstream consumers: exact qubit measurement/reset sampling and Axis-1 state evidence.

### Code usage
| frozen file:line | qualname | service/call path | runtime/oracle/test | responsibility |
|---|---|---|---|---|
| `carrier/cptp_channel.py:69-72` | `measurement_probabilities_z` | channel_algebra -> exact_qubit/Axis-1 | runtime | replaces every population below \(10^{-12}\), then renormalizes |
| `carrier/exact/circuit_sim.py:116,124` | measurement/reset helpers | exact_qubit_circuit_dm | runtime | samples the returned distribution |
| `frontend/axis1_state_evidence.py:339` | state evidence serialization | Axis-1 evidence | runtime/evidence | exports the altered probabilities |
| `tests/test_diff_circuit_forward.py:27-42` | analytic nonzero-probability check | exact_qubit | test-reference | does not test structural zeros/nonfinite values |

### Symbols, domains, and conventions
| symbol | meaning | shape/domain | units | basis/order | source symbol |
|---|---|---|---|---|---|
| \(\rho_{ii}\) | computational-basis population | valid state: real, nonnegative, sums to one | probability | diagonal \(i\) | \(|\langle i|\Psi\rangle|^2\) for pure states |
| \(q_i\) | floored weight | intended positive finite real | dimensionless | same order | none |
| \(p_i\) | code sampling probability | intended simplex; may contain NaN | probability | same order | measurement outcome probability |

### Evidence verdict
- provenance_status: `COMPOSITE-UNCLOSED`
- required visible risk marker: **高危无出处（组合公式整体无直接出处）**
- formula_correctness: incorrect
- application_fit: mismatched
- value_provenance: incomplete
- epistemic_class: Born-rule component plus unsourced, model-changing project smoothing

### Exact literature sources
| source ID | publication/version | PDF/hash | exact locator | visually checked page | source says | source does not say |
|---|---|---|---|---|---|---|
| SRC-SKINNER-BORN-v4 | Skinner, Ruhman & Nahum, *Measurement-Induced Phase Transitions in the Dynamics of Entanglement*, arXiv:1808.05953v4 (2019) | `docs/papers/skinner_ruhman_nahum_measurement_induced_transitions_1808.05953.pdf`; `83c71cb8498aacc6fa05795f30738d371d4916886558d4cdb469027154a0ffad` | PDF index 2 / printed p.3, Sec.II | yes | projective outcomes occur with \(|\langle\uparrow|\Psi\rangle|^2,|\langle\downarrow|\Psi\rangle|^2\), followed by projection/renormalization | no per-outcome floor, invalid-state repair, or \(10^{-12}\) physical mass |

### Source-to-code mapping
| source expression | code expression | transformation | exact/approximate | assumption | status |
|---|---|---|---|---|---|
| \(p_i=|\langle i|\Psi\rangle|^2\) | \(\operatorname{Re}\rho_{ii}\) | extend to mixed state by linear mixture | exact [ours-derived] for valid density matrices | computational projectors | closed component |
| \(\rho_{ii}\) | \(\max(10^{-12},\rho_{ii})/\sum q\) | smoothing plus renormalization | model-changing | structural zeros may be replaced | open/mismatched |

### Operation replay / derivation
| input | transformation | assumption | output | source locator or derivation step | status |
|---|---|---|---|---|---|
| \(\rho=|0\rangle\langle0|\) | floor \((1,0)\), normalize | floor is harmless | \((1,10^{-12})/(1+10^{-12})\) | live/code replay | contradicts exact zero |
| zero-trace or all-negative diagonal | clamp all entries | invalid inputs should be repaired | uniform distribution | reviewer edge table | invalid state becomes plausible output |
| NaN or \(+\infty\) population | clamp/divide | finite input not checked | NaN row | reviewer edge table | fail-open/nonfinite |

### Composite compatibility
| component | source | object/device/regime | composition bridge | compatible? | risk |
|---|---|---|---|---|---|
| computational projective probability | SRC-SKINNER-BORN-v4 | normalized quantum state | per-coordinate floor before normalization | no | creates forbidden events and changes rare tails |
| shared epsilon | ECS-NUM-001 | heterogeneous numerical convention | inserted as physical mass | no source/error budget | accumulates through sampling and evidence |

### Parameter/value provenance
| parameter | value/units | provenance kind | exact locator | transform | allowed claim | forbidden claim |
|---|---|---|---|---|---|---|
| \(\epsilon_{\rm num}\) | \(10^{-12}\), probability | project-design/incomplete | `numerics.py:3`; `cptp_channel.py:71` | coordinate floor | exact current code behavior | Born-rule probability, physical dark-count model, or bounded-negligible perturbation |

### Assumptions and correct-place audit
- Assumptions: inputs are finite PSD trace-one states and adding \(10^{-12}\) to every zero outcome cannot
  change a scientific conclusion.
- Simplifications and error bounds: no TV/record-law/rare-event bound across repeated measurements.
- Failure regime: ideal controls, deterministic outcomes, probabilities below \(10^{-12}\), invalid states,
  large outcome spaces, and repeated sampling.
- Why this formula belongs here: it directly selects measurement branches and exported probabilities.
- Schedule/instrument/record bridge: the altered branch law propagates into records; downstream quantification pending.
- Alternative formulation/invariant: validate finite PSD/positive trace, preserve structural zeros, normalize the
  Born diagonal, and use a sampling-only tolerance that does not rewrite probabilities.
- Verdict: mismatched

### Independent checks
| invariant/reference | independent route | falsifier | shared blind spot? | result |
|---|---|---|---|---|
| deterministic Born outcome | hand state \(|0\rangle\) | \(p_1\ne0\) | no | falsified: \(p_1>0\) |
| invalid-input fail-closed | zero/negative/NaN/inf diagonals | finite plausible output or NaN propagation | no | uniform repair or NaN observed |
| current tests | nonzero analytic case | exact-zero boundary | yes | ordinary case passes; core falsifier absent |

### Human verification
- [ ] formula transcription checked
- [ ] exact source page checked
- [ ] symbol/unit convention checked
- [ ] derivation replayed
- [ ] application location checked
- [ ] composite bridge accepted
- Human verdict: unchecked
- Notes: this row does not claim the invalid inputs are physical; their acceptance shows the boundary does not
  enforce the formula's stated domain.

## ECS-CPTP-004 — Frobenius trace-preservation residual

### Formula and role
- Normalized formula: $$\delta_{\mathrm{TP}}(K)=
  \left\|\sum_eK_e^\dagger K_e-I_d\right\|_F.$$
- Literal code realization: einsum completeness minus complex128 identity, then `torch.linalg.matrix_norm`.
- Role: diagnostic | invariant
- Scientific object: scalar zero-set diagnostic for trace preservation of a Kraus stack.
- Upstream inputs: square Kraus operators.
- Downstream consumers: channel acceptance helpers and formal/test gates; each numerical threshold is audited separately.

### Code usage
| frozen file:line | qualname | service/call path | runtime/oracle/test | responsibility |
|---|---|---|---|---|
| `carrier/cptp_channel.py:75-80` | `tp_residual` | channel_algebra -> tests/diagnostics | runtime diagnostic | computes the Frobenius residual |
| `tests/test_noise_mechanism_primitives.py:36-50` | `_assert_tp` | canonical channel_algebra acceptance | gate | compares this residual with a hand-set tolerance |
| `tests/test_window_channel.py:169-219` | TP positive/negative controls | legacy gate | test-reference | includes a non-TP control; threshold is a separate formula |

### Symbols, domains, and conventions
| symbol | meaning | shape/domain | units | basis/order | source symbol |
|---|---|---|---|---|---|
| \(K_e\) | Kraus operator | \(d\times d\) | dimensionless | computational | \(K_i\) |
| \(\delta_{\rm TP}\) | completeness residual | nonnegative real | dimensionless | Frobenius norm | none |

### Evidence verdict
- provenance_status: `DERIVED`
- required visible risk marker: none
- formula_correctness: correct
- application_fit: matched
- value_provenance: complete
- epistemic_class: [ours-derived] zero-set diagnostic; not a complete CPTP certificate by itself

### Exact literature sources
| source ID | publication/version | PDF/hash | exact locator | visually checked page | source says | source does not say |
|---|---|---|---|---|---|---|
| SRC-HANTZKO-PTM-v2 | Hantzko et al., arXiv:2411.00526v2 | `outputs/papers/2411.00526.pdf`; `dd0421cc45fcb0e95caf803ee568720aefec6319c9015f18f5c8e6f1ef812d0a` | PDF index 2 / printed p.3, Eq.12 | yes | TP Kraus operators satisfy \(\sum_iK_i^\dagger K_i=I\) | no Frobenius threshold or CP conclusion from this residual alone |

### Source-to-code mapping
| source expression | code expression | transformation | exact/approximate | assumption | status |
|---|---|---|---|---|---|
| \(\sum K^\dagger K=I\) | norm of left-minus-right | take Frobenius norm | exact zero-set in exact arithmetic | finite square matrices | derived |

### Operation replay / derivation
| input | transformation | assumption | output | source locator or derivation step | status |
|---|---|---|---|---|---|
| completeness defect \(A\) | \(\|A\|_F\) | norm is zero iff \(A=0\) | scalar zero iff TP equality holds | Eq.12 + norm axiom | closed [ours-derived] |

### Composite compatibility
| component | source | object/device/regime | composition bridge | compatible? | risk |
|---|---|---|---|---|---|
| TP equality | SRC-HANTZKO-PTM-v2 | Kraus map | finite-precision Frobenius residual | yes as diagnostic | does not check CP for arbitrary non-Kraus representations |

### Parameter/value provenance
| parameter | value/units | provenance kind | exact locator | transform | allowed claim | forbidden claim |
|---|---|---|---|---|---|---|
| diagnostic threshold | none in this function | n/a | caller-owned | n/a | report residual | pass/fail or error bound without the caller's threshold row |

### Assumptions and correct-place audit
- Assumptions: square finite Kraus stack with common \(d\), correct conjugation, and complex128 identity.
- Simplifications and error bounds: finite residual is not converted to a channel-distance bound.
- Failure regime: malformed dimensions/nonfinite input or treating a small residual as proof of all CPTP properties.
- Why this formula belongs here: it is a claim-bearing invariant used by gates.
- Schedule/instrument/record bridge: none; it validates local algebra only.
- Alternative formulation/invariant: report spectral/max norms and Choi positivity separately where required.
- Verdict: matched

### Independent checks
| invariant/reference | independent route | falsifier | shared blind spot? | result |
|---|---|---|---|---|
| valid Stinespring stack | direct \(V^\dagger V\) calculation | residual material | no | \(2.25\times10^{-16}\) in reviewer replay |
| broken map | hand \(K=2I\) | residual remains zero | no | nonzero as required; legacy negative control exists |

### Human verification
- [ ] formula transcription checked
- [ ] exact source page checked
- [ ] symbol/unit convention checked
- [ ] derivation replayed
- [ ] application location checked
- [ ] composite bridge accepted
- Human verdict: unchecked
- Notes:

## ECS-CPTP-005 — C-order Kraus Choi matrix with fixed SWAP convention

### Formula and role
- Normalized formula:
  $$J_{\mathrm{code}}(\Phi)=\sum_e|\operatorname{vec}_C(K_e)\rangle
  \langle\operatorname{vec}_C(K_e)|
  =S\,J_{\mathrm{in}\otimes\mathrm{out}}(\Phi)\,S^\dagger,$$
  where \(\operatorname{vec}_C(K)_{ad+b}=K_{ab}\) and \(S|a\rangle|b\rangle=|b\rangle|a\rangle\).
- Literal code realization: C-order `reshape(r, d*d)` followed by an outer-product sum.
- Role: channel representation | diagnostic substrate
- Scientific object: unnormalized Choi matrix in output⊗input order.
- Upstream inputs: Kraus stack.
- Downstream consumers: internal equality/PSD/Frobenius diagnostics and legacy channel gates.

### Code usage
| frozen file:line | qualname | service/call path | runtime/oracle/test | responsibility |
|---|---|---|---|---|
| `carrier/cptp_channel.py:83-91` | `choi_matrix` | channel_algebra -> diagnostics/tests | runtime diagnostic | constructs \(J_{\rm code}\) |
| `tests/test_noise_mechanism_primitives.py:109-114` | Choi equality check | canonical channel_algebra | test-reference | compares two outputs using the same convention |
| `tests/test_window_channel.py:195-219,350-358` | PSD/distance checks | legacy gate | test-reference | acknowledges PSD is tautological for a Kraus outer-product construction |

### Symbols, domains, and conventions
| symbol | meaning | shape/domain | units | basis/order | source symbol |
|---|---|---|---|---|---|
| \(J_{\rm code}\) | code Choi matrix | \(d^2\times d^2\), PSD | dimensionless | output⊗input, C-row vectorization | \(\mathrm{Choi}(\mathcal E)\) after SWAP |
| \(S\) | tensor-factor swap | unitary permutation | none | input↔output | none |

### Evidence verdict
- provenance_status: `DERIVED`
- required visible risk marker: none
- formula_correctness: correct
- application_fit: bridge-open
- value_provenance: complete
- epistemic_class: [ours-derived] convention transform of a direct Choi definition

### Exact literature sources
| source ID | publication/version | PDF/hash | exact locator | visually checked page | source says | source does not say |
|---|---|---|---|---|---|---|
| SRC-HANTZKO-PTM-v2 | Hantzko et al., arXiv:2411.00526v2 | `outputs/papers/2411.00526.pdf`; `dd0421cc45fcb0e95caf803ee568720aefec6319c9015f18f5c8e6f1ef812d0a` | PDF index 2 / printed p.3, Eqs.9,12 and footnote 3 | yes | input⊗output Choi definition, CP iff positive, Kraus form; unit-trace normalization gives a Choi state | no code C-order reshape or implicit SWAP |

### Source-to-code mapping
| source expression | code expression | transformation | exact/approximate | assumption | status |
|---|---|---|---|---|---|
| \(\sum_{kl}E_{kl}\otimes\Phi(E_{kl})\) | \(\sum_e\operatorname{vec}_C(K_e)\operatorname{vec}_C(K_e)^\dagger\) | Kraus substitution plus factor SWAP | exact | same input/output dimension and C indexing | derived |

### Operation replay / derivation
| input | transformation | assumption | output | source locator or derivation step | status |
|---|---|---|---|---|---|
| Eq.9 element \(K_{ak}K^*_{bl}\) indexed \((k,a),(l,b)\) | C-vec indexes \((a,k),(b,l)\) | apply \(S\) to both axes | \(SJS^\dagger\) | direct index replay | closed |
| TP stack | trace outer products \(\sum_e\mathrm{Tr}(K_e^\dagger K_e)\) | Eq.12 | \(\mathrm{Tr}J=d\) | Eq.12 | unnormalized, correct |

### Composite compatibility
| component | source | object/device/regime | composition bridge | compatible? | risk |
|---|---|---|---|---|---|
| Choi matrix | SRC-HANTZKO-PTM-v2 | input⊗output convention | fixed SWAP to output⊗input | yes internally | external interchange silently transposes tensor factors |
| Choi state | source footnote 3 | unit trace | code omits \(1/d\) | deliberately different | cannot call code result a normalized state |

### Parameter/value provenance
| parameter | value/units | provenance kind | exact locator | transform | allowed claim | forbidden claim |
|---|---|---|---|---|---|---|
| normalization | none; \(\mathrm{Tr}J=d\) for TP | direct/derived | Eq.12 + code | no \(1/d\) | internal channel equality/PSD in one convention | density matrix, normalized Choi state, or external convention without SWAP |

### Assumptions and correct-place audit
- Assumptions: common \(d\), C-contiguous logical reshape order, finite Kraus values, and same convention on both compared channels.
- Simplifications and error bounds: Frobenius Choi distance is not a diamond distance; current code does not label factor order.
- Failure regime: interchange with column-vectorized/input⊗output libraries, normalized-state metrics, or mixed dimensions.
- Why this formula belongs here: Choi representation is a scientific channel identity and test oracle substrate.
- Schedule/instrument/record bridge: none; local channel only.
- Alternative formulation/invariant: expose explicit `order`/`normalized` metadata and test entries against a hand-built asymmetric channel.
- Verdict: bridge-open for interchange; matched for current same-convention internal uses

### Independent checks
| invariant/reference | independent route | falsifier | shared blind spot? | result |
|---|---|---|---|---|
| convention | hand amplitude-damping Eq.9 construction and explicit SWAP | \(J_{\rm code}\ne SJS^\dagger\) | no | direct max difference \(0.3\); after SWAP \(0\) |
| gauge invariance | unitary mixing of Kraus index | matrix changes | no | follows outer-product unitarity; current canonical test does not exercise arbitrary mixing |
| identity channel | hand rank/trace | rank \(\ne1\) or trace \(\ne d\) | no | expected invariant recorded; dedicated canonical test absent |

### Human verification
- [ ] formula transcription checked
- [ ] exact source page checked
- [ ] symbol/unit convention checked
- [ ] derivation replayed
- [ ] application location checked
- [ ] composite bridge accepted
- Human verdict: unchecked
- Notes:

## ECS-CPTP-006 — Exponential Stinespring parameterization

### Formula and role
- Normalized formula:
  $$M=A+iB,\quad H=M+M^\dagger,\quad U=e^{+iH},\quad
    V=U[:,0{:}d],\quad K_{eab}=V_{ed+a,b},$$
  $$\sum_eK_e^\dagger K_e=V^\dagger V=I_d.$$
- Literal code realization: form a Hermitian matrix, exponentiate it, take the first \(d\) columns,
  then C-reshape the \(rd\times d\) isometry to \((r,d,d)\).
- Role: channel parameterization | generator-to-channel bridge
- Scientific object: differentiable rank-at-most-\(r\) CPTP channel family.
- Upstream inputs: real tensors \(A,B\in\mathbb R^{rd\times rd}\), \(\dim=d\), \(\mathrm{num\_kraus}=r\).
- Downstream consumers: public channel-algebra entrypoint and canonical random-channel TP checks.

### Code usage
| frozen file:line | qualname | service/call path | runtime/oracle/test | responsibility |
|---|---|---|---|---|
| `carrier/cptp_channel.py:101-104,118-123` | `StinespringChannel.kraus` | channel_algebra public entrypoint | runtime | maps unconstrained real/imag tensors to a Kraus stack |
| `tests/test_noise_mechanism_primitives.py:47-50` | seeded TP check | canonical channel_algebra | test-reference | checks only ECS-CPTP-004 on generated stacks |

### Symbols, domains, and conventions
| symbol | meaning | shape/domain | units | basis/order | source symbol |
|---|---|---|---|---|---|
| \(d,r\) | system dimension, Kraus/environment size | positive integers | none | environment-major block order | none |
| \(H\) | Hermitian unitary generator | \(rd\times rd\) | dimensionless parameter coordinate | computational/environment product | none |
| \(V\) | isometry | \(rd\times d\) | dimensionless | row \(ed+a\) | Stinespring isometry concept |
| \(K_e\) | Kraus block | \(d\times d\) | dimensionless | output \(a\), input \(b\) | \(K_i\) |

### Evidence verdict
- provenance_status: `DERIVED`
- required visible risk marker: none
- formula_correctness: correct
- application_fit: matched
- value_provenance: project-design
- epistemic_class: [ours-derived] analytic CPTP-by-construction parameterization; finite-precision residual remains

### Exact literature sources
| source ID | publication/version | PDF/hash | exact locator | visually checked page | source says | source does not say |
|---|---|---|---|---|---|---|
| SRC-HANTZKO-PTM-v2 | Hantzko et al., arXiv:2411.00526v2 | `outputs/papers/2411.00526.pdf`; `dd0421cc45fcb0e95caf803ee568720aefec6319c9015f18f5c8e6f1ef812d0a` | PDF index 2 / printed p.3, Eq.12 | yes | Kraus action with completeness is CPTP | no \(H\to U\to V\), first-column, sign, or environment-major convention |

### Source-to-code mapping
| source expression | code expression | transformation | exact/approximate | assumption | status |
|---|---|---|---|---|---|
| Eq.12 Kraus completeness | \(H\to U\to V\to K_e\) | construct an isometry and partition its rows | exact algebra | valid shapes and exact matrix exponential | derived |

### Operation replay / derivation
| input | transformation | assumption | output | source locator or derivation step | status |
|---|---|---|---|---|---|
| arbitrary \(M\) | \(H=M+M^\dagger\) | finite square matrix | \(H^\dagger=H\) | adjoint algebra | closed |
| Hermitian \(H\) | \(U=e^{+iH}\) | exact exponential | \(U^\dagger U=e^{-iH}e^{iH}=I\) | commuting inverse exponentials | closed |
| unitary \(U\) | first \(d\) columns | \(d\le rd\) | \(V^\dagger V=I_d\) | column orthonormality | closed |
| \(V_{ed+a,b}\) | reshape into \(K_{eab}\) | C/environment-major order | \(\sum_{e,a}V^*_{ed+a,b}V_{ed+a,c}=\delta_{bc}\) | index replay | closes Eq.12 |

### Composite compatibility
| component | source | object/device/regime | composition bridge | compatible? | risk |
|---|---|---|---|---|---|
| Kraus CPTP form | SRC-HANTZKO-PTM-v2 | finite-dimensional channel | unitary-column construction | yes analytically | numerical exponential/reshape not validated at boundary |
| \(+iH\) sign | project convention | abstract parameterization, not physical time | no dynamics interpretation | compatible | must not be read as \(e^{-iHt}\) physical evolution |

### Parameter/value provenance
| parameter | value/units | provenance kind | exact locator | transform | allowed claim | forbidden claim |
|---|---|---|---|---|---|---|
| \(d,r,A,B\) | caller supplied | project-design | dataclass fields/method | \(n=dr\) | a specified differentiable CPTP family | hardware-calibrated channel or a universal rank without \(r\ge d^2\) |
| column/sign/block choices | first \(d\), \(+i\), environment-major | project convention | lines 121-123 | unitary gauge/coordinate choice | same CPTP construction | physical environment basis identified by data |

### Assumptions and correct-place audit
- Assumptions: \(d,r>0\); \(A,B\) are finite \(rd\times rd\) tensors on one device; exact reshape order;
  caller interprets this as a channel parameterization rather than physical Hamiltonian time evolution.
- Simplifications and error bounds: no boundary validation or finite-precision CPTP error bound; fixed \(r\) limits rank.
- Failure regime: malformed shapes/nonfinite values, ill-conditioned large generators, or claims of physical
  identifiability for the Stinespring/environment gauge.
- Why this formula belongs here: it is the service's principal differentiable CPTP construction.
- Schedule/instrument/record bridge: no schedule/record claim; downstream placement remains separate.
- Alternative formulation/invariant: validate shapes/finiteness and report both \(V^\dagger V-I\) and Kraus residual.
- Verdict: matched analytically; numerical residual must remain explicit

### Independent checks
| invariant/reference | independent route | falsifier | shared blind spot? | result |
|---|---|---|---|---|
| isometry/TP | reviewer hand-constructed \(H,U,V,K\), direct \(V^\dagger V\) | material residual | no use of project TP helper | \(2.25\times10^{-16}\) |
| block convention | explicit \(K_{eab}=V_{ed+a,b}\) index sum | completeness fails | no | algebra closes |
| canonical test | generated stack checked by same-module TP helper | common indexing bug in both | yes | useful but not fully independent |

### Human verification
- [ ] formula transcription checked
- [ ] exact source page checked
- [ ] symbol/unit convention checked
- [ ] derivation replayed
- [ ] application location checked
- [ ] composite bridge accepted
- Human verdict: unchecked
- Notes: “never leaves the CPTP manifold” is analytic language only; machine outputs remain within measured residual.

## ECS-CPTP-007 — Gaussian Stinespring initializer

### Formula and role
- Normalized formula:
  $$n=dr,\qquad A_{ij},B_{ij}\overset{\mathrm{iid}}{\sim}
    s\,\mathcal N(0,1),\qquad s_{\mathrm{default}}=0.1,$$
  followed by ECS-CPTP-006.
- Literal code realization: CPU-seeded float64 `torch.randn` for two \(n\times n\) tensors, scaled and
  moved to the requested device.
- Role: numerical initializer | stochastic channel-family selector
- Scientific object: starting/channel distribution when the public `random` constructor is used.
- Upstream inputs: \(d,r,\mathrm{seed},s,\mathrm{device}\).
- Downstream consumers: currently the canonical channel-algebra TP test; public callers may also consume the channel.

### Code usage
| frozen file:line | qualname | service/call path | runtime/oracle/test | responsibility |
|---|---|---|---|---|
| `carrier/cptp_channel.py:107-113` | `StinespringChannel.random` | public channel_algebra constructor | runtime/test | defines the stochastic coordinate distribution |
| `tests/test_noise_mechanism_primitives.py:47-50` | seeds 0--4 | canonical acceptance | test input | uses random channels only to exercise TP |

### Symbols, domains, and conventions
| symbol | meaning | shape/domain | units | basis/order | source symbol |
|---|---|---|---|---|---|
| \(s\) | coordinate standard-deviation multiplier | nonnegative real expected; unvalidated | dimensionless | real and imaginary coordinates | none |
| \(A,B\) | generator coordinate matrices | \(dr\times dr\) real Gaussian | dimensionless | CPU RNG order | none |

### Evidence verdict
- provenance_status: `NO-SOURCE`
- required visible risk marker: **高危无出处**
- formula_correctness: correct
- application_fit: bridge-open
- value_provenance: project-design
- epistemic_class: convenience stochastic initializer; not a Haar, physical, or dimension-normalized channel ensemble

### Exact literature sources
| source ID | publication/version | PDF/hash | exact locator | visually checked page | source says | source does not say |
|---|---|---|---|---|---|---|
| none closing | search `S-B1B1-CPTP-001` | n/a | local call/source search | n/a | no exact source selected | no source assigns iid \(0.1\)-Gaussian coordinates to a physical or uniform CPTP ensemble |

### Source-to-code mapping
| source expression | code expression | transformation | exact/approximate | assumption | status |
|---|---|---|---|---|---|
| none | \(A,B=s\,\mathrm{randn}\) | project RNG choice | exact code behavior | CPU generator reproducibility is adequate | open |

### Operation replay / derivation
| input | transformation | assumption | output | source locator or derivation step | status |
|---|---|---|---|---|---|
| seed, \(d,r,s\) | draw \(2(dr)^2\) normals, then \(H=M+M^\dagger\) | normal RNG and device copy deterministic enough | CPTP channel via ECS-CPTP-006 | lines 107-123 | channel valid; ensemble meaning open |

### Composite compatibility
| component | source | object/device/regime | composition bridge | compatible? | risk |
|---|---|---|---|---|---|
| Gaussian coordinates | none | Euclidean generator chart | nonlinear exponential/Stinespring map | no invariant-measure claim | channel distribution depends strongly on \(d,r,s\) and chart |

### Parameter/value provenance
| parameter | value/units | provenance kind | exact locator | transform | allowed claim | forbidden claim |
|---|---|---|---|---|---|---|
| default \(s\) | 0.1 dimensionless | project-design | `cptp_channel.py:107` | multiplies normal coordinates; Hermitian sum changes variances | test/convenience default | hardware variability, Haar randomness, or comparable channel strength across dimensions |
| seed | 0 default | project-design | line 107 | CPU RNG | repeatable intended input | cross-version/device bitwise scientific ensemble without verification |

### Assumptions and correct-place audit
- Assumptions: constructor is used as an optimizer/test initializer, not as a physical noise prior.
- Simplifications and error bounds: no dimension scaling, invariant measure, or induced channel-distance distribution.
- Failure regime: comparing dimensions/ranks, treating seed sweeps as uncertainty, or interpreting draws as hardware channels.
- Why this formula belongs here: it produces scientific channel objects through a public service entrypoint and supplies test inputs.
- Schedule/instrument/record bridge: none.
- Alternative formulation/invariant: name it explicitly as a coordinate initializer and use a separately specified channel ensemble
  when stochastic physics is intended.
- Verdict: bridge-open

### Independent checks
| invariant/reference | independent route | falsifier | shared blind spot? | result |
|---|---|---|---|---|
| call-site inventory | repository search | claim-bearing production caller | no | only canonical TP test found at freeze |
| ensemble semantics | compare induced norms across \(d,r\) | dimension-invariant interpretation | not run | no such guarantee/source |

### Human verification
- [ ] formula transcription checked
- [ ] exact source page checked
- [ ] symbol/unit convention checked
- [ ] derivation replayed
- [ ] application location checked
- [ ] composite bridge accepted
- Human verdict: unchecked
- Notes: `StinespringChannel.parameters:115-116` is inspected no-formula optimizer plumbing.

## ECS-CPTP-008 — Single-qubit IXYZ Pauli-transfer matrix

### Formula and role
- Normalized formula:
  $$P_0=I,\ P_1=X,\ P_2=Y,\ P_3=Z,\qquad
    R_{ab}=\frac12\operatorname{Re}\operatorname{Tr}\!\left[P_a\Phi(P_b)\right].$$
- Literal code realization: stack \((I,X,Y,Z)\), apply ECS-CPTP-002 in batch, then
  `0.5 * einsum("aij,bji->ab", paulis, transformed).real`.
- Role: channel representation | diagnostic substrate
- Scientific object: normalized real Pauli-Liouville/PTM representation for a single-qubit
  Hermiticity-preserving channel; row \(a\)=output coefficient, column \(b\)=input basis element.
- Upstream inputs: \(2\times2\) Kraus stack.
- Downstream consumers: mechanism teachers, Pauli twirl controls, and ECS-CPTP-009/010.

### Code usage
| frozen file:line | qualname | service/call path | runtime/oracle/test | responsibility |
|---|---|---|---|---|
| `carrier/cptp_channel.py:129-145` | `single_qubit_paulis`; `pauli_transfer_matrix` | channel_algebra -> teachers/tests | runtime | fixes IXYZ order, normalization, index orientation, and real projection |
| `mechanisms/teachers.py:135,143` | teacher/twirl diagnostics | channel_algebra | runtime | consumes the PTM |
| `tests/test_noise_mechanism_primitives.py:53-58,128-139` | off-diagonal/twirl checks | canonical acceptance | test-reference | shares this PTM helper and lacks a hand-entry oracle |

### Symbols, domains, and conventions
| symbol | meaning | shape/domain | units | basis/order | source symbol |
|---|---|---|---|---|---|
| \(P_a\) | Pauli basis element | \(2\times2\), Hermitian | none | I,X,Y,Z | \(\sigma^a\) |
| \(R_{ab}\) | channel coordinate | \(4\times4\), real for HP maps | dimensionless | output row/input column | \(\mathrm{PTM}(\mathcal E)_{s,t}\) |

### Evidence verdict
- provenance_status: `DERIVED`
- required visible risk marker: none
- formula_correctness: correct
- application_fit: matched
- value_provenance: complete
- epistemic_class: [ours-derived] normalized single-qubit expansion from a direct Pauli-basis/PTM definition

### Exact literature sources
| source ID | publication/version | PDF/hash | exact locator | visually checked page | source says | source does not say |
|---|---|---|---|---|---|---|
| SRC-HANTZKO-PTM-v2 | Hantzko et al., arXiv:2411.00526v2 | `outputs/papers/2411.00526.pdf`; `dd0421cc45fcb0e95caf803ee568720aefec6319c9015f18f5c8e6f1ef812d0a` | PDF index 1/printed p.2 basis convention; index 2/printed p.3 Eqs.2-3 and PTM paragraph | yes | Pauli strings/basis and \(\mathrm{PTM}_{s,t}=\langle\sigma^s,\mathcal E(\sigma^t)\rangle\) | its prose is not unambiguous enough to cite the code's explicit \(1/2\) as a verbatim formula |
| SRC-KAUFMANN-COH-v3 | Kaufmann, Rojkov & Reiter, arXiv:2307.08741v3 | `docs/papers/coherent_robust_pauli_2307.08741.pdf`; `6054774681b301ab7d627cd424b23b9881478547fa45ea268035453afbaffd80` | PDF index 2 / printed p.3, Sec.III/Eq.4 vicinity | yes | PTM action and a two-qubit \(1/4\) coefficient in Eq.4 | nearby prose omits the normalization in one displayed \(T_{ij}\) definition; corroborating only |

### Source-to-code mapping
| source expression | code expression | transformation | exact/approximate | assumption | status |
|---|---|---|---|---|---|
| Pauli-basis channel matrix | \(\frac12\mathrm{Tr}[P_a\Phi(P_b)]\) | use \(\mathrm{Tr}(P_aP_b)=2\delta_{ab}\) to extract single-qubit coefficients | exact [ours-derived] | unnormalized Pauli matrices | closed |
| complex trace | `.real` | discard imaginary roundoff | exact for Hermiticity-preserving \(\Phi\) | valid Kraus map | matched |

### Operation replay / derivation
| input | transformation | assumption | output | source locator or derivation step | status |
|---|---|---|---|---|---|
| \(\Phi(P_b)=\sum_a c_{ab}P_a\) | multiply by \(P_c\), trace | Pauli orthogonality | \(c_{cb}=\frac12\mathrm{Tr}[P_c\Phi(P_b)]\) | Eqs.2-3 + explicit matrices | closed [ours-derived] |
| code einsum | \(\sum_{ij}(P_a)_{ij}\Phi(P_b)_{ji}\) | trace order | \(\mathrm{Tr}[P_a\Phi(P_b)]\) | index replay | exact |

### Composite compatibility
| component | source | object/device/regime | composition bridge | compatible? | risk |
|---|---|---|---|---|---|
| PTM basis/indices | SRC-HANTZKO-PTM-v2 | \(n\)-qubit formalism | specialize to \(n=1\), IXYZ | yes | callers must not infer multi-qubit support |
| Kraus action | ECS-CPTP-002 | Hermitian Pauli inputs | batch action plus projection | yes for HP channels | malformed/non-HP map would be silently real-projected |

### Parameter/value provenance
| parameter | value/units | provenance kind | exact locator | transform | allowed claim | forbidden claim |
|---|---|---|---|---|---|---|
| normalization \(1/2\) | dimensionless | complete algebraic derivation | Pauli orthogonality | coefficient extraction | identity channel maps to \(I_4\) | direct verbatim attribution to ambiguous source prose |

### Assumptions and correct-place audit
- Assumptions: single qubit, IXYZ order, Hermiticity-preserving channel, valid \(2\times2\) Kraus operators.
- Simplifications and error bounds: imaginary residual is discarded without reporting; no dimension/domain validation.
- Failure regime: qudits, multi-qubit channels, alternate Pauli ordering/normalization, or non-HP linear maps.
- Why this formula belongs here: PTM coordinates drive mechanism diagnostics and twirling controls.
- Schedule/instrument/record bridge: local channel representation only.
- Alternative formulation/invariant: validate \(d=2\), expose ordering/normalization metadata, and retain complex residual diagnostics.
- Verdict: matched

### Independent checks
| invariant/reference | independent route | falsifier | shared blind spot? | result |
|---|---|---|---|---|
| identity/X/RZ analytic PTMs | hand Pauli conjugation | wrong factor/order/transpose | not in canonical tests | reviewer recommends; formula replay closes algebra |
| amplitude damping | hand Kraus algebra | expected \(R_{ZI}=\gamma\) absent | no | reviewer obtained \(R_{ZI}=0.3\) for \(\gamma=0.3\) |
| twirl test | diagonalize same helper output | helper convention wrong identically on both sides | yes | behavior check, not independent formula oracle |

### Human verification
- [ ] formula transcription checked
- [ ] exact source page checked
- [ ] symbol/unit convention checked
- [ ] derivation replayed
- [ ] application location checked
- [ ] composite bridge accepted
- Human verdict: unchecked
- Notes: the old local reading note labels Hantzko v1; the frozen PDF itself is v2 and controls this row.

## ECS-CPTP-009 — PTM off-diagonal witness of non-Pauli action

### Formula and role
- Normalized formula:
  $$\exists\,a\ne b:\ R_{ab}\ne0
    \quad\Longrightarrow\quad
    \Phi\ \text{is not a stochastic Pauli channel in the declared IXYZ basis}.$$
- Literal code realization: scientific claim in the `pauli_transfer_matrix` docstring; consumers/tests
  inspect the off-diagonal block.
- Role: diagnostic | negative model-class witness
- Scientific object: exclusion of the diagonal stochastic-Pauli channel family.
- Upstream inputs: ECS-CPTP-008.
- Downstream consumers: non-Pauli capability tests and teacher/twirl comparisons.

### Code usage
| frozen file:line | qualname | service/call path | runtime/oracle/test | responsibility |
|---|---|---|---|---|
| `carrier/cptp_channel.py:137-145` | `pauli_transfer_matrix` docstring/output | channel_algebra | runtime claim | states diagonal-Pauli/off-diagonal implication |
| `tests/test_noise_mechanism_primitives.py:53-58` | off-diagonal magnitude check | canonical channel_algebra | gate | confirms one generated channel is outside the diagonal family |

### Symbols, domains, and conventions
| symbol | meaning | shape/domain | units | basis/order | source symbol |
|---|---|---|---|---|---|
| \(R\) | ECS-CPTP-008 PTM | real \(4\times4\) | dimensionless | IXYZ | PTM |
| stochastic Pauli channel | \(\Phi(\rho)=\sum_Pp_P P\rho P\) | \(p_P\ge0,\sum p_P=1\) | probabilities | same Pauli basis | Pauli channel |

### Evidence verdict
- provenance_status: `DERIVED`
- required visible risk marker: none
- formula_correctness: correct
- application_fit: matched
- value_provenance: complete
- epistemic_class: one-way exact exclusion witness; not a complete classifier of non-Pauli mechanisms

### Exact literature sources
| source ID | publication/version | PDF/hash | exact locator | visually checked page | source says | source does not say |
|---|---|---|---|---|---|---|
| SRC-HANTZKO-PTM-v2 | Hantzko et al., arXiv:2411.00526v2 | `outputs/papers/2411.00526.pdf`; `dd0421cc45fcb0e95caf803ee568720aefec6319c9015f18f5c8e6f1ef812d0a` | printed pp.1,3, PTM/Pauli-twirl discussion | yes | PTM represents action in Pauli basis; Pauli twirling removes non-Pauli structure | no claim that every off-diagonal term is coherent |
| SRC-KAUFMANN-COH-v3 | Kaufmann et al., arXiv:2307.08741v3 | `docs/papers/coherent_robust_pauli_2307.08741.pdf`; `6054774681b301ab7d627cd424b23b9881478547fa45ea268035453afbaffd80` | PDF index 2 / printed p.3, Sec.III | yes | Pauli noise has diagonal Pauli-Liouville representation in its model | explicitly notes nonunital noise lies outside its coherent-rotated-Pauli model |

### Source-to-code mapping
| source expression | code expression | transformation | exact/approximate | assumption | status |
|---|---|---|---|---|---|
| Pauli conjugation acts diagonally on Pauli basis | off-diagonal \(R_{ab}\) test | contrapositive of family property | exact one-way implication | same normalization/order and exact nonzero | derived |

### Operation replay / derivation
| input | transformation | assumption | output | source locator or derivation step | status |
|---|---|---|---|---|---|
| \(\Phi(P_b)=\sum_Pp_P P P_b P\) | \(PP_bP=\pm P_b\) | Pauli conjugation | only coefficient along \(P_b\); \(R_{ab}=0\) for \(a\ne b\) | Pauli algebra | closed |
| observed \(R_{ab}\ne0\) | contrapositive | exact arithmetic/basis | not stochastic Pauli | previous step | closed |

### Composite compatibility
| component | source | object/device/regime | composition bridge | compatible? | risk |
|---|---|---|---|---|---|
| diagonal family property | Pauli algebra/Kaufmann | stochastic Pauli channel | ECS-CPTP-008 convention | yes | numerical off-diagonal tolerance is caller-specific |

### Parameter/value provenance
| parameter | value/units | provenance kind | exact locator | transform | allowed claim | forbidden claim |
|---|---|---|---|---|---|---|
| “nonzero” tolerance | mathematical zero here | complete in exact algebra | implication | none | exact exclusion statement | finite-precision pass/fail without a separate threshold/error row |

### Assumptions and correct-place audit
- Assumptions: declared IXYZ PTM, exact/non-roundoff off-diagonal entry, and stochastic-Pauli comparison class.
- Simplifications and error bounds: the witness does not identify which non-Pauli mechanism caused the entry.
- Failure regime: alternate bases, numerical leakage, or using a caller threshold without calibration.
- Why this formula belongs here: it is an explicit scientific diagnostic claim attached to the runtime representation.
- Schedule/instrument/record bridge: no mechanism-to-record identification follows.
- Alternative formulation/invariant: report the full PTM and compare against a threshold with a precision/error budget.
- Verdict: matched

### Independent checks
| invariant/reference | independent route | falsifier | shared blind spot? | result |
|---|---|---|---|---|
| Pauli channel diagonal | hand conjugation table for IXYZ | off-diagonal entry | no | diagonal exactly |
| non-Pauli examples | amplitude damping and rotations | non-Pauli channel always diagonal | no | both may show off-diagonal; implication remains one-way |

### Human verification
- [ ] formula transcription checked
- [ ] exact source page checked
- [ ] symbol/unit convention checked
- [ ] derivation replayed
- [ ] application location checked
- [ ] composite bridge accepted
- Human verdict: unchecked
- Notes:

## ECS-CPTP-010 — Misapplied PTM off-diagonal coherence certificate

### Formula and role
- Normalized claimed implication:
  $$\exists\,a\ne b:\ R_{ab}\ne0
    \quad\overset{\text{claimed}}{\Longrightarrow}\quad
    \Phi\ \text{contains coherent/unitary error}.$$
- Literal code realization: the phrase “nonzero off-diagonal entries certify coherent / non-Pauli action”
  in `pauli_transfer_matrix`.
- Role: diagnostic claim | mechanism attribution
- Scientific object: attempted classification of non-Pauli PTM structure as coherent noise.
- Upstream inputs: ECS-CPTP-008.
- Downstream consumers: prose interpretation of the channel-algebra capability test.

### Code usage
| frozen file:line | qualname | service/call path | runtime/oracle/test | responsibility |
|---|---|---|---|---|
| `carrier/cptp_channel.py:137-142` | `pauli_transfer_matrix` docstring | channel_algebra | runtime scientific claim | joins “coherent” and “non-Pauli” despite different model classes |
| `tests/test_noise_mechanism_primitives.py:53-58` | off-diagonal threshold | canonical acceptance | gate/interpretation | demonstrates non-Pauli capability, not coherence identification |

### Symbols, domains, and conventions
| symbol | meaning | shape/domain | units | basis/order | source symbol |
|---|---|---|---|---|---|
| coherent error | reversible/unitary systematic component | mechanism class, not a single PTM entry | n/a | model-dependent | \(U_\theta\) in Kaufmann |
| \(R_{ab}\) | off-diagonal PTM element | real scalar | dimensionless | IXYZ | \(T_{ab}\) |

### Evidence verdict
- provenance_status: `CONTRADICTED/MISAPPLIED`
- required visible risk marker: none for this status
- formula_correctness: incorrect
- application_fit: mismatched
- value_provenance: incomplete
- epistemic_class: overgeneralized mechanism certificate; only valid under a restricted coherently-rotated-Pauli model

### Exact literature sources
| source ID | publication/version | PDF/hash | exact locator | visually checked page | source says | source does not say |
|---|---|---|---|---|---|---|
| SRC-KAUFMANN-COH-v3 | Kaufmann et al., arXiv:2307.08741v3 | `docs/papers/coherent_robust_pauli_2307.08741.pdf`; `6054774681b301ab7d627cd424b23b9881478547fa45ea268035453afbaffd80` | PDF index 2 / printed p.3, Sec.III, Eq.4 and assumptions | yes | first-order coherent terms occupy off-diagonal PTM entries when noise is small and the incoherent component is Pauli | explicitly restricts the model and notes nonunital decay exceeds its expressibility |

### Source-to-code mapping
| source expression | code expression | transformation | exact/approximate | assumption | status |
|---|---|---|---|---|---|
| restricted \(U_\theta\circ\mathcal P\), small-error model | arbitrary single-qubit Kraus channel | drops small-error, Pauli-incoherent, and unital/model assumptions | invalid generalization | every non-Pauli term is coherent | contradicted |

### Operation replay / derivation
| input | transformation | assumption | output | source locator or derivation step | status |
|---|---|---|---|---|---|
| amplitude damping with probability \(\gamma\) | hand Pauli-basis action | no coherent/unitary component | \(R_{ZI}=\gamma\ne0\) | reviewer independent calculation | falsifies implication |
| \(\gamma=0.3\) | evaluate hand formula | standard damping Kraus pair | off-diagonal \(0.3\) | no project helper | concrete counterexample |

### Composite compatibility
| component | source | object/device/regime | composition bridge | compatible? | risk |
|---|---|---|---|---|---|
| Kaufmann off-diagonal coherent term | SRC-KAUFMANN-COH-v3 | small coherently-rotated Pauli model | arbitrary CPTP channel | no | dissipative/nonunital mechanisms are mislabeled coherent |

### Parameter/value provenance
| parameter | value/units | provenance kind | exact locator | transform | allowed claim | forbidden claim |
|---|---|---|---|---|---|---|
| off-diagonal threshold | docstring says nonzero; canonical test uses 0.1 | incomplete/caller-design | source line/test | magnitude comparison | example channel is non-Pauli | coherent mechanism identified or quantified |

### Assumptions and correct-place audit
- Assumptions silently omitted by code prose: small error, Pauli incoherent component, coherently rotated
  Pauli model, and exclusion of nonunital dissipative channels.
- Simplifications and error bounds: no decomposition or coherence metric is computed.
- Failure regime: amplitude damping, reset, thermalization, leakage reduction, and general affine/nonunital channels.
- Why this formula belongs here: it converts a representation feature into a mechanism claim.
- Schedule/instrument/record bridge: no record-level coherent-mechanism identification follows.
- Alternative formulation/invariant: retain ECS-CPTP-009 wording (“non-Pauli in this basis”) and use a
  model-qualified coherent fit or an established coherence/unitarity metric separately.
- Verdict: mismatched

### Independent checks
| invariant/reference | independent route | falsifier | shared blind spot? | result |
|---|---|---|---|---|
| amplitude damping | hand Kraus/PTM derivation | all off-diagonal entries zero | no | \(R_{ZI}=0.3\), no coherent unitary component |
| source assumptions | visual read of Kaufmann p.3 | unrestricted theorem | no | source is explicitly restricted; code claim overgeneralizes |

### Human verification
- [ ] formula transcription checked
- [ ] exact source page checked
- [ ] symbol/unit convention checked
- [ ] derivation replayed
- [ ] application location checked
- [ ] composite bridge accepted
- Human verdict: unchecked
- Notes: no source or code fix is made; the contradicted wording remains visible for owner adjudication.

<!-- BATCH-1B1-ROWS-END -->

## ECS-CHAN-001 — Pauli-generator rotation family

### Formula and role
- Normalized formula:
  $$U_P(\theta)=e^{-i\theta P/2}
    =\cos(\theta/2)I-i\sin(\theta/2)P,\qquad
    P=P^\dagger,\quad P^2=I.$$
- Literal code realization: explicit \(R_X,R_Y,R_Z,R_{ZZ}\) matrices plus
  \(\cos(\theta/2)I-i\sin(\theta/2)(\sigma_l\otimes\sigma_r)\).
- Role: unitary | channel primitive | coherent-mechanism support
- Scientific object: finite-angle one- and two-qubit rotations generated by Hermitian Pauli
  involutions in computational basis order.
- Upstream inputs: angle \(\theta\), Pauli labels, and the fixed \(I,X,Y,Z\) matrices.
- Downstream consumers: retained mechanism adapter M6--M8, M11, M20, M22--M23, M28--M33;
  ECS-CHAN-002--005 and the later channel builders at lines 522--769.

### Code usage
| frozen file:line | qualname | service/call path | runtime/oracle/test | responsibility |
|---|---|---|---|---|
| `carrier/channels.py:415-447` | `rzz_unitary`; `rx_unitary`; `ry_unitary`; `rz_unitary`; `rxx_unitary`; `ryy_unitary` | channel_algebra -> retained mechanism adapter | runtime | explicit one-/two-Pauli rotations |
| `carrier/channels.py:770-782` | `_single_qubit_paulis`; `two_pauli_rotation` | channel_algebra primitive | runtime | computational-basis Pauli matrices and generic Kronecker generator |
| `carrier/channels.py:458-464,467-490` | `_axis_unitary`; `drifted_axis_mixture_kraus` | ECS-CHAN-004 | runtime | valid-axis dispatch and random-unitary components |
| `tests/test_carrier_channels_units.py:294-352` | rotation/expm pins | canonical channel_algebra | test-reference | independently exponentiates hand-typed matrices on ordinary finite inputs |

### Symbols, domains, and conventions
| symbol | meaning | shape/domain | units | basis/order | source symbol |
|---|---|---|---|---|---|
| \(P\) | Hermitian Pauli or Pauli-product generator | \(2\times2\) or \(4\times4\), \(P^2=I\) | dimensionless | \(I,X,Y,Z\); left label is outer Kronecker factor | \(\hat r\cdot\vec\sigma\), \(S_\beta\) |
| \(\theta\) | signed rotation angle | finite real | rad | half-angle convention | \(\epsilon,\theta_j,2\alpha\) |
| \(U_P\) | unitary generated by \(P\) | \(d\times d\), complex128 in code | dimensionless | computational basis | \(U,U_d\) |

### Evidence verdict
- provenance_status: `DERIVED`
- required visible risk marker: none; exact finite-domain derivation is closed
- formula_correctness: correct
- application_fit: matched
- value_provenance: complete
- epistemic_class: direct operator premises plus exact involution-series derivation; caller-specific
  physical angle magnitudes and mechanism placement are audited separately

### Exact literature sources
| source ID | publication/version | PDF/hash | exact locator | visually checked page | source says | source does not say |
|---|---|---|---|---|---|---|
| SRC-SHELDON-RB-v1 | Sheldon et al., arXiv:1504.06597v1; Phys. Rev. A 93, 012301 (2016) | `outputs/papers/1504.06597.pdf` / `609232d9fc4f3066aec0bc520174e88107ed4444e70dcfec3e05e164f589f7c9` | printed/PDF p.2 Eq.1 | yes, full equation and symbol sentence | \(U=\exp[-i(\epsilon/2)\hat r\cdot\vec\sigma]\) | two-qubit label order or project dtype |
| SRC-CLADER-ROT-v2 | Clader et al., arXiv:2101.11631v2; Phys. Rev. A 103, 052428 (2021) | `outputs/papers/2101.11631.pdf` / `406484c2c0cb1d9450c45df793d8a57763ea488a1c8767a6d851bb99d521c521` | printed/PDF p.2 Eq.1 | yes, equation plus unit-axis definition | \(\cos(\theta_j/2)I-i\sin(\theta_j/2)\vec v\cdot\vec\sigma^{(j)}\), \(\|\vec v\|=1\) | arbitrary mapping-key repair or a numerical norm floor |
| SRC-KRAUS-CIRAC-v1 | Kraus & Cirac, arXiv:quant-ph/0011050v1; Phys. Rev. A 63, 062309 (2001) | `outputs/papers/quant-ph/0011050.pdf` / `34114cd648ada331e10e832ceae6dbb9e01b59eea09983b27f99fb8062df8dc5` | printed/PDF p.5 Eqs.24,26 | yes, both equations and commutator statement | pure \(XX\) closed form and \(S_\beta=\sigma_\beta\otimes\sigma_\beta\) | all cross-label mechanisms or their physical strengths |
| SRC-HANTZKO-PTM-v2 | Hantzko et al., arXiv:2411.00526v2 | `outputs/papers/2411.00526.pdf` / `dd0421cc45fcb0e95caf803ee568720aefec6319c9015f18f5c8e6f1ef812d0a` | printed p.3 Eqs.2--3 | yes, previously checked | normalized Pauli basis/matrices | rotation-angle or mechanism semantics |

### Source-to-code mapping
| source expression | code expression | transformation | exact/approximate | assumption | status |
|---|---|---|---|---|---|
| \(\exp[-i(\theta/2)P]\) | explicit RX/RY/RZ/RZZ matrices | substitute \(X,Y,Z,ZZ\) | exact | finite real \(\theta\) | closed |
| \(e^{-i\alpha S_x}=\cos\alpha I-i\sin\alpha XX\) | `two_pauli_rotation(theta,\"X\",\"X\")` | \(\alpha=\theta/2\) | exact | \(XX^2=I\) | closed |
| normalized Pauli matrices | `_single_qubit_paulis` | numerical transcription | exact | computational basis | closed |
| arbitrary \(P=\sigma_l\otimes\sigma_r\) | generic two-label builder | use \(P^2=I\) to sum the exponential series | exact | labels in \(I,X,Y,Z\) | derived closed |

### Operation replay / derivation
| input | transformation | assumption | output | source locator or derivation step | status |
|---|---|---|---|---|---|
| \(P^2=I\) | split exponential series into even and odd powers | \(P=P^\dagger\) | \(\cos(\theta/2)I-i\sin(\theta/2)P\) | [ours-derived] elementary series from source exponentials | exact |
| \(Z\otimes Z=\operatorname{diag}(1,-1,-1,1)\) | apply the closed form | computational order \(00,01,10,11\) | code diagonal at lines 418--420 | direct replay | exact |
| finite test angles | independent `scipy.linalg.expm` of hand-typed \(P\) | test reference does not call source builders | maximum pin error below \(10^{-12}\) | canonical test lines 128--151,294--343 | pass |

### Composite compatibility
| component | source | object/device/regime | composition bridge | compatible? | risk |
|---|---|---|---|---|---|
| single-axis exponential | SRC-SHELDON-RB-v1 / SRC-CLADER-ROT-v2 | coherent single-qubit rotation | axis chosen as X/Y/Z | yes | angle magnitude not licensed |
| two-body canonical axes | SRC-KRAUS-CIRAC-v1 | closed two-qubit unitary | half-angle project convention | yes | local dressing and hardware placement excluded |
| cross-label Pauli products | Pauli algebra | mathematical primitive | generic labels \(I,X,Y,Z\) | yes algebraically | no device-specific source for each retained mechanism |

### Parameter/value provenance
| parameter | value/units | provenance kind | exact locator | transform | allowed claim | forbidden claim |
|---|---|---|---|---|---|---|
| half-angle coefficient | \(1/2\), dimensionless | source + algebraically fixed | source equations above | \(\alpha=\theta/2\) | exact rotation convention | calibrated hardware strength |
| dtype | complex128 | project numerical policy | code lines 420,427,434,439,782 | array cast | implementation precision identity | global forward-error guarantee |
| mechanism angles | caller supplied/defaulted | outside this primitive row | adapter lines 308--412 | float cast | formula evaluation at given angle | provenance of M6--M33 values |

### Assumptions and correct-place audit
- Assumptions: valid Pauli labels; finite real angle; the requested scientific object is a closed
  Pauli-generated unitary.
- Simplifications and error bounds: no truncation is used; floating trigonometric error is not globally bounded.
- Failure regime: NaN/inf angles propagate or raise; invalid labels raise a bare `KeyError`; physical
  multilevel dressing and dissipation are outside this primitive.
- Why this formula belongs here: it directly changes carrier unitaries and is reused by multiple mechanisms.
- Schedule/instrument/record bridge: primitive algebra is matched; caller-specific schedule and magnitude
  claims remain in their owning batches.
- Alternative formulation/invariant: require \(U^\dagger U=I\) and compare against
  \(\exp[-i\theta P/2]\) using an independently typed generator.
- Verdict: matched

### Independent checks
| invariant/reference | independent route | falsifier | shared blind spot? | result |
|---|---|---|---|---|
| \(U^\dagger U=I\) | hand algebra using \(P^2=I\) | dropped \(i\), sign, or half-angle | no | exact on domain |
| matrix values | SciPy exponential of hand-typed matrices | sign/order mutation | low; shares only mathematical definition | canonical pins pass |
| targeted canonical batch | pytest two owning files | implementation regression | yes for downstream semantics | 71 passed; not a source upgrade |

### Human verification
- [ ] formula transcription checked
- [ ] exact source page checked
- [ ] symbol/unit convention checked
- [ ] derivation replayed
- [ ] application location checked
- [ ] composite bridge accepted
- Human verdict: unchecked
- Notes: source pages were visually checked by the coordinator; checkboxes remain human-only.

## ECS-CHAN-002 — Commuting RXX/RYY composition

### Formula and role
- Normalized formula:
  $$U_{XX+YY}=
  e^{-i\theta_yYY/2}e^{-i\theta_xXX/2}
  =e^{-\frac i2(\theta_xXX+\theta_yYY)},\qquad [XX,YY]=0.$$
- Literal code realization:
  `ryy_unitary(theta_y) @ rxx_unitary(theta_x)`.
- Role: unitary composition | coherent exchange-family primitive
- Scientific object: a two-angle composition along the mutually commuting \(XX\) and \(YY\)
  canonical axes.
- Upstream inputs: ECS-CHAN-001 matrices and two finite real angles.
- Downstream consumers: retained M10 branch; legacy Torch comparison is not an acceptance oracle.

### Code usage
| frozen file:line | qualname | service/call path | runtime/oracle/test | responsibility |
|---|---|---|---|---|
| `carrier/channels.py:450-451` | `rxx_ryy_unitary` | channel_algebra -> M10 adapter | runtime | multiply the two commuting rotations |
| `tests/test_carrier_channels_units.py:338-352` | composite pin | canonical channel_algebra | test-reference | pins distinct \(\theta_x,\theta_y\) against independent exponentials |
| `tests/test_window_channel.py:453-472` | legacy Torch comparison | migration-era legacy | test-reference | prints but does not assert the one-angle mapping |

### Symbols, domains, and conventions
| symbol | meaning | shape/domain | units | basis/order | source symbol |
|---|---|---|---|---|---|
| \(XX,YY\) | Pauli products | Hermitian \(4\times4\), square to \(I\) | dimensionless | left-outer computational order | \(S_x,S_y\) |
| \(\theta_x,\theta_y\) | independent signed angles | finite real | rad | half-angle convention | \(2\alpha_x,2\alpha_y\) |

### Evidence verdict
- provenance_status: `DERIVED`
- required visible risk marker: none for the algebra; mechanism parameter mapping remains separately open
- formula_correctness: correct
- application_fit: matched
- value_provenance: complete
- epistemic_class: exact commuting-exponential identity derived from a directly stated canonical-axis source

### Exact literature sources
| source ID | publication/version | PDF/hash | exact locator | visually checked page | source says | source does not say |
|---|---|---|---|---|---|---|
| SRC-KRAUS-CIRAC-v1 | Kraus & Cirac, arXiv:quant-ph/0011050v1; Phys. Rev. A 63, 062309 (2001) | `outputs/papers/quant-ph/0011050.pdf` / `34114cd648ada331e10e832ceae6dbb9e01b59eea09983b27f99fb8062df8dc5` | printed/PDF p.5 Eqs.24,26 and following sentence | yes | \(S_\beta=\sigma_\beta\otimes\sigma_\beta\) and \([S_x,S_y]=0\) | project M10 ratio or physical exchange strength |

### Source-to-code mapping
| source expression | code expression | transformation | exact/approximate | assumption | status |
|---|---|---|---|---|---|
| \(S_x=XX,S_y=YY,[S_x,S_y]=0\) | RYY matrix-multiplied by RXX | set independent coefficients \(\theta_x/2,\theta_y/2\) | exact | finite real angles | closed |
| \(e^{A+B}=e^Ae^B\) for \([A,B]=0\) | one matrix product | standard commuting exponential identity | exact | exact Pauli matrices | derived closed |

### Operation replay / derivation
| input | transformation | assumption | output | source locator or derivation step | status |
|---|---|---|---|---|---|
| \(XX,YY\) | \((XX)(YY)=(XY)\otimes(XY)\) | \(XY=iZ\) | \(-ZZ\) | hand algebra | exact |
| reverse product | \((YY)(XX)=(-iZ)\otimes(-iZ)\) | Pauli multiplication | \(-ZZ\) | hand algebra | exact |
| \(\theta_x=.025,\theta_y=.0175\) | compare product to combined SciPy exponential | independent generator | max error \(3.47\times10^{-18}\) | coordinator replay | pass |

### Composite compatibility
| component | source | object/device/regime | composition bridge | compatible? | risk |
|---|---|---|---|---|---|
| RXX and RYY | ECS-CHAN-001 | closed two-qubit unitary | exact commuting product | yes | none algebraic |
| retained M10 call | project adapter | mechanism mapping | defaults \(\theta_y=0.7\theta_x\) | deferred | ratio and hardware meaning not licensed here |

### Parameter/value provenance
| parameter | value/units | provenance kind | exact locator | transform | allowed claim | forbidden claim |
|---|---|---|---|---|---|---|
| \(\theta_x,\theta_y\) | arbitrary finite radians | caller input | code signature | float cast | exact two-angle operator | physical magnitude |
| default M10 ratio | \(0.7\) | outside sub-batch/project design | adapter line 346 | multiplication | none in this row | sourced exchange anisotropy |

### Assumptions and correct-place audit
- Assumptions: both factors use the same qubit order and exact Pauli matrices.
- Simplifications and error bounds: no Trotter error because the generators commute.
- Failure regime: nonfinite angles; a future noncommuting replacement would invalidate the collapse.
- Why this formula belongs here: it constructs the runtime M10 unitary.
- Schedule/instrument/record bridge: algebra matched; M10 parameter and placement audit is deferred to
  the compatibility/catalog sub-batch.
- Alternative formulation/invariant: directly exponentiate
  \(-i(\theta_xXX+\theta_yYY)/2\) and check the commutator.
- Verdict: matched

### Independent checks
| invariant/reference | independent route | falsifier | shared blind spot? | result |
|---|---|---|---|---|
| commutator | hand Pauli multiplication | nonzero entry | no | maximum \(0\) |
| combined exponential | SciPy `expm` of summed generator | wrong angle-to-axis mapping | no | \(3.47\times10^{-18}\) max error |
| canonical test | distinct-angle pin | swapped angle arguments | small: source builders not reused | pass within \(10^{-11}\) |

### Human verification
- [ ] formula transcription checked
- [ ] exact source page checked
- [ ] symbol/unit convention checked
- [ ] derivation replayed
- [ ] application location checked
- [ ] composite bridge accepted
- Human verdict: unchecked
- Notes:

## ECS-CHAN-003 — Conditional phase on the \(|11\rangle\) projector

### Formula and role
- Normalized formula:
  $$U_{\rm CP}(\theta)=e^{-i\theta|11\rangle\langle11|}
   =\operatorname{diag}(1,1,1,e^{-i\theta}),$$
  with
  $$|11\rangle\langle11|=\frac14(II-ZI-IZ+ZZ).$$
- Literal code realization:
  `diag([1,1,1,exp(-1j*theta)])`.
- Role: unitary | conditional-phase/cross-Kerr primitive
- Scientific object: a phase accumulated only by the two-qubit \(|11\rangle\) state.
- Upstream inputs: signed phase angle and computational basis.
- Downstream consumers: retained M21 branch; catalog-to-mechanism interpretation is deferred.

### Code usage
| frozen file:line | qualname | service/call path | runtime/oracle/test | responsibility |
|---|---|---|---|---|
| `carrier/channels.py:454-455` | `controlled_phase_error_unitary` | channel_algebra -> retained M21 adapter | runtime | exact diagonal conditional phase |
| `tests/test_carrier_channels_units.py:355-371` | controlled-phase pin | canonical channel_algebra | test-reference | repeats the diagonal and discriminates angle sign |

### Symbols, domains, and conventions
| symbol | meaning | shape/domain | units | basis/order | source symbol |
|---|---|---|---|---|---|
| \(\Pi_{11}\) | \(|11\rangle\) projector | rank-one \(4\times4\) | dimensionless | \(00,01,10,11\) | conditional \(|11\rangle\) energy |
| \(\theta\) | integrated conditional phase | finite real | rad | negative Schrödinger-evolution sign | \(\phi_\zeta=\int\zeta(t)dt\) |

### Evidence verdict
- provenance_status: `DIRECT`
- required visible risk marker: none for the matrix; catalog placement is explicitly deferred
- formula_correctness: correct
- application_fit: bridge-open
- value_provenance: complete
- epistemic_class: exact primary-source matrix match; project mechanism ID and magnitude are not
  certified by this primitive row

### Exact literature sources
| source ID | publication/version | PDF/hash | exact locator | visually checked page | source says | source does not say |
|---|---|---|---|---|---|---|
| SRC-PETTERSSON-ZZ-v2 | Pettersson Fors, Fernández-Pendás & Kockum, arXiv:2408.15402v2 (2024) | `outputs/papers/2408.15402.pdf` / `4a21b457f6b0d012bd1347cb42996bc9f03cbde772213095826a0549a199deb2` | printed/PDF p.4 Eq.6 and surrounding text | yes, matrix, phase integral, and CPHASE paragraph | \(U_\zeta=\operatorname{diag}(1,1,1,e^{-i\phi_\zeta})\), \(\phi_\zeta=\int\zeta(t')dt'\) | that retained catalog M21 is the same physical placement or that its default angle is calibrated |

### Source-to-code mapping
| source expression | code expression | transformation | exact/approximate | assumption | status |
|---|---|---|---|---|---|
| source Eq.6 diagonal | code line 455 diagonal | \(\theta=\phi_\zeta\) | exact | same computational order/sign | direct closed |
| conditional energy of \(|11\rangle\) | projector exponential | spectral exponential of rank-one projector | exact | other basis states phase-referenced away | derived closed |

### Operation replay / derivation
| input | transformation | assumption | output | source locator or derivation step | status |
|---|---|---|---|---|---|
| \(\Pi_{11}=\operatorname{diag}(0,0,0,1)\) | matrix exponential | projector eigenvalues 0,1 | code diagonal | direct spectral replay | exact |
| \(\Pi_{11}=(I-Z)\otimes(I-Z)/4\) | expand tensor product | \(n=(I-Z)/2\) | \(II-ZI-IZ+ZZ\) over 4 | hand derivation | exact |
| \(\theta=.4\) | compare against bare \(R_{ZZ}(\theta)\) | same basis | maximum difference \(0.1996668333\) | coordinator falsifier | proves not bare RZZ |

### Composite compatibility
| component | source | object/device/regime | composition bridge | compatible? | risk |
|---|---|---|---|---|---|
| cross-Kerr/conditional phase | SRC-PETTERSSON-ZZ-v2 | superconducting-qubit rotating frame | direct matrix | yes | higher levels folded into effective \(\zeta\) |
| retained M21 label | project catalog/adapter | compatibility mechanism | source object -> catalog ID | open | M8/M21 naming and placement must not be silently merged |

### Parameter/value provenance
| parameter | value/units | provenance kind | exact locator | transform | allowed claim | forbidden claim |
|---|---|---|---|---|---|---|
| \(\theta=\phi_\zeta\) | radians | direct form relation | source Eq.6 | time integral of \(\zeta\) | exact phase-to-unitary mapping | current hardware magnitude |
| adapter default | project value | outside sub-batch | caller line 385 | float cast | runtime reproducibility | source-calibrated M21 value |

### Assumptions and correct-place audit
- Assumptions: computational-subspace effective Hamiltonian; single-qubit rotating-frame phases removed.
- Simplifications and error bounds: no explicit \(|2\rangle\) dynamics or time ordering remains in the
  effective phase.
- Failure regime: leakage/transport during the gate, or a mechanism that intends traceless \(ZZ\) alone.
- Why this formula belongs here: it is a distinct runtime unitary and is not equivalent to bare RZZ.
- Schedule/instrument/record bridge: primitive-to-source bridge closed; source-to-M21 catalog placement open.
- Alternative formulation/invariant:
  \(e^{-i\theta/4}[R_Z(-\theta/2)\otimes R_Z(-\theta/2)]R_{ZZ}(\theta/2)\).
- Verdict: bridge-open

### Independent checks
| invariant/reference | independent route | falsifier | shared blind spot? | result |
|---|---|---|---|---|
| projector exponential | SciPy `expm(-i theta Pi11)` | wrong diagonal index/sign | no | zero maximum error |
| Pauli decomposition | independent RZ/RZZ construction | omitted local/global phases | no | \(2.29\times10^{-16}\) max error |
| canonical test | same diagonal reference | RZZ substitution | yes: reference repeats code form | sign/index pins pass, physical placement untested |

### Human verification
- [ ] formula transcription checked
- [ ] exact source page checked
- [ ] symbol/unit convention checked
- [ ] derivation replayed
- [ ] application location checked
- [ ] composite bridge accepted
- Human verdict: unchecked
- Notes: do not relabel this primitive as RZZ without retaining the local-\(Z\)/global-phase bridge.

## ECS-CHAN-004 — Three-point drifted-axis random-unitary mixture

### Formula and role
- Normalized valid-domain formula:
  $$K_j=\sqrt{w_j}\,U_a(\epsilon+\delta_j),\qquad
    \delta=(-s,0,s),\quad w_j\ge0,\quad\sum_jw_j=1,$$
  with project defaults \(w=(1/4,1/2,1/4)\) and \(s=|\text{effective span}|\).
- Literal code realization: clean/normalize three weights, then return three scaled axis unitaries.
- Role: channel | drift discretization | composite mechanism primitive
- Scientific object: a three-atom random-unitary approximation to an angle-drift distribution.
- Upstream inputs: ECS-CHAN-001, axis canonicalizer, mean angle, span, and optional weights.
- Downstream consumers: retained M13 branch.

### Code usage
| frozen file:line | qualname | service/call path | runtime/oracle/test | responsibility |
|---|---|---|---|---|
| `carrier/channels.py:458-490` | `_axis_unitary`; `drifted_axis_mixture_kraus` | channel_algebra -> M13 adapter | runtime | dispatch, three-point discretization, and input repair |
| `tests/test_carrier_channels_units.py:557-601` | `_drift_ref`; branch tests | canonical channel_algebra | test-reference | repeats offsets/default/normalization on ordinary inputs |

### Symbols, domains, and conventions
| symbol | meaning | shape/domain | units | basis/order | source symbol |
|---|---|---|---|---|---|
| \(a\) | canonical axis | rx, ry, or rz | none | project canonicalizer | \(Z\) in nearest source |
| \(\epsilon\) | mean angle | finite real | rad | ECS-CHAN-001 | random rotation angle mean |
| \(s\) | symmetric support half-span | finite nonnegative | rad | absolute value in code | no exact source symbol |
| \(w_j\) | mixture masses | three finite nonnegative numbers, positive sum | probability | offsets \(-s,0,+s\) | continuous density in nearest source |

### Evidence verdict
- provenance_status: `COMPOSITE-UNCLOSED`
- required visible risk marker: **高危无出处（组合公式整体无直接出处）**
- formula_correctness: incorrect
- application_fit: mismatched
- value_provenance: project-design
- epistemic_class: random-unitary Kraus algebra is derived, but the three-point law, default weights,
  repair policy, accepted domain, and physical drift bridge are not source-closed

### Exact literature sources
| source ID | publication/version | PDF/hash | exact locator | visually checked page | source says | source does not say |
|---|---|---|---|---|---|---|
| SRC-HANTZKO-PTM-v2 | Hantzko et al., arXiv:2411.00526v2 | `outputs/papers/2411.00526.pdf` / `dd0421cc45fcb0e95caf803ee568720aefec6319c9015f18f5c8e6f1ef812d0a` | printed p.3 Eq.12 | yes, previously checked | operator-sum channel form and TP completeness | three-point drift law or bad-input repair |
| SRC-PATAKI-QSTATIC-v3 | Pataki et al., arXiv:2401.04530v3; Phys. Rev. A 110, 012417 (2024) | `outputs/papers/2401.04530.pdf` / `b6d065c0ebc14d0c17347686aa49ae1333440178aa1b86aea54b917ca127e4ac` | printed/PDF p.3 Eqs.8--11 | yes, Gaussian density and averaging integral | quasistatic coherent angles are sampled from a continuous Gaussian in that model | no \((-s,0,s)\) quadrature or \(1/4,1/2,1/4\) weights |

### Source-to-code mapping
| source expression | code expression | transformation | exact/approximate | assumption | status |
|---|---|---|---|---|---|
| \(\mathcal E(\rho)=\sum K_j\rho K_j^\dagger\) | list \(\sqrt{w_j}U_j\) | choose random-unitary Kraus operators | exact | finite \(w_j\ge0,\sum w=1\) | derived closed |
| continuous \(f(\theta)\), \(\int f=1\) | three atoms at \(\epsilon-s,\epsilon,\epsilon+s\) | unstated quadrature/discretization | approximate | target distribution and moment order unspecified | open |
| invalid/missing weights | clip/drop/reset defaults | project repair | exact code behavior | invalid data may be silently replaced | contradicted as validation |

### Operation replay / derivation
| input | transformation | assumption | output | source locator or derivation step | status |
|---|---|---|---|---|---|
| valid normalized \(w_j\) and unitary \(U_j\) | sum \(K_j^\dagger K_j\) | finite nonnegative weights | \((\sum w_j)I=I\) | [ours-derived] from Hantzko Eq.12 | exact CPTP |
| weights \([-1,.5,.5]\) | negative clipped to zero and normalize | code policy | valid CPTP but altered distribution | coordinator replay | silent scientific mutation |
| weights \([\mathrm{NaN},1,1]\) | Python `max(0,nan)` returns 0 | code policy | first atom erased | coordinator replay | silent mutation |
| weights \([+\infty,1,1]\) | divide by infinite total | IEEE arithmetic | NaN Kraus/completeness | coordinator replay | invalid |
| span NaN / \(+\infty\) | absolute and offset construction | no finite guard | nonfinite Kraus / `ValueError` | coordinator replay | invalid |

### Composite compatibility
| component | source | object/device/regime | composition bridge | compatible? | risk |
|---|---|---|---|---|---|
| random-unitary Kraus form | SRC-HANTZKO-PTM-v2 | finite discrete channel | weights normalized | yes on restricted domain | no bad-input semantics |
| quasistatic angle distribution | SRC-PATAKI-QSTATIC-v3 | continuous Gaussian Z rotations | replace integral by three atoms | unproved | moments and temporal persistence can differ |
| M13 adapter | project mechanism | retained compatibility path | static three-point channel -> intended drift | open | no across-time latent-state persistence is represented here |

### Parameter/value provenance
| parameter | value/units | provenance kind | exact locator | transform | allowed claim | forbidden claim |
|---|---|---|---|---|---|---|
| offsets | \((-s,0,s)\), rad | project design | code line 486 | symmetric atoms | exact implementation description | literature-derived quadrature |
| default weights | \((.25,.5,.25)\) | project design | lines 477,479,483 | normalize | reproducible project choice | Gaussian approximation accuracy |
| invalid-weight policy | clip/drop/reset | project design | lines 478--485 | nonlinear repair | describe code behavior | valid scientific-domain enforcement |

### Assumptions and correct-place audit
- Assumptions: finite mean/span; exactly three finite nonnegative weights with positive total; each
  sample is an independent random-unitary channel use.
- Simplifications and error bounds: no quadrature order, moment match, distributional distance, or
  temporal-correlation error bound is supplied.
- Failure regime: negative, NaN, or infinite weights; nonfinite span/angle; any claim of quasistatic
  memory across multiple calls.
- Why this formula belongs here: it changes the runtime channel and defines the retained drift surrogate.
- Schedule/instrument/record bridge: public accepted-input domain is mismatched and the physical
  drift-to-three-atoms bridge is open.
- Alternative formulation/invariant: validate a frozen probability distribution and either integrate/sample
  it explicitly or state and verify a quadrature moment/error target.
- Verdict: mismatched

### Independent checks
| invariant/reference | independent route | falsifier | shared blind spot? | result |
|---|---|---|---|---|
| valid-domain TP | sum scaled unitary completeness by hand | \(\sum w\ne1\) | no | exact on restricted domain |
| nonfinite boundary | direct runtime table | finite-only output contract | no | inf/NaN failures reproduced |
| target distribution | compare with source Gaussian density | three atoms absent from source | no | composition remains open |
| canonical tests | same offsets/cleaning reference | alternative physical drift law | yes | ordinary branches pass; adversarial inputs absent |

### Human verification
- [ ] formula transcription checked
- [ ] exact source page checked
- [ ] symbol/unit convention checked
- [ ] derivation replayed
- [ ] application location checked
- [ ] composite bridge accepted
- Human verdict: unchecked
- Notes: **高危无出处（组合公式整体无直接出处）**; tests certify the chosen three-point code path,
  not its physical fidelity.

## ECS-CHAN-005 — Arbitrary-axis rotation with a numerical norm floor

### Formula and role
- Intended normalized-axis formula:
  $$U(\theta,\vec c)=
    \cos(\theta/2)I-i\sin(\theta/2)
    \frac{\sum_{j\in\{X,Y,Z\}}c_j\sigma_j}{\sqrt{\sum_jc_j^2}}.$$
- Literal code realization replaces the denominator by
  \(\sqrt{\max(\sum_{\text{mapping entries}}c_j^2,10^{-12})}\) while uppercasing labels only
  when adding matrices.
- Role: unitary | arbitrary-axis coherent-mechanism primitive
- Scientific object: rotation around a real unit Bloch-sphere axis.
- Upstream inputs: arbitrary public `Mapping[str,float]`, Pauli dictionary, and shared numerical floor.
- Downstream consumers: retained M27 branch with ordinary \(\{X:1,Z:1\}\) input.

### Code usage
| frozen file:line | qualname | service/call path | runtime/oracle/test | responsibility |
|---|---|---|---|---|
| `carrier/channels.py:493-503` | `single_axis_rotation` | channel_algebra -> M27 adapter | runtime | build and normalize the generator, then use a closed-form rotation |
| `tests/test_carrier_channels_units.py:377-394` | ordinary-axis pins | canonical channel_algebra | test-reference | repeats the same norm-floor formula on valid examples |

### Symbols, domains, and conventions
| symbol | meaning | shape/domain | units | basis/order | source symbol |
|---|---|---|---|---|---|
| \(\vec c\) | real Pauli-axis coefficients | intended distinct X/Y/Z keys and nonzero norm | dimensionless | mapping insertion may alias after uppercase | unit vector \(\vec v\) |
| \(r^2\) | intended squared axis norm | \(\sum c_j^2\) | dimensionless | code counts mapping entries, not combined matrices | \(\|\vec v\|^2=1\) |
| \(\epsilon_{\rm num}\) | denominator floor | \(10^{-12}\) | coefficient squared | shared project constant | none |

### Evidence verdict
- provenance_status: `CONTRADICTED/MISAPPLIED`
- required visible risk marker: source/code contradiction on the accepted public domain
- formula_correctness: incorrect
- application_fit: mismatched
- value_provenance: project-design
- epistemic_class: primary sources require a unit rotation axis; code accepts and silently transforms
  inputs for which its generator is not an involution and the output is not unitary

### Exact literature sources
| source ID | publication/version | PDF/hash | exact locator | visually checked page | source says | source does not say |
|---|---|---|---|---|---|---|
| SRC-CLADER-ROT-v2 | Clader et al., arXiv:2101.11631v2; Phys. Rev. A 103, 052428 (2021) | `outputs/papers/2101.11631.pdf` / `406484c2c0cb1d9450c45df793d8a57763ea488a1c8767a6d851bb99d521c521` | printed/PDF p.2 Eq.1 and following sentence | yes | closed form for an arbitrary **unit** real three-vector axis | zero/tiny axes, identity components, duplicate aliases, or a floor |
| SRC-SHELDON-RB-v1 | Sheldon et al., arXiv:1504.06597v1 | `outputs/papers/1504.06597.pdf` / `609232d9fc4f3066aec0bc520174e88107ed4444e70dcfec3e05e164f589f7c9` | printed/PDF p.2 Eq.1 | yes | exponential about an axis of rotation | project input-cleaning policy |

### Source-to-code mapping
| source expression | code expression | transformation | exact/approximate | assumption | status |
|---|---|---|---|---|---|
| unit \(\vec v\cdot\vec\sigma\) | `operator / sqrt(max(norm_sq,1e-12))` | normalize mapping coefficients | exact only on restricted domain | distinct XYZ keys, finite real coefficients, norm at least \(10^{-6}\) | conditional |
| \((\vec v\cdot\vec\sigma)^2=I\) | cos/sin closed form | assume normalized traceless Pauli vector | exact only if premise holds | no I and no uppercase collisions | contradicted on accepted inputs |

### Operation replay / derivation
| input | transformation | assumption | output | source locator or derivation step | status |
|---|---|---|---|---|---|
| distinct XYZ, \(r\ge10^{-6}\) | divide by \(r\) | Pauli anticommutators cancel cross terms | \(G^2=I\), unitary \(U\) | source + hand algebra | correct subdomain |
| empty mapping, \(\theta=.7\) | \(G=0\) | floor hides zero norm | \(U^\dagger U-I\) max \(0.1175789064\) | coordinator replay | counterexample |
| \(\{X:10^{-7}\}\) | denominator fixed at \(10^{-6}\) | below floor | max unitarity error \(0.1164031173\) | coordinator replay | counterexample |
| \(\{X:1,x:1\}\) | operator becomes \(2X\), norm remains \(\sqrt2\) | aliases counted separately | max error \(0.1175789064\) | reviewer/coordinator replay | counterexample |
| \(\{I:1,X:1\}\) | normalized generator contains identity | accepted dictionary key | max error \(0.1175789064\) | reviewer/coordinator replay | counterexample |

### Composite compatibility
| component | source | object/device/regime | composition bridge | compatible? | risk |
|---|---|---|---|---|---|
| unit-axis rotation | SRC-CLADER-ROT-v2 | real Bloch vector | project mapping normalization | yes only on restricted domain | public signature does not enforce it |
| shared floor | ECS-NUM-001 | generic numerical convention | inserted into physical generator norm | no below threshold | changes the channel from unitary to trace-decreasing |
| retained M27 caller | project adapter | \(\{X:1,Z:1\}\) | valid restricted input | yes for that call | public primitive remains unsafe |

### Parameter/value provenance
| parameter | value/units | provenance kind | exact locator | transform | allowed claim | forbidden claim |
|---|---|---|---|---|---|---|
| norm floor | \(10^{-12}\) under square root | project design | code line 501 | creates \(10^{-6}\) critical norm | exact code threshold | physically meaningful axis regularizer |
| M27 components | \(X=1,Z=1\) | project mechanism choice | caller line 397 | normalize to \((X+Z)/\sqrt2\) | valid current-call unitary | validation of arbitrary mappings |

### Assumptions and correct-place audit
- Assumptions: distinct X/Y/Z labels, no identity label, finite real coefficients, norm at least \(10^{-6}\).
- Simplifications and error bounds: the floor has no unitary-error bound and is not a harmless roundoff fix.
- Failure regime: zero/tiny axes, duplicate case aliases, I components, nonfinite values, or unknown labels.
- Why this formula belongs here: it directly constructs the M27 unitary and exposes a public channel primitive.
- Schedule/instrument/record bridge: current M27 input lies in the valid subdomain, but the public accepted
  domain and scientific name are mismatched.
- Alternative formulation/invariant: combine canonicalized XYZ coefficients first, reject nonfinite/zero
  norm and I, then assert \(G^\dagger=G,G^2=I\).
- Verdict: mismatched

### Independent checks
| invariant/reference | independent route | falsifier | shared blind spot? | result |
|---|---|---|---|---|
| unit-axis requirement | source definition plus Pauli anticommutator algebra | \(G^2\ne I\) | no | accepted counterexamples fail |
| unitarity | direct \(U^\dagger U-I\) norm | error nonzero | no | up to \(0.1175789064\) |
| canonical test | same floor/reference helper | zero/tiny/alias/I input | yes | only valid examples pass |
| current M27 call | independent exponential of \((X+Z)/\sqrt2\) | mismatch | no | valid subdomain |

### Human verification
- [ ] formula transcription checked
- [ ] exact source page checked
- [ ] symbol/unit convention checked
- [ ] derivation replayed
- [ ] application location checked
- [ ] composite bridge accepted
- Human verdict: unchecked
- Notes: implementation was not changed; counterexamples are recorded for owner adjudication.

## ECS-CHAN-006 — Floored stochastic-Pauli Kraus channel

### Formula and role
- Standard formula:
  $$\mathcal E(\rho)=p_I\rho+p_XX\rho X+p_YY\rho Y+p_ZZ\rho Z,\qquad
    p_I=1-p_X-p_Y-p_Z,$$
  represented by \(K_P=\sqrt{p_P}P\) for finite \(p_P\ge0\) and \(\sum_Pp_P=1\).
- Literal code realization floors/caps every supplied or missing X/Y/Z coordinate at \(10^{-12}\),
  computes their sum, and floors the identity remainder again.
- Role: channel | stochastic-Pauli mechanism primitive
- Scientific object: one-qubit classical mixture over \(I,X,Y,Z\).
- Upstream inputs: probability mapping, ECS-NUM-002/003, and Pauli matrices.
- Downstream consumers: retained M0, M5, M25, and M26 branches.

### Code usage
| frozen file:line | qualname | service/call path | runtime/oracle/test | responsibility |
|---|---|---|---|---|
| `carrier/channels.py:506-519` | `pauli_stochastic_kraus` | channel_algebra -> retained mechanisms | runtime | map probability coordinates into four Kraus operators |
| `tests/test_carrier_channels_units.py:244-250,519-551` | `_pauli_stoch`; pins | canonical channel_algebra | test-reference | repeats the same floors and accepts \(10^{-12}\)-scale TP defects |

### Symbols, domains, and conventions
| symbol | meaning | shape/domain | units | basis/order | source symbol |
|---|---|---|---|---|---|
| \(p_P\) | mixture probability for Pauli \(P\) | finite \([0,1]\) with total one | probability | I,X,Y,Z | implicit Kraus weights |
| \(\tilde p_P\) | code-transformed probability | \(\min(1,\max(10^{-12},p_P))\) | probability | absent keys also floored | none |
| \(K_P\) | scaled Pauli Kraus operator | \(2\times2\) | \(\sqrt{\text{probability}}\) | computational basis | \(K_i\) |

### Evidence verdict
- provenance_status: `CONTRADICTED/MISAPPLIED`
- required visible risk marker: standard channel/source assumptions conflict with the implemented boundary map
- formula_correctness: incorrect
- application_fit: mismatched
- value_provenance: project-design
- epistemic_class: the ideal Kraus form is replayable from a direct source, but structural zeros and
  invalid values are rewritten into physical mass and exact TP fails near the boundary

### Exact literature sources
| source ID | publication/version | PDF/hash | exact locator | visually checked page | source says | source does not say |
|---|---|---|---|---|---|---|
| SRC-HANTZKO-PTM-v2 | Hantzko et al., arXiv:2411.00526v2 | `outputs/papers/2411.00526.pdf` / `dd0421cc45fcb0e95caf803ee568720aefec6319c9015f18f5c8e6f1ef812d0a` | printed p.3 Eqs.2--3,12 | yes, previously checked | Pauli matrices, operator-sum form, and TP completeness | a nonzero probability floor or invalid-input repair |
| SRC-PATAKI-QSTATIC-v3 | Pataki et al., arXiv:2401.04530v3; Phys. Rev. A 110, 012417 (2024) | `outputs/papers/2401.04530.pdf` / `b6d065c0ebc14d0c17347686aa49ae1333440178aa1b86aea54b917ca127e4ac` | printed/PDF p.3 Eq.5 | yes, same page as Gaussian check | an explicit Pauli error channel with genuine zero/derived probabilities | replacement of absent Pauli events by \(10^{-12}\) mass |

### Source-to-code mapping
| source expression | code expression | transformation | exact/approximate | assumption | status |
|---|---|---|---|---|---|
| \(K_P=\sqrt{p_P}P\) | four scaled Pauli arrays | direct Kraus realization | exact | unchanged valid probabilities and total one | ideal form closed |
| \(\sum K_P^\dagger K_P=I\) | floored error sum plus floored identity | apply coordinate-wise floors twice | not exact at boundary | remainder exceeds floor | contradicted |
| \(p_P=0\) | \(\tilde p_P=10^{-12}\) | physical-probability repair | approximate without bound | structural zeros dispensable | contradicted |

### Operation replay / derivation
| input | transformation | assumption | output | source locator or derivation step | status |
|---|---|---|---|---|---|
| valid \(p_P\) | sum \(K_P^\dagger K_P\) | probabilities total one | \(I\) | [ours-derived] from Hantzko Eq.12 | exact ideal |
| \((.4,.4,.2)\) | identity remainder floored | exact error sum one | completeness \(1.000000000001I\) | coordinator replay | non-TP |
| \(p_X=.5,p_Y=.5,p_Z\) absent | floor missing Z and identity | sum guard tolerance | \(1.0000000000020002I\) | coordinator replay | non-TP |
| \(p_X=1\), Y/Z absent | floor missing coordinates | guard threshold | `ValueError` | coordinator replay | pure X unrepresentable |
| negative, NaN, or \(-\infty\) X | probability floor | Python min/max order | silently becomes \(10^{-12}\) | coordinator replay | wrong channel |
| empty mapping | floor all errors | no requested error | nonidentity stochastic channel | direct replay | structural-zero violation |

### Composite compatibility
| component | source | object/device/regime | composition bridge | compatible? | risk |
|---|---|---|---|---|---|
| ideal Pauli mixture | SRC-HANTZKO-PTM-v2 / SRC-PATAKI-QSTATIC-v3 | finite probability simplex | Kraus scaling | yes | exact zeros allowed |
| probability floor | ECS-NUM-003 | generic project numerical map | insert into physical simplex coordinates | no | changes mechanism-off and pure-axis controls |
| TP assertion | canonical test helper | tolerance \(10^{-9}\) | compare \(10^{-12}\)-scale residual | masks defect | passing test is not exact CPTP evidence |

### Parameter/value provenance
| parameter | value/units | provenance kind | exact locator | transform | allowed claim | forbidden claim |
|---|---|---|---|---|---|---|
| probability floor | \(10^{-12}\) | project design | lines 511,516 via ECS-NUM-003 | clamp/cap | exact code behavior | sourced physical rare-event mass |
| sum slack | \(10^{-12}\) | project design | line 512 | permits slight excess before error | implementation guard | exact simplex enforcement |
| canonical TP tolerance | \(10^{-9}\) | test design | faithfulness helper/canonical test | residual threshold | regression acceptance | proof of exact TP |

### Assumptions and correct-place audit
- Assumptions: standard probabilities are finite/nonnegative and structural zeros may be replaced by
  rare events without affecting any scientific claim.
- Simplifications and error bounds: no total-variation, logical-error, rare-event, or mechanism-off
  propagation bound is provided.
- Failure regime: exact identity or pure-axis channels, sums near one, negative/nonfinite inputs, and
  any zero-sensitive control or certification.
- Why this formula belongs here: it constructs four retained physical mechanism channels.
- Schedule/instrument/record bridge: mismatched at the primitive boundary and propagates to all callers.
- Alternative formulation/invariant: validate the closed simplex without flooring physical coordinates;
  omit exactly zero Kraus terms and enforce \(\sum K^\dagger K=I\) at an explicit numerical tolerance.
- Verdict: mismatched

### Independent checks
| invariant/reference | independent route | falsifier | shared blind spot? | result |
|---|---|---|---|---|
| exact TP | analytic scalar sum of squared Kraus coefficients | scalar not one | no | boundary excess \(10^{-12}\)--\(2\times10^{-12}\) |
| pure-axis representability | call with \(p_X=1\) | exception or added Y/Z | no | `ValueError` |
| invalid domain | direct negative/NaN/inf table | silent repair | no | negative/NaN/\(-\infty\) become floor |
| canonical tests | helper repeats project floors; TP tol \(10^{-9}\) | exact-zero/boundary defect | yes | 71-test batch passes while defects persist |

### Human verification
- [ ] formula transcription checked
- [ ] exact source page checked
- [ ] symbol/unit convention checked
- [ ] derivation replayed
- [ ] application location checked
- [ ] composite bridge accepted
- Human verdict: unchecked
- Notes: implementation and tests remain unchanged; this row records the contradiction rather than
  silently normalizing it away.

<!-- BATCH-1B2A1-ROWS-END -->

## ECS-CHAN-AD-001 — Floored one-qubit amplitude damping

### Formula and role
- Source-level channel:
  $$K_0=|0\rangle\!\langle0|+\sqrt{1-g}|1\rangle\!\langle1|,\qquad
    K_1=\sqrt g|0\rangle\!\langle1|,$$
  $$\rho_{11}\mapsto(1-g)\rho_{11},\quad
    \rho_{00}\mapsto\rho_{00}+g\rho_{11},\quad
    \rho_{01}\mapsto\sqrt{1-g}\rho_{01}.$$
- Literal code realization first replaces the public input by
  (g=f(\gamma)=\min(1,\max(10^{-12},\gamma))), including the ECS-NUM-003 invalid-input behavior.
- Role: channel | one-qubit relaxation primitive
- Scientific object: zero-temperature downward amplitude damping in basis ((|0\rangle,|1\rangle)).
- Upstream inputs: public `gamma`, probability floor, computational-basis convention.
- Downstream consumers: legacy M4 adapter and the thermal, leakage-surrogate, and custom composites.

### Code usage
| frozen file:line | qualname | service/call path | runtime/oracle/test | responsibility |
|---|---|---|---|---|
| `carrier/channels.py:522-527` | `amplitude_damping_kraus` | channel_algebra -> M4/internal composites | runtime | floor `gamma` and construct two Kraus matrices |
| `carrier/channels.py:331-332,575,603,728` | M4/thermal/leakage/custom callers | compatibility/internal | runtime | reuse the primitive under different scientific labels |
| `tests/test_carrier_channels_units.py:400-410` | amplitude-damping pins | canonical channel_algebra | test-reference | mirrors the floored construction and uses tolerant CPTP check |
| `tests/test_noise_mechanism_primitives.py:43` | assembled reference | canonical channel_algebra | test-reference | consumes the same installed builder, not an independent operator source |

### Symbols, domains, and conventions
| symbol | meaning | shape/domain | units | basis/order | source symbol |
|---|---|---|---|---|---|
| \(\gamma\) | public damping probability | intended finite \([0,1]\) | probability | \(|0\rangle,|1\rangle\) | \(\lambda(t)\) |
| \(g\) | code-transformed probability | \([10^{-12},1]\) after repair | probability | same | \(\lambda(t)\) only when unchanged |
| \(K_0,K_1\) | downward-relaxation Kraus matrices | (2\times2) | dimensionless | row=output, column=input | \(\tilde E_0,\tilde E_1\) |

### Evidence verdict
- provenance_status: `CONTRADICTED/MISAPPLIED`
- required visible risk marker: direct core formula conflicts with the implemented public-input map
- formula_correctness: incorrect
- application_fit: mismatched
- value_provenance: project-design
- epistemic_class: the post-transform Kraus core is paper-direct; the full public
  \(\gamma\mapsto\mathcal E\) map is contradicted at mechanism-off and invalid inputs.

### Exact literature sources
| source ID | publication/version | PDF/hash | exact locator | visually checked page | source says | source does not say |
|---|---|---|---|---|---|---|
| SRC-ARSENIJEVIC-ADPD-v1 | Arsenijević & Banković, *Microscopic derivation of the one qubit Kraus operators for amplitude and phase damping*, arXiv:1606.01145v1; Kragujevac J. Sci. 38, 41-52 (2016) | `outputs/papers/1606.01145.pdf`; `32e3d12077bef0b1e6eb84f2f85f5bc35fc1fce6b5f9a3e58c625cf902ee0694` | PDF/printed p.4, Sec.3, Eqs.13-14 | yes, coordinator | zero-temperature AD master equation and exactly these Kraus operators | probability floor, invalid-input repair, or a nonidentity channel at \(\gamma=0\) |

### Source-to-code mapping
| source expression | code expression | transformation | exact/approximate | assumption | status |
|---|---|---|---|---|---|
| \(\lambda(t)\) | `g` | identify damping probability | exact on unchanged finite input | \(0\le\gamma\le1\) | direct core |
| Eq.14 matrices | two returned arrays | basis transcription | exact after transformed `g` | computational basis | direct core |
| \(\lambda(0)=0\) | `probability_floor(0)=1e-12` | insert physical mass | not source-supported | zero means mechanism off | contradicted |

### Operation replay / derivation
| input | transformation | assumption | output | source locator or derivation step | status |
|---|---|---|---|---|---|
| valid transformed \(g\) | \(\sum_i K_i^\dagger K_i\) | finite \([0,1]\) | \(I_2\) to roundoff | Eq.14 hand algebra | correct core |
| public `gamma=0`, \(|1\rangle\langle1|\) | \(g=10^{-12}\) | none | \(10^{-12}|0\rangle\langle0|+(1-10^{-12})|1\rangle\langle1|\) | coordinator runtime replay | counterexample |
| negative/NaN/\(-\infty\) | ECS-NUM-003 | invalid values silently repaired | same live (10^{-12}) damping | direct edge replay | contradicted |

### Composite compatibility
| component | source | object/device/regime | composition bridge | compatible? | risk |
|---|---|---|---|---|---|
| ideal AD core | SRC-ARSENIJEVIC-ADPD-v1 | zero-temperature Markovian qubit relaxation | direct Kraus transcription | yes | input parameter must already be physical |
| probability floor | ECS-NUM-003 | project numerical convention | prepended to physical probability | no at zero/invalid inputs | mechanism-off control is destroyed |
| thermal/custom/leakage callers | later rows | distinct composites | reuse of this primitive | conditional | caller semantics are not inherited from the AD source |

### Parameter/value provenance
| parameter | value/units | provenance kind | exact locator | transform | allowed claim | forbidden claim |
|---|---|---|---|---|---|---|
| floor | (10^{-12}) probability | project design | line 523 via ECS-NUM-003 | clamp/cap | exact implementation behavior | physical residual relaxation rate |
| M4 default | `gamma=0.015` | project design | adapter line 332 | none beyond floor | reproducible legacy profile | device-calibrated relaxation probability |

### Assumptions and correct-place audit
- Assumptions: finite physical damping probability and a zero-temperature two-level decay object.
- Simplifications and error bounds: no bound propagates the inserted (10^{-12}) mass to any metric.
- Failure regime: exact mechanism-off, negative/nonfinite inputs, or finite-temperature bidirectional relaxation.
- Why this formula belongs here: it is a public CORE-service primitive and feeds four installed paths.
- Schedule/instrument/record bridge: its interior object matches AD, but the accepted public domain does not.
- Alternative formulation/invariant: validate a closed probability interval, preserve exact zero, and reject nonfinite values.
- Verdict: mismatched

### Independent checks
| invariant/reference | independent route | falsifier | shared blind spot? | result |
|---|---|---|---|---|
| Eq.14 action | hand matrix multiplication | wrong transition direction | no | core matrices match |
| mechanism-off identity | apply to \(|1\rangle\) at input zero | nonzero ground population | no | (10^{-12}) false relaxation reproduced |
| canonical tests | inspect helper/caller independence | same probability floor | yes | tests pass while zero semantics fail |

### Human verification
- [ ] formula transcription checked
- [ ] exact source page checked
- [ ] symbol/unit convention checked
- [ ] derivation replayed
- [ ] application location checked
- [ ] composite bridge accepted
- Human verdict: unchecked
- Notes: no implementation change was made; ideal AD is retained as a direct subdomain result only.

## ECS-CHAN-PD-001 — Floored stochastic-Z dephasing

### Formula and role
- Source-level stochastic-Z channel:
  $$\mathcal E_g(\rho)=(1-g)\rho+gZ\rho Z,\qquad
    (x,y,z)\mapsto((1-2g)x,(1-2g)y,z).$$
- Literal code returns
  ({\sqrt{\max(10^{-12},1-g)}I,\sqrt gZ\}) after (g=f(\gamma_\phi)).
- Role: channel | stochastic phase-flip primitive
- Scientific object: a Pauli-Z error-probability channel, not the canonical phase-damping parameterization.
- Upstream inputs: public `gamma_phi`, ECS-NUM-002/003, I/Z matrices.
- Downstream consumers: only the legacy two-level leakage surrogate; M5 uses a different builder.

### Code usage
| frozen file:line | qualname | service/call path | runtime/oracle/test | responsibility |
|---|---|---|---|---|
| `carrier/channels.py:530-546` | `phase_damping_kraus` | channel_algebra -> leakage surrogate | runtime | build stochastic-Z Kraus terms with two floors |
| `carrier/channels.py:601-603` | `leakage_relaxation_surrogate_kraus` | compatibility M34 | runtime | compose this channel with AD |
| `tests/test_carrier_channels_units.py:413-423` | phase-damping pins | canonical channel_algebra | test-reference | mirrors floor and accepts (10^{-12})-scale TP excess |

### Symbols, domains, and conventions
| symbol | meaning | shape/domain | units | basis/order | source symbol |
|---|---|---|---|---|---|
| \(\gamma_\phi\) | public Z-flip probability | intended finite \([0,1]\) | probability | computational basis | (p(t)/2) |
| \(g\) | repaired code probability | \([10^{-12},1]\) | probability | same | (p(t)/2) on source range |
| (p(t)) | source PD parameter | (1-e^{-2rt}\in[0,1]) | dimensionless | I/Z Kraus gauge | (p(t)) |

### Evidence verdict
- provenance_status: `CONTRADICTED/MISAPPLIED`
- required visible risk marker: source dynamical domain and TP completeness conflict with accepted code inputs
- formula_correctness: incorrect
- application_fit: mismatched
- value_provenance: project-design
- epistemic_class: direct only for the unchanged mapping (g=p(t)/2\in[0,1/2]); the full callable exceeds
  that physical phase-damping regime and fails exact TP at its accepted endpoint.

### Exact literature sources
| source ID | publication/version | PDF/hash | exact locator | visually checked page | source says | source does not say |
|---|---|---|---|---|---|---|
| SRC-ARSENIJEVIC-ADPD-v1 | Arsenijević & Banković, arXiv:1606.01145v1 (2016) | local PDF/hash above | PDF/printed p.13, Eqs.53-57, especially Eq.55 | yes, coordinator | \((\sqrt{1-p/2}I,\sqrt{p/2}Z)\), completeness, and \(e^{-2rt}\) X/Y contraction | \(g>1/2\), coherence-sign reversal, or a positive floor on the zero remainder |

### Source-to-code mapping
| source expression | code expression | transformation | exact/approximate | assumption | status |
|---|---|---|---|---|---|
| (p(t)/2) | `g` | set (g=p/2) | exact | source Markovian (t,r\ge0) | direct on (g\le1/2) |
| (e^{-2rt}) | `1-2*g` | substitute (p=1-e^{-2rt}) | exact | (g\le1/2) | direct |
| zero identity coefficient at (g=1) | `positive_floor(1-g)` | force (10^{-12}) | not source-supported | endpoint allowed by code | contradicted |

### Operation replay / derivation
| input | transformation | assumption | output | source locator or derivation step | status |
|---|---|---|---|---|---|
| (0\le g\le1/2) | Pauli conjugation | normalized coefficients | X/Y factor (1-2g\ge0) | Eqs.55-57 | matched core |
| (g>1/2) | same channel | none | negative X/Y factor; valid Pauli channel but not source positive-time PD without an extra Z | hand Bloch replay | application mismatch |
| public `gamma_phi=1` | floor zero identity remainder | none | \(\sum_i K_i^\dagger K_i=(1+10^{-12})I\), Frobenius residual \(1.4143393\times10^{-12}\) | coordinator runtime replay | non-TP |

### Composite compatibility
| component | source | object/device/regime | composition bridge | compatible? | risk |
|---|---|---|---|---|---|
| stochastic-Z PD | SRC-ARSENIJEVIC-ADPD-v1 | Markovian phase damping | (g=p/2) | yes only through (1/2) | code domain doubles source range |
| positive/probability floors | ECS-NUM-002/003 | numerical convention | physical Kraus weights | no at zero/one | creates trace excess and false events |
| leakage surrogate | ECS-CHAN-LEAKSUR-001 | qubit AD-after-Z composite | same `p` for two processes | no sourced bridge | cannot inherit a leakage interpretation |

### Parameter/value provenance
| parameter | value/units | provenance kind | exact locator | transform | allowed claim | forbidden claim |
|---|---|---|---|---|---|---|
| probability floor | (10^{-12}) | project design | lines 541,544 | clamp then remainder floor | implementation behavior | sourced dephasing mass |
| source rate bridge | (g=(1-e^{-2rt})/2) | direct | Eq.55 and text | analytic substitution | source-regime mapping | code values above (1/2) as positive-time PD |

### Assumptions and correct-place audit
- Assumptions: finite Z-error probability; a phase-damping interpretation additionally requires (g\le1/2).
- Simplifications and error bounds: no bound covers sign reversal or trace excess.
- Failure regime: mechanism-off, \(g=1\), invalid/nonfinite inputs, or use as canonical \(\lambda\).
- Why this formula belongs here: it is installed and consumed by the M34 compatibility path.
- Schedule/instrument/record bridge: the sole runtime use is an unsourced leakage-labeled composite.
- Alternative formulation/invariant: expose the convention in the type/name, validate the intended interval, and preserve exact zero coefficients.
- Verdict: mismatched

### Independent checks
| invariant/reference | independent route | falsifier | shared blind spot? | result |
|---|---|---|---|---|
| Bloch contraction | direct (Z\rho Z) algebra | wrong sign/factor | no | (1-2g) confirmed |
| exact TP | scalar Kraus completeness | endpoint excess | no | (1+10^{-12}) at (g=1) |
| canonical test | inspect (10^{-9}) CPTP tolerance | exact endpoint assertion | yes | defect is masked |

### Human verification
- [ ] formula transcription checked
- [ ] exact source page checked
- [ ] symbol/unit convention checked
- [ ] derivation replayed
- [ ] application location checked
- [ ] composite bridge accepted
- Human verdict: unchecked
- Notes: the valid stochastic-Z channel for (g>1/2) is not mislabeled as a positive-time pure-dephasing semigroup.

## ECS-CHAN-PD-002 — Floored canonical phase-damping gauge

### Formula and role
- Intended canonical gauge:
  $$K_0=\operatorname{diag}(1,\sqrt{1-\lambda}),\qquad
    K_1=\operatorname{diag}(0,\sqrt\lambda),$$
  which fixes populations and maps (\rho_{01}\mapsto\sqrt{1-\lambda}\rho_{01}).
- Literal code applies (\lambda\mapsto f(\lambda)) and then floors (1-\lambda) again.
- Role: channel | canonical phase-damping primitive
- Scientific object: population-preserving qubit decoherence in the computational basis.
- Upstream inputs: public `lam`, ECS-NUM-002/003.
- Downstream consumers: only `thermal_relaxation_kraus` plus canonical tests.

### Code usage
| frozen file:line | qualname | service/call path | runtime/oracle/test | responsibility |
|---|---|---|---|---|
| `carrier/channels.py:549-557` | `phase_damping_canonical_kraus` | channel_algebra -> thermal | runtime | build the two diagonal Kraus matrices |
| `carrier/channels.py:575-577` | `thermal_relaxation_kraus` | public internal composite | runtime | apply PD after AD |
| `tests/test_carrier_channels_units.py:413-423` | phase-damping pins | canonical channel_algebra | test-reference | reuses the same floor and tolerant TP threshold |

### Symbols, domains, and conventions
| symbol | meaning | shape/domain | units | basis/order | source symbol |
|---|---|---|---|---|---|
| \(\lambda\) | canonical loss-of-coherence parameter | intended finite \([0,1]\) | dimensionless | \((|0\rangle,|1\rangle)\) | derived from \(e^{-2rt}\) |
| (r,t) | source dephasing rate/time | nonnegative | inverse-time/time | source PD model | (r,t) |
| (K_0,K_1) | diagonal Kraus gauge | (2\times2) | dimensionless | computational basis | gauge-equivalent to Eqs.53-54 |

### Evidence verdict
- provenance_status: `CONTRADICTED/MISAPPLIED`
- required visible risk marker: derived ideal gauge conflicts with literal endpoint and zero-input behavior
- formula_correctness: incorrect
- application_fit: mismatched
- value_provenance: project-design
- epistemic_class: `[ours-derived]` ideal gauge from a paper-direct channel action; literal accepted boundaries are contradicted.

### Exact literature sources
| source ID | publication/version | PDF/hash | exact locator | visually checked page | source says | source does not say |
|---|---|---|---|---|---|---|
| SRC-ARSENIJEVIC-ADPD-v1 | Arsenijević & Banković, arXiv:1606.01145v1 | local PDF/hash above | PDF/printed p.13, Eqs.53-57 | yes, coordinator | a gauge-equivalent PD Kraus set and coherence factor (e^{-2rt}) | this exact diagonal gauge, probability floors, or residual coherence at complete dephasing |

### Source-to-code mapping
| source expression | code expression | transformation | exact/approximate | assumption | status |
|---|---|---|---|---|---|
| (\rho_{01}\mapsto e^{-2rt}\rho_{01}) | (\rho_{01}\mapsto\sqrt{1-\lambda}\rho_{01}) | set (\lambda=1-e^{-4rt}) | exact channel equivalence | (r,t\ge0) | derived core |
| Eqs.53-54 Kraus gauge | two code matrices | unitary Kraus-gauge change | exact at channel level | exact arithmetic | `[ours-derived]` |
| \(\lambda=1\Rightarrow\rho_{01}'=0\) | `sqrt(positive_floor(0))` | insert \(10^{-6}\) amplitude | not source-supported | endpoint accepted | contradicted |

### Operation replay / derivation
| input | transformation | assumption | output | source locator or derivation step | status |
|---|---|---|---|---|---|
| interior \(0<\lambda<1\) | diagonal completeness sum | finite physical input | \(I_2\) and factor \(\sqrt{1-\lambda}\) | hand derivation from Eqs.53-57 | correct core |
| \(\lambda=1\), \(\rho_{01}=1/2\) | floor zero remainder | none | residual coherence \(5\times10^{-7}\) | coordinator runtime replay | counterexample |
| \(\lambda=1\) | \(\sum_i K_i^\dagger K_i\) | none | `diag(1,1+1e-12)`, residual \(1.0000889\times10^{-12}\) | coordinator runtime replay | non-TP |

### Composite compatibility
| component | source | object/device/regime | composition bridge | compatible? | risk |
|---|---|---|---|---|---|
| ideal PD action | SRC-ARSENIJEVIC-ADPD-v1 | Markovian qubit dephasing | gauge conversion | yes | conversion is derived, not direct matrix transcription |
| probability/remainder floors | ECS-NUM-002/003 | project numerical convention | inserted into Kraus weights | no at endpoints | false coherence and trace excess |
| thermal composition | ECS-CHAN-THERM-001 | low-temperature exponential T1/T2 | PD after AD | conditional | invalid time/domain behavior propagates |

### Parameter/value provenance
| parameter | value/units | provenance kind | exact locator | transform | allowed claim | forbidden claim |
|---|---|---|---|---|---|---|
| floor | (10^{-12}) probability / (10^{-6}) amplitude | project design | lines 553,555 | two-stage floor | exact code threshold | physical coherence floor |
| thermal \(\lambda_\phi\) | \(1-e^{-2t/T_\phi}\) | derived in THERM-001 | caller line 574 | rate-to-channel map | restricted exponential regime | arbitrary T2 noise |

### Assumptions and correct-place audit
- Assumptions: finite \(\lambda\in[0,1]\), exact Kraus-gauge equivalence, and no numerical repair of structural zeros.
- Simplifications and error bounds: no error bound licenses \(10^{-6}\) residual coherence at \(\lambda=1\).
- Failure regime: both physical endpoints and invalid/nonfinite public inputs.
- Why this formula belongs here: it determines the pure-dephasing half of the public thermal builder.
- Schedule/instrument/record bridge: the mathematical interior is matched; the callable contract is not.
- Alternative formulation/invariant: validate finite ([0,1]), use exact `max(0,1-lam)` only for proven roundoff, and assert endpoint action.
- Verdict: mismatched

### Independent checks
| invariant/reference | independent route | falsifier | shared blind spot? | result |
|---|---|---|---|---|
| gauge-equivalent action | act on four matrix units | population/coherence mismatch | no | ideal interior relation confirmed |
| complete-dephasing endpoint | apply to \(|+\rangle\langle+|\) | nonzero off-diagonal | no | (5\times10^{-7}) remains |
| canonical tests | compare helper formula and tolerance | exact endpoint oracle | yes | mirrored defect passes |

### Human verification
- [ ] formula transcription checked
- [ ] exact source page checked
- [ ] symbol/unit convention checked
- [ ] derivation replayed
- [ ] application location checked
- [ ] composite bridge accepted
- Human verdict: unchecked
- Notes: the source supports the channel action, not the literal code gauge plus floors.

## ECS-CHAN-THERM-001 — Floored zero-temperature exponential T1/T2 channel

### Formula and role
- Intended restricted-domain construction:
  $$\gamma=1-e^{-t/T_1},\qquad
    T_\phi^{-1}=T_2^{-1}-(2T_1)^{-1},\qquad
    \lambda_\phi=1-e^{-2t/T_\phi},$$
  $$\mathcal E=\mathrm{PD}_{\lambda_\phi}\circ\mathrm{AD}_{\gamma},\qquad
    K_{a,p}=K_p^{\rm PD}K_a^{\rm AD}.$$
  On its ideal domain, (\rho_{11}'=e^{-t/T_1}\rho_{11}) and
  (\rho_{01}'=e^{-t/T_2}\rho_{01}) in the rotating frame.
- Literal code accepts nonfinite/negative `t`, applies two probability floors, and enforces
  (T_2\le2T_1+10^{-12}) with an absolute, unit-dependent slack.
- Role: channel | T1/T2 composition
- Scientific object: low-temperature, Markovian, exponential qubit relaxation plus pure dephasing.
- Upstream inputs: `t,t1,t2`, AD/PD primitives, shared floors.
- Downstream consumers: public channel-algebra entrypoint; no installed runtime caller outside tests found.

### Code usage
| frozen file:line | qualname | service/call path | runtime/oracle/test | responsibility |
|---|---|---|---|---|
| `carrier/channels.py:560-577` | `thermal_relaxation_kraus` | channel_algebra public entrypoint | runtime | derive decay parameters, guard T1/T2, compose PD after AD |
| `tests/test_carrier_channels_units.py:426-444,1308-1320` | thermal pins/guards | canonical channel_algebra | test-reference | mirrors the floored formula; its equality-branch comment says pure AD although the helper also floors `lam_phi=0`; only coarse guard violations are tested |
| `tests/test_distribution_boundary.py:555-566` | import boundary | noncanonical | smoke | checks callable/export only |

### Symbols, domains, and conventions
| symbol | meaning | shape/domain | units | basis/order | source symbol |
|---|---|---|---|---|---|
| (t,T_1,T_2,T_\phi) | gate time and decay constants | finite; (t\ge0,T_i>0,T_2\le2T_1) | one common time unit | qubit rotating frame | (t,T_1,T_2,T_\phi) |
| (\Gamma_i) | decay rates | (1/T_i) | inverse-time | longitudinal/transverse | (\Gamma_1,\Gamma_2,\Gamma_\phi) |
| \((\gamma,\lambda_\phi)\) | channel probabilities | \([0,1]\) on ideal domain | probability | AD/canonical-PD gauges | derived |

### Evidence verdict
- provenance_status: `CONTRADICTED/MISAPPLIED`
- required visible risk marker: fully replayable ideal derivation conflicts with accepted inputs and unit-dependent guard
- formula_correctness: incorrect
- application_fit: mismatched
- value_provenance: project-design
- epistemic_class: the ideal formula is `[ours-derived]` from direct AD/PD and rate equations; the shipped callable violates the derivation's domain and exact boundary behavior.

### Exact literature sources
| source ID | publication/version | PDF/hash | exact locator | visually checked page | source says | source does not say |
|---|---|---|---|---|---|---|
| SRC-ARSENIJEVIC-ADPD-v1 | Arsenijević & Banković, arXiv:1606.01145v1 | local PDF/hash above | p.4 Eq.14; p.13 Eqs.53-57 | yes, coordinator | zero-temperature AD and Markovian PD components | this combined API, floors, or T2 slack |
| SRC-KRANTZ-QENG-v5 | Krantz et al., *A Quantum Engineer's Guide to Superconducting Qubits*, arXiv:1904.06560v5; Appl. Phys. Rev. 6, 021318 (2019), DOI 10.1063/1.5089550 | `outputs/papers/1904.06560.pdf`; `7925f8e9ee45eac83142ec8862d12e2728e6913ac26b2f912f72ecdadca2f10d` | PDF/printed p.14, Eqs.41-45; p.16, transverse-relaxation/1/f discussion | yes, coordinator | \(\Gamma_2=\Gamma_1/2+\Gamma_\phi\), exponential population/coherence decay, low-temperature downward limit | general nonexponential 1/f dephasing, invalid time repair, Kraus floors, or absolute slack |

### Source-to-code mapping
| source expression | code expression | transformation | exact/approximate | assumption | status |
|---|---|---|---|---|---|
| \(\Gamma_2=\Gamma_1/2+\Gamma_\phi\) | `inv_tphi=1/t2-1/(2*t1)` | algebraic solve | exact | exponential decay | direct rate bridge |
| Eq.44 decay factors | `gamma`, `lam_phi`, AD then PD | translate scalar decays to Kraus channels | exact | low temperature, rotating frame, finite valid times | `[ours-derived]` core |
| (T_2\le2T_1) | `t2 > 2*t1 + 1e-12` | add absolute tolerance | unit-dependent | caller chooses scale | contradicted guard |
| (t\ge0), finite | no validation | floors derived negative/NaN probabilities | nonlinear repair | invalid input accepted | contradicted |

### Operation replay / derivation
| input | transformation | assumption | output | source locator or derivation step | status |
|---|---|---|---|---|---|
| finite valid (t,T_i) away from endpoints | PD after AD | Markov/low-T/exponential/rotating frame | target (e^{-t/T_1},e^{-t/T_2}) action | Eqs.41-44 + component channels | correct core |
| `t=0`, `t=-1`, or `t=NaN`; (T_1=100,T_2=150) | both derived probabilities become/floor to (10^{-12}) | none | same near-identity but nonidentity channel; \(|1\rangle\) gains (10^{-12}) ground population | coordinator runtime replay | contradicted |
| finite `t>0`, (T_2=2T_1) | `inv_tphi=0`, then `lam_phi=0` is floored to (10^{-12}) | source relation requires zero pure dephasing | TP AD followed by a spurious coherence factor \(\sqrt{1-10^{-12}}\), not exact pure AD | direct algebra and mirrored-test inspection | contradicted exact boundary |
| `t=+inf`, \((100,150)\) | \(\gamma=\lambda=1\), compose | none | exact full ground reset and TP; nonfinite input silently accepted | coordinator correction to reviewer | domain failure, not non-TP |
| (T_1=10^{-13},T_2=2.5\times10^{-13}) | absolute slack comparison | same physical units | unphysical (T_2>2T_1) accepted | coordinator runtime replay | unit-scaling counterexample |

### Composite compatibility
| component | source | object/device/regime | composition bridge | compatible? | risk |
|---|---|---|---|---|---|
| AD component | SRC-ARSENIJEVIC-ADPD-v1 | zero-temperature downward decay | (\gamma=1-e^{-t/T_1}) | yes on valid domain | floor breaks exact (t=0) |
| PD component | SRC-ARSENIJEVIC-ADPD-v1 | exponential Markovian dephasing | (\lambda=1-e^{-2t/T_\phi}) | yes on valid domain | endpoint/floor defect |
| rate bridge | SRC-KRANTZ-QENG-v5 | low-T Bloch-Redfield exponential regime | solve for (T_\phi) | yes conditionally | explicitly not general 1/f decay |
| composition/API guard | project code | common units, finite nonnegative time | PD after AD plus floors/slack | no over accepted domain | whole callable is contradicted |

### Parameter/value provenance
| parameter | value/units | provenance kind | exact locator | transform | allowed claim | forbidden claim |
|---|---|---|---|---|---|---|
| T2 slack | (10^{-12}) in caller's raw time unit | project design | line 570 | additive boundary relaxation | exact code rule | dimensionless/physical validity tolerance |
| probability floor | (10^{-12}) | project design | AD/PD callees | clamps derived probabilities | implementation behavior | physical minimum decay |
| deterministic phase | omitted | rotating-frame assumption | Krantz Eq.44 versus code | drop (e^{\pm i\delta\omega t}) | dissipative envelope in rotating frame | full lab-frame evolution |

### Assumptions and correct-place audit
- Assumptions: finite common-unit time constants, (t\ge0), (T_2\le2T_1), low temperature, exponential Markovian decay, and rotating-frame phase removal.
- Simplifications and error bounds: no scale-invariant guard or bound for probability floors is provided.
- Failure regime: nonexponential 1/f dephasing, finite temperature/upward rate, nonfinite/negative times, exact (t=0), or rescaled time units near the guard.
- Why this formula belongs here: it is a public CORE channel-algebra entrypoint with a strong “exact thermal map” docstring claim.
- Schedule/instrument/record bridge: no installed runtime caller currently fixes units or physical regime.
- Alternative formulation/invariant: validate finite values, require (t\ge0), compare (T_2/(2T_1)) with a dimensionless tolerance, and preserve the exact identity at (t=0).
- Verdict: mismatched

### Independent checks
| invariant/reference | independent route | falsifier | shared blind spot? | result |
|---|---|---|---|---|
| ideal decay law | hand compose AD and diagonal PD | wrong order/factor two | no | expected (T_1/T_2) action recovered |
| zero-time identity | direct runtime on \(|1\rangle,|+\rangle\) | any state change | no | false (10^{-12}) decay reproduced |
| (T_2=2T_1) pure-AD boundary | hand evaluate `lam_phi=0` through the canonical-PD callee | any extra coherence contraction | yes, canonical helper copies the same floor | extra \(\sqrt{1-10^{-12}}\) factor; test comment overclaims exact pure AD |
| scale invariance | rescale valid/invalid boundary example | decision changes with units | no | absolute slack accepts (T_1=10^{-13},T_2=2.5\times10^{-13}) |
| canonical tests | inspect cases/helper | negative/NaN/inf or unit-rescaled input | yes | 71-test combined batch passes without these falsifiers |

### Human verification
- [ ] formula transcription checked
- [ ] exact source page checked
- [ ] symbol/unit convention checked
- [ ] derivation replayed
- [ ] application location checked
- [ ] composite bridge accepted
- Human verdict: unchecked
- Notes: the coordinator explicitly corrected the reviewer's claim that the `t=+inf` example is non-TP; it is TP but outside the supported scientific domain.

<!-- BATCH-1B2A2-ROWS-1 -->

## ECS-CHAN-EXC-001 — Floored upward amplitude excitation

### Formula and role
- Intended raising channel:
  $$K_0=\operatorname{diag}(\sqrt{1-g},1),\qquad
    K_1=\sqrt g|1\rangle\!\langle0|,$$
  so (|0\rangle\langle0|\mapsto(1-g)|0\rangle\langle0|+g|1\rangle\langle1|).
- Literal code first applies (g=f(\gamma_\uparrow)), so public zero/negative/NaN inputs become (10^{-12}).
- Role: channel | one-qubit pumping primitive
- Scientific object: a standalone upward transition channel, not by itself a finite-temperature thermal channel.
- Upstream inputs: public `gamma_up`, probability floor, computational basis.
- Downstream consumers: legacy M24 compatibility branch and ordinary channel tests.

### Code usage
| frozen file:line | qualname | service/call path | runtime/oracle/test | responsibility |
|---|---|---|---|---|
| `carrier/channels.py:580-585` | `thermal_excitation_kraus` | channel_algebra -> M24 adapter | runtime | floor the input and build a raising Kraus pair |
| `carrier/channels.py:390-391` | M24 dispatch | compatibility catalog | runtime | labels the primitive `thermal_excitation` |
| `tests/test_carrier_channels_units.py:447-451` | excitation pins | canonical channel_algebra | test-reference | ordinary CPTP/action checks only |
| `tests/test_window_channel.py:391` | Torch/NumPy mirror | noncanonical compatibility | test-reference | uses installed NumPy channel as expected value |

### Symbols, domains, and conventions
| symbol | meaning | shape/domain | units | basis/order | source symbol |
|---|---|---|---|---|---|
| \(\gamma_\uparrow\) | public excitation probability | intended finite \([0,1]\) | probability | \((|0\rangle,|1\rangle)\) | derived from AD/GAD parameters |
| (g) | floored/capped probability | \([10^{-12},1]\) | probability | same | no direct standalone source symbol |
| (K_1) | upward jump | (2\times2) | dimensionless | (|0\rangle\to|1\rangle) | X-conjugate of AD jump |

### Evidence verdict
- provenance_status: `CONTRADICTED/MISAPPLIED`
- required visible risk marker: derived raising core conflicts with the public mechanism-off map
- formula_correctness: incorrect
- application_fit: mismatched
- value_provenance: project-design
- epistemic_class: `[ours-derived]` by X-conjugating direct AD; a GAD source is adjacent support only for thermal context.

### Exact literature sources
| source ID | publication/version | PDF/hash | exact locator | visually checked page | source says | source does not say |
|---|---|---|---|---|---|---|
| SRC-ARSENIJEVIC-ADPD-v1 | Arsenijević & Banković, arXiv:1606.01145v1 | local PDF/hash above | p.4 Eq.14; p.5 Eq.17 | yes, coordinator | direct downward AD and the four-Kraus finite-temperature GAD family | this normalized standalone upward channel, detailed-balance-free use, or probability floor |

### Source-to-code mapping
| source expression | code expression | transformation | exact/approximate | assumption | status |
|---|---|---|---|---|---|
| AD Eq.14 | code raising pair | (K_i^{\uparrow}=XK_i^{\downarrow}X) | exact | same basis/probability | `[ours-derived]` |
| GAD Eq.17 | standalone pair | select and normalize the upward arm | not the source thermal channel | omit downward arm and equilibrium weight | adjacent only |
| physical (g=0) identity | `f(0)=1e-12` | insert upward mass | not source-supported | mechanism-off | contradicted |

### Operation replay / derivation
| input | transformation | assumption | output | source locator or derivation step | status |
|---|---|---|---|---|---|
| \(g\in[0,1]\) after transform | \(\sum_i K_i^\dagger K_i\) | finite | \(I_2\), including \(g=1\) | X-conjugated Eq.14 | correct core |
| public `gamma_up=0`, \(|0\rangle\) | floor to (10^{-12}) | none | false excited population (10^{-12}) | coordinator replay | counterexample |
| standalone `thermal_excitation` label | omit downward jump | no bath temperature/frequency | no Gibbs fixed point or detailed balance | compare Eq.17 | application gap |

### Composite compatibility
| component | source | object/device/regime | composition bridge | compatible? | risk |
|---|---|---|---|---|---|
| X-conjugated AD | SRC-ARSENIJEVIC-ADPD-v1 | abstract upward primitive | basis conjugation | yes | derivation, not direct transcription |
| finite-temperature GAD | source Eq.17 | bidirectional thermal bath | retain only upward arm | no for full thermal claim | missing equilibrium/downward rate |
| probability floor | ECS-NUM-003 | project convention | physical input transform | no at zero/invalid | false pumping |

### Parameter/value provenance
| parameter | value/units | provenance kind | exact locator | transform | allowed claim | forbidden claim |
|---|---|---|---|---|---|---|
| floor | (10^{-12}) | project design | line 581 | clamp/cap | implementation behavior | thermal population floor |
| M24 default | `gamma_up=0.006` | project design | adapter line 391 | none beyond floor | legacy sweep/profile | device temperature or detailed-balance rate |

### Assumptions and correct-place audit
- Assumptions: finite excitation probability and use as an abstract raising primitive.
- Simplifications and error bounds: omitting the downward arm has no stated thermal-regime bound.
- Failure regime: mechanism-off/invalid inputs and any claim of a complete finite-temperature bath.
- Why this formula belongs here: it is public and used by the installed M24 adapter.
- Schedule/instrument/record bridge: the M24 value is not tied to temperature, transition frequency, or gate duration.
- Alternative formulation/invariant: preserve exact zero and, for a thermal claim, parameterize paired up/down rates satisfying detailed balance.
- Verdict: mismatched

### Independent checks
| invariant/reference | independent route | falsifier | shared blind spot? | result |
|---|---|---|---|---|
| raising action | explicit X conjugation of AD matrices | wrong matrix entry | no | code core recovered |
| exact TP | hand completeness at (g=0,1) | endpoint residual | no | transformed channel is TP |
| public zero | apply to \(|0\rangle\) | nonzero excitation | no | (10^{-12}) false population |
| tests | inspect inputs/oracle | invalid/zero/detailed balance | yes | ordinary checks do not close semantics |

### Human verification
- [ ] formula transcription checked
- [ ] exact source page checked
- [ ] symbol/unit convention checked
- [ ] derivation replayed
- [ ] application location checked
- [ ] composite bridge accepted
- Human verdict: unchecked
- Notes: `thermal` in the function name is not evidence for a full thermal channel.

## ECS-CHAN-RESET-001 — Partial replacement/reset surrogate

### Formula and role
- Project channel form:
  $$K_0=\sqrt{1-p}I,\qquad K_1=\sqrt p|t\rangle\!\langle0|,\qquad
    K_2=\sqrt p|t\rangle\!\langle1|,$$
  $$\mathcal R_{p,t}(\rho)=(1-p)\rho+p|t\rangle\!\langle t|\operatorname{Tr}\rho.$$
- Literal code uses (p=f(p_{\rm public})), floors (1-p), and validates only
  `int(target_state)`, not the original discrete value.
- Role: channel | partial state-replacement surrogate
- Scientific object: convex mixture of identity and unconditional replacement by a chosen computational state.
- Upstream inputs: public probability/target, ECS-NUM-002/003.
- Downstream consumers: legacy M17 reset-to-1 compatibility branch.

### Code usage
| frozen file:line | qualname | service/call path | runtime/oracle/test | responsibility |
|---|---|---|---|---|
| `carrier/channels.py:588-598` | `reset_to_state_kraus` | channel_algebra -> M17 adapter | runtime | coerce target and construct three Kraus matrices |
| `carrier/channels.py:376-377` | M17 dispatch | compatibility catalog | runtime | instantiate target 1 with default `p=0.018` |
| `tests/test_carrier_channels_units.py:452-459,470-472` | reset pins | canonical channel_algebra | test-reference | tests integer targets and interior probabilities only |

### Symbols, domains, and conventions
| symbol | meaning | shape/domain | units | basis/order | source symbol |
|---|---|---|---|---|---|
| (p) | requested replacement probability | intended finite \([0,1]\) | probability | computational basis | reset infidelity only in adjacent experiments |
| \(t\) | target state index | strict integer \(\{0,1\}\) | label | \((|0\rangle,|1\rangle)\) | ground/excited state in adjacent experiments |
| \(\mathcal R_{p,t}\) | project surrogate channel | qubit CPTP only on exact intended domain | dimensionless | state replacement | no exact primary-source formula found |

### Evidence verdict
- provenance_status: `ADJACENT-ONLY`
- required visible risk marker: **高危无出处（仅有邻近/二手证据）**
- formula_correctness: incorrect
- application_fit: mismatched
- value_provenance: project-design
- epistemic_class: reset experiments support the physical phenomenon and magnitude neighborhood, not this Kraus mixture; the full accepted-domain implementation also fails its own ideal map.

### Exact literature sources
| source ID | publication/version | PDF/hash | exact locator | visually checked page | source says | source does not say |
|---|---|---|---|---|---|---|
| SRC-REED-RESET-v2 | Reed et al., *Fast Reset and Suppressing Spontaneous Emission of a Superconducting Qubit*, arXiv:1003.0142v2; Appl. Phys. Lett. 96, 203110 (2010), DOI 10.1063/1.3435463 | `outputs/papers/1003.0142.pdf`; `c607ac9932726d7ff5bba1a8f533ce1e04f285dde1a4d27adc540f112d873a42` | PDF/printed p.1, abstract and opening reset discussion | yes, coordinator | active ground reset reaches 99.9% fidelity in 120 ns | this convex-mixture channel, target-1 replacement, or adapter default |
| SRC-MCEWEN-RESET-v1 | McEwen et al., *Removing leakage-induced correlated errors in superconducting quantum error correction*, arXiv:2102.06131v1; Nat. Commun. 12, 1761 (2021), DOI 10.1038/s41467-021-21982-y | `docs/papers/mcewen_removing_leakage_correlated_2102.06131.pdf`; `93d0488667b5e5ba908898d7efe4e69f6fcf6575b382c2116b1bec7676a182e2` | PDF index 2/main printed p.3, Fig.2; PDF index 9/supplement printed p.3, Fig.S3 | yes, coordinator | reset to ground, about \(10^{-3}\) residual, with computational \(|1\rangle\) error dominant | this three-Kraus surrogate or probability-floor policy |

### Source-to-code mapping
| source expression | code expression | transformation | exact/approximate | assumption | status |
|---|---|---|---|---|---|
| measured reset infidelity/residual \(|1\rangle\) | mixture probability (p) | model residual as stochastic replacement | phenomenological | incoherent state-independent error | adjacent only |
| ground reset | `target_state=1` in M17 | model failure direction, not successful reset operation | project surrogate | ideal reset occurs outside this channel | bridge open |
| exact replacement at (p=1) | floored identity coefficient | add (10^{-12}\rho) | incorrect | endpoint accepted | contradicted internally |

### Operation replay / derivation
| input | transformation | assumption | output | source locator or derivation step | status |
|---|---|---|---|---|---|
| finite (0<p<1), integer target | Kraus action | exact weights | ((1-p)\rho+p|t\rangle\langle t|\operatorname{Tr}\rho) | hand operator-sum replay | correct subdomain |
| \(p=1\) | floor identity remainder | none | \(\sum_i K_i^\dagger K_i=(1+10^{-12})I\), residual \(1.4143393\times10^{-12}\) | coordinator runtime replay | non-TP |
| `target_state=0.9,-0.2,1.9,"1"` | apply Python `int` first | none | all accepted as target 0 or 1 | coordinator runtime replay | domain counterexample |

### Composite compatibility
| component | source | object/device/regime | composition bridge | compatible? | risk |
|---|---|---|---|---|---|
| physical active reset | SRC-REED-RESET-v2/SRC-MCEWEN-RESET-v1 | device reset to ground | represent residual as replacement mixture | not established | experiments are adjacent only |
| identity/replacement mixture | generic Kraus theorem | abstract channel | choose (p,t) and placement | algebraically valid on restricted domain | scientific mechanism unsourced |
| M17 adapter | project compatibility profile | reset-to-1 bias | default \(p=0.018\) | open | outside cited \(10^{-3}\)--\(10^{-2}\) neighborhood |

### Parameter/value provenance
| parameter | value/units | provenance kind | exact locator | transform | allowed claim | forbidden claim |
|---|---|---|---|---|---|---|
| M17 default (p) | (0.018) | project design | adapter line 377 | floor only | reproducible legacy default | measured device reset error |
| adjacent magnitude | about (10^{-3}), up to project sweep (10^{-2}) | experiment + project band | McEwen Fig.2/S3; Reed p.1 | interpreted as residual population | neighboring scale | source of 0.018 or exact channel probability |
| probability floor | (10^{-12}) | project design | lines 589,593 | clamp/remainder floor | code behavior | physical reset floor |

### Assumptions and correct-place audit
- Assumptions: incoherent, state-independent replacement error; target is a strict discrete bit; successful ideal reset is modeled elsewhere.
- Simplifications and error bounds: no instrument-, state-, leakage-, or schedule-dependent approximation bound is supplied.
- Failure regime: (p=0/1), nonfinite/invalid probabilities, fractional/coercible targets, or interpreting the surrogate as a direct reset-gate derivation.
- Why this formula belongs here: it is the installed compatibility M17 channel.
- Schedule/instrument/record bridge: adjacent experiments use a physical reset instrument; code exposes an isolated unconditional channel without that bridge.
- Alternative formulation/invariant: reject non-integer targets, validate exact probabilities, and explicitly label/ground the surrogate plus its placement.
- Verdict: mismatched

### Independent checks
| invariant/reference | independent route | falsifier | shared blind spot? | result |
|---|---|---|---|---|
| restricted-domain action | hand sum over matrix units | wrong target/weight | no | project formula reproduced |
| endpoint TP | exact completeness sum | (1+\epsilon) | no | fails at (p=1) |
| target domain | pre-coercion adversarial inputs | fractional values accepted | no | four aliases reproduced |
| literature | visual reset figures/text | exact Kraus mixture absent | no | remains adjacent-only |

### Human verification
- [ ] formula transcription checked
- [ ] exact source page checked
- [ ] symbol/unit convention checked
- [ ] derivation replayed
- [ ] application location checked
- [ ] composite bridge accepted
- Human verdict: unchecked
- Notes: **高危无出处（仅有邻近/二手证据）**; the corrected Reed citation is APL 96, 203110, not the stale PRL citation noted in older project history.

## ECS-CHAN-LEAKSUR-001 — Two-level AD-after-Z channel mislabeled as leakage

### Formula and role
- Literal interior composition:
  $$K_{a,z}=K_a^{\rm AD}(p)K_z^{\rm PZ}(p),\qquad
    \mathcal E=\mathrm{AD}_p\circ\mathrm{PZ}_p,$$
  yielding (\rho_{11}'=(1-p)\rho_{11}) and
  (\rho_{01}'=\sqrt{1-p}(1-2p)\rho_{01}) before floor defects.
- Every returned Kraus matrix is (2\times2); no (|2\rangle) leakage level exists.
- Role: channel | legacy synthetic composite
- Scientific object: a qubit AD-after-Z channel; the installed name/application claims a leakage surrogate.
- Upstream inputs: one shared floored `p`, AD and stochastic-Z primitives.
- Downstream consumers: legacy M34 compatibility adapter and mirror tests.

### Code usage
| frozen file:line | qualname | service/call path | runtime/oracle/test | responsibility |
|---|---|---|---|---|
| `carrier/channels.py:601-603` | `leakage_relaxation_surrogate_kraus` | channel_algebra -> M34 adapter | runtime | reuse one probability in phase then damping composition |
| `carrier/channels.py:410-411` | M34 dispatch | compatibility catalog | runtime | publish the qubit composite under leakage label |
| `tests/test_carrier_channels_units.py:460-463` | surrogate pin | canonical channel_algebra | test-reference | compares to the same component composition |
| `tests/test_window_channel.py:393` | Torch/NumPy mirror | noncanonical compatibility | test-reference | uses installed NumPy result as oracle |

### Symbols, domains, and conventions
| symbol | meaning | shape/domain | units | basis/order | source symbol |
|---|---|---|---|---|---|
| (p) | shared Z-flip and AD probability | code-repaired \([10^{-12},1]\) | probability | qubit basis only | unrelated component parameters |
| (P_{\rm leak}) | leakage-subspace projector | absent from code | dimensionless | would require \(|2\rangle\) or larger | none |
| (K_{a,z}) | composed qubit Kraus terms | four (2\times2) matrices | dimensionless | phase acts first | component Kraus only |

### Evidence verdict
- provenance_status: `CONTRADICTED/MISAPPLIED`
- required visible risk marker: **高危无出处（文献仅支持形式）**
- formula_correctness: incorrect
- application_fit: mismatched
- value_provenance: project-design
- epistemic_class: sourced AD/PZ component forms; no source for their shared-parameter composition, and the leakage application is falsified by Hilbert-space dimension.

### Exact literature sources
| source ID | publication/version | PDF/hash | exact locator | visually checked page | source says | source does not say |
|---|---|---|---|---|---|---|
| SRC-ARSENIJEVIC-ADPD-v1 | Arsenijević & Banković, arXiv:1606.01145v1 | local PDF/hash above | p.4 Eq.14; p.13 Eq.55 | yes, coordinator | separate qubit AD and stochastic-Z phase-damping forms | same-(p) composition, leakage production/relaxation, or M34 placement |

### Source-to-code mapping
| source expression | code expression | transformation | exact/approximate | assumption | status |
|---|---|---|---|---|---|
| separate AD and PZ channels | `damp @ phase` | compose PZ then AD | exact algebraically on interior | independent sequential qubit processes | form-only |
| distinct physical rates | one shared `p` | identify parameters | unsupported | equality assumed | open |
| leakage out of computational subspace | (2\times2) matrices only | none possible | impossible | a leakage level would exist | contradicted |

### Operation replay / derivation
| input | transformation | assumption | output | source locator or derivation step | status |
|---|---|---|---|---|---|
| interior (0<p<1) | apply PZ then AD | qubit state | stated population/coherence factors | hand composition | algebraically correct subdomain |
| any qubit input | inspect output support | all matrices \(2\times2\) | \(\operatorname{Tr}(P_{\rm leak}\mathcal E(\rho))=0\) identically | dimension falsifier | leakage claim impossible |
| \(p=1\) | PZ endpoint excess then TP AD | none | \(\sum_i K_i^\dagger K_i=(1+10^{-12})I\), residual \(1.4143393\times10^{-12}\) | coordinator runtime replay | non-TP |

### Composite compatibility
| component | source | object/device/regime | composition bridge | compatible? | risk |
|---|---|---|---|---|---|
| AD | SRC-ARSENIJEVIC-ADPD-v1 | qubit energy decay | after PZ | algebraically yes | not leakage |
| PZ | SRC-ARSENIJEVIC-ADPD-v1 | qubit phase flip | before AD with same (p) | unsourced | parameter conflation |
| current leakage line | `leakage_kraus` at lines 606-721, Batch 1B2b pending | qutrit (|0,1,2\rangle) | legacy M34 label | no | incompatible scientific object |

### Parameter/value provenance
| parameter | value/units | provenance kind | exact locator | transform | allowed claim | forbidden claim |
|---|---|---|---|---|---|---|
| shared (p) | caller supplied; M34 default 0.004 | project design | line 411 | used twice after floor | legacy synthetic strength | leakage/seepage rate |
| Hilbert dimension | 2 | implementation fact | returned matrix shapes | none | qubit composite | qutrit leakage carrier |

### Assumptions and correct-place audit
- Assumptions: a qubit-only synthetic stress map and an unsupported equality of phase/relaxation probabilities.
- Simplifications and error bounds: no mapping to a leakage population, WG rate, or qutrit channel is possible.
- Failure regime: every scientific leakage interpretation, plus the (p=1) endpoint.
- Why this formula belongs here: the installed M34 adapter explicitly exposes it as leakage.
- Schedule/instrument/record bridge: incompatible with the current qutrit/Wood-Gambetta leakage service.
- Alternative formulation/invariant: use an explicit enlarged Hilbert space and assert nonzero/controlled leakage projector population.
- Verdict: mismatched

### Independent checks
| invariant/reference | independent route | falsifier | shared blind spot? | result |
|---|---|---|---|---|
| component order | hand matrix composition | AD/PZ reversed | no | phase then AD confirmed |
| leakage support | dimension/projector argument | any \(|2\rangle\) amplitude | no | impossible by construction |
| endpoint TP | direct completeness | excess trace | no | fails at (p=1) |
| tests | inspect expected objects | leakage-population oracle | yes | only composition/mirror equality is tested |

### Human verification
- [ ] formula transcription checked
- [ ] exact source page checked
- [ ] symbol/unit convention checked
- [ ] derivation replayed
- [ ] application location checked
- [ ] composite bridge accepted
- Human verdict: unchecked
- Notes: **高危无出处（文献仅支持形式）**; the stronger `CONTRADICTED/MISAPPLIED` status takes precedence over a merely open composite label.

## ECS-CHAN-CUSTOM-001 — Fixed rotation followed by amplitude damping

### Formula and role
- Literal channel:
  $$U=R_Z(0.37)R_X(0.23),\qquad
    K_a=K_a^{\rm AD}(f(\eta))U,$$
  $$\mathcal E_\eta(\rho)=\mathrm{AD}_{f(\eta)}(U\rho U^\dagger).$$
  The rightmost (R_X) acts first, then (R_Z), then AD.
- Role: channel | synthetic non-Pauli stress channel
- Scientific object: fixed coherent rotation dressed by amplitude damping.
- Upstream inputs: `eta`, ECS-CHAN-001 rotation primitives, ECS-CHAN-AD-001.
- Downstream consumers: legacy M15 adapter and optional hard tests.

### Code usage
| frozen file:line | qualname | service/call path | runtime/oracle/test | responsibility |
|---|---|---|---|---|
| `carrier/channels.py:724-730` | `custom_non_pauli_kraus` | channel_algebra -> M15 adapter | runtime | compose fixed rotation before AD |
| `carrier/channels.py:374-375` | M15 dispatch | compatibility catalog | runtime | instantiate synthetic custom channel |
| `tests/test_carrier_channels_units.py:499-503` | custom pin | canonical channel_algebra | test-reference | repeats the same fixed constants and composition |
| `tests/test_window_channel.py:392` | Torch/NumPy mirror | noncanonical compatibility | test-reference | migration equivalence only |

### Symbols, domains, and conventions
| symbol | meaning | shape/domain | units | basis/order | source symbol |
|---|---|---|---|---|---|
| \(\eta\) | AD-only probability control | public float repaired to \([10^{-12},1]\) | probability | qubit | no whole-channel source |
| (0.37,0.23) | fixed Z/X angles | real | radians | rightmost-first matrix order | none |
| (U) | fixed SU(2) rotation | (2\times2) | dimensionless | (R_ZR_X) | general Pauli rotation form only |

### Evidence verdict
- provenance_status: `COMPOSITE-UNCLOSED`
- required visible risk marker: **高危无出处（组合公式整体无直接出处）**
- formula_correctness: correct
- application_fit: bridge-open
- value_provenance: project-design
- epistemic_class: component algebra is closed, but physical mechanism, order, fixed angles, and parameter meaning are project-synthetic.

### Exact literature sources
| source ID | publication/version | PDF/hash | exact locator | visually checked page | source says | source does not say |
|---|---|---|---|---|---|---|
| SRC-ARSENIJEVIC-ADPD-v1 | Arsenijević & Banković, arXiv:1606.01145v1 | local PDF/hash above | p.4 Eq.14 | yes, coordinator | AD Kraus component | rotation, order, angles, or custom mechanism |
| SRC-SHELDON-RB-v1 | Sheldon et al., arXiv:1504.06597v1; Phys. Rev. A 93, 012301 (2016) | manifest artifact | PDF/printed p.2 Eq.1 | yes, prior coordinator check | coherent rotation/over-rotation form | these axes, angles, or AD composition |

### Source-to-code mapping
| source expression | code expression | transformation | exact/approximate | assumption | status |
|---|---|---|---|---|---|
| Pauli rotations | `rz_unitary @ rx_unitary` | compose two sourced forms | exact algebraically | radians, rightmost first | components closed |
| AD Kraus | `item @ rotate` | precompose unitary before channel | exact Kraus composition | same Hilbert space | components closed |
| mechanism/value choice | fixed angles and AD-only eta | project selection | no source | synthetic test object | open |

### Operation replay / derivation
| input | transformation | assumption | output | source locator or derivation step | status |
|---|---|---|---|---|---|
| effective \(e\in[10^{-12},1]\) | \(\sum_a U^\dagger A_a^\dagger A_aU\) | AD TP, \(U\) unitary | \(I_2\) to roundoff | hand composition | correct |
| public `eta=0` | \(e=10^{-12}\), retain fixed \(U\) | eta controls AD only | about \(\sin^2(0.23/2)\approx1.32\times10^{-2}\) excitation from RX on \(|0\rangle\) before AD | coordinator/reviewer replay | not an all-channel off switch |
| fixed angles | compare source coverage | none | no device/mechanism mapping | bounded search | open |

### Composite compatibility
| component | source | object/device/regime | composition bridge | compatible? | risk |
|---|---|---|---|---|---|
| RX/RZ | ECS-CHAN-001 / SRC-SHELDON-RB-v1 | coherent qubit rotations | fixed sequential U | algebraically yes | constants unsourced |
| AD | ECS-CHAN-AD-001 / SRC-ARSENIJEVIC-ADPD-v1 | zero-temperature decay | after fixed U | algebraically yes | inherited input-floor mismatch |
| whole custom mechanism | none | optional hard-test perturbation | order + values + adapter placement | no source closure | 高危无出处（组合公式整体无直接出处） |

### Parameter/value provenance
| parameter | value/units | provenance kind | exact locator | transform | allowed claim | forbidden claim |
|---|---|---|---|---|---|---|
| Z angle | 0.37 rad | project design | line 729 | none | exact synthetic constant | calibrated device rotation |
| X angle | 0.23 rad | project design | line 729 | none | exact synthetic constant | calibrated device rotation |
| eta/default | caller supplied; M15 default 0.02 | project design | adapter line 375 | floor controls AD only | reproducible stress channel | total perturbation strength |

### Assumptions and correct-place audit
- Assumptions: this is intentionally a synthetic adversarial channel; `eta` controls only the damping component.
- Simplifications and error bounds: no physical approximation target or bound exists for the fixed composite.
- Failure regime: any device-mechanism interpretation or claim that `eta=0` disables the full channel.
- Why this formula belongs here: it ships through the M15 compatibility adapter and canonical tests.
- Schedule/instrument/record bridge: no current Axis-1 placement or device mapping was found.
- Alternative formulation/invariant: keep it explicitly test-only, or source and parameterize every component and define total-strength semantics.
- Verdict: bridge-open

### Independent checks
| invariant/reference | independent route | falsifier | shared blind spot? | result |
|---|---|---|---|---|
| composition order | act on \(|0\rangle\) and compare (AD(U\rho U^\dagger)) | reversed order | no | code order confirmed |
| CPTP | analytic completeness | residual | no | correct for transformed eta |
| constants/source | bounded local/external search | exact whole formula found | no | none found |
| canonical tests | inspect copied constants | corruption-independent values | yes | implementation mirror only |

### Human verification
- [ ] formula transcription checked
- [ ] exact source page checked
- [ ] symbol/unit convention checked
- [ ] derivation replayed
- [ ] application location checked
- [ ] composite bridge accepted
- Human verdict: unchecked
- Notes: **高危无出处（组合公式整体无直接出处）**; mathematical correctness does not promote the synthetic composite to a physical mechanism.

<!-- BATCH-1B2A2-ROWS-2 -->

## ECS-CHAN-DEP2-001 — Floored 15-Pauli two-qubit depolarizing channel

### Formula and role
- Source channel:
  $$\mathcal E_p(\rho)=(1-p)\rho+\frac p{15}
    \sum_{P\in\{I,X,Y,Z\}^{\otimes2}\setminus\{II\}}P\rho P,$$
  represented by (K_{II}=\sqrt{1-p}I_4) and (K_P=\sqrt{p/15}P).
- Literal code applies (p=f(p_{\rm public})) and floors the identity remainder separately.
- Role: channel | two-qubit stochastic-Pauli primitive
- Scientific object: total-nonidentity-event parameterization of two-qubit depolarizing noise.
- Upstream inputs: public probability, two-qubit Pauli basis, ECS-NUM-002/003.
- Downstream consumers: legacy M9 compatibility adapter and mirror tests.

### Code usage
| frozen file:line | qualname | service/call path | runtime/oracle/test | responsibility |
|---|---|---|---|---|
| `carrier/channels.py:733-742` | `two_qubit_depolarizing_kraus` | channel_algebra -> M9 adapter | runtime | enumerate 15 nonidentity Paulis and assign equal mass |
| `carrier/channels.py:341-342` | M9 dispatch | compatibility catalog | runtime | instantiate default two-qubit depolarizing channel |
| `tests/test_carrier_channels_units.py:488-496` | depolarizing pins | canonical channel_algebra | test-reference | checks 16 terms and copied (p/15) weights on interior values |
| `tests/test_window_channel.py:403` | Torch/NumPy mirror | noncanonical compatibility | test-reference | uses installed NumPy builder as expected value |

### Symbols, domains, and conventions
| symbol | meaning | shape/domain | units | basis/order | source symbol |
|---|---|---|---|---|---|
| (p) | total probability of a nonidentity two-qubit Pauli | intended finite \([0,1]\) | probability | C-order two-qubit basis | (p) |
| (P) | two-qubit Pauli | 15 elements excluding II | dimensionless | left Kronecker right | (P\in\{I,X,Y,Z\}^{\otimes2}\setminus\{II\}) |
| (q) | replace-by-(I_4/4) convention | (q=16p/15) | probability-like parameter | channel action | not the source's (p) |

### Evidence verdict
- provenance_status: `CONTRADICTED/MISAPPLIED`
- required visible risk marker: direct source formula conflicts with literal zero/one endpoint map
- formula_correctness: incorrect
- application_fit: mismatched
- value_provenance: project-design
- epistemic_class: exact direct interior formula; public endpoint and structural-zero behavior are contradicted.

### Exact literature sources
| source ID | publication/version | PDF/hash | exact locator | visually checked page | source says | source does not say |
|---|---|---|---|---|---|---|
| SRC-KAM-NM-v4 | Kam et al., *Detrimental non-Markovian errors for surface code memory*, arXiv:2410.23779v4; Quantum Sci. Technol. 10, 035060 (2025), DOI 10.1088/2058-9565/adebab | `outputs/papers/2410.23779.pdf`; `9f7bfb374110dc76df3a60a0af3e16f64347ad80de999a2fce687d88936866bf` | PDF/printed p.3, Eq.1c | yes, coordinator | exactly the 15-term two-qubit channel with total nonidentity mass (p) | probability floor, excess identity term at (p=1), or replacement-convention parameter (q) |

### Source-to-code mapping
| source expression | code expression | transformation | exact/approximate | assumption | status |
|---|---|---|---|---|---|
| Eq.1c sum over (P\ne II) | nested IXYZ labels excluding II | enumerate basis | exact | same Kronecker order up to labeling | direct |
| (p/15) | `each=p/len(non_identity)` | count 15 | exact | unchanged (p) | direct interior |
| (1-p=0) at (p=1) | `positive_floor(1-p)` | insert identity mass (10^{-12}) | not source-supported | endpoint accepted | contradicted |

### Operation replay / derivation
| input | transformation | assumption | output | source locator or derivation step | status |
|---|---|---|---|---|---|
| interior \(0<p<1\) | Pauli completeness | all 15 unitary terms | \(\sum_i K_i^\dagger K_i=I_4\) | Eq.1c | correct core |
| public (p=1) | floor zero identity weight | none | ((1+10^{-12})I_4), Frobenius residual (1.9992896\times10^{-12}) | coordinator runtime replay | non-TP |
| Pauli twirl | add/subtract II term | trace-one state | \(\mathcal E_p=(1-16p/15)\rho+(16p/15)I_4/4\) | hand derivation | convention bridge |
| public (p=0) | floor to (10^{-12}) | mechanism-off | live 15-Pauli error mass | ECS-NUM-003 replay | contradicted |

### Composite compatibility
| component | source | object/device/regime | composition bridge | compatible? | risk |
|---|---|---|---|---|---|
| equal 15-Pauli channel | SRC-KAM-NM-v4 | circuit-level depolarizing error | direct Kraus representation | yes on interior | source permits exact zero weights |
| probability/remainder floors | ECS-NUM-002/003 | project convention | inserted into event simplex | no at endpoints | false events and trace excess |
| replacement convention | hand Pauli twirl | ((1-q)\rho+qI/4) | (q=16p/15) | exact algebra | (p>15/16\Rightarrow q>1), not a convex replacement weight |

### Parameter/value provenance
| parameter | value/units | provenance kind | exact locator | transform | allowed claim | forbidden claim |
|---|---|---|---|---|---|---|
| M9 default (p) | 0.006 | project design | adapter line 342 | probability floor | reproducible legacy profile | device-derived error probability |
| floor | (10^{-12}) | project design | lines 734,738 | clamp/remainder floor | implementation behavior | sourced rare-event mass |

### Assumptions and correct-place audit
- Assumptions: finite probability, equal nonidentity Pauli mass, and total-event (p) convention.
- Simplifications and error bounds: no bound licenses endpoint flooring or maps M9's default to a device.
- Failure regime: exact identity, (p=1), invalid/nonfinite input, or confusing (p) with replacement (q).
- Why this formula belongs here: it ships through the M9 adapter and is an exact formula in a primary source.
- Schedule/instrument/record bridge: interior channel placement is compatible, but the public signature/domain is not.
- Alternative formulation/invariant: validate the closed simplex, preserve structural zeros, and document the parameter convention explicitly.
- Verdict: mismatched

### Independent checks
| invariant/reference | independent route | falsifier | shared blind spot? | result |
|---|---|---|---|---|
| Eq.1c enumeration | independently enumerate IXYZ tensor products | wrong count/weight | no | 15 terms and (p/15) confirmed |
| exact TP | analytic scalar completeness | endpoint excess | no | (p=1) fails |
| convention | two-qubit Pauli twirl identity | (q=p) assumption | no | (q=16p/15) confirmed |
| tests | inspect chosen p/oracle | endpoint/convention falsifier | yes | copied interior form only |

### Human verification
- [ ] formula transcription checked
- [ ] exact source page checked
- [ ] symbol/unit convention checked
- [ ] derivation replayed
- [ ] application location checked
- [ ] composite bridge accepted
- Human verdict: unchecked
- Notes: the direct source does not rescue the literal floored endpoint implementation.

## ECS-CHAN-CORRREL-001 — Legacy pair-loss channel under the current M12 label

### Formula and role
- Literal pair-loss channel:
  $$K_0=\operatorname{diag}(1,1,1,\sqrt{1-g}),\qquad
    K_1=\sqrt g|00\rangle\!\langle11|,$$
  with (g=f(\gamma)).
- It only transfers \(|11\rangle\to|00\rangle\); it does not implement the current collective jump
  \(L=\sqrt{\gamma_c}(\sigma^-\otimes I+I\otimes\sigma^-)\).
- Role: channel | legacy pair-loss mechanism
- Scientific object: amplitude damping on the effective subspace ({|00\rangle,|11\rangle}), with (|01\rangle,|10\rangle) inert.
- Upstream inputs: public `gamma`, probability floor, C-order two-qubit basis.
- Downstream consumers: legacy M12 compatibility dispatch and mirror tests.

### Code usage
| frozen file:line | qualname | service/call path | runtime/oracle/test | responsibility |
|---|---|---|---|---|
| `carrier/channels.py:745-750` | `correlated_relaxation_kraus` | channel_algebra -> legacy M12 adapter | runtime | build direct pair-loss Kraus matrices |
| `carrier/channels.py:355-356` | M12 dispatch | compatibility catalog | runtime | assigns the legacy object to the M12 label |
| `docs/twin_validation/m12_correlated_2q_relaxation_BUILD_prereg.md:1-19,59-60` | current M12 contract | binding project science | current oracle/contract | defines Dicke collective collapse and explicitly forbids this legacy toy |
| `tests/test_carrier_channels_units.py:478-485` | correlated-relaxation pins | canonical channel_algebra | test-reference | intentionally fixes the legacy (|11\rangle\to|00\rangle) map |
| `tests/test_window_channel.py:404` | Torch/NumPy mirror | noncanonical compatibility | test-reference | migration equality, not current-M12 science |

### Symbols, domains, and conventions
| symbol | meaning | shape/domain | units | basis/order | source symbol |
|---|---|---|---|---|---|
| (g) | repaired pair-loss probability | \([10^{-12},1]\) | probability | (|00\rangle,|01\rangle,|10\rangle,|11\rangle) | effective AD parameter only |
| (K_1) | two-excitation pair jump | (4\times4) | dimensionless | index 3 to 0 | no direct physical source found |
| \(L\) | current M12 collective single-excitation lowering sum | \(4\times4\) generator | \(\sqrt{\text{rate}}\) | same basis | current theory-first contract |

### Evidence verdict
- provenance_status: `CONTRADICTED/MISAPPLIED`
- required visible risk marker: **高危无出处（文献仅支持形式）**; current binding M12 object and the legacy channel differ in jump target, dark state, and single-excitation action
- formula_correctness: incorrect
- application_fit: mismatched
- value_provenance: project-design
- epistemic_class: the restricted pair-loss Kraus algebra is valid after transformed (g), but its public zero semantics and M12 application are wrong.

### Exact literature sources
| source ID | publication/version | PDF/hash | exact locator | visually checked page | source says | source does not say |
|---|---|---|---|---|---|---|
| SRC-ARSENIJEVIC-ADPD-v1 | Arsenijević & Banković, arXiv:1606.01145v1 | local PDF/hash above | p.4 Eq.14 | yes, coordinator | abstract two-level AD Kraus structure | physical (|11\rangle\to|00\rangle) pair loss, spectator subspace, shared bath, or M12 label |

### Source-to-code mapping
| source expression | code expression | transformation | exact/approximate | assumption | status |
|---|---|---|---|---|---|
| two-level AD | effective (|00\rangle,|11\rangle) block | embed with two inert states | exact mathematical embedding | pair states treated as two levels | form-only derivation |
| current collective \(L\) | two Kraus pair-loss map | replace a one-excitation collective jump by direct double decay | not equivalent | same M12 label | contradicted |
| (g=0) no pair loss | `f(0)=1e-12` | insert pair-loss mass | not source-supported | mechanism-off | contradicted |

### Operation replay / derivation
| input | transformation | assumption | output | source locator or derivation step | status |
|---|---|---|---|---|---|
| transformed \(g\in[0,1]\) | \(\sum_i K_i^\dagger K_i\) | finite | \(I_4\) to roundoff | effective AD algebra | valid Kraus core |
| (|11\rangle) | code jump (K_1) | jump occurs | (|00\rangle) | direct matrix entry | legacy action |
| (|11\rangle), current (L) | ((\sigma^-_1+\sigma^-_2)|11\rangle) | collective bath | (|01\rangle+|10\rangle) | binding M12 contract | contradiction |
| antisymmetric ((|01\rangle-|10\rangle)/\sqrt2) | current (L) versus legacy map | none | current dark-state signature absent as a discriminating mechanism in legacy pair loss | hand replay | object mismatch |

### Composite compatibility
| component | source | object/device/regime | composition bridge | compatible? | risk |
|---|---|---|---|---|---|
| effective pair AD | SRC-ARSENIJEVIC-ADPD-v1 form only | abstract pair-state two-level system | inert-subspace embedding | algebraically yes | no physical pair mechanism source |
| current M12 | binding prereg; primary sources deferred to Axis-1 Batch 3 | Dicke/shared-bath collapse | reuse legacy adapter | no | direct scientific contradiction |
| probability floor | ECS-NUM-003 | project convention | pair-loss probability | no at zero | mechanism-off destroyed |

### Parameter/value provenance
| parameter | value/units | provenance kind | exact locator | transform | allowed claim | forbidden claim |
|---|---|---|---|---|---|---|
| legacy M12 \(\gamma\) | default 0.01 | project design | adapter line 356 | floor | reproducible legacy toy | collective cooperativity/rate |
| current M12 rate | bracketed/swept separately | current project contract | M12 prereg | Lindblad-time conversion | later Axis-1 claim only | equivalence to this \(\gamma\) |

### Assumptions and correct-place audit
- Assumptions: an abstract direct pair jump and inert single-excitation subspace.
- Simplifications and error bounds: no approximation relates this jump to Dicke collective damping.
- Failure regime: exact mechanism-off and every current M12/shared-bath interpretation.
- Why this formula belongs here: it ships under the retained M12 compatibility label despite an explicit current prohibition.
- Schedule/instrument/record bridge: legacy adapter use is incompatible with the current same-substep joint-collapse object.
- Alternative formulation/invariant: use the collective (L), then test entangled jump target, bright/dark rates, and channel equivalence independently.
- Verdict: mismatched

### Independent checks
| invariant/reference | independent route | falsifier | shared blind spot? | result |
|---|---|---|---|---|
| legacy completeness | hand diagonal sum | non-TP | no | valid after transformed (g) |
| jump target | apply matrices to all basis kets | \(|11\rangle\to|01\rangle+|10\rangle\) | no | code goes directly to \(|00\rangle\) |
| current M12 signature | hand type (\sigma^-\otimes I+I\otimes\sigma^-) | parameter rename suffices | no | operators differ structurally |
| tests | inspect asserted target | current collective oracle | yes | canonical test enshrines legacy object |

### Human verification
- [ ] formula transcription checked
- [ ] exact source page checked
- [ ] symbol/unit convention checked
- [ ] derivation replayed
- [ ] application location checked
- [ ] composite bridge accepted
- Human verdict: unchecked
- Notes: formula correctness is assessed for the public/current M12 claim; the restricted transformed-(g) pair-loss Kraus algebra itself is valid.

## ECS-CHAN-WEAK4-001 — Fixed-unitary I/X/Z synthetic mixture

### Formula and role
- Intended restricted-domain formula:
  $$U=R_Z(0.17)R_X(0.11),$$
  $$K_0=\sqrt{1-2e}\,U,\qquad K_X=\sqrt e\,XU,\qquad K_Z=\sqrt e\,ZU,$$
  $$\mathcal E_e(\rho)=(1-2e)U\rho U^\dagger+eXU\rho U^\dagger X+eZU\rho U^\dagger Z.$$
- Literal code uses \(e=f(\eta)\) and `positive_floor(1-2e)` without enforcing the ideal bound \(e\le1/2\); with \(\epsilon=10^{-12}\), literal TP additionally requires \(e\le(1-\epsilon)/2\).
- Role: channel | synthetic coherent-plus-stochastic stress map
- Scientific object: fixed unitary dressing followed by an I/X/Z Pauli mixture.
- Upstream inputs: eta, RX/RZ primitives, Pauli matrices, numerical floors.
- Downstream consumers: legacy M19 adapter and canonical channel tests.

### Code usage
| frozen file:line | qualname | service/call path | runtime/oracle/test | responsibility |
|---|---|---|---|---|
| `carrier/channels.py:753-761` | `weak_type4_mixing_kraus` | channel_algebra -> M19 adapter | runtime | build fixed U and three scaled Kraus terms |
| `carrier/channels.py:380-381` | M19 dispatch | compatibility catalog | runtime | instantiate default synthetic type-4 channel |
| `tests/test_carrier_channels_units.py:504-507` | weak4 pins | canonical channel_algebra | test-reference | tests only interior eta values and copies fixed constants |

### Symbols, domains, and conventions
| symbol | meaning | shape/domain | units | basis/order | source symbol |
|---|---|---|---|---|---|
| \(e\) | X and Z mixture weight | ideal \(0\le e\le1/2\); literal exact-TP range after flooring is \(10^{-12}\le e\le(1-10^{-12})/2\); code allows to 1 | probability | I/X/Z after common U | none |
| (0.17,0.11) | fixed Z/X rotation angles | real | radians | rightmost RX first | none |
| (1-2e) | identity-arm weight | must be nonnegative | probability | common-U frame | none |

### Evidence verdict
- provenance_status: `COMPOSITE-UNCLOSED`
- required visible risk marker: **高危无出处（组合公式整体无直接出处）**
- formula_correctness: incorrect
- application_fit: mismatched
- value_provenance: project-design
- epistemic_class: generic unitary/Pauli components are standard, but the type-4 composition and constants are unsourced and the accepted domain is non-TP.

### Exact literature sources
| source ID | publication/version | PDF/hash | exact locator | visually checked page | source says | source does not say |
|---|---|---|---|---|---|---|
| SRC-SHELDON-RB-v1 | Sheldon et al., arXiv:1504.06597v1 | manifest artifact | p.2 Eq.1 | yes, prior coordinator check | coherent rotation form | fixed angles or type-4 mixture |
| SRC-HANTZKO-PTM-v2 | Hantzko et al., arXiv:2411.00526v2 | manifest artifact | p.3 Eq.12 | yes, prior coordinator check | operator-sum channel and TP completeness | these weights, three-term support, domain repair, or placement |

### Source-to-code mapping
| source expression | code expression | transformation | exact/approximate | assumption | status |
|---|---|---|---|---|---|
| generic rotations | fixed U | instantiate two axes/angles | exact component algebra | radians | form only |
| generic Kraus completeness | weights (1-2e,e,e) | choose a three-atom mixture | exact for (0\le e\le1/2) before floors | weights sum one | project composition |
| negative (1-2e) for (e>1/2) | `positive_floor` | replace negative weight by (10^{-12}) | invalid extension | accepted by API | contradicted domain |

### Operation replay / derivation
| input | transformation | assumption | output | source locator or derivation step | status |
|---|---|---|---|---|---|
| (e=0.1) | scalar completeness | (1-2e>10^{-12}) | exact TP to roundoff, residual (1.57\times10^{-16}) | coordinator runtime replay | correct interior |
| \(e=(1-10^{-12})/2\) | identity-arm floor meets the unfloored remainder | finite | exact scalar completeness one | hand boundary algebra | literal TP endpoint |
| (e=0.5) | floor zero first weight | none | ((1+10^{-12})I), residual (1.4143393\times10^{-12}) | coordinator replay | non-TP |
| (e=0.75,1) | floor negative first weight, retain (2e) | none | about (1.5I,2I), residuals 0.7071 and 1.4142 | coordinator replay | gross non-TP |
| public eta=0 | floor eta, retain fixed U | eta controls mixture only | nonidentity coherent rotation remains | direct semantic replay | mechanism-off mismatch if eta means total strength |

### Composite compatibility
| component | source | object/device/regime | composition bridge | compatible? | risk |
|---|---|---|---|---|---|
| fixed U | generic rotation sources | coherent qubit operation | common pre-rotation | algebraically yes | angles unsourced |
| I/X/Z mixture | generic Kraus theorem | stochastic Pauli support | project weights (1-2e,e,e) | yes only on restricted domain | no physical type-4 source |
| positive floor | ECS-NUM-002 | numerical convention | attempted extension beyond (e=1/2) | no | destroys TP |

### Parameter/value provenance
| parameter | value/units | provenance kind | exact locator | transform | allowed claim | forbidden claim |
|---|---|---|---|---|---|---|
| angles | 0.17, 0.11 rad | project design | line 755 | none | exact synthetic constants | device calibration |
| M19 eta | default 0.006 | project design | adapter line 381 | floor | reproducible legacy stress value | sourced mechanism strength |
| ideal/literal upper bounds | ideal \(e\le1/2\); literal \(e\le(1-10^{-12})/2\) while the floor remains | algebraic necessity | completeness sum | currently unenforced | precisely restricted valid domain | accepted range to 1 as CPTP |

### Assumptions and correct-place audit
- Assumptions: synthetic channel, finite ideal \(e\in[0,1/2]\), literal floored \(e\le(1-10^{-12})/2\), and fixed U independent of mixture strength.
- Simplifications and error bounds: no physical composition source or approximation target is given.
- Failure regime: literal \(e>(1-10^{-12})/2\) (including \(e=1/2\)), invalid/nonfinite inputs, total-strength interpretation of eta, or device/type-4 claims.
- Why this formula belongs here: it is exposed as M19 and tested by the CORE channel service.
- Schedule/instrument/record bridge: no current physical placement or mechanism-to-observable bridge exists.
- Alternative formulation/invariant: remove the floor on structural weights, preserve exact zero, enforce the ideal \(0\le e\le1/2\), and explicitly classify the channel as synthetic unless sourced.
- Verdict: mismatched

### Independent checks
| invariant/reference | independent route | falsifier | shared blind spot? | result |
|---|---|---|---|---|
| completeness | scalar coefficient sum times \(U^\dagger U\) | sum differs from one | no | literal exact TP iff \(e\le(1-10^{-12})/2\) after the public floor |
| boundary table | direct runtime at .1/.5/.75/1 | test claims all TP | no | reviewer typo risk resolved: .1 passes, .75/1 fail grossly |
| source closure | bounded local/external search | exact type-4 formula | no | none found |
| tests | inspect sampled eta | endpoint/invalid inputs | yes | only 0.006/0.1 interior values |

### Human verification
- [ ] formula transcription checked
- [ ] exact source page checked
- [ ] symbol/unit convention checked
- [ ] derivation replayed
- [ ] application location checked
- [ ] composite bridge accepted
- Human verdict: unchecked
- Notes: **高危无出处（组合公式整体无直接出处）**; (e=0.1) is correctly recorded as TP, not as a failure.

## ECS-CHAN-READOUT-001 — Asymmetric binary assignment matrix

### Formula and role
- Literal row-stochastic matrix:
  $$A_{y,\hat y}=P(\hat y\mid y)=
    \begin{pmatrix}1-p_{0\to1}&p_{0\to1}\\p_{1\to0}&1-p_{1\to0}\end{pmatrix}.$$
  With true/observed states indexed by rows/columns, a row distribution obeys
  (q_{\rm obs}=q_{\rm true}A); a column distribution requires (q_{\rm obs}=A^Tq_{\rm true}).
- Code floors/caps both public error probabilities, so perfect readout returns a live (10^{-12}) symmetric confusion channel.
- Role: classical channel | quantum-instrument-to-bit assignment bridge
- Scientific object: asymmetric binary readout confusion matrix.
- Upstream inputs: `p0_to_1,p1_to_0`, ECS-NUM-003, implicit orientation convention.
- Downstream consumers: M1/M2/M3/M16 adapter results; no installed consumer applying the matrix to a distribution was found.

### Code usage
| frozen file:line | qualname | service/call path | runtime/oracle/test | responsibility |
|---|---|---|---|---|
| `carrier/channels.py:764-767` | `readout_bias_matrix` | channel_algebra -> M1/M2/M3/M16 adapter | runtime | construct row-stochastic assignment matrix |
| `carrier/channels.py:318-330` | readout dispatch branches | compatibility catalog | runtime | return matrix payloads without applying them |
| `tests/test_carrier_channels_units.py:645-659` | readout pins | canonical channel_algebra | test-reference | checks row sums/entries only |
| `tests/test_physical_channels.py:61` | legacy smoke | catalog legacy source | test-reference | ordinary matrix construction only |

### Symbols, domains, and conventions
| symbol | meaning | shape/domain | units | basis/order | source symbol |
|---|---|---|---|---|---|
| (p_{0\to1},p_{1\to0}) | conditional assignment-error probabilities | intended finite \([0,1]\) | probability | true row, observed column | no exact source selected |
| (A) | assignment/confusion matrix | (2\times2), row-stochastic | dimensionless | rows true 0/1; columns observed 0/1 | none |
| (q) | classical probability vector | row or column, must be explicit | probability | matching A orientation | none |

### Evidence verdict
- provenance_status: `NO-SOURCE`
- required visible risk marker: **高危无出处**
- formula_correctness: incorrect
- application_fit: bridge-open
- value_provenance: project-design
- epistemic_class: elementary project convention with no selected exact source; row algebra is correct after transformed inputs, but public zero/invalid semantics and end-to-end orientation are not.

### Exact literature sources
| source ID | publication/version | PDF/hash | exact locator | visually checked page | source says | source does not say |
|---|---|---|---|---|---|---|
| none | bounded RAG/KG/local/external search | none | no exact locator found | n/a | no source selected that fixes this matrix direction, symbols, and floor together | exact convention remains project-defined |

### Source-to-code mapping
| source expression | code expression | transformation | exact/approximate | assumption | status |
|---|---|---|---|---|---|
| no closing source | matrix entries | project definition | exact as code | true-state rows intended | unsourced |
| row-vector propagation | consumer absent | would right-multiply by A | not exercised | orientation must be known | bridge open |
| perfect readout (A=I) | floors both zeros | replace by symmetric (10^{-12}) flips | incorrect public semantics | zero error requested | contradicted internally |

### Operation replay / derivation
| input | transformation | assumption | output | source locator or derivation step | status |
|---|---|---|---|---|---|
| (p_{01}=0.1,p_{10}=0.3) | construct A | rows are true states | `[[.9,.1],[.3,.7]]`, each row sums one | coordinator replay | algebra correct |
| column true state ((1,0)^T) | compare (Aq) and (A^Tq) | column convention | (Aq=(.9,.3)^T) sums 1.2; (A^Tq=(.9,.1)^T) is correct | independent orientation falsifier | bridge open |
| public zeros | floor both to (10^{-12}) | none | `[[1-eps,eps],[eps,1-eps]]`, not identity | coordinator runtime replay | mechanism-off mismatch |
| negative/NaN/\(+\infty\) | probability floor/cap | none | silently repaired to \(\epsilon\)/one | ECS-NUM-003 replay | invalid-domain mismatch |

### Composite compatibility
| component | source | object/device/regime | composition bridge | compatible? | risk |
|---|---|---|---|---|---|
| binary assignment matrix | none closing | classical hard-bit channel | true-to-observed orientation | project-defined | no literature closure |
| probability floor | ECS-NUM-003 | project convention | conditional-error coordinates | no at perfect/invalid inputs | false readout errors |
| quantum measurement | later instrument batches | POVM/instrument outcomes | collapse -> hard bit -> A | not implemented here | end-to-end direction and placement open |

### Parameter/value provenance
| parameter | value/units | provenance kind | exact locator | transform | allowed claim | forbidden claim |
|---|---|---|---|---|---|---|
| M1/M2/M3/M16 defaults | adapter-specific project values | project design | lines 318-330 | probability floor | reproducible compatibility payload | calibrated assignment matrix |
| floor | (10^{-12}) | project design | lines 765-766 | clamp/cap | exact implementation behavior | physical perfect-readout floor |
| orientation | true rows / observed columns | inferred project convention | entry names and row-stochastic tests | transpose for column vectors | explicit local convention | consumer correctness without a call path |

### Assumptions and correct-place audit
- Assumptions: hard binary outcomes, true-state rows, observed-state columns, and a consumer that honors row/right-multiply or transpose/column convention.
- Simplifications and error bounds: no quantum-instrument or soft-readout bridge, calibration provenance, or floor-propagation bound exists.
- Failure regime: perfect readout, invalid/nonfinite inputs, column-left multiplication by A, or interpreting row sums alone as end-to-end correctness.
- Why this formula belongs here: four installed compatibility mechanisms return it as their scientific payload.
- Schedule/instrument/record bridge: bridge-open because no installed application consumer fixes the orientation.
- Alternative formulation/invariant: type the orientation, preserve exact zero, reject invalid inputs, and add an end-to-end normalized-distribution test.
- Verdict: bridge-open

### Independent checks
| invariant/reference | independent route | falsifier | shared blind spot? | result |
|---|---|---|---|---|
| row stochasticity | hand row sums | wrong diagonal | no | correct after transformed inputs |
| consumer orientation | one-hot column propagation | total probability not one | no | A versus (A^T) distinction confirmed |
| perfect-readout identity | exact-zero call | offdiagonal mass | no | false (10^{-12}) flips reproduced |
| tests/callers | call-path scan | actual matrix-vector application | yes | no installed consumer found; tests stop at rows |

### Human verification
- [ ] formula transcription checked
- [ ] exact source page checked
- [ ] symbol/unit convention checked
- [ ] derivation replayed
- [ ] application location checked
- [ ] composite bridge accepted
- Human verdict: unchecked
- Notes: **高危无出处**; no external source was invented for an elementary but convention-sensitive project matrix.

<!-- BATCH-1B2A2-ROWS-END -->

<!--
## <Formula ID> — <name>

### Formula and role
- Normalized formula: $$ ... $$
- Literal code realization:
- Role: mechanism | source | generator | channel | carrier | sampling | instrument |
  record-transform | metric | anchor | bound
- Scientific object:
- Upstream inputs:
- Downstream consumers:

### Code usage
| frozen file:line | qualname | service/call path | runtime/oracle/test | responsibility |
|---|---|---|---|---|

### Symbols, domains, and conventions
| symbol | meaning | shape/domain | units | basis/order | source symbol |
|---|---|---|---|---|---|

### Evidence verdict
- provenance_status:
- required visible risk marker:
- formula_correctness:
- application_fit:
- value_provenance:
- epistemic_class:

### Exact literature sources
| source ID | publication/version | PDF/hash | exact locator | visually checked page | source says | source does not say |
|---|---|---|---|---|---|---|

### Source-to-code mapping
| source expression | code expression | transformation | exact/approximate | assumption | status |
|---|---|---|---|---|---|

### Operation replay / derivation
| input | transformation | assumption | output | source locator or derivation step | status |
|---|---|---|---|---|---|

### Composite compatibility
| component | source | object/device/regime | composition bridge | compatible? | risk |
|---|---|---|---|---|---|

### Parameter/value provenance
| parameter | value/units | provenance kind | exact locator | transform | allowed claim | forbidden claim |
|---|---|---|---|---|---|---|

### Assumptions and correct-place audit
- Assumptions:
- Simplifications and error bounds:
- Failure regime:
- Why this formula belongs here:
- Schedule/instrument/record bridge:
- Alternative formulation/invariant:
- Verdict: matched | mismatched | bridge-open

### Independent checks
| invariant/reference | independent route | falsifier | shared blind spot? | result |
|---|---|---|---|---|

### Human verification
- [ ] formula transcription checked
- [ ] exact source page checked
- [ ] symbol/unit convention checked
- [ ] derivation replayed
- [ ] application location checked
- [ ] composite bridge accepted
- Human verdict: unchecked
- Notes:
-->

## 5. High-risk no-source register

| formula ID | provenance status | mandatory marker | missing edge | downstream propagation | closure search state |
|---|---|---|---|---|---|
| ECS-NUM-001 | NO-SOURCE | 高危无出处 | one \(10^{-12}\) value has no derivation across heterogeneous absolute/relative/physical roles | every service using the shared constant; per-use audit required | local RAG/KG and academic search found no exact source |
| ECS-NUM-002 | NO-SOURCE | 高危无出处 | no source/error bound for the clamp or invalid-input repair | channel coefficients and denominators | open |
| ECS-NUM-003 | NO-SOURCE | 高危无出处 | zero/invalid probabilities are rewritten into live physical mass | all `carrier.channels` consumers; quantified propagation Batch 1B | no exact floor source found |
| ECS-REC-002 | NO-SOURCE | 高危无出处 | exact project flattening/order and geometry coercion have no primary source | every packed record coordinate | order bridge continues in compiler/native/PEPS batches |
| ECS-REC-006 | NO-SOURCE | 高危无出处 | custom LSB/trailing-byte protocol has no exact primary source | PEPS/fused artifacts and downstream records | host/native mirror pending Batch 6 |
| ECS-REC-007 | NO-SOURCE | 高危无出处 | custom permissive inverse/canonical padding policy is unsourced | persisted/native shot loading | open |
| ECS-REC-008 | COMPOSITE-UNCLOSED | 高危无出处（组合公式整体无直接出处） | serialization -> prior boundary -> detector fold -> carrier-specific obs -> product | all packed-carrier metrics/claims | component source exists only for XOR; bridge open |
| ECS-REC-009 | NO-SOURCE | 高危无出处 | raw prefix byte projection has no exact source or current runtime scientific consumer | compatibility only unless later consumed | call-site scan complete; scientific application open |
| ECS-CPTP-NUM-001 | NO-SOURCE | 高危无出处 | complex128/float64 has no global forward-error argument supporting “exact/high-fidelity” language | all channel-algebra residuals and exact-carrier consumers | dtype/use inventory complete; precision convergence open |
| ECS-CPTP-001 | NO-SOURCE | 高危无出处 | unconditional Hermitian projection lacks a sourced roundoff-only applicability bound | exact/fused state actions and any general-operator reuse | non-Hermitian counterexample closed the domain warning; source remains open |
| ECS-CPTP-003 | COMPOSITE-UNCLOSED | 高危无出处（组合公式整体无直接出处） | sourced Born component is composed with an unsourced per-outcome floor and renormalization | exact measurement/reset branches and Axis-1 state evidence | direct Born page verified; smoothing bridge contradicted |
| ECS-CPTP-007 | NO-SOURCE | 高危无出处 | iid Gaussian scale 0.1 has no physical, Haar, or dimension-normalized ensemble source | public random constructor; currently canonical TP-test inputs | call sites complete; physical interpretation forbidden |
| ECS-CHAN-004 | COMPOSITE-UNCLOSED | 高危无出处（组合公式整体无直接出处） | valid random-unitary algebra is composed with an unsourced three-point quadrature, fixed weights, repair policy, and memory-free drift interpretation | retained M13 channel and any drift claim | local RAG found continuous Gaussian quasistatic models instead; exact three-point source not found |
| ECS-CHAN-RESET-001 | ADJACENT-ONLY | 高危无出处（仅有邻近/二手证据） | device reset experiments do not define the project identity/replacement Kraus mixture or target coercion | legacy M17 reset-to-1 compatibility claim | Reed/McEwen pages visually checked; exact channel remains absent |
| ECS-CHAN-LEAKSUR-001 | CONTRADICTED/MISAPPLIED | 高危无出处（文献仅支持形式） | sources support separate qubit AD/PZ forms, not their same-p composition or leakage label | legacy M34 and any leakage interpretation | exact component pages checked; 2D support falsifies leakage |
| ECS-CHAN-CUSTOM-001 | COMPOSITE-UNCLOSED | 高危无出处（组合公式整体无直接出处） | fixed RX/RZ values, order, AD dressing, and M15 placement lack a whole-formula source | optional hard-test channel and any physical interpretation | component sources checked; whole composite not found |
| ECS-CHAN-CORRREL-001 | CONTRADICTED/MISAPPLIED | 高危无出处（文献仅支持形式） | AD form does not source a physical pair-loss embedding, and current M12 requires a different collective jump | legacy M12 adapter versus current Axis-1 M12 | binding prereg explicitly rejects reuse; current primary-source audit deferred to Batch 3 |
| ECS-CHAN-WEAK4-001 | COMPOSITE-UNCLOSED | 高危无出处（组合公式整体无直接出处） | fixed rotation, I/X/Z support, weights, type-4 meaning, and placement have no exact source | legacy M19 and stress-channel claims | bounded search found components only; accepted domain also non-TP |
| ECS-CHAN-READOUT-001 | NO-SOURCE | 高危无出处 | no exact source fixes entry direction, vector orientation, values, and probability floor together | M1/M2/M3/M16 classical payloads and later instrument bridge | RAG/KG/external search found no closing source; no installed consumer applies matrix |

## 6. Contradicted or misapplied register

| formula ID | source/code conflict | failed assumption or placement | affected service/claim | independent falsifier | disposition |
|---|---|---|---|---|---|
| ECS-NUM-003 | standard physical \(p=0\) is rewritten to \(10^{-12}\); negative/NaN and \(>1\) inputs are silently repaired | physical probability domain and mechanism-off controls | channel_algebra and every downstream carrier | live edge table plus acceptance test explicitly pinning absent Pauli mass | mismatched; no source fix made |
| ECS-REC-001 | intended binary/frozen record accepts values congruent to 0/1 mod 256 and remains writable after validation | binary scientific product and immutability assumption | all record-bearing services | reviewer inputs 256/257/-256/-255; post-construction mutation to 7 | incorrect/mismatched |
| ECS-REC-002 | public fold truncates fractional \(R,n_{\rm stab}\) with `int` rather than enforcing the formula domain | positive-integer geometry | public record service | \(R=1.9,n=1.2\) accepted as 1,1 | application mismatched |
| ECS-REC-006 | binary pack input is narrowed before validation | \(\mathbb F_2\) packing domain | PEPS/public pack path | wide signed integer alias test | application mismatched |
| ECS-REC-007 | deserializer narrows wide integers, ignores nonzero padding, and accepts multiple byte strings for one scientific record | canonical byte/load domain | packed record load/access | \([256,257]\) and \([0xFE,0]\) adversarial payloads | application mismatched |
| ECS-REC-008 | `PackedShotBatch.__post_init__` accepts floating payloads by direct uint8 cast; product arrays can later mutate | trusted byte-to-record bridge | fused/PEPS/public construction | \([[0.9,0.9]]\) becomes zero record; writable output test | incorrect/mismatched |
| ECS-CPTP-003 | exact Born zeros acquire probability mass; zero/all-negative trace can become uniform and nonfinite values propagate | structural-zero and valid-density-domain assumptions | exact_qubit_circuit_dm and Axis-1 state evidence | \(|0\rangle\) gives nonzero (p_1); zero/negative/NaN/inf edge table | incorrect/mismatched |
| ECS-CPTP-010 | restricted small coherently-rotated-Pauli PTM statement is generalized to every Kraus channel | incoherent component must be Pauli; nonunital decay excluded | channel-algebra mechanism interpretation | pure amplitude damping at \(\gamma=0.3\) has \(R_{ZI}=0.3\) without a coherent unitary term | incorrect/mismatched |
| ECS-CHAN-005 | sources require a real unit rotation axis, but the public builder accepts zero/tiny axes, case-colliding labels, and identity components that make \(G^2\ne I\) | normalized traceless Pauli-vector premise | channel_algebra public primitive; retained M27 is safe only on its current restricted input | unitarity errors up to \(0.1175789064\) for empty/alias/I inputs | incorrect/mismatched |
| ECS-CHAN-006 | standard stochastic-Pauli zeros/simplex coordinates are replaced by a live \(10^{-12}\) floor, including a second floor on the identity remainder | exact probability simplex, structural zeros, and Kraus completeness | retained M0/M5/M25/M26 channels and zero-sensitive controls | sum-one completeness \(1+10^{-12}\), two-coordinate boundary \(1+2\times10^{-12}\), pure X raises | incorrect/mismatched |
| ECS-CHAN-AD-001 | direct AD has an exact identity at zero, while the callable inserts \(10^{-12}\) damping | mechanism-off and invalid-input domain | M4 and thermal/leakage/custom components | gamma=0 sends \(10^{-12}\) of \(|1\rangle\) population to \(|0\rangle\) | incorrect/mismatched |
| ECS-CHAN-PD-001 | direct source regime has \(g=p/2\le1/2\) and exact completeness; code accepts to one and floors the zero identity arm | positive-time PD range and endpoint TP | leakage-surrogate PZ component | \(g=1\Rightarrow(1+10^{-12})I\); \(g>1/2\) flips coherence sign | incorrect/mismatched |
| ECS-CHAN-PD-002 | derived complete-dephasing endpoint must erase coherence, but code retains a \(10^{-6}\) amplitude and trace excess | structural zero at \(\lambda=1\) | thermal pure-dephasing component | \(|+\rangle\) retains \(5\times10^{-7}\) off-diagonal; completeness diag(1,1+eps) | incorrect/mismatched |
| ECS-CHAN-THERM-001 | valid low-T exponential derivation requires finite \(t\ge0\) and scale-invariant \(T_2\le2T_1\); code accepts negative/NaN/inf time and adds raw-unit slack | Markov/exponential/low-T/common-unit domain | public thermal channel and any T1/T2 claim | zero/negative/NaN time give the same false micro-noise; \(10^{-13},2.5\times10^{-13}\) passes the unphysical guard | incorrect/mismatched |
| ECS-CHAN-EXC-001 | X-conjugated AD has exact zero excitation at input zero; code inserts \(10^{-12}\), and standalone use lacks thermal detailed balance | mechanism-off and full-thermal assumptions | legacy M24 | public zero creates excited population; no paired downward rate | incorrect/mismatched |
| ECS-CHAN-LEAKSUR-001 | a four-Kraus \(2\times2\) AD-after-PZ map is exposed as leakage | leakage requires an enlarged Hilbert space and leakage population | legacy M34 | output support is always \(\operatorname{span}\{|0\rangle,|1\rangle\}\); \(p=1\) is also non-TP | incorrect/mismatched |
| ECS-CHAN-DEP2-001 | direct Eq.1c permits exact zero identity/error weights; code floors both public zero and the identity remainder at one | exact Pauli simplex and endpoint completeness | legacy M9 | \(p=1\Rightarrow(1+10^{-12})I_4\); \(p=0\) is nonidentity | incorrect/mismatched |
| ECS-CHAN-CORRREL-001 | legacy \(|11\rangle\to|00\rangle\) pair loss is not current M12's \(\sigma^-_1+\sigma^-_2\) collective collapse | entangled jump, dark-state, and same-substep joint-collapse contract | legacy M12 label/current Axis-1 M12 claim | current \(L|11\rangle\propto|01\rangle+|10\rangle\), while code jumps directly to \(|00\rangle\) | incorrect/mismatched |

## 7. Cross-source composite register

| formula ID | components | source regimes | unsourced composition edge | compatibility result | risk propagation |
|---|---|---|---|---|---|
| ECS-REC-001 | detector history + carrier-specific logical flip + provenance visibility firewall | detector component: SRC-BKY-DEM-v1; remaining components project-specific | repeated QEC detectors versus multiple carrier instruments | exact combined \(\{det,obs\}\) object and visibility theorem absent | no | implementation also violates binary contract |
| ECS-REC-008 | REC-006/007 serialization + REC-003/004 fold + carrier-specific observable + metadata | mixed primary/project components | fused native and PEPS qutrit carriers | no direct source for the end-to-end mechanism-to-record bridge | no | 高危无出处（组合公式整体无直接出处） |
| ECS-CPTP-003 | computational-basis Born probabilities + shared (10^{-12}) floor + renormalization | pure-state projective measurement versus project numerical convention | valid density-state measurement -> rare-event/record sampling | no source or error bound for rewriting every structural zero before sampling | no | 高危无出处（组合公式整体无直接出处） |
| ECS-CHAN-004 | sourced random-unitary Kraus form + project three-atom support + default weights + invalid-input repair | general discrete CPTP channel versus continuous Gaussian quasistatic rotations | angle distribution -> three-point channel -> retained M13 drift interpretation | no source, moment match, quadrature bound, or temporal-persistence bridge | no | 高危无出处（组合公式整体无直接出处） |
| ECS-CHAN-THERM-001 | direct AD/PD + direct \(\Gamma_2=\Gamma_1/2+\Gamma_\phi\) + project floors/guard | low-temperature exponential Bloch-Redfield regime | rate relation -> Kraus parameters -> PD after AD -> public API | compatible only on finite nonnegative common-unit domain away from floors | no over accepted domain | invalid-time and unit-scaling contradiction |
| ECS-CHAN-RESET-001 | measured active reset + generic replacement channel + project failure-direction model | superconducting reset experiments versus isolated qubit channel | reset instrument/residual population -> identity/replacement mixture -> M17 | no exact bridge | no | 高危无出处（仅有邻近/二手证据） |
| ECS-CHAN-LEAKSUR-001 | direct qubit AD + direct qubit PZ + shared project \(p\) | two separate qubit channels | same-p sequential composition -> M34 leakage label | algebraic interior only; leakage object incompatible | no | 高危无出处（文献仅支持形式） |
| ECS-CHAN-CUSTOM-001 | sourced RX/RZ + direct AD + fixed constants | generic qubit components | fixed U -> AD -> M15 synthetic mechanism | algebraically compatible, physically ungrounded | open | 高危无出处（组合公式整体无直接出处） |
| ECS-CHAN-CORRREL-001 | effective-subspace AD form + project pair embedding + current collective-M12 label | abstract AD versus Dicke/shared-bath relaxation | pair-loss Kraus -> M12 placement | incompatible | no | 高危无出处（文献仅支持形式） plus direct object contradiction |
| ECS-CHAN-WEAK4-001 | sourced rotations + generic Kraus theorem + project I/X/Z weights/constants | generic components | fixed U -> three-arm mixture -> M19 type-4 label | ideal unfloored map permits \(e\le1/2\), but the literal floored map is exactly TP only for \(e\le(1-10^{-12})/2\); whole mechanism ungrounded | no | 高危无出处（组合公式整体无直接出处） |
| ECS-CHAN-READOUT-001 | project binary matrix + probability floor + absent measurement consumer | classical assignment versus quantum instrument | outcome -> hard bit -> oriented matrix application | orientation/placement not closed | open | 高危无出处 |

## 8. Search and closure ledger

| search ID | formula IDs | local RAG query/result | KG query/result | external primary-source search | contrary/no-go search | selected full text | remaining gap |
|---|---|---|---|---|---|---|---|
| S-B1A-REC-001 | ECS-REC-001,003,004,005,008 | `temporal detector XOR consecutive syndrome initial t=0 boundary record fold`; top hit `qec_dem_estimation_syndrome_2504.14643` | concept `detector event`: no match | AnySearch academic queries for detector XOR/initial boundary; official arXiv API exact-ID verification | searched alternative first-round initialization conventions and Fowler's previous-measurement definition | SRC-BKY-DEM-v1; SRC-FOWLER-LEAK-v1 | generic prior, combined obs object, serialization, and carrier bridge remain open |
| S-B1A-NUM-001 | ECS-NUM-001,002,003 | `probability numerical floor epsilon clip zero physical channel Kraus scientific threshold`; no exact floor source | concept `numerical floor`: no match | AnySearch academic searches for quantum-channel epsilon probability floors; results gave standard Kraus forms but no exact project rule | searched zero-probability and invalid-input behavior | none closing | all three rows remain NO-SOURCE |
| S-B1A-PACK-001 | ECS-REC-002,006,007,009 | local code/notes/call-site search | no relevant concept | no exact scientific paper found for custom bytes | checked alternate bit order, padding, dtype, and raw-vs-detector semantics | none closing | project serialization only; native mirror pending |
| S-B1A-CORR-001 | SRC-BKY-DEM-v1, SRC-FOWLER-LEAK-v1 | local PDF/cache metadata | n/a | arXiv API returned v1 only for both; APS issue/article search for DOI | searched correction/erratum/retraction notices | both cached PDFs | no notice found as of freeze; absence is a dated search result, not a perpetual guarantee |
| S-B1B1-CPTP-001 | ECS-CPTP-NUM-001,001,002,004--010 | `Kraus Stinespring Choi vectorization Pauli transfer matrix normalization`; `ecs` lacked `chromadb`, rerun in `aiqec` succeeded; top relevant hit Hantzko note, whose v1 metadata was stale relative to the PDF | concepts `Kraus` and `Pauli transfer`: no match | exact local PDFs plus official arXiv/publisher-title searches | checked non-Hermitian action, Choi factor order, nonunital off-diagonal counterexample, source-version conflict, and correction/withdrawal terms | SRC-HANTZKO-PTM-v2; SRC-KAUFMANN-COH-v3 | precision/error bound and Gaussian-ensemble meaning remain open; publisher correction page was robots-blocked |
| S-B1B1-BORN-001 | ECS-CPTP-003 | `Born computational basis measurement probability zero floor clamp normalization`; no exact floor hit | concept `Born`: only adjacent joint-instrument gap | local full-text selection and exact formula-page inspection | searched structural-zero, invalid density, NaN/inf, and renormalization behavior | SRC-SKINNER-BORN-v4 | Born component closed; floor/composition remains contradicted and unsourced |
| S-B1B2A1-ROT-001 | ECS-CHAN-001,002,005 | `Pauli rotation exp(-i theta P/2) cos sin`; top hits Sheldon, Clader, Kraus-Cirac, and Cartan notes | concepts `Pauli rotation`: no match | AnySearch exact-title/academic search plus official arXiv/APS metadata checks | checked invalid axes, cross-label scope, commutator, half-angle, nonfinite inputs, and source unit-axis premises | SRC-SHELDON-RB-v1; SRC-CLADER-ROT-v2; SRC-KRAUS-CIRAC-v1 | primitive formulas closed; mechanism-specific values/placement remain later-batch work |
| S-B1B2A1-CP-001 | ECS-CHAN-003 | `controlled phase diag(1,1,1,exp(-i theta)) projector`; generic RAG results weak, exact local note/PDF found by text search | concept `controlled phase` and `ZZ coupling`: no match | official arXiv exact-title check for 2408.15402 | explicitly falsified bare-RZZ equivalence and searched local/global-Z decomposition | SRC-PETTERSSON-ZZ-v2 | source-to-matrix closed; retained catalog-M21 placement remains open |
| S-B1B2A1-DRIFT-001 | ECS-CHAN-004,006 | `quasi static coherent drift random unitary three point mixture weights`; closest source uses a continuous Gaussian | concepts `random unitary` and `Pauli channel`: no match | AnySearch primary-title searches and cached full-text selection | negative/NaN/inf weights, nonfinite span, pure-axis/zero Pauli probabilities, continuous-versus-three-atom law | SRC-HANTZKO-PTM-v2; SRC-PATAKI-QSTATIC-v3 | three-point law/defaults/repair/memory bridge remain unsourced; Pauli-floor behavior contradicted |
| S-B1B2A1-CORR-001 | five new source artifacts | local PDF headers/hashes and reading-note metadata | n/a | arXiv/APS exact-title searches | queried correction, erratum, retraction, and version terms | SRC-SHELDON-RB-v1; SRC-CLADER-ROT-v2; SRC-KRAUS-CIRAC-v1; SRC-PETTERSSON-ZZ-v2; SRC-PATAKI-QSTATIC-v3 | no paper-specific notice surfaced as of 2026-07-14; absence remains dated/open |
| S-B1B2A2-DAMP-001 | ECS-CHAN-AD-001; ECS-CHAN-PD-001,002; ECS-CHAN-THERM-001; ECS-CHAN-EXC-001 | `amplitude damping Kraus phase damping T1 T2 exp(-t/T2)`; exact Arsenijević hit plus the local thermal-relaxation note | concept `amplitude damping`: no match | exact-ID/title searches and current official arXiv metadata for 1606.01145 and 1904.06560 | tested zero/one endpoints, negative/NaN/inf time, unit-sensitive T2 slack, source dephasing range, and Krantz's nonexponential/1/f caveat | SRC-ARSENIJEVIC-ADPD-v1; SRC-KRANTZ-QENG-v5 | ideal component/rate formulas closed; probability floor, invalid-domain repair, absolute-unit guard, and full public composite remain unsupported or contradicted |
| S-B1B2A2-RESET-001 | ECS-CHAN-RESET-001; ECS-CHAN-LEAKSUR-001; ECS-CHAN-READOUT-001 | reset/readout queries found no exact replacement-mixture or oriented confusion-matrix formula | `readout` returned an unrelated syndrome-bias observable; `leakage` returned broad adjacent concepts only | exact-ID/title searches for the Reed and McEwen reset experiments | searched exact Kraus mixture, strict target domain, enlarged leakage support, and row/column probability-vector orientation | SRC-REED-RESET-v2; SRC-MCEWEN-RESET-v1 | reset evidence is adjacent only; the project mixture, two-dimensional leakage label, matrix orientation, values, and floors remain unclosed |
| S-B1B2A2-DEP-001 | ECS-CHAN-DEP2-001 | local Kam note/PDF gave the exact 15-nonidentity-Pauli convention | no exact equation-bearing match | official arXiv exact-ID/title/version search for 2410.23779 | checked p-versus-replacement convention, p=0/1 endpoints, and correction/withdrawal terms | SRC-KAM-NM-v4 | ideal Eq.1c is direct; public probability-floor endpoint behavior remains contradicted |
| S-B1B2A2-SYNTH-001 | ECS-CHAN-CUSTOM-001; ECS-CHAN-CORRREL-001; ECS-CHAN-WEAK4-001 | synthetic/composite queries returned only component-level thermal/rotation material, not these whole formulas | broad leakage/shared-bath concepts only; no exact composite | bounded exact-phrase and mechanism-object search; no closing primary source selected | checked eta=0 semantics, weak4 TP domain, pair-loss versus collective collapse, fixed constants, and composition order | component sources only; no whole-formula artifact | custom and weak4 remain COMPOSITE-UNCLOSED; pair-loss placement is contradicted by the current M12 object |
| S-B1B2A2-CORR-001 | five new source artifacts | local PDF headers/hashes and reading-note metadata | n/a | current official arXiv pages plus journal/DOI metadata checks | queried versions, corrections, retractions, and withdrawals; 1606.01145 carries an arXiv overlap admin note and says its text was corrected | SRC-ARSENIJEVIC-ADPD-v1; SRC-KRANTZ-QENG-v5; SRC-KAM-NM-v4; SRC-REED-RESET-v2; SRC-MCEWEN-RESET-v1 | no withdrawal surfaced as of 2026-07-14; absence remains dated/open and the Arsenijević admin note is preserved explicitly |

An unavailable paper, supplement, or search service is recorded as `open`, not converted into a
field-level absence claim.

## 9. Source-artifact manifest

### 9.1 Frozen code and control artifacts

| artifact set | count | manifest/content SHA256 | status |
|---|---:|---|---|
| installed Python modules | 109 | `9feb60b7d8bb33f3618dd6fb99ba3f732b39a7afed7e6766519dc8db5d2e3366` | frozen |
| installed native sources | 4 | `614e7b9f607e10d20c58834c96addc107e1e0929f69dd7a3a0f1a8c5807fd3cf` | frozen |
| installed source union | 113 | `42c7557c05cae70961bb36571a347ed82940f4518bd4a544ea7366fe094a0656` | frozen |
| complete `tests/**/*.py` tree | 143 | `854f17e2397f7cc8458ffc9bf74c5a4d350d5b86a4b3a301bc335706768c1428` | frozen |
| service catalog | 1 | `f0159cd1d2fc1a8a1678a0aff7c642cc9c6e43bf3cf2905ab27ace126e7b5878` | frozen |
| code map | 1 | `80b0ab178d6db7f017ebd81ffbf875a406d2fa81a2087218218bd4d0518d5a4d` | frozen |

The final Batch 13 appendix expands the aggregate code manifests to every path and hash. Each
load-bearing primary-source PDF is added below when its equation page has been visually checked.

### 9.2 Literature artifacts

| source ID | local PDF | SHA256 | publication/version | correction/retraction check | formula IDs | visual verification |
|---|---|---|---|---|---|---|
| SRC-BKY-DEM-v1 | `docs/papers/qec_dem_estimation_syndrome_2504.14643.pdf` | `5e821a6a951a4ef342ddb80caf53e62bd8869af25a4f39ad5d6de8f4b8336bbd` | Robin Blume-Kohout and Kevin Young, *Estimating detector error models from syndrome data*, arXiv:2504.14643v1 (2025), preprint, no DOI listed | arXiv API exact ID: v1 only and no notice found, checked 2026-07-14 | ECS-REC-001,003,004,005,008 | PDF index 1/printed p.2 Sec.1.2+footnote 2 and index 2/printed p.3 Fig.1 visually checked |
| SRC-FOWLER-LEAK-v1 | `docs/papers/fowler_leakage_topological_codes_1308.6642.pdf` | `8450cca9581beb0cb1a6d3d990a47808bc2177e30402b3129b7a09d7abfaf59a` | Austin G. Fowler, *Coping with qubit leakage in topological codes*, arXiv:1308.6642v1; Phys. Rev. A 88, 042308 (2013), DOI 10.1103/PhysRevA.88.042308 | arXiv v1; APS article/issue search found no paper-specific correction/retraction notice, checked 2026-07-14 | ECS-REC-003 (corroborating/adjacent) | PDF index 0/printed p.1 and index 1/printed p.2 Sec.I/Figs.2-3 visually checked |
| SRC-HANTZKO-PTM-v2 | `outputs/papers/2411.00526.pdf` | `dd0421cc45fcb0e95caf803ee568720aefec6319c9015f18f5c8e6f1ef812d0a` | Lukas Hantzko, Lennart Binkowski & Sabhyata Gupta, *Fast generation of Pauli transfer matrices utilizing tensor product structure*, arXiv:2411.00526v2; Phys. Scr. 100, 075125 (2025), DOI 10.1088/1402-4896/ade8b3 | targeted arXiv/title/correction search found no paper-specific notice; publisher article was robots-blocked, so status remains dated/open, checked 2026-07-14 | ECS-CPTP-002,004--006,008,009; ECS-CHAN-001,004,006; component support for ECS-CHAN-WEAK4-001 | PDF index 1/printed p.2 basis convention and index 2/printed p.3 Eqs.2--3,8--12 visually checked; local reading note's v1 tag is stale |
| SRC-KAUFMANN-COH-v3 | `docs/papers/coherent_robust_pauli_2307.08741.pdf` | `6054774681b301ab7d627cd424b23b9881478547fa45ea268035453afbaffd80` | Noah Kaufmann, Ivan Rojkov & Florentin Reiter, *Characterization of coherent errors in gate layers with robustness to Pauli noise*, arXiv:2307.08741v3 (2025), preprint | current arXiv page/PDF show v3 and no withdrawal stamp; paper-specific correction status otherwise open, checked 2026-07-14 | ECS-CPTP-008--010 | PDF index 2/printed p.3 Sec.III/Eq.4 and small-error/model limits visually checked |
| SRC-SKINNER-BORN-v4 | `docs/papers/skinner_ruhman_nahum_measurement_induced_transitions_1808.05953.pdf` | `83c71cb8498aacc6fa05795f30738d371d4916886558d4cdb469027154a0ffad` | Brian Skinner, Jonathan Ruhman & Adam Nahum, *Measurement-Induced Phase Transitions in the Dynamics of Entanglement*, arXiv:1808.05953v4 (2019) | correction/retraction search not yet closed; status open | ECS-CPTP-003 | PDF index 2/printed p.3 Sec.II Born outcome probabilities and post-measurement renormalization visually checked |
| SRC-SHELDON-RB-v1 | `outputs/papers/1504.06597.pdf` | `609232d9fc4f3066aec0bc520174e88107ed4444e70dcfec3e05e164f589f7c9` | Sarah Sheldon et al., *Characterizing errors on qubit operations via iterative randomized benchmarking*, arXiv:1504.06597v1; Phys. Rev. A 93, 012301 (2016), DOI 10.1103/PhysRevA.93.012301 | exact-title arXiv/APS search found no paper-specific correction/retraction notice, checked 2026-07-14 | ECS-CHAN-001,005; component support for ECS-CHAN-CUSTOM-001 and ECS-CHAN-WEAK4-001 | PDF index 1/printed p.2 Eq.1 and symbol definitions visually checked |
| SRC-CLADER-ROT-v2 | `outputs/papers/2101.11631.pdf` | `406484c2c0cb1d9450c45df793d8a57763ea488a1c8767a6d851bb99d521c521` | B. D. Clader et al., *Impact of correlations and heavy tails on quantum error correction*, arXiv:2101.11631v2; Phys. Rev. A 103, 052428 (2021), DOI 10.1103/PhysRevA.103.052428 | exact-title arXiv/APS search found no paper-specific correction/retraction notice, checked 2026-07-14 | ECS-CHAN-001,005 | PDF index 1/printed p.2 Eq.1 and unit-real-axis sentence visually checked |
| SRC-KRAUS-CIRAC-v1 | `outputs/papers/quant-ph/0011050.pdf` | `34114cd648ada331e10e832ceae6dbb9e01b59eea09983b27f99fb8062df8dc5` | Barbara Kraus & J. Ignacio Cirac, *Optimal Creation of Entanglement Using a Two-Qubit Gate*, arXiv:quant-ph/0011050v1; Phys. Rev. A 63, 062309 (2001), DOI 10.1103/PhysRevA.63.062309 | exact-title arXiv/APS search found no paper-specific correction/retraction notice, checked 2026-07-14 | ECS-CHAN-001,002 | PDF index 4/printed p.5 Eqs.24,26 and commuting-generator sentence visually checked |
| SRC-PETTERSSON-ZZ-v2 | `outputs/papers/2408.15402.pdf` | `4a21b457f6b0d012bd1347cb42996bc9f03cbde772213095826a0549a199deb2` | Simon Pettersson Fors, Jorge Fernández-Pendás & Anton Frisk Kockum, *Comprehensive explanation of ZZ coupling in superconducting qubits*, arXiv:2408.15402v2 (2024), preprint | official arXiv exact-title search showed v2 artifact and no withdrawal/correction notice, checked 2026-07-14 | ECS-CHAN-003 | PDF index 3/printed p.4 Eq.6, phase integral, and CPHASE paragraph visually checked |
| SRC-PATAKI-QSTATIC-v3 | `outputs/papers/2401.04530.pdf` | `b6d065c0ebc14d0c17347686aa49ae1333440178aa1b86aea54b917ca127e4ac` | Dávid Pataki, Áron Márton, János K. Asbóth & András Pályi, *Coherent errors in stabilizer codes caused by quasistatic phase damping*, arXiv:2401.04530v3; Phys. Rev. A 110, 012417 (2024), DOI 10.1103/PhysRevA.110.012417 | exact-title arXiv/APS search found no paper-specific correction/retraction notice, checked 2026-07-14 | ECS-CHAN-004,006 | PDF index 2/printed p.3 Eqs.5,8--11, including continuous Gaussian density, visually checked |
| SRC-ARSENIJEVIC-ADPD-v1 | `outputs/papers/1606.01145.pdf` | `32e3d12077bef0b1e6eb84f2f85f5bc35fc1fce6b5f9a3e58c625cf902ee0694` | Milan Arsenijević & Nikola Banković, *Microscopic derivation of the one qubit Kraus operators for amplitude and phase damping*, arXiv:1606.01145v1; Kragujevac J. Sci. 38, 41--52 (2016) | current arXiv page says the text was corrected and carries an administrator note about substantial text overlap; no withdrawal surfaced, checked 2026-07-14 | ECS-CHAN-AD-001; ECS-CHAN-PD-001,002; ECS-CHAN-THERM-001; ECS-CHAN-EXC-001; component support for ECS-CHAN-LEAKSUR-001, ECS-CHAN-CUSTOM-001, and ECS-CHAN-CORRREL-001 | PDF index 3/printed p.4 Eqs.13--14, index 4/printed p.5 Eq.17, and index 12/printed p.13 Eqs.53--57 visually checked |
| SRC-KRANTZ-QENG-v5 | `outputs/papers/1904.06560.pdf` | `7925f8e9ee45eac83142ec8862d12e2728e6913ac26b2f912f72ecdadca2f10d` | Philip Krantz et al., *A quantum engineer's guide to superconducting qubits*, arXiv:1904.06560v5; Appl. Phys. Rev. 6, 021318 (2019), DOI 10.1063/1.5089550 | current arXiv page shows v5 and no withdrawal; publisher correction status remains dated/open, checked 2026-07-14 | ECS-CHAN-THERM-001 | PDF index 13/printed p.14 Eqs.41--45 and index 15/printed p.16 nonexponential/1/f applicability caveat visually checked |
| SRC-KAM-NM-v4 | `outputs/papers/2410.23779.pdf` | `9f7bfb374110dc76df3a60a0af3e16f64347ad80de999a2fce687d88936866bf` | John F. Kam et al., *Detrimental non-Markovian errors for surface code memory*, arXiv:2410.23779v4; Quantum Sci. Technol. 10 (3), 035060 (2025), DOI 10.1088/2058-9565/adebab | current arXiv page shows v4 and no withdrawal/correction notice, checked 2026-07-14 | ECS-CHAN-DEP2-001 | PDF index 2/printed p.3 Eq.1c visually checked |
| SRC-REED-RESET-v2 | `outputs/papers/1003.0142.pdf` | `c607ac9932726d7ff5bba1a8f533ce1e04f285dde1a4d27adc540f112d873a42` | M. D. Reed et al., *Fast reset and suppressing spontaneous emission of a superconducting qubit*, arXiv:1003.0142v2; Appl. Phys. Lett. 96, 203110 (2010), DOI 10.1063/1.3435463 | current arXiv page shows v2 and no withdrawal notice, checked 2026-07-14 | ECS-CHAN-RESET-001 (adjacent only) | PDF index 0/printed p.1 reset protocol and approximately 99.9 percent ground-state preparation claim visually checked; no identity/replacement Kraus mixture is supplied |
| SRC-MCEWEN-RESET-v1 | `docs/papers/mcewen_removing_leakage_correlated_2102.06131.pdf` | `93d0488667b5e5ba908898d7efe4e69f6fcf6575b382c2116b1bec7676a182e2` | Matt McEwen et al., *Removing leakage-induced correlated errors in superconducting quantum error correction*, arXiv:2102.06131v1; Nat. Commun. 12, 1761 (2021), DOI 10.1038/s41467-021-21982-y | current arXiv page shows v1 and no withdrawal notice, checked 2026-07-14 | ECS-CHAN-RESET-001 (adjacent only) | PDF index 2/main printed p.3 Fig.2 reset performance and PDF index 9/supplement printed p.3 Fig.S3 computational-error-dominant behavior visually checked; no identity/replacement Kraus mixture is supplied |

## 10. Service and module coverage summary

| service/status | scientific surfaces | source modules | formula IDs or no-formula disposition | verification surface | coverage state |
|---|---|---|---|---|---|
| shared_numerical_policy / support | shared numerical zero and clamp maps | `numerics.py` | ECS-NUM-001--003 | edge-domain replay; downstream use scan | Batch 1A complete at definition level; consumer-specific audit pending |
| record_contract_and_packing / CORE | binary record object, temporal fold, raw packing, raw-to-product bridge, prefix bytes | `carrier/__init__.py`, `record_fold.py`, `records.py` | ECS-REC-001--009 | canonical tests + exhaustive GF(2) + independent manual packer + adversarial validation probes | Batch 1A formulas reviewed; implementation/source findings open |
| channel_algebra / CORE (sub-batch 1B1) | Hermitian/Kraus action, Z probabilities, TP/Choi/Stinespring/PTM and diagnostic claims | `carrier/cptp_channel.py` | ECS-CPTP-NUM-001; ECS-CPTP-001--010 | source-page visual checks; hand Choi SWAP/Stinespring/PTM/Born/domain falsifiers; test-independence audit; targeted canonical run `10 passed` | module fully enumerated/reviewed; `channels.py` and `mechanisms/teachers.py` construction formulas remain Batch 1B2 |
| channel_algebra / CORE (sub-batch 1B2a1) | Pauli rotations, RXX/RYY composition, conditional phase, drift mixture, arbitrary axis, stochastic Pauli | `carrier/channels.py:415-521,770-784` | ECS-CHAN-001--006; `_axis_unitary` inspected-no-formula dispatch | four source-page visual checks; independent commutator/projector/axis/TP/nonfinite replays; canonical run `71 passed` | scoped 14 qualnames fully enumerated/reviewed; damping/leakage/readout/adapter/metadata partitions remain Batch 1B2 |
| channel_algebra / CORE (sub-batch 1B2a2) | amplitude/phase damping, zero-temperature T1/T2 composite, upward excitation, reset, qubit leakage surrogate, synthetic channels, two-qubit depolarizing, legacy pair loss, and readout matrix | `carrier/channels.py:522-604,724-769` | ECS-CHAN-AD-001; ECS-CHAN-PD-001,002; ECS-CHAN-THERM-001; ECS-CHAN-EXC-001; ECS-CHAN-RESET-001; ECS-CHAN-LEAKSUR-001; ECS-CHAN-CUSTOM-001; ECS-CHAN-DEP2-001; ECS-CHAN-CORRREL-001; ECS-CHAN-WEAK4-001; ECS-CHAN-READOUT-001; linked ECS-NUM-003 and ECS-CHAN-001 | five source artifacts visually checked; independent completeness/action/domain/orientation replays; test-independence audit; canonical run `71 passed` | scoped 12 callables fully enumerated/reviewed; qutrit/Wood--Gambetta, compatibility adapter, and metadata partitions remain Batch 1B2 |
| fused_within_cycle / CORE | native producer of REC-006/008 bytes | `within_cycle.py`, native kernel | linked ECS-REC-006/008; native formulas pending | current header/shape path inspected | partial; Batch 6 owns mirror equivalence |
| peps_single_wire / CORE | Python producer of REC-006/008 bytes | `peps/trajectory.py` | linked ECS-REC-004/006/008; carrier formulas pending | current codestate/pack call path inspected | partial; Batch 8 owns instrument/carrier |
| remaining services | pending sequential batches | pending | pending | pending | not started |

## 11. Reverse coverage — 109 Python modules

The per-file SHA256 is also the expanded source-artifact manifest for the installed Python
distribution. Catalog ownership, scientific disposition, and row links are filled as each
extractor-reviewer gate closes.

| frozen path | SHA256 | catalog owner/support class | scientific-formula disposition | formula IDs | reviewer coverage | notes |
|---|---|---|---|---|---|---|
| `src/error_coupling_simulator/__init__.py` | `041223a2b164011d33a61463b31efa819b3ad9a7c3cdf60e206b2330c7afa539` | `support:namespace_and_public_facades` | pending | pending | pending | |
| `src/error_coupling_simulator/carrier/__init__.py` | `461cfd85391df894491df6ed627daa8b4c487d14bd48963bf010182f53a2bdcd` | `service:record_contract_and_packing` | facade only: record re-exports audited; within-cycle re-exports belong to Batch 6 | ECS-REC-001--009 for re-exported record API | Batch 1A reviewed; whole facade partial | no independent formula |
| `src/error_coupling_simulator/carrier/accel.py` | `95717be503538f26beb94b05c88679b7063d95c2bc3ce2036c94856ed3aac73d` | `support:exact_qubit_native_acceleration` | reuses the Hermitian-domain Kraus/postprojection convention; fused arithmetic/gradient mirror pending Batch 6 | ECS-CPTP-001,002 (shared convention) | Batch 1B1 call path inspected; module partial | native/fused independence not pre-cleared |
| `src/error_coupling_simulator/carrier/channels.py` | `b86dd3b1758100f04996e3de1593c7dc76adda88a39c72abdbe2470cefcf60a9` | `service:channel_algebra` | reviewed partitions at lines 415--604 and 724--784 fully classified: 18 formula rows plus `_axis_unitary` inspected-no-formula dispatch; qutrit/Wood--Gambetta lines 606--721, compatibility adapter lines 1--414, and metadata after line 784 remain pending | ECS-CHAN-001--006; ECS-CHAN-AD-001; ECS-CHAN-PD-001,002; ECS-CHAN-THERM-001; ECS-CHAN-EXC-001; ECS-CHAN-RESET-001; ECS-CHAN-LEAKSUR-001; ECS-CHAN-CUSTOM-001; ECS-CHAN-DEP2-001; ECS-CHAN-CORRREL-001; ECS-CHAN-WEAK4-001; ECS-CHAN-READOUT-001; linked ECS-NUM-001--003 | Batch 1B2a1 and 1B2a2 extractor + independent reviewer gates complete; module partial | floors contradict structural endpoints; qubit leakage and current-M12 labels are mismatched; several synthetic composites remain unsourced |
| `src/error_coupling_simulator/carrier/cptp_channel.py` | `865939931d00ccb2104583e60ab396ba953a6157715baa658d456198da028097` | `service:channel_algebra` | all 10 callable qualnames and module-level accuracy/CPTP claims classified; `parameters` is optimizer-list plumbing only | ECS-CPTP-NUM-001; ECS-CPTP-001--010 | Batch 1B1 extractor + independent reviewer complete | Born floor and coherence certificate contradicted; Choi SWAP/domain limits explicit |
| `src/error_coupling_simulator/carrier/exact/__init__.py` | `c5e11e6fc32f0ab2947c26d8295ce0ee8a94da1ef2d873c88ea3d5f03f51040c` | `support:namespace_and_public_facades` | pending | pending | pending | |
| `src/error_coupling_simulator/carrier/exact/circuit_sim.py` | `21c2f15035901fd7454a16eef6be8f8bd2aa1f0ad6f672c89d92d8f5ac7e1ed0` | `service:exact_qubit_circuit_dm` | consumes shared Hermitian/Kraus/Born formulas; own unitary/embed/instrument evolution pending Batch 1C | ECS-CPTP-001--003 | Batch 1B1 call path inspected; module partial | floor propagates into measurement/reset |
| `src/error_coupling_simulator/carrier/exact/qutrit_dm.py` | `657574cf25d94f17d8755c51327541df087edfa3ef21164860c66a66f59b77f0` | `service:exact_qutrit_dm,ququart_cz_transport` | consumes Hermitian projection; qutrit evolution/instrument formulas pending Batch 5 | ECS-CPTP-001 | Batch 1B1 call path inspected; module partial | blocked mirror shares formula, not independent evidence |
| `src/error_coupling_simulator/carrier/joint_lindbladian.py` | `8e6b39201ed547ae7aa93092a44729b89b26fcda5a036a1e2c60d1e9060352c9` | `service:axis1_joint_channel` | pending | pending | pending | |
| `src/error_coupling_simulator/carrier/kernels/__init__.py` | `7d09d5d41adb882a456460b4ca50c7e44ab3e7d023587475d9dd355befb3fe06` | `support:namespace_and_public_facades` | pending | pending | pending | |
| `src/error_coupling_simulator/carrier/kernels/qutrit_mcwf_ops_loader.py` | `5eaaed27cb414f1095e8401efa810b50dac31e2985bef34786a913fe185d23a3` | `service:dense_qudit_mcwf_carrier` | pending | pending | pending | |
| `src/error_coupling_simulator/carrier/kernels/sv_traj_d3_loader.py` | `ab72bed88123fb957d80e5ebf63940a00a92ef3686f3e171f782141927ebeea3` | `service:fused_within_cycle` | pending | pending | pending | |
| `src/error_coupling_simulator/carrier/pepo/__init__.py` | `29d2d572b5761b3eed5bfa9b143cc8fbfcabc49fdbb675c1a5e07a611557d424` | `service:pepo_findings` | pending | pending | pending | |
| `src/error_coupling_simulator/carrier/pepo/dynamics.py` | `8abdd80b6a4eec27f851842b5f70af809ab64d5df22560bfe613bfcf93e2f4f4` | `service:pepo_findings` | pending | pending | pending | |
| `src/error_coupling_simulator/carrier/pepo/layout.py` | `191d3f6b952f3c25f3c64eaea84c38e4d2bde8061d2cb73844d8bee7fdc56972` | `service:pepo_findings` | pending | pending | pending | |
| `src/error_coupling_simulator/carrier/pepo/sampler.py` | `9bdbdaa50d6c73fd79e8b7e8cbed7df6689d5334d6342c5ee8d160233e2ed721` | `service:pepo_findings` | pending | pending | pending | |
| `src/error_coupling_simulator/carrier/peps/__init__.py` | `f19fb1e236cf5620ac4c411b82f8e1c19a5663a365451031c985d9e587f6d7df` | `service:peps_single_wire` | pending | pending | pending | |
| `src/error_coupling_simulator/carrier/peps/contraction.py` | `50341e3c312561cd025e9a6ddd6146ce303c3815ab1fbff15e379294f52d2f0c` | `service:peps_single_wire` | pending | pending | pending | |
| `src/error_coupling_simulator/carrier/peps/diagnostics.py` | `4f2c28a0fb2a7718b56a21ac3a500affe6f6e5ed5cc4c2a98a55c7476e07d741` | `service:peps_single_wire` | pending | pending | pending | |
| `src/error_coupling_simulator/carrier/peps/fet.py` | `499217410f02b47415eb3ccd7e9469b2c17cdf16927b74d9ceab3c4e0f767e1a` | `service:peps_single_wire` | pending | pending | pending | |
| `src/error_coupling_simulator/carrier/peps/sampling_maps.py` | `4348befe4571a99da4d1945a59999c20aab56dd9c16e237f0fb1f1f34c9d4dd0` | `service:peps_single_wire` | pending | pending | pending | |
| `src/error_coupling_simulator/carrier/peps/stab_tt.py` | `2b353b7df16cd5139efd5910b1fd6512789012cdc0de0bb072f0fdaa702decb3` | `service:peps_single_wire` | pending | pending | pending | |
| `src/error_coupling_simulator/carrier/peps/state.py` | `f262d30fb371e64bd9ec8527ca6f07bfb5cbc5d9ab4284be479a011162627733` | `service:peps_single_wire` | pending | pending | pending | |
| `src/error_coupling_simulator/carrier/peps/trajectory.py` | `39cfd3485594c9cb43b429f6958fa0f518845664813a05af584cf779f88c3d74` | `service:peps_single_wire` | pending | pending | pending | |
| `src/error_coupling_simulator/carrier/record_fold.py` | `beb923f486312e6b79f974afe22a26049cfcb48cf231ec680c6b4cfaa3d7f4da` | `service:record_contract_and_packing` | scientific formulas audited; valid-domain algebra passes, public domain/first-boundary bridge open | ECS-REC-002--005 | Batch 1A reviewed | nonbinary/fractional geometry accepted |
| `src/error_coupling_simulator/carrier/records.py` | `f38ed11b252cc86c693adb8d9171319dd3348d2a6499aa999412a946b073370d` | `service:record_contract_and_packing` | scientific record/packing formulas audited; validators and composite bridge contradicted | ECS-REC-001,002,006--009 | Batch 1A reviewed | uint8 wrap, mutable arrays, permissive payload/padding |
| `src/error_coupling_simulator/carrier/within_cycle.py` | `1fab8f6fe971fb38a7ff12cc0d488bcac928f7baab60925d00783c283f324712` | `service:fused_within_cycle` | pending | pending | pending | |
| `src/error_coupling_simulator/certify/__init__.py` | `b4dd6f6ecdc75953e46ffbef1dca0ffd15eb193c4a0a1928001efb78bfa3d84f` | `support:namespace_and_public_facades` | pending | pending | pending | |
| `src/error_coupling_simulator/certify/anchors/__init__.py` | `8171e90a1fa9c34034180bad79b563343cda5eb0b8d66125bd84d489645712c5` | `service:formal_certification` | pending | pending | pending | |
| `src/error_coupling_simulator/certify/anchors/closed_form.py` | `3daf8a10aab1a7971f4fdac10af68f3a94e6e9c6fd237bacd94f01cee9931937` | `service:formal_certification` | pending | pending | pending | |
| `src/error_coupling_simulator/certify/anchors/controls.py` | `a0416346c53b64cbb9986794fddd5b1244e8bb6bae1dc2397bd46de09f008746` | `service:formal_certification` | pending | pending | pending | |
| `src/error_coupling_simulator/certify/anchors/dm_oracle.py` | `8a96c0d9d5837b5c6b51a3ab3c5fb5eaba302791a4211d3c6be5190cd504b036` | `service:formal_certification` | pending | pending | pending | |
| `src/error_coupling_simulator/certify/anchors/stim_clifford.py` | `52d5117645c940dbc268c5b97f03cc98ae0c3e393c4b1666c9f424f92965164b` | `service:formal_certification` | pending | pending | pending | |
| `src/error_coupling_simulator/certify/channel_diagnostics.py` | `a30392e35a6dfa14b6607237458b5af66bd6e60d7c0c9f154fa03049656910f7` | `service:channel_diagnostics` | pending | pending | pending | |
| `src/error_coupling_simulator/certify/core.py` | `5beef56a38bbd6f7afae0dfa09f761122c008320bbdd12e6e81140739cc213f8` | `service:formal_certification` | pending | pending | pending | |
| `src/error_coupling_simulator/certify/facade.py` | `ad65e73af7722161c003216f3dbfefe1b38f25bc9e5aa9c5d9a96d193ea35771` | `service:formal_certification` | pending | pending | pending | |
| `src/error_coupling_simulator/certify/types.py` | `d10adaef78cb7a40b70675b8012dbc0761c28854150d6b961506ed62dd7662fa` | `service:formal_certification` | pending | pending | pending | |
| `src/error_coupling_simulator/frontend/__init__.py` | `132213f068176e9ec98f533391708fc1b108bc41a0069808d6ab3cc5ad4b217f` | `support:namespace_and_public_facades` | pending | pending | pending | |
| `src/error_coupling_simulator/frontend/analog_schedule.py` | `cc2aa06ff6dbc956a84363bc52cde011ce35008802cf822950ceca0f75ebb38b` | `service:axis1_schedule_adapter` | pending | pending | pending | |
| `src/error_coupling_simulator/frontend/artifacts.py` | `dfbc90cbd3d8670e586ab46147ac5dc1e0719b0a5a74de822a4aa8340dfd4895` | `support:frontend_artifact_and_schema_support` | pending | pending | pending | |
| `src/error_coupling_simulator/frontend/axis1_bridge.py` | `fbeb924255db1d71e12a5da66888fba11dc4dfd895c031d6a9f156598b0b8018` | `support:axis1_ir_selection_and_evidence_support` | pending | pending | pending | |
| `src/error_coupling_simulator/frontend/axis1_carrier_execution.py` | `2b974845eed13da8290b47b4b2de61448b52367747e32aad388b673ec4b50735` | `service:axis1_dense_jointl_record` | pending | pending | pending | |
| `src/error_coupling_simulator/frontend/axis1_carrier_program.py` | `267ac5e23d590d95915bffb271563c10fa203353f6dd921a402424019e618545` | `support:axis1_ir_selection_and_evidence_support` | pending | pending | pending | |
| `src/error_coupling_simulator/frontend/axis1_channel_evidence.py` | `0b1f85f8a7d2f6c2391403279c233d48c9eee701e09f74cdd4be08d838c1c2cb` | `service:axis1_joint_channel` | pending | pending | pending | |
| `src/error_coupling_simulator/frontend/axis1_codespec_runner.py` | `38aa269fcdcd5a6c827072a3eb439914afb87f774a8f89465bcb31059edfe571` | `support:internal_evidence_runners` | pending | pending | pending | |
| `src/error_coupling_simulator/frontend/axis1_context.py` | `94c4ca089180b8b951ed6bb76d96f0651bec6b648e51086abe2f667e57cef6be` | `support:axis1_ir_selection_and_evidence_support` | pending | pending | pending | |
| `src/error_coupling_simulator/frontend/axis1_evidence_guard.py` | `99b6830a999619437fe65906f7479ff53dc3f758622badb1664a95c5ec341ce4` | `support:axis1_ir_selection_and_evidence_support` | pending | pending | pending | |
| `src/error_coupling_simulator/frontend/axis1_g2_runner.py` | `28a785b08990e56acf0013c89b38d9027a3b688bdc29e3fd0976f33830d1199d` | `support:internal_evidence_runners` | pending | pending | pending | |
| `src/error_coupling_simulator/frontend/axis1_ideal_controls.py` | `d11d22110df8fec0b792bfb311b1b9bc51fa9866744ffa8eab08c5284d98d973` | `support:axis1_ir_selection_and_evidence_support` | pending | pending | pending | |
| `src/error_coupling_simulator/frontend/axis1_mcwf_dense_certification.py` | `edfa5a4e3feffb0a09337dce1293a4755b1435dfdc4630295878e32a0426e94f` | `support:axis1_certification_harnesses` | pending | pending | pending | |
| `src/error_coupling_simulator/frontend/axis1_mcwf_mps_contract.py` | `c5dcc1975599e7a7b3305efd92b66721f500067605ff88ec7a1b6279080f62a3` | `service:restricted_axis1_1d_mps` | pending | pending | pending | |
| `src/error_coupling_simulator/frontend/axis1_mcwf_mps_execution.py` | `9ddaaf58e7dcf21fc7aa2e3229cabc1f0d5982daee1a99551be2c7e21adee4d0` | `service:restricted_axis1_1d_mps` | pending | pending | pending | |
| `src/error_coupling_simulator/frontend/axis1_qt_mps_contract.py` | `41ed133784ce2ffae9369bbae8a32969aaec65ed96dbbb15d6289705b27730fb` | `service:restricted_axis1_1d_mps` | pending | pending | pending | |
| `src/error_coupling_simulator/frontend/axis1_qt_mps_execution.py` | `3d2394767b61ee1b1619fa09e2d31f4d45e9e567ae9be2a987536382996f09af` | `service:restricted_axis1_1d_mps` | pending | pending | pending | |
| `src/error_coupling_simulator/frontend/axis1_qutip_cuquantum_probe.py` | `b75936f1d6f66523487216b4aa8728ba7ead667de74dce17c55f8032c96db308` | `service:qutip_cuquantum_probe` | pending | pending | pending | |
| `src/error_coupling_simulator/frontend/axis1_qutrit_leakage_certification.py` | `f068ac9abef036940633798165872970ae2e65d88a293cab0327404891a84246` | `support:axis1_certification_harnesses` | pending | pending | pending | |
| `src/error_coupling_simulator/frontend/axis1_record_evidence.py` | `c2a2196e875ca201939ce89cce9fd31db6caf143f3417bcbf112fa711e32f102` | `service:axis1_dense_jointl_record` | pending | pending | pending | |
| `src/error_coupling_simulator/frontend/axis1_selection.py` | `4844bb7953f634985c00573a518a7df2bf0149d8d5959174214fedc0a66bc337` | `support:axis1_ir_selection_and_evidence_support` | pending | pending | pending | |
| `src/error_coupling_simulator/frontend/axis1_state_evidence.py` | `84e02a554309e6de3939b82de5a4902b84211c682361b68b2d6d7e64dfb01716` | `service:axis1_dense_jointl_record` | pending | pending | pending | |
| `src/error_coupling_simulator/frontend/b8_io.py` | `2c4cffc9c7134a0fa62f9f9269edf90ae99df00031aa716fdafde8f94c6ffbb2` | `service:record_io_and_dem_reduction` | pending | pending | pending | |
| `src/error_coupling_simulator/frontend/circuit_ir.py` | `faf2bbcfdea922dd8f6798ec2d4b888d7b9e1184e153959ba03698bfebc66299` | `service:frontend_compile_and_records` | pending | pending | pending | |
| `src/error_coupling_simulator/frontend/code_spec.py` | `af2ac889b9542c4256340ddff4038a2e4c119effaaa32ab587d7ff649076495d` | `service:frontend_compile_and_records` | pending | pending | pending | |
| `src/error_coupling_simulator/frontend/compiler.py` | `9b6c179e1465f7b87e06fd8a5a4bf449518b169be1fb2a2ebbe1e54c853ef17c` | `service:frontend_compile_and_records` | pending | pending | pending | |
| `src/error_coupling_simulator/frontend/cudaq_grover.py` | `596f1f130910c6c1de3e69ebdd0f80178233149c7f9622f37a7e5d6d920549bb` | `service:cudaq_grover_plugin` | pending | pending | pending | |
| `src/error_coupling_simulator/frontend/decoder.py` | `7feb814c59336832bb853af621e57fe4a374c80898540649a5fe9c84bc3dfe59` | `service:pymatching_decoder` | pending | pending | pending | |
| `src/error_coupling_simulator/frontend/experiments.py` | `4b7f18abeba8c1c52f28a0a18eccadfaeae459f9f5c0298b852a624da40990e7` | `service:xzzx_external_schedule` | pending | pending | pending | |
| `src/error_coupling_simulator/frontend/interop.py` | `3222e9e3af519f854c6220e50ebdcf05b87e4f73950e593fa58bfdb637180a84` | `service:record_io_and_dem_reduction,pymatching_decoder` | pending | pending | pending | |
| `src/error_coupling_simulator/frontend/mcwf_backend.py` | `c031c5b89d7d266de0c9aff6007fc87ee8d9fd26aed9edb8095d9369025507ce` | `service:dense_qudit_mcwf_carrier` | pending | pending | pending | |
| `src/error_coupling_simulator/frontend/mcwf_executor.py` | `8a560c283eb5fba1e26a58a87f5a402caead3f329ad5b138f9421c79c7b498a7` | `service:dense_qudit_mcwf_carrier` | pending | pending | pending | |
| `src/error_coupling_simulator/frontend/mcwf_grover.py` | `ca9a2cfce87d1325a7ba3f85abd0dcc9a8110c31a2dd378553de49c24e327c07` | `service:dense_mcwf_grover` | pending | pending | pending | |
| `src/error_coupling_simulator/frontend/mcwf_program.py` | `c1d86e1b2ebd0a973f2db7ac880fc4dafa9622c1ee97f09a0fefffaf33dace0e` | `service:dense_qudit_mcwf_carrier` | pending | pending | pending | |
| `src/error_coupling_simulator/frontend/metadata_guard.py` | `f83c703cc2b91793c19d58212fafa59b1f4c8b721df35121b4125a6d27fb978e` | `support:frontend_artifact_and_schema_support` | pending | pending | pending | |
| `src/error_coupling_simulator/frontend/noise.py` | `c06ad3c55d625775624f089a5254e0fdddeb8572a67beaf51af7ade995e4730f` | `service:frontend_compile_and_records` | pending | pending | pending | |
| `src/error_coupling_simulator/frontend/noise_spec.py` | `1dcf9840b48714fce541132cae45f39f7e09ebf10fbbd426b38eff0e4215d0f1` | `service:frontend_compile_and_records,source_stim_pauli_projection` | pending | pending | pending | |
| `src/error_coupling_simulator/frontend/operation.py` | `f2e0fffe5b55259386796a0e7e1a4e53a474edab5ca5b85dff495eac94a7b5c6` | `service:frontend_compile_and_records` | pending | pending | pending | |
| `src/error_coupling_simulator/frontend/pij.py` | `581a5ae6046cc1f94de5a5d2399967d3045550438010af794d5fd8b0e7ece477` | `support:probability_table_helper` | pending | pending | pending | |
| `src/error_coupling_simulator/frontend/ququart_transport.py` | `825ae05f5f6d207eebd447425325bfcd514acbaf4b50d515edaab5e048df45ea` | `service:ququart_cz_transport` | pending | pending | pending | |
| `src/error_coupling_simulator/frontend/qutip_cuquantum_backend.py` | `53dce79fc9ae18707164eb6b95fd965f6a9ed4efaa79795e21ed4b6236fae9f5` | `service:qutip_cuquantum_probe` | pending | pending | pending | |
| `src/error_coupling_simulator/frontend/qutrit_leakage.py` | `4557a1de6b173de566feb4a2354a8ae79eeacb886a8dd80e5b5b12b655d19fcb` | `service:qutrit_wg_frontend` | pending | pending | pending | |
| `src/error_coupling_simulator/frontend/record_layout.py` | `9fe55bdce6835e271ace3a7731aebd894c085625a659e7e1a79a866af308e17b` | `support:frontend_artifact_and_schema_support` | pending | pending | pending | |
| `src/error_coupling_simulator/frontend/record_schema.py` | `4fea40486535465b878fb80cf20fcc49b8fdbf2e82b224ce405d4c57bc4e422b` | `support:frontend_artifact_and_schema_support` | pending | pending | pending | |
| `src/error_coupling_simulator/frontend/schedule.py` | `5a5c6e3622e516c31fa0648547748229e84c7eb2fb3ad564a80360d46f196d35` | `service:frontend_compile_and_records` | pending | pending | pending | |
| `src/error_coupling_simulator/frontend/simulator.py` | `7f8b60e74bce0b79b73ffe52bdc24b19b6999bb2bf49a0bd3745bd19c932e4f1` | `service:frontend_compile_and_records,source_stim_pauli_projection` | pending | pending | pending | |
| `src/error_coupling_simulator/frontend/source_sidecar.py` | `f0f2e7f879afe95bb99aa1a93e6f2e0001abc6cac0190828cc8ff4fac45af07a` | `support:evaluator_source_sidecar` | pending | pending | pending | |
| `src/error_coupling_simulator/frontend/stim_io.py` | `3d3e08d753b90f5cea1923fc198f92b34358e41f865dbe7d3a5d3e86342f8b97` | `service:frontend_compile_and_records` | pending | pending | pending | |
| `src/error_coupling_simulator/frontend/stim_source.py` | `4f2e84e59995a9bd67f9dafe4a3961c15d3dc5fc5e87358cae321bf300613978` | `service:frontend_compile_and_records` | pending | pending | pending | |
| `src/error_coupling_simulator/frontend/xzzx_code.py` | `52c94d3e42d8cd236434d9fa864cdd92fb4e0c274c5f4252ecc89bf12b0120f5` | `service:frontend_compile_and_records,xzzx_external_schedule` | pending | pending | pending | |
| `src/error_coupling_simulator/frontend/xzzx_parser.py` | `b830355a5827863e05ec0d14e5deb7d63f167eb70e80a003cb61aa4a7f719b09` | `service:xzzx_external_schedule` | pending | pending | pending | |
| `src/error_coupling_simulator/mechanisms/__init__.py` | `6edd8ee3cecc094fffd5d75bf7f2754acee3f22697fa3a74aaa76c897404d876` | `support:namespace_and_public_facades` | pending | pending | pending | |
| `src/error_coupling_simulator/mechanisms/axis1_primitives.py` | `ed03ca7bdc09243ee79e42972da8e198e8cb77cc2e0786aa8101d0d17689a958` | `service:axis1_joint_channel` | pending | pending | pending | |
| `src/error_coupling_simulator/mechanisms/catalog.py` | `a95931cfc50000741153368cf432498b8cfcbaaff899467b67d38e0704792d15` | `support:compatibility_catalog_and_seam_fixtures` | pending | pending | pending | |
| `src/error_coupling_simulator/mechanisms/cz_leakage.py` | `f102ec505da804d5f617a0383b0ec36bd7c8f8c97abdf4f4309c0356a58e9faf` | `service:ququart_cz_transport` | pending | pending | pending | |
| `src/error_coupling_simulator/mechanisms/qutrit_teachers.py` | `f366224da9813396985fdbca15953d6e04944e248cc537aacf8513811b5f079e` | `service:qutrit_wg_frontend` | pending | pending | pending | |
| `src/error_coupling_simulator/mechanisms/seam_teachers.py` | `99342501160df2cbd6c2e715605bc6d50385723ae50ef9bccfd2cce18adc794e` | `support:compatibility_catalog_and_seam_fixtures` | pending | pending | pending | |
| `src/error_coupling_simulator/mechanisms/teachers.py` | `c258c13374676d0e85be19e7c7914aa4bcd5c9d4a8d5174884e5d9bb576eac3a` | `service:channel_algebra` | PTM consumer links audited; teacher/twirl channel construction pending Batch 1B2 | ECS-CPTP-008--010 (consumer) | Batch 1B1 call path inspected; module partial | shared PTM helper creates test/common-blind-spot risk |
| `src/error_coupling_simulator/noise_processes/__init__.py` | `53e34530ffc57db19fc6d262e945f4b35a73a7ad05038620e9656679a9e67c01` | `support:namespace_and_public_facades` | pending | pending | pending | |
| `src/error_coupling_simulator/noise_processes/coupled_cycle.py` | `8a943c1072a59bc81e9b5a99c277e757c77bd0dbbd9a7a75280880d05444c6d1` | `service:classical_1f_nonmarkov_chain` | pending | pending | pending | |
| `src/error_coupling_simulator/numerics.py` | `384ca72a89e4b62048374a07ee6ed02e797291aa662e2108482fc9260c5de0ae` | `support:shared_numerical_policy` | all definitions audited; use-specific consequences remain with owning formula rows | ECS-NUM-001--003 | Batch 1A reviewed | global value/source gap and probability rewrite |
| `src/error_coupling_simulator/quantum_bath/__init__.py` | `5bb8e751db2577fb143f596e6df99ac6494674ffdc254133156bc0fd8d0dd3dd` | `service:quantum_bath_research` | pending | pending | pending | |
| `src/error_coupling_simulator/quantum_bath/carrier.py` | `f1a44bad4c75d2ecb7713a63c2cac253b4edaa57a041817a4b74bb49de4b055c` | `service:quantum_bath_research` | pending | pending | pending | |
| `src/error_coupling_simulator/quantum_bath/crow_joynt.py` | `48a1576512c3a0ef508d4ed2cac72622500e88256a2943a82c60de9eee7f0715` | `service:quantum_bath_research` | pending | pending | pending | |
| `src/error_coupling_simulator/quantum_bath/gksl.py` | `63a60c7462b7eed35d79ddd8f0f6c0936609f55b8ada9f9062b6c63c911cfad3` | `service:quantum_bath_research` | pending | pending | pending | |
| `src/error_coupling_simulator/quantum_bath/ground_truth.py` | `5c2b7364260a217e1d1c25487c2f50729956598c9379efae62462a8be5ac75b9` | `service:quantum_bath_research` | pending | pending | pending | |
| `src/error_coupling_simulator/quantum_bath/memory_witness.py` | `8a56d0fa3f9cb488b774ea18fffef439ae431ec0d99dacaa186627bb8c50393c` | `service:quantum_bath_research` | pending | pending | pending | |
| `src/error_coupling_simulator/quantum_bath/nulls.py` | `9ef10ec2a995512e510aa0664938ede1b66eb2c4f7c73c08a34bd0a0063996c0` | `service:quantum_bath_research` | pending | pending | pending | |
| `src/error_coupling_simulator/quantum_bath/observables.py` | `cfdfe694fbe81ffcce02376dafd2f2b1d8820c2335ca5997ba03bb5fccaa98d8` | `service:quantum_bath_research` | pending | pending | pending | |
| `src/error_coupling_simulator/source/__init__.py` | `ad6cb6c746ac614c8f5a73cd7873e1c47b7551ad33eb2a3833ffe24106942c5f` | `support:namespace_and_public_facades` | pending | pending | pending | |
| `src/error_coupling_simulator/source/coupling.py` | `78ea40a11b478d1b261bdd4beb72784517373356b8532542d6f4c15f214f83b7` | `service:classical_1f_nonmarkov_chain` | pending | pending | pending | |
| `src/error_coupling_simulator/source/process.py` | `3ffc8db0eba8d1421d0e3f44859ed3412a57c0772852a3592bc0ef19d7dfa924` | `service:classical_1f_nonmarkov_chain,classical_burst_storm_sources` | pending | pending | pending | |

## 12. Reverse coverage — 4 native files

| frozen path | SHA256 | mirrored scientific object | formula IDs | host/native equivalence check | reviewer coverage | notes |
|---|---|---|---|---|---|---|
| `src/error_coupling_simulator/carrier/kernels/fused_kraus_local.cpp` | `d818752884e7a975ad17232678bed509c7acfcb6083a6b5cd3864554d8b27d52` | pending | pending | pending | pending | |
| `src/error_coupling_simulator/carrier/kernels/fused_kraus_local.cu` | `1e5efde0da8db8a2305323363242f066b65c11a74a25f5e7f1945c1d13f3c00e` | pending | pending | pending | pending | |
| `src/error_coupling_simulator/carrier/kernels/qutrit_mcwf_ops.cu` | `524dfbba14a3a3e4255a5599add7ada6da672aa3a9c5a48ab42e43ee8b71e8cc` | pending | pending | pending | pending | |
| `src/error_coupling_simulator/carrier/kernels/sv_traj_d3.cu` | `8f98dd4ef12cd00dbf919713f5c4844b47ff394a271fa4889e00253e16fac7ee` | pending | pending | pending | pending | |

## 13. Verification-surface coverage

### 13.1 Canonical 52 acceptance files

| lane | frozen unique file count | formula/oracle/gate classification | Batch 12 disposition |
|---|---:|---|---|
| `cpu_light` | 26 | pending | pending |
| `cpu_exclusive` | 6 | pending | pending |
| `gpu_serial` | 20 | pending | pending |
| total | **52** | pending | pending |

### 13.2 Remaining test and harness surface

| surface | count relationship | audit requirement | disposition |
|---|---|---|---|
| noncanonical pytest-named files | 79 of 131 | inspect for independent formulas, current scientific gates, and shared-formula blind spots | pending |
| executable harness self-test | 1 (`tests/harness/proc_selftest.py`) | classify as engineering-only or scientific | pending |
| other Python harness/support files | remainder of 143 | classify; do not count utilities as independent scientific evidence without a formula | pending |

### 13.3 Exact 143-file test-side inventory

This table prevents the 52-file canonical execution set from being mistaken for the complete
verification surface. The structural class is frozen in Batch 0; the scientific
formula/oracle/gate disposition remains for Batch 12.

| frozen path | SHA256 | structural class | catalog service references | canonical lane/environment | scientific disposition |
|---|---|---|---|---|---|
| `tests/_support/__init__.py` | `135bde285a294bd268f140ee8a79b4620ccdc16fea803648dddc114d10b9b969` | harness/support | `-` | `-/-` | pending |
| `tests/_support/faithfulness.py` | `e5f0b70a3b697b10dadb50c234834f7a00b3384604c6b249fae942ffc7482cd2` | harness/support | `-` | `-/-` | pending |
| `tests/_support/fixtures.py` | `9cec8dbe7c9ef5753bde29a555dc02bf649d03e6e5db54d6a335e405a9806328` | harness/support | `-` | `-/-` | pending |
| `tests/_support/test_faithfulness_selftest.py` | `4f4f3a729149b1fc3f200a6eaa9391cfc374b490ec3cfc3c4b9f5d18e42b66a6` | noncanonical pytest | `-` | `-/-` | pending |
| `tests/_support/test_support_selftest.py` | `0016cce51a538db901468d8b6864013e46e2eb6b2467ee9082ff0590b4cba261` | noncanonical pytest | `-` | `-/-` | pending |
| `tests/conftest.py` | `aa54e3e219c49a5341fe20c285e97d7782bd005b77ae0aef048e09e7daaab1a8` | harness/support | `-` | `-/-` | pending |
| `tests/harness/__init__.py` | `d8a8faa7a0a06e21266fdaadd9bbe8eb74f618e8e2203e66da3205b460bc64fe` | harness/support | `-` | `-/-` | pending |
| `tests/harness/coverage_audit.py` | `7b457e8c0845ddcf8ea8ff95e0084f797f17b4d21886ce84459116a86258a1db` | harness/support | `-` | `-/-` | pending |
| `tests/harness/gate.py` | `df9a0df015b43048f7b7c33e2f34ba347a4cb88fe0e8e45ddf8f390c346c2f84` | harness/support | `-` | `-/-` | pending |
| `tests/harness/gpu_pool.py` | `c72499e9a163632db936a2a9586af6f0d0b08345abcfd6f0301b2030df9f2eef` | harness/support | `-` | `-/-` | pending |
| `tests/harness/mutation.py` | `526616ea46aac52baa5e1388b01c652ad6109115cb3800993180fda0357e138c` | harness/support | `-` | `-/-` | pending |
| `tests/harness/proc.py` | `8a1e40bf1aa959d587dde77a85bed3c660bbdc64877598931d3d6db557a84013` | harness/support | `-` | `-/-` | pending |
| `tests/harness/proc_selftest.py` | `c975b748b1dbb0f47138f96956c6cfc7c75f1b4ec13ccfc10c100ac4792376a2` | noncanonical selftest | `-` | `-/-` | pending |
| `tests/harness/service_acceptance.py` | `465e8dfe2eaded028ca33d8d85f07d394dd08faedbbda65b4077de3127373b5d` | harness/support | `-` | `-/-` | pending |
| `tests/harness/test_mutation.py` | `4a5246ec1899b2c9cdf617e22943736b3d7fdb55fe837abc05f1561a7c7e0ae7` | noncanonical pytest | `-` | `-/-` | pending |
| `tests/test_analog_schedule_units.py` | `883784b5f026d18b7415f5aa2cd299226deb2f26f339868cc38f7d0588fa09df` | canonical acceptance | `axis1_schedule_adapter` | `gpu_serial/ecs` | pending |
| `tests/test_artifacts_units.py` | `f966e59eed648399b5bc6ceaf4f3934309aa2cb046cde55289696058c00d6499` | noncanonical pytest | `-` | `-/-` | pending |
| `tests/test_axis1_connected_cluster_join.py` | `3d3e0a55e2c1c6f2b83a9544ef3d651646b5c45e0b53fb38927c9c58f4c597e8` | noncanonical pytest | `-` | `-/-` | pending |
| `tests/test_axis1_context_units.py` | `1bd98b46f5b9c8e9e75968537dad047978746644982a7e5d9933ff13152ffab2` | noncanonical pytest | `-` | `-/-` | pending |
| `tests/test_axis1_convergence.py` | `3473a79500cb987a3bd62a16c3254f2464a4b61c119aaa883134e646f70f98df` | canonical acceptance | `axis1_joint_channel` | `gpu_serial/ecs` | pending |
| `tests/test_axis1_evidence_guard.py` | `6e89afcd87bdd454d0cee5fb35732e86f18b54a0aecf9e21c1d01b63f41f0cd6` | noncanonical pytest | `-` | `-/-` | pending |
| `tests/test_axis1_evidence_guard_units.py` | `372ee5f45762896d5fc41c339b23c43090e3f63d56e688908d747333635ab2ff` | canonical acceptance | `axis1_dense_jointl_record` | `gpu_serial/ecs` | pending |
| `tests/test_axis1_finite_step_error_control.py` | `61700ba6a345bad0db33b2b49b49db105a1417d7db23d059d0857e03da8b0d15` | noncanonical pytest | `-` | `-/-` | pending |
| `tests/test_axis1_m6_constraint_ledger.py` | `a61862c912f1d7431b7b2207ca55b3731c053bbef24c430d4918073394c9914b` | noncanonical pytest | `-` | `-/-` | pending |
| `tests/test_axis1_record_params_override.py` | `a15aabb3306847a1c7808f7a324c029c18d4116e22e7e4feffa0f4dfae28a241` | canonical acceptance | `classical_1f_nonmarkov_chain,exact_qubit_circuit_dm,axis1_dense_jointl_record` | `gpu_serial/ecs` | pending |
| `tests/test_axis1_runners_units.py` | `260c0459c53f825373f0ab896404af33c87afc41bfeded32e51d6185ee6eb0a8` | noncanonical pytest | `-` | `-/-` | pending |
| `tests/test_axis1_selection_units.py` | `8485849d7c9e723d8fa3a66c6b0963cd6131afc82e76c7370bbdfac2bc464e27` | noncanonical pytest | `-` | `-/-` | pending |
| `tests/test_axis1_wb_acceptance_gate.py` | `f177a9757cb81b9550e31679dda5466ca7a37c30ff93208ca83d413c2743facc` | canonical acceptance | `restricted_axis1_1d_mps` | `gpu_serial/ecs` | pending |
| `tests/test_axis1_wc_decircularized.py` | `efbca66cc14b387c2231cc4549b9ad01d2323acd52bb68f3082c4d2f0282de58` | noncanonical pytest | `-` | `-/-` | pending |
| `tests/test_b8_io_units.py` | `bb301ab793d54b0c95c38de17d7ba400bc739f21db413240a0ecee8bb64bc72b` | canonical acceptance | `record_io_and_dem_reduction` | `cpu_light/ecs` | pending |
| `tests/test_batched_mps_ops.py` | `4600d093dc1dfca56c36bc80ea8054bcc93303a98afaab71d726c2eeb586f840` | noncanonical pytest | `-` | `-/-` | pending |
| `tests/test_bayes_floor.py` | `4de9dc407d002686f7b3115e9a58e7fb93f63ad65455ce80ac5fb184066c559c` | noncanonical pytest | `-` | `-/-` | pending |
| `tests/test_carrier_channels_units.py` | `1f3cc3d89e23f8a707b7168ba8c11c57db88fc69c04828a714d58d52c8b920ea` | canonical acceptance | `channel_algebra` | `cpu_light/ecs` | Batch 1A numerical-floor pins share the policy; Batch 1B2a1 rotation/expm pins are independent only on ordinary inputs while several references repeat project formulas; Batch 1B2a2 lines 166--255 mirror every damping/reset/synthetic/readout target, including the same floors/constants, and `assert_cptp` tolerance `1e-9` masks `1e-12` endpoint defects; no invalid/nonfinite time/probability, scale-sensitive T2, fractional reset target, weak4 boundary, leakage projector, current-M12 action, or readout-orientation falsifier; targeted owning batch `71 passed`; qutrit/WG formulas remain pending |
| `tests/test_carrier_record_fold.py` | `aefe051704f8236db5b7be11f4b07d72bb94aaead84d8adacc8aa87df7b039fe` | canonical acceptance | `record_contract_and_packing` | `cpu_light/ecs` | Batch 1A: normal-domain example, inverse, shape guards; shares formula and misses nonbinary/fractional/prior cases |
| `tests/test_carrier_seam_composition.py` | `fb9b9ee6474c340aa06b26692bc89067bf63962359c2efaf5e0285e0f6ba2609` | noncanonical pytest | `-` | `-/-` | pending |
| `tests/test_carrier_seam_instrument.py` | `4e989e5c9d374995e138cf664b296aedd16d663c2b9e77e867c4e7a93a96692a` | noncanonical pytest | `-` | `-/-` | pending |
| `tests/test_carrier_seam_pins.py` | `94f5a8079f2a230b5386d43b6b5ba2b9c34b824537dacab4e3b78b8eb5d5fb3c` | noncanonical pytest | `-` | `-/-` | pending |
| `tests/test_certify.py` | `4cb1e53ab0f5d0cf6715ae2a4e3988e777e956cb96bc1cadbac010a994d4ad05` | canonical acceptance | `formal_certification` | `cpu_light/ecs` | pending |
| `tests/test_certify_anchors_units.py` | `fb6b41c5c5437a8af667321d182e9e913e8d9bde0ca8111b87f0203c37242be4` | canonical acceptance | `formal_certification` | `gpu_serial/ecs` | pending |
| `tests/test_certify_contracts.py` | `07b07e1c63d19d540c5acf0f37089f738401c6e8664daab94ed3639dc93bda6c` | canonical acceptance | `formal_certification` | `cpu_light/ecs` | pending |
| `tests/test_certify_core_units.py` | `f6779d6506eb4251a25ad38d34e29497f9adf1efe79e301104550478c1866284` | canonical acceptance | `formal_certification` | `gpu_serial/ecs` | pending |
| `tests/test_channel_diagnostics.py` | `f2ee2430dac6b1465dc2c32aabc19193538d3fd88352af64257ad7340023cdcf` | canonical acceptance | `channel_diagnostics` | `cpu_light/ecs` | pending |
| `tests/test_circuit_ir_units.py` | `b553a9226a0937c3cfe81a5b44549bb5494834460d30966128ceb08c35d9afe0` | noncanonical pytest | `-` | `-/-` | pending |
| `tests/test_code_spec_units.py` | `16b5764605a0ad9dd1192ec9562e3e74807449593cd1601e801743aa04cf17c7` | noncanonical pytest | `-` | `-/-` | pending |
| `tests/test_coupled_cycle_teacher.py` | `deb3d34ae6bb05e77a1dc156768dae956dbce26d12178a08128028fa80ede715` | noncanonical pytest | `-` | `-/-` | pending |
| `tests/test_coupled_cycle_units.py` | `28e2dc1809b03ca9c8636f97b5f2e2b9507d8c512dd39751ae0fc7c6ee18c3cd` | canonical acceptance | `classical_1f_nonmarkov_chain` | `gpu_serial/ecs` | pending |
| `tests/test_cz_leakage_mechanism_units.py` | `f2fb533295a3bd87768d612a7a4515e8588d3fe43046d5a6fa58b0fe5d773212` | canonical acceptance | `ququart_cz_transport` | `cpu_light/ecs` | pending |
| `tests/test_decoder_units.py` | `1c84f3b6caae3418f0df7e68527428bc710ef31bd12ad44b6b66f5778f5d261f` | canonical acceptance | `pymatching_decoder` | `cpu_light/ecs` | pending |
| `tests/test_diff_circuit_forward.py` | `ce6dd88af62fa736b8d4e56f64e8028aa119084635f1ffcefbdedf2328e854e8` | canonical acceptance | `exact_qubit_circuit_dm` | `cpu_light/ecs` | Batch 1B1: checks ordinary nonzero Z probabilities/gradients but omits exact-zero, invalid-state, NaN/inf, and floor-induced rare-event falsifiers; remaining exact-DM formulas Batch 1C |
| `tests/test_distribution_boundary.py` | `f146373827e14019166cd08c72abd40d7e6d8eaa6824b600b1723a981e37d7e2` | noncanonical pytest | `-` | `-/-` | Batch 1A: isolated-wheel normal packed-record/product smoke; Batch 1B1: callable/export and ordinary probability smoke only; Batch 1B2a2 lines 553--566 merely import and assert callability of `custom_non_pauli_kraus` and `thermal_relaxation_kraus`; no other a2 family or independent formula is checked, and adversarial domains remain absent |
| `tests/test_experiments_import_boundary.py` | `e87858f7a96d8f314358673211864a4243e6f5a8c0be7c96c8e56137395b9389` | noncanonical pytest | `-` | `-/-` | pending |
| `tests/test_experiments_units.py` | `03a41b54d3997ef000b45ea11bf12b4e1748329b75bdf0e7b45521c389b9a748` | noncanonical pytest | `-` | `-/-` | pending |
| `tests/test_fault_graph.py` | `eb8193d3c42139313299c086a0836104972d78d9df7f5ae7bee97ed4260bd0ad` | noncanonical pytest | `-` | `-/-` | pending |
| `tests/test_finite_rtn_exact_cpdiv_gate.py` | `0efd5ed3690938e946b36ce9ea52c83419e3fbe3992563893b65620f3fe52cb0` | noncanonical pytest | `-` | `-/-` | pending |
| `tests/test_frontend_experiments.py` | `88b66cae58330bca8d493374770080a4d8a105d6bce7a4a78e39c6f2574ca341` | canonical acceptance | `xzzx_external_schedule` | `gpu_serial/ecs` | pending |
| `tests/test_fused_within_cycle_sampler.py` | `337d43aec2e3a22fda27435e6ef642ad7ad6e551a95bc5e979552db1622ef628` | canonical acceptance | `fused_within_cycle` | `cpu_light/ecs` | pending |
| `tests/test_gate_soundness_matrix.py` | `b4532006397c1ba0e26fa93265ce9dc44ca79ce2a69eac77844023832ac58860` | noncanonical pytest | `-` | `-/-` | pending |
| `tests/test_hardware_m1_ingestion.py` | `e0c68a0b13c6623a2dc387e3ff91ffa04cb065686e5c029dba3fb7f267953a31` | noncanonical pytest | `-` | `-/-` | pending |
| `tests/test_hardware_m2_window_closure.py` | `2753c330cd1713c6ed6a8f92056a8c967cecaf16bfb2d190d7c9ba5281748b04` | noncanonical pytest | `-` | `-/-` | pending |
| `tests/test_hardware_m3_window_nll.py` | `7df8b9d5871e298794338092fd19f6f9fc82fa17fba438d271a1fdc81cd5f5c4` | noncanonical pytest | `-` | `-/-` | pending |
| `tests/test_hardware_m4_decode.py` | `531e07361b0f974a4570b112dd878479b3f8e61aa9b941ec09eaf4e233600538` | noncanonical pytest | `-` | `-/-` | pending |
| `tests/test_hardware_m4_decoder_prior.py` | `0a40ab594aaa1291cf2f365a146a3a9b93d2be641ceb8a85b39f787b70385ec7` | noncanonical pytest | `-` | `-/-` | pending |
| `tests/test_hardware_m4_dem_compose.py` | `2acd3920a7fcf20e2621d6b8d0a555ba79cffa435236875a35954bdd0d2a87f2` | noncanonical pytest | `-` | `-/-` | pending |
| `tests/test_hardware_nll_graph_mode.py` | `b5cc052e52b7127523232b282d8b1a8927a48d0a9e28be4e5815c380e47d765f` | noncanonical pytest | `-` | `-/-` | pending |
| `tests/test_harness_gpu_pool.py` | `2ab4bc0a23bb641c3d4b7b918c75c00955e9a256da5fce3960e4b3f3e4fe9f78` | noncanonical pytest | `-` | `-/-` | pending |
| `tests/test_harness_proc.py` | `252dd77e0111cb77498174a893456a8311db0cebce62be8de78337d001cf4579` | noncanonical pytest | `-` | `-/-` | pending |
| `tests/test_hypergraph_dem_tn_d3_surface.py` | `d9b887bd414da39cc0e0ff9696b1147fac354935578299120e50ee6ea5a5ee15` | noncanonical pytest | `-` | `-/-` | pending |
| `tests/test_interop_units.py` | `25f444ceb6cf984929125c6d60da9f81a85680a6918725e23fb25672181b114f` | canonical acceptance | `record_io_and_dem_reduction,pymatching_decoder` | `cpu_light/ecs` | pending |
| `tests/test_joint_lindbladian.py` | `58f579647c8819d08f56cab6078c08ee856832280e62fdcb61946788972e28f2` | canonical acceptance | `axis1_joint_channel` | `gpu_serial/ecs` | Batch 1B1: QuTiP/SciPy comparisons are comparatively independent for valid Hermitian-state Kraus action, but do not cover non-Hermitian domain; Lindbladian formulas Batch 3 |
| `tests/test_kernels_fused_kraus.py` | `27c9665173c283840b5800cd681444498aa1dfb54d4c92f6fd5a30dd24b0f9aa` | noncanonical pytest | `-` | `-/-` | pending |
| `tests/test_kernels_vmap.py` | `fa2088ae750ea9afd350abdc37d50666d3e2cdd6d5a49f3f77ac406b7a9ce665` | noncanonical pytest | `-` | `-/-` | pending |
| `tests/test_m10_coherent_rxx_ryy_constraint_ledger.py` | `f14cf588dd5adc116e098080656c6fdb8aaef0fa02ef284de7918bd4a5bd35d6` | noncanonical pytest | `-` | `-/-` | Batch 1B2a1 screening: hand-types the XX+YY generator and independent composite identities for a legacy/qec_twin GPU carrier, corroborating ECS-CHAN-002 form only; it does not call the installed NumPy primitive or close its M10 parameter mapping; full Axis-1 gate audit remains Batch 3/12 |
| `tests/test_m12_phaseB_seam.py` | `d2f23934c0e9a315877fcd87aea8c17d0246ef32855ca36d94e0053838c2ac6d` | noncanonical pytest | `-` | `-/-` | pending |
| `tests/test_m20_coherent_ry_constraint_ledger.py` | `4756faa55d264909d7e4b1b0671e2f0cb6dcbd5378c8da92bdf215a287982b44` | noncanonical pytest | `-` | `-/-` | pending |
| `tests/test_m22_coherent_cxx_constraint_ledger.py` | `059da0e3c2133f576cf6928d6a844e3b7dacd733f5c32335357ddc81b59df2b1` | noncanonical pytest | `-` | `-/-` | pending |
| `tests/test_m23_coherent_cyy_constraint_ledger.py` | `94faf13ddb9ab048d3753b4cbe4ef567553256cca9bf2ac4a1e62e6ba26cb758` | noncanonical pytest | `-` | `-/-` | pending |
| `tests/test_m29_coherent_zx_constraint_ledger.py` | `034496d036deafdde9196988beb7e105c985bdc9ab3013760a36f358f10ee849` | noncanonical pytest | `-` | `-/-` | pending |
| `tests/test_m6_coherent_rx_constraint_ledger.py` | `8cfa31de9b759c30a920627d698f6626085fcf6da00298d29de72e43a8766e0b` | noncanonical pytest | `-` | `-/-` | pending |
| `tests/test_m7_coherent_rz_constraint_ledger.py` | `b78b80b7da7000c8fdd5e61c1377e82c7830227c44a540f8340da6b813820419` | noncanonical pytest | `-` | `-/-` | pending |
| `tests/test_metadata_guard_units.py` | `1e2930e3a26df6208a1ca43036fff414d212e27a4babb8633d14e02ad1cc9639` | noncanonical pytest | `-` | `-/-` | pending |
| `tests/test_mps_seams_units.py` | `cac0ac22d7d811d431fe1e256838846e57157c56f2d957659e7f0e189cc2f494` | noncanonical pytest | `-` | `-/-` | pending |
| `tests/test_mps_terminal_degenerate_guard.py` | `0dfc8c8218460569f6127eb9c450d5aa86155f541c02ac54f0851677619a5cab` | noncanonical pytest | `-` | `-/-` | pending |
| `tests/test_noise_mechanism_primitives.py` | `12fa911600cab0743195e55ceb60fae1b9b51d7c7693328ba1257f642e7c0e0d` | canonical acceptance | `channel_algebra,qutrit_wg_frontend` | `cpu_light/ecs` | Batch 1B1 principal gate has shared Choi/PTM/domain blind spots; Batch 1B2a1 only consumes `rx_unitary(0.3)`; Batch 1B2a2 uses the same-module `amplitude_damping_kraus(0.12)` in its reference assembly and therefore does not independently certify AD or the other families; combined targeted run `71 passed`; qutrit/WG formulas remain pending |
| `tests/test_noise_spec_units.py` | `b8f83e37df219f648c3102c1d487f0b475bdaf6271f7ccf4a6ce471ea303f084` | noncanonical pytest | `-` | `-/-` | pending |
| `tests/test_operation_units.py` | `2d9f3e04ddd2fe1fa66155dbe3039ffdd585efbc64bef6bbaf3cd6f594cbbfaf` | noncanonical pytest | `-` | `-/-` | pending |
| `tests/test_p0_interop.py` | `76be37c3d7aadf3722515ab4fe041ebf04a3b82810e74629ba74123949b0a717` | noncanonical pytest | `-` | `-/-` | pending |
| `tests/test_p2_mps_per_round_leak.py` | `9cd9d3cd5196bc0a256283de9a7acf0b14796a6ccc61b033d62a99dc74f252ae` | noncanonical pytest | `-` | `-/-` | pending |
| `tests/test_p2_theta_leakage.py` | `77d7ef55263990adc584ee27e744a22cdcf3fcb29fb1731f650a707e487b08fb` | noncanonical pytest | `-` | `-/-` | pending |
| `tests/test_package_release_contract.py` | `02009ccdde54da82176f4634582be7976fc0cd12ebfd8fb0bdc7c18f42fc593d` | noncanonical pytest | `-` | `-/-` | pending |
| `tests/test_pepo_host_seam.py` | `eb3f0a7d680d10fe5661bb043fb98e8048639be9c6e12e7129dfa825c7a900ea` | canonical acceptance | `pepo_findings` | `cpu_light/ecs` | pending |
| `tests/test_pepo_rung1.py` | `290c203f073ed931969461d09ec832cd4b299416a6eebce222f6b2ccbe56e6df` | catalog legacy source | `pepo_findings` | `-/-` | Batch 1A: legacy PEPO fold equality, inverse, and prefix-XOR checks; project-formula oracle, not source-independent; remaining PEPO formulas Batch 9 |
| `tests/test_peps_fet.py` | `1ac9966b1f4f0faecbfb76784802d0e12547509c6943acc677331cfc2af5eed4` | noncanonical pytest | `-` | `-/-` | pending |
| `tests/test_peps_host_seam.py` | `f29afc9192c49a235ddd557b96bccf75961ffa9b9f429b6b5e5cbd39e9b9ed0e` | canonical acceptance | `peps_single_wire` | `cpu_light/ecs` | pending |
| `tests/test_peps_spike.py` | `fdc5d0106c0b49c37556a67d7122cbd3cda7deb7abe55971d183194cb8214276` | catalog legacy source | `peps_single_wire` | `-/-` | Batch 1A: legacy PEPS fold equality and two-way inverse checks; project-formula oracle, not source-independent; remaining PEPS formulas Batch 8/9 |
| `tests/test_physical_channels.py` | `e0e2d58de10983768b05a6193a41f6c7b0b6ee354b8ad4bd488f715f5281a0da` | catalog legacy source | `channel_algebra` | `-/-` | Batch 1B2a1 screening covers ordinary RZZ/RX/RZ/Pauli PTM; Batch 1B2a2 directly checks only ordinary AD action and readout row sums, while the explicit adapter subset is M4/M15/M9/M1 and broader catalog loops check only finite/distinct fingerprints; installed primitives/project helpers make this migration evidence rather than an independent formula oracle |
| `tests/test_quantum_bath.py` | `50fb3b69928ebf33169170cd9a4606920e18e6c2ce6cf7a8e1528be7efe15722` | canonical acceptance | `quantum_bath_research` | `cpu_exclusive/ecs` | pending |
| `tests/test_quantum_bath_carrier_units.py` | `a9e6382512123427b96b28f930d006450497b2c5c3c7a085d343a1214dd705d3` | canonical acceptance | `quantum_bath_research` | `cpu_exclusive/ecs` | pending |
| `tests/test_quantum_bath_gksl_crowjoynt_units.py` | `85c01fd9d6948d9b94a554fa0a0c022c947832f22f7fa645a8e7e4afc2922ca2` | canonical acceptance | `quantum_bath_research` | `cpu_exclusive/ecs` | pending |
| `tests/test_quantum_bath_groundtruth_nulls_units.py` | `fb63a99d6b2d646b0fcb304961c5b63aca2a3c60c1093799a6f0680453c2001d` | canonical acceptance | `quantum_bath_research` | `cpu_exclusive/ecs` | pending |
| `tests/test_quantum_bath_memwitness_units.py` | `9d658f1f36141947059cd04294d491e1b152dc0de135a744c5da0231c3045894` | canonical acceptance | `quantum_bath_research` | `cpu_exclusive/ecs` | pending |
| `tests/test_quantum_bath_observables_units.py` | `a1c05a45ba368e943f2d3f34118d80e1dfd2d0fcc8a74131758c291a5cd6f0f5` | canonical acceptance | `quantum_bath_research` | `cpu_exclusive/ecs` | pending |
| `tests/test_qutrit_dm_exact.py` | `f1bfe154dcaf746df2af1c70e3372852905db5f2554318e75121fdd0b1b51382` | noncanonical pytest | `-` | `-/-` | pending |
| `tests/test_qutrit_dm_measurement_semantics.py` | `9417840317ce826d6dc30f0f46f02839935a613af6b482d6b479a58a0e470abf` | canonical acceptance | `exact_qutrit_dm,formal_certification` | `cpu_light/ecs` | pending |
| `tests/test_qutrit_dm_memlean.py` | `d5cfca748e3ea2bbff6463f3752b6a71883363ad20c9190dec1b9a3602669c84` | canonical acceptance | `exact_qutrit_dm` | `gpu_serial/ecs` | Batch 1B1: blocked Hermitianization is checked against the same project formula, so it verifies mirror equality but not applicability; qutrit carrier formulas Batch 5 |
| `tests/test_record_batch_units.py` | `bad99b1d28807fd3111436b8836999d18ca247c07ba79c2957d1002c7ed27f85` | canonical acceptance | `record_contract_and_packing` | `cpu_light/ecs` | Batch 1A: normal byte/fold and evaluator-key gate; misses uint8 pre-cast, padding, float payload, and mutation falsifiers |
| `tests/test_record_layout_units.py` | `8f9ee30fa86504334da9934539ac9c516d4975a0f43f6d78ead3efef19ad8782` | noncanonical pytest | `-` | `-/-` | pending |
| `tests/test_record_schema_units.py` | `9da613937c9e62e8b78edfff06d409c8bd485873d2a3f0158a2e8a4330282031` | noncanonical pytest | `-` | `-/-` | pending |
| `tests/test_schedule_units.py` | `fbaa82194975b4715400eae4e63b99e044dc6927c4baad501d2d22fb14cc012c` | noncanonical pytest | `-` | `-/-` | pending |
| `tests/test_scope_boundary.py` | `f75567cc822a089c56cbcfff5b2a2953ff0dfe0e7b962fbc3fa4cc1507d5724a` | noncanonical pytest | `-` | `-/-` | pending |
| `tests/test_seam.py` | `e44e832ab05b2dec590baac9e459266167e608b2311b9151ddeffae1bc0e0592` | noncanonical pytest | `-` | `-/-` | pending |
| `tests/test_seam_teachers_units.py` | `b95b6869f494177414a621a3545db4a65d2dd372ab7c98404494bcec9e628701` | noncanonical pytest | `-` | `-/-` | pending |
| `tests/test_service_acceptance_harness.py` | `5c6e25bd98675f5267913f272230f097b99065769f5467a5ff67398e66e00cce` | noncanonical pytest | `-` | `-/-` | pending |
| `tests/test_shotset_records.py` | `42bababa5561bfabd865f22145a578cff002d70574b7ecbf7886650d03c65f0f` | noncanonical pytest | `-` | `-/-` | legacy `qec_twin.ShotSet` integration gate; shared project packing convention, not current-package or literature-independent evidence |
| `tests/test_shotset_units.py` | `b561b085002b3dff761fad671a548ff823b3ffaacec3d7655e3bb1906c8bc034` | noncanonical pytest | `-` | `-/-` | legacy `qec_twin.ShotSet` unit/property gate; verifies byte mechanics only, not current scientific record semantics |
| `tests/test_simulator_axis1_schedule.py` | `ec9fde4787727fd8e5bd019f7f42d0c720a3eccdbae7d929cc799f03966731df` | canonical acceptance | `axis1_schedule_adapter,axis1_joint_channel,exact_qubit_circuit_dm,axis1_dense_jointl_record,restricted_axis1_1d_mps,qutip_cuquantum_probe` | `gpu_serial/ecs` | pending |
| `tests/test_simulator_codespec.py` | `24a893e23817d6e0bf11c0ec38a687bc61d040e9e51e68edaedc57a2b63a0e82` | canonical acceptance | `frontend_compile_and_records` | `cpu_light/ecs` | pending |
| `tests/test_simulator_cudaq_grover.py` | `7939d02c56fb829a69a424542247ece6681fcbfd0810603af1277c36c545c3ac` | canonical acceptance | `cudaq_grover_plugin` | `gpu_serial/aiqec` | pending |
| `tests/test_simulator_frontend.py` | `e155e98d465bb4d99ee93b3ad603da64d25a7318f889bd5a7cf3e90e72625a25` | canonical acceptance | `frontend_compile_and_records` | `cpu_light/ecs` | pending |
| `tests/test_simulator_frontend_structure.py` | `3898e4e0fe92850fb5c11cea4f5ff730cbec0c147873614c267692ddfb346dfc` | noncanonical pytest | `-` | `-/-` | pending |
| `tests/test_simulator_mcwf_backend.py` | `3ca88edbab966957e1fa80bd5f5aef485e284cb07571a09f217dce1865ef7d51` | canonical acceptance | `dense_qudit_mcwf_carrier` | `gpu_serial/ecs` | pending |
| `tests/test_simulator_mcwf_grover.py` | `a4aee2ae9e31decaa393c6c368af7bea37c998de6a0bbeda60af30a49984f26d` | canonical acceptance | `dense_mcwf_grover` | `gpu_serial/ecs` | pending |
| `tests/test_simulator_noise_module.py` | `8d0664f0b549624adfd501651592b78fc07392f11e48c7fcd94588b7868fff11` | canonical acceptance | `frontend_compile_and_records` | `cpu_light/ecs` | pending |
| `tests/test_simulator_noiseless_interface.py` | `244a03bf0f95b564971e5ad928c94203f40b4328aad6f802b7ce106e1c87aeb3` | noncanonical pytest | `-` | `-/-` | pending |
| `tests/test_simulator_ququart_transport.py` | `6aa042740433fbae5e74a0c4d3bad78d6d422731735d435122c3ec990dfb8344` | canonical acceptance | `ququart_cz_transport` | `gpu_serial/ecs` | pending |
| `tests/test_simulator_qutip_cuquantum_backend.py` | `9ab6024651f1759d099cd792b8944b0f01da82ce05df87b1caa809eadaccbdf9` | canonical acceptance | `qutip_cuquantum_probe` | `gpu_serial/ecs` | pending |
| `tests/test_simulator_qutrit_leakage.py` | `c682cd26e8e5f27a850effa4b348a7ad89b456c81cd11e0b98c7b7a853dbd34a` | canonical acceptance | `qutrit_wg_frontend` | `gpu_serial/ecs` | pending |
| `tests/test_simulator_record_batch.py` | `882d72527e30fafb8085e6af27a9ae2b817f3fe3ee3c810e18f46119d173b81f` | noncanonical pytest | `-` | `-/-` | Batch 1A: ordinary Stim-to-RecordBatch artifact/provenance smoke; no adversarial binary, immutability, packing, or generic-prior oracle |
| `tests/test_simulator_source_projection.py` | `43353c8c5bc2fc5ec4f303424bf403284ccac99618edd28402018c7f37813477` | canonical acceptance | `source_stim_pauli_projection` | `cpu_light/ecs` | pending |
| `tests/test_simulator_source_sidecar.py` | `05c735a3f3f53579f8ec6e3b0258d2e81105aacbd14bc8e5b55ce198ec573eb0` | canonical acceptance | `source_stim_pauli_projection` | `cpu_light/ecs` | pending |
| `tests/test_soft_readout.py` | `1fa9778abd564660f4cda44b9b08fc0245b8c9a4e40a499d88bf9e30f16784d6` | noncanonical pytest | `-` | `-/-` | pending |
| `tests/test_source_closed_forms.py` | `5f7aae536284de2c24a39d2ce0d75ec20b3daee522aed048f0ffc0f4f0f78e8a` | noncanonical pytest | `-` | `-/-` | pending |
| `tests/test_source_coupling.py` | `847d008b2349ee802106f924c7294b472378d134d00e60171b8ba065f8c30a29` | noncanonical pytest | `-` | `-/-` | pending |
| `tests/test_source_coupling_units.py` | `063260b2a86baee4f81c750b60a4286b142a56a46ecfcb822305ab8662611c5c` | canonical acceptance | `classical_1f_nonmarkov_chain` | `cpu_light/ecs` | pending |
| `tests/test_source_process.py` | `4c86ef9be44801063afd8afe14d7069852aff8daf940b7bc5a170dbdca9b1785` | canonical acceptance | `classical_burst_storm_sources` | `cpu_light/ecs` | pending |
| `tests/test_source_process_units.py` | `bb86da51f8c65bc3575d91387dfd6414f1dbc3c8dfbe08b21ccd54eb7a685f60` | canonical acceptance | `classical_1f_nonmarkov_chain,classical_burst_storm_sources` | `cpu_light/ecs` | pending |
| `tests/test_steady_state_fusions.py` | `41c1f66a274d5640c568ed0b9488ededcebe4d046473fa448f2afc2db351137d` | noncanonical pytest | `-` | `-/-` | pending |
| `tests/test_stim_io_units.py` | `aa59aaf623446fe93e00f8ea29b59b7e27bc0e2c1230fd3ce73e8ed32e7034f1` | noncanonical pytest | `-` | `-/-` | pending |
| `tests/test_stim_source_units.py` | `76a7873c18f3e043bda213691a0d99fd32f222c1056ff108f9d4a4adec2658e6` | canonical acceptance | `frontend_compile_and_records` | `cpu_light/ecs` | pending |
| `tests/test_sv_traj_d3_loader_units.py` | `ff3b2799a3a56347916c7513edad964efcb9c0dab255b8a3a8d10851ccac90c4` | canonical acceptance | `fused_within_cycle` | `gpu_serial/ecs` | pending |
| `tests/test_window_channel.py` | `2572022c3496ca79782ccf777defdcdb5a29f4c2acd2e480de609d4f53c09893` | noncanonical pytest | `-` | `-/-` | Batch 1B1 TP/Choi checks share project conventions; Batch 1B2a1 cross-implementation comparisons use installed NumPy builders as expected values; Batch 1B2a2 lines 386--404 mirror AD, stochastic-Z phase damping, excitation, leakage surrogate, custom, depolarizing, and correlated relaxation with the same NumPy/project builders, so they are cross-implementation mirrors rather than independent physical oracles |
| `tests/test_within_cycle_host.py` | `2ea888e363793c1cce59eb1d477ad218321b5953b7d8547c5d67569d8c375c11` | noncanonical pytest | `-` | `-/-` | pending |
| `tests/test_within_cycle_precision.py` | `4cd82a14033394494f9839b8fa5f225594fb3d9529165d0264218f8f2f740b00` | canonical acceptance | `fused_within_cycle` | `gpu_serial/ecs` | pending |
| `tests/test_xzzx_parser_owner.py` | `b79fcf659ef76506c02bf47af19105507c57bcac4de278887c729f89175733d0` | canonical acceptance | `xzzx_external_schedule` | `cpu_light/ecs` | pending |

## 14. Final human adjudication

- [ ] all 113 installed implementation files have a reverse-coverage disposition
- [ ] all 52 canonical acceptance files have a verification disposition
- [ ] all noncanonical test/harness files have been screened for scientific formulas or gates
- [ ] every closing primary-source equation page has been visually checked
- [ ] every source-to-code graph has been replayed
- [ ] high-risk markers and downstream propagation have been reviewed
- [ ] contradicted/misapplied findings have been reviewed
- [ ] cross-source composite bridges have been reviewed
- [ ] formula correctness verdicts have been reviewed
- [ ] application-fit verdicts have been reviewed
- [ ] value provenance verdicts have been reviewed
- Human verdict: unchecked
