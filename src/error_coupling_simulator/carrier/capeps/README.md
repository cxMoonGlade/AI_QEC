# carrier/capeps

Status: **all-qubit Clifford-augmented PEPS engineering prototype; not a
canonical Record backend or Record-faithful carrier**.

`capeps` keeps one algebraic representation invariant (Stim omits the
physically irrelevant global phase of a Clifford),

```text
|psi> = C |phi>,
```

where `C` is a Clifford frame and `|phi>` is a residual state.  Clifford
operations update `C` only.  A coherent physical Pauli expansion

```text
U = sum_j c_j P_j
```

is pulled through the frame term by term,

```text
Q_j = C^dagger P_j C,
|phi> <- (sum_j c_j Q_j) |phi>.
```

The coefficients remain complex amplitudes.  This package never replaces the
sum by a Pauli twirl or independently sampled Pauli alternatives.

## Modules

- `algebra.py` owns the qubit specialization of GCAMPS Eq. (5), including
  GF(2) generator decomposition, explicit ordered-product phase recovery,
  complex128 Clifford synthesis, and small-local-unitary Pauli expansion.
- `frame.py` owns the untruncated Clifford-frame boundary.  Stim 1.16 is the
  installed all-qubit owner.  The optional SDIM adapter targets SDIM 1.3.3
  (official source inspected at commit
  `115c495b23ade35ef0f68b7299afef463129bf51`) and is deliberately qubit-only:
  SDIM's full qudit Clifford algebra is not the repository's
  computational-qubit-plus-leakage direct-sum model.
- `residual.py` owns the untruncated complex128 dense residual and the NumPy/Quimb
  open-boundary PEPS residual.
- `state.py` owns coherent updates, explicit measurement forks, conditional
  branch log mass, computational-basis measure-reset, Pauli expectations, and
  local Clifford refactorization exact up to global phase. Constructor inputs
  and public frame/residual access are defensive snapshots.

The source-located, top-down formula ledger and code mapping is
[the GCAMPS formula implementation audit](../../../../docs/simulator_validation/GCAMPS_2511_06672_FORMULA_IMPLEMENTATION_AUDIT_2026-07-27.md).

PECOS is a future isolated differential-reference candidate.  No CAPEPS–PECOS
comparator is currently implemented or accepted.  Any future comparison must
independently lower the neutral input; PECOS is not imported into this
prototype runtime path.

## Minimal use

```python
import stim

from error_coupling_simulator.carrier.capeps import CAPEPSState

state = CAPEPSState.peps_zero((1, 2))
state.apply_clifford(stim.Circuit("S 0\nCX 0 1"))
update = state.apply_ry(0, 0.02)
branch_0, branch_1 = state.fork_measurement(
    stim.PauliString("Z_"),
    reset_to_zero=True,
)

print(update.pulled_back_terms)
print(update.residual_update)
print(branch_0.conditional_probability, branch_1.conditional_probability)
```

To request the optional SDIM frame explicitly, construct
`SdimCliffordFrame(num_qubits)` and pass it as `frame=...` to `dense_zero` or
`peps_zero`.  `sdim_backend_status()` reports the pinned availability first;
there is no silent fallback from SDIM to Stim.  SDIM is absent from the current
acceptance environment, so the live SDIM gate path is not claimed as tested.

## Untruncated prototype surface

- all-qubit Clifford circuits with no measurement, reset, or noise inside the
  frame update;
- coherent Pauli expansions and Pauli rotations, including the sign returned
  by tableau conjugation;
- Eq. (5) stabilizer/destabilizer exponents with an explicit
  \(\{\pm1,\pm i\}\) phase ledger and a direct-pullback consistency gate;
- arbitrary small-local-qubit unitary expansion into all `4**k` Pauli terms,
  without a floating structural-zero filter; the public default is `k <= 2`,
  and larger support requires explicit `max_local_qubits` opt-in;
- one- and adjacent two-site Clifford refactorization, exact at the physical-ray
  level: `(C, |phi>) -> (C Q^dagger, Q |phi>)`;
- normalized physical Pauli expectation values;
- forced or two-way Pauli-measurement branches;
- `Z` measure-reset via
  `A_b = |0><b| = X^b (I + (-1)^b Z) / 2`;
- dense complex128 residuals and finite open-boundary Quimb PEPS residuals.

For a one-site pulled-back expansion, Quimb contracts one complex128 local
operator into the site tensor and does not grow a virtual bond.  For a
multi-site expansion it uses Quimb's untruncated PEPS algebraic direct sum.  This
preserves coherence without a dense multi-site gate, but grows all virtual
bonds additively.  No truncation, compression, simple update, boundary
approximation, or hidden dense fallback is performed.

## Correctness boundary

The physical-ray algebra follows exactly by induction:

1. `G C |phi> = (G C) |phi>` for a Clifford `G`.
2. `P C = C (C^dagger P C)` for every signed Pauli term.
3. A physical Pauli projector pulls through by the same identity, while its
   pre-normalization norm supplies the conditional Born probability.
4. For `Z` measure-reset, the conditional physical `X^b` is left-multiplied
   into the frame after projection.

That proof covers the untruncated algebraic representation implemented here,
up to complex128 floating evaluation.  It does
not certify approximate contraction, finite-bond truncation, a complete
multi-round detector/observable Record, leakage, Kraus noise, d5/d7, logical
error rate, or scaling.  `MeasurementEvent` is an ordered raw branch ledger,
not `RecordBatch`.

Focused tests use separately written complex128 matrices on one- and
two-qubit fixtures to catch frame composition direction, Eq. (5) transpose and
phase errors, signed Pauli pullback, local-unitary reconstruction,
coherent-versus-twirled semantics, exact-refactor direction, observable/Born
consistency, branch isolation, tiny positive probabilities, reset, and Quimb
bond growth. Passing those tests is engineering evidence only.

The floating branch boundary is deliberately asymmetric: an upper-bound
contraction overshoot within `NUMERICAL_ZERO` is clamped to one, but no positive
probability is floored to zero.  Consequently, algebraic cancellation can still
leave a mathematically structural-zero PEPS branch as a tiny positive floating
branch.  Closing that case needs symbolic reachability or an independent
complement-consistency certificate, not a blanket threshold.

Registration records an engineering-mechanics prototype only.  The existing
full-PEPS XZZX v2 preregistration does not authorize CAPEPS target execution,
Record-law claims, or an efficiency comparison.  CAPEPS-specific literature
closure and preregistration remain open before any such experiment.
