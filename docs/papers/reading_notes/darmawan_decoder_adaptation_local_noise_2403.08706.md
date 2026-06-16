# Deep review — Darmawan, Optimal Adaptation of Surface-Code Decoders to Local Noise

> **Digest-tier note.** Built 2026-06-14 from a sub-agent digest of the arXiv/PRA HTML
> (not an independent full read); specific numbers marked *digest* — re-check the PDF
> before citation. The paper is **PRA-published (peer-reviewed)**, so the science is
> reliable; the residual risk is digest transcription, not validity. Part of the
> 2026-06-14 external-landscape cluster (hub:
> `2026-06-14_coherent_noise_and_neural_decoders.md`). **Relevance to the twin** centerpiece.

## Metadata
- **Author.** Andrew S. Darmawan (YITP, Kyoto).
- **Venue / status.** Phys. Rev. A **112, 042431** (2025-10-23); arXiv:2403.08706 (submitted 2024-03-13); YITP-24-28.
- **Domain / type.** QEC decoding; **simulation** + near-optimal tensor-network decoding; surface code under local noise.

## Executive summary
Given a characterized device, **how much does adapting the decoder to each noise
feature buy, and which features matter most?** Method: a near-optimal **tensor-network
(PEPS / TEBD)** decoder as an *oracle* for the maximum achievable benefit, plus
**selective mischaracterization** (hold physical noise `N`, feed the decoder a
one-parameter-perturbed `N′`, read the LER degradation) to rank feature importance.
Three noise families: coherent (rotations, CNOT timing), spatially inhomogeneous
amplitude-phase damping (per-qubit T1/T2), biased.

> Logical channel via the Pauli transfer matrix (*digest*, §II.3.2):
> `C_ij = Tr( L_i ( R_s ∘ N(L_j) ) )`, contracted via TEBD over a PEPS; recovery
> minimizes the diamond-norm distance to the identity logical.

Headline results (*digest*): adapting to **T1/T2 spatial inhomogeneity** is worth
>2× in qubits (`d≈35` optimal vs `d≈52` uniform for LER `1e-10`); for **coherence**
at `d=9`, optimal / Pauli-adapted / MWPM LER = `0.17 / 0.20 / 0.28` (θ=0.2π),
shrinking to a **~5% optimal-vs-Pauli gap at θ=0.125π**; broad conclusion — **only a
few critical parameters** need adapting, and the method names them.

For the twin this is **the closest published anchor to M4** and the calibration of
expectations: for *uncorrelated* coherent noise a Pauli-adapted decoder is
near-optimal, so our hardware's ~40% Pauli-DEM penalty must come from the
correlation/bunching that breaks locality.

## Contributions (claim → evidence → strength)
- **C1. Near-optimal PEPS/TEBD decoder as an oracle** + diamond-norm recovery selection. *Strength: strong.*
- **C2. Selective mischaracterization as a feature-importance probe** (one-parameter ablation of the decoder's prior). *Strength: strong — clean and reusable.*
- **C3. T1/T2 spatial inhomogeneity is the dominant adaptable feature** (>2× qubit saving). *Strength: strong (digest numbers).*
- **C4. Coherence: Pauli-adapted ≈ optimal at small θ (~5%)**, gap widens with θ; MWPM lags both. *Strength: strong.*
- **C5. "Few critical parameters" thesis** — near-optimal decoding needs only a small adapted subset, identified per family (coherence → Pauli-component strength; inhomogeneity → per-qubit T1/T2 ratio). *Strength: strong.*

## Method (deep) (*digest*)
- **PTM logical channel.** `C_ij = Tr( L_i ( R_s ∘ N(L_j) ) )`; TEBD contraction over a PEPS; recovery = `argmin` diamond-norm to the identity logical (near-optimal / coset-ML style).
- **Selective mischaracterization.** Fix `N`, vary the decoder's `N′` one parameter at a time; `ΔLER` = that parameter's importance.
- **Noise families + scale.** Coherent (rotations, CNOT timing), inhomogeneous amp-phase damping (per-qubit T1/T2), biased; `d=3` circuit-level, `d=9` noiseless syndrome (*digest*).

## Methodology assessment (digest-tier; PRA-reviewed)
| Criterion | 1–5 | Assessment |
|---|---|---|
| Soundness | **5** | Near-optimal TN decoder + diamond-norm; PRA-reviewed. |
| Novelty | **4** | Selective mischaracterization + "few critical parameters" is a clean, quotable framing. |
| Reproducibility | **4** | TN decoding is standard; method well-specified (verify in PDF). |
| Experimental design | **4** | Three noise families; oracle vs Pauli-adapted vs MWPM. |
| Statistical rigor | **4** | Threshold/overhead estimates; verify error bars in PDF. |
| Scalability | **3** | TN oracle decoder is not real-time; `d=9` noiseless syndrome is small. |

## Strengths
- **S1 — the oracle framing** (near-optimal TN decoder) cleanly separates "value of adapting" from "decoder limitation."
- **S2 — selective mischaracterization** is a directly reusable ablation tool for "which noise DOF is worth characterizing."
- **S3 — "few critical parameters" + naming them** (Pauli-component for coherence; T1/T2 ratio for inhomogeneity) is an actionable identifiability statement.

## Weaknesses / limitations
- **W1 — local single-qubit noise only — no correlation / crosstalk / bunching.** The crucial boundary for us.
- **W2 — TN oracle decoder is not real-time**; small distances.
- **W3 — noise assumed known** (not learned); static (no drift); simulation only.

## Relevance to the twin
1. **The closest published anchor to M4, and the reconciliation.** Darmawan: uncorrelated coherent noise → Pauli-adapted decoder near-optimal (~5% gap, C4). Our M4 (`metric_results.md` ~:1711): the independent-edges (Pauli-structured) DEM decodes ~40% worse on real hardware. **Reconciliation:** real hardware has bunching (R̂ up to 17.7; M3) that breaks his locality assumption (W1) — so his near-optimal-Pauli is the best case our correlated hardware falls through. This **sharpens the Paper-1 claim**: the failure is the correlation structure, not coherence magnitude in isolation.
2. **Selective mischaracterization = the M3↔M4 bridge + an N1/N2 arm.** It directly ranks which DOFs move LER — the missing link between the M3 syndrome-NLL win and the M4 decode loss, and a ready control arm for the carrier **N1 (format ceiling) / N2 (calibration tax)** controlled sim (`docs/_archive/PAPER1_STRATEGY.md`).
3. **understand / manipulate.** "Few critical parameters" is the decode-side twin of the project's identifiability / probe-richness story (ADR 0005/0006): only a few channel DOFs are LER-relevant; the `do()`→ΔLER axis should target those.
4. **Metric.** The diamond-norm logical-channel construction (PTM + TEBD) is a precedent for scoring the **lossy Pauli/DEM export** in plan3 (`docs/cf_wr/window_covering_architecture.md`: "the Pauli export residual is itself a reportable result") and aligns with the project's Bravyi-`P_L` / diamond-norm metric lineage (`correcting_coherent_errors_surface_1710.02270`).
5. **Decoder substrate.** The frozen-decoder ΔLER scoring (`decoder/` frozen MWPM/pymatching) is what M4 used; Darmawan's oracle shows the **headroom above MWPM** — how much the twin *could* deliver if the format carried the right DOF.

## How to use / trust + open questions
- **Trust:** high (PRA); re-check the digit-level numbers in the PDF.
- **Open questions:** (i) implement selective mischaracterization on our window twin to rank DOFs and bridge M3↔M4; (ii) does the small-θ "Pauli near-optimal" crossover place our XZZX hardware in the regime where the independent-edges DEM should have sufficed — making bunching the *sole* culprit?; (iii) use his T1/T2-ratio result to motivate the drift axis (per-qubit coherence drift = the inhomogeneity he adapts to, now time-varying = our `predict` headline).
