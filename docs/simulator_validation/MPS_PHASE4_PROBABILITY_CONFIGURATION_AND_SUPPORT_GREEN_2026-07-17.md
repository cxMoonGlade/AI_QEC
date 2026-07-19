# Restricted MPS Phase 4 — probability, configuration, and support hygiene — GREEN — 2026-07-17

> Historical phase snapshot. Schema identities and registry counts below describe this phase at
> review time; current identities live in `docs/SIMULATOR.md` and the frontend owning README.

## Disposition

Disposition: **MPS-006 through MPS-011 are GREEN inside the restricted MPS verification
contract**.

This phase closes the declared probability-mass, post-mutation norm, public-control, route-support,
and exact-bond defects. It does not register MPS as a scientific Carrier, certify a complete QEC
Record law, close the strict restricted-MPS coverage registry, complete Phase 5 consolidation, or
claim any time or memory optimization.

The implementation follows one ownership rule: only law-neutral validation and raw sampling
mechanics are shared. QT Kraus/projective completeness, MCWF projective completeness, MCWF
first-order jump residuals, support policy, and final acceptance remain route-owned.

## ID-by-ID behavior change

| ID | Before | After | Durable falsifier / boundary |
|---|---|---|---|
| `MPS-006` | Hard-coded `1e-15` cuts could relabel a representable positive branch as structural zero. Direct `1-exp(-x)` could cancel to zero for tiny positive `x` or saturate to the false open endpoint `1.0`. | [`probability.py`](../../src/error_coupling_simulator/carrier/mps/probability.py) preserves exact zero separately from every representable positive float. Products use the shared scaled arithmetic and raise when a positive result is not representable. `-expm1(-x)` is used for the stable open-interval decay probability and rejects false `1.0`. | Decimal-reconstructed tiny T1/T2 fixtures, minimum-subnormal versus zero, positive-product underflow, and the saturated endpoint are pinned in [`test_mps_phase4a_probability_and_norm.py`](../../tests/test_mps_phase4a_probability_and_norm.py). |
| `MPS-007` | MCWF standalone-reset and measurement-reset mutation could continue after a zero or nonfinite post-operation norm. | `_normalize_mcwf_mutated_state_` validates the raw squared norm before normalization. Zero, negative, NaN, and Inf fail loudly without a normalization multiply; the smallest positive subnormal remains legal and receives a finite normalization factor. | Both reset routes have negative controls for zero, negative, NaN, and Inf and a non-vacuous minimum-subnormal counterfixture. This is a post-operation validity guarantee, not a claim that a failed operation is transactionally rolled back. |
| `MPS-008` | Public integer, enum, real, sequence, boolean, and device controls could be narrowed or truth-value coerced before validation; aggregate or Carrier paths could reach CUDA, a child executor, or routing first. | [`controls.py`](../../src/error_coupling_simulator/carrier/mps/controls.py) rejects bool-as-integer, floats, numeric strings, bytes, nonfinite reals, invalid choices, empty devices, and out-of-range values. Integral controls use `operator.index`, preserving legal index-protocol objects. Every public MPS route validates its controls before its first CUDA/child/routing boundary. | The hostile matrix in [`test_mps_phase4b_configuration_support_and_bond.py`](../../tests/test_mps_phase4b_configuration_support_and_bond.py) covers QT direct plus four aggregate routes, MCWF direct and standalone contract, QT standalone contract, dense certification, forced Carrier routes, and Carrier auto routing with must-not-run sentinels. |
| `MPS-009` | QT support preflight inherited a support decision broad enough for MCWF, so `COH_*` families could pass QT preflight despite having no QT apply branch and then fail later. | QT and MCWF own separate predicates. QT structurally blocks every `COH_*` family it cannot lower. MCWF independently retains its eight implemented coherent Pauli families and does not import the QT private predicate. | Every coherent family has a QT structured-blocker fixture and an MCWF supported counterfixture; an AST gate forbids reintroducing the private QT predicate import into MCWF. |
| `MPS-010` | The qubit helper used `2**ceil(n/2)`, overestimating the exact-sufficient bond on odd site counts and over-blocking valid caps. The mixed-dimension helper returned the physical dimension rather than bond one for a single site. | Exact sufficiency is the maximum cut-product rank, `max_cut min(prod(left_dims), prod(right_dims))`. For uniform qubits this is `2**floor(n/2)`; mixed local dimensions use the same explicit cut formula; either single-site route returns one. | An independent hand-written cut-product oracle covers qubit widths 1–8 and all dimension tuples in `{2,3,4}` for widths 1–5. The retired formula is deliberately detected on `{1,3,5,7}`; a three-qubit cap of two is pinned exact-sufficient. |
| `MPS-011` | Candidate weights could be silently normalized before the raw total mass and residual were exposed, obscuring missing/excess probability and conflating QT completeness with MCWF first-order approximation error. | `RawProbabilityMass` freezes the unnormalized values, total, residual from one, and raw positive indices. Sampling normalizes only the validated positive weights for the categorical draw and maps back to the original index. Unvalidated or all-zero mass fails before RNG consumption. Route Adapters separately decide whether unit total is required. | Immutable/raw-order tests, RNG-state and raw-index counterfixtures, incomplete QT Kraus/measurement partitions, incomplete MCWF projective measurement, and the hand-derived MCWF `17/16` mass with `1/16` residual all pass. |

No shared helper chooses restricted acceptance, a numerical gate, or scientific meaning. The new
helpers validate and preserve values; the owning Adapter interprets them.

## Route-specific probability policy

| Surface | Raw-mass rule | Policy boundary |
|---|---|---|
| Shared `carrier/mps/probability.py` | finite, nonnegative, immutable raw values; exact zero retained; no implicit unit-mass requirement | Mechanics only; never decides whether a residual is acceptable. |
| QT exact and sampled Kraus/reset/measurement partitions | raw total must equal one within the registered QT total-probability residual gate `1e-8` before branch promotion or RNG use | QT Adapter owns completeness and fails an incomplete partition. |
| QT single projected branch | zero is a legal absent branch and is not normalized; a representable positive branch is normalized without pruning | The enclosing QT partition, not the scalar helper, establishes completeness. |
| MCWF projective level measurement | raw partition must equal one within `NUMERICAL_ZERO == 1e-12` before RNG use | MCWF measurement Adapter owns projective completeness. |
| MCWF first-order no-jump/jump candidates | finite nonnegative total may differ from one; both raw total and residual are emitted | The finite-step mass budget and certification/acceptance state machine evaluate the residual. The sampler does not relabel it as a complete QT partition. |

This separation is intentional. A common “normalize then sample” policy would hide the very MCWF
finite-step residual that restricted acceptance must see.

## Strict public-input timing

Invalid controls are rejected at the owner boundary, before the first operation capable of hiding the
error behind environment or route behavior:

- QT direct execution validates device, bond, branch/record caps, microsteps, finite-step choice,
  truncation gates, trajectory controls, seed, and dense-certification flag before CUDA. Bond sweep,
  seed sweep, evidence bundle, and resource probe validate their complete public surfaces before
  invoking a child; the resource probe also validates before CUDA memory instrumentation.
- QT standalone contract validates `device` before `_require_cuda_device`.
- MCWF direct execution validates device, local dimensions, bond, truncation gates, microsteps,
  finite-step choice, trajectory controls, initial levels, readout probability, and mass budget before
  CUDA. Its standalone contract validates device/local dimensions before CUDA.
- `dense_jointL_record_certification` validates `device`, `dense_channel_max_dim`, and every numerical
  gate before either a true-over-cap early return or level/Record/channel routing.
- Carrier forced QT/MCWF routes validate pass-through options before a child or CUDA. Carrier `auto`
  validates the device and all supplied MCWF options before CUDA acquisition and before the VRAM
  routing decision.

The negative table includes bool, float, string/bytes, nonfinite, invalid enum, zero/boundary, duplicate
sweep, and invalid sequence cases. A legal object implementing `__index__` while rejecting `int(...)`
is retained as the positive counterfixture; lossless Python index-protocol support was not removed in
the name of strictness.

## QT/MCWF coherent-support separation

The QT predicate now accepts only Hamiltonian families for which that executor has a lowering:
`ZZ`, `FSIM_PHASE`, and the declared supported `CTRL_*` controls at the correct support arity. It
returns a structured `unsupported_hamiltonian_family:<family>` blocker for:

`COH_RX`, `COH_RY`, `COH_RZ`, `COH_XX_YY`, `COH_XX`, `COH_YY`, `COH_ZX`, and
`COH_CROSSTALK_ZZ`.

MCWF has a separate `_is_supported_mcwf_hamiltonian_term` and retains all eight families with their
one- or two-site arity. This is not a shared route-mode switch: the policies remain in their respective
Adapters, and MCWF has no private QT support-predicate import.

## Exact-bond meaning

For an open chain with local dimensions `d_0, ..., d_(n-1)`, the largest Schmidt rank any state can
require across cut `k` is bounded by:

```text
min(product(d_0 ... d_(k-1)), product(d_k ... d_(n-1)))
```

The exact-sufficient bond is the maximum of this quantity over all cuts. It is a representation-capacity
statement only. It does not say that a smaller observed rank is inaccurate, that a finite cap produced
no local loss, or that discarded weight bounds the complete Record distribution. Actual split ledgers
and route acceptance remain separate evidence.

## Direct-schema hard cut

Phase 3 changed the direct QT/MCWF execution schemas from v2 to v3 for the Record-layout/reset repair.
Phase 4 changes both direct execution identities from v3 to v4:

- `error_coupling_simulator.frontend.qt_mps_restricted_execution.v4`;
- `error_coupling_simulator.frontend.mcwf_mps_state_record_execution.v4`.

The Carrier wrapper has an exact v4 schema registry and rejects any other direct-child schema. Current
source and tests contain no v3 direct-schema reader, alias, or fallback. The QT sweep, bundle, resource,
and restricted-acceptance policy schemas retain their own existing versions; a direct-child hard cut
does not silently relabel those different artifact families.

## Verification

Current-mainline invocations on 2026-07-17 produced:

| Gate | Result |
|---|---:|
| Phase 4A + 4B: `test_mps_phase4a_probability_and_norm.py` and `test_mps_phase4b_configuration_support_and_bond.py` | **196 passed** |
| Phase 1B firewall, independently | **343 passed** |
| Phase 1B + Phase 4 three-file selection | **539 passed** |
| Complete `test_simulator_axis1_schedule.py` | **179 passed, 1 skipped, 27 warnings** |
| Dedicated dense-certification file plus Phase-4 dense-control timing selection | **20 passed** |
| Full restricted-MPS registry behavior stage | **824 passed, 1 skipped, 27 warnings** |

The prior `534` combined snapshot predates the finalized hostile-control parameterization. It is not
used as the current Phase-4 count.

The behavior stage is GREEN, but the unchanged strict coverage target is not. The current audit is:

```text
COVERAGE-AUDIT: FAIL
units=32, under_target=7, missing_canonical=0,
stray_registered=0, exemption_errors=0
```

All eleven Phase-4 public helper functions — four in `probability.py` and seven in `controls.py` — are
at 100% statement and branch coverage. No target was lowered and no exemption was added.

The seven retained public-unit gaps and their current statement/branch counts are:

1. `carrier/mps/uncapped_nonlocal.py::preflight_uncapped_nonlocal_resource` — `20/25`,
   `13/18`;
2. `carrier/mps/uncapped_nonlocal.py::apply_uncapped_nonlocal_unitary` — `24/27`, `5/8`;
3. `frontend/_mps_actual_split.py::apply_capped_two_site_unitary` — `45/51`, `14/20`;
4. `frontend/_mps_actual_split.py::commit_mps_candidate_` — `23/30`, `10/14`;
5. `frontend/axis1_qt_mps_execution.py::axis1_qt_mps_trajectory_seed_sweep_manifest` —
   `32/37`, `4/8`;
6. `frontend/axis1_mcwf_dense_certification.py::dense_jointL_record_certification` —
   `43/47`, `26/30`; and
7. `frontend/axis1_mcwf_dense_certification.py::restricted_acceptance_policy` — `193/231`,
   `102/140`.

These remain coverage debt. Passing behavior plus full coverage of the new helpers does not convert
the overall strict registry into a release-green claim.

The bound coverage JSON SHA-256 is
`1ecc05642f6b408988532debdb8fd833fe93b8e88547f0087265da1c04d70f19`; the bound registry
SHA-256 is `5c209846c9d0a8d6e964386bc0a6760b6b9247feebce63c0f97ef3be98b807d8`.

## Isolated external comparators

The frozen external replays remain byte-authenticated and were not co-loaded into one long-lived
Torch/JAX/Aer process.

- **Aer:** the repo-owned orchestrator launched **15 fresh `ecs-baseline-aer` workers**; all state,
  truncation, gate-corruption, and worker-cleanup checks passed. Exact report SHA-256:
  `6d8143ba96a0a0607556a314db7185cfa0e413eb29ccaea801bf14758d353440`.
  The pristine clone is at `837c3ef3c39248aae936580360c22224dcefb265`. The installed Aer
  distribution is recorded separately and is not claimed to have been built from that clone.
- **YASTN:** the isolated `ecs-baseline-yastn` replay passed the product-MPS candidate-mass comparison,
  retained the hand-derived wrong-jump corruption, and imported no project module. Exact report
  SHA-256: `b6f17d3134eab7fdced7b1e981aef0721aa02456266979a902d6a81a7c00aa9f`.
  Its installed source tree is bound to the pristine clone at
  `595bd802ba0753a187b4bf7fd5c6d5007c0170d0`.

The complete external learning set is clean at the frozen commits:

| Clone | Commit | Status in this audit |
|---|---|---|
| Qiskit Aer | `837c3ef3c39248aae936580360c22224dcefb265` | clean; numerical replay above |
| YASTN | `595bd802ba0753a187b4bf7fd5c6d5007c0170d0` | clean; numerical replay above |
| variPEPS Python | `0edc81acc634e1465264d53f224101d66dcf04e2` | clean; code-learning reference only in Phase 4 |
| ITensorMPS.jl | `7ce812c42bfedcb3da1c250fdd5f19cb20394d4d` | clean; code-learning reference only in Phase 4 |

Aer validates a bounded qubit unitary-MPS state/truncation surface. YASTN validates a bounded
product-MPS raw candidate-mass construction. **Neither is an Axis-1 QEC trajectory-law, schedule,
reset, detector/observable Record, or restricted-acceptance oracle.** The load-bearing Phase-4 gates
therefore remain the hand-reconstructed scalar/cut-product references and corruption falsifiers.

## Remaining work and non-claims

Phase 5 is **not complete**. In particular, this report does not claim that all authenticated Quimb
state/split mechanics and raw truncation aggregation have been consolidated under their final
README-owned `carrier/mps/` owner, that every old private implementation has been deleted, or that
the Phase-5 dependency/documentation exit conditions have passed. The Phase-4 removal of one private
QT support-predicate dependency from MCWF is necessary but is not sufficient to close Phase 5.

No performance optimization was performed or accepted here. There is no new wall-time, peak-memory,
throughput, maximum-system-size, or production-scalability claim. Any later conservative optimization
must first preserve the Phase 1–4 independent falsifiers and then replay the isolated external
comparators; benchmark improvement cannot substitute for numerical or Record correctness.
