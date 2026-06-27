# MCWF Executor Optimization Pre-Registration

Status: PRE-REGISTRATION, 2026-06-27. This document is written before the next
MCWF executor optimization run. Existing baseline runs are treated as measured
starting points, not as post-hoc predictions.

Scope: optimize the project-native qutrit finite-Kraus MCWF simulator carrier so
the same circuit/noise semantics run faster. This is an execution-layer prereg,
not a new noise-model prereg and not a new claim that MCWF alone implements the
Axis-2 non-Markovian source layer.

## 0. Grounding ledger

| sub-axis | mechanism / design anchor | observable / metric anchor | local note / code | use here |
|---|---|---|---|---|
| Leakage semantics | Wood-Gambetta arXiv:1704.03081: `L1`, `L2`, `C_L`, qutrit leakage/seepage | Leakage population, coherent-leakage bounds, CPTP Kraus checks | `docs/papers/reading_notes/wood_gambetta_leakage_characterization_1704.03081.md`; `qec_twin.mechanisms.qutrit_teachers.leakage_kraus_torch` | Preserve leakage physics; never replace by Pauli/twirl for speed |
| Qutrit MCWF carrier | Manabe-Suzuki-Darmawan arXiv:2308.08186: qutrit MPS/state trajectory, Kraus sampling `p_i = Tr(K_i |psi><psi| K_i^dag)` | Syndrome/logical record emission, trajectory convergence, truncation ledger for MPS future | `docs/papers/reading_notes/leakage_tensor_network_simulation_2308.08186.md`; `forward/scalable/README.md` | Mainline execution shape: pure-state qutrit trajectory, not density matrix |
| Beyond-Pauli / DEM boundary | Hines et al. arXiv:2603.18457: computational-subspace non-Pauli DEM approximation; explicit leakage/relaxation caveats | Stim/DEM representability boundary, anti-laundering manifest | `docs/papers/reading_notes/qec_beyond_pauli_stochastic_sim_2603.18457.md`; `simulator_architecture_prereg.md` | Do not claim `.stim/.dem` carries leakage or analog joint-L truth |
| CP trajectory vs non-Markovian caveat | Shen-Lidar arXiv:2502.18929 note: CP/Kraus trajectories are Born-positive; negative-rate non-Markovian regimes are a different object | Axis-2 source must be explicit `z_t`, not independent Kraus draws renamed "memory" | `docs/papers/reading_notes/shen_lidar_realtime_signproblem_qmc_2502.18929.md` | Keep MCWF as carrier; source histories condition carrier parameters |
| Existing native CUDA trajectory design | `sv_traj_d3.cu`: one block per trajectory, fixed op schedule, per-shot RNG stream, packed records | Bitwise / distribution equivalence against dense oracles and draw-order controls | `src/qec_twin/forward/kernels/sv_traj_d3.cu`; `src/qec_twin/forward/scalable/sv_sampler.py` | Reuse op-stream trajectory-kernel design instead of Grover-specific shortcuts |
| Generic frontend MCWF carrier | `DenseQutritMcwfBackend`: batched dense qutrit MCWF; fused CUDA primitives for gates/phase/Kraus | Torch-GPU reference equivalence; qutrit convention; artifact manifests | `src/qec_twin/simulator/mcwf_backend.py`; `tests/test_simulator_mcwf_backend.py` | Current frontend carrier to optimize without changing semantics |
| CUDA execution primitives | NVIDIA CUDA Graphs docs/blog; cuQuantum/cuStateVec docs; CUDA-Q simulator docs | Kernel-launch count, graph replay, statevector/gate/sampling primitives | NVIDIA docs: CUDA graphs; cuStateVec; CUDA-Q simulators | Engineering guide only; not a replacement for project noise semantics |
| Frontend reference only | Local CUDA-QX baseline docs | Code/circuit/record layout inspiration | `external/baselines/cudaqx/...`; `simulator_cudaqx_design_prereg.md` | Frontend design reference only; do not import CUDA-QX error construction |

## 1. Mechanism preserved by optimization

The optimized executor must preserve the exact same semantic object:

1. A qutrit statevector trajectory over `3^n` amplitudes, with qutrit 0 as the
   most-significant trit.
2. Qubit gates lifted into the `{|0>, |1>}` subspace with leaked `|2>` levels
   inert unless a registered multi-level gate/noise operator says otherwise.
3. Finite-Kraus MCWF sampling: for each CPTP Kraus family `{K_k}`, compute
   `p_k = ||K_k |psi>||^2`, draw one branch from those Born probabilities, apply
   `K_k |psi> / sqrt(p_k)`, and continue as a pure state.
4. Final qutrit/Born measurement and declared leaked-readout map, with raw
   qutrit outcome summaries retained before binary readout projection.
5. Axis-1 / Axis-2 compatibility:
   - Axis-1 joint-L or joint-channel couplings later attach as compiled channel
     primitives or window sidecars, not as a Pauli projection.
   - Axis-2 non-Markovianity later attaches as explicit source histories `z_t`
     that condition many parameters across cycles. Independent per-site Kraus
     draws are not a memory model.

The current 12-qutrit Grover leakage adapter is only a workload adapter. The
optimization target is the reusable executor path, not a Grover-only fused
success-amplitude trick.

## 2. Optimization hypothesis

Observed baseline before this prereg:

- 12-qutrit Grover, target `000000000000`, 10k MCWF shots, dense qutrit c128,
  default fused kernels: about 1269 s wall time; marked fraction 0.99; mean final
  leaked sites 0.0208; any-leakage fraction 0.0083.
- CUDA-Q noiseless 12-qubit Grover, target `000000000000`, 10k samples: about
  0.85 s internal artifact run time; marked probability 0.9999455.

These are not directly comparable physics workloads. The first evolves
`3^12 = 531441` complex128 amplitudes per trajectory with stochastic Kraus
branches and leakage readout. The second evolves `2^12 = 4096` qubit amplitudes,
no leakage, no Kraus, no trajectory ensemble. The useful comparison is not
"match CUDA-Q speed"; it is "remove avoidable Python/launch/scratch overhead
without changing qutrit MCWF semantics."

Primary hypothesis:

- The current frontend MCWF path is launch-chain and Python-loop heavy:
  gate-by-gate, site-by-site calls allocate temporaries and launch many kernels.
- A compiled MCWF program / op-stream executor should reduce overhead by:
  - precompiling the circuit/noise schedule into a typed op stream;
  - reusing state/scratch/norm/select buffers across the whole batch;
  - fusing repeated one-site Kraus norm/select/apply where possible;
  - optionally CUDA-graph replaying a fixed-address fixed-op stream.

This is an executor optimization. It must not change the number, order, or
semantics of gate/noise/measurement operations except through a separately
registered compiler transformation with an equivalence witness.

## 3. Registered observables

Correctness observables:

| observable | class | gate |
|---|---:|---|
| Same deterministic gates as Torch-GPU reference for 1/2/3-qubit lifted gates | (a) exact | max amplitude gap `<= 1e-12` c128 |
| Same Kraus branch result with pre-supplied uniform tensor | (a) exact | max amplitude gap `<= 1e-12` c128 |
| Same no-leakage Grover success probability as closed form | (a) exact | pre-readout marked probability gap `<= 1e-12` for small n |
| Same distribution as current reference for stochastic runs | (c) gate | two-sample / binomial bands declared per run; no silent bitwise claim when RNG order differs |
| Same qutrit leakage summaries | (c) gate | mean leaked sites and any-leakage fraction within MC standard error |
| Same artifact schema | (a) exact | manifest representability, qutrit convention, raw qutrit counts, no `.stim/.dem/.b8` for MCWF Grover |

Performance observables:

| observable | class | reason |
|---|---:|---|
| end-to-end wall time excluding first JIT compile | (c) gate | user-visible throughput |
| shots / second at fixed `(n, shots, batch_size, precision, noise)` | (c) gate | primary performance metric |
| kernel launches per Grover iteration / per trajectory batch | (b) prediction band | should fall after op-stream / graph capture |
| GPU memory peak | (c) gate | no density-matrix blow-up |
| GPU utilization | (c) gate | distinguish launch-bound from bandwidth/FLOP-bound |
| artifact write time | (c) gate | reported separately; not counted as physics speedup |

## 4. Falsifiable performance bets

All speed numbers are gates, not scientific claims.

P1. Op-stream executor, no CUDA graph yet:

- Prediction: at 12 qutrit / 10k Grover-leakage shots, speedup over the observed
  1269 s baseline should be at least 2x if Python/kernel-launch overhead is a
  material bottleneck.
- Miss interpretation: if speedup is <2x but correctness passes, the workload is
  dominated by actual `B * 3^n` memory traffic / Kraus reductions, not Python
  overhead. That is a finding, not a failure to hide.

P2. Persistent scratch and no per-site temp allocations:

- Prediction: allocator activity and peak transient memory should drop; no OOM
  is allowed at 12 qutrit / 10k shots with the same batch size that completed
  before.
- Miss interpretation: register finding and inspect tensors; do not reduce the
  physical state space or silently lower precision to fit.

P3. CUDA graph replay for fixed op stream:

- Prediction: if a fixed-address fixed-op run can be captured, launch overhead
  should fall measurably; expected gain is workload dependent and may be modest
  if kernels are memory-bandwidth dominated.
- Gate: graph mode must be numerically equivalent to eager op-stream mode before
  any performance number is reported.

P4. Complex64 throughput mode is deferred:

- Prediction is not registered yet. c64 can only open after a c64-vs-c128
  distribution equivalence prereg with leakage summaries and final counts.
  No current optimization is allowed to switch precision to win speed.

## 5. Independent ground truth

The optimized executor must be certified against non-circular references:

1. Torch-GPU reference path with `QEC_TWIN_NO_KERNELS=1` for small batches and
   pre-supplied uniform draws. This is a different implementation of the same
   qutrit MCWF semantics.
2. Exact small-system density/state oracles (`QutritDM` / closed-form Grover) for
   no-leakage and small leakage probes where density-matrix cost is feasible.
3. Existing `sv_traj_d3.cu` / `SvSampler` trajectory design as an architectural
   precedent and, when a common d3 XZZX op stream is available, as a packed-record
   cross-check. It is not an oracle for 12q Grover unless the same program is
   compiled into both shapes.
4. CUDA-Q noiseless is only a qubit-subspace sanity check for no-leakage
   algorithm circuits. It is not a leakage oracle.
5. qutip-cuquantum remains a small-system continuous `H + c_ops` probe/oracle
   seam. It is not the production 12-qutrit finite-Kraus Grover carrier.

## 6. Bounded simplifications and hard stops

Allowed in this slice:

- Dense qutrit statevector capped at 12 qutrits.
- Complex128 only.
- Finite-Kraus CP Markovian leakage/seepage channels.
- Grover as the first workload adapter, provided the executor API is
  algorithm-neutral.
- Timing gates on one workstation, with CUDA visibility explicitly verified.

Forbidden anti-toy shortcuts:

- No direct marked-amplitude flip shortcut that bypasses the gate-level oracle
  and diffuser sequence.
- No replacing qutrit leakage by a qubit Pauli/Stim DEM projection for the MCWF
  backend.
- No qutip-cuquantum full dense tensor operator build for 12 qutrits.
- No CPU fallback for serious MCWF runs.
- No Grover-specialized monolithic kernel as the headline executor API.
- No precision downgrade, shot reduction, batch-size change, or noise removal
  counted as speedup unless separately reported as a changed workload.
- No calling independent per-site Kraus draws "non-Markovian"; Axis-2 requires
  explicit shared source state.

Hard stops:

- Any exact-reference mismatch above tolerance stops performance reporting.
- Any manifest/schema drift that launders MCWF as `.stim/.dem` truth stops the
  run.
- Any density-matrix memory scaling (`D x D` at `D=3^12`) entering the production
  path stops the run.

## 7. Build org for the next implementation slice

Recommended slice order:

1. `CompiledMcwfProgram` in `qec_twin.simulator`, separate from `forward`:
   typed op stream for lifted qubit gates, multi-controlled phase, one-site
   Kraus, final measurement metadata, qutrit convention, and artifact schema.
2. `DenseQutritMcwfExecutor` backend adapter:
   runs a compiled program via the existing Torch-GPU reference and fused CUDA
   primitive path; preserves current `DenseQutritMcwfBackend` API for direct use.
3. `NativeTrajectoryExecutor` / kernel path:
   generic qutrit op-stream kernel or a small family of kernels modeled on
   `sv_traj_wc_kernel`, with one block/trajectory or a registered alternative
   mapping. It must be program-driven, not Grover-driven.
4. Optional CUDA graph replay:
   fixed op stream, fixed tensor addresses, explicit eager-vs-graph equivalence
   test before timing.
5. Bench + evidence:
   write `outputs/simulator/.../perf_summary.json` with timings split into
   compile/JIT, physics execution, sampling, artifact writing, and total wall.

Module boundary:

- `qec_twin.simulator` owns program IR, compilation from user circuit / Grover /
  future XZZX schedule, run manifests, and artifacts.
- `qec_twin.forward.kernels` may own CUDA `.cu` kernels and loaders because they
  are acceleration assets, not product surface or physics semantics.
- `qec_twin.mechanisms` remains the source of leakage Kraus/channel definitions.

## 8. Reviewer checklist

An independent reviewer should score:

1. Is the optimized path an executor for the same qutrit MCWF semantics?
2. Does any code path collapse leakage into Pauli/Stim truth?
3. Is the Grover adapter still gate-level and workload-only?
4. Are random draws either bitwise-controlled or statistically banded?
5. Are performance numbers separated from JIT compile and artifact write time?
6. Is GPU-only execution enforced for MCWF?
7. Are Axis-1 / Axis-2 hooks preserved rather than erased by the executor API?

Only after these pass should the optimized executor become the default for the
12-qutrit MCWF workload.

## 9. External engineering references

These references are used only for executor design, not for noise semantics:

- NVIDIA CUDA C Programming Guide, CUDA Graphs:
  `https://docs.nvidia.com/cuda/cuda-c-programming-guide/index.html#cuda-graphs`
- NVIDIA CUDA Graphs blog, launch-overhead motivation:
  `https://developer.nvidia.com/blog/cuda-graphs/`
- NVIDIA cuQuantum / cuStateVec documentation:
  `https://docs.nvidia.com/cuda/cuquantum/latest/custatevec/index.html`
- CUDA-Q simulator backends documentation:
  `https://nvidia.github.io/cuda-quantum/latest/using/backends/simulators.html`
- CUDA-Q pre-trajectory sampling with batch execution example:
  `https://nvidia.github.io/cuda-quantum/latest/using/examples/ptsbe.html`
