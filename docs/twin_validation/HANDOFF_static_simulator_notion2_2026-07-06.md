# HANDOFF — static QEC error-coupling SIMULATOR, notion-2 legitimacy, 2026-07-06

**SELF-CONTAINED.** This hands off the mainline **static (passive-record) QEC error-coupling simulator** after a
session that (1) CLOSED the notion-3 quantum-memory line as a literature-grounded protocol boundary and (2) ran the
first corrected effect-size go/no-go (Class-1), which **honestly capped** the mild-1/f route. It supersedes the
open items of `HANDOFF_simulator_nonmarkovian_visibility_2026-07-04.md` (still the master map; read its §0/§1/§2/§6)
by resolving its Track 1 Step 1 for Class-1. `[[...]]` links are Claude-Code auto-memory notes, not repo files.

---

## 0. Mission + scope (unchanged, binding)
Build the **error-coupling SIMULATOR** — a faithful forward generator of QEC records `{det,obs}` with
coupled/non-Markovian error mechanisms. Validity = **(i) faithfulness** (record matches an INDEPENDENT oracle) +
**(ii) anti-toy legitimacy** (the coupling/non-Markovian feature is DISTINGUISHABLE from a genuine
CP-divisible/Markovian null — else it is a toy). The digital **twin** (teacher-as-learner, `recover`, `do()`,
active-observation) is a SEPARATE LATER project, OUT OF SCOPE. ([[feedback-simulator-is-goal-twin-is-next]],
[[feedback-simulator-not-decoder]].) NOTE: `CLAUDE.md`/`docs/plan3.md` describe the OLDER `qec_twin` **twin** project;
the live work is the **`error_coupling_simulator`** package + `docs/twin_validation/`.

## 1. THIS SESSION'S PROGRESS (2026-07-06)

### 1a. notion-3 (quantum non-classicality of memory) — CLOSED as a PROTOCOL BOUNDARY. (committed `7536633`)
The whole "does the passive record carry genuinely QUANTUM memory?" line is retired — not as a failure, as a
principled boundary. Doc: **`notion3_protocol_boundary_closure.md`**. Two literature-nailed premises:
- **(A)** witnessing quantum memory REQUIRES active/informationally-complete interventions — it "cannot be passively
  observed" (Giarmatzi–Costa process-tensor witness 1811.03722; Taranto hierarchy 2307.11905; Bäcker applied witness
  2510.19522 — all active).
- **(B)** standard QEC syndrome extraction **Pauli-twirls** the noise, erasing coherent + non-unital structure
  (QMCtwin 2606.19848: "phase … invisible to Pauli twirling", "nonunital drift … Pauli twirling erases"; Kattemolle
  2602.08464: twirl also INDUCES non-Markovian artifacts; Wagner 2107.14252: syndrome estimates a Pauli channel and,
  by construction, ONLY the Pauli part; 2412.21055: logical noise Pauli-izes exponentially in d).
- **⇒ the passive syndrome record carries only classical (Pauli / notion-2) noise structure.** The in-house kill:
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

**KEY LEARNING (the load-bearing takeaway for the next step):** obstacle **B** (non-triviality) is the DEEPER,
INTRINSIC one — a **mild 1/f source (sum-of-RTNs, near-Gaussian, near-Markovian) is almost indistinguishable from a
single slow-RTN at the record level.** No siting/amplitude tweak fixes that; it needs a genuinely non-Markovian
(non-slow-RTN-reducible) SOURCE. This matches [[project-cpdiv-notion-hierarchy-passive-record]] ("needs strong
non-Gaussian RTN; 1/f is CP-divisible/twirled").

## 2. THE NEXT STEP (how to expand)

The corrected legitimacy question is now sharp: **is there a REALISTIC device-noise source whose passive-record
multi-time (Pauli/notion-2) imprint is BOTH feasible (>1e6 floor) AND non-Markov-k-trivial (not reproducible by a
matched low-order-Markov / slow-RTN null)?** The Class-1 go/no-go answered "no for mild 1/f." Ranked options:

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
- **notion-3 quantum-memory WITNESS line** (Control 3/3b as a RECORD claim) — CLOSED (1a). The `quantum_bath`
  revival witnesses are non-Markovianity/backflow diagnostics only.
- **G0-quantum GO-CORNER-ONLY** (`g0_quantum_effectsize_prereg.md`) — coherent (commutator) sector, PARKED; also
  moot for the record (coherent structure is Pauli-twirled out per 1a). Not part of the classical-visibility line.
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

## 5. IMMEDIATE NEXT ACTION
**A cheap source-realism GO/NO-GO** (predict-before-measure): re-run the `notion2_class1_gonogo.py` harness with a
genuinely non-Markovian source (`TemporalStormSPPSource` / strong non-Gaussian RTN) and, if useful, a joint
multi-lag / Markov-k-comparator (`gates/g5_baseline.py`) discriminator, to decide whether a realistic source clears
**Guardrail B** (non-Markov-k-trivial) at N≤1e6. Present the bandwidth before any full build. Resolve **D1** (the
realistic source anchor) with the user first, or run a declared class-(c) sweep and report across it.
