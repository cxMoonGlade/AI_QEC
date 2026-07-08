# HANDOFF — coupling error simulator, 2026-07-02 (session close)

**For the next session. Self-contained: read this + `CLAUDE.md` + memory index; everything else is linked.**
**Mission (user-set, binding):** a quantum error COUPLING SIMULATOR — forward simulator of correlated
(cross-qubit) + non-Markovian (cross-round) QEC noise producing `(detection_events, obs_flips)` with a
swappable code layer. Judged simulator-vs-simulator at channel/process/record level. **NOT a decoder/twin**
(A8 scope rule; LER/DEM/decoders never in the validity chain — only output format / record statistics /
labeled optional demos). **NEW scope decision (2026-07-02, user): the QUANTUM-BATH slot is a CORE feature
of THIS paper — not deferred to a second paper. It is the next session's primary task.**

## 1. Where everything is

| Asset | Path |
|---|---|
| Operative prereg + amendments A1–A9 (THE spine doc) | `docs/twin_validation/B_syndrome_shot_bridge_prereg.md` |
| Sourced budget table (composition inputs, freq hierarchy) | `docs/twin_validation/error_budget_sourced_table.md` |
| Paper draft (Intro+RW+Methodology+Experiments, 32 refs, validated) | `docs/coupling_simulator_intro_draft.tex` |
| Metric ledger incl. NEW `D_comb` row | `docs/METRICS.md` |
| Certified pseudomode params {H,Γ,g} (dephasing slot) | `outputs/_step2_grounded_dephasing_params.npz` |
| Certified classical OU field params (production carrier) | `outputs/_step3_classical_field_params.npz` |
| Composed d=3 simulator (v1) / spatial v2 / sweeps | `outputs/step4_composed_d3_phaseflip_v1.py`, `step4_v2_spatial_shared_field.py`, `step4_v1_sweep.py`, `step4_sw2_memory_kill.py` |
| Tier-0 comb metric ((a)-exact closed form) | `outputs/step4_v2b_tier0_comb_distance.py` |
| Tier-1 silent-flip scissors | `outputs/step4_v2b_tier1_silent_flips.py` |
| Pipeline steps 2/3 (SDP engine + classical specialization) | `outputs/pipeline_step2_grounded_dephasing_fit.py`, `pipeline_step3_classical_field_layer.py` |
| 6 fresh 精读 notes (Clader, Pataki, Rojas-Arias, Wang-sym, HF, Layden) | `docs/papers/reading_notes/` (slugs in prereg A9) |
| Session log memory (the full arc) | memory: `project-coupled-pseudomode-pilot-v1.md` |
| Paper texts cache (157+; incl. 2101.11631, 1209.2157) | `outputs/papers/*.txt` |

## 2. State of the evidence (all pre-registered, all principal-verified)

**Three-layer metric stack** (one concept: distance to the best Markov imitator):
- Channel: `D_Choi(ours, best-Markov) = 0.20` (block level, ledgered).
- Process: `D_comb` vs machine-matched memoryless null — temporal wedge 1.69e-2 (R=2) → 2.77e-2 (R=3);
  spatial wedge 0.80/1.59/3.16e-2 @ f=0.25/0.5/1 (linear in f). R=1 ≡ 0 built-in calibration
  ((a)-theorem: coherence-graded pieces are Choi-traceless ⇒ marginals depend only on diag(Σ)).
- Record: composed-code conditional CMI excess (2e-3) is the MACHINE's parity+meas HMM residual, NOT field
  memory (memory-kill: flat over ρ₁∈[0.02,0.72]; field part ≤1e-4) ⇒ **machine-matched-null RULE**.

**Headline result (novelty-adjudicated):** the silent-failure scissors — at pinned per-qubit marginals,
shared-field fraction f=0→1: syndrome-silent logical flips 1.10e-5 → 1.75e-4 (**15.9×**, pre-registered
Gaussian-moment center **15**), while detection rate FALLS (0.0416→0.0412), P(quiet) RISES, raw obs FALLS.
**A9 adjudication (3 search agents + 6 full-text 精读, 16/16 quotes verified): the moment law incl. the
literal 15 = Clader et al. PRA 103, 052428 (2021) — CITE, never claim. Surviving novelty: detection-rate
DECREASE (un-owned anywhere), silent-run framing at circuit level, the f-interpolation, the 3-observable
composite, machine-matched-null methodology.** Hardware contrast: known correlated events are NOISY-type
(bursts raise detection); ours is SILENT-type.

**Carrier architecture (settled):** classical slots (data-idle 1/f^0.9 dephasing, 20% budget share) run on
the EXACT classical OU carrier (random-unitary theorem; cross-engine vs pseudomode 1.2e-7; zero Hilbert
cost — d=3 surface = 2MB/trajectory). The pseudomode engine (step-2, ALL ledger gates PASS) is the
designated carrier for QUANTUM-back-action slots. Cox/stochastic-Pauli sampler ≈ full quantum sim to ~2%
at grounded rates (measured across 10 configs) — the certified-approximation ladder for large d.

## 3. THE NEXT TASK: quantum-bath slot into the code layer (core-paper scope)

**What:** a near-resonant quantum bath (TLS with T1-type energy exchange) coupled to data qubit(s) inside
the composed d=3 unit, carried by the pseudomode enlarged GKSL — the slot where the classical-field
representation is INVALID by the frequency hierarchy (βℏω_q ≈ 12: the budget table §4 note).

**Why it is the paper's sharpest arm:** classical fields pass through measurement UNCHANGED (no
back-action) — a quantum mode is CONDITIONED by the qubit measurements (the §3b/record-layer result:
mode-conditional memory, the staircase). **The falsifiable discriminator between "quantum-bath simulator"
and ANY classical-field model is measurement-back-action on the bath imprinted in the records.** Design the
experiment around that: same marginals, quantum-mode arm vs best classical-field imitator arm (matched BCF),
difference in conditional record statistics / comb distance = the classically-unforgeable wedge. If the
difference is ≈0 at code-realistic rates, that is a REPORTABLE bound, not a failure (mirror of the
Cox≈sim 2% result).

**Theory-first FIRST (do not skip):** grounding pass for (i) which budget share hosts it (T1 contribution
inside data-idle row + near-resonant TLS; the table's leakage/heating rows stay out); (ii) the TLS spectral
model + parameters (start: `gao_nonlocal_nonmarkovian_tls_2605.23385` note, `kurilovich_..._2506.18228`
note, `cattaneo_..._2005.06229` for collective dissipation; Layden 1903.01046 for the common-fluctuator
generator); (iii) the quantum FDT asymmetry S(ω)≠S(−ω) is the physics — no symmetrized shortcut.

**Build path (traps pre-flagged):**
1. Single-qubit + 1 quantum mode (JC/relaxation) block — REUSE pilot-3 style closed-form anchors
   (Ω=√(κ²/16−g²), κ=2λ) + step-2's Γ=i(K−K†) convention (the tomography-caught factor-2 — memory).
2. Embed in the single-stabilizer unit (2 data + anc + 1 mode): exact-DM reference at dim ≤ 64.
   **HARD GUARDS: qutip mesolve superoperator nnz explodes — dim ≤ 600 assert (near-OOM 3× this session:
   56/70 GB at dim 2592). Compute the Liouvillian/superop budget BEFORE running. No concurrent heavy jobs
   (live desktop).**
3. Records at scale: MCWF trajectories (record-level statistics are sampling-penalty-free — unraveling
   equivalence; rare-event √N curse only bites tiny-expectation observables, declared boundary).
4. Score with the SAME stack: D_Choi (block certification) → D_comb vs (a) memoryless null AND (b) the
   matched-BCF classical-field null (the new, decisive comparison) → record layer with machine-matched
   nulls. Pre-register bands + falsifiers before running (a/b/c classes).

## 4. Rules that bit us this session (do not relearn)
- **Ledger metrics ONLY as gates** (D_Choi/1−F_e/D_comb; RMSE = ⚠ diagnostic). 3rd recurrence recorded.
- **Machine-matched nulls** at code layer; matched-marginal surrogates for conditional detector stats
  (collider trap: D=M⊕M is a function of a Markov chain, Burke–Rosenblatt); pairwise lag≥2 is artifact-clean.
- **Seed-robustness ≥3 seeds** (same-seed rerun = determinism check only); truncation by EVIDENCE
  (occupation print + nmax-convergence assert), never reflex bumps.
- **Scripted execution**: committed scripts, asserts, printed evidence; inline bash one-liners keep failing
  (`\$VAR` dies in the Windows→WSL quote chain — LITERAL paths; `&&` grep chains stop silently — use `;`;
  PDF txts have ﬀ-ligatures + hyphen line breaks — grep SHORT ASCII fragments).
- **Delegated 精读 needs principal spot-verification** of load-bearing quotes vs cached txt (16/16 done this
  round; one paraphrase-marked-as-quote caught).
- **src/qec_twin/ promotion is commit-gated** (user confirmation required). Docs/outputs flow freely.
- Env: WSL `~/miniconda3/envs/aiqec/bin/python` via `wsl -d ubuntu-f bash -lc '...'`; cvxpy present;
  70 GB RAM, user's LIVE desktop; background runs + completion notifications, no polling watchdog one-liners.

## 5. MATH-NOVELTY STRATEGY (agreed 2026-07-02, user-ratified — the paper's theorem layer)

Diagnosis: current novelty is conjunction-type; the paper needs a mathematical spine. Five candidate
"bones", adjudicated:

| # | Direction | Verdict |
|---|---|---|
| 4 | **Closed-form process tensor for classical-Gaussian-dephasing stabilizer circuits** (Clifford comb ∘ Gaussian kernel on the coherence-grading lattice; a≠0 pieces Choi-traceless ⇒ marginals = diag(Σ) only; all matched nulls constructible) | **WRITE FIRST** — 2-3 page structure lemma, already proven in code comments (`step4_v2b_tier0_comb_distance.py`); the spine regardless of headline. No experiments needed. |
| 1 | **Classical-representability boundary for measured-circuit records** (when do stabilizer syndrome records of a quantum bath admit a classical-field representation?) | **THE Shen–Lidar-grade candidate** — decided by the CGF probe (below), not by taste. Positioning: instantiate Milz–Sakuldee–Modi process-classicality to stabilizer records with an EXPLICIT bath-parameter boundary. |
| 2 | Exact closed-form silent-floor functional for arbitrary Gaussian covariance (silent run ⇔ per-round flips ∈ {identity, logical}; E[Π(Πqᵢ+Πpᵢ)] = finite Fourier sum of Gaussian CFs) + the device metric ∂(floor)/∂f\|₀ | **Lemma, not headline** — corollary of 4; cite as "Clader endpoints → exact interpolating functional + new metric". Do it, don't lead with it. |
| 3 | Bochner-type physicality (comb PSD ⇔ w(a) positive-definite kernel on the grading lattice) → **physicality-guaranteed estimation of spatiotemporal noise from syndrome data** | Sequenced after 1 & 4. **Branch-B insurance: demo the estimator on the LOCAL real Google detector datasets** — "theory + real-hardware artifact" nobody else has. A8-compliant (estimation ≠ decoding). |
| 5 | Monotone information inequality (I(detectors; logical) decreasing in f at fixed marginals) | **PARKED until 1+2+4 land.** When attempted: attack at the FIELD layer, not the record layer — the f-interpolation is a pointwise coupling on a fixed probability space (same ξ_sh, ξ_loc draws); Gaussian tools (Royen, I-MMSE) live there; the flip layer's non-Gaussianity is the real obstacle. |

**Week-1 concurrent plan:** (i) write 4 as LaTeX; (ii) PRE-REGISTER then run the CGF probe; (iii) the
probe's clean/messy criterion is decided BEFORE running (theory probes obey prereg discipline too).

**CGF probe spec (1q + 1 quantum mode, exact DM — machinery exists; minor glue: symmetrized-BCF OU fit
of the quantum mode's correlation function via step-3 NNLS):**
- Compare record CGFs: quantum-mode arm vs matched-classical arm at the SAME symmetrized BCF.
- **Imitator-class definition (the Lamb-phase trap, fixed before running):** classical representability =
  classical Gaussian process **+ arbitrary deterministic time-dependent Hamiltonian control**. A classical
  field can never match the antisymmetric spectrum, but its only pure-dephasing effect is a deterministic
  (Lamb-type) phase — which deterministic control absorbs. Without this definition the theorem is won by a
  strawman.
- **Registered CLEAN criterion:** the leading-order difference has PRODUCT structure with two independent
  kill switches — Δ ∝ (antisymmetric spectral weight) × (measurement-insertion term) — verified by three
  sweeps: asymmetry knob (βω → 0 must kill it), measurement on/off (off must kill it), coupling power law.
  ANY switch failing to kill ⇒ conjecture shape wrong ⇒ MESSY, retreat.
- **Branches:** A (clean) → direction 1 is the headline; paper = theorem + forward + inverse + guarantees
  (四件套). B (messy) → headline = 2+3 combo (exact functional + guaranteed inverse + real-data demo),
  scissors as phenomenology, **and 1 demoted to a measured BOUND** ("records classically representable to
  within ε at code-realistic parameters") — publishable either way because the quantum-bath slot is core
  scope: **the probe is win-win, not a gamble.**

## 6. Open threads (parked, not lost)
- P1 surface d=3 (17q state-vector feasible NOW; registered bet B4′: does the scissors survive the
  weight-4 mix? — rep-code 42% share is a declared favorable-mix instance).
- CZ-crosstalk coherent-ZZ slot (11–17% share); QS reinstatement for no-DD/ancilla-sited arms.
- f hardware grounding (candidate source: von Lüpke 1912.04982 two-qubit dephasing cross-spectroscopy).
- Cox/correlated-Pauli sampler scale-out (d≥5) with d=3 certification gate; GPU port (engineering debt).
- Half-silent failure spectrum (1–2-detector failures); λ=0.04 record-layer tail convergence (starred).
- Paper: figures (all results are console tables), abstract/discussion, repro package; Tier-2 frozen-decoder
  demo optional under A8.
- Root `HANDOFF.md` (Jun 15) NOT touched — this file is the current handoff.
