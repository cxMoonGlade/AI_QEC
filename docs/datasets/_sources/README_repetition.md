# *google_72Q_repetition_code_d29*

1. [Overview](#overview)
2. [File contents](#file-contents)
3. [Decoding pathways](#decoding-pathways)
4. [Usage examples](#usage-examples)
5. [Additional resources](#additional-resources)
6. [References](#references)

## Overview <a name="overview"></a>
This dataset contains repetition code data for memory experiments in `X` and `Z` bases, organized as follows:
```
dataset_dir
├── X
│   ├── sample_00
│   ├── sample_01
│   └── ...
├── Z
│   ├── sample_00
│   ├── sample_01
│   └── ...
└── README
```
where the subdirectories named `sample_00`, ..., `sample_99`, store the data that was sequentially acquired in an experiment. Each sample contains `100,000` shots, and every shot consists of `1,000` cycles of error correction.

The distance-29 repetition code was layed out on a square grid of qubits in the following configuration:

![patches](layout.png)

Below is the description of the directory contents for a single dataset sample:
```
sample_dir
├── circuit_ideal.stim
├── circuit_noisy_si1000.stim
├── measurements.b8
├── sweep_bits.b8
├── detection_events.b8
├── obs_flips_actual.b8
├── metadata.json
└── decoding_results
    ├── pathway_1
    │   ├── error_model.dem
    │   └── obs_flips_predicted.b8
    ├── pathway_2
    │   ├── error_model.dem
    │   └── obs_flips_predicted.b8
    └── ...
```

## File contents <a name="file-contents"></a>

___
```
...
├── circuit_ideal.stim
...
```
The QEC circuit, including annotations describing how detection events are computed from the measurement record and what the logical observable is.

Stored in `stim` circuit format, see [The Stim Circuit File Format](https://github.com/quantumlib/Stim/blob/main/doc/file_format_stim_circuit.md).
___
```
...
├── circuit_noisy_si1000.stim
...
```
The noisy version of the QEC circuit with [SI1000](https://quantum-journal.org/papers/q-2021-12-20-605/) circuit error model.
___
```
...
├── measurements.b8
...
```
The actual measurement data collected from the device. The detection event data and observable flip data is derived from this data.

Stored in `b8` format, see [The b8 Format](https://github.com/quantumlib/Stim/blob/main/doc/result_formats.md#b8). In the parsing function, the `bits_per_shot` argument should be the total number of measurements in the circuit. Each shot's data is byte aligned by padding up to a multiple of 8 bits. Bits are packed into bytes in little endian order.
___
```
...
├── sweep_bits.b8
...
```
Circuit configuration data, describing which sweep bits were set in each shot. Specifically, the sweep bits are used to initialize the data qubits into different patterns of 0s and 1s. These bits determine whether instructions like `CX sweep[0] 5` in the circuit file are turned into an `X` gate or `I` gate on qubit 5.  Detection event data and observable flip data is derived from this data.

Stored in `b8` format, see [The b8 Format](https://github.com/quantumlib/Stim/blob/main/doc/result_formats.md#b8). In the parsing function, the `bits_per_shot` argument should be the number of sweep bits in the circuits, which can be determined from `circuit_ideal.stim`. Each shot's data is byte aligned by padding up to a multiple of 8 bits. Bits are packed into bytes in little endian order.
___
```
...
├── detection_events.b8
...
```
Detection event data, describing which detectors flipped and did not flip in each QEC shot. The detection event data is used by the decoders to predict whether or not the logical observable was flipped. The bits in every shot should be interpreted as `0` meaning "detector was not flipped" and `1` meaning "detector was flipped".

Stored in `b8` format, see [The b8 Format](https://github.com/quantumlib/Stim/blob/main/doc/result_formats.md#b8). In the parsing function, the `bits_per_shot` argument should be the number of detectors in the circuit, which can be determined from `circuit_ideal.stim`. Each shot's data is byte aligned by padding up to a multiple of 8 bits. Bits are packed into bytes in little endian order.
___
```
...
├── obs_flips_actual.b8
...
```
Observable flip data, indicating if the observable was flipped compared to what it would have been if the circuit had executed noiselessly. The bits in every shot should be interpreted as `0` meaning "observable was not flipped" (i.e. the observed result agreed with the result that would occur if there was no noise) and `1` meaning "observable was flipped".

This is the data that decoders are supposed to predict, hence the subscript `_actual` as opposed to `_predicted`.

Stored in `b8` format, see [The b8 Format](https://github.com/quantumlib/Stim/blob/main/doc/result_formats.md#b8). In the parsing function, the `bits_per_shot` argument should be the number of observables in the circuit, which in this dataset is always 1.
___
```
...
├── metadata.json
...
```
Contains additional information for convenience. The `json` dictionary includes:
1. Basis in which the repetition code is prepared and measured
2. Code distance
3. Number of QEC cycles
4. Number of QEC shots
5. Coordinates of the "data qubits"
6. Coordinates of the "measure qubits", i.e. auxiliary qubits used to measure the stabilizers
7. Qubit order in the repetition code chain
___
```
...
├── decoding_results
│   ├── pathway_1
│   │   ├── error_model.dem
│   │   └── obs_flips_predicted.b8
│   ├── pathway_2
│   │   ├── error_model.dem
│   │   └── obs_flips_predicted.b8
│   └── ...
...
```
A directory containing the decoding results. Each decoding pathway resides in the separate subdirectory. The pathways typically differ from each other in the choice of the decoder or the error model.

The detector error model (DEM) `error_model.dem` can be used as a prior to configure a decoder. It represents error mechanisms as hyperedges in a weighted hypergraph where nodes correspond to detectors. Error mechanisms that set off more than two detectors also contain suggested decompositions into edge-like errors (errors with at most two detectors).

Stored in `dem` format, see [The Detector Error Model File Format](https://github.com/quantumlib/Stim/blob/main/doc/file_format_dem_detector_error_model.md).

The `obs_flips_predicted.b8` file contains the observable flips predicted by the decoder. The bits in every shot should be interpreted as `0` meaning "observable was not flipped" (i.e. the observed result agreed with the result that would occur if there was no noise) and `1` meaning "observable was flipped". Whether a logical error occurred or not in any given shot can be determined by computing an XOR of this data with `obs_flips_actual.b8` data.

Stored in `b8` format, see [The b8 Format](https://github.com/quantumlib/Stim/blob/main/doc/result_formats.md#b8). In the parsing function, the `bits_per_shot` argument should be the number of observables in the circuit, which in this dataset is always 1.

## Decoding pathways <a name="decoding-pathways"></a>

| Pathway | Decoder | Prior |
| ------- | ------- | ----- |
| MWPM_decoder_with_RL_optimized_prior | Minimum-weight perfect matching decoder [[1]](#1). | Prior optimized with reinforcement learning [[2]](#2) for the MWPM decoder. $10^4$ (out of $10^7$ total) shots from `sample_00` were used as the training data. Training involved 25 sensors-codes of distance 5 subsampled from the target code.

## Usage examples <a name="usage-examples"></a>

### Example 1

`detection_events.b8` and `obs_flips_actual.b8` can be derived from the `measurements.b8` and `sweep_bits.b8` with the following Stim command:

    # Assumes a linux-like command line environment.
    # Assumes a python environment with stim 1.9+ installed.
    # Assumes your working directory is the relevant sample directory.

    stim m2d \
        --circuit circuit_ideal.stim \
        --in measurements.b8 \
        --in_format b8 \
        --sweep sweep_bits.b8 \
        --sweep_format b8 \
        --out detection_events.b8 \
        --out_format b8 \
        --obs_out obs_flips_actual.b8 \
        --obs_out_format b8

### Example 2

Here we illustrate the decoding workflow with an open-source [PyMatching](https://github.com/oscarhiggott/PyMatching) decoder and a simple [SI1000](https://quantum-journal.org/papers/q-2021-12-20-605/) circuit error model which mimics the hierarchy of physical error rates in superconducting qubits.


First, we create a directory for this decoding pathway:

    # Assumes a linux-like command line environment.
    # Assumes your working directory is the relevant sample directory.

    pymatching_dir="decoding_results/pymatching_decoder_with_si1000_prior"
    mkdir $pymatching_dir

Detector error model can be extracted from the noisy Stim circuit as follows:

    # Assumes a python environment with stim 1.9+ installed.

    stim analyze_errors \
        --in circuit_noisy_si1000.stim \
        --out $pymatching_dir/error_model.dem

Finally, the data can be decoded with PyMatching as follows:

    # Assumes a python environment with pymatching 2.0+ installed.

    pymatching predict \
        --dem $pymatching_dir/error_model.dem \
        --in detection_events.b8 \
        --in_format b8 \
        --out $pymatching_dir/obs_flips_predicted.b8 \
        --out_format b8


## Additional resources <a name="additional-resources"></a>

 [Stim](https://github.com/quantumlib/Stim) repository on GitHub and the [Getting Started Notebook](https://github.com/quantumlib/Stim/blob/main/doc/getting_started.ipynb).

[PyMatching](https://github.com/oscarhiggott/PyMatching) repository on GitHub.

[Related dataset](https://doi.org/10.5281/zenodo.11403594) acquired on Google's Sycamore processor, released in Ref. [[2]](#2).

[Another related dataset](https://zenodo.org/records/6804040) acquired on Google's Sycamore processor, released in Ref. [[3]](#3).

## References <a name="references"></a>

<a id="1">[1]</a>
E. Dennis *et al.*,
[Topological quantum memory](https://pubs.aip.org/aip/jmp/article-abstract/43/9/4452/230976/Topological-quantum-memory?redirectedFrom=fulltext)
J. Math. Phys. 43, 4452–4505 (2002)

<a id="2">[2]</a>
V. Sivak *et al.*,
[Optimization of decoder priors for accurate quantum error correction](https://arxiv.org/abs/2406.02700)
arXiv:2406.02700 (2024)

<a id="3">[3]</a>
Google Quantum AI,
[Suppressing quantum errors by scaling a surface code logical qubit](https://www.nature.com/articles/s41586-022-05434-1)
Nature 614, 676–681 (2023)
