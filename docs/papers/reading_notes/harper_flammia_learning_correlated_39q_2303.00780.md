# Body-read — Harper & Flammia, "Learning correlated noise in a 39-qubit quantum processor" (arXiv:2303.00780v1; PRX Quantum 4, 040311 (2023))

> **Provenance.** Body-read by opus subagent 2026-07-02, targeted scope: **A9 adjudication** (what
> correlated structure was learned on real Google hardware; is the "correlated models matter for
> sub-threshold prediction" claim about decoder-prior accuracy or floor prediction; any quantitative
> "independent model underestimates by X×"; any silent/zero-syndrome channel). PDF downloaded
> `arxiv.org/pdf/2303.00780` (`outputs/papers/fetch_and_extract.py`, 5.86 MB, 22 pp incl. 9 appendices) →
> text `outputs/papers/2303.00780.txt` (fitz). Full body + all appendices A–I read; figure Hinton diagrams
> not pixel-extracted (the per-qubit error rates + Table I + Fig 5 LER numbers are in the running text /
> captions, captured here). **Pending principal spot-verification.** Tags: **[paper]** = stated in the
> paper; **[ours]** = our inference for `qec_twin`, NOT the paper's claim.

## Metadata [paper]
- **Authors / affiliation.** Robin Harper (Univ. Sydney, EQUS), Steven T. Flammia (AWS CQC / IQIM Caltech;
  contribution while at Univ. Sydney).
- **Venue / status.** arXiv:2303.00780v1 [quant-ph], 1 Mar 2023 → PRX Quantum 4, 040311 (2023).
- **Type.** **Real-hardware noise-learning experiment.** 39 of 54 qubits of Google's **Sycamore** (the
  [ref 58] Arute-2019 device), running **surface-code syndrome-extraction ("stabilizer preparation")
  circuits WITHOUT mid-circuit measurement/reset**, learning the **locally-averaged Pauli noise** on the 20
  data qubits as a **graphical (Ising/graphical-model) description** via the LACE / Flammia-Wallman-Harper
  eigenvalue-sampling method [refs 47,48]. Decoding via a generic tensor-network decoder (QECSIM, bond
  dim χ=8).

## Executive summary [paper]
Learns a **globally consistent Pauli noise model** on real Sycamore data to ±0.1% relative error on all
1- and 2-qubit rates, fits four nested graphical models of increasing power (IID → IND → Ising → CG1D →
full "Global"), and asks whether the correlation structure matters for predicting logical performance. Key
finding, verbatim from the abstract: **"accurate correlated noise models are increasingly important for
successfully predicting sub-threshold behavior."** The quantitative core (§V, Fig 5): at the device's own
noise (avg per-qubit physical rate 0.136) all models agree; but as one extrapolates to LOWER (sub-threshold)
noise, the simple (uncorrelated) models **under-predict** the logical error rate relative to the correlated
/ full distribution by roughly **2×** at avg physical rate 0.031.

## What correlated structure was learned — size & type (§III, Fig 3, Table I) [paper]
- **Precision:** "a bootstrap analysis (at the 2σ level) shows a maximum relative error of ±0.1% on both
  single-qubit error and two-qubit error rates." [paper, §I]
- **Per-qubit rates (Fig 3, verbatim table):** one-round data-qubit error probabilities span **0.075 →
  0.230** (e.g. qubit (5,1)=0.230, (5,3)=0.215, (4,2)=0.197, (5,5)=0.182, (4,4)=0.168 at the high end;
  (3,3)=0.075, (3,7)? … (1,5)=0.080 at the low end). Avg single-qubit error rate **0.136 ± 0.001** [§I].
- **Two-body correlation structure (Fig 3, Hinton; ρ defined Eq 1 = Pearson of per-qubit error indicators):**
  "there are correlated errors in the device which mostly cluster locally, although **some significant
  longer-range correlations are present.**" "the correlations between data qubits appear (mainly) to be
  stronger with local data qubits (i.e. those close in Manhattan distance according to the device
  connections)." [paper, §III + Fig 3 caption] **No single scalar correlation length is stated**; the
  structure is reported as a Hinton diagram, quantified downstream by the covariance-matrix norm (Table I).
- **Model-error ladder (Table I, verbatim), model vs learned Global distribution `D`:**
  | Model | JSD(D‖M) | ‖Σ_D − Σ_M‖ |
  |---|---|---|
  | IID  | 0.229 | 0.124 |
  | IND  | 0.192 | 0.090 |
  | Ising | 0.167 | 0.056 |
  | CG1D | 0.148 | 0.019 |
  Richer model ⇒ smaller model error (both JSD and covariance-norm). Ising factor graph has **31 factors →
  124 parameters**; CG1D has 4 factors of 2⁸ → **1024 parameters** (only model with exponential-in-width
  scaling). Appendix H confirms (via conditional entropy) the **physical-location Ising ansatz is
  near-optimal** — best alternative blankets differ by ≤ one qubit and <0.5% CE.
- **Attributed cause (tentative):** "it is possible that the long range two-body correlations … and the
  multi-qubit errors … are symptoms of the **leakage errors** in such Sycamore devices" [§III, citing
  Miao et al. ref 59]. Also "energy state leakage, leakage of control signals and qubit frequency crowding"
  as Ising-model-breaking mechanisms [§IV].

## The exact "sub-threshold" claim: decoder-prior accuracy vs floor prediction? [paper]
**The claim is about PREDICTING the logical failure RATE (performance forecasting), NOT about a decoding
prior and NOT about a floor.** Precisely:
- The pipeline (§V, Fig 5): construct **counterfactual lower-noise channels** that RETAIN the correlation
  structure via a continuous-time interpolation `p(t)=W⁻¹ exp(t log(Wp))` (Eq 3–4, W=Walsh-Hadamard),
  `t<1` = less noisy, then fit each graphical model to each counterfactual and decode with a **GENERIC**
  (correlation-agnostic) tensor-network decoder. Crucially: **"by using a generic decoder, we are not
  attempting to utilise our knowledge of the noise to improve the decoding process … this is not what we do
  here — rather the analysis below might be seen as setting out the base success rate."** [§V, verbatim]
  So the models differ only as **inputs (sampled error distributions)**, decoded identically ⇒ the finding
  is about **whether a simpler model of the same device predicts the right LER**, i.e. *forecasting
  fidelity*, NOT prior-informed decoding gain (which they explicitly defer: "Writing such decoders is the
  subject of on-going work").
- **NOT a floor.** No error-floor / plateau / rare-event-tail claim anywhere; the object is the LER along a
  noise-strength sweep and its pseudo-threshold. (Interestingly, "the simplest models … through to the most
  complex models all gave approximately the same pseudo-threshold (physical = logical ≈ 0.1)"; the
  divergence is BELOW threshold, in the *predicted* LER, not at a floor.)

## The quantitative "independent model underestimates by X×" [paper]
**YES — a factor of ~2× (roughly a factor of two), stated as absolute LER pairs, not as a named
"underestimate factor".** Verbatim (§I and Fig 5):
- "with an average physical error rate of 0.031, the simpler models predicted logical error rates of
  **0.006 ± 0.001**, whereas the logical error rate from the extrapolated global probability distribution
  was **over twice as much (0.0121 ± 0.002)**. In this regime, models that capture correlated errors, such
  as an Ising model, gave logical error rates commensurate with or higher than the global distribution
  **0.014 − 0.018**." [§I, verbatim]
- Fig 5 table (LER at avg physical error 0.031): **IDD 0.0066, IND 0.0068, Global 0.0127, CG1D 0.0156,
  Ising 0.0191.** So IID under-predicts the Global by **0.0127/0.0066 ≈ 1.9×**; the Ising model is
  *pessimistic* (over-predicts) — the paper attributes this to Ising folding long-range correlations into
  too-strong short-range ones (§V).
- Framing sentence: "models that fail to take into account correlated errors … can potentially
  **underestimate expected logical failure rates by a significant fraction.**" [§I]

So the answer to A9's decision question: the claim is **predicting sub-threshold LER**; the quantitative
statement is **~2× underestimate by the uncorrelated model at physical rate 0.031** (absolute pairs
0.0066 vs 0.0127). It is a *performance-forecasting* claim, decoder held generic.

## Silent / zero-syndrome channel discussion? [paper]
**NO explicit silent-flip / zero-syndrome / trivial-syndrome-logical-error discussion.** The paper never
isolates a syndrome-invisible logical-flip rate. Nearest-adjacent content, all of which is about
*characterization*, not a silent channel:
- The experiment **omits mid-circuit measurement & reset** and works on a **code-capacity** basis (§V), so
  the syndrome/detection-event layer is not modeled at all — there is no detection-event-rate object and
  hence no "quieter-syndrome" observable. This is a **structural gap** relative to our v2b circuit-level,
  mid-circuit-measurement observable — the paper is data-qubit-Pauli-distribution only.
- "the probability distribution will have 2ⁿ elements"; unobserved bit patterns "are 0 in the empirical
  probability distribution" (Appendix C) — a sampling remark, not a silent-channel claim.
- Appendix I explicitly disclaims physicality of the counterfactual channels ("not to generate channels
  that represented something achievable in the device, but rather to 'construct' counterfactual theoretical
  channels … retain all the 'interesting' features and correlations"). High-weight (≥3) errors "are still
  prevalent even on the least noisy maps" (Fig 10b) — the closest thing to a persistent-tail remark, but
  about error WEIGHT, not syndrome-invisibility.

## A9 verdict [ours]
**SUPPORTS keeping our component out of (a); this paper is the empirical GROUNDING for the RELEVANCE of
correlated models on real Google hardware, but it does NOT own our specific observable.** Specifically:
1. It **grounds "correlated models matter"** with a real-device ~2× under-prediction — the strongest
   empirical citation available for *why* the twin should carry correlation. Use it as the motivating
   real-hardware anchor.
2. But its object is **data-qubit Pauli-distribution LER forecasting**, code-capacity, generic decoder — it
   has **no detection-event rate, no fixed-marginal correlated-vs-independent decode-cost, no silent/
   zero-syndrome logical-flip rate**, and no common-mode/Gaussian dephasing model. So it does **not**
   pre-empt A9's apparently-novel (c) items — the detection-event-rate DECREASE at fixed marginals, the
   syndrome-silent-run floor as an observable, or the common↔local `f` interpolation.
3. Net: this paper belongs in A9 as **motivating prior art for "correlated noise degrades/mispredicts
   logical performance on real Google" (a general (b)-style framing citation with a hard ~2× number)** — it
   does **not** compress the silent-flip-rate or detection-drop components to (a). Our (c) items survive.

## Decisive verbatim quotes [paper]
- **Sub-threshold / correlated-models claim (abstract):** "By extrapolating our experimentally learned
  noise models towards lower error rates, we demonstrate that accurate correlated noise models are
  increasingly important for successfully predicting sub-threshold behavior in quantum error correction
  experiments."
- **The ~2× quantitative underestimate:** "with an average physical error rate of 0.031, the simpler models
  predicted logical error rates of 0.006 ± 0.001, whereas the logical error rate from the extrapolated
  global probability distribution, was over twice as much (0.0121 ± 0.002)." (§I)
- **Underestimate framing:** "models that fail to take into account correlated errors (such as those caused
  by crosstalk) can potentially underestimate expected logical failure rates by a significant fraction."
  (§I)
- **It is forecasting, NOT prior-informed decoding:** "by using a generic decoder, we are not attempting to
  utilise our knowledge of the noise to improve the decoding process … rather the analysis below might be
  seen as setting out the base success rate, which such decoders might seek to improve on." (§V)
- **Precision of the learned model:** "a bootstrap analysis (at the 2σ level) shows a maximum relative error
  of ±0.1% on both single-qubit error and two-qubit error rates." (§I)
- **Correlation structure (size/type):** "there are correlated errors in the device which mostly cluster
  locally, although some significant longer-range correlations are present." (§III) / "the correlations
  between data qubits appear (mainly) to be stronger with local data qubits (i.e. those close in Manhattan
  distance…)." (Fig 3 caption)
- **Leakage as tentative cause:** "it is possible that the long range two-body correlations … and the
  multi-qubit errors … are symptoms of the leakage errors in such Sycamore devices." (§III)
- **No mid-circuit measurement (structural gap):** "we run the circuits required for non-demolition
  four-body stabilizer measurements of the data qubits, but without actually performing the ancilla
  measurements or the resets required in a real error correction experiment." (§II)

## Limitations [paper]
- **L1.** No mid-circuit measurement/reset ⇒ **no detection-event / detector layer**; code-capacity LER
  only. (Authors flag it: numbers "must be regarded with this caveat in mind.")
- **L2.** Generic (correlation-agnostic) decoder throughout — the paper measures *forecasting* value of
  correlation, not decoding gain (deferred to future work).
- **L3.** Counterfactual lower-noise channels are **non-physical constructions** (continuous-time
  Walsh interpolation + simplex projection), explicitly disclaimed as not device-achievable (Appendix I).
- **L4.** Correlation structure reported as Hinton diagrams + covariance-norm; **no scalar correlation
  length**, cause (leakage/crowding) only tentatively attributed. Ising model is a good fit but *pessimistic*
  for LER because it cannot hold long-range correlations (§V).
- **L5.** Single device, single 8-hour slot, ~60 h post-calibration; drift uncompensated (Appendix B).
