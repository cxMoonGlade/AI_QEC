# Simulator Frontend Contract

**Status:** Block-2a build contract for the QEC simulator frontend. The current
implementation includes the Stim/Pauli artifact base, the first
CodeSpec/XZZX compiler smoke, and explicit operation/schedule/record-layout
frontend structure. It binds to
`simulator_architecture_prereg.md` for the CodeSpec/CircuitIR/backend/artifact
separation and the theory-vs-sample artifact split. This lives as
`error_coupling_simulator.frontend`, deliberately separate from the carrier:
`carrier` owns forward evolution, while `frontend` owns user-facing circuit construction,
Stim-compatible artifact
export, Pauli-noise sampling, DEM construction, `.b8` record output, and decoder
smoke results. Analog source
coupling must attach to a stable frontend/artifact surface.

## Scope

The frontend owns the simulator product surface:

```
CircuitIR / Stim circuit
  or CodeSpec -> CircuitIR
  + NoiseSpec
  + optional decoder choice (default: none)
  -> circuit_ideal.stim
  -> circuit_noisy_pauli.stim
  -> detector_error_model.dem
  -> detection_events.b8 / obs_flips_actual.b8
  -> [decoder only] obs_flips_predicted.b8
  -> sample_summary_ideal.json / sample_summary_noisy.json
  -> theory_prediction.json
  -> [decoder only] decoder_results.json
  -> manifest.json

CUDA-Q algorithm circuit
  -> statevector.npy
  -> probabilities.npy
  -> measurement_counts.json
  -> theory_prediction.json
  -> manifest.json
```

This block is **Stim-compatible only**. It supports Clifford/stabilizer circuits,
detectors, observables, Pauli/depolarizing noise expressible in Stim, DEM export,
and PyMatching decode through the existing frozen decoder path. It does **not**
claim to represent analog joint-Lindbladian, coherent non-Clifford, qutrit
leakage, or shared-source truth inside `.stim` or `.dem`.

Separate from that Stim-compatible surface, the frontend also exposes
a CUDA-Q **noiseless algorithm** adapter for non-Clifford circuits such as
12-qubit Grover. That adapter declares
`representability="cudaq_statevector_noiseless"` and writes state/count artifacts
instead of `.stim`, `.dem`, detector records, or decoder results.

## Design Boundary

`error_coupling_simulator.frontend.CircuitIR` is the internal source of truth for user-defined
circuits. Stim is an interchange and artifact format, not the only simulator IR.
This prevents two failure modes:

- hard-wiring the simulator to the Google d3 XZZX parser;
- pretending Stim can carry analog teacher truth it cannot represent.

XZZX remains the main syndrome-code target, but it must compile into the same IR
as a user-built circuit or a Stim-imported circuit. Future code-specific compilers
therefore target:

```
CodeSpec -> CircuitIR
Stim file -> CircuitIR or Stim-backed circuit
User builder -> CircuitIR
```

The current `XZZXCodeSpec` is a 3x3 checkerboard compiler smoke with mixed-basis
stabilizer checks, repeated syndrome deltas, final data closure detectors, and
one deterministic non-stabilizer-span observable. It is not a certified
distance-3 memory, hardware schedule, and does not imply analog coupling truth.

Noise placement in this frontend is **Stim/Pauli-targeted only**. The supported
targeted rules are user-facing placement controls over the declared `CircuitIR`
schedule: one gate occurrence, gate type, all gates, measurement type, and
idle qubits at explicit `TICK` boundaries. They do not claim hardware-location
identifiability, analog joint-L truth, leakage truth, or shared-source memory.
The frontend rejects unsupported Stim noise instructions instead of letting them
silently change record schemas or DEM assumptions.
Gate/measurement `target_filter` is an exact instruction-target tuple filter,
not a per-target override. Users who need per-pair/per-qubit placement inside a
bundled gate instruction must split the circuit instruction before applying the
noise rule.

## Artifacts

The artifact set is split by representability:

| artifact | meaning |
|---|---|
| `circuit_ideal.stim` | ideal detector circuit, no simulator-added noise |
| `circuit_noisy_pauli.stim` | Stim-representable Pauli/depolarizing projection |
| `detector_error_model.dem` | DEM from the noisy Stim circuit; default record-only runs preserve hyperedges, while explicit PyMatching requests graphlike decomposition |
| `detection_events.b8` | noisy detector records, packed little-endian; omitted/null when there are zero detectors |
| `obs_flips_actual.b8` | noisy observable flips, packed little-endian; omitted/null when there are zero observables |
| `obs_flips_predicted.b8` | frozen decoder predicted observable flips; omitted with `decoder_not_requested` unless decoding is explicit, and omitted/null when there are zero observables |
| `ideal_detection_events.b8` | ideal detector records for the same shot count; omitted/null when there are zero detectors |
| `ideal_obs_flips_actual.b8` | ideal observable flips for the same shot count; omitted/null when there are zero observables |
| `sample_summary_ideal.json` | ideal finite-shot sample summary |
| `sample_summary_noisy.json` | noisy finite-shot sample summary |
| `theory_prediction.json` | exact/analytic prediction when declared by the backend; otherwise `{available:false, reason:...}` |
| `decoder_results.json` | frozen decoder predictions and LER summary; omitted with `decoder_not_requested` by default |
| `manifest.json` | schema, counts, backend, seed, noise provenance |

MVP correction note: the first untracked frontend wrote `expected_ideal.json` /
`expected_noisy.json`; those names were retired before tracking because they
mixed finite-shot summaries with theoretical expectations.

Future analog backends add evaluator-only sidecars such as `source_trace.npz`,
`channel_truth.npz`, or `analog_truth.json`; those sidecars are not `.stim`
substitutes.

## Acceptance Gates For This Block

1. A Python-built circuit round-trips to a Stim circuit with declared detectors
   and observables.
2. Stim-compatible global and targeted noise specs insert only supported
   Pauli/depolarizing noise without changing detector or observable counts.
   Targeted placement means frontend schedule placement, not analog/hardware
   location truth.
3. `Simulator.run(...)` writes `.stim`, `.dem`, actual `.b8`, and JSON record artifacts without a
   decoder by default. Prediction and decoder-result artifacts require explicit
   `decoder="pymatching"`; otherwise their manifest entries are fail-closed omissions.
   `Simulator.run_noiseless(...)` and `simulate_noiseless(...)` are the public
   convenience entrypoints for no-simulator-added-noise runs. They require the
   compiled ideal/noisy circuit pair to be identical and the noise manifest to
   be absent; pre-noised sources must use `run(noise=None, ...)` instead of the
   noiseless convenience path.
   `simulate_cudaq_grover_noiseless(...)` is the CUDA-Q algorithmic no-noise
   path; it is not a DEM/decoder run.
4. Positive-width `.b8` files use the package-local `frontend.b8_io.pack_bits`
   convention and can be read back by `frontend.b8_io.read_b8` / `unpack_bits`;
   zero-width record classes are omitted/null in the manifest, not written as
   unreadable 0-byte files.
5. Decoder results use the package-local optional port
   `frontend.decoder.decode_dem`, backed by pinned external PyMatching rather than a bundled
   implementation. The explicit decoder path requires a graphlike DEM acceptable to PyMatching;
   default record-only runs instead preserve arbitrary Stim DEM hyperedges and do not decode them.
6. The manifest explicitly declares `representability="stim_pauli"` so this block
   cannot be mistaken for analog joint-L teacher evidence.
7. The manifest rejects ambiguous representability: evaluator-only sidecars are
   listed separately, never part of learner-visible inputs, and `.stim`/`.dem`
   are not allowed to imply analog/source/leakage truth. The frontend validates
   `backend`, `representability`, ideal/noisy record-schema equality, and sidecar
   visibility before writing.
8. Theory-vs-sample is explicit: finite-shot summaries are labelled as sample
   estimates, and `theory_prediction.json` is either exact/analytic with a
   named method or `{available:false, reason:...}`.
9. `CodeSpec` compilation remains decoupled: `XZZXCodeSpec` compiles to ordinary
   `CircuitIR`, and the simulator/decoder/noise path has no XZZX-specific
   branch. The current compiler schedule is limited to repeated ancilla parity
   checks whose final data-closure/readout basis is compatible per data qubit.
10. Invalid code specs fail early: non-commuting checks, logical/check
    anti-commutation, logicals inside the stabilizer span, duplicate records,
    evaluator-truth metadata, or incompatible final logical measurement bases do
    not write artifacts.
11. Schedule and record-layout metadata are honest: `repeated_memory_v1` has a
    fixed detector/final-readout policy, generated record keys use parseable
    check/logical tokens, and persisted `manifest.json` record names match the
    compiler `RecordLayout` order exactly.
