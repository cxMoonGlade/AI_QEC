# External baseline environments and comparison legs

How to rebuild the four isolated baseline environments and run the four external comparison legs.
Read this before running or repairing a leg; the upstream code anchors and pinned commits are in
[`TENSOR_NETWORK_CODE_MAP.md`](TENSOR_NETWORK_CODE_MAP.md).

A comparison leg is not simulator acceptance. Each leg compares one external implementation against
a repository-owned reference on frozen neutral fixtures; none of them establishes full-record
faithfulness.

## The four legs

| Leg | Environment | Compares | Runs |
|---|---|---|---|
| Qiskit Aer MPS | `ecs-baseline-aer` | qubit circuit MPS execution vs an independent dense reference | `ECS_RUN_AER_MPS_COMPARISON=1` |
| YASTN | `ecs-baseline-yastn` | frozen product-MPS MCWF candidate-mass arithmetic | `ECS_RUN_YASTN_MPS_COMPARISON=1` |
| QuTiP | `ecs-baseline-qutip` | continuous-time MCWF X/Z Record trajectories | `ECS_RUN_QUTIP_MCWF_XZ_COMPARISON=1` |
| ITensorMPS | `ecs-baseline-itensor` | canonical split: per-bond Schmidt spectra and truncation error | `ECS_RUN_ITENSOR_MPS_COMPARISON=1` |

Each leg's contract tests run in `ecs` with no external runtime present; the flag above enables the
isolated integration run only. Service acceptance supplies these flags itself.

## Rebuilding the environments

Every environment has a committed lock at the repository root. The locks record the exact conda
package set, the upstream commit, and how the running distribution is bound to the pristine clone.

```bash
# ITensorMPS (Julia): creates the env, installs from the pristine clone, writes the lock
conda create -y -n ecs-baseline-itensor -c conda-forge julia
python scripts/external_baselines/build_itensor_baseline_environment.py

# Aer (released wheel) and YASTN (commit-pinned source)
conda create -y -n ecs-baseline-aer python=3.12.13
conda run -n ecs-baseline-aer python -m pip install "qiskit-aer==0.17.2"

conda create -y -n ecs-baseline-yastn python=3.12.13
conda run -n ecs-baseline-yastn python -m pip install \
  "git+file://$PWD/external/baselines/yastn@595bd802ba0753a187b4bf7fd5c6d5007c0170d0"

# re-emit both locks from the built environments
python scripts/external_baselines/build_mps_baseline_environment_locks.py
```

QuTiP follows the recreation sequence inside `baseline-environment-qutip-linux-64.lock.json`.

### Two installation rules that are easy to get wrong

**Bind by commit, not by directory.** `pip install <path>` records `dir_info` in `direct_url.json`
and binds nothing: the same command against a modified clone succeeds silently. The YASTN and QuTiP
legs reject that and require `git+file://<clone>@<commit>`, which records `vcs_info` with the exact
commit. Aer is the deliberate exception — its orchestrator requires `direct_url` to be *absent*
because the leg runs the released wheel, so installing Aer from source makes the leg fail.

**A directory install pollutes the upstream clone.** Building from a clone writes `build/`,
`*.egg-info/` and a generated `_version.py` into it. All three are gitignored, so
`git status --porcelain` reports the clone clean while the leg later fails with an opaque
source-tree mismatch. Check with `git status --porcelain --untracked-files=all --ignored` and clean
the clone before rebuilding. External clones are pristine inputs; adaptors live in this repository.

## Running a leg

```bash
ECS_RUN_ITENSOR_MPS_COMPARISON=1 conda run -n ecs python -m pytest -q \
  tests/test_external_itensor_mps_comparison.py

# or the orchestrator directly, which publishes a report
conda run -n ecs python scripts/external_baselines/run_itensor_mps_comparison.py
```

Reports land under `outputs/simulator_validation/` and carry their own claim boundary, provenance
block, and content hash.

## CUDA-Q QEC and PECOS XZZX capability environments

These are capability probes, not two additional comparison legs and not registered simulator
services. Their installed-state locks are:

- `baseline-environment-cudaq-qec-linux-64.lock.json`
- `baseline-environment-pecos-linux-64.lock.json`

The locks record the complete observed distribution-version set, selected distribution `RECORD`
hashes, exact Conda package URLs, pristine source-reference commits, and the compatibility overrides
used here. They do **not** hash-pin every transitive pip artifact, attest wheel bytes, or establish
full recreation. Rebuild the installed-state ledgers with:

```bash
python scripts/external_baselines/build_xzzx_capability_environment_locks.py
```

The environments were created with these top-level steps:

```bash
conda create -y -n ecs-baseline-cudaq-qec python=3.12.13
conda run -n ecs-baseline-cudaq-qec python -m pip install \
  "cudaq-qec==0.6.0" "cudaq-qec-cu13==0.6.0" "stim==1.16.0"
conda run -n ecs-baseline-cudaq-qec python -m pip install \
  "cutensornet-cu13==2.12.2"
conda run -n ecs-baseline-cudaq-qec python -m pip check

conda create -y -n ecs-baseline-pecos python=3.13.14
conda run -n ecs-baseline-pecos python -m pip install \
  "quantum-pecos[cuda13]==0.9.0.dev2" "stim==1.16.0" \
  "nvidia-cublas==13.6.0.2"
conda run -n ecs-baseline-pecos python -m pip install \
  "cupy-cuda13x[ctk]==14.1.1"
conda run -n ecs-baseline-pecos python -m pip check
```

CUDA-Q 0.14.2 permits cuTensorNet `~=2.11`, but `cutensornet-cu13==2.13.0` caused a native
`CUTENSORNET_STATUS_INVALID_VALUE` abort on the minimal measurement/reset MPS control on this host.
Version `2.12.2` passed that control repeatedly and is therefore a required compatibility pin, not
an optional performance choice.

PECOS's CUDA extra did not by itself supply every runtime/header dependency needed by CuPy and
`pytket-cutensornet`. The `[ctk]` extra supplies those packages. The worker also requires the
environment-local library directory:

```bash
PECOS_PREFIX=/home/cx/miniforge3/envs/ecs-baseline-pecos
export LD_LIBRARY_PATH="$PECOS_PREFIX/lib/python3.13/site-packages/nvidia/cu13/lib"
```

Generate the frozen neutral CUDA-Q fixtures and run a worker as follows. GPU runs must hold the
same `/tmp/ecs_gpu.0.lock` used by the repository GPU pool; do not overlap the two environments.

```bash
conda run -n ecs python \
  scripts/external_baselines/emit_xzzx_d7_capability_fixture.py \
  --rounds 2 \
  --output-json outputs/simulator_validation/xzzx_d7_r2_fixture.json \
  --output-stim outputs/simulator_validation/xzzx_d7_r2_fixture.stim

CUDA_VISIBLE_DEVICES=0 ECS_GPU_SLOT=0 \
  flock /tmp/ecs_gpu.0.lock \
  conda run --no-capture-output -n ecs-baseline-cudaq-qec python \
  scripts/external_baselines/cudaq_xzzx_d7_capability_worker.py \
  --fixture outputs/simulator_validation/xzzx_d7_r2_fixture.json \
  --output-json outputs/simulator_validation/cudaq_xzzx_d7_r2_noiseless.json \
  --shots 1 --max-bond 2 --precision fp32 --damping-probability 0

CUDA_VISIBLE_DEVICES=0 ECS_GPU_SLOT=0 \
  LD_LIBRARY_PATH="$PECOS_PREFIX/lib/python3.13/site-packages/nvidia/cu13/lib" \
  flock /tmp/ecs_gpu.0.lock \
  conda run --no-capture-output -n ecs-baseline-pecos python \
  scripts/external_baselines/pecos_xzzx_d7_capability_worker.py \
  --rounds 7 --coherent-angle 0.02 --chi 16 \
  --output outputs/simulator_validation/pecos_xzzx_d7_r7.json
```

CUDA-Q consumes the neutral local-H XZZX fixture. PECOS instead consumes its native
`checkerboard_xzzx`/SZZ circuit. PECOS includes one 24-check initialization layer before the
requested complete rounds, so its raw and detector widths are 24 larger than the neutral Stim
fixture at the same `rounds`; the worker reports this difference rather than silently comparing
the arrays column-for-column.

The CUDA-Q non-Pauli mechanism is explicit two-Kraus amplitude damping on all 49 data qubits after
each complete round. The PECOS MPS mechanism is coherent `RY` over-rotation after each complete
round. PECOS's MPS gate bindings expose no dissipative Kraus/channel operation; its actual amplitude
damping implementation belongs to the exponentially scaling density-matrix path. Neither probe is
qutrit leakage, and finite bond dimension is not a Record-law faithfulness certificate.
The dated capability audit records the bounded `p=0.01` CUDA-Q attempts and their timeout/native
failure; the reproducible command above is the completed no-noise control, not a noisy-target pass.

## What each leg does and does not cover

Aer, YASTN and QuTiP pin execution results. None of them observes the canonical split itself: the
Aer leg does not compare against this project's carrier, the YASTN leg is a bond-dimension-one
product-MPS mass check that performs no SVD, and two of the three legs in
`scripts/mps_three_leg_comparator.py` run the same quimb that implements this project's splits.

The ITensorMPS leg exists for that gap. Its Julia worker applies every two-qubit gate through an
explicit orthogonalize/contract/SVD cycle instead of `apply`, because `apply` performs the same
split and discards its `Spectrum`; non-adjacent gates are routed into adjacency with SWAPs so every
split on the state is measured. It reports per-bond dimensions, Schmidt spectra, and the truncation
error at the moment of the split.

Two conventions are echoed as required result fields, because each is silently wrong-looking-right:

- amplitudes are little-endian with qubit 0 varying fastest, matching the Aer fixtures;
- spectra are **squared** Schmidt coefficients, so a maximally entangled bond reads `0.5`, not
  `0.707`.

Every fixture runs full rank first. A full-rank fidelity below `1 - 1e-12` aborts that fixture
before any capped row is scored: a convention error is invisible at full rank only by coincidence
and then masquerades as truncation damage. A deliberate corruption must be caught, because a
comparison that agrees with everything is indistinguishable from one that agrees with the truth.

## Provenance

| Leg | Binding |
|---|---|
| QuTiP | pristine commit/tree, selected installed solver sources, full distribution identity, exact 36-package lock conformance |
| YASTN | `direct_url` VCS binding to the pinned clone commit |
| Aer | installed-wheel name and version; the pristine clone is the source reference the code map reads, **not** the executed code |
| ITensorMPS | resolved package tree hash, `Manifest.toml` digest, and per-file digests of four named source anchors, re-checked against the clone after installation |

Julia has no `direct_url.json` analogue, which is why the ITensorMPS leg binds by tree hash and
per-file digests instead. Its builder also verifies the clone is unchanged after installation and
fails closed if it is not.
