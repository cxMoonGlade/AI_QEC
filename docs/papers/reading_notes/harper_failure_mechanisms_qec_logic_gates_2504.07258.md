# Full-text review — Harper et al., "Characterising the failure mechanisms of error-corrected quantum logic gates" (arXiv:2504.07258)

> **Provenance (2026-07-07): FULL-TEXT read (精读).** PDF `outputs/papers/2504.07258.pdf` → txt `outputs/papers/2504.07258.txt` (PyMuPDF, 16 pages, 71,358 chars). All §/Eq/Fig/Table refs from that text. [Figures not pixel-extracted — figure facts = captions + numbers stated in text.]

## Metadata [paper]
- **Authors**: Robin Harper, Constance Lainé, Evan Hockings, Campbell McLauchlan, Georgia M. Nixon, Benjamin J. Brown, Stephen D. Bartlett
- **Affiliations**: University of Sydney (Centre for Engineered Quantum Systems), UCL (London Centre for Nanotechnology), IBM Quantum (T.J. Watson + IBM Denmark)
- **Venue**: Nature Communications 17, 5039 (2026); arXiv:2504.07258v1 [quant-ph], 9 Apr 2025
- **Type**: Experiment (superconducting qubits) + numerical simulation (Stim/PyMatching)

## Executive summary [paper]
This paper experimentally characterizes the failure mechanisms of error-corrected logic gates on IBM's 156-qubit Heron r2 processor "Marrakesh" using the heavy-hex code (d=3). Two complementary experiments are performed: (1) a **memory experiment** quantifying logical survival over syndrome extraction rounds, and (2) a **stability experiment** benchmarking lattice-surgery logic gate fidelity. Two circuit innovations — parallel X+Z check measurement and reset elimination via Pauli frame update — improve memory survival from <90% to **96% per round**. The stability experiment shows below-threshold exponential decay with additional rounds. Through circuit-level noise modeling (Stim) fitted to experimental data, **measurement noise is identified as the dominant factor limiting fault-tolerant logic gate fidelity** — classical measurement error (p_c.meas = 4.2%) is the primary bottleneck. The paper reveals a **memory/stability trade-off**: more stability rounds reduce gate failure but increase memory decay, and the optimal balance depends on device noise parameters.

## Method (deep) [paper]

### Heavy-hex code on Heron
- **Code**: d=3 heavy-hex subsystem code on IBM 156-qubit Heron r2 "Marrakesh"
- **Code placement**: Optimized via simultaneous randomized benchmarking to identify highest-quality qubit blocks
- **Decoder**: Standard MWPM (PyMatching) populated with averaged device calibration data, no post-selection
- **Physical parameters**: T1 median 197.36 µs, T2 median 118.43 µs; 2Q gate median error ~0.35% (Heron-class, ~10× better than Eagle); measurement time 3–4 µs (substantially longer than Eagle's 768 ns combined meas+reset)

### Memory experiment
- Measures logical survival probability over t syndrome extraction rounds
- Two initial states: |0⟩ (Z-basis) and |+⟩ (X-basis); negligible basis asymmetry
- Fit: logical success probability = A·p^t + 0.5, where p is the decay factor
- Logical fidelity per round = (1+p)/2
- "Memory survival" plotted as 2p−1 (re-scaled from 1→0, giving straight lines on semi-log)

### Stability experiment
- Over-complete stabilizer checks whose product is constrained to +1; violation = undetected measurement errors
- Detection events: disagreement between consecutive stabilizer readings → fed to decoder
- Logical failure: one specific stabilizer fails every round with no detection events produced
- Failure probability: P_fail = B(d)·Γ^t (exponential in rounds t)
- Without reset: detectors compare outcomes 2 rounds apart (halves time-like distance but also halves measurement noise)

### Circuit innovations
1. **Parallel X+Z checks**: New syndrome extraction circuit measuring X and Z checks simultaneously in one round, using next-nearest-neighbor CNOT gates to mimic surface-code readout circuit on heavy-hex lattice; avoids hook errors without flag qubits in bulk. Circuit depth: 10 layers of 1Q+2Q gates between init and readout; parallelizable over all plaquettes.
   - Original circuit: 11.1 µs (sequential X then Z, with resets)
   - Improved (no reset): 3.2 µs
   - Improved (with reset): 5.4 µs
2. **Reset elimination**: Replace post-measurement reset with classical Pauli frame update (following Gehér et al. 2408.00758). On Marrakesh, reset is implemented as measurement + conditional X-gate → effectively a second measurement, doubling idling time. No appreciable difference observed between reset and no-reset circuits in stability — the doubled time-like distance from resets is cancelled by doubled measurement/idling noise.

### Noise model (circuit-level, for Stim simulation)
A circuit-level depolarizing model with parameters fitted via Nelder-Mead optimization:

| Parameter | Symbol | Fitted value |
|-----------|--------|--------------|
| Single-qubit gate depolarizing | p_1Q | 0.02% |
| Two-qubit gate depolarizing | p_2Q | 0.41% |
| Quantum measurement noise (Pauli-X before meas) | p_q.meas | 1.2% |
| Classical measurement error (wrong output) | p_c.meas | 4.2% |
| Idling depolarizing (during meas/reset) | p_idle | 1.2% |
| Reset error (Pauli-X after reset) | p_reset | 7.5% |

Constraint: p_q.meas = p_idle (quantum measurement noise ≈ idling during measurement time; consistent with device characterization in §IV C).

Each parameter is varied independently — from p⁰_i down to p⁰_i/100 in steps (1/2, 1/10, 1/100) — to assess sensitivity.

### Device characterization (§IV C)
1. **Simultaneous RB** (§IV C 1): Knill-variant RB with state randomization (randomly target |0⟩ or |1⟩) — eliminates nuisance parameter, detects measurement bias, reveals qubits with extreme SPAM errors that RB alone would miss. Operated simultaneously on 156 qubits; <1 minute QPU time.
2. **Mid-circuit measurement RB** (§IV C 2): Extension of simultaneous RB interleaving measurement rounds (4 Cliffords between measurements). Revealed that **spectator (data) qubits experience relaxation during measurement time** (not from measurement crosstalk per se, but from the idling duration). Example: qubit 90 fidelity drops from 0.998 to **0.983 per measurement cycle**. Dynamic decoupling partially mitigates but the fundamental limit is T1/T2 during the ~2 µs measurement window.
3. **Temporal consistency** (§IV C 3): Fixed-sequence RB interleaved between experiments to monitor qubit stability over hours/days. Detected a measurement readout shift at 15-hour mark that correlated with reduced logical fidelity.
4. **Crosstalk analysis** (§IV C 4): Adapted Harper-Flammia (PRX Quantum 4, 040311, 2023) circuit for heavy-hex with mid-circuit measurements. Circuit-level noise model broadly replicated; minor additional crosstalk observed but **at least an order of magnitude smaller than idling + classical measurement errors**. Heron r2 substantially improved over r1 (which had severe mid-circuit measurement crosstalk).

## The MECHANISM (for implementation) [paper → ours]

### Mechanisms described in the paper:
1. **Idling/dephasing during measurement**: Data qubits idle during mid-circuit measurement (~3–4 µs), experiencing T1/T2 relaxation. Modeled as depolarizing channel with p_idle on data qubits during measurement and reset operations of ancilla qubits. This is the dominant mechanism for **memory** infidelity.
2. **Classical measurement error**: Readout returns wrong value independent of qubit state (p_c.meas = 4.2%). This is the dominant mechanism for **stability** (logic gate) infidelity — measurement errors are the underlying cause of logical failures in the stability experiment.
3. **Quantum measurement noise**: Pauli-X on measurement qubit before readout (p_q.meas = 1.2%), attributed to measurement qubit idling during the measurement time.
4. **Gate depolarizing noise**: 1Q (0.02%) and 2Q (0.41%) depolarizing on data and ancilla qubits.
5. **Reset noise**: Pauli-X after reset (p_reset = 7.5%). Note: on Marrakesh, "reset" = measurement + conditional X → effectively a second measurement.

### Relevance to our project:
- **Maps onto our noise axes**: (1) idling/T1-T2 is a **coherent/incoherent single-qubit channel** — our `T1T2Channel` or amplitude-damping + dephasing; (2) measurement error is **classical readout assignment error** — our `readout_assignment` or Bayesian readout model; (3) 2Q depolarizing = our Pauli channel substrate.
- **Circuit-level model with fitted parameters**: The Table I parameters give us REAL DEVICE MAGNITUDES for a state-of-the-art superconducting processor — directly usable as ground-truth anchors for our controlled-teacher simulations.
- **Memory/stability trade-off**: This is a **decision-regret** / **do()-intervention** target: varying t (rounds) trades off gate-failure vs memory-decay. Our `knobs/` module's do() framework maps naturally onto this.
- **Key implication for our twin**: The paper identifies measurement noise as the DOMINANT bottleneck — this means our twin's ability to separate measurement noise from gate noise and idling noise is the critical identifiability challenge. If we can't resolve classical measurement error from quantum measurement noise + idling, we can't capture the dominant failure mode.

## The OBSERVABLE / metric [paper]

1. **Memory survival probability** = 2p−1 (re-scaled from logical success probability A·p^t + 0.5). The decay factor p maps to logical fidelity per round = (1+p)/2. This is effectively the **logical error rate per round** — our standard `logical_error_rate` metric.
2. **Stability failure probability** P_fail = B(d)·Γ^t. Fit to simple exponential (omitting first 2 rounds that lack full stabilizer information). The decay constant Γ characterizes below-threshold behavior.
3. **RB survival probability** ˆp(q, m, s, x) — per-qubit, per-sequence, per-length. Marginalized over sequences → exponential fit → average gate fidelity.
4. **Critical insight on observables**: The paper uses **detector correlations** (mutual information between qubit pairs) to check for non-circuit-model crosstalk (§IV C 4). This is the Harper-Flammia 2023 method. Key finding: the circuit-level model broadly holds, so the relevant observable for characterizing failure is the **deviation from circuit-model predictions**, not raw correlations.
5. **What's insufficient**: Raw detector correlations alone don't separate measurement noise from gate noise — the paper needs the full Stim noise model fitting to attribute failure to measurement vs gates vs idling. This is an **identifiability lesson**: a single observable (e.g., logical error rate) can't disentangle the failure mechanisms; you need the full noise model + parameter variation.

## Findings + numbers [paper]

| Finding | Number | Context |
|---------|--------|---------|
| Memory survival (original circuit) | <90% per round | Sequential X+Z + resets |
| Memory survival (improved, no reset) | **96% (|0⟩), 97% (|+⟩)** per round | Parallel X+Z, no resets |
| Circuit depth reduction | 11.1 µs → 3.2 µs | 3.5× speedup |
| Stability Γ (decay constant) | ~0.5–0.7 (estimated from Fig. 3) | Below-threshold |
| Reset vs no-reset difference | Negligible | Reset = measurement+X on Marrakesh |
| Dominant noise source | **Classical measurement error (4.2%)** | Limits stability |
| Secondary noise source | Idling during measurement (1.2%) | Limits memory |
| 2Q gate error benefit saturates | Improvement stops at p_2Q/10 | Memory + stability |
| Idling error benefit saturates | Improvement stops at p_idle/10 | Memory + stability |
| Measurement improvement | **Continues improving to p_meas/100** | Especially for stability |
| Reset quality improvement | Only helps stability "ur" circuit | Not as effective as measurement improvement |
| T1 median | 197.36 µs | Heron r2 |
| T2 median | 118.43 µs | Heron r2 |
| Measurement time | 3–4 µs | Substantial fraction of T1/T2 |
| Spectator fidelity loss per meas cycle | 0.998 → 0.983 | From RB with mid-circuit meas |

## Limitations [paper]
- **d=3 only** — small code distance; the memory/stability trade-off conclusions may differ at larger d (where memory improves exponentially with d, stability improves exponentially with t)
- **Heavy-hex code has no threshold** for memory experiments — different codes (Floquet, surface codes on heavy-hex) needed for arbitrary improvement
- **Single device** (Marrakesh, Heron r2) — results may not generalize to other processor architectures
- **Circuit-level depolarizing model** — assumes Markovian, stochastic noise; the paper acknowledges non-exponential behavior (flattening after ~15 rounds in Fig. 3) suggesting additional noise processes outside the model
- **Reset implementation specific to Marrakesh** (measurement + conditional X) — conclusions about reset vs no-reset may differ on devices with true physical resets
- **No leakage modeling** in the Stim simulation — leakage is documented in prior heavy-hex work (Sundaresan et al. 2023) but not included in this noise model
- **Static noise model** — temporal variation detected (Fig. 8) but not incorporated into the model
- **No closed-form theoretical bounds** — the memory/stability trade-off is characterized numerically; no analytic expression for optimal (d, t) given noise parameters

## Relevance to qec_twin [ours]

### Directly usable:
1. **Real device noise parameters** (Table I): These are calibrated magnitudes for state-of-the-art superconducting qubits — directly usable as controlled-teacher ground truth for our mechanisms.
2. **Circuit-level noise model structure**: The 6-parameter model (p_1Q, p_2Q, p_q.meas, p_c.meas, p_idle, p_reset) is a clean, minimal parameterization that captures the dominant failure modes. Our `forward/` substrate can implement this exactly.
3. **Memory/stability trade-off as a do()-target**: Our `knobs/` module could implement t-round variation as a do() intervention, with the ΔLER scored against this paper's exponential-fit predictions.
4. **RB-based device characterization protocol**: The state-randomized simultaneous RB protocol (§IV C 1) is a lightweight (~1 min QPU time) method to get per-qubit fidelity + measurement bias — potentially usable for our R2-lite hardware characterization.

### Corrections/insights for our work:
1. **Measurement noise is the dominant bottleneck — not gate noise.** If our twin focuses primarily on gate noise mechanisms (as most Pauli-noise models do), we miss the leading-order failure mode. Our `calibration/` learner MUST be able to separate classical measurement error from quantum noise.
2. **Idling during measurement ≠ gate error.** The paper shows that spectator qubit fidelity loss during measurement (0.998→0.983 per cycle) is from T1/T2 relaxation during the measurement *duration*, not from crosstalk. Our mechanisms should model this as a distinct idling channel, not lump it into gate noise.
3. **The circuit-level model broadly holds** — crosstalk deviations are at least 10× smaller than idling + measurement errors. This justifies our choice of independent (non-crosstalk) Pauli channels as the first-order model.
4. **Reset elimination via Pauli frame update** is a practical circuit optimization that substantially reduces idling — our forward model should support detector patterns with 2-round spacing (not just consecutive-round comparison).

### Open questions for our work:
1. Can our `calibration/` learner **separate classical measurement error (p_c.meas) from quantum measurement noise (p_q.meas)** given only logical-level observations? This is a non-trivial identifiability question — the paper needs full Stim parameter fitting to do it.
2. At d=3, memory and stability are comparable failure rates. At larger d (our target d=5, d=7), the trade-off shifts — does measurement noise remain dominant, or does idling/gate noise catch up?
3. The paper finds p_reset = 7.5% but reset quality doesn't matter much because reset = measurement on Marrakesh. For our controlled-teacher, we should model "true physical reset" as distinct from "measurement-based reset" — they have different noise signatures.

## How to use / trust + open questions [ours]
- **Trust level**: High — Nature Communications published; detailed methods section; experimental data on real hardware; simulation corroboration. The noise parameters (Table I) are fitted, not directly measured — trust as **(b) prediction-band** ground truth, not **(a) exact**. Figure facts not pixel-extracted; all numbers from text/captions.
- **GT-feasibility**: The circuit-level noise model is straightforward to implement in our forward substrate. The memory and stability circuits can be replicated in Stim (the paper uses Stim + PyMatching). An independent ground-truth check would be: (a) reproduce the memory decay curve using our own forward + decoder on the same noise parameters → compare to Fig. 2; (b) reproduce the stability decay curve → compare to Fig. 3.
- **Key reference for**: R2-lite hardware data analysis; measurement-noise identifiability; d=3→d=5→d=7 scaling predictions; do()-intervention design on t-round stability/memory trade-off.
- **Related reading notes**: [[sundaresan_demonstrating_qec_2302.04]] (prior heavy-hex on IBM), [[geher_reset_or_not_2408.00758]] (Pauli frame update theory), [[gidney_stability_experiment_2022]] (stability experiment definition), [[harper_flammia_correlations_2023]] (crosstalk detection method), [[hetnyi_wootton_surface_code_heavy_hex_2024]] (surface code on heavy-hex lattice).
