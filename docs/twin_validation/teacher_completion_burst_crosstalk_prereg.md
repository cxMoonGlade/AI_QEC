# Teacher-Completion — Error Bursts + the 4 Crosstalk Forms — Pre-Registration (theory-first, LITERATURE-GROUNDED)

Status: PRE-REGISTRATION v1 (LITERATURE-GROUNDED), 2026-06-25. The user chose to **complete the d3-XZZX Axis-A
teacher infra BEFORE the learner/UQ layer** ("把 infra 搭完全再做下一步"), scope = **burst (build, teacher-axis
only) + all 4 crosstalk forms (model all, do NOT defer)**. Every mechanism + observable + predicted behaviour
below is anchored to a DOWNLOADED + FULL-TEXT-READ (精读) paper with a committed reading note, OR to existing
in-repo grounded code. Predictions are written BEFORE the build. This pre-reg EXTENDS the WS2 ⑤ pre-reg
(`ws2_spatial_crosstalk_prereg.md`) — it reuses the ⑤a (spatial) + ⑤b (temporal/drift) machinery and adds the
new pieces (operation-conditioning, correlated readout, the conditional-MI observable, the burst trigger).
Strategic frame (kept honest): **the infra is 料, not 肉** — the contribution is the learner (recovery +
generate + UQ on known truth, `project-uq-novelty-verdict`); this finishes the teacher well without inflating
infra value.

## 0. Grounding ledger (the corresponding papers — all 精读 + committed reading notes)
| axis | mechanism paper(s) | observable paper | reading note | in-repo reuse |
|---|---|---|---|---|
| Burst (cosmic-ray / TLS-burst) | **McEwen 2104.05219** (canonical phenomenology, Nat.Phys.'22) + **Tan 2406.18897** (resilience + model) + Kurilovich 2506.18228 (phase-burst) | Tan Fig 5 (per-round detection-density spike) | `tan_surface_code_error_bursts_2406.18897.md` | ⑤a + ⑤b (reuse, NOT a new operator) |
| Crosstalk-1 DRIVE/microwave (pulse spillover, operation crosstalk) | **Sarovar 1908.09855** (taxonomy + drive spillover Ex.1/Eq.13-14) | **Sarovar §6.4** (conditional-indep / G²-CMI / max-TVD) | `sarovar_detecting_crosstalk_errors_1908.09855.md` | single/two-site apply, op-conditioned (new gating) |
| Crosstalk-2 fSim COHERENT gate-error | **Foxen 2001.08343** (fSim(θ,φ); purity-limited) | Bravyi 1710.02270 (`P_L`, twirl-underestimate) | `foxen_fsim_twoqubit_gateset_2001.08343.md` | coherent rx + ⑤a coherent; leakage part = path-B (done) |
| Crosstalk-3 READOUT/detection | **Heinsoo 1801.07904** (correlated assignment + measurement-induced dephasing) | Heinsoo (pairwise readout correlation, <1%) | `heinsoo_multiplexed_readout_crosstalk_1801.07904.md` | `soft_readout.py` emitter; new correlated-assignment POVM |
| Crosstalk-4 TLS/spectator | **Gao 2605.23385** (coupler-hosted TLS, 1/f^1.05, non-local) | Gao (temporal corr / drift envelope); Kam §IV.C caveat | `gao_nonlocal_nonmarkovian_tls_2605.23385.md` | ⑤b (Kam temporal + Bhardwaj drift) reuse; rare ⑤a |

## 1. The cross-cutting result this pre-reg registers (the EMERGING PATTERN, now 4-form confirmed)
**Every crosstalk form splits into a COHERENT part (syndrome-TWIRLED → d3-GATED) and an INCOHERENT part
(first-order → CERTIFIABLE moment).** This is not assumed — it is read out of the four papers:
- Sarovar's OWN simulation: coherent Z⊗Z crosstalk under random/twirling circuits manifests only at **O(ε²)**
  and needs **10× the shots**; stochastic operation-crosstalk + incoherent readout-detection crosstalk show at
  **first order** (`sarovar... §7.1`).
- Foxen: the fSim coherent residual is **purity-limited ~7e-5** (calibrated-negligible) + coherent → twirled.
- Heinsoo: readout crosstalk is **incoherent** (classical correlation + measurement-induced dephasing) → a
  direct syndrome-record moment.
- Gao: the coherent TLS exchange (vacuum Rabi/Bell) → twirled; the **1/f^1.05 dephasing drift + temporal
  correlation** → the certifiable ⑤b envelope.
This matches the established certifiability map (`project-axisA-teacher-ws1-ws2`,
`project-coherence-not-identifiable-syndrome-only`): coherence is not identifiable from binary syndromes (~5×
confirmed); the certifiable misspecification is the MOMENT/temporal/spatial observables an iid-stationary-Pauli
learner misses. **Registered prediction (class (b)):** on the d3-feasible sub-codes, the INCOHERENT bucket
certifies (significant + structured moment); the COHERENT bucket does NOT (suppressed/twirled, |z|<2 on binary
d3), its payoff deferred to larger-d / soft-readout. A coherent form that DID certify on binary d3 would falsify
the pattern (a finding).

## 2. The mechanisms (theory-first, literature-anchored; reuse where it exists)

### Burst — rare chip-wide correlated-depolarizing trigger (REUSE ⑤a + ⑤b, NOT a new operator)
- **Model (Tan/McEwen):** a rare event (cosmic ray / quasiparticle burst) elevates the depolarizing rate
  CHIP-WIDE (spatial) for a MULTI-ROUND window (temporal) — a T1/T2 collapse, i.e. **Pauli correlated-
  depolarizing**, NOT an operator-non-Pauli channel. Implementation = a triggered elevated-rate envelope:
  `p_eff(q, r) = p_base + B·𝟙[r∈window]·𝟙[q∈footprint]` over all qubits (footprint = full chip at d3) for a
  window of `W` rounds. This is an extreme rare-event case of the ⑤b Kam streaky / Bhardwaj drift envelope
  applied simultaneously across ⑤a's spatial extent → REUSE both. + a per-event **detection flag**.
- **Grounded magnitude (bracketed):** rate ~1/hr large chip (Willow gap-eng floor; Harrington 2402.03208
  ~1/10 min per 10q); footprint chip-wide (>600 µm, Wilen 2012.06029); duration `W` = tens–hundreds of cycles
  (ms); T1 ↓ ~1–2 orders (~100×, Vepsäläinen 2001.09190) → `B` set to the ×100-T1-collapse-equivalent depol.
  All SWEPT.

### Crosstalk-1 DRIVE / microwave (pulse spillover, operation crosstalk; Sarovar)
- **Coherent spillover (Sarovar Ex.1):** an op on region A applies a small coherent rotation on spectator B
  (`exp(−i δ X_B)` or the Z⊗Z of Eq.14). REUSE coherent rx (single-site) / `zz_coupling_kraus` (two-site).
- **Stochastic operation-crosstalk (Sarovar Eq.13, the certifiable part):** an op on A applies a depolarizing/
  dephasing kick `D_p` on disjoint B — an **independence violation** (B's local map is context-dependent on A's
  setting). New gating: the teacher applies the extra channel on B conditioned on the "setting" (which gate ran
  on A this layer). REUSE single-site apply, gated by the layer's op list.
- **Grounded magnitude (bracketed):** Sarovar uses illustrative `p=ε=1e-2`; NO device-measured drive rate
  exists → bracket real drive spillover **≲1e-3** (sub-deployed) up to a visible `1e-2`. SWEPT.

### Crosstalk-2 fSim COHERENT gate-error (Foxen)
- **Model:** apply the CZ as `fSim(δθ, π+δφ)` — a small coherent over-rotation (residual swap δθ + phase
  miscalibration δφ) on CZ-adjacent data pairs. REUSE the coherent two-site apply.
- **Split (declared):** the leakage part |11⟩→|02⟩ = the dominant fSim error = **already path-B** (done,
  `leakage_transport_pathB_prereg.md`); THIS form = only the coherent residual.
- **Grounded magnitude:** Foxen **purity-limited, coherent residual ~7e-5** (calibrated-negligible; δθ ≲ 5° as
  an uncalibrated byproduct only). Bracket [7e-5, the H2-visible 0.05] — but flag the realistic value is
  bounded-negligible.

### Crosstalk-3 READOUT / detection (Heinsoo)
- **Model (two parts):** (a) **correlated ancilla-readout assignment** — a classical 2×2 correlated assignment
  error: ancilla i's reported bit acquires a dependence on neighbour j's measured state (Sarovar Ex.4 /
  detection-crosstalk POVM E10/E11 with flip prob `pm`); (b) **measurement-induced dephasing** on spectator
  data/ancilla qubits during readout. INCOHERENT/classical. New: a correlated-assignment layer on the readout
  emitter (`soft_readout.py` / the binary POVM) + a spectator-dephasing kick during the measure layer.
- **Grounded magnitude (bracketed):** Heinsoo simultaneous-vs-individual readout error **within <1%**;
  Purcell-protected ≪1% vs unprotected larger; Sarovar illustrative `pm=1e-2`. Bracket ≲1%. SWEPT.

### Crosstalk-4 TLS / spectator (Gao) — REUSE ⑤b (microscopic origin), rare ⑤a
- **Incoherent envelope (the dominant, certifiable part):** a slowly-fluctuating 1/f / RTN modulation of the
  affected qubit's error rate (T1 jumps + low-freq dephasing) = the **⑤b** axis: Kam-temporal correlation +
  Bhardwaj drift `g(r)=g0+Σ g_m sin(ω_m r)`. REUSE WS2 ⑤b machinery directly. TLS is the **microscopic ORIGIN**
  of ⑤b, not a new operator.
- **Coherent exchange (twirled):** vacuum-Rabi / Bell-generation between qubits sharing a coupler-defect — a
  rare **⑤a**-style correlated two-qubit kick. REUSE `correlated_dephasing_kraus`. Rare.
- **Grounded magnitude (bracketed):** Gao 1/f^1.05 over ten decades (0.1 mHz–1 MHz); TLF switching rates
  0.6 mHz–0.2 GHz; effective g̃ up to 10 MHz (tunable ∝1/Δ); occasional discrete jumps. SWEPT (the count/range
  is phenomenological, NOT a physical inventory — declared).

## 3. Predicted observables (class (b) bands unless noted; LITERATURE-ANCHORED)

### INCOHERENT bucket → CERTIFIABLE on d3 (the registered positive predictions)
- **Drive stochastic operation-crosstalk → conditional-MI / max-TVD moment (Sarovar §6.4).** The op on A
  creates a conditional dependence `P(R_B | S_B, S_A) ≠ P(R_B | S_B)` an iid-Pauli learner (factorized layer
  map) misses. PREDICTION: the G²/CMI (or max-TVD) edge B↔A-setting is significant (z≫2) when the spillover is
  on, ≈0 with crosstalk off + ≈0 for the iid foil. (Decode-independent moment; Sarovar's pyGSTi PC/G² is an
  INDEPENDENT published implementation to cross-check our statistic.)
- **Readout crosstalk → pairwise neighbour-ancilla readout correlation (Heinsoo) + spectator-dephasing LER.**
  PREDICTION: a same-round cross-ancilla readout covariance `>0` for the neighbour pair, ≈0 otherwise; the iid-
  readout learner factorizes the POVM ⇒ misses it. (A NEW certifiable moment distinct from ⑤a error-spatial_corr
  and ③ rr_corr.)
- **TLS / ⑤b temporal → LER-DEGRADATION + recoverable drift** (Kam LER-degradation under streaky correlation;
  Bhardwaj static-DEM penalty `Δ`). PREDICTION (reuse WS2 ⑤b): the marginalized-iid decoder's ΔLER under the
  1/f/temporal structure; drift recoverable by window estimation. **NOT** the 2-point round-to-round detector
  autocorrelation (Kam §IV.C PROVES it cannot distinguish benign vs catastrophic; Gao's 1/f confirms structure
  beyond lag-1).
- **Burst → per-round detection-density SPIKE + chip-wide simultaneity (Tan Fig 5).** PREDICTION: during the
  burst window the per-round detection density spikes across ALL stabilizers simultaneously (distinct from
  leakage = localized, and from always-on ZZ = stationary); the iid-stationary learner has no such rare
  chip-wide multi-round mode → its UQ band should flag out-of-model / widen. **This is the teacher-axis test of
  the LEARNER's UQ (band-widening on a rare out-of-model event), NOT a decoding contribution** (burst-decoding
  is OWNED — Tan: detect+standard-decode suffices; Willow gap-eng 1/hr@1e-10; detect-and-discard deployed).

### COHERENT bucket → d3-GATED (the registered null/suppressed predictions)
- **Drive coherent spillover, fSim residual (δθ,δφ), TLS coherent exchange → EXCESS-LER / twirl-underestimate**
  (Bravyi `P_L = 2Σ_s p(s)|sinθ_s|`), but **syndrome-TWIRLED → suppressed on binary d3** (the H2 `B_misspec`
  overconfident-band signature is the decode-relevant footprint, d-gated at distance-2). PREDICTION: |z|<2 on
  the binary d3 syndrome moments (no certifiable spatial/temporal correlation from the coherent part); the
  payoff lives at larger-d / soft-readout. A coherent form certifying here would FALSIFY §1.

## 4. Exact ground truth (non-circular, INDEPENDENT of the carrier)
- **Coherent + stochastic two-/single-site channels:** `QutritDM.record_oracle` with the channel on the derived
  CZ-adjacent / spectator sites, on a DM-feasible valid sub-code (overlapping-stab for spatial moments; ≤6
  qutrits, distance-2; HARD-BOUND to small d3 — full-9q R≥2 FORBIDDEN, `feedback-no-concurrent-gpu-jobs`).
  DM-vs-carrier Gate-4 (1/√N convergent). The two-site apply is already validated vs a from-scratch dense embed
  (`<1e-12`, WS2 B1).
- **Drive operation-crosstalk CMI/TVD:** computed IDENTICALLY on DM-emitted and carrier-emitted records; the
  INDEPENDENT cross-check = Sarovar's pyGSTi PC/G² (a separate published implementation, baseline-pristine per
  `feedback-baselines-pristine`) on the same records — a non-circular second observable.
- **Readout correlated-assignment:** a CLASSICAL post-process on emitted bits → apply the SAME 2×2 correlated-
  assignment map to DM-emitted and carrier-emitted bits; the pairwise readout-corr moment is then exact both
  sides + cross-checked vs the **closed-form** expectation of the 2×2 correlated-assignment POVM (analytic,
  independent of either engine).
- **TLS / ⑤b:** reuse WS2 ⑤b GT exactly (classical streaky mask + round-indexed `g(r)`, applied identically to
  DM and carrier; DM vs MCWF are different objects → not circular).
- **Burst:** the elevated-rate envelope is known truth → DM/carrier produce the bursted record exactly; the
  detection-density spike is a direct count statistic cross-checked vs the **analytic** expected detection
  density under the elevated rate (closed-form, independent).
- **Controls (non-optional, `feedback-scrutinize-vacuous-checks`):** iid foil (moments ≡0); crosstalk-OFF /
  burst-OFF / drift-OFF matched null; corrupt-stab geometry teeth (must fail loudly); marginalized-independent
  (Kam matched-marginal); the **coherent-bucket positive control** = the SAME coherent channel on the rep-code
  (d=5) where the LER/excess-LER signal is NOT d-gated (proves the d3 null is genuine d-gating, not a dead check
  — the WS2 Δ=+0.029 z=12.5 rep-code template).

## 5. Bounded simplifications (declared; unbounded ⇒ STOP — `feedback-anti-toy-ground-truth-protocol`)
- **All magnitudes SWEPT, never frozen** (no device-measured drive rate; readout ≲1%; TLS 1/f range
  phenomenological; burst rate/footprint/duration bracketed). Each is a reported band from run 1
  (`feedback-prevent-toy-from-the-start`).
- **Operation-conditioning is a per-LAYER effective channel**, not a pulse-level spillover simulation (the
  carrier/DM act on layers, not ns-pulses). Bound: the difference vs a pulse-resolved sim is out of scope
  (declared; connects to `feedback-carrier-transition-numerical-traps` T4 Stim-timing). Class (c).
- **Readout + drive operation-crosstalk touch the ancilla/measurement**, which the carrier IDEALIZES
  (`project-soft-readout-d1`): the correlated-assignment + spectator-dephasing are applied at the readout/
  soft-readout emitter, NOT an ancilla-resolved circuit. Bound declared (out of scope), not silently equated.
- **Burst = an extreme rare-event reuse of ⑤a/⑤b**, not a first-principles cosmic-ray/quasiparticle-diffusion
  sim (Tan/McEwen phenomenology); the footprint is full-chip-at-d3 (a d3 simplification of the >600µm spatial
  profile). Class (c).
- **fSim coherent residual is bounded-NEGLIGIBLE** (Foxen ~7e-5) — included for completeness, flagged not
  inflated; do not report it as a load-bearing axis.
- per-round-lumped siting inherited (WS1 b3-S1); the 2-point RR_CORR is a known-INSUFFICIENT summary (Kam §IV.C
  + Gao 1/f) — carried as a declared limitation of any temporal certify check.

## 6. Epistemic status (METRICS.md ladder; `feedback-standard-metrics-ladder`)
- **(a) exact:** the two-/single-site apply validations; the DM record/moment identities; the closed-form
  readout-assignment + burst-detection-density expectations; the fixed-marginal algebra (Kam App A); known-truth
  drift/burst LER.
- **(b) prediction bands (a miss is a finding):** the INCOHERENT-bucket positives (drive CMI/TVD; readout
  pairwise-corr; ⑤b/TLS LER-degradation + recoverable drift; burst detection-density spike + UQ band-widening)
  AND the §1 pattern itself (coherent→d3-gated null / incoherent→certifiable).
- **(c) heuristic gates:** the MC bands; the iid-foil / off / corrupt-stab / marginalized-independent / rep-code
  positive controls; the burst trigger threshold + detection flag; the bracket arms (representative, not
  physical-truth — `feedback-underdetermined-bracket-not-freeze`).
- **Metric ladder:** %ΔLER (ledger); conditional MI / G² + max-TVD (Sarovar, field-standard crosstalk metric);
  detection density (field-standard); pairwise readout correlation (Heinsoo). Any non-ledger metric flagged.
- Verdict "teacher-completion certified" stays **PROVISIONAL** (convergence + independent oracles; reportable,
  gating-usable, NOTHING built on it — `project-uq-novelty-verdict` corollary). Closes with a metric audit + a
  rigor audit.

## 7. Build org (heavy-task discipline: ≥3 disjoint builders + an UN-LED reviewer; `feedback-heavy-tasks-multi-agent`)
- **B1 (teachers, outputs/):** the 4 crosstalk-form teachers (drive op-conditioned spillover + stochastic;
  fSim residual; readout correlated-assignment + spectator-dephasing; TLS = ⑤b reuse) + the burst trigger
  envelope (⑤a/⑤b reuse) — all on the carrier + the DM oracle, on the derived sub-codes.
- **B2 (observables/certification, outputs/):** the INCOHERENT-bucket moments (drive CMI/TVD + the pyGSTi PC/G²
  cross-check; readout pairwise-corr vs closed-form; ⑤b/TLS LER-degradation; burst detection-density vs
  analytic) + the COHERENT-bucket d3-gated null + the rep-code positive control.
- **B3 (controls + UQ-axis hook, outputs/):** the non-optional controls (§4) + the burst UQ band-widening probe
  (the teacher-axis test of the learner's out-of-model flag — the bridge to the UQ layer).
- **Reviewer:** UN-LED (stage problem + ultimate goal + artifacts ONLY; omit our diagnosis/expected answers —
  `feedback-reviewer-no-leading`). Prefer STATIC review; any GPU/DM run SERIAL + small-d3-bounded (NO concurrent
  GPU jobs — `feedback-no-concurrent-gpu-jobs`).
- **Constraints:** GPU-only model compute (`feedback-gpu-only-execution`); scripted-execution (committed scripts
  + asserts + printed evidence + `__main__` guard — `feedback-scripted-execution`); mainline (any
  `src/qec_twin/` change, e.g. a readout-emitter correlated-assignment hook or an op-conditioning gate) is
  COMMIT-GATED on the user (`feedback-confirm-mainline-before-commit`); this pre-reg lands before any code.

## 8. FRONTIER MAGNITUDE UPDATE (2026-06-26) — the crosstalk grounding was fixed-coupling-era (5+ yr old)
User correction ("why are the crosstalk papers all 5+ years old?"). A 2023–2026 frontier-literature sweep
(deep-research-equivalent: manual WebSearch+Fetch; the deep-research workflow harness errored) + 精读 of three
new committed reading notes shows the crosstalk **FORMS are still valid** but the **MAGNITUDES are stale**
because modern hardware uses **tunable couplers** (the single biggest 2018→2026 change). The teacher's channels
are physically parameterized + SWEPT, so these are **declarative bracket updates, NOT rebuilds**.
- **⑤a ZZ (`pettersson_fors_zz_coupling_comprehensive_2408.15402`, 2024 + measured residual `[2505.22276]`):**
  FORM EXACT (Eq.3 cross-Kerr ζ; Eq.6 `U=diag(1,1,1,e^{-iφ})`, **φ=ζ̄·t_g** = our `exp(-iφ ZZ)`). MAGNITUDE
  **STALE ~100–1000×**: modern residual ζ<1 kHz (<100 Hz coupler-off) vs the coherence-limited threshold
  ζ̄<2π·100 kHz (Eq.9). **φ bracket `1e-3..0.15` → `1.6e-5..1.6e-4`** (residual), `1.6e-2` = the matters-edge;
  retire 0.05–0.15 as strong-ZZ/near-CZ (NOT residual). [updated in `ws2_spatial_crosstalk_prereg.md` §1.]
- **READOUT (`xiong_multiplexed_readout_purcell_2509.11822`, 2025 + `[2505.00674]` MIST, 2026):** FORM VALID
  (`Γφ~χ²n̄/κ` dispersive dephasing + classical 2×2 assignment). MAGNITUDE **STALE ~50×**: modern protected
  cross-fidelity ≈0.02% (n̄≈5e-4) vs Heinsoo's <1%. **`pm`/spectator-deph bracket `≲1%` → `2e-4..1e-3`**
  (modern protected → unprotected upper edge). **NEW SUB-AXIS to add — readout-induced LEAKAGE (MIST /
  ionization):** the readout drive excites the qubit to |2⟩+ at a critical n̄ (offset-charge dependent; Fechant
  2505.00674); Xiong measures ℒ↑≈0.08%/100 ns ⇒ a readout-conditioned `|1⟩→|2⟩` leak (~1e-3, SWEPT) that
  **connects READOUT to the ④ leakage axis** (reuse the QuTiP WG-leak, readout-power-conditioned).
- **DRIVE (`song_microwave_crosstalk_planar_2606.02440`, ETH 2026 + IQM `[2603.11018]`):** FORM (off-resonant-
  Rabi spectator effect) VALID; magnitude **roughly IN-RANGE** (least-stale): `c ∈ [0.01, 0.1]` (cross-drive
  ratio X = −40..−20 dB, Song-measured) — keep, but re-ground in Song's measured X (not Sarovar's illustrative
  1e-2) + the post-frequency-planning residual (IQM 99.96%). **SOURCE understanding UPDATED**: not pure spectral
  spillover — capacitive + PACKAGE-MEDIATED cavity tail (−2.7 dB/mm, dominates at distance) + crossover; Sarovar's
  distance-scaling is insufficient on intermediate-scale chips.
- **Action items (deferred — the user chose the report + notes first):** patch the QuTiP param-mapping defaults
  to these brackets (`_phi_to_J` to the ⑤a φ residual; the readout `deph`/`pm` bracket; the drive `c` re-grounded)
  in `outputs/teacher_prereg/{qutip_teacher_source,tc_readout_teacher,tc_drive_teacher}.py`; add the readout-
  induced-leakage sub-axis (a readout-power-conditioned WG-leak). Each is a SWEPT bracket update + a declared
  re-grounding, not a channel rebuild. Epistemic class (b) bands throughout.
