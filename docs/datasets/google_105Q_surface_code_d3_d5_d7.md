# Dataset note — `google_105Q_surface_code_d3_d5_d7` (Willow 105Q XZZX surface code, d3/d5/d7)

> Dataset reading note in the house format (full read of the shipped README +
> one real `metadata.json` + captured directory listings, cached under
> `docs/datasets/_sources/`). Centerpiece: **Relevance to qec_twin** — this is the
> **destination dataset**: the declared d=5/d=7 surface-code twin target (C = R3,
> ADR 0007), reachable only on the post-ADR-0008 scalable carrier. It also carries
> the d3→d5→d7 ladder for Λ (error-suppression-factor) scoring.

## Metadata
- **Local path.** `/home/cx/Document/google_105Q_surface_code_d3_d5_d7/google_105Q_surface_code_d3_d5_d7/` (doubled directory; top level: patch dirs + `README/` — **no sample level**).
- **Source.** Zenodo 13273331 family, CC-BY (per ADR 0007; the cached README carries **no DOI or host-paper statement itself**). Project docs attribute it to Google Willow, arXiv:2408.13687 / Nature s41586-024-08449-y (ADR 0007 References). The Libra pathway (matching synthesis, 2024) is consistent with the Willow decoding stack.
- **Cached originals.** `_sources/README_surface_d3d5d7.md`, `_sources/google_105Q_surface_code_d3_d5_d7.metadata.sample.json`, `_sources/directory_listings.txt`. README references `patches.png` and `logicals.png` — **not cached**.
- **Note.** `*:Zone.Identifier` Windows ADS artifacts may sit next to data files locally; ignore them.

## Executive summary
QEC **memory experiments of the XZZX surface code at distances 3, 5, and 7** on the 105-qubit device, organized `patch_dir/basis_dir/cycles_dir` — **one acquisition tier only**: unlike the rep-code and 72Q surface releases there is **no `sample_NN` level**, hence no sequential-acquisition / drift axis in this release. The captured top-level listing is complete (17 entries < the 20-line cap) and shows **14 patches: nine d3, four d5, one d7** — with `d3_at_q6_7` and `d7_at_q6_7` sharing center (6,7). Bases X and Z; round levels "`r10`, `r30`, etc." (full list not stated; **r90 confirmed** by the cached metadata sample, a d3 instance with 50,000 shots). Per-instance file kit identical to the other releases; five decoding pathways including the **Libra** ensembling decoder, unique to this set.

## (a) Experiment design
- **Code.** XZZX surface code (Overview, verbatim, same wording as the 72Q sets): "Note that the `X` or `Z` basis is an arbitrary designation for the [XZZX surface code] used here. For each patch, one can inspect the corresponding `circuit_ideal.stim` file …, and more specifically, the `OBSERVABLE_INCLUDE` and `QUBIT_COORDS` annotations to determine the protected observable."
- **Hierarchy** (Overview): `dataset_dir/patch_dir/basis_dir/cycles_dir/<files>` — two fewer tiers of replication than the 72Q sets (no samples) and one fewer than rep (no per-sample series). A patch "is characterized by the code distance and its spatial location on the grid of qubits"; named by distance + center qubit.
- **Patches** (complete, from the captured listing; README shows them only as `patches.png`):
  - **d3 (9 patches, 17q each = 9 data + 8 measure):** `d3_at_q2_7`, `d3_at_q4_5`, `d3_at_q4_9`, `d3_at_q6_3`, `d3_at_q6_7`, `d3_at_q6_11`, `d3_at_q8_5`, `d3_at_q8_9`, `d3_at_q10_7`.
  - **d5 (4 patches, 49q each = 25 data + 24 measure, derived):** `d5_at_q4_7`, `d5_at_q6_5`, `d5_at_q6_9`, `d5_at_q8_7`.
  - **d7 (1 patch, 97q = 49 data + 48 measure, derived):** `d7_at_q6_7` — shares center (6,7) with `d3_at_q6_7`. (ADR 0007 cites "97–101q" for d7; the 97 here is the bare code count derived from d² + (d²−1); any extra ancillas are not visible from the cached material.)
- **Rounds (rNN levels).** "subdirectories for the number of QEC cycles (rounds) in each particular memory experiment: `r10`, `r30`, etc." — full list **not stated in the README**. Confirmed to exist: **r90** (cached metadata sample, `rounds=90`). The pathway table's "13-cycle calibration data" implies 13-cycle instances exist somewhere in the release (not directly confirmed). Note the example tick marks differ from the 72Q sets ("r10, r30" vs "r05, r10") — possibly a different round grid, **unverified**.
- **Shots.** Metadata sample: **50,000** (the d3_at_q4_5 patch — data coords centered (4,5) — basis X, r90). Global per-instance shot count **not stated**; other instances may differ.
- **Acquisition / calibration freshness: not stated.** The README contains **no statement** about acquisition order, wall-clock span, or calibration freshness (no analogue of set1's 15-hour note or set2's mixed-calibration note).
- **Metadata schema** (cached sample): `{"basis": "X", "rounds": 90, "shots": 50000, "distance": 3, "data_qubit_coords": [9 coords centered (4,5)], "meas_qubit_coords": [8 coords]}` — same 6-item schema as the 72Q surface sets (`rounds`; `*_qubit_coords`; no `qubit_order`).
- **Per-instance semantics** (Overview): one decoded instance = "a single point in the figure that shows the decay of the expectation value of the logical observable (in this case, **`X` observable**)" — note the example figure here is the X observable (the 72Q sets' READMEs say Z).

## (b) File inventory + formats
Per leaf instance `data_dir = dataset_dir/patch_dir/basis_dir/cycles_dir` (README File contents — wording identical to the other releases):
`circuit_ideal.stim`, `circuit_noisy_si1000.stim` (stim circuit format); `measurements.b8` (bits_per_shot = "the total number of measurements in the circuit"); `sweep_bits.b8` (= number of sweep bits, from `circuit_ideal.stim`); `detection_events.b8` (= number of detectors, from `circuit_ideal.stim`); `obs_flips_actual.b8` (= number of observables, "which in this dataset is always 1"); `metadata.json`; `decoding_results/<pathway>/{error_model.dem, obs_flips_predicted.b8}` (predicted flips: 1 bit/shot).
- **b8 packing** (verbatim, all kinds): "Each shot's data is byte aligned by padding up to a multiple of 8 bits. Bits are packed into bytes in little endian order."
- **Sweep-bit semantics** (verbatim): "the sweep bits are used to initialize the data qubits into different patterns of 0s and 1s. These bits determine whether instructions like `CX sweep[0] 5` … are turned into an `X` gate or `I` gate on qubit 5."
- Per-instance detector/measurement counts: **not in the README**; read from `circuit_ideal.stim`. No per-instance directory listing was captured for this set (the collector found no `sample_00`), so file sizes are unverified here.

## (c) Logical observable
- Defined by `OBSERVABLE_INCLUDE` (+ `QUBIT_COORDS`) in `circuit_ideal.stim`; **exactly 1 observable** ("always 1").
- `obs_flips_actual.b8`: flips "compared to what it would have been if the circuit had executed noiselessly"; "the data that decoders are supposed to predict, hence the subscript `_actual`".
- **Per-shot logical-error recipe** (verbatim): "Whether a logical error occurred or not in any given shot can be determined by computing an XOR of this data with `obs_flips_actual.b8` data."

## (d) Noise model shipped
- `circuit_noisy_si1000.stim` — SI1000 circuit error model (Gidney et al., Quantum 5, 605 (2021)). **Parameter value not stated in the README**; read p from the circuit file.

## (e) Decoding pathways shipped — evaluator/baseline-only
Isolation contract: all `decoding_results/` artifacts are baselines/evaluator inputs only. Five pathways; note the ensembles here are **51**-wide (the 72Q sets use 101) and **Libra** appears only in this release:

| Pathway | Decoder | Prior |
|---|---|---|
| `correlated_matching_decoder_with_si1000_prior` | Correlated matching on sparse blossom [Higgott 2303.15933] + "a variant of the two-step re-weighting strategy" [Fowler 1310.0863] | SI1000 prior [Gidney et al.] |
| `correlated_matching_decoder_with_rl_optimized_prior` | same | RL-optimized [Sivak 2406.02700], (verbatim) "Optimized **jointly for all distance-3 and distance-5 patches** using the 13-cycle calibration data." |
| `harmony_decoder_with_si1000_prior` | Harmony [Shutty 2401.12434] "ensembling **51** correlated matching decoders" | SI1000 prior |
| `harmony_decoder_with_rl_optimized_prior` | same | RL-optimized prior |
| `libra_decoder_with_rl_optimized_prior` | Libra [Jones 2408.12135] "ensembling **51** correlated matching decoders" | RL-optimized prior |

- The RL prior is trained **jointly over d3+d5 patches** (vs per-patch/basis in isolation for the 72Q sets); **the d7 patch is not mentioned in the prior-training sentence** — how the d7 instances' RL-prior pathway was configured is not stated in the README.
- **No pij/detector-correlations prior and no uninformative-prior pathway shipped** (set2 is the only release with those); pij baselines here must be self-computed.
- DEM semantics (verbatim, same as the others): hyperedges in a weighted hypergraph over detectors; >2-detector mechanisms "contain suggested decompositions into edge-like errors."

## (f) Provenance recipes + references
- **Example 1 (m2d)**: `stim m2d --circuit circuit_ideal.stim --in measurements.b8 --in_format b8 --sweep sweep_bits.b8 --sweep_format b8 --out detection_events.b8 --out_format b8 --obs_out obs_flips_actual.b8 --obs_out_format b8` (stim 1.9+) — the ingestion-parity check for this set.
- **Example 2**: `stim analyze_errors --in circuit_noisy_si1000.stim --out error_model.dem` then `pymatching predict --dem … --in detection_events.b8 --in_format b8 --out obs_flips_predicted.b8 --out_format b8` (pymatching 2.0+).
- **References cited:** [1] Higgott et al. 2303.15933 (sparse blossom); [2] Fowler 1310.0863; [3] Gidney et al., Quantum 5, 605 (2021) (SI1000); [4] Sivak et al. 2406.02700 (RL priors; related Sycamore dataset doi:10.5281/zenodo.11403594); [5] Shutty et al. 2401.12434 (Harmony); [6] Google QAI, Nature 614, 676 (2023) (related dataset zenodo 6804040); [7] Jones 2408.12135 (**Libra** — matching synthesis). Additional resources: Stim, PyMatching.

## (g) Relevance to qec_twin
- **Role: the destination (C = R3).** ADR 0007 Context 3 / Decision 2: "the d=5/d=7 surface-code twin on the scalable carrier" is the declared target, entered only after the carrier's swap gate (do()-preservation on overlapping exact instances) and the C-entry gates. The four d5 patches (49q) and the d7 patch (97q) are that target's data. Nothing here fits the ≤~15q `forward/exact` backend whole-code: even d3 is 17q — **windows only** (the R2-lite-b regime), and d5/d7 are strictly post-ADR-0008.
- **The Λ ladder.** d3 (×9 patches) → d5 (×4) → d7 (×1) on one device is the canonical input for the METRICS.md hardware-ledger Λ (error-suppression factor) and ε_d (logical error per round) rows — the field-standard scaling claim format (Willow's headline). Any twin-prior %ΔLER at d5/d7 would be scored against the shipped RL/SI1000 arms under a frozen named decoder.
- **R2-lite-b side use.** The nine d3 patches give spatial replication (9 locations × 2 bases × round levels) for window-closure audits (M2-style) across the 105Q grid — a richer located non-locality map than the 72Q sets — with the same deliverable framing: closure violations are reported as misspecification directions consistent with documented crosstalk/leakage, never attributed.
- **No drift axis.** With no sample tier and no acquisition-time statement, this release supports no sample-indexed drift work (M5/H4-adjacent analyses live in the rep set and set2). Cross-patch variation here is *spatial*, not temporal.
- **Claim discipline:** R2-lite forbidden claims verbatim until the C-entry gates fire — no `do()` on hardware, no mechanism attribution, no Born/CPTP-learning claims; shipped priors/predictions evaluator/baseline-only. The d=5/d=7 ambition is sequenced (trigger-gated behind ADR 0008 + swap gate), never dropped.
- **Reader caveats:** patch list is from the captured listing (complete at 14 + README); round-level inventory unknown beyond r90 + "r10, r30, etc."; shots confirmed only for the cached d3 sample (50,000); no per-instance file sizes captured; d7 prior-training configuration unstated.
