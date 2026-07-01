## Provenance

- **Source:** arXiv:2605.17156, fetched 2026-06-30
- **Reading method:** FULL-TEXT read (精读) via arXiv HTML — all sections, equations, and appendices
- **Status:** complete full-text close-read

# Deep review — Sayedsalehi, Bagherzadeh, Shcherbakov & Gaudiot, Sparse Mamba Decoder for Quantum Error Correction

> **Digest-tier note.** Built 2026-06-14 from a sub-agent digest of the arXiv HTML (v2);
> numbers marked *digest* — re-check the PDF before citation. Part of the 2026-06-14
> external-landscape cluster (hub: `2026-06-14_coherent_noise_and_neural_decoders.md`).
> **Relevance to the twin** centerpiece.

## Metadata
- **Authors.** Samira Sayedsalehi, Nader Bagherzadeh, Maxim Shcherbakov, Jean-Luc Gaudiot (UC Irvine).
- **Venue / status.** arXiv:2605.17156, v1 2026-05-16 / v2 2026-05-20; submitted to *Quantum*.
- **Domain / type.** QEC decoding; **machine-learning decoder** (Mamba state-space model); surface code on depolarizing / circuit-level / SI1000 / Sycamore.

## Executive summary
At realistic error rates **<5% of syndrome entries are active**, yet
MWPM / Tesseract / Belief-Matching / dense Mamba all process the full `d²×R` array.
The **Sparse Mamba Decoder (SMD)** recasts the syndrome as a variable-length **list of
active-defect tuples** (each a **13-dim feature**: spatial x/y, temporal index, X/Z
stabilizer type, neighbor flags, boundary distances, cumulative-XOR-reconstructed
measurement bit) and runs a **Mamba SSM** → **O(k)** in the number of active defects
`k`. Trained in three regimes: Stim synthetic (AdamW), SI1000 curriculum (Lion+EMA),
then 50k real Sycamore shots fine-tune. The DEM is used **purely as a pretraining data
generator**.

> Headline (*digest*): **40–91% LER improvement** over MWPM/Tesseract/Belief-Matching
> on depolarizing (`d=3–11`); **12–53%** on uniform circuit-level (`d=3–7`); SI1000
> LER ratio **0.65 (d3) / 0.51 (d5)**; Sycamore ensemble `d3 2.94e-2 / d5 3.00e-2`
> (≈ dense Mamba); latency **2.4×** from `d3→d9` (24–57 µs on RTX 4090), **95–467×**
> faster than Tesseract, **232–463×** than Belief-Matching; 7.5–16M params.

For the twin this is a **competitive neural-decoder baseline on the same Sycamore
family**, whose XEB→DEM→Stim pretraining uses exactly the independent-edges DEM that
M4 showed is lossy — and which never questions DEM fidelity. It **optimizes the decoder
given the DEM**; we **calibrate the noise model**. Orthogonal → clean citation, and a
precedent for plan3 **Component B** (neural amortization).

## Contributions (claim → evidence → strength)
- **C1. Defect-centric sparsification (13-dim tuples) → O(k) decoding.** *Strength: strong (the right structural insight).*
- **C2. Mamba SSM backbone exploiting YY-correlation** (joint λZ/λX prediction). *Strength: strong.*
- **C3. Three-regime training incl. Sycamore fine-tune; matches dense Mamba on hardware.** *Strength: medium-strong (digest).*
- **C4. Large latency win vs Tesseract/Belief-Matching at comparable/better accuracy.** *Strength: strong.*

## Method (deep) (*digest*)
- **Sparsification.** Active detectors → `k` tuples (13-dim each); sequence length `k ≪ d²R`.
- **Selective SSM (Mamba).** `h_t = Ā h_{t−1} + B̄ x_t, y_t = C h_t` with input-dependent `(A,B,C,Δ)`; `O(k)` recurrence vs attention `O(L²)`.
- **Training.** Stim depolarizing/circuit-level (AdamW+cosine) → SI1000 3-stage curriculum (Lion+EMA) → 50k Sycamore shots fine-tune. DEM = pretraining oracle.

## Methodology assessment (digest-tier)
| Criterion | 1–5 | Assessment |
|---|---|---|
| Soundness | **4** | Standard ML-decoder methodology; verify train/test split in PDF. |
| Novelty | **4** | Sparsification + SSM for QEC decoding is a fresh, sensible combination. |
| Reproducibility | **3?** | Verify code/data release. |
| Experimental design | **4** | Multiple noise regimes + real hardware + several baselines. |
| Statistical rigor | **3–4** | Verify ensemble/CI reporting in PDF. |
| Scalability | **5** | O(k); gentle latency growth (2.4× d3→d9). |

## Strengths
- **S1 — sparsity-exploiting O(k) decoding** is the right structural insight (<5% active).
- **S2 — Mamba/SSM** gives near-linear sequence modeling with YY-correlation capture.
- **S3 — large latency advantage** with matched/better accuracy on real Sycamore.

## Weaknesses / limitations
- **W1 — noise is a black box**; the DEM is only a scaffold; no noise-model calibration / posterior / uncertainty.
- **W2 — Pauli / depolarizing only; no coherence.**
- **W3 — static** (each config i.i.d.); no drift; Sycamore (not Willow/105q).

## Relevance to the twin
1. **Decoder-accuracy foil on shared data.** The same XEB→DEM→Stim pretraining uses the **independent-edges DEM** M4 (`metric_results.md` ~:1711) showed decodes worse; SMD never questions DEM fidelity. They optimize the decoder *given* the DEM; we calibrate/question the noise model (`recover`). Orthogonal → clean citation: they set the **decoder-accuracy frontier**; we deliver a **calibration-quality (NLL)** result that the accuracy metric does not surface (M3 +56/+44 nats).
2. **Component B precedent (plan3 1+1).** The Mamba/SSM amortization over syndrome structure is a direct precedent for the **black-box GNN fusion-merger** (`docs/plan3.md`; `docs/cf_wr/window_covering_architecture.md`) — neural amortization that carries calibrated bands rather than an exactness class.
3. **The metric gap is our pitch.** SMD reports LER ratios; it cannot show the likelihood/coherent-slot result — exactly the "the accuracy metric doesn't surface our win" framing (plan3 scoop-resistance argument).
4. **Drift axis unoccupied.** Treats each config as i.i.d. — our drift/`predict` headline (battlefield verdict 2026-06-13) is unpre-empted; but **M5 is unbuilt** (no `metric_results.md` M5 block / no `test_hardware_m5`).
5. **Baseline pool.** With paper 4 (`scalable_neural_decoder_realtime_2510.22724`) + dMLE (`qec_differentiable_mle_noise_2602.19722`), part of the comprehensive decoder / noise-estimation baseline pool (baseline discipline) any decode-side claim must run against.

## How to use / trust + open questions
- **Trust:** medium (digest, preprint); re-check numbers + architecture in the PDF.
- **Open questions:** (i) is SMD a baseline we must beat, or orthogonal (we don't claim decoder accuracy)? Likely orthogonal — cite, don't compete. (ii) borrow the 13-dim defect featurization for Component B input encoding. (iii) note their dense-Mamba parity on Sycamore as the accuracy ceiling our NLL story sidesteps.
