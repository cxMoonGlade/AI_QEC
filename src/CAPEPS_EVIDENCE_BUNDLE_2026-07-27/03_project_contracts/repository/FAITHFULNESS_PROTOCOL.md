# Faithfulness protocol — current simulator gate

This protocol governs every claim that a current `error_coupling_simulator` process, channel,
carrier, or emitted record represents its declared mathematical object. It is an acceptance
contract, not a historical narrative. `docs/SIMULATOR.md` defines the product boundary;
`docs/METRICS.md` defines the registered comparisons.

## Required gate

A faithfulness claim is admissible only when all of the following are present.

### 1. Freeze the object and coordinate

Name the process, carrier, parameter regime, record coordinate, precision, and supported horizon.
Do not compare raw syndromes with temporal detector events, a reduced detector error model with an
analog channel, or a state-only quantity with a multi-time record claim.

### 2. Use an independent reference

The reference must be capable of failing differently from the implementation under test. Accepted
routes are:

- an exact or separately formulated density-matrix calculation;
- a raw caller-supplied circuit artifact with independently checked semantics;
- a closed-form identity derived from a cited primary source;
- a from-scratch reconstruction that shares neither the implementation path nor the suspected
  simplification.

An implementation compared with its own helper, cache, or reformatted output is a regression check,
not an independent reference. If no feasible independent reference exists, the result is
`UNANCHORED`.

### 3. Require a discriminating falsifier

Every load-bearing invariant needs a deliberate corruption that the gate rejects. The corruption
must alter the claimed object, and the unchanged positive path must still pass. An inert control
forces `FAIL`; skipping or allowlisting it does not close the claim.

### 4. Declare and bound simplifications

Every truncation, projection, factorization, finite-step approximation, precision change, fitted
contraction, and reduced representation must declare:

- what object it changes;
- where it is applied;
- the metric used to compare it with the reference;
- a bound or a paired independent comparison in the claimed regime.

An unbounded simplification cannot support a faithfulness conclusion. Resource caps and local
tensor objectives remain implementation diagnostics unless a proved bridge connects them to the
record metric.

### 5. Freeze numerical provenance

Every claim-bearing value follows `docs/NUMERICAL_PROVENANCE.md`: source kind, exact locator,
units, scope, and transformation chain. Literature equations justify a form, not an uncited
amplitude. Project defaults, numerical tolerances, and resource limits are not evidence of hardware
realism.

## Current owner-backed falsifiers

| Surface | Required invariant and corruption | Current owner and gate |
|---|---|---|
| Record boundary | Inputs are binary before narrowing, copied, immutable, shape-consistent, and expressed in the declared raw-syndrome or detector coordinate. Corrupt values, padding, schema, prior, or fold direction must be rejected. | `carrier/records.py`, `carrier/record_fold.py`; `tests/test_record_batch_units.py`, `tests/test_carrier_record_fold.py` |
| Formal certification | A feasible independent anchor must disagree after stabilizer corruption or destruction of record order. A control that does not fire makes the report fail. | `certify/core.py`, `certify/anchors/controls.py`; `tests/test_certify_core_units.py`, `tests/test_certify_contracts.py` |
| Channel algebra | Kraus completeness, Choi/PTM construction, joint-vs-composed behavior, and exact commuting controls must respond to sign, support, ordering, and generator corruptions. | `carrier/cptp_channel.py`, `carrier/joint_lindbladian.py`, `certify/channel_diagnostics.py`; their registered owner tests |
| Exact qutrit probabilities | Structural zero probabilities remain zero; non-finite, non-Hermitian, non-positive, or non-positive-trace states are rejected rather than repaired into a distribution. | `carrier/exact/qutrit_dm.py`; `tests/test_qutrit_dm_measurement_semantics.py` |
| Qutrit leakage | Leakage rates, Kraus maps, readout semantics, and reference independence must change under physically targeted corruptions. | `mechanisms/qutrit_leakage.py`, `frontend/qutrit_leakage.py`; the `qutrit_leakage_channel_and_process` acceptance files |
| Source-conditioned record process | Shared, matched-marginal, and source-off arms must remain distinct; schema, field routing, temporal order, and source-to-parameter corruptions must be detected. | `source/`, `noise_processes/coupled_cycle.py`; the `classical_finite_rtn_source_chain` acceptance files |
| Finite-RTN research diagnostic | Factorized formulas must agree with separately formulated full-state oracles, while wrong rate convention and omitted-factor corruptions must disagree. | `scripts/finite_rtn_free_induction_diagnostic.py`; `tests/test_finite_rtn_free_induction_diagnostic.py` |
| PEPO/PEPS research carriers | Dense d3 comparisons, trace/negativity checks, host ownership, truncation corruptions, and independent entropy checks remain mandatory. | `carrier/pepo/`, `carrier/peps/`; their registered acceptance files |

Passing a local invariant does not promote an open carrier. PEPO remains a bounded research carrier;
PEPS full-record finite-truncation fidelity remains open, and its current FET entropy falsifier is a
scientific blocker.

## Verdict semantics

The current certification types define the allowed outcomes:

- `PASS` — every required exact row passed and every required control fired;
- `PASS*` — exact rows and controls passed, while sampled rows remain provisional;
- `FINDING` — a registered sampled prediction missed its band;
- `FAIL` — an exact invariant failed or a required control was inert;
- `UNANCHORED` — no feasible independent reference exists;
- `CONTROL` — an explicit falsifier row, never a positive result.

No status is upgraded because a carrier is expensive, a reference is infeasible, or a result looks
plausible. A failed scientific gate remains visible until the current implementation passes the
unchanged invariant or the claim is withdrawn.

## Evidence packet

Before a faithfulness claim enters current documentation, its packet must contain:

1. the frozen object, supported regime, and excluded regimes;
2. the source owner and exact source hash;
3. the independent reference and an independence argument;
4. the invariant ledger and one demonstrated corruption per load-bearing invariant;
5. the simplification list and bound or paired comparison;
6. the registered metric, epistemic class, and comparison band;
7. the numerical-provenance manifest;
8. the executable test or script, result artifact, environment identity, and artifact hashes.

Missing items stop claim propagation. Test success proves only the object named by the test; it does
not automatically certify another carrier, a larger distance, a longer horizon, a hardware device,
or the complete record.
