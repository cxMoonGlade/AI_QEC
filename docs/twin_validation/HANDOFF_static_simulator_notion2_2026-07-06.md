# HANDOFF — static QEC error-coupling SIMULATOR — GOAL, positioning & next steps, 2026-07-06

> **SUPERSEDED ON NOTION 1/2/3, 2026-07-13.** The simulator may retain notion-3 as out of product
> scope, but not because a universal physical-twirl/no-passive-witness theorem was proved. `K` is a
> protocol-family Kolmogorov test, and coherent/non-unital record reachability is mechanism/schedule
> dependent. See
> [`notion123_taxonomy_literature_closure_2026-07-13.md`](notion123_taxonomy_literature_closure_2026-07-13.md).
> The CP-div result belongs to a Gaussian surrogate, not the production finite-RTN source, and the
> `s<=.3`, `N<=1e6` “realistic” cap is a project threshold only. Value authority:
> [`../NUMERICAL_PROVENANCE.md`](../NUMERICAL_PROVENANCE.md).

**SELF-CONTAINED.** This hands off the mainline **static (passive-record) QEC error-coupling simulator** after a
session that (1) CLOSED the notion-3 quantum-memory line as a literature-grounded protocol boundary and (2) ran the
first corrected effect-size go/no-go (Class-1), which **honestly capped** the mild-1/f route, and (3) **reframed the
GOAL to an INFRASTRUCTURE contribution** (§0/§0b — online-grounded competitive analysis). It supersedes the
open items of `HANDOFF_simulator_nonmarkovian_visibility_2026-07-04.md` (still the master map; read its §0/§1/§2/§6)
by resolving its Track 1 Step 1 for Class-1. `[[...]]` links are Claude-Code auto-memory notes, not repo files.

---

## 0. Mission + scope (the GOAL — reframed 2026-07-06)
**The goal is a USABLE TOOL for a specific, plausibly-unowned CONJUNCTION: generate QEC error records `{det,obs}` /
DEM from [LEAKAGE + non-Markovian TEMPORAL coupling + SHARED-LATENT cross-mechanism coupling] TOGETHER, at d3–d5,
oracle-bounded, Stim/DEM-interoperable** — the thing you reach for when Stim's Pauli noise (and even
Deltakit/PECOS/Tsim's phenomenological leakage/coherent models) cannot give you that faithful *coupled* record.
**Due-diligence** (`conjunction_ownership_duediligence_2026-07-06.md`, 2026-07-06): **①** the triple-conjunction-as-a-
tool is **PROVISIONALLY UNOWNED** (each axis/pair owned separately — Quiroz 2412.16092 non-Markov+crosstalk but a
gate-noise model not a QEC generator; chain-mapping shared-bath; Darmawan leakage); **②** deliverable + usable at
**d3 (exact) / d5 (MPS-truncated, oracle-bounded)** — the classical couplings are free, only the leakage-qutrit level
count sets the wall. It is a CONJUNCTION + PACKAGING contribution, NOT new physics (accepted). It ingests device-grounded coupled mechanisms and emits QEC records
`{det,obs}` + a DEM in **Stim/DEM-interoperable** form, with every mechanism's generation error **bounded vs an
INDEPENDENT exact oracle**. It is NOT a decoder, NOT a twin (`recover`/`do()`/active-observation are a SEPARATE LATER
project, OUT OF SCOPE — [[feedback-simulator-is-goal-twin-is-next]], [[feedback-simulator-not-decoder]]), and NOT a
bid for a new physics observable (the coupled-noise physics is already explored in research code — see §0b).

**Two legs of validity, RE-RANKED (2026-07-06):**
- **(i) FAITHFULNESS = THE gate + the differentiator.** The generated record matches an INDEPENDENT oracle (exact
  qutrit-DM / QuTiP / ACE / from-scratch / closed form), with a declared, bounded error per mechanism
  (`docs/FAITHFULNESS_PROTOCOL.md`). No sampler/product found *advertises* this oracle-bound (§0b) — it is the
  **candidate** moat, but UNVERIFIED and possibly narrow/research-contested (QMCtwin/SPP/Darmawan); verify before betting.
- **(ii) anti-toy legitimacy = DEMOTED to an optional VALUE-MAP flag.** "Is this regime beyond a matched Markov-k /
  Stim-DEM null?" now *labels when a user should reach for the tool*, NOT a build gate. A regime being Stim-DEM
  tractable is fine — it just means Stim suffices there; the tool's value is the regimes it does NOT.

NOTE: `CLAUDE.md`/`docs/plan3.md` describe the OLDER `qec_twin` **twin** project; the live work is the
**`error_coupling_simulator`** package + `docs/twin_validation/`.

## 0b. POSITIONING & SUCCESS CRITERIA (competitive landscape, online-grounded 2026-07-06)
**⚠ CORRECTED 2026-07-06 (adversarial due-diligence search): the "empty niche" claim does NOT survive as first
framed. The noise-MODEL + sampling space — INCLUDING leakage and coherent — is substantially OCCUPIED.** Occupied vs
the (narrow, still-UNVERIFIED) surviving sliver:
- **OCCUPIED — fast samplers of a given noise model:** Stim (Pauli); **QuEra Tsim** (2026, non-Clifford/coherent,
  drop-in Stim API, GPU — but a *sampler* that applies pre-encoded noise, explicitly NO oracle bound); **NVIDIA
  CUDA-Q QEC** (Stim backend); **Qiskit-qec**.
- **OCCUPIED — phenomenological realistic noise MODELS incl. leakage + coherent:** **Riverlane Deltakit** provides
  ToyNoise / SD6 / **SI1000 (with leakage `pL`)** / **PhysicalNoise** (gate-time-parameterised) and delegates
  sampling to Stim; **PECOS** does coherent (state-vector) + leakage + dephasing; Riverlane QEC Explorer has a
  leakage+relaxation Stim extension. These are FITTED-RATE Pauli(+leakage) models, NOT physics-derived, NOT
  oracle-bounded.  *(Earlier claim "Deltakit = ToyNoise/depolarizing only" was WRONG — corrected here.)*
- **RESEARCH CODE for physics-DERIVED coupled noise:** QMCtwin 2606.19848 (Markovian Lindblad; no exact oracle at
  4^97), SPP / quantum-combs 2603.05474 (multi-time non-Markovian → Pauli-twirled), non-Clifford-crosstalk TN
  2605.29514, Darmawan qutrit-MPS 2308.08186 (leakage, 1D, approximation-free), non-Markovian spin 2507.08713.
- **THE SURVIVING NICHE — now VERIFIED (provisional), see `conjunction_ownership_duediligence_2026-07-06.md`:** a
  USABLE tool GENERATING QEC records from the CONJUNCTION [leakage + non-Markovian-temporal + shared-latent],
  oracle-bounded, Stim/DEM-interop. **① ownership: PROVISIONALLY UNOWNED** — no owner of the triple-as-a-QEC-generator
  found across the RAG精读 corpus + 4 adversarial web searches + fetches; each axis/pair owned separately (Quiroz
  non-Markov+crosstalk = a gate-noise model, not a QEC generator; chain-mapping shared-bath = a bath oracle; Darmawan
  = leakage, 1D). **② scale: usable at d3–d5** (leakage-qutrit sets the wall; the classical couplings are free; d7+
  via adoptable PEPS/boundary-MPS). **Risks:** Quiroz is close + productizable (time pressure); "unowned" is
  provisional (moderate confidence); the room is a narrow conjunction+packaging, not new physics. **Company to
  watch:** Qoro Quantum. Residual checks: the full-Quiroz leakage question + a small confirmatory d3 run.

**The three differentiators (the moat, in order of defensibility):**
1. **Oracle-bounded faithfulness ★** — every mechanism's generation error bounded vs an INDEPENDENT exact oracle.
   Research codes lack this (QMCtwin: no oracle at scale; Darmawan: 1D). Hardest to copy — this is where the project's
   faithfulness protocol becomes the product's moat.
2. **Coverage / unification** — one API spanning Pauli + coherent + leakage + latent-drift non-Markovian coupling, vs
   stitching 4 research codes.
3. **Interop** — emit Stim/DEM; plug into Deltakit / PyMatching / CUDA-Q. Without this it is not adoptable = not a
   contribution.

**Success criteria — "candidate → contribution" (a skeptic accepts it when):**
1. a faithful, oracle-bounded noise-generation engine + a **mechanism × oracle × error-bound × max-d** coverage table;
2. **interop:** emits Stim/DEM the standard stack ingests;
3. a **killer demo:** a record Stim-Pauli cannot make (leakage / coupled non-Markovian), bounded vs oracle, that
   changes a downstream result (a decoder's / threshold-estimate's behavior differs from the Stim-Pauli prediction);
4. (bonus) one real user/collaborator who needs Stim-impossible faithful coupled records.

**Judged by faithfulness + adoption + filling a verified gap — NOT by novelty** (Stim itself is the proof: no new
physics, a huge contribution). Standing goal alignment: [[project-goal-industry-twin]] ("judged by industry
adoption"). The science findings in §1 are NOT retracted — they are the **value-map** (where Stim suffices vs where
this tool must exist).

## 1. THIS SESSION'S PROGRESS (2026-07-06)

### 1a. notion-3 historical boundary claim — REOPENED / NARROWED 2026-07-13
The simulator may keep process-level quantum-memory identification out of product scope, but the old proof of
unreachability was invalid. Current narrow conclusions:
- **(A)** Full process-level identification generally needs an intervention/tester family. A fixed passive record
  is one projection and cannot support a model-free origin claim; this does not rule out every restricted witness.
- **(B)** Pauli-twirled baselines and some schedules suppress coherent structure, but there is no universal theorem
  that physical syndrome extraction erases all coherent or non-unital record effects. Marshall–Kafri and Manabe
  *et al.* provide QEC counterexamples; Varbanov *et al.* provide a schedule-specific near-null.
- **⇒ the passive record's content is mechanism-, schedule-, and instrument-dependent.** The in-house result:
  **Control 0b** (`outputs/twin_validation/notion3_control0b_classical_nm_negcontrol.py`, sha `1590fd59`) — a bare
  negativity/concurrence REVIVAL is RHP non-Markovianity, forged by classical RTN dephasing; only the genuine Bäcker
  `C♯(t1)<C(t2)` (an ACTIVE-channel quantity) survives, and it does not read the record. The `quantum_bath` package
  is retained as **forward-generation infrastructure**; its revival witnesses are relabeled backflow/non-Markovianity
  diagnostics (RETRACTED as quantum-memory). See `notion3_relaxation_dualaxis_prereg.md`,
  [[project-notion3-relaxation-dualaxis-Kz-forgeable]].
- **This SHARPENS the simulator:** twirl removes notion-3 (out of scope); the record RETAINS **notion-2** classical
  multi-time correlations the stochastic-Pauli baseline misses (QMCtwin positive KL gap) — that is the target.

### 1b. Class-1 notion-2 effect-size GO/NO-GO — HONEST CAP (mild-1/f route). (`e191cb65`)
First corrected go/no-go (Track 1 Step 1 re-sited to Class-1). Doc: **`notion2_class1_gonogo_prereg.md`**; script
`outputs/twin_validation/notion2_class1_gonogo.py`, GATE `CLASS1_GONOGO_CAP_A_SUBFLOOR`. Observable = the CORRECTED
**absolute lag≥2 `p_ij` shared-vs-off** (off = MA(1) structural zero), the 1/f source modulating ancilla readout
`p_ro`. Method: EXACT conditional delta-rate `E[D_r|x]=μ_{r-1}+μ_r−2μ_{r-1}μ_r` over a trajectory MC (no Bernoulli
noise; self-checks green). **RESULT — both guardrails FAIL at realistic drift:**
- **(A feasibility)** `N_detect_A` is sub-1e6-floor for realistic readout drift `s≤0.3` (readout-only crossover
  `s*>0.5`; readout+reset `s*≈0.45`).
- **(B non-Markov-k-trivial)** `N_detect_B ≈ 450–4500× N_detect_A` everywhere — the mild-1/f lag-2 shape gap vs a
  matched slow-RTN is only ~6% of the source autocov (`C_x(2)=0.696` vs `C_x(1)²=0.653`) ⇒ **Markov-k-trivial** even
  where detectable.
- **⇒ do NOT hard-build the Class-1 ancilla-axis architecture on this observable (G4-consistent registered STOP).**

**HISTORICAL KEY LEARNING, NARROWED 2026-07-13:** for this registered lag-2 observable and threshold, obstacle
**B** (non-triviality relative to the matched slow-RTN null) was deeper than raw detectability: the mild finite-RTN
mixture was nearly indistinguishable from that null. This is not a source-level CP-divisibility statement and does
not imply a universal twirl theorem. The Gaussian surrogate is CP-divisible; two explicitly declared exact
finite-RTN free-induction lifts are BLP-positive; the production fan-out/QEC-channel/record bridge remains open.

## 2. THE NEXT STEP (how to expand) — reframed 2026-07-06 to the infrastructure goal

Under the goal (§0/§0b) the PRIMARY track is the **infrastructure deliverables**, NOT a notion-2 legitimacy proof:
**(1)** a **faithfulness coverage table** — each coupled mechanism (`mechanisms/`+`source/`) × its independent oracle
(exact qutrit-DM / QuTiP / ACE / closed form) × the bounded generation error × the max `d` reached (leg (i) = the
gate + the moat); **(2)** an **`emit → Stim/DEM` interop** path so Deltakit / PyMatching / CUDA-Q ingest the records;
**(3)** a **killer demo** — a Stim-impossible coupled/leakage record, oracle-bounded, that changes a downstream
result vs the Stim-Pauli prediction.

The **anti-toy / notion-2 go/no-go is DEMOTED to a SECONDARY value-map tool** — it labels *which regimes* beat a
matched Markov-k / Stim-DEM null (i.e. *when* a user reaches for this tool over Stim), NOT a build gate. The Class-1
go/no-go already filled one cell — **mild 1/f is Stim-DEM-tractable** (don't advertise value there). The ranked
source-realism options below EXTEND that value-map (leakage is the leading candidate for a cell where the tool clearly
beats Stim-DEM, AND is the leading killer-demo source); run them to fill the map, not to justify the build:

- **RECOMMENDED FIRST — source-realism go/no-go with a genuinely non-Markovian source (attacks obstacle B directly,
  cheap, same harness).** Re-run the go/no-go with a **bursty / heavy-tailed / hidden-Markov** source instead of mild
  1/f: `TemporalStormSPPSource` (already in `source/process.py` — a 2-state HMM with tunable correlation length and a
  storm/calm Pauli marginal) and/or a strong non-Gaussian RTN. Test whether its lag≥2 (and joint multi-lag) imprint
  clears Guardrail B (separable from a matched slow-RTN / best-Markov-k) at N≤1e6. **This decides whether ANY
  realistic source gives a legitimate notion-2 signature on the passive record** — if yes, that source is the
  simulator's legitimacy core; if no, the honest conclusion is a deeper cap (the passive record can't legitimately
  carry non-trivial notion-2 either, for realistic sources). Predict-before-measure; class-(c) amplitude/correlation
  bracket; the same exact-conditional-rate MC + spitz SE + the Markov-k comparator (`gates/g5_baseline.py`) as the
  Guardrail-B null.
- **Joint multi-lag / CMI / differentiable-syndrome-NLL observable** (attacks B modestly). Use the whole lag vector
  (2..R) or CMI, not a single lag-2. Stronger than a single lag, but the mild-source ~6% gap is intrinsic — pair this
  with the richer source above, not with mild 1/f.
- **Class-2 (CZ-depol) siting** (attacks A). Deferred in the current teacher; only worth building if a source clears
  B first.
- **Stronger amplitude** (attacks A only, not B). Necessary but insufficient.

**Do NOT** build the full Class-1/2 architecture until a source clears **both** guardrails in a cheap go/no-go — that
is the whole point of the go/no-go gate (prevents building on a sub-floor or trivial signal). D1 (the realistic
source amplitude/sensitivity anchor) remains a **user decision**: commit a cited flux/charge/TLS-spectroscopy anchor,
or run a declared class-(c) sweep and report the bandwidth (as the Class-1 go/no-go did).

## 3. WHICH DOCUMENTS ARE CORRECT for the next-step static simulator

**OPERATIVE / CORRECT (build on these):**
- `docs/twin_validation/HANDOFF_simulator_nonmarkovian_visibility_2026-07-04.md` — the master map (scope §0, the
  three-error diagnosis §1, the corrected observable §2, the resource/reuse map §6). Valid; Track 1 Step 1 now done
  for Class-1 (this handoff).
- `docs/twin_validation/notion3_protocol_boundary_closure.md` — notion-3 = boundary; record = notion-2. (NEW)
- `docs/twin_validation/notion2_class1_gonogo_prereg.md` — the Class-1 cap + open routes + the go/no-go template. (NEW)
- `docs/twin_validation/simulator_legitimacy_direct_correlation_design_2026-07-04.md` — the corrected
  direct-correlation observable design (still "DESIGN for review"; open decisions D0 refs/tolerances, D1 realistic
  amplitude, D2 null tier, D3 error class — D3 partly resolved: Class-1 mild-1/f capped). Partially validated by 1b.
- `docs/twin_validation/corrected_multitime_observable_prereg.md` — the corrected multi-time observable prereg.
- `docs/twin_validation/g6_null_model_rederivation_2026-07-03.md` — the a-exact MA(1) closed form (off-arm
  `p_ij(lag1)=μ=0.0149`, `p_ij(lag≥2)=0`). VALID, reused.
- Gate scaffolding `docs/twin_validation/gates/`: `g5_baseline.py` (best-converged **Markov-k** comparator = the
  Guardrail-B non-triviality null), `g6_ablation.py` (`spitz_p_ij`, cluster-bootstrap SE), `g4_imprint.py`,
  `g7_isolation.py`, `_gate_common.py`. VALID.
- Substrate code: `src/error_coupling_simulator/teachers/coupled_cycle.py` (`CoupledCycleTeacher.emit`),
  `source/process.py` (`OneOverFDriftSource`, `RTNSource`, **`TemporalStormSPPSource`**), `source/coupling.py`
  (Θ fan-out, `SourceCouplingConfig`), `src/qec_twin/hardware/pij.py` (canonical `spitz_pij_exact/_delta_se`),
  `quantum_bath/` (forward non-Pauli generation infra). VALID.
- `docs/twin_validation/h2_effectsize_g4_prereg.md §7.B/§7.C` — the Class-1 ΔLER finding + realistic bracket (a
  DIFFERENT quantity from the correlation observable — do not conflate).
- `docs/twin_validation/detector_layer_cmi_bridge_prereg.md`, `coupled_teacher_round_gates_prereg.md`,
  `full_error_coupling_prereg.md` — the Class-0/1/2 arms, the G-gate suite, the mechanism catalog + C10 gate.
- Grounding memory: [[project-cpdiv-notion-hierarchy-passive-record]], [[project-coupled-cycle-teacher-build-state]]
  (has the 2026-07-06 status at top), [[feedback-simulator-is-goal-twin-is-next]], [[feedback-simulator-not-decoder]].

**RETRACTED / VOID / PARKED (do NOT trust or build on):**
- **G0-v2 FAIL / G6 "sub-floor"** — wrong observable (2-point TV / shared-minus-markovian). `g0_v2_effectsize.json`
  is the retracted metric. Machinery kept; conclusions void. (2026-07-04 handoff §7.)
- **notion-3 quantum-memory WITNESS line** (Control 3/3b as a model-free RECORD claim) — RETRACTED (1a). The
  `quantum_bath` revival witnesses are reduced-dynamics/backflow or protocol-family diagnostics only.
- **G0-quantum GO-CORNER-ONLY** (`g0_quantum_effectsize_prereg.md`) — coherent (commutator) sector, PARKED; also
  not a model-free quantum-memory certificate. Not part of the classical-visibility line.
- **2026-07-03 "active-observation reconstruction"** — scope error, deleted; its handoff VOID.
- The **twin** docs (`docs/plan3.md`, `do()`/`recover`) — SEPARATE LATER project.
- The many **Axis-1 mechanism** preregs (`m6`–`m34`, `axis1_*`) — valid as the FORWARD mechanism library, but the
  coherent ones do not survive on the record (twirled out); they are not the legitimacy question.

## 4. Disciplines + environment (standing — unchanged)
- **Theory-first / predict-before-measure** (prediction + epistemic class (a)/(b)/(c) registered BEFORE any run; a
  miss is a finding). **theory-fix** trip-wires when a clean/hoped-for result is about to be built on.
- **Scripted-execution:** committed script + precondition asserts + printed evidence + flush + `__main__` guard +
  `content_hash`/`GATE_RESULT`. **wsl `$`-pre-expansion trap** ([[feedback-wsl-exit-code-quote-chain]]): never put
  `$?`/`$!`/`$(...)`/`$VAR` control logic in the outer `wsl.exe bash -lc '…'`; write a committed `.sh` or a fixed
  literal log path + `echo "python-exit=$?" >> log` INSIDE the script's own shell.
- **Confirm mainline before commit** (H6): `src/**`+`tests/**` need explicit user confirmation; docs/outputs = normal
  flow. **`outputs/` is gitignored** (local audit trail).
- **GPU serial, no concurrent** on the live desktop; heavy → `ssh spark` ([[reference-ssh-spark-compute]]). This
  session's go/no-go is CPU-analytic (no GPU).
- **Anti-toy / independent-GT** ([[feedback-anti-toy-ground-truth-protocol]]): verify against a reference with a
  DIFFERENT blind spot; every claim from committed-script printed evidence, never relayed memory.
- **RAG-first** for literature: `python -m qec_twin.rag.store --query "…"` (1902 chunks; `--build --force` after
  adding notes). **CODE_MAP:** `python tools/gen_code_map.py` after any src change.
- **Env:** `wsl.exe bash -lc 'cd /home/cx/Document/AI_QEC/AI_QEC && /home/cx/miniconda3/envs/aiqec/bin/python …'`
  (conda not on PATH; use the absolute interpreter). Scope pytest to `tests/`.

## 5. IMMEDIATE NEXT ACTION (reframed to the infrastructure goal, 2026-07-06)
**Lead with the positioning + the first infra deliverable — do NOT lead with the notion-2 go/no-go.**
1. **Positioning one-pager** — the §0/§0b goal + competitive gap + the three differentiators + the acceptance
   checklist, as a standalone `docs/` doc a reviewer/funder/user can read (and re-verify the competitive claims:
   Deltakit `ToyNoise`-delegates-to-Stim, CUDA-Q/Tsim Stim-centric, coupled-noise-generation = research-code-only).
2. **Faithfulness coverage table (leg (i) = the gate/moat)** — enumerate the built mechanisms (`mechanisms/`+`source/`)
   × the independent oracle for each × the bounded generation error × the max `d`; fill the empty cells. This is what
   no competitor has.
3. **Interop spike + killer demo** — a minimal `emit → Stim/DEM` export decodable by PyMatching/Deltakit, then a
   Stim-impossible coupled/**leakage** record (Darmawan-style qutrit-MPS, bounded vs qutrit-DM) whose oracle-bounded
   generation changes a decoder result vs the Stim-Pauli prediction. Leakage is the leading demo source (Stim-impossible
   AND has existing forward machinery in `carrier/` + `quantum_bath/`).

The **source-realism go/no-go** (`notion2_class1_gonogo.py` harness with `TemporalStormSPPSource` / non-Gaussian RTN +
the `gates/g5_baseline.py` Markov-k comparator, predict-before-measure) is now **SECONDARY** — run it to FILL THE
VALUE-MAP (which regimes beat Stim-DEM), alongside or after the infra deliverables, not before them. **D1** (the
realistic source anchor) is still a user decision when it runs.
