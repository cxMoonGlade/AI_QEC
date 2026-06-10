# hardware — R2-lite published-data ingestion

Bounds the hardware-data ingestion rung (ADR 0007, R2-lite): stim-native published
QEC releases (`.stim` circuits, `.b8` bit-packed shots, `.dem` decoder models) in →
label-free **OBSERVATIONS** out. First target: the local Google d=29
repetition-code release (`google_72Q_repetition_code_d29`, Zenodo 13273331 family;
Willow arXiv:2408.13687), resolved via the `QEC_TWIN_HW_DATA` env var (parent
directory holding the release folder).

- `dataset.py` — root resolution + `RepCodeD29` layout/structure contract (the M1 P1 integers).
- `b8_io.py` — chunked stim-b8 reader (packed uint8; never materializes a fully unpacked corpus).
- `stim_artifacts.py` — circuit counts, detector `(chain, layer)` grid, m2d conversion +
  bit-exact parity, evaluator-side DEM pair-support extraction.
- `detection_stats.py` — detection-event fractions (METRICS.md hardware ledger) +
  shot-level bootstrap SEs/CIs + layer-profile flatness/burst report.
- `pij.py` — Spitz **Eq. 13 exact** `p_ij` (two-point; hyperedge-blind — METRICS.md
  hardware ledger), the pre-registered pair-class set, per-entry and class-mean SEs.
- `observations.py` — the label-free observation container handed to calibration (M3).
- `m1_report.py` — M1 ingestion-parity scoring driver (gates P1–P4, side-bets P5–P9;
  pre-registration: `docs/metric_results.md` 2026-06-09).

**Isolation contract.** This module never imports from `qec_twin.mechanisms` (no
teacher machinery on the hardware path). The release's `decoding_results/` artifacts
(RL-optimized DEM prior, predicted observable flips) are evaluator/baseline material:
reachable only through the explicitly tagged
`RepCodeD29.evaluator_decoding_artifacts(...)` accessor, never mixed into
learner-facing observation containers (`observations.py` excludes them by
construction).

**Claim restrictions (R2-lite, ADR 0007).** Work scored through this module licenses
prediction-calibration and decoder-prior-utility statements only — no
`do()`/counterfactual claim on hardware, no mechanism attribution, no
Born-generation/CPTP-learning claim, no unscored "fits the device" language.
Residual structure is reported as a **misspecification direction** (back-edge
input), never an attributed mechanism. Spec: `docs/TWIN.md`; metrics:
`docs/METRICS.md` (hardware-data section).
