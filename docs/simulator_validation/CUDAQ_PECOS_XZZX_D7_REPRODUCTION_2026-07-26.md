# Independent reproduction of the CUDA-Q / PECOS XZZX d7 capability probe

Date: 2026-07-26. Status: **neither runtime produces a usable XZZX d7 multi-round non-Pauli
Record. Both execute the target and both emit a Record whose contents are truncation
artifacts.**

The prior record's PECOS verdict ("YES for coherent non-Pauli multi-round execution") is
wrong. Its CUDA-Q verdict ("NO usable target completion") is right in substance and wrong in
its stated reason: the leg does complete when given the budget, but its Record carries no
attributable dissipative signal.

An earlier draft of this file claimed CUDA-Q occupied the dissipative row. A p -> 0 control
on the same code path refuted that, and the claim is withdrawn below.

This is a reproduction record, written separately from the document it corrects so the
correction can be reviewed before that document is edited. Every number below was produced
on this machine in this session by running the committed workers, or by reading installed
source at a named version.

Scope: engineering capability and reproduction only. Nothing here is a faithfulness claim,
a distribution, or a logical error rate for any runtime, ours included.

## What reproduced exactly

| target | prior record | this run |
|---|---|---|
| CUDA-Q ideal XZZX d7/r2, bond 2, no noise | one 145-bit Record in 162.47 s, all 96 detector folds zero | **163.54 s**, 1010 operations, 0 damping applications, raw 145 bits with **0 ones**, **0/96 detectors fired**, observable 0 |
| PECOS native XZZX/SZZ d7/r7 construction | 97 qubits, 132 ticks, 5,368 gate batches, 409 raw measurements, 360 detectors, 1 observable | identical on every field; also 1170 `SZZ`, 2030 `H`, `checkerboard_xzzx` frame, build 0.030 s |
| PECOS d7/r7 coherent `RY(0.02)`, bond 16 | one 409-bit Record in 239.12 s | **267.5 s**, 409 raw, 360 detectors, 7 coherent layers, 343 injections |

The fixture regenerated to the same shape: 97 qubits, 145 measurements, 96 detectors,
stim sha256 `193d56d199b45016d91e8d5742f52fdc4e8e3b74d571891c78e28f7ec4eca6bd`.

## Correction 1 — CUDA-Q completes the dissipative target, but the Record carries no signal

The prior record reports the two-Kraus amplitude-damping leg as "360.24 s hard timeout,
rc 124, no Record", and concludes **"actual dissipative Kraus channel: neither tested stack
produced a robust d7 multi-round Record"**.

Rerunning the same committed worker, same fixture, same `--max-bond 16
--damping-probability 0.01`, with the only change being a 1800 s budget instead of 360 s:

```
worker: kernel built operations=1010 damping_applications=98 max_bond=16 precision=fp32
worker: CUDA-Q sample end elapsed_seconds=1586.521443
EXIT_RC=0
```

It completes in **1586.5 s** and writes a Record. The Record is not degenerate:

| leg | raw width | raw ones | detectors fired | observable |
|---|---|---|---|---|
| ideal, bond 2 | 145 | 0 | 0 / 96 | 0 |
| **dissipative, bond 16** | 145 | **58** | **31 / 96** | 0 |

The 31 fired detectors were re-folded independently from the fixture's own `detector_rows`
and matched the worker's emitted detector bits exactly.

So the *completion* is real and the stated reason in the prior record — a hard timeout — is
not what blocks it. The `READING_ORDER.md` entry ("times out or native-crashes") is wrong as
a description of what happens with an adequate budget.

**But the Record is not usable, and the control that establishes this was missing from both
the prior probe and the first draft of this one.** The noiseless comparison must hold the
code path and the bond fixed and vary only the physical parameter, because a run without a
`noise_model` takes a different CUDA-Q path. Pushing the damping probability to `1e-12`,
physically indistinguishable from zero, with the same bond 16 and the same 98 Kraus
applications:

| leg | raw ones | detectors fired | damping applications | seconds |
|---|---|---|---|---|
| ideal, bond 2, p = 0 | 0 / 145 | 0 / 96 | 0 | 163.5 |
| **p = 1e-12, bond 16 (control)** | **58 / 145** | **35 / 96** | 98 | 507.2 |
| p = 0.01, bond 16 (target) | 58 / 145 | 31 / 96 | 98 | 1586.5 |

The control fires **more** detectors than the target, and the raw record has identical
weight. The 31 events are therefore a bond-16 truncation artifact on the noisy code path,
not a dissipative signal. **The claim that CUDA-Q occupies the dissipative d7 multi-round
row is withdrawn.** The separate noiseless bond-16 run on the noise-free path did not
finish inside 2400 s (rc 124), so it contributes nothing either way.

What survives is narrower and worth stating precisely: CUDA-Q *executes* an explicit
two-Kraus amplitude-damping channel 98 times across a 97-qubit XZZX d7 two-round circuit and
emits a folded Record, in 1586.5 s at 26.6 GB. It does not demonstrate that the Record
reflects the channel.

The real constraint is memory, not expressiveness: `max_rss_kib = 26598084` (26.6 GB) on a
33.7 GB RTX 5090.

Two further facts bound this capability, both read from the installed runtime:

- CUDA-Q 0.14.2 exposes `KrausChannel` and `KrausOperator` alongside the built-ins
  (`AmplitudeDampingChannel`, `BitFlipChannel`, `DepolarizationChannel`, `Depolarization1`,
  `Depolarization2`, `PhaseDamping`, `PhaseFlipChannel`). Arbitrary user Kraus operators are
  accepted, so the dissipative surface is general rather than an amplitude-damping special
  case.
- CUDA-Q has **no qudit type at all**. `cudaq.qvector(size: int)` is qubits only,
  `hasattr(cudaq, "qudit")` is `False`, and no name in the namespace matches
  `qudit|qutrit|level|dim`. A third level is not merely unused in this probe, it is
  unrepresentable in that stack. Encoding one qutrit into two qubits (as Camps et al.
  arXiv:2406.04083 do with Qulacs) is a route, untested here, and would take the patch from
  97 to 194 qubits.

## Correction 2 — PECOS executes far more mechanisms than RY, and none of them yields a usable Record

### The mechanism surface is much wider than the probe used

The prior worker hardcodes one mechanism: a single-qubit, single-axis `RY(theta)` layer on
all 49 data qubits after each complete round. The PECOS MPS bindings expose **86 gates**,
including the continuous non-Clifford entries `RX RY RZ R1XY T Tdg` and, on two qubits,
`RZZ RXX RYY RXXRYYRZZ R2XXYYZZ CRX CRY CRZ SqrtZZ`.

A uniform single-axis rotation is also the weakest available reading of "non-Pauli": it is
Gaussian, which is exactly why Marton & Asboth (Quantum 7, 1116 (2023)) reach a full 2D
d=19 patch with exact fermionic linear optics. The mechanism that is neither Gaussian nor
free-fermion reducible is two-qubit `RZZ` residual crosstalk, which is the model Harper,
Nakhl, Sevior & Usman (arXiv:2605.29514v1) use for their d=9 result.

`scripts/external_baselines/pecos_xzzx_d7_mechanism_probe.py` runs the same frozen native
construction and swaps only the injected mechanism. All five complete at d7/r7, chi=16:

| mechanism | raw | detectors | fired | obs flips | injections | seconds |
|---|---|---|---|---|---|---|
| `none` (control) | 409 | 360 | **126** | 0 | 0 | 308.3 |
| `ry_layer`, RY(0.02) | 409 | 360 | 151 | 0 | 343 | 298.6 |
| `t_layer`, T = pi/4 | 409 | 360 | **151** | 1 | 343 | 286.4 |
| `r1xy_layer`, two-angle | 409 | 360 | **151** | 0 | 343 | 238.8 |
| `rzz_per_2q`, Harper-class | 409 | 360 | 143 | 1 | **1260** | 453.8 |

So "PECOS can only do RY" is a property of the prior worker, not of PECOS.

### But the control the prior probe never ran destroys the result

An ideal noiseless run must fire **zero** detectors. The `none` control fires **126 of 360**.

The circuit and the detector definitions are not at fault. Driving the identical circuit
through PECOS's own `SparseStab` stabilizer backend, with the identical
`extract_detection_events_and_observables` definitions:

```
STABILIZER noiseless: raw=409 ones=122 detectors_fired=0 obs_flips=0 in 0.1s
```

Exactly zero, in a tenth of a second. (The 122 raw ones are expected: ancillas are not
reset, so raw outcomes are random and only the folded differences must vanish.)

Two further observations make the Record unusable rather than merely noisy:

1. `RY(0.02)`, `T` (a pi/4 rotation, two orders of magnitude larger) and `R1XY` all report
   **identically 151** fired detectors. No physical mechanism produces that.
2. The MPS backend is healthy at small scale, so this is not a measurement or collapse bug:
   H-then-measure gives 24/40 ones over 40 independent seeds, repeated measurement agrees
   40/40, Bell-pair correlation is 40/40, and `Init`-after-measure resets 40/40.

### The cause is bond truncation, established from observables rather than from a bound

Noiseless `none` control, d7/r7, versus chi:

| chi | d7/r7 fired (correct answer 0) | seconds | | chi | d7/r2 fired | bonds at cap | fidelity lb |
|---|---|---|---|---|---|---|---|
| 4 | 128 / 360 | 109.1 | | 16 | 62 / 120 | 160/192 | 1.23e-47 |
| 16 | 126 / 360 | 267.0 | | 64 | 55 / 120 | 140/192 | 1.70e-46 |
| 64 | 120 / 360 | 1254.3 | | 128 | 47 / 120 | 122/192 | 1.08e-42 |
| | | | | 256 | 53 / 120 | 124/192 | 1.70e-45 |

These are single shots, so the variation across chi is not a trend — chi=256 comes back
*worse* than chi=128. The defensible statement is the qualitative one: **from chi=16 to
chi=256, a sixteenfold increase, the noiseless run keeps firing 40-50 percent of its
detectors where the correct answer is exactly zero, and the bonds pinned at the cap fall
only from 160/192 to 124/192.** The MPS never escapes the ceiling.

### The cause is confirmed by locating the exactness threshold at a size where it exists

At d3 the whole system is 17 qubits, so a large enough chi makes the MPS exact and there is
no truncation left to blame. Five shots per point:

| chi | d3 fired over 5 shots (correct 0) | fidelity lower bound |
|---|---|---|
| 16 | 28 | 1.59e-05 |
| **64** | **0** | **1.000** |
| 256 | 0 | 1.000 |
| 512 | 0 | 1.000 |

This does three things at once. It **validates the probe** — at sufficient chi it agrees
exactly with the stabilizer reference. It **confirms truncation as the cause** rather than a
gate-convention or measurement defect. And it shows the fidelity lower bound is *tight when
there is no truncation*: it reads exactly 1.000, so "fidelity_lb == 1" is a sound
no-truncation certificate even though the bound cannot quantify a truncated state.

Scaling of the same noiseless control at chi=16, r=3:

| d | qubits | MPS chi=16 fired | stabilizer | chi needed for exactness |
|---|---|---|---|---|
| 3 | 17 | 5 / 28 | 0 | **64** |
| 5 | 49 | 22 / 84 | 0 | > 256, not located |
| 7 | 97 | 74 / 168 | 0 | far beyond 256; fidelity lb ~1e-45 there |

d3 already needs chi=64. That is the wall, measured here rather than argued.

**A caveat that must travel with these numbers.** The pytket MPS object also reports
`fidelity`, and at chi=16 it reads `3.14e-29` then `1.23e-47`, with 168 of 192 bonds pinned
at the cap. That number is a **lower bound**, defined in
`pytket/extensions/cutensornet/structured_state/mps.py:67` as "A lower bound of the
fidelity, obtained by multiplying" per-truncation fidelities, accumulated as
`self.fidelity *= this_fidelity` over thousands of gates. A product of thousands of factors
slightly below one decays exponentially even when the true state fidelity is far better, so
that reading corroborates the conclusion and cannot carry it. The conclusion rests on the
noiseless control against an independent stabilizer reference, and on the
mechanism-insensitivity, both of which are direct observations.

This is the same wall Manabe, Suzuki & Darmawan name when they fix their patch width at 3
and defer two-dimensional connectivity to "tensor network ansatz beyond MPS"; the table
above is that wall measured on this machine.

## Correction 3 — the PECOS `leak` gates are not a leaked level

The prior record states that neither probe represents qutrit leakage, which is correct, but
does not say why, and the MPS bindings do contain `leak`, `leak |0>`, `leak |1>`,
`unleak |0>` and `unleak |1>`. Reading
`pecos/simulators/mps_pytket/bindings.py:32-36`:

```python
"leak":       init_zero,
"leak |0>":   init_zero,
"leak |1>":   init_one,
"unleak |0>": init_zero,
"unleak |1>": init_one,
```

`leak` is an alias for state re-initialization. There is no third level in the state;
leakage is tracked as a classical qubit set in the machine layer
(`pecos/machines/generic_machine.py`). This is the same class as Google Pauli+, Riverlane's
LCD flag-and-depolarize, and Plaquette's XPauli classical label.

## Correction 4 — PECOS has no Kraus binding on any backend, not just none on MPS

The prior record says the MPS bindings have no channel or Kraus entry and that "actual
amplitude damping is in the exponentially scaling density-matrix path". The first half is
confirmed: `mps_pytket` exports only `MPS, bindings, gates_init, gates_meas,
gates_one_qubit, gates_two_qubit, patch_nvmath_cupy_external_stream, state`, and across the
whole package `Kraus` appears only in `quantum_info.py`.

The second half is imprecise. `amplitude.?damp|dissipat` has **zero** matches anywhere in
the installed Python surface, so PECOS ships no named amplitude-damping channel at all;
`KrausOps` is a `pecos_rslib.quantum_info` type rather than a simulator gate; and the
`density_matrix` backend exposes no `kraus|channel|noise|damp` attribute either. The
accurate statement is that **no PECOS backend exposes a Kraus or channel gate binding on
the Python surface in this installed version**, so the dissipative route is closed by API,
not merely by the cost of a 4**97 density matrix.

## Corrected verdict table

| mechanism at XZZX d7, multiple rounds | verdict | evidence |
|---|---|---|
| coherent single-axis unitary | executes; **no usable Record at any chi tested** | this record, Correction 2 |
| coherent two-qubit `RZZ` (Harper-class) | executes, 1260 injections in 453.8 s; same Record defect | this record, Correction 2 |
| maximally non-Clifford `T` layer | executes; same Record defect | this record, Correction 2 |
| dissipative two-Kraus amplitude damping | executes 98 Kraus applications, completes in 1586.5 s at 26.6 GB; **Record carries no attributable signal** — a p=1e-12 control on the same path and bond fires 35/96 versus the target's 31/96 | this record, Correction 1 |
| physical third level carried in the state | **not representable** | CUDA-Q has no qudit type; PECOS `leak` is `init_zero` |

The project consequence, stated without spin: **on this machine, neither external runtime
produces a usable XZZX d7 multi-round non-Pauli Record.** Both execute; both emit Records
dominated by bond truncation; and in both cases the defect is only visible once a control
holds everything fixed except the physical mechanism. That control was absent from the prior
probe and from this record's first draft.

This does not restore any project differentiator. The coherent rows remain occupied in the
literature by methods that do not carry the code state in a truncated ansatz at all —
Marton & Asboth's exact fermionic linear optics to d=19, Harper et al.'s Clifford tableau
plus an MPS over the deviation at d=9 — and those results are unaffected by anything
measured here. What this record establishes is narrower: two specific installed stacks, at
the bond dimensions reachable on one RTX 5090, do not get there, and the reason is the
ansatz, not the budget.

The one row still unoccupied anywhere is a physically carried third level, matching the
independent literature sweep in
`docs/simulator_validation/ENGINEERING_ROWS_LITERATURE_CHECK_2026-07-26.md` and its d=3
frontier for that family.

## My own errors in this reproduction, recorded

- I summed the return of `extract_detection_events_and_observables` as if it were a bit row.
  It returns per-shot lists of fired detector **indices**, so my first mechanism run
  reported "2833 events" out of 120 detectors. Fixed to `len()`; those two numbers are void.
- I first read the flat chi trend (128 at chi=4, 126 at chi=16) as evidence that truncation
  was *not* the cause. The correct reading is that both are saturated. The chi=64 point and
  the bonds-at-cap count settle it the other way.
- I described the pytket `fidelity` reading as a measured state fidelity before checking its
  definition. It is a lower bound accumulated as a product; see the caveat above. The d3
  threshold scan later showed the bound *is* tight at 1.000 when nothing truncates, so it is
  usable as a no-truncation certificate — but that was established afterwards, not assumed.
- I read a trend into single-shot data twice: first that the flat chi=4/chi=16 pair showed
  truncation was not the cause, then that 62/55/47 showed slow convergence. chi=256 returning
  53 exposed both. Single shots can disqualify (any nonzero firing on a noiseless run is
  disqualifying) but cannot establish a rate or a trend.
- I asserted that d7 had "no reachable chi, an ansatz problem rather than a resource problem"
  before running the d3 positive control that could distinguish truncation from a probe bug.
  The conclusion survived the control, but I stated it before earning it.
- Worst: I wrote that CUDA-Q occupied the dissipative row on the strength of 31 fired
  detectors, without the p -> 0 control on the same code path and bond — the exact control
  whose absence I had just used to overturn the PECOS verdict. The control refuted the claim.
  The prior record was closer to right than I was on that leg.

## Reproduction commands

```bash
P=$CONDA_PREFIX_PECOS/lib/python3.13/site-packages/nvidia/cu13/lib   # env-local CUDA runtime

conda run -n ecs python scripts/external_baselines/emit_xzzx_d7_capability_fixture.py \
  --rounds 2 --output-json fx.json --output-stim fx.stim

conda run -n ecs-baseline-cudaq-qec python \
  scripts/external_baselines/cudaq_xzzx_d7_capability_worker.py \
  --fixture fx.json --output-json cudaq_damped.json \
  --damping-probability 0.01 --max-bond 16      # needs > 1600 s, not 360 s

env LD_LIBRARY_PATH="$P:$LD_LIBRARY_PATH" conda run -n ecs-baseline-pecos python \
  scripts/external_baselines/pecos_xzzx_d7_mechanism_probe.py --rounds 7
```

Runtimes: PECOS 0.9.0.dev2, pytket 2.18.1, cupy 14.1.1, Python 3.13.14. CUDA-Q 0.14.2,
cudaq-qec 0.6.0, cutensornet-cu13 2.12.2, cupy 13.6.0, driver 13030, RTX 5090 33.7 GB.
