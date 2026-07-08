# Full-text review — Google Quantum AI and Collaborators, "Quantum error correction below the surface code threshold" (arXiv:2408.13687)

> **Provenance (2026-07-01): FULL-TEXT read (精读).** PDF `outputs/papers/2408.13687.pdf`
> -> txt `outputs/papers/2408.13687.txt` (PyMuPDF, 27 pp). This note complements the earlier focused leakage
> note `willow_qec_below_threshold_2408.13687.md`; here the load-bearing sections are the coherence/lifetime
> facts, the surface-code error budget, and the rare-burst discussion used by
> `docs/twin_validation/error_budget_sourced_table.md`. Figures were not pixel-extracted.

## Metadata [paper]
- Authors / affiliation: Google Quantum AI and Collaborators.
- Venue / status: arXiv:2408.13687, dated August 27, 2024 in the cached text; later Google/Willow-era
  surface-code result.
- Type: superconducting surface-code experiment, repetition-code ultra-low-error probe, real-time decoding,
  and simulation-based error-budget attribution.

## Executive summary [paper]
The paper reports below-threshold surface-code memories, with distance-7 logical performance below distance-5
and a neural-decoder suppression factor `Lambda = 2.14 +/- 0.02` in the main result (`txt:10-19`). It also
reports a logical memory lifetime of 291 +/- 6 us, exceeding the best physical-qubit lifetime of 119 +/- 13 us
by a factor of 2.4 +/- 0.3 (`txt:176-209`). For the simulator budget table, the essential data are Table S4's
component decomposition of `(Lambda_3/5)^-1`, the statement that correlated errors are estimated at about 17%
of the budget, and the observation of rare correlated detection bursts.

## Method (deep) [paper]
The supplementary error-budget method again uses

```text
(Lambda_3/5)^-1 = sum_i w_i p_expt^(i)
```

with component probabilities multiplied by sensitivities (`txt:1964-1988`). The paper states that CZ-related
rows dominate the budget, data idle contributes about 20%, readout plus reset about 12%, and SQ about 9%.
The sensitivities for Table S4 assume perfect DQLR and a correlated matching decoder (`txt:1964-1988`). The
same section reports that the Eq. (5) budget predicts `Lambda_3/5 = 2.25`, while direct simulation gives
`Lambda_3/5 = 2.17`.

## The MECHANISM (for implementation) [paper -> ours]
The simulation error model is a dressed circuit with channels for decoherence, passive heating, readout/reset,
CZ-induced leakage, stray-coupling crosstalk, and excess SQ/CZ/idle error (`txt:1668-1705`) [paper]. The main
text names correlated ZZ and swap-like errors from unwanted interactions during CZ as correlated-error
mechanisms (`txt:270-295`) [paper].

[ours] For the composed simulator table, the Table S4 local CZ/SQ/readout/reset rows can serve as the
Markovian background, the data-idle row can be used as the dephasing-residual share target, and the CZ
crosstalk row can serve as a spatial-correlated slot. This grouping is a declared simulator design choice,
not a grouping asserted by the paper.

## The OBSERVABLE / metric [paper]
The budget metric is the component contribution to `(Lambda_3/5)^-1`. The repetition-code burst analysis uses
time-resolved detection fractions to identify rare correlated bursts. These are separate observables and should
not be merged into a per-round Markovian background rate.

## Findings + numbers [paper]
Main/device anchors:

| Quantity | Value | Source locus |
|---|---:|---|
| Main threshold processor | 105-qubit processor for d7 surface code | `txt:104-130` |
| 105Q operating coherence | `T1 = 68 us`, `T2,CPMG = 89 us` | `txt:104-130` |
| Cycle time | 1.1 us | `txt:10-19`, `txt:482-543` |
| d7 logical lifetime | 291 +/- 6 us | `txt:176-209` |
| Best physical-qubit lifetime comparator | 119 +/- 13 us | `txt:176-209` |
| Break-even factor | 2.4 +/- 0.3 | `txt:176-209` |

Table S4 budget (`txt:2051-2091`):

| Component | `p_expt` | `w_i` | Contribution | Share |
|---|---:|---:|---:|---:|
| CZ gates, excluding crosstalk/leakage | 2.8e-3 | 65 | 0.182 | 41% |
| CZ crosstalk | 5.5e-4 | 91 | 0.050 | 11% |
| CZ leakage | 2.0e-4 | 108 | 0.022 | 5% |
| Data qubit idle | 0.9e-2 | 10 | 0.090 | 20% |
| Readout | 0.8e-2 | 6 | 0.048 | 11% |
| Reset | 1.5e-3 | 6 | 0.009 | 2% |
| SQ gates | 6.2e-4 | 63 | 0.039 | 9% |
| Leakage heating | 2.5e-4 | 18 | 0.005 | 1% |

Rare burst facts (`txt:2160-2180`): correlated detection-fraction bursts show a sharp rise and exponential
decay; the paper reports roughly once per hour, equivalently about once every 3e6 shots, with 400-700 us decay
scale and spatial grouping of affected measure qubits.

## Limitations [paper]
- The 68 us / 89 us coherence values are stated for the 105-qubit processor in the d7 result section. They
  should not be relabeled as the 72Q processor's coherence without another source.
- Table S4 sensitivities assume perfect DQLR and correlated matching; the budget is therefore a model-based
  decomposition under those assumptions.
- The paper states the error budget overpredicts `Lambda` by about 20%, so the model captures most but not all
  effects (`txt:270-295`). That residual is not identified as any one microscopic mechanism.

## Relevance to AI_QEC [ours]
Use Table S4 as the Willow-era component-share anchor for composed simulator inputs. The data-idle row provides
a cited 20% budget target for a residual dephasing channel; the local CZ/SQ/readout/reset rows provide a
cited Markovian background scale; CZ crosstalk provides a cited spatial-correlated slot. Keep the rare bursts
as a separate block/event-timescale phenomenon rather than folding them into ordinary per-round rates.

## How to use / trust + open questions [ours]
Trust level: high for Table S4 arithmetic, lifetime/coherence values, and burst timescales as stated in the
text. Open question: if the table needs a 72Q-specific coherence row, it needs a separate cited extraction from
the 72Q calibration/figure material rather than the 105Q main-result values.
