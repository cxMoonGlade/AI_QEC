# HANDOFF — coupled-Lindblad-pseudomode PILOT (fresh-session entry point)

Date 2026-06-30. Point-in-time map, NOT live truth. Read the cited files; code/notes are truth, this drifts.

## 0. Illusion-resilience preamble (READ FIRST)
The prior session was repeatedly corrected for being illusion-prone: assembling claims from summaries,
concluding "infeasible / not worth building" too fast (twice wrong — wrong tool + wrong observable), and
nearly missing that the core method was already published. Binding rules for consuming this handoff:
1. **Tags:** `[COMMITTED]` = on Dev-F now; `[VERIFIED-TEXT]` = read from the paper's extracted text this
   session; `[PRIOR]` = re-verify before building on it; `[REASONED]` = inference.
2. **Code/notes are truth.** Re-run cited certs (they live in gitignored `outputs/` — local-only, re-run),
   re-read cited reading notes yourself. Do NOT trust a summary of a summary.
3. **Standing disciplines (memory `MEMORY.md`):** theory-first (math/paper grounding BEFORE code; 精读 the
   FULL text yourself, never a sub-agent summary); faithfulness/anti-toy (INDEPENDENT ground truth, never a
   parallel copy of the engine; constraint ledger + falsifier; declare+bound every simplification, unbounded
   = STOP); scripted-execution (every run = a committed script with asserts+printed-evidence+`__main__`);
   GPU-only + **no concurrent GPU jobs** (serialize; multi-agent fan-out = READ-ONLY/web only); hard
   commit-gate on `src/qec_twin/**`+`tests/**` (explicit user OK per commit; docs/outputs normal flow);
   standard metrics; don't lead the reviewer.

## 1. Immediate next action
**Prototype the pilot in `docs/twin_validation/coupled_pseudomode_pilot_prereg.md` — do that pre-reg's §7/§8.**
A committed `outputs/` script (NO `src/` yet) that, at **n=2 qubits first, then 3–4**:
(a) SDP/Loewner-fits the coupled matrix-BCF → `{H, Γ, g}` (per `[2506.10308]` S1);
(b) runs the enlarged **CPTP GKSL** evolution on the qubits ⊗ `N` pseudomodes (dense, small, exact, GPU);
(c) cross-checks vs the INDEPENDENT oracle — **ACE `[arXiv:2405.19319]`** (method-distinct) + the closed-form
    `C(t)`/`J(ω)` `[2602.21430 Eq.33 / 2509.19685 Eq.40–45]`;
(d) measures the FOUR pre-registered bets: polylog `N` (SDP feasibility), coherence-revival survival at
    `N=3–4`, oracle agreement ≤1e-3 (coherence-weighted), and the **(c)-gate RWA-breaking `n_max`** cost
    (QEC X/Y/CZ gates break excitation preservation → pseudomode Fock-dim may blow up — the concrete open risk).
Separate-lane reviewer before the GPU run; GPU serial. PASS ⇒ QEC arm (multi-round records + decode-relevant
PT-vs-Markov ΔLER, coherence-scored `[2412.13739]` + 2D-iPEPO `[2512.01781]`), each re-gated. A sub-floor /
FAIL result is an honest FINDING (name the failing bet), never re-fit.

## 2. The plan in one paragraph
Build the twin's **coupled** (correlated + non-Markovian) error teacher. The QEC-sim literature (QMCtwin
2606.19848 d7/97q; leakage-TN 2308.08186) **factorizes** the dissipation — that's why it scales and why it
does NOT solve our problem. A 15-paper cross-field 精读 found the core method IS published: **coupled-
Lindblad-pseudomode `[2506.10308, PRL 136 090403, 2026]`** represents a **shared bath across qubits** (SM §S2
matrix coupling `g∈C^{N×n}`, `Ĥ_SA=Σⱼ ŜⱼÂⱼ`, cross-qubit matrix-BCF `C^c(t)=g†e^{-iKt}g` `[VERIFIED-TEXT]`)
as an **exact CPTP GKSL channel** (runs on our engine); 1/f/TLS = Lorentzian-sum = its exact regime
`[2602.21430]`. Our CONTRIBUTION narrows to the **QEC application** (RWA-breaking `n_max`; multi-round
records; decode-relevant ΔLER; 2D-iPEPO composition; real-device BCF grounding) + the **independent-oracle
certification** (ACE/closed-form, the anti-circular GT the field concedes it lacks) + the **coherence-revival
wedge** (distinguished from two OWNED baselines: spatial-Markovian `[2510.24181]` and coherent-coupling QMCtwin).

## 2b. RAG over the reading notes — USE IT to navigate `[VERIFIED works 2026-06-30]`
A semantic + concept + epistemic-status-aware retrieval store over the 精读 notes now exists (user-built):
`src/qec_twin/rag/store.py` → Chroma collection `reading_notes_v2` in `.chroma_notes/` (gitignored), driven
by `docs/papers/CONCEPT_INDEX.md`. Query it INSTEAD of grepping:
`conda run -n aiqec python -m qec_twin.rag.store --query "<question>" --top-k 8 [--concept "<concept>"]`
(also `--build [--force]` to (re)index, `--interactive`). It returns section-level chunks ranked by
relevance (verified: "coupled Lindblad pseudomode shared bath across qubits" → the exact
implementation-mechanism + limitations sections of 2509.19685 / 2407.10140 / 2606.30569 / 2602.21430).
**Caveat (theory-first):** RAG chunks are a NAVIGATION aid, not 精读 — still read the FULL note + the
`outputs/papers/*.txt` for anything load-bearing before building on it.

## 3. Key files (verified paths)
- `docs/twin_validation/coupled_pseudomode_pilot_prereg.md` — THE pre-reg (the thing to build).
- `docs/twin_validation/coupled_teacher_architecture_synthesis.md` — the full 15-paper architecture + the
  RECENT-2026 update (the de-risking).
- `docs/twin_validation/coupled_teacher_rate_and_observable_grounding.md` — rates reconciled (real idle ZZ
  ~few kHz = source-value faithful, G2 370kHz = demo; T1~68/T2~89µs), observable = decode-relevant ΔLER
  (NOT syndrome-correlation, Kam-benign `[2410.23779]`).
- Reading notes (精读, committed `docs/papers/reading_notes/`): `coupled_lindblad_pseudomode_2506.10308.md`
  (carrier), `ace_process_tensor_toolkit_2405.19319.md` (oracle), `markovian_embeddings_nonmarkovian_2602.21430.md`,
  `markovian_embedding_correlated_noise_2509.19685.md`, `tepepo_2d_open_system_tn_2512.01781.md` (2D carrier),
  `tn_decoders_process_tensor_nonmarkovian_2412.13739.md` (decoder), `exact_threshold_correlated_surface_code_2510.24181.md`
  (baseline anchor), `chain_mapping_block_lanczos_shared_bath_2407.10140.md` + `t_tedopa_crossed_baths_2606.30569.md`
  + `collisional_tn_correlated_reservoir_2202.04697.md` (more oracles). Extracted texts at `outputs/papers/*.txt`.
- Memory: `project-scalable-coupled-error-open-problem`, `project-carrier-d3-scale-autoroute`,
  `project-coupling-nonmarkovian-is-the-contribution`, `project-simulator-paper-positioning`.

## 4. Working-tree state `[VERIFIED 2026-06-30 via git]`
- Branch `Dev-F`. **NEW src commits THIS session (the carrier work, landed):**
  `1fa0e82` axis1(auto-route): VRAM-aware dense→MCWF routing; `9ea4722` axis1(mcwf-d3): multi-record
  mixed-X/Z terminal measurement + over-cap-honest dense cert (the mcwf file also carries the prior M12
  seam — committed together per user decision). Agents also committed the 15 reading notes (docs, normal flow).
- **UNCOMMITTED, commit-gated, left for user:** the prior-session Axis-1 rebuild pile
  (`src/qec_twin/mechanisms/axis1_primitives.py`, `simulator/axis1_qt_mps_execution.py`, deleted/added `tests/`).
  Also uncommitted: the `.gitignore` fix (reading_notes negation) + this session's docs (normal flow).
- The carrier now RUNS full d3 q17 end-to-end via `execution_backend_contract="auto"` → MCWF (measurement
  machine-precision-certified 2.22e-16). q17 = restricted over-cap, NOT exact-dense-certified at 17q (correct).

## 5. Context that is settled (don't re-litigate)
- Axis-1 within-substep coupling = certified CHANNEL-level (G2, `cert_axis1_full_coupling.py`, 2.4e-15 vs
  independent scipy GT) `[PRIOR — re-run to rely]`. It is NOT a record-level discrimination signal (G0 showed
  zeta record-dead + gamma_phi decode-benign per Kam; that's faithful, not a failure).
- The d3-MCWF `CoupledCycleTeacher` design (`coupled_cycle_teacher_d3_mcwf_design.md`) FAILED a 3-agent review
  (retired-strawman observable, batching=multi-week-rewrite, circular certs, round-index bug) — marked
  DO-NOT-BUILD. Superseded by the pseudomode architecture (§2). The earlier dense
  `coupled_cycle_teacher_design.md` is also REVIEW-superseded.

## 6. First action, concretely
Query the RAG store (§2b) to pull the relevant note sections, then read the pre-reg + the `2506.10308` and
`2405.19319` reading notes IN FULL (and skim their `outputs/papers/*.txt`),
confirm you can OPERATE the SDP-BCF-fit + the enlarged-GKSL evolution + the ACE oracle from the equations,
then write the §7 prototype script (n=2 first). Do NOT start by writing `src/`. Slow is fast.
