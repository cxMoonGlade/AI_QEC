# CUDA-Q / PECOS XZZX d=7 non-Pauli multi-round capability probe

Date: 2026-07-26  
Status: engineering capability audit; **not** simulator acceptance or scientific faithfulness

## Question and frozen gate

Can either current external runtime actually execute an XZZX distance-7 memory experiment with
multiple syndrome rounds, a non-Pauli mechanism, mid-circuit measurement/reset, a raw per-shot
measurement Record, and detector/logical folding?

The gate was frozen before the target runs:

- distance 7, 49 data plus 48 ancilla qubits;
- 2 complete rounds as the first target; 7 complete rounds as the follow-on;
- raw measurement order fixed before execution;
- detector and observable XOR rows evaluated independently of the runtime;
- amplitude damping is the dissipative target; a Pauli twirl does not count;
- a coherent non-Clifford rotation is reported separately and does not count as dissipative Kraus;
- one shot can establish execution capability only, never a distribution or faithfulness claim;
- no result here counts as qutrit leakage.

## Result

| Runtime / path | Actual result | Scoped verdict |
|---|---|---|
| CUDA-Q GPU MPS, neutral XZZX d7/r2, no noise, bond 2 | Completed one 145-bit Record in 162.47 s; all 96 detector folds and the logical fold were zero; the v2 worker bound the canonical fixture, exact runtime versions, and environment lock | **YES, ideal execution capability only.** The all-zero raw row is not reference agreement: ideal Stim has random projected raw syndromes, and bond 2 has no faithfulness certificate |
| CUDA-Q GPU MPS, same r2, two-Kraus amplitude damping `p=0.01`, 49 data after each round, bond 16 | 98 explicit Kraus applications were compiled; 360.24 s hard timeout, rc 124, no Record | **NO usable target completion at this resource gate** |
| CUDA-Q GPU MPS, same dissipative target, bond 2 | Native `CUTENSORNET_STATUS_INTERNAL_ERROR`, segmentation fault rc 139 after 59.23 s, no Record | Reducing the bond does not rescue a robust channel path |
| PECOS native XZZX/SZZ d7/r7 construction and Clifford/Pauli sampling | 97 qubits, 132 ticks, 5,368 gate batches, 409 raw measurements, 360 detectors, 1 observable | **YES** for native XZZX structure, raw Record, detectors, and Pauli-representable sampling |
| PECOS GPU MPS, native XZZX d7/r7, coherent `RY(0.02)` after complete rounds, bond 16 | Completed one 409-bit raw Record in 239.12 s; 360 detector folds and 1 logical fold emitted | **YES** for coherent non-Pauli multi-round execution; not amplitude damping, leakage, or a faithfulness result |
| PECOS scalable MPS plus dissipative Kraus | MPS bindings contain unitary/projective gates and reset, but no channel/Kraus binding; actual amplitude damping is in the exponentially scaling density-matrix path | **NO current practical joint d7 path** |

The answer therefore depends on what “non-Pauli” means:

- **coherent unitary error:** PECOS has the required scalable gate surface;
- **actual dissipative Kraus channel:** neither tested stack produced a robust d7 multi-round Record;
- **qutrit leakage:** neither probe represents it.

This refutes any broad project differentiator phrased as “existing tools cannot express XZZX d7,
multiple rounds, non-Pauli operations, and Records.” It does **not** show that an external runtime
already supplies this repository's explicit multilevel leakage semantics, restricted
Carrier/evaluator boundary, or a certified full Record law.

## Neutral CUDA-Q fixture

`scripts/external_baselines/emit_xzzx_d7_capability_fixture.py` starts from Stim's flattened
rotated-Z-memory circuit and applies a gate-by-gate checkerboard local-H frame:

- selected data initialization `RZ -> RX`;
- selected data final measurement `MZ -> MX`;
- each interaction touching selected data becomes `H(data); CX; H(data)`;
- ancilla measurement/reset and every record offset keep their original order;
- only active sparse Stim ids are compacted, from a sparse span of 118 to 97 active qubits.

This produces genuine XZZX checks rather than relabeling samples from a CSS execution. In particular,
turning every selected-data interaction into `CZ` would be wrong when selected data is the CX
control.

| Complete rounds | Qubits | Raw measurements | Detectors | Observables | Dense Stim SHA-256 |
|---:|---:|---:|---:|---:|---|
| 2 | 97 | 145 | 96 | 1 | `193d56d199b45016d91e8d5742f52fdc4e8e3b74d571891c78e28f7ec4eca6bd` |
| 7 | 97 | 385 | 336 | 1 | `20a32d1cd1293d4d4d6e74d8af04fe7b1300ddb82dbf734f558fb764ad27c4d7` |

Independent Stim controls over 10,000 shots at each round count produced zero detector and logical
folds. Raw first-round projected syndromes were not assumed to be zero.

PECOS does not consume that neutral fixture. Its native
`interaction_basis="szz", clifford_frame_policy="checkerboard_xzzx"` circuit includes one initial
24-check measurement layer followed by the requested number of complete 48-check rounds and final
49 data measurements. Consequently:

| Complete rounds | PECOS raw width | PECOS detector width | Syndrome layers |
|---:|---:|---:|---:|
| 2 | 169 | 120 | 1 partial + 2 complete |
| 7 | 409 | 360 | 1 partial + 7 complete |

The PECOS worker skips the partial initialization layer and injects coherent `RY` only after each
complete 48-check round. The two runtime arrays must not be compared column-for-column.

## Environments and provenance

Both upstream clones remained pristine, including ignored paths:

| Runtime | Isolated environment | Installed version | Inspected source reference |
|---|---|---|---|
| CUDA-Q QEC | `ecs-baseline-cudaq-qec` | CUDA-Q 0.14.2; CUDA-Q QEC 0.6.0; cuTensorNet 2.12.2 | `external/baselines/cudaqx-qec-0.6.0` at `84d18ca948a8582afe54035c85e2aceb3f3bee19` |
| PECOS | `ecs-baseline-pecos` | `quantum-pecos==0.9.0.dev2`; `pytket-cutensornet==0.12.1`; cuTensorNet 2.13.0 | `external/baselines/PECOS` at `fa974197f0debd6478343c760af47f6faa4f04d2` |

`baseline-environment-cudaq-qec-linux-64.lock.json` and
`baseline-environment-pecos-linux-64.lock.json` record the observed installed state and selected
distribution `RECORD` hashes. They explicitly do not attest wheel bytes or fully hash-pin every
transitive pip artifact. The inspected commits are source references; the installed distributions
are not asserted byte-identical to those clones.

Two compatibility findings are load-bearing:

1. CUDA-Q's MPS path native-aborted with `cutensornet-cu13==2.13.0`. Pinning 2.12.2 made repeated
   Bell and multi-round measurement/reset controls pass.
2. PECOS's CUDA extra needed the CuPy `[ctk]` dependencies plus its environment-local
   `nvidia/cu13/lib` on `LD_LIBRARY_PATH`. After that, an RTX 5090 MPS constructor and gates ran.

Both environments pass `pip check`. GPU target runs were serialized on `/tmp/ecs_gpu.0.lock`; the
earlier exploratory runs that overlapped the GPU were discarded and are not evidence.

## Staged execution evidence

### CUDA-Q controls and target

Before d7:

- repeated Bell MPS controls passed after the cuTensorNet compatibility pin;
- a three-round ancilla `measure -> reset` kernel returned explicit per-shot measurement strings;
- a deterministic five-measure MPS control returned `10110` in execution order, ruling out an
  implicit bitstring reversal in the worker's Record fold;
- the same small MPS kernel accepted explicit two-operator amplitude damping;
- the CUDA-Q QEC surface helper completed a d3/two-round one-shot control with and without the
  custom Kraus channel.

The final fail-closed v2 d7/r2 no-noise run then completed:

- sample time: 162.4674 s;
- outer `/usr/bin/time` wall time: 165.29 s;
- outer `/usr/bin/time` peak host RSS: 5,332,908 KiB; the artifact's in-process
  `ru_maxrss` field is 5,170,504 KiB;
- observed GPU allocation: approximately 16,414 MiB;
- raw width 145, detector width 96, logical width 1;
- detector and logical folds: all zero.

Artifact:

- `outputs/simulator_validation/cudaq_xzzx_d7_r2_noiseless_capability_v2.json`
- SHA-256 `95a58927f36743cc40d7d76f5e307cf72abbf058839d00c275bc78ddcd35617d`

The artifact uses result schema v2. It binds canonical fixture SHA-256
`69f4be0f2e4020ba7dc16b58cf2edd1bb501936a984f75f9175168b267e62f13`, environment-lock
SHA-256 `b38b4b83b84685d323c601007535d2f983fe98e6ed724d40849185dac5ebe0cc`, exact critical
runtime distributions, and `is_non_pauli_active=false`.

The d7/r2 amplitude-damping target compiled 98 explicit Kraus applications. At bond 16 it hit the
360 s hard timeout:

- rc 124; no Record;
- peak host RSS: 8,805,784 KiB;
- observed GPU allocation: approximately 16,414 MiB.

Timeout ledger:

- `outputs/simulator_validation/cudaq_xzzx_d7_r2_amplitude_damping_timeout.json`
- SHA-256 `f86d0d1dc7036b0e45727719e7ac8b7e4334c854cad43c1d0876bfd35834d0f3`

The bond-2 retry did not time out: it failed earlier with a cuTensorNet internal error and native
segmentation fault after 59.23 s (rc 139, peak RSS 3,508,824 KiB). No r7 Kraus run was admitted
after both r2 gates failed.

### PECOS controls and target

The native d7/r7 circuit built in approximately 0.03 s. A Pauli-noise DEM sampler produced
detector/observable arrays of shape `(2, 360)` and `(2, 1)`, while the corresponding Stim conversion
produced a `(2, 409)` raw Record. This establishes native structure and record plumbing only.

The published Python package does not ship `pecos_rslib_exp` (`publish = false` at the inspected
commit), so its documented `sim_neo(TickCircuit)`/`RawMeasurementResult` route is not available in
the installed distribution. The repository-owned worker therefore iterates the native
`TickCircuit` through public MPS gate bindings. It also works around a PECOS wrapper defect where
`DefaultSimulator.run_gate` drops measurement outcome zero by truthiness; the worker calls the
public measurement binding directly so both bit values survive.

The final d7/r7 coherent run completed:

- 97 qubits, 132 ticks, 5,368 native gate batches;
- one 24-check initialization layer plus seven complete 48-check rounds;
- `RY(0.02)` on all 49 data qubits after each complete round: 343 applications;
- raw Record width 409, weight 193;
- detector width 360, 151 fired detector indices;
- one logical observable, not flipped in this shot;
- MPS maximum bond 16, float64;
- artifact-recorded execution time 239.1210 s;
- outer `/usr/bin/time` wall time 241.24 s and peak host RSS 1,871,436 KiB;
- normal exit code 0.

Artifact:

- `outputs/simulator_validation/pecos_xzzx_d7_r7_coherent_capability.json`
- SHA-256 `c489c096aa4e42e53d901e1dc134001f3060f2955e20d0ab2425f6e554367ddd`

The event count is descriptive only. With one shot and a finite bond cap, it is not an estimate of
a physical detector rate or evidence that the detector distribution is faithful.

Two exploratory outputs were moved under `outputs/simulator_validation/quarantine/` so that they
cannot be mistaken for current evidence:

- `cudaq_xzzx_d7_r2_noiseless_capability_v1_superseded.json`, SHA-256
  `20643fefbf495f9f45463b137161f1497486184031b13122e07851f510624570`, is a valid but
  pre-hardening CUDA execution superseded by the v2 artifact above;
- `pecos_xzzx_d7_r2_coherent_capability_invalid_exploratory.json`, SHA-256
  `aa62850e269efefdd6f69a51746c7a0da7e53b74f70835d24e6c40296dcb391b`, has invalid
  round-placement and detector-index interpretation and is explicitly **not evidence**.

## Falsifiers and focused tests

`tests/test_external_xzzx_d7_capability_fixture.py` protects:

- frozen r2/r7 dense circuit and canonical JSON fingerprints;
- exact shapes, detector arities, 97-active/118-sparse boundary, and measurement/reset ledger;
- raw-to-detector/logical folding with no bitstring reversal;
- removal of one conjugating H, removal of mid-round reset, and loss of one temporal record term;
- exact CUDA-Q Kraus placement: 49 data applications after every complete 48-MR round;
- zero-strength controls labeled inactive;
- PECOS's 24-check initialization layer versus complete-round semantics;
- both workers' critical runtime versions and root environment-lock binding;
- Conda URLs carrying actual SHA-256 fragments;
- installed-state-only provenance language.

Focused command:

```bash
conda run -n ecs python -m pytest -q \
  tests/test_external_xzzx_d7_capability_fixture.py
```

## Four ledgers

### Implemented

- two isolated environments and two installed-state locks;
- pristine source-reference clones at exact commits;
- one neutral XZZX d7 fixture emitter;
- one CUDA-Q neutral-fixture/MPS/Kraus worker;
- one PECOS native-circuit/MPS/coherent worker;
- focused fixture, Record, corruption, placement, runtime, and provenance tests;
- no change under `src/**`.

### Focused engineering evidence

- frozen fixture tests and falsifiers pass;
- environment `pip check` passes;
- target runs use fresh processes, a single GPU lease, hard timeouts, and flushed output;
- native aborts and timeouts remain negative evidence rather than being converted to skipped/pass.

### Scientific evidence

- none is claimed from one-shot finite-bond target runs;
- no distributional comparison, convergence in bond dimension, truncation certificate, calibrated
  channel, decoded logical-error rate, or qutrit leakage reference was established;
- exact Stim noiseless folds validate fixture semantics, not finite-bond noisy faithfulness.

### Release evidence

- these workers are not in `docs/service_status.json`, package entry points, or aggregate service
  acceptance;
- no product service or claim boundary was upgraded;
- the full suite, coverage gate, and release supervisor are not required to answer this external
  capability question and were not treated as scientific certification.

## Consequence for project positioning

The broad simulator claim has failed: XZZX geometry, d7 schedules, multi-round Records, detector
folding, scalable tensor-network execution, coherent non-Pauli gates, and small-scale/general Kraus
machinery all exist externally in overlapping products.

The surviving project question is narrower:

> Can this repository produce and independently validate the full multi-time Record for an explicit
> multilevel leakage process, while keeping evaluator-only truth out of emitted data and refusing
> unsupported finite-bond claims?

Nothing in this probe answers that question. It does show that “we can build an XZZX d7 non-Pauli
simulator” is not a defensible differentiator by itself.
