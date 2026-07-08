# HANDOFF — the non-Markovian characterization RECONSTRUCTION (active-observation re-unification), 2026-07-03

> **⛔ SCOPE-CORRECTED / VOID (2026-07-04). Do NOT execute this handoff.** This whole "active-observation
> re-unification" was a **scope error**: it re-unified the coupling **simulator** onto the qec_twin's
> **digital-twin** spine (active `C_cal(r)` characterization + label-free NLL learner + `do()`). **The
> digital twin — teacher-as-learner, twin, do() — is a SEPARATE, LATER project, OUT OF SCOPE for the
> current plan.** The current plan's goal **IS the simulator itself**: a faithful forward generator whose
> product is the record and whose ONLY validity criterion is **faithfulness of the record vs INDEPENDENT
> oracles** (channel-cert + record-char + matched nulls) — never a learner's recovery, LER, or `do()`.
> (Binding memory: [[feedback-simulator-not-decoder]], [[feedback-simulator-first-passive-record-rationale]],
> [[project-coupled-pseudomode-pilot-v1]] "drop twin/do() vocabulary; teacher = the forward controlled
> generator".) All Phase-0/1 output of this handoff (the `RECONSTRUCTION_active_observation_*` doc + prereg,
> the retraction notices on the G0-v2/G0-quantum/G6/H2 docs, the memory banners) was **REVERTED 2026-07-04**.
> **Re-examination verdict:** none of those retractions stood — but NOT because detectability is out of
> scope. **Discriminability from MATCHED NULLS at feasible N IS a simulator concern — the anti-toy
> LEGITIMACY gate** (a distinctive feature indistinguishable from its matched null at feasible N is a TOY;
> this is the "matched nulls" half of simulator validity). **⚠ SUPERSEDED 2026-07-04:** the sentence that
> once read "the G0-v2/G0-quantum/G6/H2 findings STAND as simulator legitimacy results" is **WRONG and
> RETRACTED** — the later three-error diagnosis (see `HANDOFF_simulator_nonmarkovian_visibility_2026-07-04.md`
> §1) established that **G0-v2/G6 used the WRONG observable** (a 2-point matched-marginal / shared-minus-
> exchangeable-markovian statistic — error A), so **they do NOT stand**. What IS kept: the *concept* that
> discriminability-from-a-matched-null is IN scope (anti-toy legitimacy); what falls: G0-v2/G6's specific
> "sub-floor" conclusions (wrong observable + weak source + over-generalized IW-1). Out of scope =
> detectability-FOR-recovery (can a learner characterize the mechanism); IN scope =
> discriminability-FOR-legitimacy. NO active-characterization / learner / `do()` machinery.
> See [[feedback-simulator-is-goal-twin-is-next]]. Below is retained for provenance ONLY.

**Self-contained. Read this + the APPROVED PLAN `C:\Users\cx\.claude\plans\reflective-wishing-aho.md`
(also mirror the plan into the repo if you prefer a tracked copy) + `CLAUDE.md` + the memory index.**
This hands off a **large-scale reconstruction** of the coupling-simulator / quantum-bath-teacher program's
non-Markovian-characterization framing, ratified by the user. Phase 0a (grounding + RAG + memory) is DONE;
Phases 0–4 remain.

---

## 0. Mission (BINDING — user-ratified)

**RE-UNIFY** the coupling-simulator's non-Markovian characterization onto the qec_twin's existing
**active-observation** spine. The coupling-simulator (`error_coupling_simulator`) becomes the forward
**teacher** that generates data; the qec_twin's already-built **active `C_cal(r)` probe ladder +
label-free exact-NLL learner + `do()` interventions** CHARACTERIZE its coherent non-Markovian noise.
Pivot: **passive/static + matched-marginal 2-point + mild source → active/designed + direct-learning
/ multi-time / process-tensor + realistic source.**

## 1. Why (the diagnosis + the audit trail — READ so you don't repeat it)

The program had concluded that record-level non-Markovian imprints are "sub-feasible / a faithful
sub-floor / unmeasurable at feasible N" (G0-v2 STOP, G0-quantum NO-GO, G6 sub-feasibility, H2 cap). An
adversarial audit (user-driven, this session) established this is an **ARTIFACT of three self-imposed
constraints, NOT physics**:
1. **PASSIVE/static observation** → the coherent (CP-divisibility) sector is *quadratically* suppressed
   (Prop IW-1 — a CORRECT theorem; passive real machines are EVEN in the commutator sector). The active
   pole (a complex designed gate `W=S·H`) gives *linear* coherent access (Prop IW-1's own Case-3).
2. **MATCHED-MARGINAL / 2-point discrimination observable** → cancels the first-order signal, forces
   second order; Kam 2410.23779 proves the 2-point autocorrelation is insufficient anyway.
3. **MILD source** (γφ~1e-5) → ~6 orders below the readout/reset instrument; unrealistic.

**Two concrete errors were made THIS session and corrected — do not repeat:**
- **(a) A mismatched effect-size comparison** ("quantum wedge ~9–10 orders larger than classical",
  4.7e-2 vs 5.6e-12) — RETRACTED: it compared quantum-at-SATURATION (dimensionless `8κ²`) to
  classical-at-realistic-weak (γφ²-units `Δγ`). Apples-to-apples (same units, matched coupling):
  quantum/classical ≈ **1.32** (SAME order). Lesson: an effect-size "win" that is really strong-vs-weak
  coupling / different units is a mismatch, not a result. ([[project-g0-quantum-effectsize]].)
- **(b) Over-generalizing Prop IW-1** (a correct theorem about the COHERENT sector under PASSIVE
  observation) into "non-Markovian is unmeasurable." The literature routinely measures it (see §6).
  The genuinely-hard part is only the COHERENT/CP-divisibility sector under PASSIVE observation — which
  active observation resolves.

**The frame SURVIVES** (coherence = the contribution; stochastic round-correlation = the measurable
baseline) — it matches the literature. Only the OBSERVABLE + OBSERVATION-MODEL + SOURCE were wrong.

## 2. What's DONE (Phase 0a — committed to disk)

- **The plan is APPROVED** (`C:\Users\cx\.claude\plans\reflective-wishing-aho.md`). Read it — it is the
  operative spec for Phases 0–4.
- **Local RAG connected + recorded.** `qec_twin.rag.NoteStore` (chromadb + `BAAI/bge-small-en-v1.5` over
  `docs/papers/reading_notes/`, epistemic-status-aware via `docs/papers/CONCEPT_INDEX.md`). **1669 chunks
  indexed** (171 notes). QUERY IT FIRST for grounding: `python -m qec_twin.rag.store --query "..."`;
  re-`--build --force` after adding notes. Memory: [[reference-local-rag-reading-notes]].
- **Remote compute recorded:** `ssh spark` (192.168.1.88, user ednovas, key ~/.ssh/spark_ed25519) for
  HEAVY GPU (Phase 2/3). Memory: [[reference-ssh-spark-compute]].
- **5 gap papers 精读'd + committed reading notes** (the active-observation spine):
  `white_pollock_process_tensor_tomography_2106.11722` (PTT foundation + the passive/active boundary),
  `giarmatzi_multitime_process_tomography_superconducting_2308.00750` (measure-and-prepare causal breaks
  realizable on superconducting HW; quantum NM detected), `white_unifying_nonmarkovian_selfconsistent_2312.08454`
  (self-consistent PTT → "active ⇏ no gauge"; TN scale), `ziyad_emergent_nonmarkovianity_logical_2512.08893`
  (QEC: syndrome qubits ARE the memory), `kattemolle_nonmarkovianity_pauli_twirling_2602.08464` (twirling
  ≠ clean Markov null).

## 3. What's NEXT (Phases 0–4 — from the approved plan)

- **Phase 0 (docs; normal flow) — NEXT.** New doc `docs/twin_validation/RECONSTRUCTION_active_observation_2026-07-03.md`
  (the 3-constraint diagnosis + the re-unification decision + corrected spine + kept/retracted lists). Add
  dated **RETRACTION NOTICEs** to the 5 artifact docs (see §4). Update `nonmarkovian_memory_carrier_scope.md`
  + `qec_coupling_simulator_build_contract.md` to the active-observation + re-unified spine.
- **Phase 1 (theory-first prereg; no model code).** Run the `theory-first` skill for the re-unified
  active-observation characterization: register the corrected observables (mid-`W` coherent access;
  `t`-vs-`t²` split; Walsh-Hadamard learnability + gauge; process-tensor/kernel memory), the realistic
  source bracket, the identifiability ceiling (Zheng) + gauge band, and the new gates (replacing
  G0-v2/G0-quantum/G6/H2). Anchored to the notes on disk (query the RAG). Un-led reviewer on the prereg.
- **Phase 2 (src; H6-confirmed; ≥3 disjoint builders + un-led reviewer).** Teacher emits active-probe
  responses via `C_cal(r)`; extend `calibration/nll.py` to characterize the coherent NM generator; wire
  `knobs/intervention.py` + `audit/validity.py` for counterfactual validation.
- **Phase 3 (heavy GPU; serial; use `ssh spark`; ≥3 builders + reviewer; H6).** Run the corrected gates
  (learnability/identifiability + coherent-vs-incoherent + effect-size under active obs on a realistic
  source; classical-imitator RHP=0 + motional-narrowing controls kept).
- **Phase 4.** Metric audit (METRICS.md ladder) + rigor audit (theorem-backed vs provisional) + memory.

## 4. KEPT vs RETRACTED

**KEPT (correct; re-scoped, not deleted):** Prop IW-1 (`involuntary_w_check_2026-07-03.md` — the
passive-obstruction + active-pole justification for the pivot); the frame; the G2-certified source/channel
wedge (N_BLP=0.11, D_Choi=0.20–0.43, RHP ΔΓ=0.36); the classical-imitator (RHP=0) + motional-narrowing
controls; the qec_twin active machinery (§5); the pseudomode teacher machinery.

**RETRACTED (add a dated RETRACTION NOTICE at the head, keep derivation for provenance):**
`coupled_teacher_round_gates_prereg.md` §1 (G0-v2 STOP) + §5 (G6), `g6_null_model_rederivation_2026-07-03.md`,
`g0_quantum_effectsize_prereg.md`, `h2_effectsize_g4_prereg.md`, `qec_coupling_simulator_build_contract.md`
(mild-source cap), `nonmarkovian_memory_carrier_scope.md` §3 gate-3 (passive-record observability duty),
`quantum_bath_slot_prereg.md` A7.

## 5. Reuse map (qec_twin spine — REUSE, do not rebuild)

- `src/qec_twin/contexts/{probe_catalog,probe_contract,ladder,seam_strip}.py` — the active `C_cal(r)`
  probe ladder; `RZZ_MINIMAL_INTERVENTION_PROBES` = the concrete active-`W`. Extend with a TEMPORAL rung
  (multi-round / short-time / measure-and-prepare causal breaks per Giarmatzi 2308.00750).
- `src/qec_twin/calibration/nll.py` (`CoupledRepCodeTwin`, `calibrate()`) — label-free exact-NLL learner;
  extend the coherent edge DOF → the coupled/non-Markovian generator.
- `src/qec_twin/knobs/intervention.py` (`do_remove`/`do_weaken`), `audit/validity.py` — `do()` + validation.
- `error_coupling_simulator.carrier.joint_lindbladian`, CoupledCycleTeacher, the pseudomode pilots — the
  forward TEACHER.

## 6. Grounding (the literature — query the RAG first)

New notes (§2) + cached allies: `qec_learnable_logical_noise_2601.22286` (Zheng — Walsh-Hadamard
learnability from syndrome, gauge = unlearnable, ~2e4 shots d=7), `keeling_process_tensor_2509.07661`
(PT-MPO bond = memory), `montanalopez_nonmarkovian_learning_manybody_2511.16772` (mid-`W` kernel access),
`lindbladian_learning_insitu_2603.05492` (Ivashkov: `t` vs `t²` separates coherent/incoherent),
`tn_decoders_process_tensor_nonmarkovian_2412.13739` (PT-decoders for QEC), `qec_dem_estimation_syndrome_2504.14643`,
`rhp_nonmarkovianity_measure_0911.4270` / `blp_nonmarkovianity_measure_0908.0238`. Two QEC-specific results
(Ziyad 2512.08893 + Gravier 2507.08713) POSITIVELY establish record-level NM is real + measurable.

## 7. Disciplines (standing — non-negotiable)

Theory-first (prereg precedes code; predict-before-measure; 精读 = full-text read by YOU, not a
summarizer). Faithfulness protocol (INDEPENDENT ground truth + constraint ledger + bounded simplification;
≥2 methods + positive control). ≥3 disjoint builders + un-led reviewer for heavy runs (reviewer gets
problem+goal+artifact ONLY). GPU serial, no concurrent GPU on the live desktop — offload heavy to `ssh
spark`. Standard metrics (METRICS.md ladder). Scripted-execution (committed runner + pipefail + tee +
`python-exit`, `__main__` guard). H6: every `src/**`+`tests/**` change user-confirmed before commit;
docs/outputs normal flow. RAG-first + CODE_MAP-first before re-exploring; regenerate CODE_MAP after any
`src/` change. Adversarial self-verification (the two errors in §1 are why).

## 8. Environment + infra (CRITICAL)

- `aiqec` conda env; run with env bin on PATH: `wsl.exe -d ubuntu-f -- bash -c 'cd /home/cx/Document/AI_QEC/AI_QEC
  && export PATH=/home/cx/miniconda3/envs/aiqec/bin:/usr/local/cuda/bin:/usr/bin:/bin && python …'`.
- **wsl outer-shell PRE-EXPANDS `$`** — put `${PIPESTATUS[0]}`/multi-line python in a committed `.sh`
  read from disk (not inline in the `bash -c` string), or it mangles. Git Bash also path-mangles
  `/home/...` args — wrap in `bash -c "..."`.
- Full pytest suite exits 134/139 from a benign teardown crash AFTER the summary — parse the summary line.
  Scope pytest to `tests/`.
- RAG: `python -m qec_twin.rag.store --query "..."` (offline, bge-small cached). Spark: `ssh spark`.

## 9. Pointers

Approved plan `C:\Users\cx\.claude\plans\reflective-wishing-aho.md`; Prop IW-1
`involuntary_w_check_2026-07-03.md`; the retracted docs (§4); memory
[[project-g0-quantum-effectsize]] [[project-coupled-cycle-teacher-build-state]]
[[project-coupling-nonmarkovian-is-the-contribution]] [[project-nonmarkovian-wedge-must-be-coherence]]
[[reference-local-rag-reading-notes]] [[reference-ssh-spark-compute]] [[feedback-simulator-not-decoder]].
