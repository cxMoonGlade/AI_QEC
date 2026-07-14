# HANDOFF — simulator scientific-formula provenance audit (2026-07-14)

> **Purpose:** hand a new session one bounded, exhaustive, read-only scientific audit. This file is
> an execution contract, not evidence that any formula is correct. `docs/SIMULATOR.md` remains the
> binding product specification; `docs/CODE_MAP.md` and `docs/service_status.json` define the live
> distribution surface.

## 0. Mission and final deliverable

Audit **every scientific formula that the current `error_coupling_simulator` distribution uses**.
For every formula, give the normalized mathematics, exact literature source, exact implementation
location, downstream role, assumptions, source-to-code mapping, and two separate verdicts:

1. is the formula itself transcribed/derived correctly?;
2. is it used for the correct scientific object, regime, schedule position, and observable?

The single final deliverable is:

```text
docs/SCIENTIFIC_FORMULA_PROVENANCE.md
```

That file is separate from `docs/NUMERICAL_PROVENANCE.md`:

- `SCIENTIFIC_FORMULA_PROVENANCE.md` audits equations, derivations, conventions, placement, and
  applicability;
- `NUMERICAL_PROVENANCE.md` audits the values inserted into them, including units, device scope,
  and conversion/calibration chains.

If an exact source cannot be verified, the formula row must contain the literal visible marker:

```text
高危无出处
```

Do not replace it with “standard,” “well known,” “project convention,” “likely,” or an adjacent
citation. The human owner will personally inspect every row; all human-verdict boxes remain
unchecked until that happens.

## 1. Read in this order

1. `CLAUDE.md` — current main line, commands, and red lines.
2. `docs/SIMULATOR.md` — binding object/product/carrier contract.
3. This handoff — audit scope and completion contract.
4. `docs/service_status.json` — exact 27-service ownership, support, exclusions, acceptance files,
   and complete flow data.
5. `docs/CODE_MAP.md` — generated reverse module inventory and Mermaid service flow; do not edit it
   manually.
6. `docs/ARCHITECTURE.md` and every owning module `README.md`.
7. `docs/FAITHFULNESS_PROTOCOL.md`, `docs/METRICS.md`, and
   `docs/NUMERICAL_PROVENANCE.md` — evidence, metric, and value-provenance constraints. Treat their
   citations and verdicts as audit inputs, not automatically verified conclusions.
8. `docs/twin_validation/HANDOFF_literature_closure_and_status_2026-07-13.md` — previous scientific
   status and known open bridges; its old execution snapshot is superseded by Section 2 below.
9. `docs/papers/CONCEPT_INDEX.md`, `docs/papers/reading_notes/`, and the actual full-text papers.
   RAG/KG/notes are discovery surfaces only.

## 2. Frozen engineering snapshot

Audit the **current live worktree**, not bare Git `HEAD`:

```text
snapshot_date: 2026-07-14
HEAD: d5434c1b8b5d7373967b774ad68971fafb3189dc
worktree: DIRTY — many existing modified and untracked files; preserve all of them
service_catalog_schema: error_coupling_simulator.service_status.v2
service_catalog_sha256: f0159cd1d2fc1a8a1678a0aff7c642cc9c6e43bf3cf2905ab27ace126e7b5878
CODE_MAP_file_sha256: 80b0ab178d6db7f017ebd81ffbf875a406d2fa81a2087218218bd4d0518d5a4d
CODE_MAP_input_sha256: d32bb846743cdd403c581a5d2769a0fba580281eecf07dd6811e75d09f08e131
```

Current catalog/distribution surface:

- 27 services and 8 explicit exclusions;
- 109 installed Python modules: 81 service-owner modules + 28 support modules;
- 4 native source files in 3 native families:
  - `carrier/kernels/fused_kraus_local.cpp` and `fused_kraus_local.cu`;
  - `carrier/kernels/qutrit_mcwf_ops.cu`;
  - `carrier/kernels/sv_traj_d3.cu`;
- 52 unique canonical acceptance files;
- 47 flow nodes and 89 flow edges.

Latest canonical engineering/service gate:

```text
52 / 52 acceptance files PASS
26 cpu_light + 6 cpu_exclusive + 20 gpu_serial
51 files in ecs + isolated CUDA-Q file in aiqec
summary: outputs/twin_validation/logs/service_acceptance/
         run-20260714T184829.985740Z-p1945132-a000623a/summary.json
```

This proves the service and execution contracts run. It **does not prove any scientific formula is
correct, sourced, independently grounded, or used in the right place**. Never promote `52/52 PASS`
into a scientific verdict.

At audit start, refreeze the live source manifest because line numbers and the dirty worktree may
have changed:

```bash
git rev-parse HEAD
git status --short
python tools/gen_code_map.py --check
find src/error_coupling_simulator -type f \
  \( -name '*.py' -o -name '*.cu' -o -name '*.cpp' -o -name '*.cuh' -o -name '*.hpp' \) \
  -not -path '*/__pycache__/*' -print0 | sort -z | xargs -0 sha256sum
```

Record the resulting manifest digest in the final audit. If any audited source changes mid-audit,
stop, refreeze, and identify every row that must be rechecked. Do not silently mix snapshots.

## 3. Scientific status that the engineering gate does not upgrade

The formula audit begins from **unknown until checked**, not from “tests pass.” Preserve these open
boundaries:

- the source-conditioned dense-qubit path and static data-qutrit XZZX path remain disconnected
  implementation islands; the production bridge is `OPEN / CODE_BLOCKED`;
- the full multi-round record faithfulness of finite PEPS truncation is not established;
- the current whole-horizon readout/reset policy is not established as a causal,
  prefix-consistent map family;
- current source lowering reaches only the implemented `zeta` and `gamma_phi` coordinates, not a
  narrated all-mechanism source-to-leakage chain;
- d5/d7 distributional claims remain PROVISIONAL and are never premises;
- formal exact-DM, QuTiP, closed-form, and test oracles are bug-catchers, not physical ground truth;
- a test comparing two routes that share the same formula or convention is not independent
  certification.

Existing docs may contain strong language, historical formulas, reopened conclusions, or stale
line references. The audit must read the live code and primary source rather than inherit a prose
verdict.

## 4. Exhaustive scope — what “all formulas” means

### 4.1 Runtime and installed support surface

Inspect every one of the 109 installed Python modules classified by the generated CODE_MAP,
including CORE, OPTIONAL, RESEARCH, ARCHIVED, and support modules. A support module can still carry
scientific semantics. Every file receives one of exactly three dispositions in the final reverse
coverage appendix:

1. one or more formula IDs;
2. `无科学公式：仅 namespace/编排/序列化/校验/软件资源管理` with a concrete reason;
3. explicit exclusion authorized by Section 5.

Do not infer “no formula” from a filename or from the catalog calling a module support. Read it.

### 4.2 Native source

Inspect all four `.cpp/.cu` files at source level. Determine whether each arithmetic operation is:

- a native mirror of a separately audited Python formula;
- an independent implementation of a scientific formula;
- indexing/layout arithmetic with no scientific content.

Link mirrors to the same formula ID and audit dtype, basis order, conjugation, normalization,
sampling, and RNG semantics. Do not inspect binary disassembly.

### 4.3 Verification-side formulas

Separately audit every formula in the 52 acceptance files, formal anchors, and tracked gates that is
used as an independent reference, invariant, metric, pass band, negative control, or hand-typed
literature formula. Mark each as `runtime`, `oracle`, `test-reference`, `metric`, or `gate`.

A test-side formula must not be cited as literature, and a reference copied from runtime is not
independent. Threshold formulas and physical formulas are distinct rows.

### 4.4 Scientific values and transformations

For each formula, also inventory scientifically meaningful defaults, fitted constants, unit
conversions, normalization factors, time slicing, rate/probability conversions, and regime
thresholds. Link each value row to `docs/NUMERICAL_PROVENANCE.md`, but verify it against the live
code and exact source. A paper equation supporting a functional form does not support the numeric
value inserted into it.

### 4.5 Delegated third-party operations

Do not audit the internal implementation of Torch, SciPy, Stim, QuTiP, cuQuantum, quimb, PyMatching,
or CUDA-Q. Do audit every project-supplied Hamiltonian, collapse operator, channel, tensor,
probability, schedule convention, and observable passed to those libraries, plus the assumptions
under which the selected third-party operation is scientifically valid.

### 4.6 What counts as a scientific formula

Include, at minimum:

- Hamiltonians, generators, master equations, collapse/jump operators, rates, spectra and
  correlation functions;
- channel constructions and conversions: unitary, Kraus, Stinespring, superoperator, Choi, PTM,
  Pauli twirl, composition, embedding, and partial traces;
- measurement effects and instruments, Born probabilities, branch updates, readout/reset rules,
  detector folding, record probabilities, and logical-observable maps;
- stochastic-source laws: RTN transition laws, finite-band 1/f construction, Lorentzian PSDs,
  HMMs, burst/storm laws, source-to-parameter fan-out, and controls;
- numerical physics: matrix exponentials, product formulas, Trotter/microstep rules, MCWF jump and
  no-jump evolution, trajectory normalization and sampling;
- tensor-network formulas: MPS/PEPS/PEPO contractions, truncation objectives, SVD/discarded weight,
  FET/WTG/ZMT quantities, Born sampling, and approximation/error claims;
- qutrit/ququart leakage and CZ transport, Wood–Gambetta quantities, heating/seepage/readout models;
- quantum-bath GKSL/pseudomode/QRT/null/witness formulas;
- metrics, estimators, certification anchors, confidence/error bands, and claimed bounds;
- dimension, memory, scaling, or complexity formulas when they support a scientific feasibility or
  carrier claim rather than mere logging.

Pure byte packing, hashes, path handling, process scheduling, logging, CLI parsing, schema plumbing,
and index arithmetic are not scientific formulas unless the index/basis/order changes physical
semantics.

## 5. Explicit exclusions

- `legacy/` downstream inference, calibration, hardware analysis, and Bayes-floor/headroom code;
- the retired old XZZX thin-strip driver;
- repository-only experiments under `outputs/`, except an output/gate explicitly used as the
  current service's independent scientific reference;
- third-party library internals;
- docs-only historical proposals that are neither implemented nor used as a current oracle/gate.

The installed ARCHIVED PEPO service remains in scope because it ships. The installed compatibility
catalog/seam support also receives a coverage disposition even when it is not an active production
route. Frozen `qec_twin.*` schema strings are not runtime formulas.

## 6. Evidence levels and mandatory verdicts

Every formula gets exactly one provenance status:

| Status | Meaning | Can close source provenance? |
|---|---|---|
| `DIRECT` | Same or strictly equivalent formula in the verified full text, with matching object and assumptions | yes |
| `DERIVED` | Completely replayable project derivation from `DIRECT` equations/theorems, with no hidden step | yes, but label `[ours-derived]` |
| `COMPOSITE-UNCLOSED` | Components have sources but their combination, placement, or mechanism→observable bridge does not | no |
| `ADJACENT-ONLY` | Only a related model, summary, abstract, RAG/KG hit, reading note, docstring, or secondary statement | no |
| `NO-SOURCE` | No exact verifiable source found after recorded search | no |
| `CONTRADICTED/MISAPPLIED` | Source exists but code or use conflicts with it, or its assumptions do not hold | no; immediate high-risk finding |

Mandatory visible markers:

- `COMPOSITE-UNCLOSED` → **高危无出处（组合公式整体无直接出处）**;
- `ADJACENT-ONLY` → **高危无出处（仅有邻近/二手证据）**;
- `NO-SOURCE` → **高危无出处**;
- a paper supports only the form but not coefficient/normalization/slicing/placement →
  **高危无出处（文献仅支持形式）**.

`project-design` and “standard practice” do not waive these markers for a scientific formula.
Numerical-only software tolerances may be classified as non-scientific controls, but any threshold
used to make a scientific conclusion remains in scope.

Provenance does not equal correctness. Record these four axes independently:

```text
formula_correctness: correct | incorrect | unresolved
application_fit: matched | mismatched | bridge-open
value_provenance: complete | project-design | incomplete
human_verdict: unchecked | accepted | rejected
```

No agent may set `human_verdict` to accepted or rejected.

## 7. Exact-source minimum

A source closes a row only when the audit records all applicable items:

- authors, title, year, publication status, DOI and/or **versioned** arXiv ID;
- correction/retraction status;
- local PDF path and SHA256;
- PDF page index and printed page, section/subsection, Eq./Theorem/Proposition/Appendix/Supplement
  locator;
- visually verified equation page;
- source symbols mapped one by one to code symbols;
- Hilbert space, basis and Kronecker/index order;
- units and angular-frequency versus cyclic-frequency convention;
- source assumptions and code regime;
- frozen `file:line`, function/class qualname, service ID, and call path.

Only a DOI, paper name, bibliography entry, or reading-note path is not a specific formula source.
The load-bearing PDF equation must be visually checked; text extraction is navigation, not math
ground truth.

## 8. Formula-row schema for the final Markdown

Use stable IDs such as `ECS-AX1-001`, `ECS-RTN-001`, or `ECS-PEPS-001`. Do not collapse different
normalizations, regimes, or placement rules into one “formula family.” Each formula section must
contain this schema:

```markdown
## <Formula ID> — <name>

### Formula and role
- Normalized formula: $$ ... $$
- Literal code realization:
- Role: mechanism | source | generator | channel | carrier | sampling |
  instrument | record-transform | metric | anchor | bound
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
```

The final document also requires:

1. a service/module coverage summary;
2. a compact formula index;
3. a **High-risk no-source register**;
4. a contradicted/misapplied register;
5. a cross-source composite register;
6. a source-artifact manifest with hashes;
7. a search/closure ledger;
8. a reverse-coverage appendix for all 109 Python modules and 4 native files.

## 9. Sequential agent protocol — one at a time

Do not parallelize formula agents. The coordinator owns the single final Markdown and starts the
next agent only after the previous batch is merged and coverage-checked. Fresh context is useful;
shared concurrent edits are not.

For each batch:

1. start one un-led extractor agent with only the files/services, scope, and row schema — do not
   tell it the expected verdict;
2. the extractor reverse-enumerates formulas from code, then closes sources and writes its rows;
3. stop that agent;
4. start one separate reviewer agent, also alone, with the code, sources, and produced rows;
5. the reviewer checks completeness, equations, exact locators, mapping, applicability, and
   coverage; it must search for omissions and contrary sources;
6. merge corrections and update the coverage appendix;
7. only then begin the next batch.

Recommended batch order follows the implemented service flow rather than filename order:

| Batch | Scientific surface |
|---|---|
| 0 | coordinator freezes file/service/source manifests and creates the final Markdown skeleton |
| 1 | numerical conventions, channel algebra, Kraus/Stinespring/Choi/PTM, exact-qubit DM, record fold |
| 2 | frontend noise/compile/schedule formulas, Stim projection, record I/O, DEM reduction, optional decoder |
| 3 | Axis-1 Hamiltonians, ideal controls, collapse operators, joint Lindbladian, dense record evolution |
| 4 | RTN, finite-band 1/f, PSD/correlation conventions, burst/storm/HMM sources, `Theta(z_t)` fan-out, coupled cycle |
| 5 | exact-qutrit DM, WG leakage/seepage, readout/reset instrument, ququart CZ transport |
| 6 | generic dense MCWF, fused within-cycle execution, all native mirrors, Grover and isolated CUDA-Q plugin |
| 7 | restricted Axis-1 MCWF/MPS and QT/MPS product-formula verification routes |
| 8 | active single-wire PEPS: codestate, contractions, stabilizer TT, Born sampling, FET/truncation diagnostics |
| 9 | shipped ARCHIVED PEPO findings route and every reused PEPO→PEPS scientific formula |
| 10 | quantum-bath GKSL/pseudomode/QRT/null/memory-witness research suite |
| 11 | formal certification, closed-form/DM/Stim anchors, channel diagnostics, metrics, bands, and negative controls |
| 12 | verification-side independent formulas across all 52 acceptance files and tracked current gates |
| 13 | reverse-coverage closer: all modules/native files, duplicate IDs, high-risk propagation, and source manifest |

If a batch is too large for one agent context, split it by service, but preserve strict sequential
execution and extractor→reviewer order.

## 10. Required literature and falsification workflow per formula

This is an audit of existing results, so use `theory-fix`, not `theory-first`, unless a later,
separately authorized repair proposes a new formula.

For each formula or tightly bounded formula family:

1. freeze the exact code claim, scientific object, role, measured observable, assumptions,
   alternatives, and downstream consumers;
2. query local evidence first:

   ```bash
   conda run -n aiqec python -m qec_twin.rag.store \
     --query "<formula mechanism observable bridge>" --top-k 12
   conda run -n aiqec python outputs/knowledge_graph/kg_query.py concept "<concept>"
   ```

3. treat RAG/KG hits as discovery only; build a gap ledger for form, coefficient, normalization,
   units, approximation, placement, mechanism→observable bridge, and contrary/no-go evidence;
4. search externally for every missing or project-inference-only row and explicitly search for
   null/no-go/failure/limitation/alternative conventions;
5. deep-read every load-bearing full text, visually verify formula pages, and perform an operation
   replay from source equation to code output;
6. separate `[paper]` from `[ours-derived]` at every transformation;
7. stress-test the formula and its placement against symmetries, dimensions, independent oracles,
   alternate formulations, and known failure regimes;
8. write `高危无出处` rather than continuing from an unclosed premise;
9. update the final Markdown, then send it to the sequential reviewer.

An unavailable paper, search outage, or missing supplement is `open`, not evidence that no source
exists. It can become a field-level confirmed literature gap only after the full recorded closure
workflow; the formula row remains visibly high-risk meanwhile.

## 11. Source-to-code mapping must be a graph, not a citation sticker

For any adapted or composite formula, reconstruct:

```text
primary-source equation
  -> symbol / basis / vectorization transform
  -> unit and angular-frequency conversion
  -> continuous-to-discrete or rate-to-probability conversion
  -> approximation / truncation / product formula
  -> multi-mechanism composition
  -> circuit substep / support placement
  -> measurement instrument
  -> temporal detector record / metric
```

Every edge needs a source or an explicit project derivation, assumptions, and an error statement.
Several individually sourced components do not source their composition. One paper sourcing a
mechanism and another sourcing an observable does not source the mechanism→record bridge.

## 12. Mandatory correctness trip-wires

At least check these for every applicable row:

- missing signs, adjoints, complex conjugates, transposes, factors of 2, 4, `pi`, `2pi`, or `hbar`;
- angular frequency vs cyclic frequency; ns/us/s and per-gate/per-cycle/per-time units;
- population decay vs amplitude decay; `T1`, total `T2`, and pure `T_phi` conventions;
- GKSL/Lindblad normalization and whether rates sit in `L` or in the collapse amplitude;
- row/column vectorization, Choi normalization, PTM ordering, endianness, Kronecker order, and
  qutrit/ququart basis order;
- Hamiltonian vs channel vs POVM effect vs selective instrument — never treat them as the same
  object;
- continuous-time RTN switch-rate convention, stationary probabilities, Lorentzian one-/two-sided
  PSD, finite-band normalization, and cycle-held discretization;
- probability clipping or logit transformation changing the intended source law;
- MCWF no-jump norm, jump probabilities, branch normalization, random-stream reuse, and ensemble
  equivalence conditions;
- Trotter/product-formula ordering and missing commutator/error terms;
- physical pulse/frame distinction and exact schedule/substep placement;
- raw syndrome versus temporal detector fold at `R>=2`;
- source law versus whole-horizon policy versus causal/prefix-consistent process;
- local state/bond/truncation objective versus the claimed complete record or rare LER bound;
- cross-paper/device composite compatibility and source form versus inserted value.

## 13. Known high-risk seeds — not an exhaustive list and not pre-judged verdicts

Give each extractor these only after its un-led enumeration, so they do not cap discovery:

- `exp(L/4)` within-cycle quarter-slice convention;
- `phi_ZZ = zeta*t/4` and every static-ZZ/fSim normalization;
- finite-RTN sum normalization, switch-rate convention, Lorentzian PSD, and “1/f” band claim;
- source-to-`zeta`/`gamma_phi` fan-out and whole-horizon readout/reset policy;
- Wood–Gambetta `L1/L2` definitions and conversion to `theta/g_seep/g_heat`;
- leaked-readout bias `b` and the effect→instrument distinction;
- source-to-Stim Pauli projection and probability clipping;
- MCWF, MPS, PEPS, and PEPO branch probabilities, product formulas, and normalization;
- FET/WTG/ZMT objectives and any claimed bridge to complete-record faithfulness;
- pseudomode GKSL, Crow–Joynt null, QRT, concurrence/Choi witness formulas;
- TV/KL/NLL/CMI/`G^2`/BLP/RHP/`p_ij`/LER/`Lambda` formulas and whether their use matches the
  measured object;
- every hand-typed “independent” formula in a test, gate, or certification anchor.

Existing `METRICS.md` and `NUMERICAL_PROVENANCE.md` are valuable seeds, but neither is the completed
formula audit and neither may pre-clear a row.

## 14. Hard red lines

- Audit is read-only with respect to `src/**`, tests, tolerances, numerical floors, FET settings,
  bond caps, and precision policy.
- Do not run new d5/d7, FET, tolerance, or claim-bearing experiments.
- Do not “fix while reading.” Record an error or misapplication in the final Markdown and stop its
  downstream propagation; implementation repair requires a later explicit user authorization.
- Do not use low-level binary disassembly. Read the scientific Python/CUDA/C++ source.
- Do not use a passing test, own oracle, docstring, old preregistration, RAG/KG hit, abstract, or
  reading-note summary as a literature source.
- Do not call a form citation a parameter citation or a physical/hardware calibration.
- Do not use downstream teacher/learner, inference, hardware-fit, or Bayes-floor framing as the
  simulator object. Use specified noise process, mechanism, carrier, instrument, record, metric,
  and formal anchor.
- Do not reset, clean, mass-format, or overwrite the dirty worktree.
- No full 52-file rerun is needed for formula inventory. If any later test is justified, use the
  canonical process-isolated runner; never merge native stacks into one long-lived pytest process.
- CUDA-Q stays in `aiqec`; the simulator core stays in `ecs`.

## 15. Definition of complete

The final Markdown is complete only when all are true:

- all 27 services, all 81 service-owner modules, all 28 support modules, and all 4 native files
  reconcile exactly against the frozen catalog/source manifest;
- every in-scope file has formula IDs or an explicit inspected-no-scientific-formula disposition;
- every scientific formula has a normalized equation, symbols/units/basis, code qualname and line,
  service/call path, role, assumptions, downstream consumers, and independent checks;
- every source claim has a full-text artifact, hash, exact locator, visual formula check, and
  source-to-code mapping;
- every formula has separate provenance, correctness, application-fit, value-provenance, and human
  verdict fields;
- every unclosed, adjacent-only, composite-unclosed, contradicted, or misapplied row is present in
  the appropriate high-risk register with downstream propagation sites;
- runtime, oracle, test-reference, metric, and gate formulas are distinguishable;
- duplicated implementations/native mirrors reconcile to the same formula or explicitly document
  their difference;
- the source-artifact manifest and search/closure ledger are complete;
- a final sequential reviewer reruns reverse coverage and reports zero unclassified files and zero
  silent `TBD`/“standard” provenance placeholders;
- all `Human verdict` fields remain `unchecked` for the owner to decide.

Finding an error, a misapplication, or `高危无出处` does **not** make the audit incomplete. Hiding it
does. The audit is an inventory and decision surface, not a promise that every formula will pass.

## 16. Prompt for the new session

```text
Read CLAUDE.md, docs/SIMULATOR.md, and
docs/twin_validation/HANDOFF_simulator_scientific_formula_audit_2026-07-14.md.

Run the scientific-formula audit exactly as handed off. Create only the single final ledger
docs/SCIENTIFIC_FORMULA_PROVENANCE.md. Work read-only against src/** and tests. Freeze the live
dirty-worktree source manifest first. Use one formula agent at a time, followed by one separate
reviewer at a time; never run formula batches concurrently. Audit all 109 installed Python modules,
all 4 native source files, the 52 acceptance files' independent formulas, and current formal
anchors/gates. For every scientific formula give its LaTeX form, exact full-text literature locator,
source-to-code derivation, file/qualname/line, service/call path, scientific role, assumptions,
correctness, and application-fit verdict. If exact provenance is not closed, write the literal
marker 高危无出处 (with the specified subtype). RAG/KG/notes/tests are discovery or checks, not
literature evidence. Do not change formulas, tolerances, FET, precision, or run new d5/d7 work.
Leave every human-verdict box unchecked for me.
```

## 17. Dirty-worktree preservation

The current state contains substantial user-owned and prior-session modifications plus untracked
files. Inspect `git status --short` before every write. Do not reset, clean, restore, rename, or
reformat unrelated files. The only required audit write is
`docs/SCIENTIFIC_FORMULA_PROVENANCE.md`; durable paper notes/cache/index maintenance may be added by
the literature workflow, but they are auxiliary evidence and must be linked from the one final
ledger. Do not commit or push unless the user asks.
