# MPS/PEPS record-faithfulness literature closure — 2026-07-17

## Decision

The tensor-network literature closes the representation and local numerical-mechanics questions needed
to interpret the current restricted carriers, but it does **not** certify the complete simulator output law.

- The restricted MCWF/MPS and QT/MPS routes may use canonicalization, local SVD diagnostics, explicit
  raw-norm bookkeeping, and finite-bond convergence sweeps as verification machinery.
- A local discarded weight, TDVP residual, PEPS environment fidelity, FET overlap, entropy match, or
  bond-dimension plateau is not by itself a bound on the joint multi-round detector/observable `Record`.
- The PEPS/FET path remains a research surface until a non-degenerate rank-reducing update passes an
  independent state/record oracle. An all-noop fallback cannot be promoted by a literature citation.
- No production pruning or full-record-faithfulness claim is authorized by this packet.

Packet status:

- `closure_status: open`
- `closed_subscope: representation_and_local_numerical_mechanics`
- `record_bridge_status: missing`
- `downstream_status: production_and_preregistration_blocked`

## Frozen question and kill condition

The question was frozen before using benchmark outcomes:

> Which facts from MPS trajectories, MPS truncation, finite PEPS, closed-loop truncation, and PEPS
> sampling transfer to the simulator's declared sequential `Record`, and which facts stop at a state,
> environment, observable, or cost surrogate?

The kill condition is source-independent: if a paper does not control both probability mass and the
conditional post-operation state through the complete adaptive instrument sequence, it cannot be used as
a complete-record certificate. A fixed-time density estimate or terminal bitstring distribution is not
silently substituted for the multi-round `Record`.

## Project authority and separation rule

The binding project claims come from `docs/SIMULATOR.md`, `docs/METRICS.md`, and
`docs/FAITHFULNESS_PROTOCOL.md`. Source-only facts remain in schema-valid notes under
`docs/papers/reading_notes/`; project mappings and decisions remain in this audit family. Legacy notes,
RAG hits, knowledge-graph hits, and search snippets route readers to primary sources but are not evidence.

## Current-corpus roster

`docs/papers/CURRENT_CORPUS.toml` binds 11 source-reviewed notes and 153 `paper_fact` sections under
corpus SHA-256 `49a22a310b015c3676741623c64b45ff5237c98223dfd942d824952ce3a95e15`.
Ten notes form this carrier-precision closure core; the eleventh, Wood--Gambetta, is retained as a
project-level leakage baseline and is not used as a tensor-network precision premise.

| Core source | Bound note | Load-bearing Fact IDs |
|---|---|---|
| Paeckel et al. | `docs/papers/reading_notes/paeckel_mps_time_evolution_1901.05824_source_review.md` | `paeckel-canonical-cut`; `paeckel-direct-svd-error`; `paeckel-tebd-error-separation`; `paeckel-tdvp-errors` |
| Jaschke et al. | `docs/papers/reading_notes/jaschke_open_system_tn_1804.09796_source_review.md` | `jaschke-effective-hamiltonian`; `jaschke-solver-norm-caveat`; `jaschke-waiting-time-trigger`; `jaschke-jump-selection` |
| Sander et al. (2025) | `docs/papers/reading_notes/sander_tensor_jump_2501.17913_source_review.md` | `sander-tjm-jump-trigger`; `sander-full-bond-theorem`; `sander-error-inventory`; `sander-projection-error` |
| Fröhlich et al. | `docs/papers/reading_notes/froehlich_tensor_jump_2607.01323_source_review.md` | `fact.tjm-norm-loss`; `fact.pauli-unitary-hazard`; `fact.ctjm-error-classes`; `gap.accumulated-projection-effect` |
| Lubasch et al. | `docs/papers/reading_notes/lubasch_finite_peps_1405.3259_source_review.md` | `lubasch-finite-open-peps`; `lubasch-environment-positivity`; `lubasch-peps-gauge-limit`; `lubasch-conditioning-caution` |
| Evenbly | `docs/papers/reading_notes/evenbly_closed_loop_truncation_1801.05390_source_review.md` | `evenbly-bond-environment`; `evenbly-wtg-definition`; `evenbly-fet-objective`; `evenbly-cut-cycle-limit` |
| Mc Keever and Szymańska | `docs/papers/reading_notes/mc_keever_stable_ipepo_fet_wtg_2012.12233.md` | `fact.pepo-not-inherently-positive`; `fact.alternative-mixed-state-fidelity`; `fact.local-trace-distance-benchmark`; `gap.sequential-measurement-law` |
| Kilda et al. | `docs/papers/reading_notes/kilda_ipepo_stability_2012.03095.md` | `fact.stationarity-diagnostic`; `fact.protocol-robust-nonconvergence`; `fact.nonmonotone-bond-stability`; `gap.outcome-distribution-accuracy` |
| Rudolph and Tindall | `docs/papers/reading_notes/rudolph_tindall_gpu_peps_2507.11424.md` | `fact.terminal-sampling-law`; `fact.probability-ratio`; `fact.sample-kld`; `fact.local-global-mismatch`; `gap.adaptive-outcome-sequences` |
| Werner et al. | `docs/papers/reading_notes/werner_positive_tensor_network_open_systems_1412.5746.md` | `werner-local-purification`; `werner-purification-bound`; `werner-discarded-weight`; `werner-compression-error`; `werner-trace-norm-certificate`; `werner-gap-historical-record-law` |

Sixteen additional notes passed the same full-text and artifact gate but remain
`reviewed-but-excluded`: Acuaviva; Dziarmaga GTU; Dziarmaga NTU; Kshetrimayum--Weimer--Orús;
Liao; Naumann/variPEPS; O'Rourke--Chan; Patra; Rams/YASTN; Sander (2026); Schieffer; Shao et al.;
Sokolov--Dziarmaga; tePEPO; Vanhecke; and Zheng--Yang. They supply redundant truncation variants,
fixed-terminal/static-operator benchmarks, software/performance facts, or restricted complexity
existence results, but no additional carrier-to-`Record` bridge. Exact dispositions remain in
`READING_NOTES_PROJECT_FIT_INVENTORY_2026-07-17.md` and each note's separate project-fit audit.

## Evidence matrix

| Question | Primary source evidence | Closed source-level conclusion | Boundary that remains open |
|---|---|---|---|
| What does an OBC MPS cut expose? | Paeckel et al., Sec. 2.6, Eqs. (15)–(18), PDF pp. 8–9 | In mixed canonical form, the truncated SVD is locally optimal at one cut and the discarded singular-value squares give the local Hilbert-space approximation error. | Successive local optima are not automatically a global trajectory or `Record` bound. |
| Which MPS evolution errors are distinct? | Paeckel et al., Sec. 4.1.1, PDF pp. 18–19; Sec. 6.2.2, PDF pp. 49–50 | Time-step, projection, truncation, and local-solver errors are separate and respond differently to control parameters. | One threshold cannot stand in for all four errors or for downstream measurement statistics. |
| Where does MCWF branch probability live? | Jaschke et al., Sec. III.B, PDF pp. 10–12; Sander et al. (2025), Eqs. (42)–(45), PDF p. 8 | Non-Hermitian norm loss is physical jump/no-jump mass; channel weights are normalized only after total jump mass is fixed. | Renormalized conditional-state agreement cannot recover mass discarded before normalization. |
| What does the TJM convergence theorem cover? | Sander et al. (2025), Theorem 2, PDF p. 10 | The stated density-estimator convergence assumes MPS trajectories of full bond dimension and concerns a fixed-time density estimate. | The theorem does not authenticate finite-bond sequential records. |
| What finite-bond error does TJM name? | Sander et al. (2025), Sec. IV.C, Eqs. (57)–(58), PDF pp. 10–11 | Finite bond dimension introduces TDVP projection error in addition to splitting, time-step, and sampling error. | The paper supplies no conversion from the residual to joint-record total variation or LER. |
| Can branch mass be trivial for special jump families? | Fröhlich et al. (2026), Eqs. (8)–(13), PDF pp. 3–4 | For sparse Pauli-Lindblad unitary jumps, hazards are state-independent and the dissipative contraction is a global scalar before renormalization. | This is a special Pauli-unitary structure, not a license to cap generic Kraus, no-jump, leakage, or reset operators. |
| Does the tensor-jump source close accumulated projection error? | Fröhlich et al. (2026), Sec. III.B, Eq. (16), PDF p. 5 | The source separates finite-manifold projection error and does not supply a general estimator for its accumulated observable impact outside named special cases. | This is a source-local absence, not a field-wide no-go theorem; discarded weight or bond dimension still needs an independent bridge. |
| What is the finite-PEPS approximation structure? | Lubasch, Cirac, and Bañuls, Secs. II–III, PDF pp. 2–7 | Finite OBC PEPS uses approximate environments; the exact norm environment is PSD, approximate contraction can lose positivity, and no generic MPS-like canonical identity gauge exists. | Hermitianization, eigenvalue clipping, gauge conditioning, or ALS convergence does not prove the true environment or output law. |
| What changes on a closed loop? | Evenbly, Secs. II–V, Eq. (12), PDF pp. 2–6 | Closed-loop bond spectra are gauge/environment dependent; FET optimizes a normalized whole-network overlap using a bond environment. | Normalized overlap is scale-insensitive and does not by itself preserve unnormalized branch probability. |
| What does mixed-state iPEPO FET optimize? | Mc Keever and Szymańska, Sec. II.D, Eq. (9), PDF p. 5; Sec. III.B, Figs. 4–5, PDF p. 8 | FET optimizes a normalized Hilbert–Schmidt overlap, not Uhlmann fidelity; the reported trace-distance comparison is for nearest-neighbor reduced density matrices in a specific benchmark. | Neither the normalized objective nor a local reduced-state benchmark controls unnormalized branch mass or the historical `Record`. The compressed PEPO is not positive by construction. |
| Is increasing PEPO bond dimension a monotone accuracy test? | Kilda et al., Sec. 2.2, Fig. 6, PDF pp. 6–8 | Increasing `D` can destroy a previously stationary simple-update iPEPO history; bond-spectrum stationarity can therefore be spurious rather than a monotone convergence sequence. | A stationary spectrum, smaller timestep, or larger `D` is not a state, branch-law, or `Record` certificate. |
| Is there any discarded-weight-to-state bridge in the literature? | Werner et al., Appendix A, Lemma 1, PDF p. 6; Appendix D, Definition 5, Lemma 6, Theorem 7, PDF pp. 10–12 | For a finite one-dimensional locally purified TN under the theorem's local-Liouvillian and canonical-compression assumptions, purification error and per-compression discarded weight compose into a final density-operator trace-norm bound while positivity is structural. | The theorem does not cover an ordinary pure-state trajectory MPS, two-dimensional PEPO/PEPS contraction, selective branch mass, or a historical multi-round classical register. |
| Can terminal PEPS samples be convergence-tested? | Rudolph and Tindall (2025), Sec. II.C, Eqs. (5)–(6) | Boundary-MPS sampling exposes `p(x)/q(x)` and sample KLD diagnostics for terminal samples from a pure-state planar tensor network. | The paper does not cover noisy mixed-state PEPO, mid-circuit reset, or the complete multi-round instrument record. |

Every load-bearing row above has a source-only note, a verified source artifact, and a separate hashed
project-fit audit. The strict reviews that are not required by this minimum matrix remain
`reviewed-but-excluded`: being fully read does not itself make a source part of the current corpus.

## Operation reconstruction

The load-bearing probability/truncation sequence is reconstructed as follows.

1. Begin with an unnormalized branch state. Its squared norm is branch probability mass, not a numerical
   nuisance.
2. Apply an allowed physical operation without an MPS cap wherever its norm determines branch selection.
3. Record pre-normalization mass and the complete support/configuration identity.
4. Normalize only after branch selection.
5. If an allowed unitary MPS split is capped, ledger each actual split and its local discarded weight; do
   not reinterpret the sum as a proved global state or record error.
6. Populate outcomes into a schedule-derived immutable `Record` layout. Tensor-network libraries do not
   define detector boundaries, XOR folding, reset semantics, or observable columns for this project.
7. Compare the emitted joint record law against an independent exact oracle in the declared finite
   regime. Only this last comparison can promote a record-level claim.

For PEPS, two approximation layers must be kept distinct: state-bond truncation after an update and
environment contraction used to evaluate an objective or Born probability. Increasing the state bond
dimension does not remove environment error, and increasing the environment bond dimension does not
prove that a rank-reducing state update occurred.

## Disconfirmation-search status

The project-side discovery pass targeted papers that could overturn the open-gap verdict:

- stochastic MPS simulations of sequential/local measurements;
- finite-bond quantum-trajectory convergence and monitored-MPS projection error;
- PEPS terminal-sampling convergence and direct probability diagnostics;
- randomized Schmidt-rank truncation in trace distance;
- quantum-instrument and sequential-measurement bounds.

The strongest source-verified near-matches narrow the gap but do not close the project-specific bridge:

- stochastic-MPS measurement papers demonstrate how to simulate measurement trajectories, not a
  finite-bond error theorem for the resulting joint law;
- terminal PEPS samplers expose probability-ratio or KLD diagnostics, but not mid-circuit
  measurement/reset records;
- Werner et al. demonstrate that canonical discarded weights can be composed into a final-state
  trace-norm certificate for a finite 1D locally purified carrier. This disproves the overly broad claim
  that tensor-network truncation metrics can never bridge to state accuracy, but its assumptions do not
  include the present pure-state trajectory MPS, 2D PEPO/PEPS, selective branch mass, or a persistent
  historical register;
- trace-distance contractivity therefore supplies a credible route through an explicit
  classical-quantum instrument, but the current restricted-carrier ledger still must separately account
  for branch mass, conditional states, adaptive composition, and the packed historical register;
- randomized low-rank mixtures concern state approximation and do not directly certify this simulator's
  deterministic per-split truncation path.

Accordingly, the open gap is not “measurement statistics can never be bounded.” It is the narrower and
actionable absence of a validated bridge from the exact numerical quantities emitted by the current
restricted carriers, through the complete adaptive classical-quantum instrument, to their declared
historical `Record` law.

This packet does not contain an exact, reproducible external-search ledger with dated queries, routing
domains, candidate lists, version/retraction checks, and per-candidate rejection reasons. It therefore
does not claim search exhaustion or a `confirmed-literature-gap`; discovery must continue before the gap
can be closed or formally confirmed absent.

## Open gap ledger

| Gap ID | Required bridge | Evidence checked | Status | Consequence |
|---|---|---|---|---|
| `gap.mps-local-to-record` | Current restricted-carrier split/mass/path ledger through a stepwise classical-quantum instrument telescope to joint multi-round `Record` distance | Paeckel; Jaschke; Sander 2025; Fröhlich 2026; Werner 2015 | `ours-inference-only` | The proposed telescope is a project inference, not yet a source-closed derivation; exact record comparison remains mandatory. |
| `gap.finite-bond-mcwf-law` | Finite-bond MCWF/QT propagation to the full stochastic trajectory law | Jaschke; Sander 2025; Fröhlich 2026 | `missing` | Full-bond/fixed-time convergence cannot be inherited by capped routes. |
| `gap.branch-mass-composition` | Accumulated raw-mass error plus conditional-state error through adaptive instruments | MCWF norm rules; candidate instrument route not yet source-closed | `missing` | Kraus/no-jump/jump operations remain uncapped in the restricted route. |
| `gap.peps-fet-to-record` | Approximate-environment FET objective to true branch mass and complete QEC record | Lubasch; Evenbly; Mc Keever; Kilda; Rudolph–Tindall | `missing` | PEPS FET non-degeneracy and independent record gates remain mandatory. |
| `gap.lptn-final-state-to-history` | Werner's final-state 1D trace-norm certificate to a selective trajectory with an explicit persistent classical history register | Werner 2015; candidate adaptive-instrument route not yet source-closed | `missing` | The theorem is a valid bounded precedent, not a certificate for the current carrier or an already-discarded history. |
| `gap.terminal-to-multiround` | Terminal pure-state sample convergence to noisy mixed-state measurement/reset histories | Rudolph–Tindall; candidate sequential-instrument route not yet source-closed | `missing` | `E_q[p/q]` is a norm identity, not a worst-event or TV bound; terminal `p/q` or KLD cannot replace multi-round validation. |

## Allowed and prohibited transfers

Allowed now:

- cite canonical OBC MPS SVD semantics for one actual split;
- use raw norm as physical branch mass in MCWF/QT bookkeeping;
- separate splitting, projection, truncation, sampling, and solver errors;
- use finite-bond/bond-threshold sweeps as diagnostics;
- use PEPS gauge, positivity, environment, and FET checks for their declared local targets;

Prohibited without a new bridge and independent validation:

- summing local discarded weights and calling the result a state, `Record`, TV, or LER theorem;
- renormalizing away raw mass loss and certifying only the conditional state;
- applying a bond cap to a physical branch operator whose norm chooses the branch;
- inheriting the Sander full-bond theorem for finite-bond production claims;
- treating a PEPS environment tolerance, FET fidelity, entropy equality, or all-noop fallback as a
  complete-record certificate;
- using lower bond dimension, lower variance, or faster runtime as evidence of scientific correctness.

## Next closure step

The next admissible step is to finish the literature closure, not to preregister or implement a favorable
project derivation. Record exact dated external queries, routing domains, candidate sources, source
versions/retraction checks, and per-candidate rejection reasons for the six rows above. Only a closed
evidence packet, or a properly established `confirmed-literature-gap`, may then hand a downgraded
project-side proposal to preregistration.

The leading project inference to test after that gate is a classical-quantum instrument telescope that
separately bounds:

1. raw branch-mass error at every selective operation;
2. conditional post-operation trace distance after every accepted MPS/PEPS approximation;
3. accumulation under the exact schedule-derived adaptive instrument;
4. the induced total-variation distance of the packed joint `Record`;
5. decoder/LER sensitivity to that record distance in the declared finite regime.

Until the literature packet closes and that bridge is then proved and independently falsified, the
repository's exact record comparison remains the scientific gate and the tensor-network metrics remain
diagnostics.
