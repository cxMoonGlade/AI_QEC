# QuTiP-family master-equation backend review

**Status:** theory-first backend suitability review, 2026-06-28.

**Question.** After cloning `qutip`, `qutip-cuquantum`, and `qutip-jax` under
`external/baselines/`, should the QEC coupling simulator use the QuTiP family as
the main backend for master-equation evolution?

## Decision

Use the QuTiP family as a **master-equation reference/probe layer**, not as the
canonical Axis-1 G2 channel-evidence backend.

Concretely:

1. **Keep `qec_twin.forward.joint_lindbladian` as the canonical G2 backend.**
   G2 needs dense channel evidence: Liouvillian, one `expm(L*dt)`, superoperator
   equality witnesses, Choi/Kraus reconstruction, and process-infidelity rows.
   The current torch-GPU assembler was written exactly for that evidence object.
2. **Use QuTiP core as the field-standard definition/oracle.**
   QuTiP is excellent for defining `H + c_ops`, building `qt.liouvillian`,
   checking superoperator conventions, and deriving small channels before they
   are converted into engine-ready Kraus.
3. **Use qutip-cuquantum as an optional state/density evolution probe backend.**
   It supports `sesolve`, `mesolve`, and `mcsolve` on GPU-backed cuDensityMat
   objects. It is best for large composite tensor-structured systems where the
   tensor structure is preserved. It is not the right object for G2's full dense
   Choi/superoperator ledger, but it is valuable as an independent continuous
   `H + c_ops` evolution probe.
4. **Do not put qutip-jax on the mainline yet.**
   Its own README marks the plugin as pre-alpha. It is useful later for
   differentiable calibration/prototype gradients, not for release-bearing
   teacher evolution.

## Grounding inputs checked

- Project contract: `qec_coupling_simulator_build_contract.md` defines Axis-1 as
  one within-substep `L_substep = -i[sum H_i, .] + sum D[c_i]` and one
  `expm(L_substep*dt)`, with G2 as the headline composed-vs-joint channel gate.
- Existing implementation: `forward/joint_lindbladian.py` already implements the
  dense torch-GPU Liouvillian -> superoperator -> Choi/Kraus -> process-fidelity
  evidence path, and states its convention against `qt.liouvillian`.
- Existing tests: `tests/test_joint_lindbladian.py` validates the torch backend
  against both QuTiP `liouvillian(...).expm()` and a hand-written scipy
  column-stacking Liouvillian.
- Existing QuTiP prereg: `qutip_channel_derivation_prereg.md` already declares
  the original architecture: QuTiP derives/validates channels, the engine applies
  engine-ready Kraus.
- New cloned upstreams:
  - `external/baselines/qutip`
  - `external/baselines/qutip-cuquantum`
  - `external/baselines/qutip-jax`

## Upstream capability findings

### QuTiP core

QuTiP's `mesolve` is exactly a Lindblad/von-Neumann master-equation solver. Its
interface accepts a Hamiltonian or Liouvillian plus collapse operators, including
time-dependent `QobjEvo` forms. This is the clean reference language for our
master-equation mechanisms.

QuTiP's `mcsolve` is also a proper quantum-trajectory solver for `H + c_ops`.
That makes it useful as a small-system conceptual/oracle bridge to our MCWF
carrier. It does **not** replace our finite-Kraus/qutrit trajectory executor,
because our production MCWF path has QEC-specific record packing, qutrit
conventions, leakage readout, source-conditioned parameters, and GPU-only
artifact semantics.

**Verdict:** strong reference/oracle; not production mainline for G2.

### qutip-cuquantum

qutip-cuquantum provides cuQuantum cuDensityMat data layers for QuTiP and is
designed for large composite quantum systems via tensor-network contractions on
GPU. Its docs say the tested solvers are `sesolve`, `mesolve`, and `mcsolve`,
with cuQuantum-specific methods such as `CuVern7`.

The limitation is shape of evidence. qutip-cuquantum optimizes **state/density
evolution** with tensor structure. G2 needs **channel evidence**: dense
superoperators, equality witnesses, Choi states, Kraus stacks, and row-level
process-infidelity JSON. Forcing qutip-cuquantum into full dense channel
materialization would discard the tensor structure it is designed to preserve.

**Verdict:** suitable optional backend for state/density master-equation probes
and small/medium continuous `H + c_ops` cross-checks; not the canonical G2
channel-evidence backend.

### qutip-jax

qutip-jax gives QuTiP a JAX linear-algebra backend and autodiff path. It supports
JAX/diffrax solver usage in docs, but the README explicitly says the plugin is
pre-alpha and not ready for use.

**Verdict:** research/prototype only; no release-bearing teacher backend.

## Environment smoke

Ran:

```bash
conda run -n aiqec python /tmp/qutip_family_backend_smoke.py
```

Observed:

```text
qutip 5.3.0
qutip_mesolve_trace 1.0
qutip_cuquantum imported
qutip_jax 0.1.1
qutip_cuquantum_mesolve_trace 1.0
```

The qutip-cuquantum smoke also printed several `converting to Dense` messages.
This is not a failure, but it is a warning against treating a tiny 2-level smoke
as evidence that the tensor-structured path will remain efficient after dense
channel materialization.

## Backend allocation

| role | backend | status |
|---|---|---|
| Axis-1 G2 canonical channel evidence | `qec_twin.forward.joint_lindbladian` | **keep as mainline** |
| Independent convention/oracle | QuTiP core + scipy | **keep and expand** |
| State/density continuous `H + c_ops` probe | qutip-cuquantum | **add optional adapter after G2/teacher wiring** |
| Differentiable prototype/calibration | qutip-jax | defer |
| qutrit finite-Kraus leakage MCWF production | native torch/CUDA/qutrit MCWF | keep |

## Why not replace G2 with qutip-cuquantum?

The simulator's anti-toy gate is not merely "can evolve a density matrix under a
master equation." It is:

1. build the joint within-substep Liouvillian;
2. build the naive composed alternative;
3. compare them as channels;
4. prove exact-zero pairs by a structural Liouvillian-commutator witness;
5. produce row-level evidence with `1 - F_e` process infidelity.

qutip-cuquantum helps most when the object remains a tensor-structured state or
density matrix. G2 intentionally asks for dense channel objects. So using
qutip-cuquantum as the G2 mainline would fight its design and weaken the
evidence contract.

## Recommended next build path

1. Continue Axis-1/Axis-2 convergence with the existing canonical backend:
   `source_coupling.py` -> schedule adapter -> `joint_lindbladian.py` ->
   `CoupledCycleTeacher` truth/records.
2. Add a **QuTiP-family oracle adapter**, not a replacement backend:
   - `qutip_core_liouvillian_oracle`: small-window `H,c_ops -> S` reference.
   - `qutip_cuquantum_state_probe`: optional `H,c_ops,rho0,tlist -> states/expect`
     probe for larger tensor-structured sanity checks.
   - explicit manifest flag: `oracle_backend=qutip|qutip-cuquantum`, never
     `production_truth`.
3. Gate the adapter on:
   - same trace/positivity for small `mesolve` probes;
   - same final state as canonical dense channel on a tiny window;
   - no claim that qutip-cuquantum emits G2 Choi/process evidence.

## Decision boundary for future reversal

qutip-cuquantum may become a production evolution backend only if we define a new
record-level carrier contract where the primary evidence is state/density
trajectory output, not dense channel comparison. That would be a new backend
class, not a replacement for G2.
