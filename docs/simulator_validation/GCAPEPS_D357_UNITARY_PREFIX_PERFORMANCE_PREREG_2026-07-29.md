# GCAPEPS \(d=3,5,7\) unitary-prefix performance sweep — preregistration

Status: **FROZEN BEFORE IMPLEMENTATION OR TARGET EXECUTION, 2026-07-29;
effective in the first commit containing this file and its closure.**

Closure:
`GCAPEPS_D357_UNITARY_PREFIX_PERFORMANCE_LITERATURE_CLOSURE_2026-07-29.md`.

## 1. Question charter

Measure current-implementation time, completion/censoring, memory, and
representation resources for two equal-status candidates:

- `plain_quimb_physical_prefix_plus_local_ry`: physically apply every frozen
  complex128 H/CX gate to the Quimb state, then one raw complex128 local
  \(R_Y(0.137)\);
- `gcapeps_stim_frame_plus_rank2_tree_residual`: update one Stim frame with the
  identical batched H/CX circuit, then call the certified GCAPEPS physical
  Pauli-rotation API for the identical \(R_Y(0.137)\).

No candidate is truth. No vector, norm, Born probability, expectation,
fidelity, measurement, reset, trajectory, Record, detector, observable, or
logical error is an estimand.

## 2. Frozen fixture family

Start from Stim
`surface_code:rotated_memory_z(distance=d, rounds=2)` and apply the existing
checkerboard local-H XZZX conjugation and compact sparse-to-active qubit map.
The source uses two rounds only to bind the already audited emitter family.
The benchmark scans the transformed circuit in chronological order and stops
immediately before the first `MR`.

Before that stop:

- `R q` means the declared \(|0\rangle_q\) initial state and emits no gate;
- `RX q` emits exactly `H q`;
- `H` and ordered-control `CX` emit the corresponding gate;
- coordinates and `TICK` are metadata only;
- any other operation is a fixture-construction failure.

Thus this object is named the **first-measurement unitary prefix**, never a
syndrome-extraction round or Record.

The compact sites, gate counts, and frozen hashes are:

| \(d\) | \(n=2d^2-1\) | H | CX | total | unique graph edges | prefix stream SHA-256 | first-seen edge stream SHA-256 |
|---:|---:|---:|---:|---:|---:|---|---|
| 3 | 17 | 37 | 24 | 61 | 24 | `e8d5686a6ebb8c9ac9522a8dd623ff30f14cea89bb881e411a9ddaf0b9183c4b` | `d57e8b13c831565d4ecc327aa6481745a7d393055983acc76eb46a7e34cc5a51` |
| 5 | 49 | 117 | 80 | 197 | 80 | `44f13a5e55332af5009d78194ad99598d794172ca0bc7b0e1437ae67b12ac164` | `754033fa23821b43e7bbb14f179f8e3e863d8ff75e63ae8e76fae9cf23c25021` |
| 7 | 97 | 241 | 168 | 409 | 168 | `bd99a17547d398895992910ac9c836aceba05dfe82ccf261a9050cf42d71a5aa` | `ea3449fb76aa214de37e7b73e4f32c19eb68ff37309b38875e7056dda1d04c50` |

Prefix rows serialize as
`{index:04d}|{token}|{comma-separated compact targets}\n`.
First-seen undirected edges serialize with sorted endpoints as `{a},{b}\n`.
The full transformed two-round Stim hashes inherited from the existing
emitters are respectively:

```text
d3 7067b1241251bd7558e7dc85b2f84bc13a45c1217a49f8fcfa2e51205879ecb0
d5 be26b8708efe36a027bcf79074bc936de552b1a5d22b35b627d7d9cdbb27f008
d7 20a32d1cd1293d4d4d6e74d8af04fe7b1300ddb82dbf734f558fb764ad27c4d7
```

The logical Quimb site is the compact integer. The original Stim coordinate
is retained, along with

\[
\mathrm{row}=(x+y)/2-1,\qquad
\mathrm{col}=(x-y)/2+d-1.
\]

Every transformed coordinate must be an integer in
\([0,2d-2]^2\), unique, and every CX edge must have Manhattan length one in
this ledger. Quimb uses only the active arbitrary graph; missing bounding-box
sites are not padded.

## 3. Frozen non-Clifford row

Among `RX`-initialized graph-degree-four ancillas, choose the site minimizing
the squared physical-coordinate distance to \((d,d)\), then compact id. This
selects:

| \(d\) | physical ancilla \(a\) | coordinate |
|---:|---:|---:|
| 3 | 6 | `(3,3)` |
| 5 | 22 | `(5,5)` |
| 7 | 44 | `(7,7)` |

After the prefix, apply

\[
R_Y^{(a)}(\theta)=\exp[-i\theta Y_a/2],
\qquad \theta=\mathrm{float64}(0.137).
\]

This is one rank-two coherent Pauli rotation. It is not the separate
\(n=8,r=3\) fixture. The exact Stim signed pullbacks
\(C^\dagger Y_aC\), using `_` for identity, are:

```text
d3 -_____XYX____X_X__     support=(5,6,7,12,14)
d5 -_____________________XYX______X_X________________
    support=(21,22,23,30,32)
d7 -___________________________________________XYX____________X_X____________________________________
    support=(43,44,45,58,60)
```

Each support must be a connected four-edge star in the frozen graph. Stim and
an isolated, untimed SDIM-qubit path must agree on the signed word before
target timings are eligible.

The plain raw gate is built independently as
\(\cos(\theta/2)I-i\sin(\theta/2)Y\), with output-row/input-column axes.
The GC lane supplies the physical signed `Y` word and angle to
`GCAPEPSState.apply_pauli_rotation`; it may not inject the preregistered
pullback directly.

## 4. Common numerical and implementation boundary

Both lanes use the same frozen Quimb fork commit/tree and environment:

```text
dtype = numpy.complex128
to_backend = None
convert_eager = true
max_bond = None
cutoff = 1e-12
renorm = false
gauge_smudge = 0.0
equilibrate_every = None
```

The cutoff is the shared floating numerical threshold and removes numerical
null SVD directions. It is not advertised as exact-state, zero-truncation, or
matched-accuracy evidence. There is no finite bond cap. The GC tree lowering
itself remains uncompressed.

The plain worker must not import `quimb.experimental.gcapeps`. The GC worker
may not call `state_vector`, `to_dense`, `norm`, measurement, or generic
`apply_coherent_pauli_sum`. Candidate workers see only the neutral fixture and
their own private output.

The GC resource preflight is exact for the product residual and frozen
weight-five star:

| \(d\) | operator elements \(4n+76\) | candidate elements \(2n+38\) |
|---:|---:|---:|
| 3 | 144 | 72 |
| 5 | 272 | 136 |
| 7 | 464 | 232 |

For every distance, maximum local operator elements are 64, maximum local
candidate elements are 32, maximum predicted bond is 2, maximum routed-rank
product is 2, and maximum total-growth product is 2. Refactor factors remain
one. Any mismatch is a construction failure, not a larger permissive cap.

## 5. Timing, resources, and repetitions

The primary update samples are:

```text
plain_update_ns =
    physical_prefix_apply_ns + physical_local_ry_apply_ns

gcapeps_update_ns =
    tableau_prefix_apply_ns + certified_tree_rotation_apply_ns
```

The GC prefix is submitted as one Stim circuit and the plain prefix as one
tuple of raw Quimb gates; these are each candidate's native batched interface
for the same chronological rows. Initialization, import, fixture parsing,
post-update snapshots, and report serialization are excluded from
`update_ns` but remain in `worker_total_ns`.

Each distance and lane has one discarded fresh-process warmup and six
measured fresh-process samples. Measured order alternates
`plain,gcapeps` then `gcapeps,plain`, three times. Children run serially,
single-threaded, on the same pinned CPU. Retain all samples and report median
and MAD.

For jointly completed eligible lanes:

\[
R_t(d)=
\frac{\operatorname{median}t_{\rm plain}(d)}
     {\operatorname{median}t_{\rm gca}(d)}.
\]

\(R_t>1\) means GCAPEPS was faster only for that frozen point. Report the
analogous plain/GC ratios for process peak RSS, cgroup `MemoryPeak`, maximum
bond, tensor elements, and logical tensor bytes where defined. Do not fit an
asymptotic exponent or combine the three ratios into a universal verdict.

## 6. Censoring and release gates

Every child has the same 8-GiB memory limit, zero swap allowance, 300-second
wall limit, one-CPU affinity, empty CUDA visibility, and one-thread BLAS /
OpenMP settings. A timeout, OOM, or exact GC resource guard is retained as a
censored result. No cap, cutoff, gate stream, distance, or repetition count is
changed after seeing it. All three distances are attempted independently; a
censored smaller distance does not silently delete a requested larger point.
No finite performance ratio is emitted when either lane is censored.

Before target execution:

1. the existing \(n=8,r=3\) scoped regression, NumPy anchor, construction
   fixtures, Stim frame check, and SDIM-qubit check must pass;
2. fixture hashes/counts/coordinates, signed pullbacks, star routes, resource
   formulas, dtype/settings, and operation counts must pass;
3. a plain-worker prohibited-import control and a GC forbidden-contraction
   control must pass;
4. coefficient/sign, stream, target-order, route, cutoff, and timing-boundary
   corruptions must be detected;
5. the execution checkout must be commit/tree bound and pristine before and
   after the run.

Only the fixture, workers, controls, supervisor, and report schema are
authorized after this preregistration commit. Target execution is authorized
only after those controls pass.

## 7. Allowed terminal language

Allowed:

> On the frozen first-measurement XZZX unitary-prefix fixtures, Quimb fork,
> complex128 numerical settings, machine, and process envelope, the two
> equal-status candidates completed or were censored with the reported
> median/MAD update time, memory, bond, and tensor-resource ledgers.

Forbidden:

- either lane is truth or large-state faithful;
- the result certifies a measurement/reset/Record law;
- the three points establish an asymptotic scaling law;
- GCAPEPS is generally faster, keeps bonds generally small, or makes PEPS
  contraction efficient;
- the \(r=2\) sweep extends the \(n=8,r=3\) point as one controlled scaling
  series.
