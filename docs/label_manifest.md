**Memo: Google QEC Dataset Labeling Potential**

Date: May 31, 2026

We found several Google QEC datasets under `/home/cx/Document`, not only the 72Q surface-code Set1 dataset. The local inventory includes:

- `google_72Q_repetition_code_d29`
- `google_72Q_surface_code_d3_d5_set1`
- `google_72Q_surface_code_d3_d5_set2`
- `google_105Q_surface_code_d3_d5_d7`

These datasets contain real hardware measurement records, detection events, logical observable flips, Stim circuits, metadata, DEM files, and decoder predictions. They are valuable for external validation, decoder utility, calibration, transfer, drift-style analysis, and proxy mechanism discovery.

The strongest labels available are:

- shot-level logical flip labels from `obs_flips_actual.b8`
- decoder failure labels from `obs_flips_actual XOR obs_flips_predicted`
- context labels such as dataset, sample, patch, basis, rounds, distance, and qubit coordinates
- decoder/prior labels from `decoding_results`
- DEM-derived proxy labels such as support size, boundary/bulk region, detector degree, round layer, logical support, and fault-graph community

However, these datasets do **not** provide true per-shot physical error mechanisms, true hidden fault partitions, or catalog mechanism labels such as `M0/M1/...`. Any such labels must be treated as proxy labels, not ground truth.

Recommendation: build a unified `google_dataset_inventory` and `label_manifest` that records strong labels, context labels, decoder labels, and DEM/proxy labels separately. This would turn the Google datasets into a strong external validation benchmark without overstating them as true physical-mechanism supervision.

## Current Scorecard Diagnosis

The current Google X/Z scorecard should be treated as a smoke benchmark, not as
the primary benchmark for SCOPE-level advantage over dMLE.

### Question 1: Why are NLL results concentrated near `0.0024-0.0026`?

Answer: the reported `heldout_local_window_excess_nll` is not raw NLL. It is:

```text
model_window_nll - heldout_empirical_window_entropy
```

with units:

```text
nats_per_window, equal-window averaged
```

In the current 24-context Set1 run, the actual evaluation windows were very
shallow:

```text
num_windows:      28 or 55
max_window_bits:  2
mean_window_bits: about 1.55 to 1.68
```

Therefore the scorecard mostly measures single-detector, detector-pair,
logical-single, and logical-pair statistics. Strong per-context DEM models are
expected to cluster tightly on this residual metric. The concentration near
`0.0024` is therefore evidence that the metric is narrow and low-order, not
evidence that all models have the same generated-noise quality.

Evidence:

- `src/scope_static/experiments/willow_data/local_mechanism.py` defines the excess
  metric as model window NLL minus empirical window entropy.
- `src/scope_static/dem/metrics.py` records the same definition in flattened
  metric fields.
- The completed 24-context run recorded only size-1 and size-2 effective
  evaluation windows.

### Question 2: Is current preprocessing exposing the right Google-data structure?

Answer: not yet. The current preprocessing is useful for checking that the DEM
pipeline, upstream dMLE adapter, and same-context heldout likelihood evaluation
work. It does not yet expose the richest Google-data structure to the model or
to the primary metric.

The current scorecard mostly reduces each Google leaf to:

```text
same-context train shots
same-context heldout shots
DEM fault graph
low-order local-window likelihood
```

That is close to dMLE's natural operating mode. It does not yet strongly test:

```text
cross-context transfer
calibration or domain shift
drift prediction
logical-tail generation
decoder-facing utility
DEM-fault proxy structure
boundary / bulk / chain / region effects
high-order syndrome correlations
```

This means that the current X/Z scorecard can show whether SCOPE-style models
can match dMLE on a narrow same-leaf task, but it cannot establish exponential
or structural advantage over dMLE.

## Implication

The next Google-data step should be read-only and diagnostic before more large
training runs:

```text
1. Build a real google_dataset_inventory artifact.
2. Build a real label_manifest artifact with strong/context/decoder/proxy
   labels separated.
3. Add a scorecard_metric_audit artifact reporting raw NLL, empirical entropy,
   excess NLL, window size distribution, window kind distribution,
   detector/logical coverage, and per-window residual spread.
```

Only after that should the benchmark move to harder metrics such as:

```text
cross-context heldout NLL
masked conditional syndrome NLL
higher-order window NLL
logical-tail calibration
decoder failure CE / Brier score
decoder-facing utility
sample-efficiency curves
```

These are the metrics more likely to test whether a structured SCOPE model is
learning transferable noise structure rather than merely matching per-context
DEM rate fitting.
