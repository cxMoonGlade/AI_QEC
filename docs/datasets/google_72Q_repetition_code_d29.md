# Dataset note — `google_72Q_repetition_code_d29` (Willow 72Q, distance-29 repetition code)

> Dataset reading note in the house format (full read of the shipped README +
> one real `metadata.json` + captured directory listings, all cached under
> `docs/datasets/_sources/`). Centerpiece: **Relevance to qec_twin** — this is the
> **R2-lite-a** dataset (ADR 0007), the one real-hardware release that fits the
> `forward/exact` backend today via 11–15q sliding windows.

## Metadata
- **Local path.** `/home/cx/Document/google_72Q_repetition_code_d29/` (top level: `README/`, `X/`, `Z/`).
- **Source.** Zenodo 13273331 family, CC-BY (per ADR 0007 References; the cached README carries **no DOI or host-paper statement itself**). Project docs attribute it to Google Willow, arXiv:2408.13687 / Nature s41586-024-08449-y (`docs/metric_results.md`, M1 pre-registration header).
- **Cached originals.** `_sources/README_repetition.md`, `_sources/google_72Q_repetition_code_d29.metadata.sample.json`, `_sources/directory_listings.txt`. The README references a `layout.png` (chain layout on the square grid) that is **not cached** — only the markdown was copied.
- **Note.** `*:Zone.Identifier` files appear next to every data file in the local tree (Windows download ADS artifacts); readers must ignore them.

## Executive summary
Memory experiments of a **distance-29 repetition code** (29 data + 28 measure qubits, a 57-qubit chain snaking over a square grid of the 72Q device) in **both X and Z bases**, organized as `{X,Z}/sample_00 … sample_99/` — per README Overview, "the subdirectories named `sample_00`, ..., `sample_99`, store the data that was sequentially acquired in an experiment. Each sample contains `100,000` shots, and every shot consists of `1,000` cycles of error correction." Corpus: 2 bases × 100 samples × 10⁵ shots = **2×10⁷ shots**, 1000 cycles each. Each sample directory ships the stim circuit pair (ideal + SI1000-noisy), raw `measurements.b8`, `sweep_bits.b8`, derived `detection_events.b8` and `obs_flips_actual.b8`, a small `metadata.json`, and one decoding pathway (MWPM + RL-optimized prior). The sequential sample index is the natural drift axis; the README contains **no calibration-freshness statement** (unlike surface set1/set2).

## (a) Experiment design
- **Code/bases.** Repetition code, d=29, memory experiments in `X` and `Z` bases (basis is the *top-level* directory — opposite nesting to the surface sets). X-basis = phase-flip protection, Z-basis = bit-flip (not stated in README; the README only names the bases).
- **Layout.** README Overview: "The distance-29 repetition code was layed out on a square grid of qubits in the following configuration" + `layout.png` (not cached). `metadata.json` gives the actual chain: 29 `data_qubits`, 28 `meas_qubits`, plus `qubit_order` (see anomaly below).
- **Hierarchy** (README Overview + listings): `dataset_dir/{X,Z}/sample_NN/<files>` — no patch level, no per-rounds level; every shot has the same 1000 cycles.
- **Counts.** 100 samples per basis (`sample_00`–`sample_99`; the captured listing's link count on `X/` — 102 = 2 + 100 subdirs — confirms exactly 100). 10⁵ shots/sample; 1000 cycles/shot.
- **Acquisition.** "data that was sequentially acquired in an experiment" (Overview) — a sequentially indexed sample series, i.e. sample index ≈ wall-clock order. **Calibration freshness: not stated anywhere in this README** (the deliberately mixed-calibration policy belongs to surface set2; do not import it here).
- **Metadata sample** (`basis="X"` instance): `distance=29`, `cycles=1000`, `shots=100000`, `data_qubits` (29 coords), `meas_qubits` (28 coords), `qubit_order`.
- **⚠ Anomaly (hand-verified, flag for M1).** The cached `qubit_order` has **58 entries**, not 57: it alternates data/measure along the chain and ends `..., [10, 6], [10, 5], [11, 5]` — the trailing `[11, 5]` appears in **neither** `data_qubits` **nor** `meas_qubits`. README File-contents item 7 only says "Qubit order in the repetition code chain". Purpose of the extra qubit is **not stated**. A reader must not assume `len(qubit_order) == len(data)+len(meas)`. (M1 P1 gates on detector/measurement/sweep/observable counts, not on `qubit_order`, so no gate impact — but record it.)

## (b) File inventory + formats
Per sample directory (README File contents):

| File | Format | `bits_per_shot` (README wording) | This dataset (derived from listed file sizes, sample_00) |
|---|---|---|---|
| `circuit_ideal.stim` | stim circuit | — | 2,293,023 B; carries detector + observable annotations |
| `circuit_noisy_si1000.stim` | stim circuit | — | 3,619,399 B; SI1000 noisy version |
| `measurements.b8` | b8 | "the total number of measurements in the circuit" | 350,800,000 B = **3508 B/shot** → 28,057 measurements (= 28×1001 + 29; 3508 = ceil(28057/8)) |
| `sweep_bits.b8` | b8 | "the number of sweep bits in the circuits, which can be determined from `circuit_ideal.stim`" | 400,000 B = **4 B/shot** → 29 sweep bits (one per data qubit; exact 29 to be confirmed from the circuit at M1) |
| `detection_events.b8` | b8 | "the number of detectors in the circuit" | 350,700,000 B = **3507 B/shot** → 28,056 detectors (= 28 measure qubits × 1002 detector layers: 1 init + 1000 bulk + 1 final) |
| `obs_flips_actual.b8` | b8 | "the number of observables in the circuit, which in this dataset is always 1" | 100,000 B = **1 B/shot** → 1 observable |
| `metadata.json` | json | — | keys: `basis`, `distance`, `cycles`, `shots`, `data_qubits`, `meas_qubits`, `qubit_order` (1,039 B) |
| `decoding_results/<pathway>/error_model.dem` | stim DEM | — | one pathway shipped (link count on `decoding_results` = 3 → exactly 1 subdir) |
| `decoding_results/<pathway>/obs_flips_predicted.b8` | b8 | number of observables (= 1) | 1 B/shot |

- **b8 packing** (verbatim, identical for all b8 kinds): "Each shot's data is byte aligned by padding up to a multiple of 8 bits. Bits are packed into bytes in little endian order."
- **Sweep-bit semantics** (verbatim): "the sweep bits are used to initialize the data qubits into different patterns of 0s and 1s. These bits determine whether instructions like `CX sweep[0] 5` in the circuit file are turned into an `X` gate or `I` gate on qubit 5."
- **Derived-data chain** (File contents): `detection_events.b8` and `obs_flips_actual.b8` are *derived* from `measurements.b8` + `sweep_bits.b8`.
- Volume: ≈ 701.5 MB of b8 per sample → ≈ **140 GB** for the full 200-sample corpus (derived estimate, not a README number).

## (c) Logical observable
- Defined in `circuit_ideal.stim`: "The QEC circuit, including annotations describing how detection events are computed from the measurement record and what the logical observable is" (File contents). (This README, unlike the surface ones, does not name `OBSERVABLE_INCLUDE` explicitly, but that is the stim annotation in question.)
- **Exactly 1 observable** per circuit: "the number of observables in the circuit, which in this dataset is always 1."
- `obs_flips_actual.b8` (verbatim): "indicating if the observable was flipped compared to what it would have been if the circuit had executed noiselessly … This is the data that decoders are supposed to predict, hence the subscript `_actual` as opposed to `_predicted`."
- **Per-shot logical-error recipe** (verbatim, from the `obs_flips_predicted.b8` description): "Whether a logical error occurred or not in any given shot can be determined by computing an XOR of this data with `obs_flips_actual.b8` data." I.e. per-shot logical error = `obs_flips_predicted XOR obs_flips_actual`.

## (d) Noise model shipped
- `circuit_noisy_si1000.stim`: "The noisy version of the QEC circuit with SI1000 circuit error model" (link: Gidney et al., Quantum 5, 605 (2021)). **The README does not state the SI1000 parameter value.** The project's M1 pre-registration (`docs/metric_results.md`, P8) records the shipped circuit as SI1000(**p = 1e-3**), to be verified against the circuit file at M1 — treat p=1e-3 as pre-registered, not README-sourced.

## (e) Decoding pathways shipped — evaluator/baseline-only
Under the isolation contract, everything in `decoding_results/` (DEM priors, predicted flips) is a **baseline/evaluator artifact**: it configures comparison decoders and scores %ΔLER; it is never an input to the label-free learner.

| Pathway | Decoder | Prior (verbatim) |
|---|---|---|
| `MWPM_decoder_with_RL_optimized_prior` | Minimum-weight perfect matching [Dennis et al. 2002] | "Prior optimized with reinforcement learning [Sivak et al. 2406.02700] for the MWPM decoder. $10^4$ (out of $10^7$ total) shots from `sample_00` were used as the training data. Training involved 25 sensors-codes of distance 5 subsampled from the target code." |

- This is the **only** shipped pathway (confirmed by the directory link count). **No SI1000-prior or pij/correlation-prior pathway is shipped** for this dataset — Usage example 2 shows how to build the SI1000 one yourself; the pij baseline for M3/M4 must be self-computed (Spitz Eq. 13).
- DEM semantics (verbatim): "It represents error mechanisms as hyperedges in a weighted hypergraph where nodes correspond to detectors. Error mechanisms that set off more than two detectors also contain suggested decompositions into edge-like errors (errors with at most two detectors)."

## (f) Provenance recipes + references
- **Example 1 (m2d)** — regenerate detection events + observable flips from raw data (the M1 P2 bit-for-bit target):
  `stim m2d --circuit circuit_ideal.stim --in measurements.b8 --in_format b8 --sweep sweep_bits.b8 --sweep_format b8 --out detection_events.b8 --out_format b8 --obs_out obs_flips_actual.b8 --obs_out_format b8` (stim 1.9+).
- **Example 2 (baseline pathway)** — `stim analyze_errors --in circuit_noisy_si1000.stim --out error_model.dem`, then `pymatching predict --dem … --in detection_events.b8 --in_format b8 --out obs_flips_predicted.b8 --out_format b8` (pymatching 2.0+).
- **References cited:** [1] Dennis et al., J. Math. Phys. 43, 4452 (2002) (MWPM); [2] Sivak et al., arXiv:2406.02700 (RL priors; related Sycamore dataset doi:10.5281/zenodo.11403594); [3] Google Quantum AI, Nature 614, 676 (2023) (related Sycamore dataset zenodo 6804040). Additional resources: Stim, PyMatching repos.

## (g) Relevance to qec_twin
- **Role: R2-lite-a, NOW** (ADR 0007 Decision 2). The d=29 chain is quasi-1D and gate-local: sliding windows of 5 data + 6 measure qubits (11q), up to 7 + 8 (15q), sit inside the §1.1b exact-backend window — this is the only flagship release reachable **without** `forward/scalable`.
- **Milestones it feeds:** M1 ingestion parity (pre-registered 2026-06-09, `docs/metric_results.md` — P1 structure, P2 m2d bit-for-bit, P3 detection fraction, P4 pij support); M2 window-closure audit (the 11q-boundary correlation-mass map is itself a deliverable); M3 held-out per-shot syndrome NLL vs naive + pij priors; M4 twin-calibrated `.dem` + frozen pymatching %ΔLER (published rep-code bar: dMLE 30.6%; the shipped RL pathway is a second reference point); M5 drift slice over the sequential `sample_NN` index with finite-sample band coverage.
- **Contexts stand-in:** X/Z bases × 100 sequential samples are the hardware stand-in for the probe-richness ladder — few fixed contexts ⇒ wide alias; M3's fallback alias analysis quantifies exactly this.
- **Cross-check vs M1 pre-registration — all consistent, no discrepancies:** 28,056 detectors = 28×1002 ✓ (350,700,000 B = 3507 B/shot × 10⁵); 28,057 measurements = 28×1001+29 ✓ (3508 B/shot; sizes alone bound bits to [28,057, 28,064] — exact value confirmed at M1 from the circuit); 29 sweep bits ✓ (4 B/shot; sizes bound to [25, 32]); 1 observable ✓; b8 bytes/shot 3507/3508/4/1 ✓; 100 samples/basis ✓; 10⁵ shots/sample, 1000 cycles, d=29 ✓ (metadata); corpus 2×10⁷ ✓. SI1000 p=1e-3 is *absent from the README* (not contradicted). The one surprise is the 58-entry `qubit_order` with trailing `[11, 5]` (above).
- **Claim discipline (R2-lite restrictions, ADR 0007 Decision 1):** no `do()` / counterfactual / intervention claims on this data; no mechanism attribution (long-range pij tails are reported as **misspecification directions** feeding M2/H2, never "this is leakage" — H3-relevant but unattributed); no Born-generation / CPTP-learning claims; shipped priors/predictions used as baselines only. The drift leg (M5) satisfies neither Gate B nor the H4 controlled-sim gate.
