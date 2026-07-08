# Full-text review — Google Quantum AI, "Suppressing quantum errors by scaling a surface code logical qubit" (arXiv:2207.06431)

> **Provenance (2026-07-01): FULL-TEXT read (精读).** PDF `outputs/papers/2207.06431.pdf`
> -> txt `outputs/papers/2207.06431.txt` (PyMuPDF, 44 pp). This note is written for the
> load-bearing error-budget and detector-scale facts used by `docs/twin_validation/error_budget_sourced_table.md`.
> Figures were not pixel-extracted; figure facts below are only captions and numbers stated in text.

## Metadata [paper]
- Authors / affiliation: Google Quantum AI.
- Venue / status: arXiv:2207.06431; Nature 614, 676 (2023).
- Type: superconducting surface-code experiment plus Pauli/Pauli+ simulation and error-budget attribution.

## Executive summary [paper]
The paper implements repetition and surface-code memories on a 72-transmon Sycamore processor. The
headline surface-code result is that the distance-5 logical qubit modestly outperforms the ensemble of
distance-3 logical qubits, with logical error probability per cycle 2.914% +/- 0.016% versus 3.028% +/- 0.023%
in the abstract block (`txt:12-23`). For the present simulator work, the load-bearing part is the component
error budget: local CZ, crosstalk, data-idle decoherence, readout/reset, SQ, leakage, and heating are converted
to contributions to `(Lambda_3/5)^-1`.

## Method (deep) [paper]
The error budget uses the component sensitivity expansion

```text
(Lambda_3/5)^-1 = sum_i w_i p_expt^(i)
```

where `p_expt^(i)` is the measured error probability for mechanism `i` and `w_i` is the simulated sensitivity
weight for that mechanism. The paper states that the `w_i` are evaluated at the half-operation point and
that the resulting sum is compared against the inverse simulated suppression factor (`txt:4600-4650`). For
the CZ row, the table uses 4.85e-3 rather than the headline 6.05e-3 because crosstalk and leakage are carried
as separate rows; this avoids double-counting (`txt:4600-4650`).

## The MECHANISM (for implementation) [paper -> ours]
- Local stochastic circuit components: SQ, local CZ, readout, reset, and heating/leakage rows are tabulated
  as per-operation rates with sensitivity weights [paper].
- Data-qubit idle row: the paper attributes a significant logical-budget contribution to data-qubit
  decoherence during measure-qubit readout/reset. It identifies the primary mechanism as low-frequency
  flux-noise dephasing and says XY-4 dynamical decoupling is used to mitigate it (`txt:1303-1318`) [paper].
- [ours] For the coupled simulator, this means the sourced data-idle row is a post-DD residual dephasing slot,
  not the bare bath strength. A pseudomode/bath model may target that residual channel, but the microscopic
  pseudomode mapping is not supplied by this paper.

## The OBSERVABLE / metric [paper]
The detector-level observables include stabilizer detection probabilities and detection-event correlations.
The budget metric is not a detector probability itself; it is the contribution to `(Lambda_3/5)^-1` from each
component via `w_i p_expt^(i)`. This distinction matters: detector-event fractions give the scale of observed
syndrome activity, while Table III gives a logical-suppression budget.

## Findings + numbers [paper]
| Quantity | Value | Source locus |
|---|---:|---|
| Processor | 72 transmon qubits, 121 couplers | `txt:145-150` |
| Mean coherence | `T1 = 20 us`, `T2,CPMG = 30 us` | `txt:145-150` |
| Cycle duration | 921 ns, including 500 ns measurement and 160 ns reset | `txt:127-136` |
| Weight-4 detection probability | 0.185 +/- 0.018 (d5), 0.175 +/- 0.017 (d3 avg) | `txt:250-270` |
| Weight-2 detection probability | 0.119 +/- 0.012 (d5), 0.115 +/- 0.008 (d3 avg) | `txt:250-270` |

Table III budget (`txt:4528-4564`):

| Component | `p_expt` | `w_i` | Contribution | Share |
|---|---:|---:|---:|---:|
| SQ gates | 1.09e-3 | 78.7 | 0.086 | 9.6% |
| CZ gates | 4.85e-3 | 54.5 | 0.264 | 29.4% |
| Data qubit idle | 2.46e-2 | 7.0 | 0.172 | 19.2% |
| Readout | 1.96e-2 | 5.6 | 0.110 | 12.2% |
| Reset | 1.86e-3 | 5.6 | 0.0104 | 1.2% |
| Leakage heating | 6.4e-4 | 125 | 0.080 | 8.9% |
| CZ leakage | 2.0e-4 | 125* | 0.025 | 2.8% |
| CZ crosstalk | 9.5e-4 | 158 | 0.150 | 16.7% |

The listed contributions sum to about 0.898, close to the paper's inverse simulated suppression factor scale
(`txt:4600-4650`).

## Limitations [paper]
- The budget is a sensitivity decomposition of the 72Q Sycamore surface-code experiment, not a bath-spectrum
  spectroscopy result.
- The paper identifies the data-idle mechanism as flux-noise dephasing but does not publish a device-specific
  flux-noise PSD amplitude for the processor in this table.
- Pauli/Pauli+ simulation and component sensitivities are used for attribution; this is not a full analog
  microscopic derivation of every row.

## Relevance to AI_QEC [ours]
Reuse these numbers as cited facts for detector-event scale, Sycamore coherence/cycle context, and the
surface-code error-budget shares. The data-idle row justifies a dephasing-type mechanism slot at roughly
19% of the budget in this generation. It does not by itself justify a particular finite-pseudomode fit,
TLS count, or amplitude transfer from another device class.

## How to use / trust + open questions [ours]
Trust level: high for Table III values and stated detector/coherence numbers; all are text/table facts. Open
question: a device-matched transmon flux-noise spectroscopy source would be needed before treating a PSD
amplitude as a Google-device cited fact rather than a share-calibrated simulator design choice.
