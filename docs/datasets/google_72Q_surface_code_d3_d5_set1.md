# Dataset note — `google_72Q_surface_code_d3_d5_set1` (72Q XZZX surface code, d3/d5, set 1)

> Dataset reading note in the house format (full read of the shipped README +
> one real `metadata.json` + captured directory listings, cached under
> `docs/datasets/_sources/`). Centerpiece: **Relevance to qec_twin** — feeds
> **R2-lite-b** (d3 plaquette/boundary windows) and, at d5, the declared
> surface-code destination behind the ADR 0008 carrier.

## Metadata
- **Local path.** `/home/cx/Document/google_72Q_surface_code_d3_d5_set1/google_72Q_surface_code_d3_d5_set1/` (note the doubled directory; top level: `sample_NN/` dirs + `README/`).
- **Source.** Zenodo 13273331 family, CC-BY (per ADR 0007; the cached README carries **no DOI or host-paper statement itself**). The decoding pathways and the related-dataset pointers tie it to Sivak et al., arXiv:2406.02700.
- **Cached originals.** `_sources/README_surface_d3d5s1.md`, `_sources/google_72Q_surface_code_d3_d5_set1.metadata.sample.json`, `_sources/directory_listings.txt`. The README references `patches.png` (patch layout) and `logicals.png` (logical-observable decay) — **not cached**, markdown only.
- **Note.** `*:Zone.Identifier` Windows ADS artifacts may sit next to data files locally; ignore them.

## Executive summary
QEC **memory experiments of the XZZX surface code** on the 72-qubit device, organized `sample_NN/<patch>/<basis>/<rNN>/` — sample = "a collection of QEC data acquired in one experiment", patch ∈ {five d3 patches + one d5 patch}, basis ∈ {X, Z}, rNN = number of QEC cycles ("`r05`, `r10`, etc."). Calibration freshness statement (Overview, italic, verbatim): **"The last 16 experiments in this dataset were performed sequentially during the course of 15 hours."** — i.e. set1 is the *fresh/sequential* counterpart to set2's deliberately mixed-calibration selection. Each leaf instance ships the same file kit as the rep-code release (ideal + SI1000 stim circuits, raw b8 measurements/sweeps, derived detections/observable flips, metadata, decoding pathways); the cached metadata sample is a d3 instance with **50,000 shots** at **90 rounds**.

## (a) Experiment design
- **Code.** XZZX surface code (Overview, verbatim): "Note that the `X` or `Z` basis is an arbitrary designation for the [XZZX surface code] used here. For each patch, one can inspect the corresponding `circuit_ideal.stim` file …, and more specifically, the `OBSERVABLE_INCLUDE` and `QUBIT_COORDS` annotations to determine the protected observable." (XZZX ref: Bonilla Ataides et al., Nat. Commun. 12, 2172 (2021).)
- **Hierarchy** (Overview): `dataset_dir/sample_dir/patch_dir/basis_dir/cycles_dir/<files>`. "The naming convention is chosen to indicate the code distance and the location of the center qubit of the patch."
- **Patches** (from the captured `sample_00` listing — README shows them only as `patches.png`): `d3_at_q3_5`, `d3_at_q5_3`, `d3_at_q5_5`, `d3_at_q5_7`, `d3_at_q7_5`, `d5_at_q5_5` — **five d3 patches (center + 4 neighbors) and one d5 patch sharing center (5,5)**. d3 = 9 data + 8 measure = **17 qubits** (metadata sample confirms 9+8); d5 = 25 data + 24 measure = **49 qubits** (derived from code structure, no d5 metadata cached).
- **Samples.** Named `sample_00, sample_01, …`. Exact count is **not stated in the README**; the captured listing's link count on the dataset dir (24 = 2 + 22 subdirs = 21 samples + `README/`) implies **21 samples, `sample_00`–`sample_20`** (consistent with the highest index visible in the truncated listing, `sample_20`) — *inferred from the listing, not README-stated*.
- **Acquisition / calibration freshness (load-bearing, verbatim):** "*The last 16 experiments in this dataset were performed sequentially during the course of 15 hours.*" Nothing more is said: the calibration state of the earlier (≈5) samples is **not stated**. Contrast set2, whose README declares deliberately mixed calibration ages — set1 is the comparatively controlled/sequential set.
- **Rounds (rNN levels).** README Overview: "subdirectories for the number of QEC cycles (rounds) in each particular memory experiment: `r05`, `r10`, etc." — the **full list of round counts is not stated**. Confirmed to exist: **r90** (the cached metadata sample: `rounds=90`). The Decoding-pathways table references "the 13-cycle calibration data", implying **13-cycle instances** exist somewhere in the release (r13 dirs not directly confirmed by the captured listings).
- **Shots.** Metadata sample: **50,000 shots** for that instance (d3_at_q5_5 / X / r90). A global per-instance shot count is **not stated in the README**; other instances may differ.
- **Per-instance semantics** (Overview): "This data, when decoded, results in a single point in the figure that shows the decay of the expectation value of the logical observable (in this case, `Z` observable)."
- **Metadata sample** (cached): `{"basis": "X", "rounds": 90, "shots": 50000, "distance": 3, "data_qubit_coords": [9 coords centered (5,5)], "meas_qubit_coords": [8 coords]}`. Note the schema differs from the rep release: `rounds` (not `cycles`), `data_qubit_coords`/`meas_qubit_coords` (not `data_qubits`/`meas_qubits`), and **no `qubit_order` key** (README metadata list has 6 items here vs 7 for the rep code).

## (b) File inventory + formats
Per leaf instance `data_dir = dataset_dir/sample_dir/patch_dir/basis_dir/cycles_dir` (README File contents):

| File | Format | `bits_per_shot` (README wording) |
|---|---|---|
| `circuit_ideal.stim` | stim circuit | — (detector + observable annotations; the source of all bit counts) |
| `circuit_noisy_si1000.stim` | stim circuit | — (SI1000 noisy version) |
| `measurements.b8` | b8 | "the total number of measurements in the circuit" |
| `sweep_bits.b8` | b8 | "the number of sweep bits in the circuits, which can be determined from `circuit_ideal.stim`" |
| `detection_events.b8` | b8 | "the number of detectors in the circuit, which can be determined from `circuit_ideal.stim`" |
| `obs_flips_actual.b8` | b8 | "the number of observables in the circuit, which in this dataset is always 1" |
| `metadata.json` | json | — (basis, distance, rounds, shots, data/meas qubit coords) |
| `decoding_results/<pathway>/error_model.dem` | stim DEM | — |
| `decoding_results/<pathway>/obs_flips_predicted.b8` | b8 | number of observables (= 1) |

- **b8 packing** (verbatim, all b8 kinds): "Each shot's data is byte aligned by padding up to a multiple of 8 bits. Bits are packed into bytes in little endian order."
- **Sweep-bit semantics** (verbatim): "the sweep bits are used to initialize the data qubits into different patterns of 0s and 1s. These bits determine whether instructions like `CX sweep[0] 5` in the circuit file are turned into an `X` gate or `I` gate on qubit 5."
- Detector/measurement counts per instance are **not stated in the README** (depend on d and rounds); read them from `circuit_ideal.stim`.

## (c) Logical observable
- Defined by `OBSERVABLE_INCLUDE` (+ `QUBIT_COORDS`) annotations in `circuit_ideal.stim` (Overview, quoted in (a)); `circuit_ideal.stim` carries "annotations describing how detection events are computed from the measurement record and what the logical observable is" (File contents).
- **Exactly 1 observable**: "the number of observables in the circuit, which in this dataset is always 1."
- `obs_flips_actual.b8` (verbatim): "indicating if the observable was flipped compared to what it would have been if the circuit had executed noiselessly … This is the data that decoders are supposed to predict, hence the subscript `_actual` as opposed to `_predicted`."
- **Per-shot logical-error recipe** (verbatim): "Whether a logical error occurred or not in any given shot can be determined by computing an XOR of this data with `obs_flips_actual.b8` data."

## (d) Noise model shipped
- `circuit_noisy_si1000.stim` — "The noisy version of the QEC circuit with SI1000 circuit error model" (Gidney et al., Quantum 5, 605 (2021)). **No SI1000 parameter value is stated in the README**; read p from the circuit file. (The M1 pre-registration's p=1e-3 applies to the *rep-code* release; do not assume it here without checking.)

## (e) Decoding pathways shipped — evaluator/baseline-only
Isolation contract: shipped DEM priors and `obs_flips_predicted.b8` are baseline/evaluator artifacts (decoder configuration + %ΔLER scoring), never learner inputs. Four pathways:

| Pathway | Decoder | Prior |
|---|---|---|
| `correlated_matching_decoder_with_si1000_prior` | Correlated matching on the sparse blossom engine [Higgott et al. 2303.15933] with "a variant of the two-step re-weighting strategy" [Fowler 1310.0863] | SI1000 prior [Gidney et al.] |
| `correlated_matching_decoder_with_rl_optimized_prior` | same | RL-optimized prior [Sivak et al. 2406.02700], (verbatim) "Optimized for each patch / basis in isolation using the 13-cycle calibration data." |
| `harmony_decoder_with_si1000_prior` | Harmony [Shutty et al. 2401.12434] "ensembling **101** correlated matching decoders" | SI1000 prior |
| `harmony_decoder_with_rl_optimized_prior` | same | RL-optimized prior |

- **No pij / detector-correlations prior is shipped in set1** (set2 has it) and **no uninformative-prior pathway** either — the pij baseline for any set1 comparison must be self-computed.
- DEM semantics (verbatim): "It represents error mechanisms as hyperedges in a weighted hypergraph where nodes correspond to detectors. Error mechanisms that set off more than two detectors also contain suggested decompositions into edge-like errors."

## (f) Provenance recipes + references
- **Example 1 (m2d)**: `stim m2d --circuit circuit_ideal.stim --in measurements.b8 --in_format b8 --sweep sweep_bits.b8 --sweep_format b8 --out detection_events.b8 --out_format b8 --obs_out obs_flips_actual.b8 --obs_out_format b8` (stim 1.9+) — regenerates the derived data; the ingestion-parity check for this set.
- **Example 2**: `stim analyze_errors --in circuit_noisy_si1000.stim --out error_model.dem` then `pymatching predict --dem … --in detection_events.b8 --in_format b8 --out obs_flips_predicted.b8 --out_format b8` (pymatching 2.0+).
- **References cited:** [1] Higgott et al. 2303.15933 (sparse blossom); [2] Fowler 1310.0863 (correlated re-weighting); [3] Gidney et al., Quantum 5, 605 (2021) (SI1000); [4] Sivak et al. 2406.02700 (RL priors; related Sycamore dataset doi:10.5281/zenodo.11403594); [5] Shutty et al. 2401.12434 (Harmony); [6] Google QAI, Nature 614, 676 (2023) (related Sycamore dataset zenodo 6804040). Additional resources: Stim, PyMatching.

## (g) Relevance to qec_twin
- **Role: R2-lite-b** (ADR 0007 Decision 2): "surface-code d=3 plaquette/boundary windows from the 72Q sets", entered "after the carrier feasibility study, or earlier with declared window caveats". The d3 whole-code instance is **17q > the ~15q exact wall** — even d3 is windows-only on `forward/exact`; the measured **window-closure violation is itself a deliverable** (a located map of correlation mass the pij/window abstraction cannot express, consistent-with — never attributed-to — the documented nonlocal crosstalk/leakage).
- **d5_at_q5_5 (49q)** is destination material: the d=5/d=7 surface-code twin (C = R3) behind the ADR 0008 carrier swap gate. Not reachable by the exact backend in any window regime worth claiming whole-code results on.
- **Drift/freshness axis:** the "last 16 experiments … 15 hours" sequential block makes set1 the *well-calibrated, short-baseline* condition; set2 supplies the deliberately stale/mixed condition. For H4-style hardware drift contrasts, set1 is the control arm. (Any such use stays R2-lite-scoped: sample-indexed trajectories + finite-sample band coverage; neither Gate B nor the H4 controlled-sim gate is satisfied by hardware slices — ADR 0007 M5 scoping.)
- **Mechanism link to H2:** Google's correlated-error wedge (leakage + CZ stray-interaction ZZ/swap, ≈17% of the error budget per ADR 0007) is the predicted closure violator here; H2 is its *simulation twin*. Residual structure from these patches is reported as a misspecification direction feeding H2/H3 sequencing via the back-edge.
- **Claim discipline:** R2-lite forbidden claims apply verbatim — no `do()` on hardware, no mechanism attribution, no Born/CPTP-learning claims, no unscored "fits the device" language; shipped priors (SI1000/RL) are baselines for the METRICS.md hardware ledger (%ΔLER under a frozen named decoder, held-out NLL, pij agreement).
- **Reader caveats:** sample count (21) and patch list are listing-inferred, not README-stated; round-level inventory per patch/basis is unknown beyond r90 + "r05, r10, etc."; shots per instance confirmed only for the cached sample (50,000).
