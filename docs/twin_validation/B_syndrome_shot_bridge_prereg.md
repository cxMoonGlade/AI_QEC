# Pre-registration — (B) syndrome-shot bridge: multi-round syndromes from the pseudomode noise model

**Date 2026-07-01. Theory-first (literature-anchored), pre-code.** Produce faithful surface-code **syndrome
shots** `(detection_events, obs_flips)` from the *certified* correlated non-Markovian pseudomode NOISE MODEL
(A), with a **swappable code layer**. The load-bearing crux — **the pseudomodes carry non-Markovian memory
ACROSS measurement rounds** — is grounded here, not invented. Classes: **(a) exact**, **(b) band**, **(c) gate**.

## 0. What is already grounded (checked; no reinvention)
- **ME → syndrome forward pipeline:** QMCtwin `[2606.19848]` does exactly this (toggling-frame Lindblad →
  syndrome statistics) at d7/97q — **but SINGLE-ROUND, non-negative-Markovian only; multi-round detector
  histories are its explicit FUTURE WORK.** ⇒ the multi-round / non-Markovian syndrome generation is the
  UNADDRESSED piece (our contribution), not a reinvention.
- **The multi-round structure = the process-tensor comb** `[2412.13739]`: instruments `A_j` (stabilizer
  measurements) act on the system only; the system-bath maps `U_j` act on system+bath; **tracing the bath
  leaves the temporal correlations**. Our pseudomodes ARE that persistent bath.
- **Repo machinery (reuse, do not rebuild):** `forward/scalable/seam.py` (the `(detection_events, obs_flips)`
  fold — `det[:,0]=s[:,0]`, `det[:,r]=s[:,r]^s[:,r-1]`, `logical_flip=parity(terminal data)^m` — G2-tested);
  `mps_forward.py`/`sv_sampler.py` (Born-sampled + projected mid-circuit stabilizers, ancilla reset).
- **Cost is settled:** beyond-Pauli + non-Markovian ⇒ **density-matrix / trajectory, NOT Stim** (QMCtwin +
  Hines `[2603.18457]` both state this; Stim is Pauli-only).

## 1. Mechanism / method (ANCHORED)
State `ρ` on **(data qubits ⊗ ancilla qubits ⊗ N pseudomodes)**. Per QEC round `r`:
1. **Evolve** `ρ` under the enlarged GKSL `dρ/dt = -i[H_S+H_A+H_SA, ρ] + D_A(ρ)` for the round duration
   (qubits ⊗ pseudomodes coupled; `{H,Γ,g}` from PILOT 1's SDP; ASSEMBLE certified by PILOT 3/4 to ~1e-7).
2. **Stabilizer circuit:** the code layer's CNOT/CZ schedule (data↔ancilla) — SWAPPABLE (surface / other code).
3. **Born-measure the ancillas + project the QUBIT subspace ONLY:** measurement superoperator
   `Π_s = P_s ⊗ I_modes` (`P_s` the qubit projector, identity on the modes); Born-sample outcome `s`,
   collapse `ρ → Π_s ρ Π_s / Tr[Π_s ρ]`. **The modes are NOT measured — they persist and carry the memory.**
4. **Reset ancillas**; record syndrome bits `s`; go to round `r+1` (the modes' state + their qubit-correlation
   is the memory the next round inherits — the non-Markovian across-round correlation, = the process-tensor comb).
Repeat `R` rounds; **fold** to `(detection_events, obs_flips)` via `seam.py` (the SAME convention).

## 2. Observable (the RIGHT one — not invented)
- **Single-round syndrome distribution** (baseline, OWNED by QMCtwin): syndrome-extraction bias `δk`,
  ancilla-stabilizer disagreement, syndrome↔string-parity mutual information `[2606.19848]`. These are the
  Markovian-single-round metrics — a check we reproduce them, NOT the contribution.
- **THE CONTRIBUTION observable — cross-round TEMPORAL detector correlation** (`[kam_nonmarkovian_surface_code
  _2410.23779]`): the non-Markovian memory shows as correlation between detection events at rounds `r, r'`
  with `|r−r'|≥2`, absent in a Markovian (round-independent) model. **CAVEAT (grounded, Kam §IV.C):** the bare
  lag-1 2-point detector autocorrelation is INSUFFICIENT to witness streaky/non-Markovian temporal structure
  — use a higher-order / fixed-marginal temporal statistic (or the joint-vs-Markov KL on multi-round histories).

## 3. Predicted behavior (falsifiable) + epistemic classes
- **(a) EXACT:** the fold (seam.py) + the comb structure (measurement = instrument on system, modes persist)
  are exact identities. A Markovian noise model (modes reset each round / no bath) ⇒ round-independent
  detectors (cross-round correlation = 0) — definitional.
- **(b) BAND:** our pseudomode model (memory across rounds) produces a **nonzero cross-round detector
  correlation** that a Markovian/round-reset model cannot. *Falsifier:* if the cross-round correlation is
  ≤ the Markovian baseline (e.g., the memory is erased by the mid-round measurement/reset — measurement
  backaction on the modes kills it), the multi-round contribution is null (a finding).
- **(c) GATE/BRACKET:** decode-relevance of the cross-round correlation is a separate (deferred) layer
  (per METRICS.md the wedge is layered: source → channel → decoder; %ΔLER is the decoder layer, not this).

## 4. Independent ground-truth (Rule I, non-circular)
At **d3 (or a small repetition-code patch) + few pseudomodes**: the EXACT density-matrix multi-round evolution
(interleaved Born measurement, no trajectory approximation) is the reference; certify the trajectory/sampled
version against it. Cross-check the single-round δk/MI vs the exact ME (reproduce QMCtwin's owned metrics).
The pseudomode ASSEMBLE is already independently certified (PILOT 3/4 vs unitary discretization + analytics).

## 5. Bounded simplifications (Rule III)
- **(c) Fock truncation** nmax per mode — bounded (PILOT 3/4: nmax=3 gave ~1e-7 vs analytic; a relaxation mode
  holds ≤ #excitations).
- **(a→verify) measurement backaction on the modes:** the mid-round projection acts on qubits ⊗ `I_modes`, so
  it does NOT directly measure the modes, but it DOES update the qubit-mode correlation — this is physical
  (not a simplification), but MUST be implemented exactly (project qubits only), and its effect on the retained
  memory is a *prediction* (§3b falsifier), not an assumption.
- **(c) block decomposition** for scale (local blocks, from the certified block-feasibility) — the syndrome
  sampling runs per local block; global bursts bracketed separately.

## 6. Build plan (commit-gated; outputs/ first)
`outputs/`: (1) smallest bridge — repetition-code (or d3) data qubits + ancilla + a certified single-/two-qubit
pseudomode block; interleave GKSL-evolve → stabilizer circuit → Born-measure ancilla + project qubits (modes
persist) → reset → repeat R rounds; fold via seam.py. (2) EXACT density-matrix reference at this small scale
(anti-circular). (3) measure the cross-round temporal detector correlation (higher-order, per Kam) vs a
Markovian/round-reset control (the falsifiable contribution). (4) reproduce single-round δk/MI (QMCtwin check).
Density-matrix (safe dims: few qubits + few modes, nmax≤3); NOT Stim. Reviewer before any scale claim.

## 7. Verdict (provisional, pre-code)
The (B) method is GROUNDED: the ME→syndrome pipeline (QMCtwin), the multi-round persistent-bath structure
(process-tensor comb, 2412.13739), and the fold + Born-measurement machinery (repo) all exist; the
**multi-round non-Markovian syndrome generation is the unaddressed contribution** (QMCtwin's future work). I can
OPERATE it (interleaved GKSL + qubit-only projection + fold). The load-bearing OPEN question is **§3b**: does
the across-round pseudomode memory SURVIVE the mid-round measurement/reset to produce a real cross-round
detector correlation, or is it erased? That is the falsifiable first experiment — PROVISIONAL until measured.

## 8. Amendments (2026-07-01, post-§3b / post-detector-layer / post-budget-table — supersede where stated)

**(A1) §3b RESOLVED + the observable of §2 is REPLACED.** §3b = Outcome A (memory survives;
`pilotB_s3b_memory_survives_measurement.py`, then the Markov-order staircase). The detector-layer campaign
(`detector_layer_cmi_bridge_prereg.md` §8) found the **differencing/collider artifact**: `D=M⊕M` makes ALL
conditional multi-time statistics on D confounded at M-marginal ≠ 0.5 (function-of-Markov-chain,
Burke–Rosenblatt; collider bias) — so §2's "cross-round temporal detector correlation" is measurable ONLY as
an **excess over a matched-marginal Markov-k SURROGATE NULL** (fit Markov-k to observed M → surrogate
ensemble → XOR → null distribution; instrument built + validated, ANC honest-negative / DATA excess PROMOTED
4/4). Pairwise lag≥2 D-statistics are artifact-clean but Kam-insufficient. This replaces §2's bare
"correlation vs Markovian model" wording.

**(A2) COMPOSITION is now mandatory (supersedes any single-mechanism run being called "realistic").** A
single mechanism must NEVER carry the whole error budget. The composed model + shares come from the SOURCED
budget table (`error_budget_sourced_table.md`): **Markovian background** (CZ local + SQ + readout + reset,
~63%, standard channels at published p_expt) + **the coupled non-Markovian mechanism at its grounded share**
(data-qubit idle = low-frequency-flux-noise dephasing, post-DD residual, 19–20% across two device
generations; mechanism alone must reproduce p_expt ≈ 0.9e-2/cycle — the share-consistency loop) + **the
spatial correlated slot** (CZ crosstalk 11–17% → shared-bath matrix-g, Pilot-4-certified assemble) + leakage
rows declared out-of-scope + bursts bracketed + the ~20% budget-vs-experiment residual left explicitly
unmodeled. `{H,Γ,g}` come from the PILOT-1 pipeline run on the grounded J(ω): **shape = 1/f^0.9 (Bylander
1101.4707, (a)-sourced) + TLS Lorentzians; amplitude = share-calibrated (declared bracket)**; the 1/f BCF
fit likely needs the quasi-static split (slow component quasi-static + fast tail → pseudomodes).

**(A3) Carrier = MCWF (state-vector trajectories), with two gates.** Exact-DM is dead at d=3+mode
(propagator ≥ TB-scale); MCWF is statistically penalty-free for RECORD-layer observables (records are
Born-sampled in both approaches — unraveling equivalence; our per-shot DM was already trajectory-like in the
measurement branching). Gates: (i) **certification vs the exact-DM single-stabilizer instance** (Rule I,
anti-circular) before any d=3 claim; (ii) **declared rare-event boundary** (Rule III): the √N curse applies
to tiny-expectation observables (deep-subthreshold LER ≪1e-4, tiny populations) — out of scope here; record
statistics at detection fractions 0.10–0.19 are abundant. T2 norm-bleed guards (c128 + renorm + jump
bookkeeping) carried over.

**(A4) Effect-size-first (registered BEFORE the composed run).** Dilution arithmetic: mechanism share s
shrinks its own record structure ~s²; background acts ~BSC attenuation. At the grounded share the detector
excess is predicted to drop from ~5e-4 (mechanism-alone) to ~1e-5 scale ⇒ **N ~ 10⁵–10⁶ shots needed**
(MCWF-affordable, DM-impossible). The precise prediction MUST be recomputed from the pipeline's actual
{H,Γ,g} output and registered before the composed run. Both outcomes weighty: excess survives dilution at
grounded share = hardware-relevant unforgeable structure; drowned = honest budget-share-limited finding
(echoes the syndrome-only-coherence ~2% lesson at the twin layer).

**(A5) Spatial-coupling observable (new; the axis §1–§6 left implicit).** With the matrix-g shared bath
across neighboring data qubits: **cross-stabilizer detector correlation** vs an INDEPENDENT-bath control at
MATCHED marginals (the Pilot-4 Dicke/broken-sharing logic lifted to the code layer). Same surrogate-null
discipline applies to any conditional spatial-temporal statistic.

**(A6) Carrier specialization for the CLASSICAL slots (2026-07-01) — dissolves the mode-count wall.** The
step-2 data-idle mechanism is DECLARED classical (βω≪1, real symmetric BCF). For pure dephasing by classical
Gaussian noise the random-unitary representation is **(a)-EXACT** (coherence = E[e^{iφ}], φ Gaussian ⇒
exp(−χ) identically; no quantum bath required). ⇒ the production carrier for this slot = **correlated
classical stochastic fields**: OU-sum (AR(1)) fit of the SAME grounded band (nonnegative weights = classical
realizability), **exact discrete (ξ, ∫ξ) joint-Gaussian updates** (no timestep error, QS includable),
spatial correlation = cross-covariance of the fields (shared + local — the classical matrix-g analog), and
measurement does NOT back-act on the field (physically faithful for a macroscopic flux/TLS bath). Cost:
per-trajectory state = 2^{n_qubits} (no nmax^N factor) ⇒ BOTH walls fall (mode count; and the A4 statistics
N~10⁵–10⁶ becomes affordable). Scoring UNCHANGED: the same closed-form Gaussian-dephasing oracle, ledgered
D_Choi/1−F_e, share p_Z. **Cross-engine certification (Rule I): the classical-MC channel vs the certified
pseudomode channel (step-2 {H,Γ,g}) vs the closed form — two independent implementations against one
oracle.** The pseudomode engine is REPOSITIONED, not retired: quantum-back-action slots (TLS T1-exchange,
resonant modes) + the 2506.10308 generality arm. Code-layer consequence (declared): σ_z dephasing is
X-stabilizer-visible ⇒ the composed run uses a PHASE-FLIP repetition code.

**(A4-REGISTERED, 2026-07-01, `outputs/step4_a4_effect_size_registration.py` — printed BEFORE any full-sim
result.)** Derived-given-model (a): composed per-stabilizer detector rate ≈0.043; **field share of detection
events ≈42%** — the rep-code MIX differs from the surface 1/Λ 20% share (component rates grounded, mix
derived; a weight-4 surface-code detector would dilute the field more ⇒ v1 is a declared FAVORABLE-mix
instance, the surface version is the harder test). Field lag-1 corr ρ₁=0.58 ⇒ flip-modulation corr 0.336
(Isserlis). **Registered bets (b), band ×/÷2 around the Cox-toy forecast (N=4e5):**
- **B1** composed detector rate ∈ [0.034, 0.054];
- **B2** M-layer CMI1 ∈ [8.0e-3, 3.2e-2], p<0.05;
- **B3** D-layer surrogate excess exc(CMI1_D) ∈ [1.0e-3, 4.1e-3] — the Cox toy forecasts the temporal
  structure SURVIVES dilution at grounded shares (~1400× the null 1.4e-6±0.5e-6);
- **B4 falsifier**: full-sim D-excess < surrogate-null 95th pct at N=1e6 ⇒ dilution DROWNS it (reportable
  honest-negative).
(c) toy simplifications (per-cycle re-projection, Poissonized flips, no ancilla-circuit coherence) — a
toy-vs-sim gap OUTSIDE the bands is itself a finding. DESIGN NOTES for the full sim: M-marginal is a parity
random walk (equilibrates ~20-40 cycles) ⇒ the toy's M-layer CMI is partly drift-exposed — full sim uses
R≥80 with warmup≥40 for the M-layer claim (D-layer differencing-protected); N=1e6 affordable (A6 carrier).

**(A4-RESULTS, 2026-07-01 — main run + sweep + discriminator; `step4_composed_d3_phaseflip_v1.py`,
`step4_v1_sweep.py`, `step4_sweep_discriminator.py`.)** Main run (N=1e6, preconditions P1/P2/P3 pass):
**B1 PASS** (rate 0.0416), **B2 PASS** (CMI1_M=1.62e-2), **B3 PASS** (D-excess +2.10e-3 ∈ band), **B4 not
triggered — SURVIVES dilution** (excess = 24,000× the null 95th pct). First composed (detection_events,
obs_flips) shots delivered (seam convention; 100k sample `_step4_v1_records.npz`; obs saturated at R=80 —
high-noise-regime dataset, declared). SWEEP: **SW1a MISS INVERTED** — excess is monotone DECREASING in s
(4.89/3.57/2.10/0.92e-3 at s=0.25/0.5/1/2); **SW1b PASS and strengthened: the surface-like mix (s=0.25,
~15% share) is the STRONGEST point**, so the favorable-mix worry is inverted — the realistic-share
direction favors detectability. **DISCRIMINATOR: the Cox toy reproduces the entire inversion to ~2% at
every s ⇒ the trend is CLASSICAL** (my registered s² scaling guide was wrong algebra — the miss is the
finding; no analytic form claimed, empirically ~1/s over this grid). SW2 (memory axis) **inconclusive by
design flaw**: γ×16 under χ-pinning only spans effective lag-1 correlation ρ₁ ∈ [0.34, 0.72] (weight
redistribution keeps slow components) — SW2b/c cannot be read as "memory irrelevant"; a true memory-kill
config (single fast OU, ρ₁≈0) is required to close that axis. Stationarity caveat: s≤0.5 magnitudes carry
a drift caveat (mixing ~48 cyc > warmup 40); the s=1→2 decrease is drift-free so the direction is robust.
**Sweep-wide provisional statement: at grounded-to-4× noise, the composed d=3 record statistics are
quantitatively captured by the classical Cox description (sim≈toy ~2% across all configs) — the quantum
channels contribute ≲ few % here; the cheap toy is PREDICTIVE for record-layer statistics, the full sim's
role = verification + regimes where coherence should matter (to be sought deliberately).**

**(A7 — MEMORY-KILL REATTRIBUTION, 2026-07-01, `step4_sw2_memory_kill.py` — supersedes the MECHANISTIC
reading of B3/B4 and the share-sweep trend; the measured VALUES stand.)** True memory-kill (single fast OU,
γ=25, ρ₁=0.021, χ-pinned ⇒ rate identical 0.0416): **D-excess = +2.043e-3 ≈ grounded +2.10e-3 — the
memory-response curve is FLAT over ρ₁ ∈ [0.02, 0.72]; toy≈sim at the kill point ⇒ classical.**
REATTRIBUTION: the composed code's temporal D-excess is the **PARITY+MEASUREMENT HMM RESIDUAL of the code
machine itself** (beyond-M2 structure of parity-walk ⊕ meas-flips, which an M2-surrogate cannot own; the
window drift, same in all arms, is part of it) — **NOT the field's non-Markovian memory**. The
field-specific temporal excess = grounded − kill ≈ 6e-5, at/below current resolution — matching the
ORIGINAL pessimistic dilution arithmetic (~1e-5..1e-4); the 2e-3 that "survived dilution" was never the
field. Consequently: (i) the share-inversion trend = the machine's HMM structure strengthening as rates
drop (slower parity mixing), coherent with everything; (ii) **METHODOLOGICAL RULE (the third instance of
the same lesson): a fitted Markov-k chain is NOT a sufficient owned-null for CODE-layer records — the null
must be MACHINE-MATCHED (the same code machine with a memoryless source), because the trivial machine
already produces ~2e-3 beyond-M2 excess**; (iii) the field-memory claim at the code layer needs either
paired-seed machine-null differencing (resolve ≤1e-4) or a different observable — **lag≥2 PAIRWISE
detector autocovariance (pij-style)**, which is zero for the memoryless machine (meas errors span only
lag-1; flips iid) and artifact-clean — full circle to the field's standard tooling. v2's spatial finding
(lag±1 cross-stab growth + lag-0 suppression, post-hoc) is pairwise and machine-null-clean, so it is
UNAFFECTED by this reattribution.

**(A9 — NOVELTY CHECK on the v2b silent-flip result, 2026-07-02: 3 independent opus search agents
(FT-theory / sim+hardware / quantitative-mechanism), convergent verdict. REPOSITIONS the claim.)**
- **(a) PRIOR ART — cite, do not claim:** the Gaussian-moment/double-factorial enhancement INCLUDING the
  literal 15 is **Clader et al., PRA 103, 052428 (2021), arXiv:2101.11631**: common-mode single shared
  dephasing angle at fixed per-qubit marginal, P_unc≈5σ⁴/8 vs P_cor≈15σ⁴/8 at d=3, ratio growing as d!!
  (their Fig. 1 literally prints 3, 15, 105, 945…). Also (a): fixed-marginal spatial correlation degrading
  logical performance (Novais–Preskill 1209.2157; Rojas-Arias 2603.03051 — closest physical setup: Si-spin
  rep code, correlation-length sweep at fixed p, but CODE-CAPACITY with ideal syndrome extraction).
- **(b) folklore-unquantified:** collective flip = logical operator ⇒ zero syndrome (2401.04530 exhibits a
  trivial-syndrome channel for INDEPENDENT noise; 2506.15490 frames line-correlated errors as correctable);
  the isolated syndrome-silent-RUN rate as an observable.
- **(c) APPARENTLY NOVEL (all three agents concur):** (i) **the detection-event rate DECREASE under
  correlation at fixed marginals** — the literature uniformly has correlated events RAISING detection
  density (bursts/noisy detectors); "the code looks quieter while failing more" is un-owned — THE headline;
  (ii) the three-observable composite (silent ×15.9 ∧ detection↓ ∧ raw-flip↓) at CIRCUIT level with
  mid-circuit measurement; (iii) the common↔local interpolation f with the silent rate along it; (iv) the
  CCF/beta-factor reliability framing + the simulator-tooling "underestimate by moment factor" statement.
- **REPOSITIONED CLAIM:** our 15.9× measurement = a circuit-level, mid-circuit-measurement confirmation of
  Clader's moment law, REFRAMED onto the syndrome-silent-run floor; the novel content = the quieter-syndrome
  scissors + the f-knob + the composite. READING DEBT before any writeup: 精读 2101.11631 (mandatory),
  2401.04530; body-reads 2506.15490, 2303.00780, 1903.01046.
- **ADJUDICATED 2026-07-02 (post-精读; 6 committed notes, 16/16 load-bearing quotes principal-verified
  against cached full texts; debt CLEARED):** (1) Clader precision: model = COHERENT Y-rotations with a
  shared random angle, correlation BINARY (no interpolation), object = post-decode fidelity / marginal
  logical probability (Eq 13–14) — full-text confirms all five "not done" items (no silent-run, no
  detection-density curve, no f-knob, no round-resolved detector stream; marginal fixing implicit only) ⇒
  the (c)-list SURVIVES INTACT. (2) 2401.04530: "spatially and temporally correlated… beyond the scope"
  verbatim (txt:195); trivial-syndrome channel cited via Eqs. 44/49 (earlier quoted phrase was a paraphrase
  — cite equations, not strings); σ↔χ calibration map in the note. (3) Rojas-Arias correction: the paper's
  own number is "<2 orders of magnitude suppression from d=1→15 under PERFECT correlation" (txt:423) +
  "not a fundamental barrier" (txt:517); code-capacity/ideal-SE confirmed verbatim (txt:917). (4) Wang
  2506.15490 stays (b): their correlated errors are STABILIZER-VALUED (harmless, threshold-RAISING,
  P_success=1) — the OPPOSITE regime to our silent-logical flips; no silent rate, no detection rate.
  (5) Harper–Flammia: real-Google motivation anchor — simple models under-predict LER >2× (0.006 vs 0.0121,
  txt:139); a forecasting claim, owns none of our observables. (6) Layden 1903.01046: mechanism citation
  for H_E=Σg_jZ_j; explicitly not-generally-DFS; no stabilizer syndrome/silent rates — adjacent, not prior
  art. Notes committed: clader_correlations_heavytails_qec_2101.11631, quasistatic_phase_damping_stabilizer_
  2401.04530, rojas_arias_si_spin_correlated_scaling_2603.03051, wang_symmetry_correlated_thresholds_
  2506.15490, harper_flammia_learning_correlated_39q_2303.00780, layden_common_fluctuator_qec_1903.01046.

**(A8 — SCOPE RULE: this is a SIMULATOR; where DEM/decoders may and may not appear. User-set, third
recurrence 2026-07-02.)** The simulator's VALIDITY chain is channel-level certification (D_Choi/1−F_e vs
independent oracles) → record-level characterization (correlations/CMI with machine-matched nulls). DEM /
decoders / LER never enter the validity chain and are never the contribution. Permitted roles ONLY:
(a) OUTPUT FORMAT — detector streams `(detection_events, obs_flips)` are the product definition (no decoder
involved); (b) record-level STATISTICS (pij-style lag covariances = field-standard record measures, not
decoding); (c) OPTIONAL, clearly-labeled consumer-relevance DEMO — a frozen standard decoder used as a
measurement instrument (Kam-style), never as a gate or claim. Forbidden: LER as a simulator-fidelity
metric; decoder-dependent validity gates; any decoding-innovation claim. Consequently v2b's PRIMARY
observable is decoder-free: **P(obs_flip ∧ all-detectors-quiet) vs f** — the syndrome-SILENT logical-flip
rate, computable directly from the shot format, vs the f=0 machine-matched arm; frozen-MWPM ΔLER is
Tier-2 optional only.
