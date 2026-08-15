# Full-text review — Rojas-Arias, Camenzind, Wu, Stano, … Tarucha, "Scaling of silicon spin qubits under correlated noise" (arXiv:2603.03051v1, 3 Mar 2026)

> **Provenance (2026-07-02): FULL-TEXT read (精读).** Cached full text
> `outputs/papers/2603.03051.txt` (WSL path; also reachable as
> `\\wsl.localhost\ubuntu-f\home\cx\Document\AI_QEC\AI_QEC\outputs\papers\2603.03051.txt`),
> 26 pp, read end-to-end incl. Methods (device, PSD, TLF model, repetition/surface-code error-rate
> derivations Eqs. 16–34) and Extended Data A1–A10 captions. All §/Eq/Fig refs from that text; the plotted
> LER/correlation curves (Figs. 4, 5, A6, A8, A9) are not pixel-extracted — the load-bearing NUMBERS quoted
> here are those stated in the running text + captions. **Authored by opus subagent 2026-07-02; pending
> principal spot-verification.** Tags: **[paper]** = stated in the paper; **[twin]** = our
> application/inference for `qec_twin`, NOT the paper's claim.

## Metadata [paper]
- **Authors / affiliation.** Juan S. Rojas-Arias, Leon C. Camenzind, Yi-Hsien Wu, Peter Stano, Akito Noiri,
  Kenta Takeda, Takashi Nakajima, Takashi Kobayashi, Giordano Scappucci, Daniel Loss, Seigo Tarucha (RIKEN
  RQC/CEMS; Slovak Acad. Sci.; QuTech/TU Delft; Basel; KFUPM). Same Rojas-Arias/Stano/Tarucha line as the
  spatial-correlation Si-spin papers [refs 27, 28, 30, 41] this work builds on.
- **Venue / status.** arXiv:2603.03051v1 [cond-mat.mes-hall], 3 Mar 2026. Article + Methods + Extended Data
  (A1–A10) + refs (26 pp).
- **Type.** **Experiment** (24-hour interleaved-Ramsey noise spectroscopy of a 5-qubit Si/SiGe array over 8
  months / 2 cooldowns) + **microscopic TLF model** (Monte Carlo dipole ensembles) + **analytic/numerical
  QEC impact study** (repetition code analytic; surface code via Monte-Carlo subset sampling). NOT a QEC
  hardware demonstration — the QEC part is a code-capacity calculation fed by measured correlation profiles.

## Executive summary [paper]
Quantifies the spatial extent of dephasing-noise correlations in a 5-qubit Si/SiGe array and feeds the
measured profile into a QEC-scaling calculation. Two correlated-noise sources are separated:
- **Global magnetic-field drift** (superconducting-magnet demagnetization, ~8 Hz/s) → **perfectly correlated**
  (`|c(f)|=1`), distance-independent, dominant below ~10⁻² Hz. Sets a **hard lower bound on LER** (Ext. Data
  A8), but is technical: mitigable by feedback / decoherence-free subspaces / better magnets.
- **Charge noise from two-level fluctuators (TLFs)** → **partially correlated** (`0<|c(f)|<1`), short-range,
  above ~10⁻² Hz. Distance decay well fit (in the accessible range) by exponential `e^{−x/l_c}` with
  **`l_c = 81 nm` (= `N_c=0.75` at spacing `L_q=108 nm`)**; TLF Monte-Carlo model (single fit parameter
  `ρ_TLF=3×10¹⁰ cm⁻²`) reproduces short/intermediate range and predicts a `∝x^{−4.2}` screened polynomial
  tail; a statistically significant `4.89σ`/`8.20σ` remnant correlation at 3rd/4th neighbors exceeds the
  TLF-only model (Ext. Data A10) but changes the QEC LER by `<7%`.
- **QEC impact (fixed marginal `p≈10⁻²`).** Repetition code `⟦N,1,N⟧` (analytic) + surface code (MC, limiting
  regimes only). **Uncorrelated** → exponential LER suppression. **Perfectly correlated** → suppression
  "much weaker", surface-code LER drops **less than two orders of magnitude going d=1→d=15** (=225 data
  qubits). **Partially correlated (measured charge noise ≈ `N_c≈1`)** → "nearly indistinguishable from"
  uncorrelated, "only marginally worse"; LER `<10⁻¹⁰` reachable at **`d=13` (1D) / `d=15` (2D)** with no
  overhead vs uncorrelated.
- **Headline conclusion (verbatim):** *"correlated noise in silicon spin qubits, while present, does not
  represent a fundamental obstacle to fault-tolerant quantum computing at the levels observed here."*

## Setup exact — codes, correlation model, fixed-marginal methodology [paper]
### Codes analyzed
- **Repetition code `⟦N,1,N⟧`** correcting phase-flip errors, `d=N`, corrects up to `(N−1)/2` errors
  (Methods "Repetition code error rate", Eqs. 16, 27). Logical states are product states
  `|0_L⟩=∏_k|+⟩_k`, `|1_L⟩=∏_k|−⟩_k` (Eq. 16). Analytically tractable — used as the workhorse.
- **Surface code `⟦d²,1,d⟧`**, `N=d²` (Methods "Surface code error rate", Eqs. 28–34). Only the
  **uncorrelated** and **perfectly correlated** limits are computed (intermediate is intractable there).
- **1D vs quasi-2D repetition-code embedding** (Fig. 5b upper) to isolate pure geometry from code structure.

### Correlation model
- Primary measure = **normalized cross-PSD** `c_{α,β}(f)=C_{α,β}(f)/√(S_α S_β)` ∈[0,1] (Methods Eqs. 1–2);
  phase 0 = in-phase (global), π = out-of-phase (TLF between qubits), other = delay.
- QEC input = **spatial correlation coefficient** `c_{i,j}=exp(−|r_i−r_j|/(N_c L_q))` (exponential, Fig. 5a)
  OR the TLF-model-averaged profile; `N_c` = decay length in units of qubit spacing (`N_c=1` ⇒ decay within
  nearest neighbors; `N_c→0` uncorrelated; `N_c→∞` perfectly correlated).
- **Joint-Gaussian phase treatment (verbatim, Methods Eqs. 20–25):** the accumulated phase
  `ϕ_k=∫₀^τ δν_k(t)dt` (Eq. 17); for jointly-Gaussian zero-mean phases *"⟨e^{iX}⟩=exp(−½⟨X²⟩)"* with
  `X=Σ_j a_j ϕ_j` [ref 65, Kubo cumulant] (Eq. 22). So all averages of products of `cos ϕ_j` reduce to
  two-point correlators `⟨ϕ_i ϕ_j⟩=c_{i,j}⟨ϕ²⟩` (Eqs. 23, 25). This is the **same Gaussian-moment machinery
  our A9 (a) uses** (Clader `⟨e^{iX}⟩=exp(−½⟨X²⟩)`), applied to the correlation-length sweep.

### Fixed-marginal methodology (verbatim) — the (a)-anchor construction
The physical single-qubit error rate is **held fixed** while the correlation length is swept:
- **(Methods "Repetition code error rate", verbatim):** *"We adopt a physical phase-flip error rate
  `p = 10⁻²`, corresponding to dephasing accumulated during a cycle time `τ = 1 µs`."* Realized via the
  single-qubit map `p = ½(1−e^{−⟨ϕ²⟩/2}) = ½(1−e^{−τ²/T₂*²})` (Eq. 26), with measured `T₂* ≈ 7 µs` giving
  `p≈10⁻²`.
- **(Main text, verbatim):** *"For spatial correlations, we either use the correlation profile predicted by
  the TLF model (averaged over ensembles) or an exponential form `c_{i,j}=exp(−|r_i−r_j|/N_c L_q)`."* The
  correlation `c_{i,j}` enters ONLY the OFF-diagonal `⟨ϕ_iϕ_j⟩` (Eq. 25); the diagonal `⟨ϕ²⟩` (hence `p`) is
  pinned. ⇒ **correlated vs uncorrelated differ only in structure at matched single-qubit marginal** — the
  identical construction to our fixed-χ (fixed-marginal) correlated sweep, and to Clader 2101.11631 / Kam
  2410.23779 Appendix A.

## Load-bearing numbers — LER / distance-scaling degradation [paper]
- **Correlation length:** `l_c = N_c L_q = 81 nm`, `N_c = 0.75`, `L_q = 108 nm` (Fig. 4 caption). TLF density
  `ρ_TLF = 3×10¹⁰ cm⁻²` (single fit parameter; screened-charge-trap alt model gives `5×10¹⁰ cm⁻²` but needs
  `ℏω₀>10 meV`, ruled out). Screened dipole tail `∝x^{−4.2}`; unscreened `∝x^{−3}` (Ext. Data A6). Measured
  gate-voltage tunability: nearest-neighbor avg correlation `0.57` at ~108 nm vs `0.20` at ~137 nm (Fig. 3b).
- **Fixed physical rate:** `p = 10⁻²` (cycle `τ=1 µs`, `T₂*≈7 µs`), Eq. 26.
- **Surface code, perfectly correlated (the headline degradation, verbatim, Fig. 5b caption):** *"While
  uncorrelated noise yields exponential suppression of logical errors with increasing distance, perfectly
  correlated noise results in a reduction of less than two orders of magnitude when increasing the distance
  from d = 1 to d = 15."* (`N=d²=225` at d=15 ⇒ the weak suppression is at large qubit overhead.)
  [twin-note: the task guessed "100–1000×"; the paper's stated figure is *< 2 orders of magnitude total*
  over d=1→15 under PERFECT correlation — i.e. the OPPOSITE end (weak suppression), not a 100–1000× LER
  penalty at a fixed d. Use the paper's framing.]
- **Perfectly correlated LER lower bound (Ext. Data A8):** a global source with variance `⟨ϕ_c²⟩` gives
  `p≈⟨ϕ_c²⟩/4` and `c_{i,j}=1` for all pairs; adding uncorrelated noise cannot get BELOW the
  perfectly-correlated curve (the correlation-dilution is exactly counteracted by the raised single-qubit
  rate) — a HARD LER floor from magnetic drift.
- **Partially correlated (measured charge noise, `N_c≈1`):** "nearly indistinguishable from an exponential
  decay with `N_c≈1`", "only marginally worse than the uncorrelated limit"; `LER<10⁻¹⁰` at **`d=13` (1D
  repetition)**, **`d=15` (2D)** — no overhead vs uncorrelated. Surface code (limiting regimes) "closely
  resemble those of the repetition code".
- **Repetition-code error-rate machinery (for reproduction):** `p_n=Σ_{S∈K_n}⟨∏_{i∈S}|β_i|²∏_{j∉S}|α_j|²⟩`
  (Eq. 19) with `α_k=cos(ϕ_k/2)`, `β_k=sin(ϕ_k/2)` (Eq. 18); `p_err=Σ_{n≥(N+1)/2} p_n` (Eq. 27).
  Uncorrelated ⇒ binomial `p_n=C(N,n)p^n(1−p)^{N−n}` (Eq. 31); perfectly correlated ⇒ Eq. 32 (double-sum,
  `≈C(N,n)p^n Σ_k C(N−n,k)[2(n+k)−1]!!(−p)^k`, Eq. 32b — **the `!!` double-factorial** signature, cf. A9).
  Surface code: `p_err=Σ_n F_n p_n` (Eq. 29), `F_n`=fraction of uncorrectable weight-`n` configs from Stim +
  PyMatching MC (`n_samples=15000`); subset-sampling bounds `p^{LB}_err`/`p^{UB}_err` with cutoff `n_max=14`
  (Eqs. 33–34).

## KEY LIMITATION verbatim — code-capacity / ideal syndrome extraction (the (a)-caveat) [paper]
The QEC calculation neglects everything about the extraction circuit — this is exactly why, *by
construction, they cannot see a detection-rate / measurement-back-action effect*:
- **(Methods "Repetition code error rate", verbatim):** *"In this analysis, we focus exclusively on
  correlated dephasing acting on the data qubits. We neglect correlations between data and ancillary qubits
  used for syndrome extraction and assume ideal syndrome extraction, decoding, and correction. Thus, the
  logical error rate reflects solely the impact of spatially correlated dephasing during the QEC cycle."*
- **(Main text, verbatim):** *"To isolate the impact of correlated dephasing, we assume ideal syndrome
  extraction, decoding, and correction, so that no additional error channels are introduced during the QEC
  cycle."*
- Also (main text): *"These estimates neglect relaxation processes (T₁ = ∞) and other hardware and decoding
  imperfections. In practice, such effects will reduce performance …, requiring larger code sizes where
  long-range correlations may become more relevant."*

⇒ **This is a data-qubit-only, single-shot code-capacity model with perfect ancillas/measurement.** There
are NO syndrome-extraction rounds, NO mid-circuit measurement, NO detection events, NO measurement
back-action, NO silent-run isolation. The `⟦N,1,N⟧` code is applied to a product state, one dephasing
window, decode once (Eqs. 16–19, 27). This is the precise sense in which prereg A9 flags it: *"CODE-CAPACITY
with ideal syndrome extraction."*

## "Compatible with fault tolerance" — conclusion sentences verbatim [paper]
- Abstract: *"In contrast, the measured charge noise correlations are moderate, electrically tunable, and
  compatible with fault-tolerant operation with minimal qubit overhead."*
- Intro/summary: *"Our main conclusion is that correlated noise in silicon spin qubits, while present, does
  not represent a fundamental obstacle to fault-tolerant quantum computing at the levels observed here."*
- Results (surface code): *"Since the TLF-based correlations observed in our device are far from the perfectly
  correlated limit, we conclude that the level of noise correlations typical for current semiconducting
  devices does not fundamentally limit surface-code implementations, even though these correlations are
  sizable."*
- Conclusions: *"Our results establish that correlated noise in silicon spin qubits, while present, does not
  constitute a fundamental barrier to fault-tolerant quantum computing at the levels observed here."*
- Caveat carried by the authors themselves: global magnetic drift *"imposes a hard lower bound on the logical
  error rate"* (needs mitigation); and the FT verdict is "at the levels observed here" with `T₁=∞` and ideal
  extraction — not a circuit-level claim.

## What they do NOT do (scope boundaries) [paper]
1. **No circuit-level noise / no mid-circuit measurement.** Ideal syndrome extraction, `T₁=∞`, perfect
   ancillas (quoted above). No extraction rounds, no measurement channel.
2. **No detection-event observables, no detection-rate change, no syndrome-silent-RUN isolation.** The model
   never produces detectors; LER is computed combinatorially from data-qubit phase correlators (Eqs. 19, 27).
   The detection-rate scissors (our A9 (c)) is invisible by construction.
3. **No moment-RATIO headline.** The double-factorial `!!` enhancement is present in the machinery (Eq. 32b)
   but the paper's framing is correlation-LENGTH scaling at fixed `p` and a fault-tolerance verdict — it does
   not isolate a correlated/uncorrelated LER *ratio* growing as `d!!` as its result (that explicit framing =
   Clader 2101.11631 / our A9 (a)).
4. **No non-Markovian / temporal-correlation QEC claim.** Temporal correlations are mentioned only as
   "QEC can tolerate certain forms" (intro, refs 11, 12); the analysis is a single dephasing window (spatial
   correlations only). (Temporal-structure QEC = Kam 2410.23779 / 2603.05474 in our notes.)
5. **Surface code only in the two LIMITS.** Intermediate (`0<N_c<∞`) surface-code LER is stated intractable;
   only uncorrelated + perfectly-correlated surface curves exist (repetition code carries the intermediate
   regime).

## Limitations [paper]
- **L1 — code-capacity, ideal extraction, `T₁=∞`** (the quoted core limitation); a spatial-dephasing-only,
  data-qubit-only, single-window model. Not circuit-level.
- **L2 — surface code: limits only.** Intermediate correlation lengths not computed for the surface code.
- **L3 — ensemble-average with `|⟨ϕ_iϕ_j⟩|`.** Because `⟨ϕ_iϕ_j⟩` can change sign, the ensemble average is
  strongly cancelled; they substitute the ensemble average of the ABSOLUTE value `|⟨ϕ_iϕ_j⟩|_TLF` as the
  effective QEC input (Methods, above Eq. 26) — a declared modeling choice ("more representative estimate"),
  not a first-principles identity. [twin-flag: this is exactly a `feedback-underdetermined-bracket-not-freeze`
  situation — a sign-ambiguous quantity replaced by a representative surrogate; the authors are explicit it's
  representative, not "the physical value".]
- **L4 — exponential fit is range-limited.** `e^{−x/l_c}` holds only in the experimentally accessible range;
  the model itself predicts a `x^{−4.2}` polynomial tail (Ext. Data A6), and a statistically significant
  remnant correlation beyond the TLF model appears at 3rd/4th neighbors (`4.89σ`, `8.20σ`; Ext. Data A10,
  `<7%` LER impact).
- **L5 — single device, one TLF-density fit parameter**; `ℏω₀=1.2 meV` tuned to match the measured auto-PSD.

## Relevance to the twin — the (a)-anchor for A9 ("closest physical setup") [twin]
1. **This is the `(a)` prior-art anchor cited verbatim in prereg A9** (`B_syndrome_shot_bridge_prereg.md`,
   lines 211–213): *"fixed-marginal spatial correlation degrading logical performance (Novais–Preskill
   1209.2157; Rojas-Arias 2603.03051 — closest physical setup: Si-spin rep code, correlation-length sweep at
   fixed p, but CODE-CAPACITY with ideal syndrome extraction)."* The full text CONFIRMS every clause: (i)
   Si-spin rep code (`⟦N,1,N⟧`, Eq. 16); (ii) correlation-length sweep (`N_c`, Fig. 5a); (iii) fixed `p=10⁻²`
   (Eq. 26, quoted); (iv) **code-capacity with ideal syndrome extraction** (the two verbatim limitation
   sentences above). ⇒ **A9's classification of this paper is exactly correct — no contradiction found.**
2. **Our differentiator, sharpened against this paper.** Rojas-Arias occupies the SPATIAL-correlation /
   fixed-marginal / fault-tolerance-verdict ground physically. Our contribution over it is precisely the
   axis it declares out of scope: **circuit-level noise WITH mid-circuit measurement + syndrome extraction**,
   the **syndrome-SILENT logical-flip run rate** (their model has no detectors at all), the **detection-rate
   DECREASE** at fixed marginal (their model produces no detection events), and the **moment-ratio (×15.9 /
   `d!!`) framed as a measured observable** (present in their Eq. 32b machinery but not isolated as a result).
   This is a clean, non-overlapping wedge — they cannot see any of our headline observables *by construction*
   (ideal extraction, `T₁=∞`, data-qubit-only, single window).
3. **Shared Gaussian-moment machinery = the (a) lineage is real.** Their Eqs. 20–25 use the same
   `⟨e^{iX}⟩=exp(−½⟨X²⟩)` and the same double-factorial expansion (Eq. 32b) as Clader 2101.11631 / our A9
   (a). So our ×15.9 is genuinely the SAME moment law these fixed-marginal correlated-noise papers exploit —
   A9's "cite, do not claim" verdict on the moment enhancement is confirmed by this independent read. Our
   novelty is the circuit-level *reframing onto the silent-run floor* + the *detection scissors*, not the
   moment law itself.
4. **`p=½(1−e^{−τ²/T₂*²})` cross-check (Eq. 26).** This is the same single-qubit dephasing→phase-flip map as
   Pataki 2401.04530 Eq. 12 (`p=½(1−e^{−2σ²})` with `σ=τ/T₂*`… up to the √2 convention of 2401.04530 Eq. 58):
   the two anchor papers agree on the marginal-calibration identity, which is our step-2 target. Convention
   carry: **2603.03051 uses `p=½(1−e^{−⟨ϕ²⟩/2})` with `⟨ϕ²⟩=τ²/T₂*²`; 2401.04530 uses `p=½(1−e^{−2σ²})` with
   `σ=√2 T_meas/T₂*`** — consistent once `⟨ϕ²⟩ = 2σ²` (i.e. their `σ` = SD of the half-angle vs full-angle
   differ by the factor-2 in the Ẑ-rotation exponent). Reconcile explicitly before quoting either alongside
   our χ.
5. **Hard-LER-floor lesson (Ext. Data A8).** A perfectly-correlated (global) source is a HARD LER floor that
   added uncorrelated noise cannot beat — a useful independent statement of why *common-mode* correlation is
   the dangerous regime, aligning with our common↔local interpolation `f` (A9 (c) iii): pushing toward the
   common-mode end is where the silent-flip rate and the LER floor both blow up.

## How to use / trust + open questions [twin]
- **Trust:** high for the measurement + the code-capacity QEC calculation (standard Stim+PyMatching MC for
  `F_n`; analytic rep-code; peer-review-grade cross-PSD Bayesian pipeline [ref 61]). The FT verdict is
  correctly hedged ("at the levels observed here", `T₁=∞`, ideal extraction) — do NOT over-read it as a
  circuit-level fault-tolerance claim. The `|⟨ϕ_iϕ_j⟩|` absolute-value substitution (L3) is a declared
  representative choice, not an identity — flag if we ever reuse their numbers as ground truth.
- **Independent-GT candidate:** their exact rep-code closed forms (Eqs. 19, 31, 32b) are a from-scratch
  reconstruction target for OUR fixed-marginal correlated sweep at the code-capacity level — a clean
  cross-check that our correlated-vs-uncorrelated moment scaling reproduces the `[2(n+k)−1]!!` law before we
  add the circuit-level machinery they omit.
- **Open for us:** (i) reconcile the σ/χ/`⟨ϕ²⟩` conventions across 2603.03051, 2401.04530, and our carrier
  before quoting a single calibration number (item 4). (ii) When we claim the detection-rate scissors as
  novel, this paper is the strongest "they didn't/couldn't see it" citation — because their model has no
  extraction circuit, not because they looked and found nothing. (iii) The `x^{−4.2}` screened tail vs
  `x^{−3}` unscreened (Ext. Data A6) is the physically-grounded long-range spatial-correlation profile to use
  IF we ever put a physical spatial-correlation kernel on our carrier's data qubits.
