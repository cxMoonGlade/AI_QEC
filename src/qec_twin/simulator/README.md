Standalone user-facing simulator frontend.

This package owns circuit/code construction, Stim-compatible artifact export,
`.b8` record output, manifest schemas, and decoder plumbing. It is deliberately
separate from `qec_twin.forward`, which owns carrier/substrate evolution, and
from `qec_twin.mechanisms`, which owns evaluator-only mechanism definitions and
controlled teachers.

Current slice:

- `CircuitIR` and `CircuitBuilder` for small user-defined detector circuits.
- `CodeSpec`, `XZZXCodeSpec`, and `compile_code_spec(...)` for compiling a
  small 3x3 checkerboard XZZX compiler smoke into ordinary `CircuitIR`.
- Explicit frontend construction structure: `OperationSpec`/`OperationSet`,
  `ScheduleTemplate`, and `RecordLayout`.
- Source adapters: `CircuitIRSource`, `StimCircuitSource`, and direct
  `CompiledCircuit` entry into `Simulator.run(...)`.
- `RecordSchema` and manifest guards for detector/observable bit widths,
  ideal/noisy schema equality, and evaluator-only sidecar visibility.
- Stim export/import helpers.
- Stim-compatible Pauli/depolarizing noise insertion through both the legacy
  global gate-class `StimPauliNoiseSpec` and the user-facing `NoiseBuilder`.
  `NoiseBuilder` supports insertion after one gate occurrence, after a gate
  type, after all gates, before measurement types, and during scheduled idles at
  `TICK` boundaries.
- `.stim`, `.dem`, `.b8`, sample-summary, theory-prediction, decoder-result,
  and manifest artifacts.
- Frozen PyMatching decode through `qec_twin.hardware.m4_decode`.
- CUDA-Q noiseless Grover adapter for non-Clifford algorithm circuits.
- Exact qutrit/ququart adapters for small multi-level leakage smoke runs:
  `simulate_qutrit_wg_leakage(...)` (`|2>` single-site WG leakage) and
  `simulate_ququart_transport_smoke(...)` (`|3>`-faithful two-site CZ transport).
- Generic dense qutrit MCWF backend: `DenseQutritMcwfBackend` owns batched
  qutrit state trajectories, site matrices, multi-controlled computational
  phase gates, Kraus-branch sampling, and final qutrit/Born measurement.
  `CompiledMcwfProgram` is the generic op-stream contract between workload
  adapters and executors. `DenseQutritMcwfExecutor` is the full Python/Torch-GPU
  reference executor, while `NativeOpStreamMcwfExecutor` runs the cached hot
  subset (`H`, `X`, `phase=-1`, one Kraus family over selected sites) through a
  native CUDA op-stream runner. Its lowering exactly coalesces adjacent
  unique-site `X` gates into one qutrit-lifted permutation kernel; this is a
  launch-count optimization only and leaves leaked `|2>` levels inert.
  `GraphCapturedMcwfExecutor` is the default
  cached-subset executor: it CUDA-graph captures a fixed program/batch/Kraus
  shape and refreshes both random draws and same-shape Kraus values before each
  replay, so graph capture does not freeze stochastic branches or leakage
  parameters. `simulate_mcwf_qutrit_grover_leakage(...)` compiles Grover into
  that op stream; it is only the Grover workload adapter on top of the backend.
  The mainline is project-native finite-Kraus MCWF:
  fused CUDA kernels accelerate common 1/2/3-qubit gates, multi-controlled
  phase, one-site Kraus branch sampling, all-sites one-Kraus-family sampling,
  cached op-stream execution, and the experimental `BlockTrajectoryMcwfExecutor`
  when available; the Torch-GPU path remains the reference implementation.
  `BlockTrajectoryMcwfExecutor` maps one CUDA block to one full trajectory and
  is useful as a correctness-backed device-side experiment, but it is not the
  default 12-qutrit path because large dense statevectors need more grid
  parallelism. Programs containing arbitrary 1/2/3-qubit unitary ops currently
  use the dense executor until the native op-stream learns that table format.
- qutip-cuquantum adapter probes: local qutrit collapse operators are constructed
  as symbolic `CuOperator(..., mode=site, hilbert_dims=(3,)*n)` terms. This path
  is a safety/oracle integration seam for continuous `H + c_ops` MCWF, not the
  production 12-qutrit gate-level Grover carrier.

Representability boundary:

- `representability="stim_pauli"` means Clifford/stabilizer circuit artifacts
  plus Stim-representable Pauli noise only.
- `.stim` and `.dem` are not analog joint-Lindbladian truth, leakage truth, or
  shared-source non-Markovian truth.
- Zero-width detector/observable classes are omitted in the manifest instead of
  written as unreadable 0-byte `.b8` files.
- The current XZZX constructor is a DEM-compatible compiler/schedule smoke: it
  exercises mixed-basis checks, repeated syndrome deltas, final data closure
  detectors, and one deterministic non-stabilizer-span observable. It is not a
  certified distance-3 memory, hardware schedule, or analog coupling teacher.
- The current compiler schedule requires one compatible final measurement basis
  per data qubit for closure/readout. More general stabilizer-code closure
  strategies are future compiler work.
- Record-layout helpers are frontend artifact facts. They do not import or
  imply the Axis-1/Axis-2 coupled error model.
- Future analog/source/leakage backends must attach evaluator-only truth
  sidecars and declare a distinct representability class in the manifest.
- `representability="cudaq_statevector_noiseless"` is for noiseless algorithm
  circuits such as Grover. It writes state/count artifacts, not `.stim`, `.dem`,
  detector records, or decoder results.
- `representability="exact_qutrit_density_matrix_leakage"` is the in-house
  `QutritDM` carrier on `{|0>,|1>,|2>}`. It writes qutrit density/probability
  artifacts, not decoder records.
- `representability="exact_ququart_density_matrix_transport"` is the in-house
  `QuquartDM` carrier on `{|0>,|1>,|2>,|3>}` using the QuTiP-derived two-site
  CZ transport Kraus. It is resource-capped small-register evidence, not a full
  9-data-register production path.
- Scaling leakage beyond exact density matrices routes to the existing MCWF/MPS
  carriers in `qec_twin.forward.scalable`. MCWF is a sampling carrier, not the
  non-Markovian claim: Axis-2 non-Markovianity still requires an explicit shared
  source history `z_t` that conditions many mechanism parameters across cycles.
- `representability="dense_qutrit_statevector_mcwf_leakage"` is a trajectory
  carrier/backend class. It outputs final measured bit counts plus raw qutrit
  outcome counts and leakage summaries; it is not a `.stim/.dem/.b8` decoder path.
  Workload adapters such as Grover must call `DenseQutritMcwfBackend` rather than
  implementing trajectory sampling themselves. The Grover adapter uses the
  standard gate-level sequence `X`-mask -> multi-controlled phase -> unmask for
  the oracle, and `H/X/multi-controlled-phase/X/H` for the diffuser; it must not
  shortcut by directly flipping the marked basis amplitude.
- qutip-cuquantum `mcsolve` consumes continuous-time Hamiltonian/collapse
  operators. It is not a drop-in finite-Kraus branch sampler and is not currently
  registered as the 12-qutrit Grover carrier. The safe adapter intentionally
  refuses 12-qutrit `mcsolve` production runs; 12q Grover+leakage routes through
  `DenseQutritMcwfBackend`. Do not build 12q local collapse operators via
  `qutip.tensor([...])`: that expands a full `3**12 x 3**12` operator. Use the
  local symbolic `CuOperator` factory instead.

Design target:

`CodeSpec -> CircuitIR`, imported Stim circuits, and hand-built `CircuitIR` all
feed the same `Simulator.run(...)` artifact surface. XZZX is the first target
code spec, not a hard-coded simulator core.

Noiseless quickstart:

```python
from qec_twin.simulator import (
    XZZXCodeSpec,
    compile_code_spec,
    simulate_noiseless,
)

spec = XZZXCodeSpec(layout_size=3, rounds=2).to_code_spec()
circuit = compile_code_spec(spec)
result = simulate_noiseless(
    circuit,
    shots=1024,
    out_dir="outputs/simulator/noiseless_xzzx",
    seed=0,
)

detections = result.load_detection_events()
observables = result.load_observable_flips()
print(result.paths.manifest)
print(detections.shape, observables.shape)
```

This writes the same standard artifact set as noisy runs, with
`manifest["noise"] is None`. The noisy/ideal Stim artifacts must be identical in
this mode; `run_noiseless(...)` rejects pre-noised `StimCircuitSource` or
`CompiledCircuit` inputs whose ideal/noisy circuit pair already differs. Use
`Simulator(source).run(noise=None, ...)` when the source itself intentionally
carries a pre-noised circuit pair. Future coupled-error backends attach below
the same product surface.

Hand-built circuit + targeted noise quickstart:

```python
from qec_twin.simulator import CircuitBuilder, Noise, Simulator

builder = CircuitBuilder(num_qubits=3)
builder.h(0)
builder.cz((0, 1))
builder.tick()
builder.x(2)
builder.idle(1)
builder.tick()
builder.measure((0, 1, 2), key=("m0", "m1", "m2"))
builder.detector("d0", xor=("m0",))
builder.observable("logical0", xor=("m0",), index=0)
circuit = builder.build()

noise = (
    Noise.targeted()
    .after_gate(0, "X_ERROR", 0.001)           # first user gate occurrence
    .after_gate_type("CZ", "DEPOLARIZE", 0.01) # auto -> DEPOLARIZE2
    .after_all_gates("Z_ERROR", 0.0005)
    .during_idle("DEPOLARIZE", 0.002)          # auto idle qubits at TICK
    .before_measurement("X_ERROR", 0.01)
    .build()
)

result = Simulator(circuit).run(
    shots=1024,
    noise=noise,
    out_dir="outputs/simulator/targeted_noise",
    seed=7,
)
print(result.manifest["noise"]["matched_counts"])
print(result.paths.circuit_noisy_pauli)
```

This path writes `.stim`, `.dem`, `.b8`, summaries, decoder output, and a
manifest. `qec_twin.simulator.noise` is intentionally limited to
Stim-representable Pauli noise.
Gate and measurement `target_filter` arguments are exact instruction-target
tuple filters; they never override where the inserted noise lands. To address
one pair/qubit inside a bundled instruction, split that source instruction
first. Idle noise is inserted only at explicit `TICK` boundaries, so a terminal
idle interval needs a trailing `builder.tick()`.
Leakage, analog joint-L coupling, and shared-source non-Markovian noise attach
through backend-specific truth sidecars / carriers, not by laundering them into
this Pauli insertion layer.

CUDA-Q Grover quickstart:

```python
from qec_twin.simulator import simulate_cudaq_grover_noiseless

result = simulate_cudaq_grover_noiseless(
    num_qubits=12,
    marked_state="111111111111",
    shots=1024,
    seed=42,
    out_dir="outputs/simulator/grover12_cudaq_noiseless",
)

print(result.iterations)
print(result.marked_probability)
print(result.marked_counts, "/", result.shots)
print(result.top_outcomes(3))
```

This uses CUDA-Q's current target (on this workstation: NVIDIA/cuStateVec when
available). It writes `statevector.npy`, `probabilities.npy`,
`measurement_counts.json`, `theory_prediction.json`, and `manifest.json`.

Multi-level leakage quickstarts:

```python
from qec_twin.simulator import (
    simulate_qutrit_wg_leakage,
    simulate_ququart_transport_smoke,
)

q2 = simulate_qutrit_wg_leakage(
    num_qutrits=3,
    initial_levels="111",
    cycles=1,
    shots=1024,
    out_dir="outputs/simulator/qutrit_wg_leakage3",
)
print(q2.total_leaked_population)
print(q2.top_outcomes(4))

q3 = simulate_ququart_transport_smoke(
    num_ququarts=2,
    initial_levels="12",
    shots=1024,
    out_dir="outputs/simulator/ququart_transport2",
)
print(q3.outcome_probability("30"))
print(q3.top_outcomes(4))
```

Both paths use project-owned GPU carriers under `forward/exact`; both write
multi-level probability/count artifacts and a manifest, not `.stim`, `.dem`,
`.b8`, or decoder results.

MCWF backend + Grover leakage workload quickstart:

```python
from qec_twin.simulator import simulate_mcwf_qutrit_grover_leakage

result = simulate_mcwf_qutrit_grover_leakage(
    num_qubits=12,
    marked_state="111111111111",
    shots=16,
    seed=123,
    batch_size=2,
    use_fused_kernels=True,
    out_dir="outputs/simulator/grover12_mcwf_leakage",
)

print(result.iterations)
print(result.mean_pre_readout_marked_probability)
print(result.marked_fraction)
print(result.mean_final_leaked_sites)
print(result.top_outcomes(4))
print(result.top_qutrit_outcomes(4))
```

This writes `measurement_counts.json`, `qutrit_outcome_counts.json`,
`leakage_by_site.json`, `trajectory_summary.json`, `theory_prediction.json`, and
`manifest.json`. The measurement is trajectory/Born sampled from the final
qutrit state; final `|2>` levels are also reported before being mapped through
the leaked-readout bias into binary counts. The manifest declares
`algorithm="single_solution_grover_gate_level"` and records the oracle/diffuser
realization.

The reusable backend can also be used directly by future circuit/schedule
adapters, or through the generic compiled-program surface:

```python
from qec_twin.simulator import CompiledMcwfProgram
from qec_twin.simulator.mcwf_program import h, kraus_all_sites

program = CompiledMcwfProgram(
    num_qutrits=3,
    operations=(
        h(0),
        h(1),
        h(2),
        kraus_all_sites("wg_leakage", range(3)),
    ),
)
print(program.summary())
```

The lower-level backend remains available for oracle-style tests:

```python
import torch

from qec_twin.simulator import DenseQutritMcwfBackend
from qec_twin.simulator.mcwf_backend import CDTYPE

backend = DenseQutritMcwfBackend(num_qutrits=2, seed=7)
psi = backend.basis_state(batch_size=32, initial_levels="11")
swap_12 = torch.zeros((3, 3), dtype=CDTYPE, device=backend.device)
swap_12[0, 0] = 1
swap_12[1, 2] = 1
swap_12[2, 1] = 1
psi = backend.apply_kraus_all_sites(psi, swap_12.unsqueeze(0))
measurement = backend.sample_measurements(psi, leaked_readout_b=1.0)
print(measurement.qutrit_counts)
```

qutip-cuquantum local-operator safety probe:

```python
from qec_twin.simulator import qutip_cuquantum_symbolic_collapse_summary

summary = qutip_cuquantum_symbolic_collapse_summary(num_qutrits=12, site=0)
assert summary.collapse_data_type == "CuOperator"
assert summary.cdc_data_type == "CuOperator"
```

The corresponding `mcsolve` smoke is deliberately capped to small registers:

```python
from qec_twin.simulator import probe_qutip_cuquantum_local_mcwf

probe = probe_qutip_cuquantum_local_mcwf(num_qutrits=2, ntraj=1)
print(probe.method, probe.end_condition)
```
