# Dataset note — `google_72Q_surface_code_d3_d5_set2` (72Q XZZX surface code, d3/d5, set 2 — deliberately mixed calibration)

> Dataset reading note in the house format (full read of the shipped README +
> one real `metadata.json` + captured directory listings, cached under
> `docs/datasets/_sources/`). Centerpiece: **Relevance to qec_twin** — the
> **deliberately mixed calibration freshness** makes set2 the natural hardware
> testbed for the drift axis (H4-adjacent, R2-lite-scoped), and it is the only
> 72Q surface set that **ships pij-prior baselines**.

## Metadata
- **Local path.** `/home/cx/Document/google_72Q_surface_code_d3_d5_set2/google_72Q_surface_code_d3_d5_set2/` (doubled directory; top level: `sample_NN/` dirs + `README/`).
- **Source.** Zenodo 13273331 family, CC-BY (per ADR 0007; the cached README carries **no DOI or host-paper statement itself**). Pathways and related-dataset pointers tie it to Sivak et al., arXiv:2406.02700.
- **Cached originals.** `_sources/README_surface_d3d5s2.md`, `_sources/google_72Q_surface_code_d3_d5_set2.metadata.sample.json`, `_sources/directory_listings.txt`. README references `patches.png` and `logicals.png` — **not cached**.
- **Note.** `*:Zone.Identifier` Windows ADS artifacts may sit next to data files locally; ignore them.

## Executive summary
Same experiment family, device, code (XZZX surface code), patch set, hierarchy (`sample_NN/<patch>/<basis>/<rNN>/`) and per-instance file kit as set1, but with a different — and load-bearing — acquisition policy (Overview, italic, **verbatim**): **"In some experiments, the device was well calibrated, while in others the calibrations have not been refreshed for several days. This selection is intended for testing the decoding algorithms under a wide range of experimental conditions."** Set2 also ships a much richer decoding-pathway matrix: 3 decoders (correlated matching, Harmony, belief matching) × 3 priors (**uninformative, detector-correlations/pij, RL-optimized**) = 9 pathways — including the field-standard **pij prior**, absent from set1. The cached metadata sample is a d3 instance with **50,000 shots at 15 rounds** (so **r15** exists here, alongside the README's "`r05`, `r10`, etc.").

## (a) Experiment design
- **Code/bases/patches/hierarchy: identical wording to set1.** XZZX surface code; "the `X` or `Z` basis is an arbitrary designation"; protected observable read from `OBSERVABLE_INCLUDE` + `QUBIT_COORDS` in `circuit_ideal.stim`; hierarchy `dataset_dir/sample_dir/patch_dir/basis_dir/cycles_dir`; patch named by distance + center qubit.
- **Patches** (captured `sample_00` listing; identical to set1): `d3_at_q3_5`, `d3_at_q5_3`, `d3_at_q5_5`, `d3_at_q5_7`, `d3_at_q7_5`, `d5_at_q5_5` — five d3 (17q each: 9 data + 8 measure, metadata-confirmed) + one d5 (49q, derived) sharing center (5,5). Same patch geometry as set1 ⇒ set1/set2 are directly comparable per patch.
- **Samples.** `sample_00, sample_01, …`; exact count **not stated in the README**. The captured listing's link count (38 = 2 + 36 subdirs = 35 samples + `README/`) implies **35 samples, `sample_00`–`sample_34`** (highest index visible in the truncated listing: `sample_32`) — *listing-inferred, not README-stated*. Note set2 has more samples than set1 (35 vs 21, both inferred).
- **CALIBRATION FRESHNESS — the set1↔set2 difference (verbatim, load-bearing for H4-style drift work):** set2: "*In some experiments, the device was well calibrated, while in others the calibrations have not been refreshed for several days. This selection is intended for testing the decoding algorithms under a wide range of experimental conditions.*" vs set1: "*The last 16 experiments in this dataset were performed sequentially during the course of 15 hours.*" Set2 deliberately spans calibration ages (well-calibrated ↔ stale-by-days); set1 is the sequential short-baseline block. **Which samples are which is not stated** — the README gives no per-sample calibration-age labels or timestamps.
- **Rounds (rNN levels).** "subdirectories for the number of QEC cycles (rounds) in each particular memory experiment: `r05`, `r10`, etc." — full list **not stated**. Confirmed to exist: **r15** (cached metadata sample, `rounds=15`). The pathway table's "13-cycle calibration data" implies 13-cycle instances exist somewhere in the release (not directly confirmed by the captured listings).
- **Shots.** Metadata sample: **50,000** (d3_at_q5_5 / X / r15). Global per-instance shot count **not stated**; other instances may differ.
- **Metadata schema** (cached sample): `{"basis": "X", "rounds": 15, "shots": 50000, "distance": 3, "data_qubit_coords": [9 coords centered (5,5)], "meas_qubit_coords": [8 coords]}` — same schema as set1 (`rounds` not `cycles`; `*_qubit_coords` not `*_qubits`; no `qubit_order`); README metadata list has the same 6 items.
- **Per-instance semantics** (Overview): one decoded instance = "a single point in the figure that shows the decay of the expectation value of the logical observable (in this case, `Z` observable)."

## (b) File inventory + formats
Identical kit and wording to set1, per leaf instance:
`circuit_ideal.stim`, `circuit_noisy_si1000.stim` (stim circuit format); `measurements.b8` (bits_per_shot = "the total number of measurements in the circuit"); `sweep_bits.b8` (= number of sweep bits, from `circuit_ideal.stim`); `detection_events.b8` (= number of detectors, from `circuit_ideal.stim`); `obs_flips_actual.b8` (= number of observables, "which in this dataset is always 1"); `metadata.json`; `decoding_results/<pathway>/{error_model.dem, obs_flips_predicted.b8}` (predicted flips: 1 bit/shot).
- **b8 packing** (verbatim, all kinds): "Each shot's data is byte aligned by padding up to a multiple of 8 bits. Bits are packed into bytes in little endian order."
- **Sweep-bit semantics** (verbatim): "the sweep bits are used to initialize the data qubits into different patterns of 0s and 1s. These bits determine whether instructions like `CX sweep[0] 5` … are turned into an `X` gate or `I` gate on qubit 5."
- Per-instance detector/measurement counts are **not in the README**; read from `circuit_ideal.stim`.

## (c) Logical observable
- Defined by `OBSERVABLE_INCLUDE` (+ `QUBIT_COORDS`) in `circuit_ideal.stim`; **exactly 1 observable** ("always 1").
- `obs_flips_actual.b8`: flips "compared to what it would have been if the circuit had executed noiselessly"; "the data that decoders are supposed to predict, hence the subscript `_actual`".
- **Per-shot logical-error recipe** (verbatim): "Whether a logical error occurred or not in any given shot can be determined by computing an XOR of this data with `obs_flips_actual.b8` data."

## (d) Noise model shipped
- `circuit_noisy_si1000.stim` — SI1000 circuit error model (Gidney et al., Quantum 5, 605 (2021)). **Parameter value not stated in the README**; read p from the circuit file.

## (e) Decoding pathways shipped — evaluator/baseline-only (the richest matrix of the four releases)
Isolation contract: all `decoding_results/` artifacts are baselines/evaluator inputs only. **3 decoders × 3 priors = 9 pathways:**

| Pathway | Decoder | Prior |
|---|---|---|
| `correlated_matching_decoder_with_uninformative_prior` | Correlated matching on sparse blossom [Higgott 2303.15933] + "a variant of the two-step re-weighting strategy" [Fowler 1310.0863] | "Uninformative prior, see Appendix C of Ref. [Sivak 2406.02700]" |
| `correlated_matching_decoder_with_prior_from_detector_correlations` | same | (verbatim) "Prior based on the detector correlations [Spitz 1800012], [Nature 595, 383], [Nature 614, 676]. Fitted on each patch / basis in isolation using the 13-cycle calibration data." — **the pij prior** |
| `correlated_matching_decoder_with_rl_optimized_prior` | same | RL-optimized [Sivak], "Optimized for each patch / basis in isolation using the 13-cycle calibration data." |
| `harmony_decoder_with_uninformative_prior` | Harmony [Shutty 2401.12434] "ensembling **101** correlated matching decoders" | uninformative |
| `harmony_decoder_with_prior_from_detector_correlations` | same | pij |
| `harmony_decoder_with_rl_optimized_prior` | same | RL |
| `belief_matching_decoder_with_uninformative_prior` | Belief matching [Higgott PRX 13, 031007] on sparse blossom "with 4 belief propagation steps" | uninformative |
| `belief_matching_decoder_with_prior_from_detector_correlations` | same | pij |
| `belief_matching_decoder_with_rl_optimized_prior` | same | "Same as optimized prior above, but produced for the belief matching decoder." |

- Set2 is the **only one of the four releases shipping the pij / detector-correlations prior** — the exact M3/M4 comparison baseline named in ADR 0007 — and the only one shipping an **uninformative-prior** arm (the Sivak "48%/10.6% vs uninformative" convention's reference point).
- DEM semantics (verbatim, same as the others): hyperedges in a weighted hypergraph over detectors; >2-detector mechanisms "contain suggested decompositions into edge-like errors."

## (f) Provenance recipes + references
- **Example 1 (m2d)** and **Example 2 (analyze_errors → pymatching predict)**: identical commands to set1 (stim 1.9+, pymatching 2.0+); Example 1 is the ingestion-parity (bit-for-bit) check for this set.
- **References cited:** [1] Sivak et al. 2406.02700 (RL priors, uninformative prior App. C; related Sycamore dataset doi:10.5281/zenodo.11403594); [2] Shutty et al. 2401.12434 (Harmony); [3] Higgott et al. 2303.15933 (sparse blossom); [4] Higgott et al., PRX 13, 031007 (2023) (belief matching); [5] Spitz et al., Adv. Quantum Technol. 1, 1800012 (2018) (**pij estimator**); [6] Google QAI, Nature 595, 383 (2021); [7] Google QAI, Nature 614, 676 (2023) (related dataset zenodo 6804040); [8] Fowler 1310.0863. Additional resources: Stim, PyMatching.

## (g) Relevance to qec_twin
- **Role: R2-lite-b** (ADR 0007 Decision 2), same as set1: d3 = 17q > the ~15q exact wall ⇒ **plaquette/boundary windows only** on `forward/exact`; the window-closure violation map is itself a deliverable. d5_at_q5_5 (49q) is destination material behind the ADR 0008 carrier.
- **The drift/condition-diversity set (H4-adjacent).** The deliberately mixed calibration freshness — quoted verbatim in (a) — is exactly the "wide range of experimental conditions" a drift-aware twin must survive: per-sample parameter trajectories, forecasting, finite-sample band coverage across well-calibrated ↔ days-stale samples. Two caveats travel with any such use: (i) the README provides **no per-sample calibration-age labels**, so condition must be inferred from the data (and reported as inferred); (ii) R2-lite scoping holds — sample-indexed trajectories and coverage only; **neither Gate B nor the H4 controlled-sim gate is satisfied by hardware slices** (ADR 0007 M5 scoping).
- **Baseline richness.** Shipped uninformative / pij / RL priors × 3 decoders give ready-made reference arms for the METRICS.md hardware ledger (%ΔLER under a frozen named decoder, pij-matrix agreement, held-out NLL) without rebuilding competitor pipelines — set2 is where a twin-calibrated `.dem` can be scored against the *shipped* pij prior rather than a self-computed one.
- **Set1↔set2 contrast as a context pair:** same patches, same device, different calibration policy — the closest hardware analogue of the probe-ladder's context axis for d3 windows (few fixed contexts ⇒ wide alias; report bands/abstain accordingly, indicative not certified-covering).
- **Mechanism link:** expected closure violators are the documented nonlocal crosstalk + leakage tails (H2 is the simulation twin of the stray-coupling component; H3 the leakage axis). All residuals reported as **misspecification directions**, never attributed mechanisms.
- **Claim discipline:** R2-lite forbidden claims verbatim — no `do()` on hardware, no mechanism attribution, no Born/CPTP-learning claims; shipped priors/predictions are evaluator/baseline-only under the isolation contract.
- **Reader caveats:** sample count (35) is listing-inferred; round-level inventory unknown beyond r15 + "r05, r10, etc."; 13-cycle calibration instances implied by the pathway table but not directly confirmed; shots confirmed only for the cached sample (50,000).
