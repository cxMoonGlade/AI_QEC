# QuTiP First-Principles Channel Derivation — Pre-Registration (theory-first, LITERATURE-GROUNDED)

Status: PRE-REGISTRATION v1, 2026-06-25. User directive: **build ALL teacher channels from QuTiP Hamiltonians/
Lindblads (like path-B did for leakage), in one push; and PUSH the correlation structures into QuTiP where
feasible.** This REPLACES the phenomenological analytic-Kraus channels of the Axis-A teacher + the
teacher-completion crosstalk forms with channels DERIVED from coupled-system Hamiltonians — the honest upgrade
from "modeled" to "first-principles" the un-led reviewer asked for (drive `dr-S2`).

## 0. Architecture (extend path-B; the engine does NOT change)
The path-B leakage channel (`outputs/teacher_prereg/qutip_cz_leakage_channel.py`) established the pattern, REUSED
verbatim here: a coupled-transmon Hamiltonian → QuTiP `propagator`/`mesolve` → superoperator → **truncated-to-Kraus**
(Choi eigendecomposition, `superop_to_truncated_kraus`) → engine-ready Kraus in the `QutritDM` index convention.
- **QuTiP = the CHANNEL-DERIVATION tool** (CPU/dense, one-time, ≤~25-dim per pair; mesolve/propagator). It is
  NOT the engine (mesolve is ODE, ~1000× slower) and NOT the independent oracle (circularity — see §3).
- **The torch-GPU `QutritDM` engine is UNCHANGED** — it applies the precomputed Kraus (`apply_channel` /
  `apply_channel_2site`). The 5 teacher+cert files + the carrier are re-pointed at the QuTiP-derived Kraus.
- **Reuse** the path-B primitives (`ghz`, `mhz`, `transmon_H_static`, `coupling_H`, `superop_to_truncated_kraus`,
  `CZParams`/calibration, `_virtual_z`) — do NOT re-derive the Duffing pair or the truncation algebra.

## 1. The per-channel Hamiltonian/Lindblad ledger (each → engine Kraus; grounded; with a NON-QuTiP oracle)

### Single-transmon physical channels (Lindblad/drive → 3×3 Kraus, |2> tracked)
| # | channel | QuTiP form | grounding | independent oracle | class |
|---|---|---|---|---|---|
| ① | Pauli baseline (recast) | T1 amplitude-damping `c=√γ₁ a` + Tφ dephasing `c=√(2γφ) n` Lindblad, `mesolve` over a cycle → Kraus | Varbanov B3–B6 (the path-B dissipative variant) | **analytic** AD `{√(1-γ),|0><0|+√(1-γ)|1><1|; √γ|0><1|}` + dephasing `{√(1-λ)I,√λ Z}` Kraus | (a)/(b) |
| ② | coherent rx | drive `H=Ω/2 (a+a†)`, propagator over t → `exp(-iθ X)` on {0,1} | standard | **analytic** rotation `rx(θ)` | (a) |
| ③ | amp-damp (non-unital) | T1 Lindblad at the ③ rate (= ① arm, stronger γ) | standard / Varbanov | **analytic** AD Kraus | (a) |

### Two-transmon coherent channels (Duffing pair → 9×9 Kraus; reuse the path-B rig)
| # | channel | QuTiP form | grounding | independent oracle | class |
|---|---|---|---|---|---|
| ④ | leakage transport | 2-transmon Duffing + diabatic flux pulse | Miao/Varbanov | analytic g_eff + Miao fractions | **DONE** |
| ⑤a | ZZ crosstalk | STATIC dispersive pair `H = ζ n₁n₂` (the residual-ZZ from the always-on Duffing dispersion; no flux pulse), propagator t_g → `exp(-iζ t_g n₁n₂)` ≈ `exp(-iφ Z⊗Z)` on {0,1}² | Harper 2605.29514 (J_ZZ·t_g≈1e-3) | **analytic** `exp(-iφ ZZ)=diag(e^{-iφ},e^{iφ},e^{iφ},e^{-iφ})` | (a)/(b) |
| — | drive spillover | driven transmon A: `H_A=Ω(t)cos(ω_d t)(a_A+a_A†)`; spillover on disjoint B: `c·Ω(t)cos(ω_d t)(a_B+a_B†)` (classical crosstalk coefficient `c`) → off-resonant Rabi on B conditioned on A's drive | Sarovar Ex.1 (pulse spillover) | **analytic** off-resonant Rabi `Ω_eff=√(c²Ω²+Δ²)`, `P=(c²Ω²/Ω_eff²)sin²(Ω_eff t/2)` | (b) |
| — | fSim residual | the path-B Duffing+flux rig, calibrated (`cz_propagator_calibrated`); residual `(δθ,δφ)` = the `detune_int` miscalibration knob | Foxen 2001.08343 | **analytic** fSim(δθ,π+δφ) matrix | (b)/(c) bounded-negligible |

### Open-system / bath channels (Lindblad / coupled bath → Kraus)
| # | channel | QuTiP form | grounding | independent oracle | class |
|---|---|---|---|---|---|
| — | readout-induced dephasing | qubit+readout-resonator dispersive `H=χ n a†a` + resonator drive `ε(b+b†)` + Purcell decay `κ`, `mesolve` → measurement-induced dephasing on the measured + spectator qubit | Heinsoo 1801.07904 | **analytic** measurement-induced dephasing `Γφ=8χ²n̄/κ` (dispersive readout) | (b) |
| — | TLS/spectator | qubit+TLS (2-level) `H=g(σ⁺τ⁻+σ⁻τ⁺)` + TLS dephasing/relaxation Lindblad, `mesolve` → the coupled qubit channel | Gao 2605.23385 | **analytic** vacuum-Rabi / Jaynes-Cummings `P=sin²(g t)` | (b) |

## 2. The correlation-structure PUSH into QuTiP (user choice: "push where feasible") — with the honest feasibility gradient
These were classical layers in the phenomenological build. We attempt a first-principles QuTiP derivation; each
declares what becomes first-principles vs what remains bounded-phenomenological (device params unmeasured).
- **⑤b temporal correlation / 1/f (FEASIBLE — the real win).** Couple the data qubit to a BATH of N two-level
  fluctuators (TLFs) with a distribution of switching rates (random-telegraph / `mesolve` with stochastic
  collapse) → a **genuine non-Markovian, temporally-correlated** qubit channel whose 1/f^≈1 spectrum emerges
  from the Dutta-Horn ensemble (Gao Fig 3; switching rates 0.6 mHz–0.2 GHz). The Kam streaky SYNDROME
  correlation then EMERGES from per-round measurement of this process — NOT an imposed R/O/T mask. Independent
  oracle: the **analytic** Dutta-Horn 1/f PSD from the declared TLF rate distribution (closed-form, non-QuTiP);
  + the WS2 `TemporalCorrMask` becomes a CROSS-CHECK target (does the emergent correlation match Kam's class?).
  Bounded simplification: N finite (declared); a single representative round-to-round process. Class (b).
- **readout 2×2 correlated-assignment (FEASIBLE, heavier).** Two qubits + two readout resonators with
  resonator-resonator coupling `J_R` + off-resonant cross-driving (Heinsoo: intra-resonator photon ∝Δ⁻⁴ with
  Purcell, ∝Δ⁻² without); `mesolve` the joint dispersive readout → the correlated IQ outcome + measurement-
  induced spectator dephasing EMERGE. The IQ→bit classifier stays a (declared) classifier on the resonator
  output (soft_readout). Independent oracle: **analytic** Heinsoo intra-resonator photon scaling + the closed-
  form 2×2 assignment from the joint readout SNR. Bounded: resonator Fock truncation (declared, convergence-
  checked); the classifier is not a Hamiltonian. Class (b).
- **burst chip-wide correlation (PARTIAL — small-N demo, mostly bounded-phenomenological).** A COMMON mode
  (cosmic-ray phonon / shared bath) coupled to M qubits → correlated elevated relaxation (McEwen 2104.05219;
  Tan 2406.18897). QuTiP can do a small-M shared-bath demo (the elevated-T1 channel itself is QuTiP-derivable
  per ①); the CHIP-WIDE (d3 = 9q) simultaneity is structural and stays a declared classical broadcast of the
  QuTiP-derived elevated-T1 channel across the footprint. Independent oracle: **analytic** correlated-T1 decay
  + the closed-form detection-density (already built). Class (b) for the channel, (c) for the broadcast.

## 3. Anti-circularity (HARD — `feedback-anti-toy-ground-truth-protocol`)
Every QuTiP-derived channel is checked against an **analytic closed-form oracle INDEPENDENT of QuTiP** (the
rightmost ledger column) — NEVER QuTiP-vs-QuTiP ("our own qutip"). Where a torch-DM / Stim slice gives a third
path, use it. The path-B precedent (analytic g_eff + Miao fractions + ladder couplings, none vs the module's own
output) is the template. The reviewer's caveat that path-B's checks were independent is preserved per-channel.

## 4. Bounded simplifications (declared; unbounded ⇒ STOP)
- **All device params SWEPT, never frozen** (`CZParams`-style dataclasses): T1/Tφ, χ, κ, g_TLS, ζ_ZZ, the drive
  crosstalk `c`, the TLF rate distribution. No device-measured value for several (drive `c`, TLF ensemble) ⇒
  BRACKETED bands, not pinned (honest: first-principles FORM, bracketed MAGNITUDE).
- **Truncation-to-Kraus** is exact on the tracked subspace (Choi eigendecomposition); leaked-out population is
  the completion-policy bias, reported (path-B `identity_sink`, `leaked_population`).
- **Rotating-frame + RWA** where path-B uses it (the |3>/|4> dynamics resolved by `sim_levels`).
- **The 3 correlation pushes** carry the §2 per-item bounds (finite TLF N; resonator Fock truncation; chip-wide
  broadcast). Each declares first-principles-vs-phenomenological explicitly.
- **Per-round-lumped siting** inherited (no within-cycle CZ schedule on the d3 sub-codes).

## 5. Epistemic status (METRICS.md ladder)
- **(a) exact:** the truncation-to-Kraus identity; the analytic oracles; CPTP of every channel (<1e-12).
- **(b) prediction bands:** each QuTiP-derived channel MATCHES its analytic oracle within a declared band (a
  miss is a finding); the emergent ⑤b 1/f spectrum matches Dutta-Horn; the readout correlation matches Heinsoo
  scaling; the drive Rabi matches the off-resonant formula.
- **(c) gates:** the swept brackets (representative, not physical truth — `feedback-underdetermined-bracket-not-
  freeze`); the burst chip-wide broadcast; the IQ classifier.
- Verdict "QuTiP channels certified" stays **PROVISIONAL** (oracle-matched + convergence; nothing built on it).
  Closes with a metric audit + a rigor audit. The CERTIFIABILITY MAP is UNCHANGED by this work (coherent still
  d3-gated; readout excess still sub-MC-floor on d3) — QuTiP buys FAITHFULNESS, not new certifiable signal
  (`[[project-uq-novelty-verdict]]`: infra is 料, not 肉).

## 6. Build org (heavy-task: 3 disjoint builders + un-led reviewer; QuTiP=CPU, GT=serial-GPU)
- **Builder 1 — single-transmon channels:** ① T1/Tφ Pauli-baseline recast, ② coherent rx, ③ amp-damp → 3×3
  Kraus derivers + analytic oracles. (`qutip_single_qubit_channels.py` + cert.)
- **Builder 2 — two-transmon coherent channels:** ⑤a static-ZZ, drive-spillover (driven A + disjoint B), fSim
  residual (reuse path-B rig) → 9×9 Kraus derivers + analytic oracles. (`qutip_twoqubit_channels.py` + cert.)
- **Builder 3 — open-system/bath + the correlation pushes:** readout-dephasing + 2-resonator correlated readout,
  TLS + TLF-bath ⑤b 1/f, burst elevated-T1 + shared-bath → Kraus/process derivers + analytic oracles +
  the emergent-correlation cross-checks. (`qutip_opensystem_channels.py` + cert.)
- **Shared:** all reuse `qutip_cz_leakage_channel` primitives + `tc_crosstalk_observables`. The 5 existing
  teacher files are re-pointed at the QuTiP Kraus in a final integration pass (orchestrator).
- **Reviewer:** UN-LED (stage problem + goal + artifacts only — `feedback-reviewer-no-leading`). STATIC review;
  GT runs SERIAL + small-d3-bounded (NO concurrent GPU — `feedback-no-concurrent-gpu-jobs`). Builders AUTHOR
  only (no heavy QuTiP/GPU runs); the orchestrator serializes the CPU-QuTiP derivation + the GPU GT-checks.
- **Constraints:** GPU-only model compute; scripted-execution (asserts + printed evidence + `__main__` guard);
  mainline (`src/`) changes COMMIT-GATED on the user (the engine itself is unchanged; any `src/` edit, e.g. a
  ququart-dim extension if Arm-2 is needed, is gated). This pre-reg lands before any code.
