> **ARCHIVED 2026-06-15.** Legacy 72Q measured structure (different device); the 105Q d3 re-measurement is step-3. Kept as a motivating reference.

# Measured real d3 XZZX structure (72Q set2 — legacy reference)

> The measured noise structure of a real Google XZZX d3 surface code. **Dataset note (2026-06-15):**
> this was measured on the **72Q** `surface_code_d3_d5_set2` device (`d3_at_q5_5`), a **different device**
> from the **105Q** `d3_d5_d7` live front. After the 2026-06-15 redirect the white-box is unified on the
> 105Q nine `d3_at_q*` patches (D1); these 72Q numbers are kept as a **legacy motivating reference**
> (independent-edges insufficient), and the analogous structure on the 105Q d3 patches is the first
> step-3 re-measurement. Plain reporting of measured facts.

## Measurement — `outputs/surface_d3_structure.py`

Real 72Q set2 `d3_at_q5_5/X/r15`, sample_00 (60k shots, decoder-independent; detection events + circuit
only):

- detection ≈ 6.3% / detector;
- 2-body correlation sits **on the matching graph** (0 far / non-edge pairs above 5σ);
- **device vs the shipped SI1000 sim: detection 2.4×, edge-pij 3.6×, 3-body cumulant 2×** — 467/600
  matching-graph triangles carry a 3-body cumulant above the `1/N` floor.

The real device is noisier, more correlated, and higher-order than the sim. One instance (single
patch / basis / round / sample), not a sweep; the device-vs-sim gap may carry sample-calibration
content.

Method: 2-body via `spitz_pij_exact` (Spitz Eq. 13, exact); 3-body via the matching-graph triangle
cumulant. Syndrome-weight variance is a 2-point quantity, so it is not used as a higher-order measure;
the higher-order read is the measured-vs-SI1000 3-body cumulant.

## Implication for the model

An independent-edges model is insufficient (real 2-body + 3-body; even the SI1000 sim under-predicts).
The model must carry correlations and the higher magnitude — the **window-channel field** of weight-≤t
mechanism compositions ([`window_covering_architecture.md`](../whitebox/window_covering_architecture.md)). The correlated/coherent ≤2-qubit
mechanisms (M8/M9/M10/M11/M12/M21/M22–M33) produce this structure: a 2-qubit error flips several
detectors, giving the measured hyperedge / 3-body cumulant content that an independent-edges DEM cannot
represent.

## Validation (real data — no synthetic ground truth)

Held-out per-shot syndrome NLL + the structure-residual check (does the fitted model reproduce the
measured detection / 2-body / 3-body). There is no exact channel ground truth on real data; claims are
observation-fit + residual structure, with honest bands.
