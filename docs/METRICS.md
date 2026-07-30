# METRICS — current simulator ledger

This file defines only metrics that have a current implementation or registered test owner in
`error_coupling_simulator`. The simulated object is the multi-time detector/observable record;
metrics are measurements of that object, not substitutes for it. The binding product boundary is
`docs/SIMULATOR.md`, and the machine-readable owner map is `docs/service_status.json`.

The final preregistered-pending section freezes formulas for work that has not yet acquired a
current implementation or test owner. It is not part of the current certification ledger and cannot
make a result claim-bearing until its named activation conditions are met.

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

## Preregistered GCAPEPS native-repair development metrics

This subsection freezes only the development checks in
`docs/simulator_validation/GCAPEPS_FINITE_MEMORY_NATIVE_REPAIR_PREREG_2026-07-29.md`.
They test bounded engineering determinism; they are not PEPS faithfulness, state-accuracy,
performance, Record, or production claims.

For finite, nonzero, raw `complex128` complete vectors \(x,y\) in the same physical coordinate,
without phase fitting, normalization, dtype conversion, or coordinate permutation, define

\[
d_\infty=\max_j|x_j-y_j|,\qquad d_2=\|x-y\|_2,
\]

\[
d_{\rm rel}=\frac{2d_2}{\|x\|_2+\|y\|_2},\qquad
d_{\rm norm}=\frac{2|\|x\|_2-\|y\|_2|}{\|x\|_2+\|y\|_2},
\]

\[
F_{\rm raw}=\frac{|\langle x|y\rangle|^2}
{\langle x|x\rangle\langle y|y\rangle}.
\]

Every denominator and output must be finite and strictly positive where required. Set
`fidelity_roundoff_correction=max(0.0,F_raw-1.0)` and use
`F=min(1.0,F_raw)` only after requiring that correction to be at most `1e-12`; a larger excess
fails rather than granting a clipping license. At both T3 operation-99 and operation-100
checkpoints, require `d_rel<=1e-9`, `d_norm<=1e-10`, `1-F<=1e-10`, and
`fidelity_roundoff_correction<=1e-12`. At each thread setting, the candidate and independent-dense
materializations form a development-only, report-only paired comparison. The one-versus-four-thread
candidate comparison remains a metamorphic engineering-determinism check. For T1 operator reconstruction,
\(d_{\infty,\mathrm{op}}=\max_{i,j}|U_{ij}-U^{\rm ref}_{ij}|\), with the preregistered
`1e-12` gate.

For a full nonincreasing singular spectrum
\(\sigma_0\ge\cdots\ge\sigma_{m-1}\ge0\), with finite entries,
\(\sigma_0>0\), and kept dimension \(k\), the scale-stable relative discarded tail is

\[
f_{\rm disc}=
\frac{\sum_{j=k}^{m-1}(\sigma_j/\sigma_0)^2}
{\sum_{j=0}^{m-1}(\sigma_j/\sigma_0)^2}.
\]

The T3 truncation nondegeneracy row requires `full_dim=m>32`, `kept_dim=k=32`,
`cause=max_bond`, and `f_disc>1e-12`. A length-33 equal spectrum has the known answer
`f_disc=1/33`; multiplying every singular value by the same finite positive scale must leave the
value unchanged. Invalid/nonfinite spectra and an unscaled-square overflow corruption must fail.
This local class-(c) cause/resource diagnostic is not a whole-state truncation-error bound.

## Preregistered pending GCAPEPS differential metrics

This section freezes only the planned `n=8`, active-rank-`3`, untruncated
plain-Quimb-versus-GCAPEPS fixture. None of the paths below is a current owner
until the path exists,
its independent contract tests pass, and `tests/CODEBOOK.md` plus the service catalog name the
implemented surface. Until then these formulas are non-current preregistration entries, not
simulator evidence.

Let \(y_q\) be the ordinary-Quimb physical PEPS vector and \(y_g\) the GCAPEPS physical vector
obtained by the frozen literal complex128 Clifford lift of its residual PEPS
vector. Both inputs must
be finite one-dimensional length-256 `complex128` arrays in the frozen q0-most-significant-bit
coordinate, with finite strictly positive norms and denominators. No phase fit, normalization,
dtype cast, or coordinate permutation is permitted. Define

\[
d_\infty=\lVert y_g-y_q\rVert_\infty,\qquad
d_2=\lVert y_g-y_q\rVert_2,
\]

\[
d_{\rm rel}=\frac{2d_2}{\lVert y_g\rVert_2+\lVert y_q\rVert_2},\qquad
d_{\rm norm}=
\frac{2\left|\lVert y_g\rVert_2-\lVert y_q\rVert_2\right|}
{\lVert y_g\rVert_2+\lVert y_q\rVert_2},
\]

\[
F_{\rm raw}=
\frac{|\langle y_q|y_g\rangle|^2}
{\langle y_q|y_q\rangle\langle y_g|y_g\rangle}.
\]

Set
`fidelity_roundoff_correction=max(0.0,F_raw-1.0)`. Use
`F=min(1.0,F_raw)` only when `fidelity_roundoff_correction <= 1e-12`; a larger correction is a
failure rather than a clipping license. The frozen class-(c) complex128 agreement gates are
`d_rel <= 2e-11`, `d_norm <= 2e-11`, `1-F <= 1e-12`, and
`fidelity_roundoff_correction <= 1e-12`. Absolute `d_inf` and `d2` are mandatory report-only
diagnostics and never determine `AGREE`. The pair family is evaluated after the Clifford prefix and
after the final rank-three update.

The planned untimed independent NumPy anchor will construct a residual vector
from the closed-form four-amplitude
input plus literal bitwise Pauli action, and constructs a physical vector independently from
`|0^8>`, literal complex128 preparation/Clifford gates, and literal bitwise signed physical-Pauli
action. The two anchor formulations must first agree under the same literal lift. GC
residual is then
graded against anchor residual, while plain physical and lifted-GC physical vectors are separately
graded against anchor physical, using the same formulas, bands, raw phase convention, and no fit,
normalization, cast, or permutation. The anchor will be required to import no
Quimb, Stim, SDIM, or GCAPEPS and
will contribute no timing or memory sample. After implementation and controls,
it may qualify only this single `n=8` input-state action; it
does not prove all-input operator equality, generic PEPS truth, a detector/observable Record law, or
carrier faithfulness.

The planned engineering timing instrument uses one discarded fresh-process warmup per candidate lane
in order `plain,gcapeps`, then six measured fresh workers per lane in serial alternating pair order
`plain,gcapeps`; `gcapeps,plain`, repeated three times. Every child is fully reaped before the next.
It reports every raw integer-nanosecond sample, median, and median absolute deviation. Its primary
samples are

```text
plain_update = physical_clifford + pepo_build + pepo_apply
gcapeps_update = tableau_prefix + coherent_ir_build + carrier_apply
```

with materialization excluded and reported separately. The planned GCAPEPS sample must
declare `includes_exact_small_internal_dense_and_norm_checks=true`; it is not a pure kernel timing.
Define

\[
R_{\rm update}=
\frac{\operatorname{median}(t_{\rm plain})}
{\operatorname{median}(t_{\rm gcapeps})},\qquad
R_{\rm RSS}=
\frac{\operatorname{median}(\mathrm{RSS}_{\rm plain})}
{\operatorname{median}(\mathrm{RSS}_{\rm gcapeps})}.
\]

The directional hypothesis `R_update > 1` is report-only, not an acceptance
gate. Efficiency is interpretable only when the candidate differential, every
anchor
qualification row, and the required SDIM signed-frame corroboration pass.
Even then it describes only the frozen fixture, machine, fork commit, lowering, and worker envelope;
it is not a general efficiency, asymptotic scaling, contraction-complexity, Record, production, or
finite-truncation claim.

| Pending quantity | Planned owner; activation condition |
|---|---|
| Frozen fixture and candidate vectors | `scripts/external_baselines/emit_gcapeps_n8_r3_fixture.py`, `plain_quimb_n8_r3_worker.py`, and `gcapeps_n8_r3_worker.py`; pending implementation and exact fixture/shape/dtype tests |
| Independent exact-small anchor rows | `scripts/external_baselines/gcapeps_n8_r3_dense_anchor.py`; pending prohibited-import, dual-formulation, corruption, and one-input state-action tests |
| Symmetric pair/anchor metrics and verdict algebra | `scripts/external_baselines/compare_gcapeps_n8_r3_differential.py`; pending independent formula, raw-phase, roundoff, non-finite/zero-denominator, report-only, and shared-corruption tests |
| Signed frame corroboration | `scripts/external_baselines/gcapeps_n8_r3_sdim_worker.py`; pending exact Stim/SDIM sign comparison; non-PASS makes qualification and efficiency ineligible but never changes pair/anchor metrics or enters a numeric ratio |
| Fresh-worker timing and publication | `scripts/external_baselines/run_gcapeps_n8_r3_differential.py`; pending worker isolation/order, resource-envelope, identity, and atomic-publication tests |
| Complete pending test surface | `tests/test_external_gcapeps_n8_r3_differential.py`; absent until implemented and therefore not a current acceptance owner |

### Current bounded GCAPEPS bridge forced-truncation metrics

The following metrics were frozen in
`docs/simulator_validation/GCAPEPS_NATIVE_FORCED_TRUNCATION_PREREG_2026-07-29.md` before implementation.
The native strategy, independent dense anchor, guarded parent runner, and
non-formal contract tests now exist, and the held-out result is current at
`docs/simulator_validation/GCAPEPS_NATIVE_FORCED_TRUNCATION_RESULT_2026-07-29.md`.
The formulas and observed values apply only to a complete length-four
`complex128` vector on the registered bridge fixture.

For anchor \(x\) and candidate \(y\),

\[
d_\infty=\max_j|x_j-y_j|,\qquad
d_2=\|x-y\|_2,\qquad
d_{\rm rel}=\frac{\|x-y\|_2}{\|x\|_2},
\]

\[
d_{\rm norm}=\frac{|\|x\|_2-\|y\|_2|}{\|x\|_2},\qquad
F=\frac{|\langle x|y\rangle|^2}
{\langle x|x\rangle\langle y|y\rangle}.
\]

Zero or non-finite denominators fail closed. Fidelity clipping is permitted
only after recording the positive roundoff excess above one and requiring it
at most `1e-12`. Exact untruncated/high-cap/direct-control lanes use
`d_rel<=1e-12`, `d_norm<=1e-12`, and `1-F<=1e-12`. The held-out cap-only lane
is checked against the exact preregistered values
`d2=d_inf=5/13`, `d_norm=1/13`, and `F=144/169`, each within absolute
`1e-12`.

Each native two-site split additionally reports full and kept singular values,
kept dimension, and discarded squared weight from an uncapped shadow replay
of the same owned pre-state. The cap-only target must contain a positive
discarded weight `25/169` within `1e-12`. These split quantities are class-(c)
cause/resource diagnostics even though the bridge fixture has an independent
class-(a) derivation. They may not replace complete-state fidelity or be
promoted to a loopy-PEPS, accumulated-error, probability, Record-TV, or LER
bound.

Current parent owners are
`scripts/external_baselines/gcapeps_forced_truncation_dense_anchor.py` and
`scripts/external_baselines/run_gcapeps_native_forced_truncation.py`, with
non-formal acceptance contracts in
`tests/test_external_gcapeps_native_forced_truncation.py`. The native fork is
bound to commit `e6cbe016f336843925e01a559db26f209fa9d37b`, tree
`854ff4d5ef692497f017a57250cf8f440e47110f`; the formal runner binds parent
commit `1e9517af31f83d174bcbdf656c1955f12227b605`, tree
`17c17eb549d5f091263e7deaa86476d90420174b`. The formal verdict is
`PASS_BOUNDED_BRIDGE_TRANSIENT_TRUNCATION`: the cap-only lane observed the
positive first-CNOT tail `25/169`, `d2=d_inf=5/13`, and
`F=144/169`. Exact-tree, uncapped, high-cap, and direct-control complete
vectors agreed with the anchor to at most `3.8e-16`, and complete operator
reconstruction had `d_inf=1.25e-16`. The cutoff-loss control produced the same
complete vector as the cap-only lane while its ledger correctly named cutoff,
not cap, as the cause. The final exact state had rank one, so this is a
transient path-dependence witness rather than a final-state bond lower bound.

The raw temporary JSON had SHA-256
`55d428ceebb38aba91e1fbeb2e2a6d6f1b2f5da944534179ef2f583e4fa65ac7`
and canonical content hash
`73ca030b410b0bf60f6fc6a1e599064ec21a5c024c8ecfd28955e8f7ad934a58`.
The non-formal tests still use only the preregistration-excluded API pilot or
synthetic ledgers and cannot execute the formal target. Neither those tests nor
the formal result supplies performance, Record, multiround, qutrit/SDIM,
leakage, loopy-PEPS, global truncation-error, generic PEPS, or general
efficiency evidence.

## Preregistered pending GCAPEPS finite-memory bond-32 metrics

This subsection freezes the metric semantics for
`docs/simulator_validation/GCAPEPS_FINITE_MEMORY_BOND32_PREREG_2026-07-29.md`.
It is pending: no quantity becomes current evidence until the independent
dense, plain-Quimb, GCAPEPS, timing, and SDIM owners exist, pass their controls,
and a clean held-out artifact is published.  Width means the width of the
two-row system--memory ladder, not code distance or qudit dimension.

Epistemic classes are fixed before execution.  The BLP trace-distance object is
source-defined, while the named `>1e-10` decision threshold is class-(c).
Directional hypotheses `H_E` and `H_F` are class-(b) project predictions with
the exact one-sided/tie bands below.  Fidelity `high/degraded/low` labels and
positive-cap detection are class-(c) bounded gates.  Timing and memory are
`engineering-performance-only`, not class-(a/b) scientific predictions and not
accuracy, acceptance, portability, or asymptotic claims.

For raw complete vector \(v\) in q0-most-significant-bit order, with system
axes first and memory axes second, before any division, normalization,
reduction, Schmidt decomposition, fidelity, or entropy calculation require
one-dimensional shape `(2**(2*w),)`, exact dtype `complex128`, and finite real
and imaginary parts.  With `z=np.vdot(v,v)` computed in `complex128`, record the
raw C-order byte hash, `abs(imag(z))`, and `real(z)`; require
`abs(imag(z))<=1e-12` and finite `real(z)>0`.  This applies to every dense and
candidate vector, including each finite-ensemble path.  Only after this gate may
metric-local normalization, reduction, and comparison begin.

Every persisted numerical array uses the preregistered exact `ndarray-v1`
object with key set `(encoding,dtype,shape,order,nbytes,data_sha256,data_base64)`.
Complex vectors/states/tensors use little-endian `"<c16"`; real gauges/spectra
use `"<f8"`; source arrays are already C-contiguous c128/f64 in a required
little-endian environment.  The payload is exact `a.tobytes(order="C")` encoded
as canonical padded RFC-4648 Base64 with no whitespace and a lower-case SHA-256.
The comparator rejects wrong/extra keys, booleans in shape/nbytes, wrong
dtype/rank/shape/order/length, noncanonical Base64, hash disagreement,
nonfinite decoded values, or any raw-byte round-trip mismatch before use.  It
reconstructs the registered ndarray from decoded bytes; a hash without the raw
bytes is never a metric input.  A vector's `data_sha256` equals its independently
recorded pre-metric C-order hash.

\[
A=\operatorname{reshape}_{C}(v;2^w,2^w),\qquad
\rho_S=AA^\dagger/\operatorname{Re}z.
\]

Field ownership is strict.  Each plain/GC evidence worker owns only its raw
candidate vectors and checkpoint-local raw validation fields, candidate-only
guards, local spectra/tails/events, signed-pullback rows, algorithm
bonds/resources, and the frame-aware canonical final-carrier hash.  It receives
neither dense nor peer
candidate artifacts and cannot form a two-input trace distance.  Every vector
is marked `source_branch="instrumented_replay"`.  The terminal
comparator alone reads the neutral fixture, dense, both candidate, and SDIM artifacts and computes
all cross-artifact quantities below: `F_raw`, its correction and `F`, `D_pure`,
trace distance, `d_rel`, `d_norm`, raw/normalized `d2` and `dinf`,
signed/absolute norm error, `S1/S2` errors, checkpoint
candidate-versus-dense trace-distance error, \(\Delta F\), and every associated
verdict.  That comparator imports no Stim, SDIM, Quimb, GCAPEPS, or ECS; it joins
already emitted values/strings and recomputes numerical metrics from raw
artifacts only.

For every dense or candidate reduced state, the max-entry residuals are

\[
h_\rho=\max_{ij}|\rho_{ij}-\rho^*_{ji}|,\qquad
t_\rho=|\operatorname{Tr}\rho-1|.
\]

Both must be at most `1e-12` before forming the metric-local Hermitian copy
\(\rho_H=(\rho+\rho^\dagger)/2\).  For
\((\lambda,V)=\operatorname{eigh}(\rho_H)\), require minimum eigenvalue at
least `-1e-12` and max-entry eigenpair and reconstruction residuals at most
`1e-10`.  Eigenvalues in `[-1e-12,0)` are clipped only after recording
\(m_-=\sum_j\max(0,-\lambda_j)\le10^{-12}\), then divided by their positive
sum.  The pre-normalization sum, normalization factor, and
\(h_\rho/2\) Hermitization correction are recorded; stored states are unchanged.
Entropies use the resulting \(\tilde\lambda\) and base-2 logarithms,

\[
S_1=-\sum_j\tilde\lambda_j\log_2\tilde\lambda_j,
\qquad
S_2=-\log_2\sum_j\tilde\lambda_j^2,
\]

with \(0\log_2 0=0\).  Trace distance uses
\(\tfrac12\sum_j|\operatorname{eigvalsh}(\rho_{H,1}-\rho_{H,2})_j|\).

The normalized Schmidt values are the singular values of \(A\) divided by
\(\|v\|_2\).  Numerical rank counts values greater than `1e-12` times the
largest normalized value.  The registered entanglement hypothesis applies only
at `(width=7, axis_family=3, p_event=p_star, rounds=R_star)` to exact dense
input trajectory 1:

\[
S_1(R_\star)>S_1(1)+10^{-10}.
\]

It is a terminal-versus-first-round hypothesis, not monotonic-growth evidence.

Two BLP-style objects are distinct.  For the fixed `CARRIER` mask,

\[
D_r^{\rm carrier}
=\tfrac12\|\rho_{S,1}(r)-\rho_{S,2}(r)\|_1,
\qquad
W_{\rm carrier}=\sum_{r=1}^{R}\max(0,D_r^{\rm carrier}-D_{r-1}^{\rm carrier}),
\qquad
\delta_{\max}^{\rm carrier}=\max_{1\le r\le R}(D_r^{\rm carrier}-D_{r-1}^{\rm carrier}).
\]

For the 32 equally weighted dense-only `BLPENSEMBLE` paths,

\[
\bar\rho_{S,a}(r)=\tfrac1{32}\sum_{m=0}^{31}\rho_{S,a,m}(r),
\quad
\bar D_r=\tfrac12\|\bar\rho_{S,1}(r)-\bar\rho_{S,2}(r)\|_1,
\quad
\bar W=\sum_{r=1}^{R}\max(0,\bar D_r-\bar D_{r-1}),
\quad
\bar\delta_{\max}=\max_{1\le r\le R}(\bar D_r-\bar D_{r-1}).
\]

The density matrices are averaged before trace distance.  Averaging pathwise
distances, deduplicating coincident endpoint masks, or comparing a one-mask
candidate against the ensemble is forbidden.  Both initial distances must be
one within `1e-12`.  Only the corresponding named maximum increment greater
than `1e-10` gates a witness; each summed \(W\) is report-only.  A pass is
respectively `BLP_WITNESSED_FIXED_MASK` or
`BLP_WITNESSED_FINITE_32_MASK_ENSEMBLE` for that named pair and map only; the
corresponding `NO_WITNESS_*_FOR_REGISTERED_PAIR` result is not a Markovian
verdict.  Persistent memory, entanglement, bond growth, or a candidate-only
revival is not a BLP witness.

At `p_event=0`, exact fixed-path and 32-path ensemble controls require every
event bit and active rotation count to be structurally zero, every-round
system--memory \(S_1,S_2\le10^{-12}\) for both inputs, both named trace-distance
trajectories within `1e-12` of one, and no maximum increment above `1e-10`.
Failure is a negative-control failure.  Candidate fidelity and checkpoint
trace-distance errors remain ordinary faithfulness diagnostics and never become
candidate BLP evidence.

At every materialized candidate checkpoint, the only candidate trace-distance
diagnostic is the terminal comparator's
\(|D_r^{\rm candidate}-D_r^{\rm dense}|\) for the fixed `CARRIER` mask.  A
single-input evidence worker cannot form it.  Sparse-checkpoint increments are
never summed or named a candidate BLP measure or BLP-measure error.

For dense reference \(x\) and candidate \(y\), both raw `complex128` complete
vectors, the mandatory metrics are

\[
F_{\rm raw}=\frac{|\langle x|y\rangle|^2}
{\langle x|x\rangle\langle y|y\rangle},
\]

\[
d_{\rm rel}=\frac{2\|x-y\|_2}{\|x\|_2+\|y\|_2},
\qquad
d_{\rm norm}=\frac{2|\|x\|_2-\|y\|_2|}
{\|x\|_2+\|y\|_2}.
\]

Both norm-squared denominators and \(F_{\rm raw}\) must be finite; each
denominator must be strictly positive; and \(F_{\rm raw}<0\) fails.  The raw
value and `fidelity_roundoff_correction=max(0,F_raw-1)` are mandatory.
Set \(F=\min(1,F_{\rm raw})\) only when the correction is at most `1e-12`; a
larger excess fails.  Thus a gross \(F_{\rm raw}>1\) cannot be hidden by the
pure-state distance calculation.  Zero/nonfinite denominators and nonfinite or
negative raw fidelity also fail.

After that gate, \(D_{\rm pure}=\sqrt{1-F}\).  No square root or
fidelity clipping is evaluated before the gate passes.

Writing \(n_x=\|x\|_2\), \(n_y=\|y\|_2\),
\(\hat x=x/n_x\), and \(\hat y=y/n_y\), the mandatory companion metrics are

\[
d_{2,\rm raw}=\|x-y\|_2,\qquad
d_{\infty,\rm raw}=\max_j|x_j-y_j|,
\]

\[
d_{2,\rm normalized}=\|\hat x-\hat y\|_2,\qquad
d_{\infty,\rm normalized}=\max_j|\hat x_j-\hat y_j|,
\]

\[
\Delta n_{\rm raw}=n_y-n_x,\qquad
e_{n,\rm raw}=|\Delta n_{\rm raw}|,\qquad
e_{S_k}=|S_k^{\rm candidate}-S_k^{\rm dense}|\quad(k=1,2).
\]

Both raw norms are recorded.  Stored vectors are hashed before any metric-local
normalization.  Phase fitting, coordinate permutation, dtype casting, or
normalizing stored candidate/reference payloads is forbidden.

An independent small vector/matrix known-answer suite must exercise the raw
vector gate; permitted tiny-negative eigenvalue clipping; gross negativity,
non-Hermiticity, trace, eigenpair, and reconstruction failures; and hand-check
`F`, `D_pure`, trace distance, `d_rel`, `d_norm`, raw/normalized `d2`/`dinf`,
signed/absolute norm error, and `S1/S2` error.  Zero/nonfinite vectors fail
before division.  This validates the metric implementation, not the candidate state.

The stress-cell comparison is

\[
\Delta F=\min_a F_{\rm GC}^{(a)}(R_\star)
-\min_a F_{\rm plain}^{(a)}(R_\star),
\]

with `supported` for \(\Delta F>10^{-10}\), `tie/inconclusive` for
\(|\Delta F|\le10^{-10}\), and `falsified` for \(\Delta F<-10^{-10}\).
The project-only labels `high` (\(F\ge0.99\)), `degraded`
(\(0.95\le F<0.99\)), and `low` (\(F<0.95\)) describe only a bounded output.

A local split is a positive bond-32 cap event only if

```text
full_bond_dimension > 32
kept_bond_dimension == 32
discarded_squared_weight > 1e-12
cause == "max_bond"
configured_max_bond == 32
```

The stress verdict is eligible only if plain/GC crossed with both registered
inputs all independently satisfy that rule.  Full and kept spectra, discarded
weight/fraction, and cause are local class-(c) diagnostics, never a whole-state,
observable, probability, Record, or accumulated-error certificate.
Complete vectors, full/kept spectra, tail weights/fractions, positive-event
counts, candidate-only guards, signed-pullback rows, algorithm bonds/resources,
and the frame-aware canonical final-carrier hash are mandatory in evidence
schemas.  Cross-artifact
state metrics and verdicts are forbidden there and mandatory only in the
terminal comparator schema.  Performance schemas omit vectors, guards,
spectra/tails/events, and cross-artifact metrics rather than emit null/zero; they
retain only algorithm bond fields, logical/process memory, the same
frame-aware canonical final-carrier hash, and timing.

Calibration cap discovery uses separate calibration-only probe workers.  A
probe executes only the instrumented candidate path, creates an uncapped shadow
from the immediate pre-split state for every selected two-site split, and has no
complete no-shadow branch, vector output, cross-artifact metric, or timing-role
output.  It stops only after the physical operation containing the first
positive split has fully validated and committed, before the next operation;
for GC, one operation includes exact lowering, every routed compression split,
and commit.  If no positive split occurs it completes the trajectory.  Its
output is limited to cap rows, the stop locator, provenance, logical/process
resource observations, and raw worker/supervisor duration.  A probe-positive
path that is full-evidence-negative is an invalid control, never a selected
cell.  Each probe launch is counted before launch against the shared 100-attempt
Stage-B/C calibration ceiling.

Bond resources use exactly `max_exact_precompression_bond` (GC only and null
for plain), `max_committed_bond`, and `final_committed_bond`.  The first records
the exact routed transient before native compression; the latter two observe
only committed states.  Plain physical-PEPS and GC residual-PEPS bonds are
separate diagnostics and never a common physical-entanglement or accuracy
metric.

Timing is engineering-performance-only.  Worker wall spans use
`time.perf_counter_ns`; CPU spans use main-process user-plus-system
`time.process_time_ns`; integer offsets are relative to process-local roots.
Those CPU spans include the worker's native threads but not a short-lived child
process.  The live unit-cgroup `cpu.stat[usage_usec]` is the separately named
child-inclusive process diagnostic and never substitutes for a worker span or
enters the main-process CPU ratio.
Every span has exact `duration=end-start`; every parent has exact
`duration=sum(direct children)+unattributed`, with no tolerance.  Zero-duration
leaves are legal; negative durations and nonpositive ratio/root values are not.

Warmups are exactly `plain,gc`; measured order is exactly
`plain[0],gc[0],gc[1],plain[1],plain[2],gc[2]`.  The aggregation key is
`(case_id,lane,trajectory_id=1,scope,round_index,operation_index,step_index,kind)`.
Each key retains the three raw wall/CPU samples and reports median, unscaled
`MAD=median(abs(x-median(x)))`, minimum, and maximum over exactly indices
`0,1,2`.  Values never pool across round/operation/step/kind.
`state_update_only` is summed per worker before the three-worker aggregate.
Evidence, dense, SDIM, comparator, and workflow spans are singleton raw values
with no fabricated aggregate fields.

The primary input-1 ratios are

\[
R_{T,\rm wall}=\frac{\operatorname{median}(T^{\rm algo,wall}_{\rm GC})}
 {\operatorname{median}(T^{\rm algo,wall}_{\rm plain})},\qquad
R_{T,\rm cpu}=\frac{\operatorname{median}(T^{\rm algo,cpu}_{\rm GC})}
 {\operatorname{median}(T^{\rm algo,cpu}_{\rm plain})},
\]

with analogous same-direction `ratio_gc_over_plain` for measured fresh-process
supervisor-launch wall and the completed trajectory-1 evidence-worker total.
Only the first three performance-derived ratios—algorithm wall, algorithm CPU,
and supervisor-launch wall—require exactly three of three completed measured
workers per lane and 3/3 final-carrier-hash equality to the matching evidence
branch.  The evidence ratio is a singleton raw plain/GC comparison, never a
fabricated 3/3 population.  Any missing, censored, nonfinite, or nonpositive
required sample makes the affected ratio and band unavailable; completed rows
and reasons remain.  Evidence trajectory 2 has a separate singleton descriptive
ratio.

`validation_and_evidence_materialization` is absent, not zero, in performance
workers.

For evidence, `candidate_algorithm_case_e2e` and `state_update_only` contain
exactly the first complete no-shadow trajectory.  After its scalar/ledger/hash
fields are frozen and carrier released, the entire second trajectory is nested
as
`validation_and_evidence_materialization/instrumented_replay_total`, including
its initialization, every repeated frame/tableau/PEPS update, validator,
commit, uncapped shadow, checkpoint lift/contraction, materialization, hash
comparison, and release.  None may be primary algorithm time or unattributed.
The raw candidate arrays come from this instrumented replay; its final-carrier
hash must equal the no-shadow hash.  `evidence_worker_total` and singleton
`R_evidence` contain both trajectories and serialization; performance executes
only the no-shadow trajectory.

`case_workflow_supervisor_wall_ns` is the absolute serial per-cell
total across dense, evidence, performance, SDIM, and comparator launches and
has no lane ratio.  Its end is immediately after the last required child
launch receipt for that cell is atomically published and before any case-summary
publication; summary-publication duration is an external publisher result, not
part of the self-contained workflow total.  An early stop is marked partial and
excluded from complete workflow aggregates.  Calibration and heldout totals
never mix.  Only
\(R_{T,wall}\) receives the descriptive bands: GC faster below `0.80`, same
order on `[0.80,1.25]`, and GC overhead above `1.25`.  These are not
acceptance, portability, or asymptotic claims.

Every clean exit-zero worker result uses two length-prefixed canonical-JSON
frames on stdout.
Scientific array construction/validation occurs before `serialization`; that
leaf rechecks raw hashes, builds each `ndarray-v1` Base64 wrapper, and constructs
the core canonical bytes, but excludes stdout writes/trailer.  The worker root
then ends.  It samples
`resource.getrusage(resource.RUSAGE_SELF)` and constructs/writes a small late
telemetry trailer outside the worker root.

Before loading evaluator output, the root runner sets `PR_SET_DUMPABLE=0`,
requires `PR_GET_DUMPABLE==0`, and binds its PID, proc start time, real uid/gid,
and non-dumpability.  One no-scientific-input preflight uses only the
noninteractive systemd-255 system manager; user-manager and later manager
fallback are forbidden.  Every service has `DynamicUser=yes`, a host uid
distinct from the runner and other live services, and only the frozen numeric
repository-read supplementary gid.  It must be denied the evaluator root, the
runner's `/proc` root/fd/mem, ptrace, and `process_vm_readv`.

The root atomically publishes and externally hashes
`outputs/external_baselines/gcapeps_finite_memory_bond32/manager_preflight_receipt.json`
under `.manager_preflight_receipt.v1`, without a self complete digest.  The
publisher uses a held parent dirfd, temporary-file fsync, no-replace rename,
parent fsync, `O_NOFOLLOW` reopen, and exact destination identity.  Inventory
and every later child rehash and bind its schema/projection/length/complete SHA;
the calibration report and amendment retain the same manager/security
projection.  Failed preflight starts no inventory or science.

Every child uses a never-reused transient service and exactly one `ExecStart`
under `systemd-run --system --no-block --no-ask-password`; `--wait`, `--pipe`,
`--collect`, user-manager execution, and fallback placement are forbidden.  The
unit has `Type=oneshot`, `RemainAfterExit=yes`, `Restart=no`, `DynamicUser=yes`,
the frozen numeric `SupplementaryGroups`, `PrivateUsers=yes`,
`ProtectSystem=strict`, `ProtectHome=read-only`, read-only repository access,
an inaccessible exact run-output root, `NoNewPrivileges=yes`, private tmp,
devices, and network, `RestrictSUIDSGID=yes`, `LimitCORE=0`, control-group kill,
memory/tasks accounting, and the preregistered timeout properties.  It has exact
`CPUAffinity=<selected_cpu_decimal>` for the single minimum CPU in the runner's
preflighted affinity; `AllowedCPUs`, inherited multi-CPU affinity, or any second
placement rule is forbidden, and every child proves the same singleton effective
affinity.  Each launch has exact
`RuntimeDirectory=gcapeps-fm-<launch_id>`, `RuntimeDirectoryMode=0755`, and
`RuntimeDirectoryPreserve=no`; the directory contains no evaluator state, and
the sole failure-snapshot path is
`/run/gcapeps-fm-<launch_id>/failure_snapshot.json`.  Every effective property
is read back verbatim.

Performance units use `MemoryMax=12884901888` and `TimeoutStartSec=600s`; all
other children use `MemoryMax=25769803776` and `TimeoutStartSec=1800s`.  Every
unit uses `RuntimeMaxSec=infinity`, `MemorySwapMax=0`, and `TasksMax=32`.
Calibration separately arms its absolute 12-hour monotonic watchdog; only its
recorded cgroup kill is the deadline-censor initiator.  Binary file caps are
exact:

| role class | `core_max` | `trailer_max` | `LimitFSIZE` |
|---|---:|---:|---:|
| dense reference | 1073741824 | 16777216 | 1090519056 |
| plain/GC evidence | 268435456 | 16777216 | 285212688 |
| fixture, probe, performance, inventory, SDIM, comparator, control | 67108864 | 16777216 | 83886096 |

`raw.stderr` has a 1048576-byte post-write validation cap in addition to the
role-wide kernel `LimitFSIZE`; the trusted helper refuses to write, and the
supervisor refuses to accept, a failure snapshot above 1048576 bytes.  Ordinary
stdin is capped at 67108864 bytes and comparator stdin at 4294967296
bytes.  The supervisor holds a device/inode-sealed dirfd for a fixed mode-0700
spool parent outside the denied output root.  Before every launch its child set
is empty; it creates one fresh canonical absolute `spool_abs` with only
mode-0600 `fixture.stdin`, `raw.stdout`, `raw.stderr`, and
`failure_snapshot.copy`.  The exact unit properties are

```text
StandardInput=file:<spool_abs>/fixture.stdin
StandardOutput=file:<spool_abs>/raw.stdout
StandardError=file:<spool_abs>/raw.stderr
```

PID 1 opens those inodes before the distinct `DynamicUser` runs.  The child gets
only fds 0/1/2 and cannot traverse the supervisor-owned spool; relative paths,
symlinks, identity drift, auxiliary descriptors, extra entries, or paths outside
the sealed parent are invalid.

Every child's sole scientific/protocol input is a bounded, sealed stdin
container under
`error_coupling_simulator.external.gcapeps_finite_memory.input_transport.v1`:

```text
u64be(manifest_len) || canonical_manifest ||
repeat in manifest entry order:
    u64be(artifact_len) || exact_artifact_bytes
```

The manifest is capped at 16777216 bytes and 64 entries and binds the role,
ordered unique allowlisted names, schemas, exact byte lengths, and SHA-256
values.  Before allocation the child `fstat`s fd 0, enforces its total stdin
cap, reads only the eight-byte manifest prefix, uses checked integer arithmetic,
requires exact container-size equality, then hashes each bounded entry before
parsing it.  The exact `role_parameters` schema is not an artifact entry.  Define
the only production entry sequences:

```text
I_CAL  = (manager_preflight_receipt,
          sdim_inventory_envelope, sdim_inventory_launch_receipt)
I_HELD = I_CAL || (target_amendment,)
B_CAL  = I_CAL  || (neutral_fixture_envelope,
                    neutral_fixture_launch_receipt)
B_HELD = I_HELD || (neutral_fixture_envelope,
                    neutral_fixture_launch_receipt)
X      = (dense_envelope, dense_launch_receipt,
          plain_input1_envelope, plain_input1_launch_receipt,
          plain_input2_envelope, plain_input2_launch_receipt,
          gc_input1_envelope, gc_input1_launch_receipt,
          gc_input2_envelope, gc_input2_launch_receipt,
          sdim_envelope, sdim_launch_receipt)
```

| run partition | child role | ordered artifact entry sequence |
|---|---|---|
| bootstrap | sacrificial manager preflight | empty |
| bootstrap | SDIM inventory collector | `(manager_preflight_receipt,)` |
| calibration | neutral-fixture emitter | `I_CAL` |
| held-out | neutral-fixture emitter | `I_HELD` |
| calibration | dense reference / BLP ensemble | `B_CAL` |
| held-out | dense reference / BLP ensemble | `B_HELD` |
| calibration | plain or GC probe/evidence | `B_CAL` |
| held-out | plain or GC evidence/performance | `B_HELD` |
| calibration | SDIM computation | `B_CAL` |
| held-out | SDIM computation | `B_HELD` |
| calibration | terminal comparator | `B_CAL || X` |
| held-out | terminal comparator | `B_HELD || X` |

The four evidence pairs inside `X` stay in the displayed order.  There is no
production wildcard, optional artifact entry, or other role; corruption
controls use separately enumerated synthetic roles.  A calibration performance
container is forbidden; performance exists only in held-out.  Thus held-out input always
includes `target_amendment`; an SDIM computation receives no dense, plain,
GC/candidate, comparator, or performance bytes; a candidate receives no dense,
peer-candidate, SDIM-result, or comparator bytes; and only the terminal
comparator receives cross-role numerical evidence.

Before writing the container, the supervisor opens every source with
`O_NOFOLLOW`, verifies its bound inode/schema/length and externally owned
complete-file SHA-256, and copies the exact bytes without re-encoding.  It
fsyncs `fixture.stdin` and the spool directory, reopens/fstats the stdin inode,
then reparses the complete container with the same bounds and requires each
entry length/hash to equal both its bytes and the external source hash.  The
final node envelope binds the container byte length/SHA-256 and ordered entry
name/source-SHA sequence.  Missing, extra, duplicated, reordered, oversize,
hash-mismatched, or noncanonical input is `invalid_control`; “reads an artifact”
always means consuming this sealed stdin copy, never opening the output tree.

A clean worker writes exactly two frames and empty stderr, flushes and `fsync`s
stdout, then self-stops with uncatchable `SIGSTOP`.  The supervisor requires the
live stopped `MainPID`, exactly one process in `cgroup.procs`, and every cgroup
thread stopped.  Before allocating or parsing JSON it `fstat`s the sealed
stdout/stderr inodes, applies the role's `LimitFSIZE`/stderr caps, reads only the
first eight bytes, checks unsigned `L_core<=core_max`, uses checked addition to
locate the second prefix, checks `L_trailer<=trailer_max`, and requires exactly
`8 + L_core + 8 + L_trailer == raw_stdout_st_size` before either bounded
payload read.  Overflow, short/truncated prefixes, oversize, or one extra byte
is `invalid_control`, never a resource censor.

While tasks remain stopped, the supervisor reads live-ControlGroup
`memory.peak/current/swap.current`, every `memory.events` key,
`pids.current/peak`, every `pids.events` key, and `cpu.stat`.  Clean evidence
requires zero swap; zero `memory.events[max]`, `oom`, `oom_kill`, and
`oom_group_kill`; zero `pids.events[max]`; and `pids.peak<=32`.
`cpu.stat[usage_usec]` is a child-inclusive lifecycle diagnostic.  It is kept
separate from worker `process_time_ns`, which is main-process-only and alone
enters the CPU ratio.  After `SIGCONT`, clean termination must be
`active/exited`, `Result=success`, `ExecMainCode=exited`,
`ExecMainStatus=0`, and `MainPID=0`; the retained pre-stop systemd `MemoryPeak`
equals live `memory.peak`, while the final helper-inclusive retained peak is
recorded separately before unload.

The declared `ExecStopPost` helper writes only a failed service's canonical
`.systemd_failure_snapshot.v1` as mode 0644 at the exact RuntimeDirectory path,
refusing payloads above 1048576 bytes.  It captures the live cgroup facts,
fsyncs both the snapshot and runtime-directory fd, then sends uncatchable
`SIGSTOP` to itself before exit.  A pre-existing file, wrong identity, missing
stopped `ControlPID`, or helper failure is invalid.  Within a 10-second monotonic
helper-barrier deadline, strictly inside `TimeoutStopSec=15s`, the supervisor
opens with `O_NOFOLLOW`, validates and hashes the snapshot, copies those exact
bytes into the sealed `failure_snapshot.copy`, fsyncs the copy, then sends
`SIGCONT`.  It requires clean helper exit and removal of the non-preserved
RuntimeDirectory before unload.  On service success the helper is a no-op, the
copy remains empty, and the runtime directory is still removed.  This is
supervisor infrastructure, never candidate output or a timing/memory sample; a
launch failure before unit creation records explicit null cgroup fields.

Trusted manager/supervisor facts are classified before child bytes.  A start
timeout is a supervisor censor only before both the self-stop barrier and
`SIGCONT`; a timeout after either is lifecycle `invalid_control`.  The only
external censors are the registered absolute-deadline kill, OOM/oom-kill,
nonzero `memory.events[max]`, nonzero `pids.events[max]`, or exact pre-/post-unit
launch-resource events.  Configuration, permission, executable, path, D-Bus,
unit-name, namespace, or property failures are invalid.  External-censor stdout
may be absent or truncated and is retained as bounded opaque bytes; if exactly
two frames are present they must still be canonical, and an extra byte remains
invalid.  Only a clean released exit-zero unit can produce `completed_result`
or `worker_censor`; malformed/nonfinite/schema-invalid clean frames,
unexpected exit/signal/core, and late failures are invalid.  An early PASS never
overrides a later terminal fact.

Every child-byte disposition remains provisional through a 30-second bounded
cleanup.  After live/failure evidence is captured, the supervisor stops or
reset-fails the unit, records the final helper-inclusive systemd `MemoryPeak`,
requires `LoadState=not-found`, then atomically no-replace-renames the sealed
spool into `<run_output_abs>/raw_spools/<launch_id>`, fsyncs both parents,
reopens every quarantined inode, and proves the outside spool parent empty.
Cleanup, unload, or quarantine failure changes the final kind to
`invalid_control`, publishes no science result, and prevents later science.

Only after cleanup and quarantine does the supervisor atomically publish the
final `.node_terminal.v1` envelope with exactly one of `completed_result`,
`worker_censor`, `supervisor_censor`, or `invalid_control`, binding the applicable
validated frames or bounded raw hashes plus unit/cgroup, exit, failure-snapshot,
final-peak, cleanup, and quarantine facts.  It contains no encompassing launch
duration.  The supervisor-launch clock ends immediately after that envelope;
only then is `.launch_receipt.v1` atomically published, binding the envelope's
complete-file SHA, final kind, cleanup/quarantine facts, and
`supervisor_launch_wall_ns`.  Receipt publication is outside the span; a failed
receipt is root-level invalid and cannot be repaired by the earlier envelope.
`R_launch` reads only three complete measured receipts, and parent reports own
their complete-file SHAs.  Calibration eligibility additionally uses
`.calibration_publication_receipt.v1` to bind the report commit offset and final
class.

All result core frames, trailers, final envelopes, amendments, and reports use
exactly `json.dumps(value, ensure_ascii=True, allow_nan=False, sort_keys=True,`
`separators=(",", ":")).encode("utf-8")`, with no trailing newline.
`result_projection_sha256` hashes that canonical projection after removing
exactly that field and nothing else; forbidden nonfinite numbers fail before
publication.

Every persisted JSON artifact in this protocol uses one publication primitive.
The publisher holds the destination parent dirfd, creates a same-directory
mode-0644 temporary file with `O_CREAT|O_EXCL|O_NOFOLLOW`, writes the already
canonical bytes, fsyncs the file, uses
`renameat2(..., RENAME_NOREPLACE)`, and fsyncs the parent.  It then reopens the
destination relative to the held dirfd with `O_NOFOLLOW`, requires the expected
device/inode/mode-0644/link-count-one identity, rereads exactly those bytes, and
externally records byte length and SHA-256.  Publication receipts use the same
primitive; no artifact may weaken the sequence or rewrite a destination.

The supervisor or parent report separately owns every nonterminal complete-file
SHA; a file never self-hashes.  The held-out terminal path is
`outputs/external_baselines/gcapeps_finite_memory_bond32/heldout_report.json`
with schema
`error_coupling_simulator.external.gcapeps_finite_memory.bond32_comparison.v1`.
It owns child envelope/receipt SHAs, forbids its own complete-file SHA field,
and retains `result_projection_sha256`.  After publication the outer runner
hashes the exact destination bytes.  The reserved future result-note path is
docs/simulator_validation/GCAPEPS_FINITE_MEMORY_BOND32_RESULT_2026-07-29.md;
it is intentionally absent until a formal held-out run, after which the
tracked note persists that SHA without claiming its own containing commit.

Logical resource bytes use four nonoverlapping base categories:

- `carrier_tensor_bytes` for raw `candidate._psi` arrays, with
  `tensor_role` equal to exactly one of `plain_physical`, `gc_residual`;
- `gauge_spectrum_bytes` for live gauge-store arrays only;
- `frame_bytes` for canonical live-frame payload, exactly zero for plain;
- `ledger_bytes` for algorithm-owned physical/construction/compression/
  frame-update/signed-pullback ledgers only.

Timing, memory, provenance, result, comparison, shadow spectra, and tail rows are
excluded from `ledger_bytes`.  Their sum is `total_owned_logical_bytes`.
Underlying NumPy roots are deduplicated by identity within one category; a root
alias across categories is rejected.  Frame/ledger sizes are canonical-JSON
UTF-8 lengths.

Evidence additionally owns `evidence_auxiliary_array_bytes` for the complete
instrumented branch, uncapped shadows, vectors, and literal lifts, plus
`evidence_auxiliary_ledger_bytes` for that branch's frame/ledgers, full/kept
spectra, tails, and evidence metadata.  At each evidence sample,

```text
evidence_owned_logical_bytes =
    current_base_total_owned_logical_bytes
    + evidence_auxiliary_array_bytes
    + evidence_auxiliary_ledger_bytes
```

The no-shadow branch executes the complete trajectory from the registered
initial fixture, freezes its base scalar/ledger/transcript/final-carrier-hash
values in memory without constructing core bytes, and releases it before the
instrumented branch executes the same complete trajectory from a byte-identical
initial fixture.  Within that instrumented
branch only, each uncapped split shadow starts from the immediate pre-split
state.  Every shadow is a complete carrier copy: its tensors/gauges enter the
auxiliary-array category and its separately owned frame/history/ledgers enter
the auxiliary-ledger category.  No complete branches coexist unless both are
fully counted.  Only the no-shadow branch owns base algorithm resource fields;
the second branch is evidence-only.  After no-shadow release,
`current_base_total_owned_logical_bytes=0`; retained result metadata is excluded
from algorithm logical bytes.  The two final-carrier hashes must agree.
Dense and comparator processes separately use `dense_reference_array_bytes`
and `comparator_array_bytes`; those bytes never enter plain/GC lane totals.

Algorithm/evidence workers report
`final_committed_owned_logical_bytes`,
`max_committed_owned_logical_bytes`, and
`max_sampled_algorithm_owned_logical_bytes`; evidence workers additionally
report `max_sampled_evidence_owned_logical_bytes`, while performance workers
omit it.  Dense/comparator workers report their separately named sampled maxima.
`max_committed` observes one current committed carrier after predecessor release;
`max_sampled_algorithm` includes old-committed plus uncommitted-candidate
coexistence.  Sampling covers initialization, candidate creation, named
substeps, pre/post commit, predecessor release, complete instrumented-branch
creation, shadow creation/completion/pre-release, and vector/lift
materialization/pre-release.  Every registered persistent auxiliary crosses a
hook.

Python-object, allocator, cache, interpreter, and between-sample ephemeral
library/SVD workspaces are excluded from logical bytes.  The post-root/pre-trailer
`resource.getrusage(resource.RUSAGE_SELF).ru_maxrss` sample is KiB and converts
by `*1024`; the live pre-release cgroup snapshot and retained systemd
`MemoryPeak` are bytes.  Process peaks supplement but do not replace logical sampling.
Neither memory family is an accuracy certificate.

Candidate inputs are discriminated by `run_partition`.  `CALIBRATION` forbids
all amendment/held-out identities and binds the theory-only commit,
preregistration/hash, calibration pair/seed/stage/attempt, fixture,
implementation, and environment.  `HELDOUT` requires the clean amendment
commit/tree/file hash and exact held-out cell/list identity.  Both reject every
dense/comparator path, hash, value, vector, metric, verdict, and locator
recursively.  In both partitions a fresh distinct-`DynamicUser` system service
receives only its role-allowlisted entries in the sealed `input_transport.v1`
stdin container through the absolute inode-sealed `StandardInput=file:`; argv
contains no artifact path and no auxiliary descriptor exists.  The candidate
never receives dense or comparator truth.  The comparator alone later receives
the full neutral-fixture, dense, candidate, and SDIM byte bundle.  Candidate
`InaccessiblePaths=` names the exact output root, and a corruption process must
be denied both the known dense path and the runner's proc root/fd/mem and
cross-process read attacks.  A clean candidate can return only the two stdout
frames and empty stderr; all effective security/input identities are recorded.

Held-out execution uses the fixed serial node order.  Any dense, evidence,
SDIM, or comparator scientific censor skips every later node in the current
cell, marks that cell/sweep incomplete, and continues with the next cell.  A
performance-only censor is the sole exception: later scientific nodes continue
and only timing is unavailable.  If an SDIM censor occurs after completed
performance, its raw performance rows remain but the cell and Q4 terminal
classification are unavailable.  Any invalid control stops the current cell
and all later cells.

The planned metric owners are the independent dense-reference worker, separate
plain/GC evidence workers, separate plain/GC performance workers, and the
terminal comparator
`scripts/external_baselines/compare_gcapeps_finite_memory_bond32.py`, as frozen
in `docs/NUMERICAL_PROVENANCE.md`.  For every calibration Stage-D seed and
held-out cell/input/preparation hash/prefix/actual-collision locator, the SDIM
worker emits its signed Pauli body/sign plus an independently replayed Stim
body/sign and their internal equality, without reading GC evidence.  The
neutral fixture owns, before any worker, the exact lexicographically ordered
request-key sequence whose key is

```text
K = (run_partition, case_id, input_id,
     input_preparation_transcript_sha256,
     shared_evolution_transcript_sha256, round_prefix,
     collision_ordinal, round_index, site_index, axis_index,
     physical_pauli_body)
```

`round_prefix` and `round_index` are one-based; `collision_ordinal`,
`site_index`, and `axis_index` are zero-based, with axes `0,1,2 = X,Y,Z`.
`physical_pauli_body` is the complete q0-to-last `IXYZ` word of length `2*w`,
and `case_id` is the exact fixture-owned held-out cell id or calibration Stage-D
pair/seed id.  No extra or coercible key field is legal.

Let `E` be that fixture sequence, `S` and `T` the SDIM and independently built
Stim sequences, and `G_raw` the concatenation without deduplication of the two
GC evidence sequences.  Each source first rejects local duplicates, and the
comparator separately rejects duplicates across the GC artifacts before forming
`G=sorted(G_raw)`.  Without reading GC evidence, the SDIM worker requires exact
ordered equality `E == S == T`.  The comparator alone receives all four sources
and, before any signed-value comparison, requires exact ordered-sequence
bijection `E == S == T == G`, equal cardinality, and exactly one occurrence of
every key.  `sdim_equals_stim=true` and an inner-join intersection are not
coverage evidence.  Missing, extra, duplicate, reordered, cross-input,
wrong-preparation, wrong-prefix, or wrong-collision rows are hard invalid
controls.  SDIM owns no
numeric state metric and enters no GC/plain timing ratio; its singleton raw
worker/supervisor duration is engineering telemetry only.  The comparator
imports no Stim/SDIM/Quimb/GCAPEPS/ECS backend.

Exactly one SDIM inventory collector runs after implementation freeze but before
the calibration wall root.  It emits its `.sdim_inventory.v1` core only through
the standard two-frame stdout/self-stop protocol and receives only the
preflight-receipt identity.  After cleanup and raw-spool quarantine, its one
ordinary final supervisor envelope is atomically published directly at
`outputs/external_baselines/gcapeps_finite_memory_bond32/sdim_inventory.json`.
That file's top-level schema is `.node_terminal.v1`; its nested role-specific
core is the unchanged `.sdim_inventory.v1`.  There is no second re-encoded core file.
The subsequent launch receipt binds this envelope, while the collector can
receive or record neither its own envelope nor its launch-receipt complete-file
SHA.  The supervisor freezes and later children bind the top/core schemas,
inventory-state hash, result-projection hash, envelope complete-file SHA, and
launch-receipt complete-file SHA.  Every SDIM replay rederives byte-identical
live installed state, and regeneration requires a new calibration.  Worker and
launch durations are bootstrap telemetry and enter no case or efficiency ratio.

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
- The bounded XZZX measurement/reset bridge registers five distinct objects through
  `scripts/external_baselines/compare_xzzx_record_peps.py`, with independent value, boundary,
  alignment, order, and proxy-firewall tests in `tests/test_external_xzzx_record_metrics.py`.
  Complete-vector fidelity uses the normalized formula above, but the XZZX owner separately binds
  the hash-pinned d3 preterminal 17-qubit state or d5 preterminal 25-data-qubit state, sorted
  physical-axis order, and complete complex128 vector; its usefulness bands are class (c).
  Tracer raw-trajectory TV is the class-(b) quantity
  `0.5*sum_x abs(p(x)-q(x))` on the complete declared ten-bit raw-measurement support, including
  structural-zero strings. It is explicitly not the folded detector/observable Record metric.
  Selected-branch maximum conditional-probability error is
  `max_k abs(p_candidate,k-p_reference,k)`, and selected-branch log-mass error is
  `abs(sum_k log(p_candidate,k)-sum_k log(p_reference,k))`; both are class-(c) gates on aligned
  measurement columns, with no probability floor and a hard error for a reference selected
  probability below `1e-12` or zero candidate selected probability. Post-reset one-site trace distance
  is the class-(a) identity `0.5*||rho-|0><0|||_1`, evaluated on a normalized Hermitian
  one-site density operator rather than an MPS tensor slice. These metrics are bounded to the
  two-round all-qubit experiment being frozen in
  `docs/simulator_validation/PEPS_XZZX_MEASUREMENT_RESET_RECORD_PREREG_V2_2026-07-27.md`; the v1
  Aer-reference route was killed before formal target execution. These metrics do not
  certify d5 full-law TV, leakage/Kraus dynamics, a decoder/LER, long-time scaling, or scalable
  exact PEPS contraction.
