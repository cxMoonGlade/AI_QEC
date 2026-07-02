# Novelty-ownership adjudication — coupling-simulator paper bones (2026-07-02)

**Scope.** Pure literature adjudication (no code, no reruns). Adversarially decides
OWNED / PARTIALLY OWNED / OPEN for the five candidate math-novelty "bones" of
`docs/twin_validation/HANDOFF_coupling_simulator_2026-07-02.md` §5, backed by close-read
(精读) committed reading notes. Burden of proof is ON novelty: a bone is OPEN only where an
axis-complete search + full-text read of the nearest competitors fails to find an owner.

**Method (executed).** 6 parallel axis search agents (classical-simulability, quantum-noise
asymmetry, process-classicality, counting/waiting-time + QEC-detector-hardware,
noise-learnability/gauge, constrained spectral estimation) → principal triage → 10 full-text
精读 committed notes (below) → principal spot-verification of every load-bearing quote against
the cached `outputs/papers/*.txt` (16/16 protocol; all quotes in this doc are verbatim-verified).

**Epistemic labeling (METRICS.md discipline).**
- Statements of the form "*owner O proves fact F*" are **(a) exact** — each carries a
  verbatim page-anchored quote from a full-text read, usable as a premise.
- Each **verdict** and each "**NO OWNER FOUND**" is a **PROVISIONAL conclusion** — it rests on
  documented search coverage + full-text reads of the nearest competitors, NOT a theorem that no
  owner exists anywhere. Reportable and usable for go/no-go gating on *what to claim vs cite*;
  **nothing may be built on it as a premise** (METRICS.md provisional-conclusion corollary). Flagged
  `[PROVISIONAL]` throughout.
- Suggested §5 / draft amendments are **(c) decision rules** for positioning — proposals for the
  user to ratify, not edits (HANDOFF/tex untouched this round, per the prompt).

---

## Reading notes committed this round (all full-text 精读, principal-verified)

| Slug | Paper | Serves |
|---|---|---|
| `budini_environment_nonclassicality_dissipative_2305.16136` | Budini, PRA 108, 042203 (2023) | A (floor) |
| `paz_silva_multiqubit_gaussian_quantum_noise_1609.01792` | Paz-Silva, Norris, Viola, PRA 95, 022121 (2017) | A (asymmetry) + B (continuous ident.) |
| `plenio_knight_quantum_jump_dissipative_quant-ph-9702007` | Plenio & Knight, RMP 70, 101 (1998) | C (anti-bunching) |
| `gicev_syndrome_error_structure_2310.12448` | Gicev, Hollenberg, Usman, PRR 6, 043249 (2024) | C (QEC-record sign test) |
| `vonlupke_two_qubit_spatiotemporal_noise_spectroscopy_1912.04982` | von Lüpke et al., PRX Quantum 1, 010305 (2020) | #3 (physicality) + B |
| `regev_closed_form_ler_surface_2605.03054` | Regev, Dilley, Delgado, Bennink, arXiv:2605.03054 (2026) | #2 (interpolant) |
| `artag_complementary_quantum_classical_records_2605.15882` | Artag et al., arXiv:2605.15882 (2026) | A (records nearest-neighbor) |
| `maity_kolmogorov_classicality_signatures_2601.01122` | Maity, Ghoshal, Onggadinata, Koh, arXiv:2601.01122 (2026) | A (classicality quantifier) |
| `bath_statistics_tagging_1907.04704` | Farina, Cavina, Giovannetti, PRA 100, 042327 (2019) | C (discriminator competitor) |
| `remm_syndrome_correlation_decoding_2502.17722` | Remm et al., PRR 8, 013044 (2026) | B (detector-moment competitor) |

Pre-existing / reused in-repo notes (verified present, not re-read): `crow_joynt_..._1309.6383`,
`schoelkopf_..._cond-mat-0210247`, `clader_..._2101.11631`, `milz_when_nonmarkovian_process_classical_1907.05807`,
`qec_learnable_logical_noise_2601.22286` (Zheng), `qec_dem_estimation_syndrome_2504.14643` (Blume-Kohout/Young),
`bhardwaj_drifting_noise_estimation_2511.09491`, `kam_*` (2410.23779 / 2603.05474), `harper_flammia_..._2303.00780`.

---

## Verdict table

### Bone A — additive quantum-record decomposition  → **PARTIALLY OWNED** (the three ingredients are each owned; the record-level additive two-kill-switch decomposition is unclaimed). `[PROVISIONAL]`

| Field | Content |
|---|---|
| **Claim** | For qubit(s) + a quantum bosonic bath under R rounds of projective stabilizer measurement, the record-distance to the best classical imitator (classical Gaussian process + deterministic Hamiltonian control, machine-matched) decomposes **additively** into (i) a measurement-independent **non-unital floor** (survives meas-off, ~g², γ/2-pinned) ⊕ (ii) a measurement-modulated ~g⁴ asymmetric-weight piece, each with its own kill switch. |
| **Decisive refs** | Milz PRX 10, 041049 (2020); Smirne QST 4, 01LT01 (2019); Budini PRA 108, 042203 (2023); Paz-Silva PRA 95, 022121 (2017); Schoelkopf cond-mat/0210247; Crow-Joynt PRA 89, 042123 (2014); Landau-Streater LAA 193 (1993) / Kümmerer-Maassen CMP 109 (1987); Artag 2605.15882; Maity 2601.01122. |
| **What owners PROVE** | **(a)** Asymmetry = quantum part: Paz-Silva names S⁻ the "quantum spectrum" and proves it "**is non-zero only when the bath is quantum**" (1609.01792 p.6); Schoelkopf owns up/down-rate ∝ S(∓ω) + detailed balance. **Non-unitality = non-classical:** Budini's indicator gives "**⇒ Qt = 1**" for unital maps (2305.16136 Eq.22) and "any open quantum dynamics induced by coupling the system with stochastic classical degrees of freedom is always unital" — a map-level *quantified* departure-from-unitality; Crow-Joynt own the channel-level qualitative obstruction ("the classical model always gives a linear relation … there is no affine term"). **Record-level classicality dividing line:** Milz owns "when is a repeatedly-measured process classical" (Kolmogorov consistency); Smirne owns the Markovian coherence→population (NCGD) mechanism. |
| **What owners do NOT prove** | None works at the **monitored-stabilizer-record** level with an **additive** floor⊕modulated split. Budini: map/dual-propagator only — flags an "operational definition and experimental measurability" as an **open problem**; no record, no γ/2 constant, no g⁴ modulation (his ~(Ω/γ)⁴ is drive-toward-classicality, *not* our g⁴). Paz-Silva: access is **active control** (filter functions + tomography), expansion is 2nd-order-in-**coupling**, no g⁴-in-measurement, no records. Milz/Smirne: single fixed observable, **single scalar**, no floor, no bath-parameter boundary, zero QEC. Maity: KCC-violation is a **single scalar** with a *multiplicative* factorization (Eq.18), and is manufactured by measuring **off** the pointer basis (vanishes in-basis — the **opposite** of a surviving floor). Artag: a **different axis** — Englert/Zurek which-path complementarity V²+D²=1 in the *environment*, driven by conditioning + Darwinism; N̄ only *smooths* the record, never drives the split. |
| **Surviving sliver (one sentence)** | The **additive, machine-matched record-level decomposition** {measurement-independent non-unital floor ⊕ measurement-modulated g⁴ asymmetric-weight piece} with **two independent kill switches**, for repeatedly-measured qubits — the conjunction and the kill-switch structure, not any one ingredient. |
| **Suggested draft amendment `[(c)]`** | Downgrade every probe-output claim to **cite-not-claim** (already flagged A-P1): asymmetry-kill → Schoelkopf/Clerk/Paz-Silva; meas-off floor → Crow-Joynt (direction) + Budini (quantified map-level); anti-bunching sign → Plenio-Knight (see Bone C); record-classicality → Milz/Smirne. Position the *only* surviving contribution as the **structured decomposition + machine-matched-null instantiation on stabilizer records**, explicitly conceding all three ingredients. This confirms and hardens the Branch-B demotion of Bone A from headline to methodology. |

### Bone C — sign discriminator (anti-bunching in QEC detection records)  → **OPEN**, but the anti-bunching physics is owned (cite), and the premise must be **reframed** (see correction). `[PROVISIONAL]`

| Field | Content |
|---|---|
| **Claim** | Short-lag conditional detection-event excess has **opposite signs** for the two noise classes — emission-jump (low-T amplitude damping) ⇒ **anti-bunched (negative)**; classical common-cause ⇒ **bunched (positive)** — surviving the syndrome fold, as a quantum-vs-classical bath discriminator. Probe measured −4.1e-2 (quantum) vs +3.3e-3 (classical). |
| **Decisive refs** | Plenio & Knight RMP 70, 101 (1998) (+ Kimble-Dagenais-Mandel 1977, Carmichael-Walls 1976); Gicev-Hollenberg-Usman PRR 6, 043249 (2024); Farina-Cavina-Giovannetti PRA 100, 042327 (2019); Gullans et al. arXiv:1402.0235 (discriminator ambition, not read but logged); QEC-hardware burst papers (McEwen 2104.05219, Wilen 2012.06029, Google 2408.13687). |
| **What owners PROVE** | **(a)** Plenio-Knight own the **anti-bunching / waiting-time mechanism**: delay function I₁(τ)=−dP₀/dτ, reset-to-ground on emission ("the normalized state after the detection of a photon … = \|0⟩", Eq.180), and next-jump rate I₁=2Γρ₁₁ (Eq.185) → zero right after a jump ⇒ short-lag anti-bunching; explicitly "for short times τ we expect to see anti-bunching," with the Kimble-Dagenais-Mandel g²(0)<1 lineage cited. Farina et al. own probe-based **bath tagging** (boson-vs-fermion) via state-distinguishability (Helstrom / quantum Chernoff). |
| **What owners do NOT prove** | Plenio-Knight is pure quantum optics (**photodetection** record) — no stabilizer/QEC records, no decoder, no quantum-vs-classical **bath** discriminator. Farina et al. discriminate **boson vs fermion (both quantum)**, via a single-time state-distinguishability **norm** (not a sign of a conditional detection statistic), no QEC. No QEC-hardware paper reports a **negative short-lag detection correlation interpreted as a quantum signature**, nor a **sign-based bath discriminator**. |
| **⚠ Mandatory correction (adversarial finding)** | **The premise "the QEC coincidence object is a probability ≥0, so negatives cannot arise by construction" is FALSE.** Gicev et al. use the field-standard Chen-et-al. p_ij = (⟨xᵢxⱼ⟩−⟨xᵢ⟩⟨xⱼ⟩)/((1−2⟨xᵢ⟩)(1−2⟨xⱼ⟩)) — a **signed covariance ratio**, plotted on a symmetric ±0.04 diverging colorbar; negatives are representable and routinely displayed (they report a qualitative "decorrelation," a reduced-positive, not a quoted negative). The positioning must therefore be reframed away from structural non-negativity. |
| **Surviving sliver (one sentence)** | The **sign of the short-lag conditional detection excess in stabilizer/QEC records, interpreted via emission anti-bunching as a quantum-vs-classical bath discriminator that survives the syndrome fold** — the *transfer* of owned anti-bunching physics into QEC detector statistics + its discriminator use, NOT the anti-bunching itself and NOT any structural-non-negativity claim. |
| **Suggested draft amendment `[(c)]`** | (1) Cite Plenio-Knight (+Kimble-Dagenais-Mandel, Carmichael-Walls) for the anti-bunching mechanism; cite Farina et al. and Gullans for the bath-discrimination ambition, and differentiate the observable. (2) **Replace** any "detection object is ≥0 by construction" language with "**no prior work reports or interprets a negative short-lag detection correlation as an emission-anti-bunching quantum-vs-classical discriminator**"; note p_ij is signed (Gicev). (3) Keep Bone C as a phenomenological discriminator, not a theorem. |

### Bone B — identifiability / blind-spot theorem for detector records  → **PARTIALLY OWNED** (discrete-Pauli gauge framework owned; continuous-Σ × passive-detector-moment map unclaimed). `[PROVISIONAL]`

| Field | Content |
|---|---|
| **Claim** | Complete characterization of which **functionals of a continuous spacetime Gaussian covariance Σ** are identifiable from which **order of passive detector (syndrome-difference) moments**, and which are provably **gauge-invisible**. In-house lemma #4 (single-detector marginals ↔ diag(Σ); off-diagonals enter only ≥2-detector moments) is the base case. |
| **Decisive refs** | Chen et al. Nat. Commun. 14, 52 (2023) (2206.06362); Zheng et al. 2601.22286 (in-repo); Blume-Kohout & Young 2504.14643 (in-repo); Remm et al. PRR 8, 013044 (2026); Paz-Silva PRA 95, 022121 (2017); von Lüpke PRX Quantum 1, 010305 (2020). |
| **What owners PROVE** | **(a)** The **learnable-vs-gauge framework** is owned for **discrete Pauli** parameters: Chen (learnable = cycle space, gauge = cut space of the pattern-transfer graph); Zheng (N&S conditions for Pauli noise learnable from syndromes; explicit gauge/unlearnable subspace via Walsh-Hadamard). Detector-moment **estimation** is owned for **discrete independent events**: Blume-Kohout/Young (p_ij first-principles), Remm ("the probability of any **independent** error event that has a **unique signature** … based on higher-order correlations", degenerate events merely lumped). **Continuous-Gaussian-covariance identifiability** is owned by Paz-Silva / von Lüpke — but via **active control**. |
| **What owners do NOT prove** | Every learnability/gauge result is **discrete Pauli**, not a continuous field: Chen/Zheng characterize error rates/eigenvalues; Remm estimates discrete Bernoulli events per unique signature and **lumps** degeneracies (not a blind-spot theorem), with no "continuous / Gaussian / field / identifiability" content (grep-confirmed absent). Paz-Silva/von Lüpke reach a continuous Σ **only via active-control spectroscopy on isolated qubits**, never passive stabilizer detectors (Paz-Silva 4-step protocol "prepare the qubits in a known state; … measure …"; von Lüpke "**no need for entangled-state preparation or readout of two-qubit observables**", spin-locking + single-qubit tomography). |
| **Surviving sliver (one sentence)** | The **Σ-functional ↔ passive-detector-moment-order identifiability map with a provable gauge/blind-spot subspace, for a continuous spacetime Gaussian covariance** — lifting the discrete-Pauli gauge question (Chen/Zheng) off the Boolean lattice onto a continuous field read from *passive* stabilizer detectors. |
| **Suggested draft amendment `[(c)]`** | Cite Chen 2206.06362 + Zheng 2601.22286 as the **structural template** (learnable/gauge) and state precisely that Bone B lifts it to a continuous Σ read from passive detector moments; cite Remm 2502.17722 as the highest-order discrete detector-moment estimator that stops at independent unique-signature events; cite Paz-Silva/von Lüpke as the active-control continuous-Σ prior art whose observable differs. Present lemma #4 + the full functional↔order map as the contribution. |

### Bone #2 — exact silent-floor functional (interpolating)  → **OPEN** (Clader owns only the binary endpoints). `[PROVISIONAL]`

| Field | Content |
|---|---|
| **Claim** | Exact **interpolating** logical silent-floor functional for **arbitrary** spacetime Gaussian covariance (a finite Fourier sum of Gaussian characteristic functions), generalizing Clader's two endpoints, + the device metric ∂(floor)/∂f\|₀. |
| **Decisive refs** | Clader et al. PRA 103, 052428 (2021) (in-repo, exhaustive note); Regev, Dilley, Delgado, Bennink arXiv:2605.03054 (2026). |
| **What owners PROVE** | **(a)** Clader owns the **binary** Gaussian-moment endpoints — P_unc≈5σ⁴/8, P_cor≈15σ⁴/8 at d=3, the literal 15, the d!! coefficient series — for *independent* vs *perfectly-common* coherent rotations (cite, don't claim). Regev owns a closed-form surface-code LER for **i.i.d. Pauli** with a single **global** correlated mode (cosmic-ray/temperature Bernoulli mixture). |
| **What owners do NOT prove** | Clader's spatial axis is **binary** — no common↔local interpolation parameter, no arbitrary-covariance functional. Regev is "**independent (in space and time) and identically distributed**"; its correlated model is one global scalar mode, a **combinatorial power-law** L≈A(p/p_th)^{d_e}, **not** a Gaussian-characteristic-function sum of a covariance Σ; explicitly defers "more general qubit dependencies in space and time" to future work; **no** interpolation parameter, **no** ∂(LER)/∂(correlation) metric. |
| **Surviving sliver (one sentence)** | The **exact interpolating functional for arbitrary Gaussian Σ as a finite Fourier sum of Gaussian characteristic functions + the ∂(floor)/∂f\|₀ device metric** — the continuous family between Clader's endpoints. |
| **Suggested draft amendment `[(c)]`** | Keep as a **lemma/corollary of the structure lemma (Bone #4)**, not a headline: cite Clader endpoints, claim the interpolant + metric, cite Regev as the nearest 2026 closed-form (i.i.d./global-only). |

### Bone #3 — physicality-guaranteed spatiotemporal noise estimation on real records  → **OPEN**. `[PROVISIONAL]`

| Field | Content |
|---|---|
| **Claim** | Estimator of spatiotemporal noise kernels from **real QEC detector data** with a **Bochner/PSD positivity constraint that guarantees physicality** (the estimate is a valid PSD kernel by construction), demonstrated on real hardware detector datasets. |
| **Decisive refs** | Blume-Kohout & Young 2504.14643, Bhardwaj 2511.09491, Zheng 2601.22286 (all in-repo, operational); von Lüpke PRX Quantum 1, 010305 (2020); GP/Bochner kernel-learning canon (Wilson-Adams; classical PSD-covariance estimation, GGLasso). |
| **What owners PROVE** | **(a)** Operational estimation **from QEC detector data** is owned — Blume-Kohout/Young (p_ij DEM), Bhardwaj (drifting p_ij), Zheng (logical noise) — all **without** a physicality constraint. Physicality-**aware** spatiotemporal spectroscopy is owned by von Lüpke — self- and cross-spectra with a "statistically motivated robust estimation approach." |
| **What owners do NOT prove** | The two literatures **do not intersect**. QEC-detector-data estimators impose **no** PSD/Bochner/CPTP guarantee. von Lüpke's physicality is **emergent, not constrained** — it is **Huber-loss robust M-estimation** (Eq.14), *not* an explicit PSD/Bochner constraint (it even notes fits can "involve a spurious positive-frequency component" that robustness suppresses), and it runs on **isolated sensor qubits via dedicated spin-locking control + single-qubit tomography**, never QEC detector records. |
| **Surviving sliver (one sentence)** | **Bochner/PSD-constraint-guaranteed** estimation of a spatiotemporal noise kernel **from real QEC detector records** — the conjunction (hard physicality constraint) × (QEC-record data source), owned by neither literature. |
| **Suggested draft amendment `[(c)]`** | Position as Branch-B insurance ("theory + real-hardware artifact"). Cite the operational QEC estimators (Blume-Kohout/Young, Bhardwaj) as the unconstrained baseline; cite von Lüpke as the closest physicality-**aware** spatiotemporal spectroscopy but **correct the record**: it is robust (Huber) estimation, not a PSD/Bochner **constraint**, and not on QEC data. A8-compliant (estimation ≠ decoding). |

---

## Frame D — the reveal/conceal duality as an organizing frame

**Question:** is the unifying frame "what syndrome records **reveal** about noise (B + #3) vs what
they provably **cannot** (A + blind spots)" itself already the organizing frame of a prior paper?

**Synthesis `[PROVISIONAL]`.** No prior paper organizes a QEC-noise-simulator contribution around
this reveal/conceal duality across a *continuous field*. The nearest precedent is the
**learnable-vs-gauge duality of Pauli-noise learning** (Chen 2206.06362; Zheng 2601.22286): "which
parameters are recoverable vs which are gauge-invisible." That duality is real prior art — but it
is **single-level and discrete-Pauli**: it is not the two-sided frame that pairs (continuous-Σ
reveal via passive detector moments + physicality-constrained inversion, Bones B/#3) against
(provable blind spots + a non-unital *record floor that classical fields cannot forge*, Bone A).
The process-classicality literature (Milz) supplies a general "what can a classical model reproduce"
half but not the QEC-detector instantiation. **Verdict: Frame D is a defensible *organizing frame*
(presentation-level novelty), not a citable theorem** — legitimate as the paper's spine provided it
explicitly cites Chen/Zheng's learnable/gauge duality as the discrete-Pauli precedent it generalizes.

---

## Negative-coverage log (documented empty searches — the basis for every OPEN/PARTIAL) `[PROVISIONAL]`

Absence-of-owner claims below rest on the 6-axis search coverage + full-text reads of the nearest
competitors named above. They are provisional (documented coverage, not exhaustive proof).

- **A.1** Record-level, machine-matched, **γ/2-pinned non-unital floor** (a lower bound on the
  record-distance to a classical imitator from non-unitality): **NO OWNER.** Budini quantifies it at
  the **map** level only; Crow-Joynt state it **qualitatively** (no constant); the record-level
  version is unclaimed.
- **A.2** **Measurement-modulated ~g⁴ × asymmetric-weight** structure (order-in-**measurement**, not
  order-in-coupling): **NO OWNER.** Searches returned only 4th-order-in-**coupling** master
  equations and optomechanical sideband asymmetry.
- **A.3** **Additive** floor⊕modulated decomposition with **two independent kill switches**: **NO
  OWNER.** Every classicality quantifier found is a **single scalar** (Milz M(C); Maity KCC-violation;
  Leggett-Garg bound) or a **multiplicative** factorization (Maity Eq.18).
- **A.4** Process-classicality instantiated to **stabilizer/QEC syndrome records with an explicit
  bath-parameter boundary**: **NO OWNER** (Milz/Smirne/Strasberg/Taranto/Maity all single-observable,
  non-QEC; spin-boson classicality boundaries are generic single-observable).
- **B.1** Identifiability/blind-spot map of a **continuous Gaussian covariance Σ from a passive
  detector-moment hierarchy**: **NO OWNER.** Learnability/gauge = discrete Pauli (Chen/Zheng);
  continuous-Σ = active control (Paz-Silva/von Lüpke); the conjunction is empty.
- **C.1** A **negative / anti-bunched short-lag detection correlation reported as a quantum
  signature** in real QEC/stabilizer records: **NO OWNER** (all documented QEC correlations are
  positive/excess; Gicev's p_ij is signed but no negative-as-quantum-signature is reported).
- **C.2** A **sign-based quantum-vs-classical bath discriminator in stabilizer records**: **NO
  OWNER** (discriminator ambition exists — Farina boson/fermion, Gullans probe-correlation — via
  different observables, non-QEC).
- **#2.1** An **interpolating arbitrary-Gaussian-covariance logical-failure functional** (finite
  Fourier sum of Gaussian CFs) and a **∂(floor)/∂f device metric**: **NO OWNER** (Clader endpoints
  only; Regev i.i.d./global-only; ∂/∂f absent everywhere).
- **#3.1** **Physicality-CONSTRAINED (PSD/Bochner-guaranteed) noise estimation FROM real QEC detector
  data**: **NO OWNER.** QEC-data estimators are operational (no constraint); Bochner/PSD-constrained
  estimation lives only on isolated-qubit spectroscopy (and von Lüpke's is robust-M-estimation, not a
  hard constraint). The two never meet on QEC data.

---

## Independent cross-check of the OPEN verdicts (Brave Search API, 2026-07-02)

Re-ran the three OPEN slivers (#2, #3, C) through an **independent** search channel (Brave Search
API; committed probe `outputs/brave_confirm_open_verdicts.py`, queries phrased in the
**prove-ownership** direction so an owner would surface if one existed). Result: **all three OPEN
verdicts survive.** No owner of any OPEN sliver appeared; the only new-to-this-doc hits are
additional *operational* estimators that reinforce, not overturn, the verdicts:

- **#3 (physicality-constrained estimation from QEC data):** the closest new hits are two more
  **operational** QEC noise estimators — Takou, Benito, Vezvaee, Lidar & Brown, "Logical error
  estimation from syndrome data of surface-code experiments" (arXiv:2606.11496), and a Bayesian
  syndrome-statistics inference (PRA, doi 10.1103/wg5h-spy6). Full-abstract check of 2606.11496:
  it estimates **DEM event probabilities + decoder priors**, with **no** PSD/Bochner/physicality
  constraint. The SDP hits are all optimal-**recovery** SDPs (Fletcher-Shor-Win; Audenaert-De
  Moor), a different use. The constrained side of the intersection stays **empty**.
- **#2 (interpolating Gaussian-covariance functional + ∂/∂f):** top hits are Regev 2605.03054
  (i.i.d./global, already read) and Wang 2510.24181 (stat-mech *threshold* under NN-correlated
  errors, not a closed-form interpolating failure functional over arbitrary Σ). No
  Gaussian-characteristic-function interpolant and no ∂(floor)/∂f metric surfaced.
- **C (sign discriminator in QEC records):** hits are Gicev 2310.12448 (biased/inhomogeneous,
  not sign-based), bath-tagging 1907.04704 (boson/fermion), and 2603.18231 (radiation-induced
  correlated noise = **positive/burst**, joint sensing+decoding). No negative/anti-bunched
  detection-correlation-as-quantum-signature and no sign-based quantum-vs-classical discriminator
  in QEC records appeared. `[PROVISIONAL]` — a second independent channel agreeing raises
  confidence but is still documented coverage, not a non-existence proof.

---

## Corrections logged this round (adversarial findings that alter positioning)

1. **`[C]` p_ij is signed, not ≥0.** The Chen-et-al. detector-correlation coefficient used across
   real QEC work (Gicev 2310.12448) is a **signed covariance ratio** on a ±diverging colorbar.
   Any "detection object is non-negative by construction" framing is **wrong** and must be replaced
   by "no prior work *reports/interprets* a negative short-lag detection correlation as a quantum
   signature." (Refines memory `project-nonmarkovian-wedge-must-be-coherence` / Bone C.)
2. **`[#3]` von Lüpke physicality is emergent, not constrained.** Its "robust estimation" is
   **Huber-loss M-estimation** (no PSD/Bochner term); physicality is only implicit (fit through a
   physical master equation). Do **not** cite it as prior art for a *constraint-in-the-estimator*
   physicality guarantee — that strengthens, not weakens, Bone #3.
3. **`[general]` authorship:** the IBM syndrome-correlation paper is **Gicev-Hollenberg-Usman
   (2310.12448)**, NOT Harper; Harper-Flammia (2303.00780) is the separate 39-qubit
   correlated-Pauli-learning line. (Corrects a memory guess.)

---

## Bottom line for the paper's math spine

- **Theorem-grade, defensible bones:** **#2** (OPEN — interpolant + ∂/∂f, a clean corollary of the
  structure lemma), **#3** (OPEN — physicality-constrained estimation from real QEC records, the
  Branch-B "theory + hardware artifact" insurance), and **B** (PARTIALLY OWNED — the continuous-Σ
  passive-detector-moment identifiability/blind-spot map, lifting the owned discrete-Pauli gauge
  framework). These three are the strongest spine and align with the Branch-B decision.
- **Demoted bones:** **A** (PARTIALLY OWNED — every ingredient is owned; only the record-level
  additive two-kill-switch decomposition + machine-matched-null instantiation survives, as
  *methodology* not theorem — confirming and hardening the A-P1 / Branch-B demotion) and **C** (OPEN
  but narrow — a phenomenological discriminator resting on owned anti-bunching physics, and requiring
  the signed-p_ij reframe).
- **Frame D** is a legitimate organizing frame (cite Chen/Zheng's learnable/gauge duality as
  precedent), not a citable result.

All verdicts are PROVISIONAL positioning conclusions; the "owner proves X" facts are exact and
quote-anchored. HANDOFF §5 and the tex are unchanged — the amendments above are proposals for user
ratification.
