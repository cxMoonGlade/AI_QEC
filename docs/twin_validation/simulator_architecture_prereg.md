# Simulator architecture pre-registration

**Status:** bounded theory-first architecture pre-registration for the standalone
`qec_twin.simulator` frontend. The current untracked frontend has completed the
Stim/Pauli artifact base plus the first CodeSpec/XZZX compiler smoke and the
explicit operation/schedule/record-layout layer. This is not a claim
that the simulator is already complete or that analog coupling truth is carried
by `.stim` / `.dem`.

**Binding decision:** the simulator product surface lives in
`qec_twin.simulator`, deliberately separate from `qec_twin.forward`. `forward`
owns carrier/substrate evolution. `simulator` owns user-facing circuit/code
construction, compilation, artifact emission, backend selection, and decoder
plumbing. Mechanisms and controlled teachers remain evaluator-side under
`qec_twin.mechanisms`.

---

## 0. Review inputs

This pre-registration was written after reading the in-repo contract and the
current MVP implementation:

- `CONTEXT.md`: the simulator must be a mechanism-conditioned noise simulator
  with knobs, not merely a syndrome sample generator.
- `docs/ARCHITECTURE.md`: `forward` is the exact/scalable physics engine;
  `hardware` owns `.stim`/`.b8`/`.dem` ingestion; `decoder`/`hardware.m4_decode`
  own frozen MWPM decoding.
- `docs/METRICS.md`: all quantitative outputs must carry standard metric names
  and conventions.
- `docs/twin_validation/qec_coupling_simulator_build_contract.md`: G2 remains
  the joint-L headline fidelity gate; G4/G6 are record-faithfulness gates.
- `docs/twin_validation/simulator_frontend_contract.md`: the first frontend
  block is Stim-compatible only and must not pretend to carry analog truth.
- `src/qec_twin/simulator/*`: current untracked MVP for `CircuitIR`,
  Stim export, Pauli noise insertion, `.b8` output, DEM/PyMatching decode.
- `src/qec_twin/hardware/b8_io.py` and `src/qec_twin/hardware/m4_decode.py`:
  the existing bit-packing and frozen decoder contracts.
- `src/qec_twin/forward/joint_lindbladian.py`: validated Axis-1 joint-L
  assembler and process-infidelity G2 metric.
- Local reading notes:
  - Takou and Brown, arXiv:2510.23797: coherent errors can leave DEM-level
    structural fingerprints, including enhanced edges and hyperedges; a DEM is
    still a decoder object, not a channel.
  - Hines et al., arXiv:2603.18457: small Markovian coherent/correlated errors
    can be mapped to a bounded-error Stim-compatible DEM, but leakage and
    relaxation/negative-rate obstructions remain outside ordinary stochastic
    DEM sampling.
  - Manabe, Suzuki, Darmawan, arXiv:2308.08186: true leakage requires a
    multi-level simulator; it should not be projected into a qubit Pauli DEM
    and called faithful.
  - Xiao et al., arXiv:2601.21472: syndrome-code learnability and
    per-location Pauli factor graphs motivate a clean separation between code,
    circuit, local noise model, and decoder-facing logical prediction.

No open-ended CUDA-Q/CUDA-QX deep research is needed for this step. CUDA-Q/X is a
future backend adapter choice, not the source of truth for the frontend IR.

---

## 1. Core separation

The simulator must separate five objects that are currently too easy to conflate:

| object | owner | role | must not do |
|---|---|---|---|
| `CodeSpec` | `qec_twin.simulator` | syndrome-code geometry, stabilizers, logicals, round count, boundary convention | assume one hard-coded circuit |
| `CircuitIR` / `StimCircuitSource` | `qec_twin.simulator` | user-defined circuit or imported Stim circuit | know the noise truth |
| `CircuitCompiler` | `qec_twin.simulator` | compile `CodeSpec` + schedule template into circuit artifacts | bind the simulator core to XZZX only |
| `NoiseSpec` | `qec_twin.simulator` + backend adapters | declare representable noise and placement rules | hide analog truth inside `.stim` |
| `Backend` | adapter layer | execute/summarize a compiled circuit under a representability contract | change the artifact schema silently |
| `RecordBundle` | `qec_twin.simulator` | detector/observable records, `.b8`, schema, sample summaries | contain evaluator-only truth |
| `ArtifactBundle` | `qec_twin.simulator` | `.stim`, `.dem`, `.b8`, JSON summaries, manifest, sidecars | mix truth and learner-visible data |

**XZZX is a `CodeSpec`, not the simulator.** A user-provided circuit must be able
to bypass `CodeSpec` entirely. Conversely, an XZZX code must compile into the
same circuit/artifact surface as a user-built circuit or an imported Stim file.

---

## 2. Representability ladder

Every run manifest must declare exactly which representability class it used.
This is the anti-toy boundary.

| class | artifact carrier | faithful for | not faithful for |
|---|---|---|---|
| `stim_pauli` | Stim circuit + stochastic DEM | Clifford/stabilizer circuits, Pauli/depolarizing noise, measurement flips, `.dem`, `.b8`, PyMatching decode | coherent phase truth, leakage, analog joint-L, shared source truth |
| `stim_bounded_nonpauli_dem` | Stim-compatible DEM plus approximation sidecar | small Markovian coherent/correlated computational-subspace effects when a registered EEG/BCH/Zassenhaus approximation applies | leakage, relaxation negative-rate regimes, large unbounded coherent rates |
| `analog_joint_l_window` | evaluator-only channel/Kraus sidecars + sampled records | exact/windowed joint-L mechanisms, G2 process-fidelity truth, small qubit/qutrit windows | scalable full-code truth without a declared carrier |
| `qutrit_leakage_trajectory` | trajectory/MPS/MCWF sidecars + sampled records | leakage/seepage and multi-level readout truth | a pure qubit Pauli DEM |
| `source_coupled` | source trajectory sidecars + records | explicit memoryful latent fan-out across mechanisms/cycles | non-negative independent Markovian-rate surrogates |

The `.stim` and `.dem` files are decoder-facing projections or exact carriers
only for the classes that declare them. They are never allowed to stand in for
full analog truth.

---

## 3. Backend matrix

| backend | current status | role in the simulator | next decision |
|---|---|---|---|
| Stim | available and used in the MVP | canonical Clifford/Pauli artifact backend: `.stim`, `.dem`, detector sampler | keep as first production backend |
| PyMatching | available through `hardware.m4_decode` | frozen decoder path at upstream defaults | reuse, do not reimplement |
| torch joint-L | validated in `forward/joint_lindbladian.py` | G2 and future analog window truth | adapter later, not in Stim frontend |
| QuTiP/scipy | test/oracle only | independent channel checks | never production frontend |
| CUDA-Q | added for noiseless algorithm circuits | non-Clifford statevector/sampling frontend, e.g. 12q Grover; writes state/count artifacts, not DEM records | keep separate from QEC noise/coupling backend until a carrier contract is registered |
| CUDA-QX | read-only frontend reference only | circuit-construction inspiration from vendored baseline | do not adopt CUDA-QX error/noise construction |
| qutrit/MPS/MCWF | literature-grounded but not in this frontend slice | leakage-capable simulator backend | slice after qubit/Stim/code compiler works |

---

## 4. Artifact contract

The stable product artifacts are:

| artifact | meaning |
|---|---|
| `circuit_ideal.stim` | ideal detector circuit when representable in Stim |
| `circuit_noisy_pauli.stim` | Stim-representable noisy projection |
| `detector_error_model.dem` | decoder-facing DEM from the declared carrier |
| `detection_events.b8` | noisy detector records, Stim little-endian `.b8` packing; omitted/null when there are zero detectors |
| `obs_flips_actual.b8` | noisy logical observable records; omitted/null when there are zero observables |
| `obs_flips_predicted.b8` | frozen decoder predicted logical observable records; omitted/null when there are zero observables |
| `ideal_detection_events.b8` | ideal detector records for the same shot count; omitted/null when there are zero detectors |
| `ideal_obs_flips_actual.b8` | ideal logical-observable records for the same shot count; omitted/null when there are zero observables |
| `sample_summary_ideal.json` | finite-shot sample summary, not a theory result |
| `sample_summary_noisy.json` | finite-shot sample summary, not a theory result |
| `theory_prediction.json` | exact/analytic prediction when the backend can provide one; otherwise `{available:false, reason:...}` |
| `decoder_results.json` | frozen decoder predictions and LER summary |
| `manifest.json` | schema, backend, representability, seeds, code/circuit/noise provenance |
| evaluator-only sidecars | source trajectories, channel truth, Kraus stacks, leakage traces, approximation bounds |

**Correction to the first MVP:** the earlier `expected_ideal.json` and
`expected_noisy.json` names were too strong for sampled marginals. The frontend
now uses `sample_summary_*` with `"estimator": "finite_shot_sample"` and a
separate `theory_prediction.json`. A theoretical result cannot be a sampled
summary in disguise.

---

## 5. Acceptance gates for the next frontend slice

These are frontend gates, separate from the G1-G8 coupling gates.

**F0 module boundary.** `qec_twin.simulator` has its own `README.md`. It does not
add flat modules under `src/qec_twin/` and does not move physics code out of
`forward` or `mechanisms`.

**F1 circuit/code decoupling.** The same `Simulator.run` path accepts:

- a hand-built `CircuitIR`;
- a Stim-backed circuit source;
- a compiled `CodeSpec` such as `XZZXCodeSpec`.

No decoder/noise/backend code may special-case XZZX.

**F2 XZZX compiler smoke.** A minimal XZZX `CodeSpec` compiles to a circuit with:
data/ancilla qubit roles, stabilizer checks, repeated syndrome measurements,
declared detectors, and at least one logical observable. The compiler output is a
normal `CircuitIR` or `StimCircuitSource`, not a private XZZX object.

**F3 Stim artifact roundtrip.** The compiled or imported circuit writes
`circuit_ideal.stim`; detector/observable counts in the manifest match Stim's
counts exactly.

**F4 noise placement without schema drift.** In the current slice,
`StimPauliNoiseSpec` is global gate-class Pauli/depolarizing noise only. It must
not change detector or observable counts. Location-aware placement remains a
future compiler/noise-map slice.

**F5 `.b8` compatibility.** Every positive-width `.b8` file can be read by
`hardware.b8_io.read_b8` / `unpack_bits` with the manifest-declared bit width.
Zero-width record classes are omitted with `file:null`, `bits_per_shot:0`, and
`omitted_reason:"zero_bit_width"` so no unreadable 0-byte artifact can masquerade
as a valid record file.

**F6 frozen decoder path.** `decoder_results.json` is produced via
`hardware.m4_decode.decode_dem`; no second PyMatching wrapper is introduced. The
current decode path assumes a graphlike DEM acceptable to PyMatching; arbitrary
Stim depolarizing noise that produces undecomposed high-order hyperedges is not
claimed as decodable in this frontend slice.

**F7 manifest anti-laundering.** The manifest refuses ambiguous runs. If the run
uses `stim_pauli`, no analog/source/leakage truth is implied. If evaluator-only
truth sidecars exist, they are listed separately and never part of learner input.
The frontend code validates `backend`, `representability`, ideal/noisy record
schema equality, and sidecar `visibility="evaluator_only"` before writing.

**F8 theory-vs-sample split.** `theory_prediction.json` is either exact/analytic
with a named method, or explicitly `{available:false, reason:...}`. Sample
summaries are labelled as finite-shot estimates.

---

## 6. Current code slice status

Implemented in `qec_twin.simulator` only, still untracked until the user decides
to track the frontend:

1. `README.md`: module scope and representability boundary.
2. `code_spec.py`: `CodeSpec`, `CodeQubit`, `StabilizerCheck`,
   `LogicalObservableSpec`, `PauliTerm`; validates qubit roles, commuting
   checks, logical/check commutation, logical-not-in-stabilizer-span, and unique
   record indices.
3. `xzzx_code.py`: first `XZZXCodeSpec` constructor for the main target code:
   3x3 checkerboard XZZX compiler smoke with mixed-basis stabilizer checks,
   repeated syndrome rounds, final data closure detectors, and a deterministic
   non-stabilizer-span observable. This is a compiler/schedule smoke, not a
   certified distance-3 memory or hardware schedule.
4. `compiler.py`: `compile_code_spec(spec, schedule_template) -> CircuitIR`
   plus direct `compile_code_spec_to_compiled(...)`. The current schedule
   supports repeated ancilla parity checks with final data closure only when
   every data qubit has one compatible final measurement basis across checks and
   logicals; broader closure strategies are future work.
5. ~~`stim_source.py`~~ -> **DONE in the untracked frontend MVP:**
   `CircuitIRSource`, `StimCircuitSource`, `CompiledCircuitSource`, and direct
   `CompiledCircuit` entry.
6. ~~`simulator.py` update~~ -> **DONE:** accepts
   `CircuitIR | CircuitSource | CompiledCircuit`.
7. ~~Artifact update~~ -> **DONE:** split finite-shot summaries from theory
   predictions and added `obs_flips_predicted.b8`.
8. Tests: **DONE in the untracked frontend suite.**
   - user-built circuit still passes;
   - imported Stim circuit emits artifacts;
   - XZZX code compiles through the same path;
   - compiled CodeSpec can enter `Simulator.run(...)` directly;
   - `.b8` readback works;
   - manifest representability is explicit;
   - decoder path remains `hardware.m4_decode`;
   - non-commuting checks, stabilizer-product logicals, evaluator-truth metadata,
     and incompatible final bases fail before artifact emission;
   - operation/schedule requirements fail before artifact emission;
   - `repeated_memory_v1` cannot carry a dishonest schedule policy;
   - custom repetition and non-XZZX mixed-basis codes compile through the same
     frontend path;
   - persisted `manifest.json` record names match `RecordLayout` order exactly;
   - generated CodeSpec record tokens reject `:` / whitespace parse ambiguity;
   - parameterized Pauli fault-response oracles check declared check
     anti-commutation against emitted detector flips across all data qubits and
     X/Z faults.

**Do not start `source_coupling.py` until this frontend slice is stable.** The
source layer needs a stable circuit/artifact surface to attach to; otherwise the
teacher will be correct internally but awkward or misleading as a simulator.

---

## 7. Open decisions before tracking/commit

1. ~~XZZX first target~~ -> **RESOLVED for this slice:** minimal generated 3x3
   checkerboard XZZX compiler smoke. A wrapper around a shipped/standard XZZX
   circuit remains the realism upgrade before making distance or G1-like
   schedule claims.
2. ~~Artifact naming migration~~ -> **RESOLVED in the untracked frontend MVP:**
   `sample_summary_*` + `theory_prediction.json`.
3. CUDA-Q/CUDA-QX boundary: CUDA-Q is allowed for noiseless algorithm circuits;
   CUDA-QX remains read-only frontend reference only. Neither defines our
   coupled-error construction.
4. Frontend tracking: all simulator-frontend files remain untracked until the
   user decides this module is ready to enter git.
