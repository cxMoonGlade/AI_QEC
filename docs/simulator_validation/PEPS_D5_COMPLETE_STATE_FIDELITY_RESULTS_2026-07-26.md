# PEPS d5 complete-state fidelity — execution result

Date: 2026-07-26

Status: **bounded operational success; registered aggregate
`inconclusive_partial`.**

Both eligible external PEPS implementations materialized the frozen 25-qubit
state at `D=1,2,4`. Both crossed the preregistered useful-fidelity threshold
`F >= 0.99` at `D=2` and approached unity at `D=4`. The `D=8,16` complete-state
contractions were resource-unavailable, so the frozen five-point aggregate
cannot issue `pass` and the conditional `D=16` exactness prediction remains
not evaluable.

This answers the narrow operational question — a d5 5-by-5 coherent
non-Pauli pure-state fixture can be run with high global fidelity — but it is
not evidence for Kraus noise, leakage, syndrome rounds, a QEC Record, LER,
d7, or general scalable/exact two-dimensional contraction.

## Frozen object and terminal artifact

| field | value |
|---|---|
| run commit | `a95ba0fa05f423d4d7949600669ce8ff163a304f` |
| fixture | open 5-by-5, 25 qubits, 272 ordered operations, four cycles |
| fixture canonical SHA-256 | `c73b932ff8c213d6dce956cddb9bee0c9bfa2b465bde3bc6a3ece5789aed1324` |
| state compared | every one of `2^25` amplitudes, one-dimensional C-order `complex128`, q0 most significant |
| metric | normalized squared whole-state overlap, Evenbly Eq. (12) |
| terminal file | `outputs/simulator_validation/peps_d5_sweeps_20260726_a95ba0f/sweep_result.json` |
| terminal file SHA-256 | `d38298d99f71bce356bdc7d453b26f4fa43e7a7595f4c084b79059a6c3f826b4` |
| canonical content SHA-256 | `35a80f11ce29da4396045318d6c0c6ec4204f2eb4282e9095d9bd113a57afbd9` |
| resource envelope per point | 1800 s, 64 GiB host peak, 28 GiB device allocation |
| device | NVIDIA GeForce RTX 5090, 33,711,521,792 physical bytes |

The result is an ignored local numerical bundle rather than a committed
binary artifact. The terminal JSON binds the child summaries, comparisons,
logs, environment locks, worker sources, fixture, and run HEAD by SHA-256. An
independent post-run streaming calculation over the six persisted candidate
vectors reproduced every fidelity below exactly at the displayed precision.

## Complete-state results

| implementation | `D=1` | `D=2` | `D=4` | `D=8` | `D=16` |
|---|---:|---:|---:|---|---|
| Quimb | `0.0000851688316772418` | `0.9998969172932962` | `0.9999999860634252` | `UNAVAILABLE`: typed CUDA OOM | `UNAVAILABLE`: typed CUDA OOM |
| Pepsy | `0.00008516883167724169` | `0.9998327620972642` | `0.9999995335988606` | `UNAVAILABLE`: CUDA OOM while requesting 16 GiB | `UNAVAILABLE`: predicted 4 TiB exact-contraction intermediate |

The completed prefix is increasing for both implementations, but the
preregistered monotonicity statement covers all five points and is therefore
not evaluable. Likewise, the non-degeneracy control was frozen as
`F(D=16)-F(D=1)>1e-4`; substituting `D=4` after seeing the result is forbidden.
For that reason both terminal candidate aggregates are
`inconclusive_partial`, even though each contains two individually useful
complete-state points.

At the best completed point:

| implementation | best completed bond | fidelity | infidelity | host peak | device peak | point wall time |
|---|---:|---:|---:|---:|---:|---:|
| Quimb | 4 | `0.9999999860634252` | `1.39365748e-8` | 2,532,909,056 B | 1,678,082,048 B | 9.552 s |
| Pepsy | 4 | `0.9999995335988606` | `4.664011394e-7` | 2,509,402,112 B | 1,677,830,656 B | 6.536 s |

Pepsy rejected `D=16` before allocating the predicted
4,398,046,511,104-byte contraction intermediate. Quimb and Pepsy each
reported a typed CUDA allocation failure for `D=8`; those rows are resource
rejections, not measured low fidelities.

## Controls

| control | result | required |
|---|---:|---:|
| d3 independent Torch versus NumPy amplitudes | pass | every amplitude within `1e-12` |
| Quimb d3 `D=16` | `F=0.9999999999999998` | `F >= 1-1e-10` |
| Pepsy d3 `D=16` | `F=1.0` | `F >= 1-1e-10` |
| d5 operation-156 sign flip | `1-F=0.0930572223836359` | `1-F > 1e-4` |
| focused contract suite | 26 passed | all pass from committed code |
| final independent review | pass | no false-fidelity or false-pass blocker |

Every successful producer reported the actual applied-operation count, exact
requested bond, finite `complex128` state, frozen basis convention, pristine
source identity, and matching run HEAD. Cotengra path search was explicitly
serial, so worker peak RSS did not omit a path-search process pool.

## External source and environment identity

All four assessed repositories are full, non-shallow, and pristine including
ignored paths:

| repository | origin | commit | role in this run |
|---|---|---|---|
| Pepsy | `https://github.com/quantinuum-dev/pepsy.git` | `27cb956ec88a739daece90407833bd3c3f8e1d8f` | eligible complete-state candidate |
| Quimb | `https://github.com/jcmgray/quimb.git` | `3c89529fe0a3487133a3928201691161e110abdf` | eligible complete-state candidate |
| TensorNetworkQuantumSimulator.jl | `https://github.com/JoeyT1994/TensorNetworkQuantumSimulator.jl.git` | `b5d4089849de1cc23806aa8325e8db56a55f2e0b` | not admitted: no public d5 complete-state exporter; local Julia also reports a CHOLMOD ABI mismatch |
| YASTN | `https://github.com/yastn/yastn.git` | `595bd802ba0753a187b4bf7fd5c6d5007c0170d0` | not admitted: no bounded public route to the required global d5 vector |

The executed environment locks are:

- `baseline-environment-quimb-peps-linux-64.lock.json`, SHA-256
  `f0bd527f51d63911bf0c78f292a703e815d6299dacdfb99a9455b12f9c553e87`;
  schema v2 binds all 118 installed Quimb Python source files byte-for-byte
  as well as the VCS commit and full distribution state.
- `baseline-environment-pepsy-linux-64.lock.json`, SHA-256
  `b8758397b2e0c49b0707a158fcbe513e05af742a931616ca04b299afe72c9bea`;
  it binds the installed Pepsy source and exact observed distribution state.

## Decision

The narrow user criterion is met: d5 ran, and two separately packaged external
PEPS routes produced global complete-state fidelity above `0.9998` at `D=2`
and above `0.9999995` at `D=4`. They are not fully independent
implementations: Pepsy depends on Quimb, and its tested gate/contraction path
reuses Quimb tensor primitives. Agreement across the routes is therefore
useful adapter evidence, while the independently implemented dense reference
is the fidelity referee.

The stronger registered claim is not met because it deliberately required a
complete `D=[1,2,4,8,16]` sweep and a `D=1` versus `D=16` non-degeneracy
control. The result therefore permits treating Pepsy and Quimb as credible
pure-state d5 adapter bases; it does not yet permit a leakage/Record claim or
an exact/scalable PEPS claim.

## Reproduction

The output directory must not already exist.

```bash
env -u PYTHONPATH PYTHONNOUSERSITE=1 \
  conda run -n ecs python \
  scripts/external_baselines/run_peps_d5_complete_state_sweeps.py \
  --output-directory \
  outputs/simulator_validation/peps_d5_sweeps_20260726_a95ba0f \
  --candidates quimb pepsy
```

The preregistration and source closure are
`PEPS_D5_PURE_STATE_FIDELITY_PREREG_2026-07-26.md` and
`PEPS_D5_PURE_STATE_FIDELITY_LITERATURE_CLOSURE_2026-07-26.md`.
