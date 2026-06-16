# Deep review — Lee, Hur & Park, Scalable Neural Decoders for Practical Real-Time Quantum Error Correction

> **Digest-tier note.** Built 2026-06-14 from a sub-agent digest of the arXiv HTML (v1);
> numbers marked *digest* — re-check the PDF before citation. Part of the 2026-06-14
> external-landscape cluster (hub: `2026-06-14_coherent_noise_and_neural_decoders.md`).
> **Relevance to the twin** centerpiece.

## Metadata
- **Authors.** Changwon Lee, Tak Hur, Daniel K. Park (Yonsei, Dept. of Statistics & Data Science).
- **Venue / status.** arXiv:2510.22724, v1 2025-10-26; preprint.
- **Domain / type.** QEC decoding; **machine-learning decoder** (Mamba SSM); real-time / latency-aware; Sycamore `d3/d5`.

## Executive summary
Transformer decoders (AlphaQubit) are accurate but scale **O(d⁴)**, and the resulting
latency **itself induces physical noise** during live operation. The paper proposes a
**Mamba SSM decoder at O(d²)** as a drop-in, and folds **latency-induced noise** into
the threshold. Pipeline: XEB→DEM→Stim (**100M-sample** pretraining) + 50k real-shot
fine-tune; curriculum over cycle lengths; Lion+cosine+EMA. Baselines: MWPM, TN
decoders, matched Transformer.

> Headline (*digest*): Sycamore `d3 ≈2.98e-2 / d5 ≈3.03e-2` (≈ Transformer accuracy);
> once decoder latency is counted, **Mamba threshold 0.0104 vs Transformer 0.0097
> (+7%, widening with d)**; `O(d²)` inference.

For the twin this is **near-duplicate positioning to paper 3** (Mamba × Sycamore ×
XEB→DEM), establishing the **efficient SOTA-matching decoder frontier**; the same
orthogonal wedge applies (they perfect the decoder; we calibrate the noise model;
neither touches drift/coherence), and the **latency→effective-threshold** accounting is
a clean honest-end-to-end pattern echoing M4's rearguard decode-cost accounting.

## Contributions (claim → evidence → strength)
- **C1. Mamba O(d²) decoder matching Transformer accuracy on Sycamore.** *Strength: strong (digest).*
- **C2. Latency-induced-noise accounting → effective threshold** (Mamba 0.0104 > Transformer 0.0097). *Strength: strong — the honest framing.*
- **C3. Scalable training (100M synthetic + curriculum) pipeline.** *Strength: medium.*

## Method (deep) (*digest*)
- **Complexity.** Mamba `O(d²)` vs Transformer `O(d⁴)` inference.
- **Latency in the error budget.** Decoder-induced latency → effective threshold (latency is itself a noise source live).
- **Pipeline.** XEB→DEM→Stim (100M) pretraining + 50k real fine-tune; curriculum over cycle lengths; Lion+cosine+EMA.

## Methodology assessment (digest-tier)
| Criterion | 1–5 | Assessment |
|---|---|---|
| Soundness | **4** | Standard ML-decoder + a sensible latency-aware threshold; verify in PDF. |
| Novelty | **3** | Mamba-for-decoding overlaps paper 3; the **latency→threshold** framing is the fresh bit. |
| Reproducibility | **3?** | Verify code/data release. |
| Experimental design | **4** | Sycamore + several baselines incl. matched Transformer. |
| Statistical rigor | **3–4** | Verify CI on the threshold gap. |
| Scalability | **5** | O(d²); the headline. |

## Strengths
- **S1 — latency-as-noise → effective threshold** is the right end-to-end honesty.
- **S2 — O(d²) with matched accuracy** is a real practical contribution.
- **S3 — large-scale pretraining + curriculum** is solid engineering.

## Weaknesses / limitations
- **W1 — Pauli-only, static**; DEM as oracle, not learned/calibrated; no uncertainty.
- **W2 — no coherence, no drift.**
- **W3 — Sycamore `d3/d5` only**; near-duplicate of paper 3's Mamba positioning.

## Relevance to the twin
1. **Real-time decoder baseline (with paper 3).** Establishes the efficient SOTA-matching frontier on shared Sycamore data; same XEB→DEM oracle (the independent-edges DEM M4 found lossy). Orthogonal to our `recover`/calibration claim — **cite as baseline, don't compete on accuracy.**
2. **Honest end-to-end accounting pattern.** "Latency-induced noise → effective threshold" is methodologically the same move as our M4 rearguard "honest decode-side cost accounting" (`docs/_archive/PAPER1_STRATEGY.md` demotes the decode end from headline to rearguard) — a citable precedent for accounting for the *full* cost, not just the headline metric.
3. **Component B precedent.** Same Mamba/SSM amortization argument as paper 3 for the GNN fusion-merger (`docs/plan3.md`).
4. **Drift unoccupied; coherent slot absent.** Reinforces both differentiation axes (`predict`/drift; coherent-capable channel object).
5. **Baseline pool.** Part of the comprehensive decoder baseline pool with paper 3 (`sparse_mamba_decoder_2605.17156`) + dMLE (`qec_differentiable_mle_noise_2602.19722`).

## How to use / trust + open questions
- **Trust:** medium (digest, preprint); verify numbers/complexity claims in the PDF.
- **Open questions:** (i) treat papers 3 & 4 as one "Mamba-on-Sycamore" citation cluster; (ii) adopt the latency→effective-threshold framing for our decode-cost honesty; (iii) confirm whether their O(d²) claim includes the fine-tuning data cost (50k shots/config) — relevant if we ever compare data efficiency.
