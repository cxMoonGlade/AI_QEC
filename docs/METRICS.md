# METRICS — current simulator ledger

This file defines only metrics that have a current implementation or registered test owner in
`error_coupling_simulator`. The simulated object is the multi-time detector/observable record;
metrics are measurements of that object, not substitutes for it. The binding product boundary is
`docs/SIMULATOR.md`, and the machine-readable owner map is `docs/service_status.json`.

## Registration rule

A quantitative result is claim-bearing only when it declares:

1. the object and coordinate being measured;
2. the metric name and formula;
3. the implementation owner and acceptance test;
4. whether the value is exact, sampled, or a project gate;
5. the comparison band and its provenance.

An unregistered score is exploratory output, not simulator evidence. A new metric requires a
source-backed definition, a current owner, an independent value test, and an update to this ledger.

The current certification ledger uses the classes carried by
`error_coupling_simulator.certify.types`:

- **(a) exact** — an enumerated value, theorem, or algebraic identity;
- **(b) prediction band** — a falsifiable value with an explicitly declared comparison band;
- **(c) heuristic gate** — a numerical or resource decision rule that is not a scientific premise.

An undeclared value is class (c). `UNANCHORED` is an evidence gap, never a pass. Independent
PEPO/PEPS reference evidence is currently bounded to d3; record-level finite-truncation fidelity
and d5/d7 scientific certification are open.

## Shared conventions

- Records use `RecordBatch.det` and `RecordBatch.obs`. Detector bits are temporal events, with
  `d[0,j]=s[0,j]` and `d[r,j]=s[r,j] XOR s[r-1,j]` for `r>=1`. A raw syndrome array must be named as
  raw syndrome data. `tests/test_carrier_record_fold.py` owns the fold identities and corruption
  checks.
- `NUMERICAL_ZERO == 1e-12` is a floating comparison threshold. It must not replace structural
  zeros, binary values, counts, or probability mass.
- Population metrics and sampled estimates must be labelled separately. A project acceptance band
  is not a confidence interval unless a derivation explicitly establishes that interpretation.
- A metric must be evaluated against an independent reference route. Shared-code agreement is a
  regression check, not scientific certification.

## Record certification

These are the quantities implemented by `certify/core.py` and enumerated by
`certify/types.Statistic`.

| Quantity | Current formula and convention | Owner and executable gate |
|---|---|---|
| Full joint record distance | `TV(p,q)=0.5*sum_x abs(p(x)-q(x))` over the joint detector/observable support | `certify.core.total_variation`; `tests/test_certify_core_units.py` independently pins the half factor and mismatch verdict |
| MCWF declared-basis label and emitted-binary distance | Compute `TV_label=0.5*sum_l abs(p(l)-q(l))` over schedule-ordered local measurement-eigenlabel tuples and `TV_binary=0.5*sum_r abs(p(r)-q(r))` over the emitted binary Record, then report `max(TV_label,TV_binary)` and require both component gates to pass. X labels `0/1` mean `|+>/|->`, Z labels are computational local levels, and leakage labels `>=2` stay explicit. The binary reference is a certifier-local marginal of the dense label law: labels `0/1` map deterministically to bits `0/1`, while each label `>=2` emits bit `1` with caller-declared probability `b`. Sampled confidence uses a Bonferroni two-component, per-bin, two-sided Hoeffding bound capped at the gross-TV ceiling. This is a class-(c) restricted gate over the declared measurement columns, not a claim of full QEC Record faithfulness. | `certify.axis1_mps._certify_level_path` and `_dense_binary_record_distribution_from_levels`; independent X/Z projectors, reset instruments, and hand-typed readout marginalization plus corruption checks in `tests/test_axis1_mcwf_dense_certification.py`, `tests/test_mps_mcwf_measurement_semantics.py`, and `tests/test_mps_phase6_evaluator_metric_binding.py` |
| MCWF frozen-fixture finite-step X/Z Record convergence | For the byte-pinned two-qubit T1 fixture only, a hand-written scalar recurrence reconstructs the normalized finite-step Record law without production-private helpers. Against the continuous law at `s=exp(-gamma*t)=0.25`, joint/Z TV is fixed at `0.0234098250, 0.0118596628, 0.0059679715, 0.0029934385` and X-after TV at `0.0102758610, 0.0050882834, 0.0025317938, 0.0012628171` for `m=10,20,40,80`; both must decrease and each doubling ratio must lie in `[1.85,2.15]`. The public `m=40`, `n=2048`, seed `19073` GPU histogram is compared to the finite-step law with one-sample Weissman radii at overall `alpha=0.01` split across joint, Z, and X views: `0.0640322086` for `k=16` and `0.0395189879` for `k=2`. Final Z remains an exact structural zero. These are class-(c), fixture-bound Record checks, not a global convergence order, linear channel, Choi, CPTP, calibration, or production claim. | `tests/test_axis1_mcwf_convergence.py`; neutral law/TV primitives in `scripts/external_baselines/qutip_mcwf_xz_protocol.py` |
| MCWF no-measurement certification | No positive metric is registered. Canonical empty-column payloads must be `[[]]` with aligned counts/probabilities, then return `unavailable` and reason `mcwf_normalized_candidate_law_has_no_registered_linear_channel_metric`. The normalized candidate total mass is input-state dependent, so a linear CPTP Choi/process comparison is not defined for this path. | `certify.axis1_mps.dense_jointL_record_certification`, policy v7 fail-closed tests in `tests/test_mps_phase6_evaluator_metric_binding.py` and public direct/Carrier tests in `tests/test_axis1_mcwf_dense_certification.py` |
| MCWF production-operator/reference difference | For every present Hamiltonian or collapse term, compute `max_ij abs(O_production[i,j]-O_reference[i,j])` against the isolated hand-typed NumPy/Pauli matrix and require it to be at most `NUMERICAL_ZERO == 1e-12` before any dense metric can authorize restricted execution. Coverage includes zero-coefficient terms, all 51 Hamiltonian families, all seven collapse families, declared support arity, and full-dimension `CORR_RELAX`; every reference-declared structural zero is checked as exact production zero rather than discovered by thresholding. A mismatch returns non-metric unavailable certification and rejects the run. This is a class-(c) software implementation gate, not a physical error metric, mechanism-source closure, or calibration claim. | `certify.mcwf_operator_reference.reference_hamiltonian_matrix_for_term`, `reference_collapse_operator_for_term`, `reference_structural_zero_mask_for_term`, and the full-family/zero-builder/insensitive-state falsifiers in `tests/test_mcwf_operator_reference.py` and `tests/test_axis1_mcwf_dense_certification.py` |
| MCWF frozen-dynamics artifact reference gate | Compile each production term once; build connected Hamiltonian-group gates from those frozen terms; then independently reconstruct every term, group partition/support/order, and group gate from certifier-local NumPy formulas and SciPy `expm`. Terms require exact declared structural zeros and floating difference at most `NUMERICAL_ZERO`; group gates require `max_ij abs(U_frozen[i,j]-U_reference[i,j]) <= 1000*NUMERICAL_ZERO`. The v2 packet must cover every substep/term/group, bind Carrier-program/artifact hashes, the reference/certifier/carrier-operator sources, and the transitive ideal-control-generator and selection-family sources, plus local dimensions and the honest finite-step identity, and pass a post-execution artifact-content recheck. The policy, Carrier, and auto seams require the current authenticated packet. This is a non-metric class-(a/c) software artifact/integrity gate, not state or Record distance, a physical tolerance, source closure, calibration, or production-scalability evidence. | `certify.axis1_mps.mcwf_dynamics_artifact_reference_certification`, `validate_mcwf_dynamics_artifact_reference_certification`, `_mcwf_dynamics_artifact_reference_failure`; TOCTOU, stale-transitive-source, state-insensitive grouping, structural-zero, packet-forgery, and public transitive-authentication falsifiers in `tests/test_axis1_mcwf_dense_certification.py`, `tests/test_mcwf_operator_reference.py`, and `tests/test_mps_carrier_child_authentication.py` |
| Neutral MCWF X/Z fixture-family statistical differential | For each registered empirical-vs-exact or empirical-vs-empirical pair, `TV=0.5*sum_x abs(p(x)-q(x))`. The byte-pinned registry contains five statistics for each of F1 T1, F2 number dephasing, and F3 thermal down/up: project-vs-dense joint and two directed marginals, QuTiP-vs-dense joint, and QuTiP-vs-project joint. With `n=2048`, family `alpha=0.01`, and 15 simultaneous entries, each receives `alpha_j=alpha/15`. A one-sample entry uses `r(n,k,alpha_j)=min(1,sqrt(log((2^k-2)/alpha_j)/(2n)))`; a two-sample entry uses the sum of two radii evaluated at `alpha_j/2`. Thus the registered one-sample joint and marginal radii are `0.0670302388436366` and `0.04421175841273293`, and the two-sample joint radius is `0.1365617560712202`. The dense leg hand-builds the 16x16 Lindblad evolution without simulator imports and preserves exact structural zeros. Mechanism-specific F1/F2/F3 corruptions must fail, while unit-modulus collapse phase is the gauge-invariant negative control. Shared samples make registered views correlated; Bonferroni allocation remains conservative. This is class-(c) finite-sample evidence for three two-qubit fixtures, not complete QEC Record, qutrit/leakage, trajectory coupling, scalability, calibration, or production evidence. | `scripts/external_baselines/qutip_mcwf_xz_protocol.py`, `mcwf_xz_dense_worker.py`, `qutip_mcwf_xz_worker.py`, and `run_mcwf_xz_fixture_family_comparison.py`; `tests/test_external_mcwf_xz_fixture_family.py` |
| Detector-record marginal distance | The same TV formula after marginalizing away the logical-observable bit | `Statistic.SYNDROME_DIST`; `tests/test_certify_core_units.py` pins the marginalization and TV comparison |
| Detector and observable marginals | Per-column detector firing means plus the observable-flip mean; comparison value is `max(abs(a-b))` | `Statistic.DETECTOR_MARG`; `tests/test_certify_core_units.py` |
| Round-to-round detector correlation | For each adjacent round and stabilizer, Pearson correlation of binary detector columns; reduce to `mean_j abs(corr[r,j])`; compare with maximum absolute component error | `Statistic.RR_CORR`, `reduce_rr_corr`; `tests/test_certify_core_units.py` |
| Same-round spatial correlation | Per round, `mean_{j!=k} abs(corr[r,j,k])`; diagonal self-correlations are excluded; compare with maximum absolute component error | `Statistic.SPATIAL_CORR`, `reduce_spatial_corr`; `tests/test_certify_core_units.py` |
| Registered scalar identity | `abs(value-reference)` for a named closed-form quantity | `Statistic.SCALAR_FUNC`; current anchor and certification tests under `tests/test_certify*.py` |

The implemented distribution band is a project gate:

```text
max(6/sqrt(N), 3*sqrt(K/N)) + statistical_anchor_band
```

where `K` is the realized union support size. Array statistics use
`8/sqrt(N) + statistical_anchor_band`; an exact scalar reference uses the current `1e-9` absolute
comparison band. These formulas are implementation policy in `certify/core.py`, not universal
confidence bounds. Their branch and boundary behavior is pinned in
`tests/test_certify_core_units.py`.

## Channel diagnostics

| Quantity | Current formula and claim boundary | Owner and executable gate |
|---|---|---|
| Trace-preservation residual | Frobenius norm `norm(sum_k K_k^dagger K_k-I)` | `carrier.cptp_channel.tp_residual`; `tests/test_noise_mechanism_primitives.py` and channel-owner tests |
| Joint-vs-composed process infidelity | `1-F` where `F` is Uhlmann fidelity between trace-normalized Choi states | `carrier.joint_lindbladian.composed_vs_joint_infidelity`; independent NumPy/SciPy/QuTiP checks in `tests/test_joint_lindbladian.py` |
| Joint-vs-composed superoperator distance | Frobenius distance between the two superoperators | `composed_vs_joint_superop_distance`; `tests/test_joint_lindbladian.py` and `tests/test_axis1_mcwf_dense_certification.py` |
| Choi-state companion distance | Frobenius distance between trace-normalized Choi states; a diagnostic, not trace distance or diamond distance | `composed_vs_joint_choi_distance`; `tests/test_joint_lindbladian.py` |
| Pauli-transfer matrix | `R_ab=Tr(P_a Phi(P_b))/d` in the declared Pauli basis | `certify.channel_diagnostics`; `tests/test_channel_diagnostics.py` |

PTM off-diagonal entries establish basis-specific non-Pauli structure only. They do not, by
themselves, identify coherent error or its physical cause.

## Current record reductions

| Quantity | Current formula and claim boundary | Owner and executable gate |
|---|---|---|
| Logical error rate | Mean XOR between decoder predictions and actual observable bits, reported per observable and for any-observable failure | `frontend.simulator._decoder_summary`; `tests/test_simulator_frontend.py` |
| Detector-pair estimate | Spitz Eq. 13 `p_ij = 1/2-sqrt(1/4-cov/(1-2*mean(x_i XOR x_j)))` plus its delta-method standard error; undefined `0/0` pairs remain `NaN` with an explicit identifiability mask | `frontend.pij`; independent recomputation and corruption checks in `tests/test_interop_units.py` |
| Optional DEM pair-edge selection | Keep a detector pair only when `p_ij > pair_floor_abs` and `p_ij > pair_floor_sigma * SE(p_ij)`; both caller-visible parameters are finite, nonnegative class-(c) reduction rules | `frontend.interop.records_to_dem`; endpoint and corruption checks in `tests/test_interop_units.py` |

The pair estimate is a two-point reduction and is blind to hyperedges. An unidentifiable pair is
excluded from the optional edge set but remains explicitly non-finite and masked in diagnostics; it
is not reclassified as zero. DEM selection floors change only the optional decoder-facing reduction
and travel in its diagnostics; they are not numerical probability floors. A strictly negative
boundary residual is always reported as a model-inconsistency clamp even when its magnitude is
smaller than `pair_floor_abs`; exact residual zero alone is structurally absent. Logical error rate
requires one named, fixed decoder and the actual observable bits; it is not evidence that the
underlying analog channel is exactly represented by a detector error model.

## Tensor-network implementation diagnostics

The retained PEPO and PEPS carriers expose bond dimensions, squared singular-value tails,
truncation objectives, trace checks, contraction deltas, and negativity diagnostics. Their current
owners are `carrier/pepo/` and `carrier/peps/`; their registered tests are listed under
`pepo_density_matrix_carrier` and `peps_single_wire` in `docs/service_status.json`.

These values measure representation cost or implementation consistency. None is a substitute for
the full record comparison. In particular:

- a discarded squared-singular-value tail is local to the stated cut;
- a bond cap is a resource limit;
- a local truncation objective is not a bound on record TV or logical error;
- trace and negativity checks are necessary validity diagnostics, not sufficient record
  certification.

The current PEPS/FET entropy falsifier is unresolved, so no PEPS/FET metric in this section carries
a passed record-faithfulness verdict.

## Bounded research diagnostics

Two research surfaces have current owners but do not certify the production record:

- `quantum_bath/observables.py` implements exact three-round distribution TV, Kolmogorov-consistency
  statistics, an L1 distance to the Markov-1 factorization, and conditional mutual information in
  bits. These apply only to the registered quantum-bath research distributions and are tested by
  `tests/test_quantum_bath_observables_units.py`.
- `scripts/finite_rtn_free_induction_diagnostic.py` reports positive trace-distance excursions for
  two explicitly declared single-qubit free-induction lifts. Its independent full-state oracles and
  corruption tests live in `tests/test_finite_rtn_free_induction_diagnostic.py`. The signed current
  artifact is pending, and no result transfers to the source-conditioned QEC channel or syndrome
  record.
- The external finite-PEPS d3/d5 diagnostic uses normalized complete pure-state fidelity
  `F=|<psi_ref|psi_candidate>|^2/(<psi_ref|psi_ref><psi_candidate|psi_candidate>)`, following
  Evenbly, Sec. V, Eq. (12), PDF p. 6. Both inputs must be complete one-dimensional complex128
  vectors in the fixture-pinned basis; a retained-weight product, local truncation tail,
  contraction residual, finite-boundary overlap, norm, or bond cap is forbidden as a substitute.
  `scripts/external_baselines/compare_peps_d5_complete_states.py` owns the value, and
  `tests/test_external_peps_d5_pure_state_fidelity.py` owns independent formula,
  amplitude-order, global-phase, non-finite, dtype/shape, identity, and proxy-firewall
  corruption checks. Its output is a nonterminal per-point metric.
  `scripts/external_baselines/run_peps_d5_complete_state_sweeps.py` is the terminal owner for
  the fixed `D=[1,2,4,8,16]` sweep, fresh-process `1800 s` point timeout, `64 GiB` host and
  `28 GiB` device caps, monotonicity prediction, and bond-knob nondegeneracy. Exact
  self/dual-route tolerances are class (a) numerical checks;
  `F>=0.99`, `0.95<=F<0.99`, and `F<0.95` are respectively useful, marginal, and low
  class-(c) project bands. This finite pure-state benchmark does not certify a detector/observable
  Record, leakage/Kraus dynamics, logical error rate, a syndrome-extraction round, d7, or scalable
  exact PEPS contraction.
