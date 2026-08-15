# Restricted MPS Phase 2 — MPS-001 uncapped nonlocal repair — GREEN — 2026-07-17

## Status and root cause

Disposition: **MPS-001 GREEN inside its bounded contract**.

For a gate on three or more sites, Quimb 1.14 `auto-mps` first converts the dense operator to an MPO.
The outer caller's `cutoff=0.0` is forwarded only to the later MPS/MPO compression; the first
dense-to-MPO split inherits Quimb's default nonzero cutoff. Therefore the old call site looked
explicitly uncapped while a weak component had already been deleted.

The independent NumPy fixture applies

```text
U = exp(-i * 2e-6 * X tensor X tensor X)
```

to `|000>`. The required `|111>` amplitude is
`-i * sin(2e-6) = -i * 1.9999999999986667e-6`. The inherited `auto-mps` route returned exactly zero
for that amplitude. The repaired route agrees with the independent dense state at absolute tolerance
`2e-14`, for both one microstep and four refined microsteps.

## Repair

`carrier/mps/uncapped_nonlocal.py` is a minimal execution-mechanics module. It is explicitly **not a
registered scientific Carrier** and makes no state-, Record-, LER-, or production-faithfulness
claim.

The helper:

1. validates strictly ascending support, declared local dimensions, source backend/dtype/device,
   finite unitary shape, and source norm;
2. rejects before gate materialization or dense allocation above five support sites, support Hilbert
   dimension 256, or 65,536 dense operator elements;
3. deep-copies the source;
4. calls `MatrixProductOperator.from_dense(..., method="svd", max_bond=None, cutoff=0.0,
   cutoff_mode="rsum2", renorm=None)`;
5. calls `gate_with_submpo_(..., method="direct", max_bond=None, cutoff=0.0,
   cutoff_mode="rsum2", normalize=False)`;
6. rejects nonfinite tensors or unitary norm drift; and
7. returns a validated candidate plus a versioned mechanics event. The frontend commits it with the
   existing transactional rollback helper.

Only `max_bond=None` connected clusters of three through five sites use this path. Capped multi-site
clusters remain fail-closed; the existing two-site actual-split path and QT route are unchanged.

## Evidence and falsifiers

`tests/test_mps_uncapped_nonlocal.py` reports **16 passed** and covers:

- the inherited-cutoff negative control and independent weak-term oracle;
- one-versus-four-microstep preservation;
- exact resource-cap equality and over-cap must-not-materialize/must-not-allocate behavior;
- duplicate, unsorted, boolean, and out-of-range support/dimension corruption;
- wrong-shape, nonunitary, and nonfinite gates;
- Quimb construction failure, candidate norm corruption, source immutability, and transactional
  commit semantics; and
- a public `CircuitBuilder -> schedule -> MCWF manifest` fixture that emits one authenticated
  `[0,1,2]` uncapped-nonlocal event.

The expanded static cutoff gate reports **11 passed** and now covers
`MatrixProductOperator.from_dense`, `gate_with_submpo`, and `gate_with_submpo_` in addition to direct
tensor splits. Removing any named cutoff from its representative calls turns the scanner RED.

The legacy two-site actual-split suite remains **49 passed**. The combined focused Phase 1/2 group is
**443 passed, 1 skipped**; the code-map check is current with input SHA-256 prefix `8b44cdb3169a` and
27 validated services.

## External-comparator boundary

Final isolated Aer and YASTN replays remain byte-identical and their clones remain clean. They check
their own declared unitary-MPS and candidate-mass responsibilities. The load-bearing MPS-001 oracle
is the hand-constructed NumPy state, because neither existing external adapter is a trajectory/Record
oracle for this connected MCWF cluster. No external result is promoted beyond that scope.

## Remaining RED surface

MPS-001 does not make local zero-cutoff decomposition a global error bound. Finite-bond multi-site
ledgering, complete adaptive Record-law validation, d5/d7 faithfulness, and performance optimization
remain open. The numerical-only allocation ceilings may be changed only with a new resource study;
they cannot be tuned to manufacture a scientific pass.
