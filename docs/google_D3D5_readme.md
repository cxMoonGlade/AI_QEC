google_72Q_surface_code_d3_d5_set1
Overview
File contents
Decoding pathways
Usage examples
Additional resources
References
Overview <a name="overview"></a>
This dataset is organized in a nested directory structure according to certain useful attributes of the QEC memory experiments:
```
dataset\\\_dir
├── sample\\\_dir
│   ├── patch\\\_dir
│   │   ├── basis\\\_dir
│   │   │   ├── cycles\\\_dir
│   │   │   │   └── ...
│   │   │   └── ...
│   │   └── ...
│   └── ...
└── ...
```
The `dataset\\\_dir` contains subdirectories for each sample, named `sample\\\_00`, `sample\\\_01`, etc. A single such sample can be thought of as a collection of QEC data acquired in one experiment.
The last 16 experiments in this dataset were performed sequentially during the course of 15 hours.
The `sample\\\_dir` contains subdirectories for different surface code patches:
![patches](patches.png)
A patch corresponds to a particular set of qubits involved in the code. It is characterized by the code distance and its spatial location on the grid of qubits. The naming convention is chosen to indicate the code distance and the location of the center qubit of the patch.
The `patch\\\_dir` contains subdirectories corresponding to different bases in which the logical qubit is prepared and measured. In this dataset, we have  bases `X` and `Z`. Note that the `X` or `Z` basis is an arbitrary designation for the XZZX surface code used here. For each patch, one can inspect the corresponding `circuit\\\_ideal.stim` file (described below), and more specifically, the `OBSERVABLE\\\_INCLUDE` and `QUBIT\\\_COORDS` annotations to determine the protected observable.
The `basis\\\_dir` contains subdirectories for the number of QEC cycles (rounds) in each particular memory experiment: `r05`, `r10`, etc.
At this final depth (corresponding to a particular sample, patch, basis, and number of cycles), we store the actual data organized as described in the next section. This data, when decoded, results in a single point in the figure that shows the decay of the expectation value of the logical observable (in this case, `Z` observable):
![logicals](logicals.png)

Below is the description of the directory contents for a single decoding instance, corresponding to a particular sample, patch, basis, and number of cycles, i.e. here `data\\\_dir = dataset\\\_dir/sample\\\_dir/patch\\\_dir/basis\\\_dir/cycles\\\_dir`:
```
data\\\_dir
├── circuit\\\_ideal.stim
├── circuit\\\_noisy\\\_si1000.stim
├── measurements.b8
├── sweep\\\_bits.b8
├── detection\\\_events.b8
├── obs\\\_flips\\\_actual.b8
├── metadata.json
└── decoding\\\_results
    ├── pathway\\\_1
    │   ├── error\\\_model.dem
    │   └── obs\\\_flips\\\_predicted.b8
    ├── pathway\\\_2
    │   ├── error\\\_model.dem
    │   └── obs\\\_flips\\\_predicted.b8
    └── ...
```
File contents <a name="file-contents"></a>
---
```
...
├── circuit\\\_ideal.stim
...
```
The QEC circuit, including annotations describing how detection events are computed from the measurement record and what the logical observable is.
Stored in `stim` circuit format, see The Stim Circuit File Format.
---
```
...
├── circuit\\\_noisy\\\_si1000.stim
...
```
The noisy version of the QEC circuit with SI1000 circuit error model.
---
```
...
├── measurements.b8
...
```
The actual measurement data collected from the device. The detection event data and observable flip data is derived from this data.
Stored in `b8` format, see The b8 Format. In the parsing function, the `bits\\\_per\\\_shot` argument should be the total number of measurements in the circuit. Each shot's data is byte aligned by padding up to a multiple of 8 bits. Bits are packed into bytes in little endian order.
---
```
...
├── sweep\\\_bits.b8
...
```
Circuit configuration data, describing which sweep bits were set in each shot. Specifically, the sweep bits are used to initialize the data qubits into different patterns of 0s and 1s. These bits determine whether instructions like `CX sweep\\\[0] 5` in the circuit file are turned into an `X` gate or `I` gate on qubit 5.  Detection event data and observable flip data is derived from this data.
Stored in `b8` format, see The b8 Format. In the parsing function, the `bits\\\_per\\\_shot` argument should be the number of sweep bits in the circuits, which can be determined from `circuit\\\_ideal.stim`. Each shot's data is byte aligned by padding up to a multiple of 8 bits. Bits are packed into bytes in little endian order.
---
```
...
├── detection\\\_events.b8
...
```
Detection event data, describing which detectors flipped and did not flip in each QEC shot. The detection event data is used by the decoders to predict whether or not the logical observable was flipped. The bits in every shot should be interpreted as `0` meaning "detector was not flipped" and `1` meaning "detector was flipped".
Stored in `b8` format, see The b8 Format. In the parsing function, the `bits\\\_per\\\_shot` argument should be the number of detectors in the circuit, which can be determined from `circuit\\\_ideal.stim`. Each shot's data is byte aligned by padding up to a multiple of 8 bits. Bits are packed into bytes in little endian order.
---
```
...
├── obs\\\_flips\\\_actual.b8
...
```
Observable flip data, indicating if the observable was flipped compared to what it would have been if the circuit had executed noiselessly. The bits in every shot should be interpreted as `0` meaning "observable was not flipped" (i.e. the observed result agreed with the result that would occur if there was no noise) and `1` meaning "observable was flipped".
This is the data that decoders are supposed to predict, hence the subscript `\\\_actual` as opposed to `\\\_predicted`.
Stored in `b8` format, see The b8 Format. In the parsing function, the `bits\\\_per\\\_shot` argument should be the number of observables in the circuit, which in this dataset is always 1.
---
```
...
├── metadata.json
...
```
Contains additional information for convenience. The `json` dictionary includes:
Basis in which the logical qubit is prepared and measured
Code distance
Number of QEC cycles
Number of QEC shots
Coordinates of the "data qubits"
Coordinates of the "measure qubits", i.e. auxiliary qubits used to measure the stabilizers
---
```
...
├── decoding\\\_results
│   ├── pathway\\\_1
│   │   ├── error\\\_model.dem
│   │   └── obs\\\_flips\\\_predicted.b8
│   ├── pathway\\\_2
│   │   ├── error\\\_model.dem
│   │   └── obs\\\_flips\\\_predicted.b8
│   └── ...
...
```
A directory containing the decoding results. Each decoding pathway resides in the separate subdirectory. The pathways typically differ from each other in the choice of the decoder or the error model.
The detector error model (DEM) `error\\\_model.dem` can be used as a prior to configure a decoder. It represents error mechanisms as hyperedges in a weighted hypergraph where nodes correspond to detectors. Error mechanisms that set off more than two detectors also contain suggested decompositions into edge-like errors (errors with at most two detectors).
Stored in `dem` format, see The Detector Error Model File Format.
The `obs\\\_flips\\\_predicted.b8` file contains the observable flips predicted by the decoder. The bits in every shot should be interpreted as `0` meaning "observable was not flipped" (i.e. the observed result agreed with the result that would occur if there was no noise) and `1` meaning "observable was flipped". Whether a logical error occurred or not in any given shot can be determined by computing an XOR of this data with `obs\\\_flips\\\_actual.b8` data.
Stored in `b8` format, see The b8 Format. In the parsing function, the `bits\\\_per\\\_shot` argument should be the number of observables in the circuit, which in this dataset is always 1.
Decoding pathways <a name="decoding-pathways"></a>
Pathway	Decoder	Prior
correlated_matching_decoder_with_si1000_prior	Correlated matching decoder based on the sparse blossom matching engine [[1]](#1) with a variant of the two-step re-weighting strategy [[2]](#2).	SI1000 prior [[3]](#3), inspired by the typical hierarchy of physical error rates in the superconducting qubits.
correlated_matching_decoder_with_rl_optimized_prior	Same as correlated matching above.	Prior optimized with reinforcement learning [[4]](#4) for the correlated matching decoder. Optimized for each patch / basis in isolation using the 13-cycle calibration data.
harmony_decoder_with_si1000_prior	Harmony decoder [[5]](#5) ensembling 101 correlated matching decoders.	Same as SI1000 prior above.
harmony_decoder_with_rl_optimized_prior	Same as Harmony above.	Same as optimized prior above.

Usage examples <a name="usage-examples"></a>
Example 1
`detection\\\_events.b8` and `obs\\\_flips\\\_actual.b8` can be derived from the `measurements.b8` and `sweep\\\_bits.b8` with the following Stim command:
    # Assumes a linux-like command line environment.
Assumes a python environment with stim 1.9+ installed.
Assumes your working directory is the relevant sample directory.
    stim m2d \\
--circuit circuit\_ideal.stim \\
--in measurements.b8 \\
--in\_format b8 \\
--sweep sweep\_bits.b8 \\
--sweep\_format b8 \\
--out detection\_events.b8 \\
--out\_format b8 \\
--obs\_out obs\_flips\_actual.b8 \\
--obs\_out\_format b8


Example 2
Here we illustrate the decoding workflow with an open-source PyMatching decoder and a simple SI1000 circuit error model which mimics the hierarchy of physical error rates in superconducting qubits.

First, we create a directory for this decoding pathway:
    # Assumes a linux-like command line environment.
Assumes your working directory is the relevant sample directory.
    pymatching\_dir="decoding\_results/pymatching\_decoder\_with\_si1000\_prior"
mkdir $pymatching\_dir


Detector error model can be extracted from the noisy Stim circuit as follows:
    # Assumes a python environment with stim 1.9+ installed.
    stim analyze\_errors \\
--in circuit\_noisy\_si1000.stim \\
--out $pymatching\_dir/error\_model.dem


Finally, the data can be decoded with PyMatching as follows:
    # Assumes a python environment with pymatching 2.0+ installed.
    pymatching predict \\
--dem $pymatching\_dir/error\_model.dem \\
--in detection\_events.b8 \\
--in\_format b8 \\
--out $pymatching\_dir/obs\_flips\_predicted.b8 \\
--out\_format b8





Additional resources <a name="additional-resources"></a>
Stim repository on GitHub and the Getting Started Notebook.
PyMatching repository on GitHub.
Related dataset acquired on Google's Sycamore processor, released in Ref. [[4]](#4).
Another related dataset acquired on Google's Sycamore processor, released in Ref. [[6]](#6).
References <a name="references"></a>
<a id="1">[1]</a>
O. Higgot et al.,
Sparse blossom: correcting a million errors per core second with minimum-weight matching
arXiv:2303.15933 (2023)
<a id="2">[2]</a>
A. Fowler,
Optimal complexity correction of correlated errors in the surface code
arXiv:1310.0863 (2013)
<a id="3">[3]</a>
C. Gidney et al.,
A fault-tolerant honeycomb memory
Quantum 5, 605 (2021)
<a id="4">[4]</a>
V. Sivak et al.,
Optimization of decoder priors for accurate quantum error correction
arXiv:2406.02700 (2024)
<a id="5">[5]</a>
N. Shutty et al.,
Efficient near-optimal decoding of the surface code through ensembling
arXiv:2401.12434 (2024)
<a id="6">[6]</a>
Google Quantum AI,
Suppressing quantum errors by scaling a surface code logical qubit
Nature 614, 676–681 (2023)