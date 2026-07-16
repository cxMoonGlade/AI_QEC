# Tensor-network truncation differential audit — 2026-07-16

## Status

The diagnostic phase is complete. No file under `src/**` was changed.

- The isolated Qiskit Aer MPS comparison is **PASS** for its declared qubit-circuit scope.
- The CUDA/Quimb actual-split diagnostic is **PASS** for its declared split-observation scope.
- The PEPS/FET replay, fallback-contract, and stabilizer-entropy gates are **RED**.
- The external repositories remain pristine. Their implementations are engineering comparators,
  not equivalent QEC trajectory or record-law oracles.

The immediate conclusion is asymmetric:

1. MPS needs an actual-split and probability-mass accounting surface before a safer adaptive cap can
   be evaluated.
2. PEPS/FET first needs fail-closed update semantics and behavior-neutral diagnostics. Changing the
   truncation optimizer before those two repairs would confound solver quality with a confirmed
   control-flow defect.

## Claim boundary

This audit compares numerical behavior and implementation discipline. It does not certify the
complete MPS or PEPS simulator.

- Aer covers qubit circuit state evolution and local MPS truncation. It does not implement this
  repository's multilevel MCWF process or emitted detector/observable record law.
- Quimb is the tensor backend used by the current restricted MCWF/MPS execution path. The new
  probe observes its real `auto-mps` split sequence, but the small frozen fixtures are not a
  complete channel test.
- YASTN finite PEPS evolution is the closest external comparator for gate-to-local-environment
  truncation, but its process and observables still differ.
- variPEPS is an infinite/periodic iPEPS and CTMRG implementation. It is useful for convergence,
  projector, SVD, and numerical-health practices; it is not a finite open-boundary trajectory
  oracle.
- Local discarded weights, local environment fidelity, state overlap, and entropy remain
  state/resource diagnostics. None alone proves the multi-round record law.

The binding PEPS requirement in
[PEPS_FET_VALIDATION.md](PEPS_FET_VALIDATION.md) remains unchanged: no FET source change or claim
promotion without literature closure, a constraint ledger, an independent corruption falsifier,
and explicit source-change confirmation.

## Frozen evidence

| Artifact | Scope verdict | Byte SHA-256 | Content SHA-256 |
|---|---:|---|---|
| `outputs/simulator_validation/diagnostics/aer_mps_comparison/report.json` | PASS | `4baa72ea7c1d2ebbdadaa33ba12d70ec97db1788505fbd21937ba0830b0568a7` | `ac87689ca0032510ad0cd4a26b52f124464f32ecaec9a40bac0253ca47396e3c` |
| `outputs/simulator_validation/diagnostics/mps_actual_split/fixtures.json` | frozen input | `b05369763a99a2de6bf0b825e975e41ef08641970cc6dd292b261f022bf7c2ac` | `79e6c6ed614f24cc9b19c0e0bdeaf4827d599178589cb692c827178881474fdc` |
| `outputs/simulator_validation/diagnostics/mps_actual_split/result.json` | PASS | `adcdf935585c9219973a03d693614964d41598798ace22e03235a289c13f5693` | `7da0b18278b13d6f62f90a73fd43900fb389bbfa5282628ce20a943c03494c36` |
| `outputs/simulator_validation/diagnostics/peps_fet_replay_audit/report.json` | RED | `6b9760926b16327bfd5a74f4fb2568d846c51dd3ee76a5d22ba63b4eeb314dfc` | `a0766dd8aab19ca5bc9a3c93ddefd409b41eff5ac9e13b2c6b15aa66ce0938bd` |

The Aer workers ran one fresh process per circuit-policy pair in `ecs-baseline-aer` with
Qiskit 2.5.0 and Qiskit Aer 0.17.2. The orchestrator did not import Qiskit. The frozen Aer clone is
pristine at `837c3ef3c39248aae936580360c22224dcefb265`; its MPS C++ subtree is unchanged from
tag 0.17.2. The installed distribution's provenance was captured, but its cryptographic relation to
that clone is explicitly **not established**.

The Quimb probe ran in a fresh `ecs` CUDA process with Quimb 1.14.0, Torch 2.12.0,
CUDA 13.0, complex128 tensors, and an NVIDIA GeForce RTX 5090. Process-group cleanup passed.

The FET report is bound to git commit
`a9229c584b7e1c30a52328ac62be6df3855a0b44`. Repeated seed-0 fresh processes were scoped-bitwise
identical. This establishes that the seed-0/debug-off baseline trajectory and its fallback/entropy
RED observations are scoped-bitwise repeatable across two fresh processes; the seed-1 and
debug-on cases were not independently repeated.

## MPS differential result

### Aer against an independent dense oracle

All full-rank results have fidelity 1.0 against a hand-typed little-endian dense oracle. A
CX-to-CZ corruption changes the source state with fidelity 0.25 in both the dense oracle and Aer,
so the comparison is non-vacuous.

| Circuit | Policy | Fidelity to dense | Aer discarded-value sum | Max logged bond | Final max bond |
|---|---:|---:|---:|---:|---:|
| Bell adjacent, 4 qubits | full | 1.000000 | 0 | 2 | 2 |
| Bell adjacent, 4 qubits | cap 1 | 0.500000 | 0.500000 | 1 | 1 |
| Bell adjacent, 4 qubits | cap 2 | 1.000000 | 0 | 2 | 2 |
| Adjacent chain, 5 qubits | full | 1.000000 | 0 | 2 | 2 |
| Adjacent chain, 5 qubits | cap 1 | 0.330468 | 0.863733 | 1 | 1 |
| Adjacent chain, 5 qubits | cap 2 | 1.000000 | 0 | 2 | 2 |
| Nonadjacent, 5 qubits | full | 1.000000 | 0 | 4 | 4 |
| Nonadjacent, 5 qubits | cap 1 | 0.855462 | 0.147798 | 1 | 1 |
| Nonadjacent, 5 qubits | cap 2 | 0.973021 | 0.026979 | 2 | 2 |
| Mixed entangling, 6 qubits | full | 1.000000 | 0 | 4 | 2 |
| Mixed entangling, 6 qubits | cap 1 | 0.165234 | 1.363733 | 1 | 1 |
| Mixed entangling, 6 qubits | cap 2 | 0.371898 | 0.767782 | 2 | 2 |

Two safety consequences are direct:

- A fixed bond cap has strongly topology- and sequence-dependent error. Cap 2 is exact on the
  adjacent-chain fixture but has fidelity only 0.3719 on the mixed fixture.
- Final saved bond dimensions are not a safety certificate. The full mixed circuit reaches logged
  bond dimension 4 but ends at dimension 2; capping every intermediate split at 2 is highly lossy.

The installed Aer distribution emits positive per-SVD `discarded_value` entries; zero-value events
are not logged individually. Absence of a positive entry was accepted only after the metadata,
brace, and per-gate bond-dimension checks passed. The installed output is normalized, while the
pristine clone's `svd.cpp::reduce_zeros` shows a retained-Schmidt renormalization mechanism. Those
are separate evidence chains because the source-to-installed-distribution provenance join is not
established. The positive discarded-value sum can exceed one, as in the mixed cap-1 case, so it is
a diagnostic rather than a global state or record-law error bound.

### Actual Quimb split behavior

The wrapper calls each actual Quimb `Tensor.split` once with the original arguments, then probes
that same split input with an additional untruncated backend SVD to recover the pre-split spectrum.
The requested split call and tensor backend are unchanged, but this artifact does not yet prove
observer-on/off final-state equivalence; that remains a future acceptance gate.

| Fixture | Cap | Actual splits | Worst relative discard | Normalized-state fidelity | Raw output norm | Route status |
|---|---:|---:|---:|---:|---:|---|
| Adjacent CNOT, 4 qubits | 1 | 1 | 0.5 | 0.5 | 0.707107 | direct diagnostic |
| Nonadjacent CNOT, 5 qubits | 1 | 7 | 0.5 | 0.5 | 0.707107 | direct diagnostic |
| Adjacent CNOT, 4 qubits | 8 | 1 | 0 | 1.0 | 1.0 | exact-cap control |
| Nonadjacent CNOT, 5 qubits | 8 | 7 | 0 | 1.0 | 1.0 | exact-cap control |
| Correlated-relaxation Bell jump, 6 qubits | 1 | 1 | 0.5 | 0.5 | 1.0 | counterfactual only |
| Correlated-relaxation Bell jump, 6 qubits | 8 | 1 | 0 | approximately 1.0 | 1.414214 | counterfactual only |

The nonadjacent gate produces seven directly observed splits. Their roles are inferred from the
support distance and Quimb auto-swap ordering as three forward swaps, the operator split, and three
reverse swaps; Quimb does not directly label those roles. The current restricted path's shadow
ledger instead densifies the uncapped post-operator state and reads target-cut Schmidt tails. For
the frozen fixture, `actual_discarded_weight_fraction_sum=0.5` over seven events while shadow
`discarded_weight_fraction_sum=2.0` over four cuts. These are different objects and must not be
substituted for one another.

The two-site no-jump and jump calls in
`src/error_coupling_simulator/frontend/axis1_mcwf_mps_execution.py::_sample_joint_jump_or_nojump`
deliberately use
`max_bond=None`. The capped correlated-relaxation fixture is therefore a counterfactual warning,
not evidence about the current restricted repo path. A future cap at that boundary must preserve
unnormalized branch norms and probabilities before it is allowed to preserve only the selected,
normalized state.

### MPS implementation differences

| Surface | Current implementation | Aer/Quimb lesson | Consequence |
|---|---|---|---|
| Event observation | Dense post-gate shadow Schmidt tails | Aer emits positive per-SVD discard entries; the new Quimb probe observes split inputs with an extra untruncated SVD | Add an actual-split ledger; retain the dense shadow only as a bounded small-system diagnostic |
| Cap policy | Hard `max_bond`, `cutoff=0` | Aer source exposes a cap plus threshold, though this artifact froze threshold 0; Quimb exposes relative cutoff modes | Treat adaptive thresholding as a proposed experiment, not an observed result |
| Nonlocal route | Quimb `auto-mps` implicitly swaps | Aer and Quimb can truncate during internal routing when a finite cap is active | Route and swap splits need their own roles and budget |
| Norm semantics | Truncated unitary output can lose norm | The installed Aer output is normalized; the pristine source shows a retained-Schmidt renormalization mechanism, without an established provenance join | Separate numerical truncation mass from physical MCWF branch mass |
| Collapse branches | Two-site joint branches bypass the cap | Counterfactual cap 1 loses half the Bell-branch fidelity | Do not forward a cap here without branch-probability and record-law gates |

## PEPS/FET differential result

### Replayed scientific gates

| Comparison or gate | Result | Key evidence |
|---|---:|---|
| Same seed, fresh-process repeat | PASS_SCOPED_BITWISE | identical maps, scalars, round state, and record payload |
| Ambient CUDA seed 0 versus 1 | FAIL_DIVERGED | `S_A` delta 0.427701; round-state projective L2 1.169252 |
| `FET_FIDCURVE_DEBUG=0` versus 1 | FAIL_NONFINITE_FID_GAMMA | `S_A` delta 0.430748; round-state projective L2 1.369755 |
| FET fallback contract | RED | all 19 rejected cuts wrote rank-reducing maps: 18 had finite below-target fidelity and one had nonfinite fidelity |
| Stabilizer entropy | RED | all four leakage-off cases miss independent GF(2) value 2.0 by far |

The entropy observations are:

| Case | `S_A` | Leakage mass | Reference | Verdict |
|---|---:|---:|---:|---:|
| seed 0, debug 0, repeat 0 | 0.5320065054 | approximately 3.33e-16 | 2.0 +/- 1e-4 | RED |
| seed 0, debug 0, repeat 1 | 0.5320065054 | approximately 3.33e-16 | 2.0 +/- 1e-4 | RED |
| seed 1, debug 0 | 0.1043058710 | 0 | 2.0 +/- 1e-4 | RED |
| seed 0, debug 1 | 0.1012586257 | 0 | 2.0 +/- 1e-4 | RED |

These replay-audit observations do not supersede the registered owner-test value
`0.10860941571062639` in [PEPS_FET_VALIDATION.md](PEPS_FET_VALIDATION.md). That owner test was not
rerun in this diagnostic phase, and the numerical discrepancy between the surfaces remains
unresolved. Both surfaces remain RED against the same GF(2) reference.

The 19 violations are 4 + 4 + 4 + 7 across four replay cases, including the deterministic repeat;
they are not 19 independent root causes. The debug case includes a cut on `B6_8` with stored
dimension 20, exact rank 4, selected rank 1, and `Fid_gamma=-inf`; a rank-reducing map was still
written.

### Confirmed current-source control-flow defect

`carrier/peps/fet.py::env_optimal_rank` documents this contract: when no rank reaches
`1 - eps_fid`, keep the full stored dimension and return an identity no-op. Both its normal and
debug fallback branches instead return the best low-rank candidate even when the fidelity is below
target or nonfinite. `trajectory.py::_policy_cut` then applies the returned map unconditionally.

Additional defects amplify the problem:

- `gamma_fidelity` uses `-inf` for several numerical-failure classes.
- The normal path converts nonfinite fidelity to the finite magic value `-1.0`, erasing the
  failure class before selecting the best candidate.
- `_als_inner` initializes its best value to `-1.0`, so an all-nonfinite solve can return a
  seed map with an apparently finite sentinel.
- Random ALS kicks use the ambient CUDA generator. Debug mode evaluates extra ranks after the first
  accepted rank and shifts the RNG stream. This is a confirmed mechanism capable of changing later
  bond updates; a dedicated RNG-state causal ablation has not yet excluded every other amplifier.
  The observed debug path is not behavior-identical.

The reproduce-instrument-localize diagnostic loop distinguishes this from a reporting defect:
the fixed-seed fresh-process repeat is scoped-bitwise identical, array archives authenticate across
Torch and NumPy, and the rejected rank-reducing map is visible at the mutation boundary.

### External PEPS implementation differences

| Surface | Current FET | YASTN / variPEPS practice worth testing | Boundary |
|---|---|---|---|
| Failed candidate | Best low-rank candidate is still committed | Project fail-closed proposal; variPEPS can reject a CTMRG-nonconverged trial step, while YASTN returns the lowest-error tested truncation and reports diagnostics | Must become an identity/no-op transaction, not a looser threshold |
| Metric health | PSD repair and default `pinv` cutoff are mostly opaque | YASTN records non-Hermitian part, minimum eigenvalue, the fraction below its metric-error threshold when metric repair is enabled, and tries cutoff variants | Diagnostic inspiration only; thresholds cannot be copied |
| Candidate search | Fixed ALS sweeps, multiple seeds, no residual/convergence gate | YASTN compares SVD/EAT and optimized variants by metric truncation error | Same objective and gauge invariance must be demonstrated first |
| Decomposition failure | Multiple failures collapse into `-1` or `-inf` | variPEPS detects NaN singular values and retries JAX SVD with the QR algorithm | The retry is not itself proof of a finite result; our boundary must remain fail-closed and record its reason |
| Environment iteration | One sequential path sweep | variPEPS CTMRG exposes convergence/failure handling; YASTN reports best method, per-method errors, and iteration counts | YASTN iteration count is not a convergence flag, and periodic CTMRG convergence does not certify this finite trajectory |
| Accumulation | Per-bond local fidelity | YASTN retains per-step/accumulated truncation diagnostics | Accumulated local values are still not a record-law bound |

The external statements above are source-located in
`external/baselines/yastn/yastn/tn/fpeps/_evolution.py:547-565,574-660` and
`external/baselines/variPEPS_Python/varipeps/utils/svd.py:28-53`. The frozen clone commits are
YASTN `595bd802` and variPEPS `0edc81ac`.

## Prioritized experiments

These are proposals to **try**, not approved source changes.

### P0a/P0b — PEPS mutation firewall, then explicit outcome type

The smallest safety repair is a mutation-boundary firewall: a rejected result must not call
`apply_fet_truncation`. Then replace the magic scalar fallback with an explicit
`accepted | noop | solver_failed` outcome. Only an accepted, finite candidate meeting
`Fid_gamma >= 1 - eps_fid` may mutate the state. Every other outcome must preserve the full bond
and exact tensor bytes by performing no update, while retaining the rejected-candidate evidence.

Minimum falsifier and gate:

- inject finite-below-target, `-1`, and `-inf` candidates;
- require unchanged bond dimension, raw dense-state hash, and projective state;
- require a qualifying control to reduce rank, proving the test is non-vacuous;
- require zero `rank_reducing_writeback` events for rejected candidates.

Passing this gate removes rejected-writeback violations. It does not clear a nonfinite-fidelity
violation or make the entropy gate green.

### P0 — MPS actual-split and norm/probability ledger

Instrument the current restricted repo execution seam without a global monkey patch. Record
pre-rank, kept-rank, raw and relative discard, inferred split role, cutoff mode, and pre/post norm.
Keep the existing dense shadow under a separate name only for Hilbert-size-capped,
dense-checkable diagnostics; it must not remain on a scalable finite-cap hot path.

Minimum falsifier and gate:

- observer on/off must preserve final raw norm to relative error `<= 1e-12`, normalized-state
  phase-aligned L2 `<= 1e-12`, and an identical record payload;
- adjacent cap 1 must expose one split with relative discard 0.5;
- nonadjacent cap 1 must expose seven splits and match the predeclared inferred
  swap/operator-role sequence;
- omitting one swap split must fail;
- unitary truncation mass and physical MCWF branch mass must be separate fields;
- jump/no-jump probabilities must always be computed from unnormalized candidate branches.

These frozen fixtures certify only two-site calls. Before any adaptive policy covers a connected
Hamiltonian cluster with support size at least three, add a three-site actual-split fixture;
otherwise the larger-support finite-cap route remains explicitly uncertified and must fail closed
under the new policy.

### P1 — Deterministic FET solver and behavior-neutral debug

Use a private generator derived from bond, rank, restart, and trial, or an equivalent deterministic
regularization. Debug collection must call the same selection/fallback code and must not consume
the ambient CUDA RNG.

Minimum gate:

- debug off/on gives bitwise-identical ranks, map hashes, round state, entropy, and record payload;
- the default CUDA RNG state is unchanged across one FET solve;
- varying unrelated ambient CUDA seeds cannot change solver output for a fixed explicit solver
  seed.

### P1 — Adaptive MPS local budget with a hard ceiling

Try the smallest rank meeting a declared per-split relative-discard budget, subject to a hard
memory ceiling. Operator and swap splits may need separate predeclared budgets. Compare fixed
left/right routing using a rule selected before viewing outcome fidelity. The first experiment is
qubit-only. The existing `mcwf_mps_multilevel_finite_bond_ledger_not_implemented` boundary remains
fail-closed for any `local_dim != 2`.

Minimum gate:

- every split meets its budget or fails closed;
- on exact-cap state controls, require `1 - fidelity <= 1e-12`, phase-aligned L2 `<= 1e-12`,
  and relative raw-norm error `<= 1e-12`;
- on the frozen adjacent, nonadjacent, and mixed circuit fixtures, report normalized-state
  fidelity, phase-aligned L2, pure-state trace distance, raw norm loss, and the actual-split ledger;
- those approximate capped state fixtures are diagnostic screens only. No state-acceptance
  threshold is selected from their observed results, and they cannot authorize the adaptive route;
- full-rank left/right routes must meet the same exact-cap state thresholds;
- add a separate repo-owned, dense-checkable, record-bearing MCWF schedule and require full joint
  record TV `<= 1e-6`, the existing strict gate in
  [NUMERICAL_PROVENANCE.md](../NUMERICAL_PROVENANCE.md); prefer exact enumeration, or require a
  predeclared 0.999 confidence interval to lie entirely below the gate if sampling is unavoidable;
- no sum of local discarded weights is claimed as a global bound.

The two-site MCWF collapse route remains uncapped. Its current correlated-relaxation
counterfactual covers only one jump candidate. Before any cap is forwarded there, add a
record-bearing fixture and independent dense joint-L oracle, then meet the exact-cap state/norm
thresholds above, require branch-probability-vector L1 error and total probability-mass error
`<= 1e-12` against the uncapped branch table, and pass the strict record-TV gate.

### P1/P2 — Condition-aware FET metric and convergence audit

Before replacing the optimizer, expose the raw anti-Hermitian norm, minimum eigenvalue, clipped
negative mass/fraction, effective rank, condition estimate, `pinv` cutoff, per-sweep objective,
normal-equation residual, iteration count, and convergence status. Compare a small predeclared
`atol`/`rtol` or effective pseudoinverse-cutoff grid and embed the rank-`chi` solution as a
warm start for rank `chi+1`.

Minimum falsifier and gate:

- internal gauge or scale changes preserve selected rank and projective dense state;
- an injected pathological eigenmode triggers rollback rather than a huge-norm map;
- all accepted candidates have finite diagnostics;
- fidelity is nondecreasing with rank within a declared tolerance on analytic PSD fixtures;
- a corrupted ALS update is classified nonconverged and produces a no-op.

Only after those gates should YASTN-style candidate comparison or variPEPS-style SVD retry be
evaluated.

### P2 — PEPS path-level copy-on-write acceptance

On exact d3 fixtures, try forward and reverse path sweeps on copies and compare them with an
independent untruncated dense branch. Commit a sweep only after state overlap and observable
residual gates pass. Entropy remains an independent invariant, not the optimization objective.

Minimum gate:

- forward/reverse orders converge to the same projective state on controlled fixtures;
- tighter tolerance or larger rank cannot reduce exact overlap;
- corruption of one cut rolls back the complete transaction;
- every retained replay case reaches `S_A = 2 +/- 1e-4`;
- passing state-level gates still does not promote full record faithfulness without the independent
  multi-round record oracle.

## Recommended order

The shortest safe sequence is:

`PEPS mutation firewall -> MPS actual-split ledger -> MPS norm/probability separation ->
FET RNG/debug isolation -> condition/convergence instrumentation -> adaptive MPS budget ->
PEPS path-level algorithm experiments`.

This order first makes failures observable and prevents rejected updates from mutating the state.
It deliberately postpones threshold tuning, optimizer replacement, and capping MCWF collapse
branches.

## Explicit no-go conclusions

- Do not weaken `eps_fid`, the entropy target, or its tolerance to admit the current PEPS result.
- Do not treat `Fid_gamma=-1` as a real fidelity.
- Do not sum local discarded weights and call the result a global state or record-law error bound.
- Do not infer safety from final MPS bond dimensions.
- Do not renormalize jump/no-jump candidates before their branch probabilities are computed.
- Do not treat Aer, YASTN, or variPEPS as an equivalent QEC record oracle.
- Do not move the diagnostic Quimb global monkey patch into the restricted source path.

## Reproduction and repository state

Diagnostic commits:

- `e14ba05 diagnostics: audit TN truncation behavior`
- `5c7f0ef diagnostics: keep split probe on tensor backend`
- `a0ea5c0 diagnostics: retain nonfinite FET evidence`
- `a9229c5 diagnostics: authenticate cross-backend norms`

Focused pure tests:

```text
47 passed, 1 skipped in 0.21s
```

The focused command was:

```bash
conda run -n ecs python -m pytest -q \
  tests/test_peps_fet_replay_audit.py \
  tests/test_mps_actual_split_diagnostic.py \
  tests/test_external_aer_mps_comparison.py
```

At audit completion, the parent worktree and the Qiskit Aer, YASTN, and variPEPS external clones
were clean.
