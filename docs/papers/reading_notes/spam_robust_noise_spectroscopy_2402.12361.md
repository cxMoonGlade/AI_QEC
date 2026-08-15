# Full-text review -- Khan, Dong, Norris, and Viola, "SPAM-Robust Multi-axis Quantum Noise Spectroscopy in Temporally Correlated Environments" (arXiv:2402.12361)

> **Provenance (2026-07-03): FULL-TEXT read (精读).** PDF via arXiv PDF -> pdftotext extraction. All 26 pp
> (text lines 1-3923) read in full. Figures not pixel-extracted; figure captions and referenced data read from
> body text. Published as Phys. Rev. Applied 22, 024074 (29 August 2024).

## Metadata [paper]

- **Authors / affiliation:** Muhammad Qasim Khan, Wenzheng Dong (Dartmouth College, Dept. of Physics and
  Astronomy); Leigh M. Norris (Johns Hopkins University Applied Physics Laboratory); Lorenza Viola (Dartmouth).
- **Venue / status:** Phys. Rev. Applied 22, 024074 (29 August 2024). arXiv:2402.12361v1 [quant-ph] 19 Feb 2024.
- **Type:** Theoretical proposal + experimental validation (IBM Quantum cloud platform). Single-qubit quantum noise
  spectroscopy protocol design with SPAM-error mitigation.

## Executive summary [paper]

The paper addresses two simultaneous gaps in single-qubit quantum noise spectroscopy (QNS): (1) vulnerability to
SPAM errors, and (2) restriction to dephasing-dominated (single-axis) noise. The authors develop a
spin-locking (SL) QNS protocol that simultaneously estimates all spherical spectra (dephasing and transverse
noise components) and is resilient to static SPAM errors. Experimental validation on the ibmq_armonk device
shows that uncorrected SPAM errors can overestimate noise spectra by up to 26.4%, and that after SPAM
compensation, clear non-classical noise signatures appear in the dephasing spectra.

## Contributions (claim -> evidence -> strength) [paper]

**C1: SPAM-robust single-axis QNS protocol.**
- Claim: Standard SL QNS for dephasing noise can be modified via time-series linear regression (multi-T
  measurements and linear fitting) to extract SPAM-free classical spectra and estimate SPAM parameters.
- Evidence: Eqs. (23)-(25) show that the log-ratio estimator picks up a constant SPAM bias `-ln[α]/T`, which
  vanishes as `T -> ∞` but can be removed at finite T by linear regression (slope = SPAM-free classical spectrum,
  intercept = SPAM parameter `α = α_SP α_M`). Sec. III B demonstrates that quantum spectra require a separate
  non-linear regression, and that `α_M` and `S^{-}(Omega)` remain coupled unless SP errors are negligible
  (the `α ≈ α_M` approximation).
- Strength: **High.** The algebra is explicit and the bias-scaling (1/T) is clearly derived. The
  `α ≈ α_M` approximation is stated as a limitation and its accuracy tied to `ϵ_SP`. The numerical simulation
  (Fig. 2) confirms recovery of SPAM-free spectra.

**C2: Multi-axis SL QNS protocol (spherical-basis formulation).**
- Claim: By using both longitudinal (z-axis) and transverse (x-axis) continuous drives with both `+Omega` and
  `-Omega` amplitudes, a complete set of spherical spectra (dephasing `S_{0,0}`, excitation `S_{1,-1}`,
  relaxation `S_{-1,1}`) can be estimated from observable expectation values.
- Evidence: Eq. (33) is the general second-order time-convolutionless (TCL) master equation under secular
  approximation. Specializing to constant `sigma_z` and `sigma_x` drives yields closed-form DEs (34)-(38)
  that directly relate population and coherence observables to spherical spectrum components. The protocol is
  summarized in Table III; it reduces to three single-axis QNS protocols (one x-drive, plus `±Omega` z-drives).
- Strength: **High.** Built on the Paz-Silva et al. (2019) spherical-basis formalism. The limitation to
  second-order TCL (Born approximation, weak-coupling, Gaussian noise, long-time `|Omega| t >> 1`) is
  clearly stated. No attempt at non-Gaussian or strong-coupling noise.

**C3: SPAM-robust multi-axis protocol and IBM Q validation.**
- Claim: The multi-axis protocol can be modified similarly via linear regression (multi-T measurements) to
  extract SPAM-free spectra; IBM Q data show SPAM causes spectral overestimation up to 26.4% and non-classical
  noise signatures appear only after correction.
- Evidence: Eqs. (49)-(55) extend the single-axis SPAM-robust formalism to the full protocol (Table IV).
  IBM Q data (Figs. 4-6, Table V) show: (a) the spherical excitation spectrum `S_{1,-1}(Omega+omega_q)`
  vanishes after SPAM correction (SPAM was causing spurious excitation artifacts); (b) the dephasing quantum
  spectrum regains the theoretically-required anti-symmetry `S_{0,0}^{-}(-Omega) = -S_{0,0}^{-}(Omega)` only
  after SPAM correction (Fig. 5); (c) the estimated measurement error parameter `α_M = 87.2-88.3%` matches IBM
  calibration data (`88.0%`) within error bars; (d) three runs over 14 hours show consistent stationarity (Fig. 6).
- Strength: **Medium-High.** The number of experimental features is limited (one qubit, 14 driving amplitudes,
  2000 shots, M=10 times per amplitude). The `|Omega| << omega_q` constraint and low-frequency cut-off
  `|Omega| ≲ 2.3 kHz` are practical confounds. The `S_{0,0}(0)` (zero-frequency dephasing) could not be
  characterized due to cloud access limits.

## Method (deep) [paper]

### System and noise model

The qubit is modeled by Hamiltonian `H_lab(t) = (1/2) omega_q sigma_z + H_ctrl(t) + H_SB(t) + H_B` with
additive multi-axis noise: `H_SB(t) = Σ_u sigma_u ⊗ B_u(t)`, where `B_u(t)` may contain both a quantum (non-commuting)
component and a classical stochastic process. The spherical-basis representation (Paz-Silva et al. 2019) reparameterizes
the noise by `α in {-1, 0, 1}` with `v_{±1} = (v_x ± i v_y)/√2` and `v_0 = v_z`.

Assumptions: (i) factorized initial state `ρ_SB(0) = ρ(0) ⊗ ρ_B`; (ii) stationary bath `[ρ_B, H_B] = 0`;
(iii) zero-mean noise `⟨B_α(t)⟩ = 0`; (iv) weak coupling (Born approximation, second-order TCL, no Markov
approximation); (v) secular approximation `ω_q t >> 1` (dropping `α + α' ≠ 0` terms).

### Spin-locking QNS

A constant resonant x-drive `H_ctrl = (1/2) Omega sigma_x` creates a dressed qubit. The toggling-frame
second-order TCL master equation yields, in the long-time `|Omega| t >> 1` limit, closed-form equations for
`⟨sigma_x(t)⟩` in terms of `S^+(Omega)` (classical spectrum) and `S^-(Omega)` (quantum spectrum). The
standard protocol (Table I) uses two initial states (`|x_+⟩` and `|x_-⟩`) to extract both.

Key equations for single-axis:
```
S^+(Omega) = (1/T) ln[ 2 / (⟨sigma_x(T)⟩_{x+} - ⟨sigma_x(T)⟩_{x-}) ]
S^-(Omega) = (⟨sigma_x(T)⟩_{x+} + ⟨sigma_x(T)⟩_{x-})/2 * S^+(Omega) / (1 - e^{-S^+(Omega)T}) + S^+(Omega)
```

### SPAM error model

State preparation (SP): characterized by a single parameter `α_SP` (fidelity `F = (1+α_SP)/2`), plus coherence
terms `c_u` that drop out from the relevant expectation values for rank-2 Pauli coupling.

Measurement errors: two-parameter POVM `Π_{z±} = (α_M/2) sigma_z + (1 ± delta)/2` where `α_M` captures
false-readout rate and `delta` captures readout asymmetry.

Combined SPAM effect on single-axis estimate (Eq. 23):
```
⟨σ̂_x(T)⟩_{x±} = α_M ⟨σ_x(T)⟩_{x±} ∓ α e^{-S^+(Omega)T} + δ
```
where `α ≡ α_SP α_M`.

### SPAM-robust modification (key idea)

The log-ratio estimator for the classical spectrum becomes:
```
ln[2 / (⟨σ̂_x(T)⟩_{x+} - ⟨σ̂_x(T)⟩_{x-})] = S^+(Omega) T - ln[α]
```

The SPAM term `-ln[α]` is independent of `T`. By measuring at multiple evolution times `{T_j}` and performing
linear regression, the slope gives the SPAM-free `S^+(Omega)` and the intercept determines `α`.

For the quantum spectrum, `α_M` and `S^-(Omega)` are coupled. Under the `α ≈ α_M` approximation (SP errors
negligible compared to measurement errors, which holds for many NISQ devices), a non-linear regression
(Table II) or linearized regression (when `S^+(Omega) T << 1`) extracts `S^-(Omega)`, `α_M`, and `delta`.

### Multi-axis generalization

Three sets of drives are needed:
1. `H_ctrl = +(1/2) Omega sigma_z`: yields `S^+_{1,-1}(Omega+omega_q)`, `S^-_{-1,-1}(-Omega-omega_q)`, `S_{0,0}(0)`
2. `H_ctrl = -(1/2) Omega sigma_z`: yields `S^+_{-1,1}(Omega-omega_q)`, `S^-_{1,-1}(-Omega+omega_q)`
3. `H_ctrl = +(1/2) Omega sigma_x`: yields `A(Omega)` and `B(Omega)`, from which `S^+_{0,0}(Omega)` and `S^-_{0,0}(Omega)`
   are extracted using the transverse spectra from steps 1-2.

The SPAM-robust modification (Table IV) repeats each sub-protocol at multiple `{T_j}` and applies the same
linear-regression separation.

### IBM Q implementation

Device: ibmq_armonk (single fixed-frequency transmon, retired; `ν_q = 4.97 GHz`, `T_1 = 169.66 us`,
`T_2 = 256.44 us`). Practical modifications: (a) z-drives implemented via virtual Rz gates + free evolution
(Trotterized with N=1000 steps); (b) x-drives as concatenated 19 us pulse segments (API sample limit);
(c) frame-alignment: measurement times chosen as `T^{(n)}_j = 2π n_j / |Omega_i|` for coherence observables.

Limitations: `S_{0,0}(0)` not characterized; 14 amplitudes `|Omega| ≲ 3.83 MHz`; low-frequency cut-off
`|Omega| ≲ 2.3 kHz` (oscillation artifacts). 2000 shots, M=10 times per amplitude.

## Results (deep) [paper]

### Numerical simulation (single-axis)

- **Noise model:** Non-commuting bath (qubit interacting via Eq. 30 with lag `γ=0.5`), Lorentzian generating
  spectrum `S̃(ω) = 1/(1 + t_c^2(|ω|-ω_0)^2)` with `ω_0/2π = 4.0 MHz`, `t_c = 0.5 μs`.
- **SPAM effect (Fig. 1):** At `α_SP=0.98, α_M=0.94, δ=0.02` (~8% total SPAM error), the classical spectrum
  is uniformly offset and the quantum spectrum shows both offset and rescaling.
- **SPAM-robust recovery (Fig. 2):** With the same `α` but attributed entirely to measurement errors
  (`α_M=0.92, δ=0.02`), the SR QNS protocol recovers both classical and quantum spectra to excellent
  agreement with the target. SPAM parameters estimated to high precision.
- **Error-rate dependence (Fig. 3):** Advantage of SR QNS diminishes with decreasing SPAM error rate; some
  advantage retained even at 1 %.

### IBM Q experiment

- **SPAM-free spectra (Fig. 4):** Standard protocol shows an increasing `S_{0,0}(Omega)` at higher drive
  amplitudes; the SPAM-robust protocol gives a plateau. The spherical excitation spectrum `S_{1,-1}(Omega+ω_q)`
  vanishes after SPAM correction (SPAM was producing spurious apparent excitation).
- **Quantum spectrum asymmetry (Fig. 5):** Without correction, `S^-_{0,0}(Omega)` shows an offset from zero
  (an artifact of the measurement asymmetry parameter `δ`). After SPAM correction, it regains the theoretically
  required anti-symmetry -- a clear indicator of non-classical (quantum) noise.
- **Stationarity (Fig. 6):** Three runs over 14 hours show consistent spectra, indicating good noise stationarity.
- **SPAM parameters (Table V):** `α_M = 87.2-88.3%` (vs. IBM calibration 88.0%); `δ = 3.2-3.8%` (vs. IBM
  calibration 1.38%, outside 95% CI -- attributed to limited data).

### Quantitative claim

"SPAM errors can cause spectra to be overestimated by up to 26.4% in a classical noise regime" (abstract).
This is reported as the peak distortion amplitude, not a per-frequency average.

## Methodology assessment (6-criterion)

| Criterion | Score (1-5) | Rationale |
|---|---|---|
| Soundness | 5 | Theoretical derivation is rigorous (second-order TCL, secular approximation, explicit filter-function limits). All assumptions stated and discussed. SPAM model is standard. |
| Novelty | 4 | First SPAM-robust multi-axis QNS protocol. The key idea (multi-T linear regression to factor out SPAM bias) is simple but effective. Prior single-axis QNS and comb-based multi-axis QNS (Paz-Silva 2019) exist, but combining all three axes with SPAM robustness is new. The quantum-spectrum asymmetry test for non-classical noise is a nice application. Not paradigm-shifting. |
| Reproducibility | 4 | IBM Q platform (even if the specific device is retired). All parameters (T1, T2, ν_q) and experimental conditions (amplitudes, shots, times, pulse parameters) reported. The Trotterization for z-drive and pulse-concatenation for x-drive are described. Main limitation: IBM Q API constraints and cloud access limits mean exact reproduction would need access to similar hardware. |
| Experimental design | 3 | Adequate for a proof-of-principle on a single qubit. Limited by: one device, 14 amplitude points, 2000 shots, M=10 times, one calibration window (14 h/24 h cycle). The `S_{0,0}(0)` datum was missed entirely. The low-frequency cut-off (oscillation artifacts) is a significant concern. No comparison to a competing SPAM-robust approach (none exists, but cross-validation with e.g. confusion-matrix readout mitigation would strengthen claims). |
| Statistical rigor | 3 | Weighted linear regression used; standard error propagation from binomial statistics (2000 shots -> Gaussian approx). 95% CI reported. However: M=10 time points per amplitude is small; the linearized regression (long-time `S^+T << 1` regime validity not exhaustively checked); no multiple-testing correction across frequency points. The claim "up to 26.4%" has no confidence interval. |
| Scalability | 2 | Single-qubit only. The protocol requires three sets of continuous drives + multi-T measurements per amplitude -- overhead grows linearly in the number of qubits, but the paper explicitly acknowledges multi-qubit extension as an open challenge. The TCL framework extends to multi-qubit (Paz-Silva 2017) but experimental complexity (no crosstalk, independent controls) grows rapidly. |

## Strengths [paper]

**S1: Clean algebraic separation of SPAM bias.** The key insight is that the SPAM contribution to the log-ratio
estimator is constant in T while the signal grows linearly -- allowing a simple linear-regression fix. This is
elegant and should generalize to other spectroscopy protocols. (Sec. III A, Eqs. 23-25, 28-29.)

**S2: Quantum-noise-asymmetry test.** The observation that the uncorrected `S^-_{0,0}(Omega)` lacks the
required anti-symmetry, and that the SPAM-robust protocol restores it, is a clean fingerprint of successful
SPAM correction. This is a non-trivial consistency check that boosts confidence in the data. (Sec. V C,
Fig. 5, lines 2108-2118.)

**S3: Self-consistent SPAM estimation.** The protocol estimates SPAM parameters alongside noise spectra,
without requiring separate calibration experiments or ancilla qubits. The `α_M` estimate matches IBM's
independently-calibrated value within error bars. (Sec. V C 2, Table V.)

## Weaknesses / limitations [paper]

**W1: SP and measurement errors cannot be separately estimated from the protocol alone.** The `α ≈ α_M`
approximation (negligible SP errors vs measurement errors) is required for quantum spectrum estimation. This
is stated as a limitation and the authors discuss possible workarounds (independent SP characterization).
But it means the "SPAM-robust" label applies fully only to the classical spectra; the quantum spectra still
depend on the SP-vs-M error ratio. (Sec. V B, Discussion lines 2328-2336.)

**W2: Second-order TCL = Gaussian noise only.** The weak-coupling Born approximation restricts the protocol to
Gaussian noise statistics. Non-Gaussian noise, which is important for TLS defects and two-level fluctuators
in superconducting qubits, requires higher-order (fourth-order) spectral estimation. The authors note this and
suggest frame-based QNS as a possible non-Gaussian extension, but do not develop it. (Discussion, lines 2339-2347.)

**W3: Low-frequency blind spot.** The protocol has a practical low-frequency cut-off (`|Omega| ≲ 2.3 kHz`) where
oscillation artifacts dominate. For 1/f noise (dominant in superconducting qubits at low frequencies), this
is a significant gap. The `S_{0,0}(0)` DC dephasing spectrum is claimed to be characterizable via
`⟨σ_x(T^{(n)})⟩` under z-drive with frame alignment (Eq. 49), but could not be experimentally demonstrated.
(Sec. V C, lines 1883-1896.)

**W4: Single-qubit only, with no direct path to multi-qubit.** The protocol is explicitly for a single qubit
with fixed energy splitting. Multi-qubit extensions (needed for the twin's QEC context) are left as "future,
separate investigation." While the spherical-basis formalism has a multi-qubit version (Paz-Silva 2017), the
SPAM-robust extension would need to handle correlated SPAM across qubits and crosstalk in the continuous
drives. (Discussion, lines 2348-2356.)

## Relevance to the twin [paper -> ours]

### 1. SPAM-aware calibration (RECOVER capability)

The twin's label-free learner (`calibration`) consumes only syndrome observations. The paper's central finding
-- that SPAM errors can bias noise spectral estimates by up to 26.4% -- directly quantifies the seriousness
of ignoring SPAM in the twin's calibration pipeline. Our calibration module operates on detector-format
syndrome data which inherently includes SPAM errors (measurement errors are baked into the detector outcomes;
state preparation imperfections enter through the initial state of each shot).

**Actionable insight:** The paper's linear-regression approach to factor out static SPAM bias (estimate
spectra at multiple times and extract slope = SPAM-free spectrum, intercept = SPAM parameter) is a candidate
template for handling SPAM in the twin's calibration. However, the twin's data is from QEC circuits (many
qubits, many rounds), not single-qubit SL experiments, so the method cannot be directly transferred. The
*principle* (exploit the different T-dependence of SPAM vs. signal) may generalize to multi-round
syndrome sequences where SPAM acts only on the first and last rounds.

**Non-trivial difference:** The paper's active-protocol QNS (requires special pulse sequences and state
preparations) is fundamentally different from the twin's *passive* syndrome-based learning. The paper's
protocols measure controlled qubit response; the twin learns from uncontrolled QEC round outcomes. This makes
the paper complementary rather than directly usable in the twin's codebase.

### 2. Non-classical noise detection (UNDERSTAND capability)

The paper demonstrates non-classical (quantum) noise in IBM dephasing spectra via the asymmetry of
`S^-_{0,0}(Omega)` (which is non-zero and anti-symmetric when the noise has a non-commuting quantum
component). This is relevant to the twin's UNDERSTAND capability, which aims to interpret the recovered
noise channel.

**Link to the Girsanov split:** The paper's classical/quantum spectral decomposition (`S^+` vs `S^-`)
is a frequency-domain manifestation of the same coherent-vs-incoherent decomposition that appears as
the Girsanov split in the twin's framework (Kaufmann 2307.08741, Ivashkov 2603.05492). The paper's
quantum spectrum `S^-_{0,0}(Omega)` corresponds to the coherent (Hamiltonian) component that survives
only when noise operators do not commute in time. This reinforces the physical basis of the twin's
decomposition -- the split is real and experimentally verifiable at the spectral level.

**Twin relevance:** The paper's non-classical noise detection method (checking spectral anti-symmetry
after SPAM correction) could serve as a validation diagnostic for the twin's recovered channel, confirming
that the coherent component is physically meaningful and not a SPAM artifact.

### 3. SPAM identifiability (IDENTIFIABILITY framing)

The paper's finding that `α_M` and `S^-` are coupled (cannot be separated from single-qubit SL dynamics
alone) is an identifiability result, though the paper does not use the gauge-freedom/identifiability
language of the twin's ADR framework. The coupling means there is an observational equivalence class
of `(α_M, S^-)` pairs that produce the same data -- the same structure as the gauge freedom in the
twin's channel-level parameterization.

**Twin relevance:** This reinforces the twin's identifiability-aware methodology. The paper's
solution (rely on `α ≈ α_M`) is a gauge-fixing convention, not a fundamental resolution of the
non-identifiability. The twin should adopt a similar posture: declare the SPAM-related gauge
explicitly, bracket the uncertainty, and avoid claiming precise SPAM separation without independent
evidence. See ADR 0005 (the retire-SCOPE reframe) for the twin's treatment of similar
observational-alias issues.

### 4. Label-free learner interaction with SPAM

The paper's protocols are active (designed control sequences with dedicated state-preparation and
measurement), while the twin's learner is passive (observes QEC round outcomes only). However, the
paper's SPAM model (Eqs. 18-19) is a candidate for the twin's measurement-error layer -- the
two-parameter POVM with `α_M` and `δ` is a reasonable description of the measurement assignment
errors in the twin's detector data. The noise spectroscopy methods in this paper can serve as an
independent SPAM characterization reference for the hardware target, similar to how randomized
benchmarking provides gate error estimates.

**Connection to the 26.4% overestimation figure:** This number quantifies how seriously SPAM can
corrupt noise characterization even in a simple single-qubit setting. For the twin's QEC setting,
where SPAM errors are present in every round of syndrome extraction, the impact may be even larger
(or differently structured). The twin must either (a) include SPAM explicitly in the forward model,
(b) demonstrate that the calibration is robust to the SPAM levels present in the data, or
(c) characterize SPAM independently (e.g., via this paper's methods) and fix its contribution.

### 5. Twin test implications

- This paper's SPAM model and protocols are **complementary** to the twin's main line (passive
  syndrome-based learning) -- not a replacement or competitor.
- The paper supports the physical reality of the twin's coherent/incoherent decomposition
  (Girsanov split) by showing non-classical noise is detectable and survives SPAM correction.
- The `α - S^-` coupling is a direct example of the identifiability/gauge issue the twin's ADR
  framework was designed to handle.
- The paper's multi-T linear-regression SPAM-robustness principle is a candidate to inform the
  twin's future multi-round SPAM handling, though the specific implementation would differ.

## How to use / trust [paper]

- **Theoretical core (Secs. II-IV):** Trustworthy. The TCL master equation and secular approximation
  are standard in the field; the algebra is explicit and the assumptions clearly bounded.
- **Numerical simulations (Sec. III C):** Trustworthy. Well-defined toy model with analytically known
  spectra; 1000-shot statistics; consistent with theory.
- **IBM Q experiment (Sec. V C):** Use with caution. Single device (retired), limited statistics
  (2000 shots, M=10 times, 14 amplitudes), one calibration window. The 26.4% overestimation figure
  is a headline number from a specific operating point, not a bound for all settings. The `δ=3.2-3.8%`
  vs. calibration `δ=1.38%` discrepancy suggests some unmodeled systematic effect.
- **SPAM parameter `α_M` match (87-88% vs. 88%):** The agreement with IBM calibration is good
  evidence the protocol works as advertised for measurement error.
- **Quantum spectrum asymmetry:** The restored anti-symmetry (Fig. 5) is the strongest experimental
  evidence that the SPAM correction is working correctly.

## Open questions

1. **Multi-qubit SPAM-robust QNS:** Can the approach be extended to 2+ qubits with correlated noise
   without requiring per-qubit independent continuous drives? The paper leaves this as future work.
2. **Non-Gaussian noise:** Can a SPAM-robust version of frame-based or fourth-order QNS be developed
   that handles non-Gaussian noise (e.g., from TLS fluctuators)?
3. **Passive QEC-data equivalent:** Is there an analogue of the multi-T linear-regression SPAM
   decoupling that works for passive syndrome observations (the twin's data modality), rather than
   active SL experiments?
4. **Zero-frequency dephasing `S_{0,0}(0)`:** The paper could not measure this experimentally.
   Is there a practical workaround for the low-frequency oscillation artifacts?
5. **SP-vs-M disambiguation:** Can augmented control (e.g., time-dependent modulation, or additional
   readout bases) separate SP and measurement errors in the quantum spectrum estimation?

## Related twin cached notes

- `paz_silva_multiqubit_gaussian_quantum_noise_1609.01792.md` -- Multi-qubit spherical-spectrum
  formalism extended from here. The present paper's spherical-basis TCL framework is built on this.
- `vonlupke_two_qubit_spatiotemporal_noise_spectroscopy_1912.04982.md` -- Two-qubit SL spectroscopy
  (predecessor of the present paper's method). That work also uses SL but without SPAM robustness.
- `schoelkopf_qubits_spectrometers_quantum_noise_cond-mat-0210247.md` -- The qubit-as-spectrometer
  canon that underlies all QNS.
- `google_suppressing_errors_budget_2207.06431.md` / `google_below_threshold_error_budget_2408.13687.md` --
  Error budgets provide the hardware context for why SPAM matters for the twin.
- `budini_environment_nonclassicality_dissipative_2305.16136.md` -- A different (map-level) quantum
  non-classicality quantifier, complementary to the frequency-domain quantum spectrum asymmetry.
- `clerk_quantum_noise_measurement_amplification_0810.4729.md` -- RMP quantum-noise reference for the
  `S^+`/`S^-` decomposition and fluctuation-dissipation relations used here.
