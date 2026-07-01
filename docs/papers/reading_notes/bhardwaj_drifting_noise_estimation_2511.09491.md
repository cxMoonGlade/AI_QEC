# Full-text review — Bhardwaj, Takou, Lin & Brown, "Adaptive Estimation of Drifting Noise in Quantum Error Correction" (arXiv:2511.09491v1, 2025)

> **Provenance (2026-06-25): FULL-TEXT read (精读) of §I–IV (method + results + decoding, pp.1–14);
> §V discussion/§VI conclusion/refs skimmed.** PDF `outputs/papers/2511.09491.pdf` (9.64 MB, 20 pp) →
> `outputs/papers/2511.09491.txt` (fitz). All Eq/Fig/Table refs from that text. Tags: **[paper]** /
> **[twin]**. (Upgraded from the 2026-06-25 characterization note once ⑤b-drift entered WS2 scope.)

## Metadata [paper]
- Devansh Bhardwaj, Evangelia Takou, Yingjia Lin, Kenneth R. Brown (Duke Quantum Center). arXiv:2511.09491v1
  [quant-ph], 12 Nov 2025; 20 pp.
- Type: analytical framework + Stim simulation — estimate TIME-DEPENDENT (drifting) Pauli error rates from
  QEC SYNDROME history alone, build a time-dependent DEM, and decode adaptively under drift.

## Executive summary [paper]
Real noise DRIFTS (1/f <1 Hz from TLS/defects; 1/f²/Lorentzian 1 Hz–100 kHz from charge/flux; white >1 MHz);
conventional DEM estimation from the FULL syndrome history yields only the TIME-AVERAGE rate, losing the
drift → suboptimal decoding. The paper post-processes the SAME syndrome data with **time WINDOWS** to retain
the time-dependence, and proves the spectral behavior analytically. Three methods (sliding / iterative /
relative window); the estimated time-dependent DEM tracks ground truth and an **adaptive decoder using it
matches the ground-truth LER, while a STATIC (time-averaged) DEM decoder has significantly higher LER**.
No extra benchmarking, no ML.

## Static baseline — DEM rates from syndrome history (§II) [paper]
From detector expectations (⟨vi⟩ = single-detector fire rate; ⟨vivj⟩ = coincidence rate; over all shots):
- **bulk edge** `p_ij = 1/2 − sqrt( 1/4 − (⟨vivj⟩−⟨vi⟩⟨vj⟩) / (1−2(⟨vi⟩+⟨vj⟩)+4⟨vivj⟩) )` (Eq 1)
- **boundary edge** `p_ii = 1/2 + (⟨vi⟩−1/2)/∏_{j≠i}(1−2p_ij)` (Eq 2)
(the Spitz/Google syndrome-only estimator, valid for independent/Pauli DEMs). Full-history evaluation ⇒
time-average only.

## The three window methods (§III — the contribution) [paper]
- **Sliding window (size W):** apply Eq 1–2 within `[t_l−WΔt, t_l)`. Proven (App. A):
  `p_est_ij(t_l) = (1/W) Σ_{k=0}^{W−1} p_ij(t_l−WΔt+kΔt)` (Eq 3) = the **temporal average** over the window
  (holds for Markovian time-dependent noise). STD `σ_W = (1/W) sqrt(Σ_k p(1−p))` (Eq 4, binomial). DFT
  (Eq 5–7): `p_est(ω_m) = (1/W)·[sin(πmW/N)/sin(πm/N)]·e^{iπm(W−1)/N}·p(ω_m)` — a **Dirichlet-kernel
  LOW-PASS FILTER** (cutoff set by W) + a phase shift / time-lag. Optimal window for cutoff `ω_c=2πm_c/(NΔt)`,
  tolerance ϵ: `|sin(πm_cW/N)/sin(πm_c/N)| = 1−ϵ` (Eq 8) ⇒ `W_opt ≈ c(ϵ)N/m_c` (Eq 9), `c(0.05)≈0.12`.
  Larger W ⇒ less variance but more damping/lag (a trade-off; single-freq drift can be phase/magnitude-
  corrected via Eq 7).
- **Iterative sliding window (§III.B):** start large `W0~O(N)` (low freq), shrink `W_k` to resolve higher
  bands (least-squares for the Fourier coeffs `p_am,p_bm` per cutoff; threshold µ=1−ϵ∈[0.05,0.2]). Resolves
  MULTI-frequency drift; removes time-lag (relates to temporal averages).
- **Relative window (§III.C):** two overlapping windows W, W+1 ⇒ instantaneous
  `p_ij(t_l) = (W+1)p_est_{W+1}(t_l+Δt) − W·p_est_W(t_l)` (Eq 11; = scaled discrete derivative,
  Savitzky-Golay smoothed). SINGLE-PASS, captures rapid multi-freq drift without window tuning.

## The DRIFT MECHANISM (the teacher — §IV) [paper → twin]
Time-varying single-qubit depolarizing per cycle: `E(ρ)=(1−g(t))ρ + (g(t)/3)(XρX+YρY+ZρZ)` (Eq 12), with
`g(t) = g0 + Σ_{m∈M} g_m sin(ω_m t)` (Eq 13) — a sum of sinusoidal drift frequencies. Applied to BOTH data
AND ancilla qubits (and gates, circuit-level §IV.D, with INHOMOGENEOUS per-qubit/per-CNOT g0,g1,ω — Table I).
The drift is in the RATE `g(t)` over rounds; spectral content = single / multi-frequency (1/f-like). `ω_m=0`
recovers the static rate g0.

## Observable / validation (§IV.E, Figs 9–11) [paper]
- The estimated DEM rate `p_est(t)` tracks ground-truth `p(t)` (Figs 3–8; bulk/boundary/timelike/diagonal
  edges).
- **Relative logical error rate `Δ = ϵ_est_L/ϵ_stim_L − 1`** (Eq 15): the adaptive (estimated-DEM) decoder
  achieves `|Δ| ~ 1e-4–1e-3` vs the ground-truth-DEM decoder, ACROSS physical rates; the **STATIC DEM
  (g1=0, time-averaged) decoder has SIGNIFICANTLY HIGHER LER** (Figs 10–11). The optimal window minimizes
  `|Δ|` (Fig 9a: W=1250 ≈ W_opt=1228±42 from Eq 9). ⇒ the drift's decode-relevant signature = the STATIC-DEM
  LER PENALTY (the cost of assuming stationarity), recoverable from syndromes.

## Limitations [paper]
- Markovian time-dependent noise (the Eq 3 average proof assumes it); drift mostly low-frequency
  (`N/m_c > 1e3`); needs many cycles (W ~ 500–12000) for low variance; phase-lag for large W; the diagonal
  (gate) edge is hardest (multi-freq interference). Pauli/DEM-graph noise (independent events).

## Relevance to the twin — grounds WS2 ⑤b-DRIFT + the PREDICT/RECOVER axis [twin]
1. **The ⑤b-DRIFT teacher mechanism (carrier-implementable):** a per-round time-varying Pauli RATE
   `g(r) = g0 + Σ_m g_m sin(ω_m r)` (Eq 12–13) on data qutrits (and, circuit-level, per gate/effective
   ancilla). This is exactly the (premature) WS2 "round-dependent `(θ_r,γ_r)` schedule" — now GROUNDED as a
   sinusoidal multi-frequency rate drift. Implementable on the carrier via `round_pre(eng,r)` applying a
   channel whose rate depends on r. DISTINCT from ⑤b-correlation (Kam 2410.23779): drift = time-varying
   MARGINAL rate; correlation = structure AT FIXED marginals.
2. **The ⑤b-DRIFT observable (decode-relevant, literature-anchored):** NOT a 2-point round-to-round
   correlation. It is (a) the **static-DEM LER PENALTY** `Δ` (Eq 15) — a stationary-rate learner is
   misspecified, decoding worse than a drift-aware DEM — and (b) the **drift-recoverability** from syndromes
   (the window estimators track `p(t)`). For the validated-twin: the misspecification (Axis A) = a static
   learner's overconfident/wrong LER under drift; the PREDICT capability = recover `p(t)` (window estimation)
   + forecast.
3. **This is the field-grounded method for the twin's long-deferred PREDICT/drift axis.** The
   sliding/relative-window syndrome estimator (Eq 1–11) is a concrete RECOVER-under-drift tool to reuse +
   validate against a KNOWN-TRUTH drifting teacher (the twin's predict-axis validation — our unowned seam is
   the *validated-against-known-truth* band on the recovered `p(t)`, which this paper does not do: it shows
   tracking + LER, not a calibrated uncertainty band validated for coverage under drift).
4. **The DEM-from-syndromes estimator (Eq 1–2)** is the standard the twin's recover builds on; the window
   variants are the time-resolved extension. The static-vs-drift-DEM LER comparison (Δ) is the ⑤b-drift
   `B_misspec`-analogue (cf. the H2 crosstalk B_misspec).
5. **GT feasibility:** the drift teacher's time-varying rate is exactly recomputable (known g(t)), so the
   exact-DM record oracle / carrier can produce the drifting record + the static-vs-true LER — a clean
   known-truth validation, no new GT machinery beyond a round-indexed rate in `round_pre`.

## How to use / trust + open [twin]
- **Trust:** high (full method read; the spectral proofs + the Stim validation are self-contained). Carry
  the Markovian-drift assumption (Eq 3) + the low-frequency regime (`N/m>1e3`) as caveats.
- **Open for WS2 ⑤b-drift:** (i) the drift mechanism is a round-indexed rate g(r) on the carrier (simple);
  the observable is the static-DEM LER penalty + recoverability (NOT a 2-point correlation). (ii) The twin's
  NOVEL bit over Bhardwaj = a *validated uncertainty band* on the recovered g(t) under known-truth drift
  (coverage), not just tracking — fits the validated-twin's Axis-C/D. (iii) Reuse the sliding/relative-window
  estimator as the recover-under-drift method; validate vs the known drifting teacher.
