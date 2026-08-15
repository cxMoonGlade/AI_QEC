# PEPS XZZX measurement/reset/Record bridge — literature closure

Date: 2026-07-26
Status: **closed for the bounded all-qubit experiment; not closed for leakage or a d5 full-Record guarantee**

## Frozen question

Can a maintained finite-PEPS implementation replay a fixed two-round XZZX
syndrome-extraction circuit with explicit ancillas, selective measurement,
reset, a coherent non-Pauli data rotation, and the fixture's absolute
detector/observable XOR rows?

The experiment is deliberately split into three evidentiary levels:

1. a small exactly enumerable tracer owns the complete joint `Record`
   distribution;
2. d3/r2 owns stepwise Born mass, normalized conditional-state fidelity,
   reset state, and the realized `Record` for selected trajectories;
3. d5/r2 is attempted only after those gates pass and owns at most the same
   conditioned-trajectory claim.

No result from this packet may be described as a retained-leakage,
Kraus-channel, decoded-LER, d5 full-law, d7, or scalable exact-PEPS result.

## Question charter

- **Decision and consequence:** a passing exact-law tracer and useful d3
  branch permits one gated d5 conditioned-trajectory attempt. No result
  promotes the adapter into `src/**` or production.
- **Importance x attackability:** explicit measurement/reset is the missing
  bridge between the existing coherent d5 PEPS benchmark and the project's
  multi-time output object. Seven-qubit enumeration and a 17-qubit dense oracle
  make the bridge independently falsifiable before the 49-qubit attempt.
- **Reusable artifact/test:** a canonical d2 tracer, parameterized d3/d5
  fixtures, a selective reset instrument, absolute-row fold tests, dense and
  Aer references, and complete-vector/proxy-firewall tests.
- **Kill condition:** stop before d5 if the literature boundary is widened,
  a fixture hash is not reproducible, a required corruption is inert, the
  tracer full law fails, dense and Aer disagree on d3, d3 misses its frozen
  usefulness band, or the only available d5 score is an approximate overlap
  proxy.

## Frozen scientific object

`decision/consequence`

: Decide whether the explicit-ancilla PEPS route is sufficiently faithful to
  justify further two-dimensional trajectory work. A passing d3 result permits
  the gated d5 conditioned-trajectory run. It does not promote the adapter into
  the simulator product or certify an unenumerated joint law.

`mechanism`

: Execute the proposed hash-frozen ordered operations and measurement keys of
  a locally Hadamard-conjugated Stim rotated-memory fixture whose parent d7
  transformation is already corruption-tested.
  Every syndrome ancilla is explicitly present. An `MR` outcome `b` is the
  selective reset instrument
  `A_b = I_rest tensor |0><b|`; terminal `M` and `MX` are projective
  measurements without reset. After each complete syndrome round, every data
  qubit receives `RY(0.02)`.

`observable`

: For the enumerated tracer, total-variation distance between the raw
  measurement-trajectory law and, separately, the folded complete
  detector/observable `Record` law. For selected d3/d5
  branches, every conditional Born probability, cumulative branch mass,
  post-reset ancilla state, exact absolute XOR fold, and normalized global
  conditioned-state fidelity when that fidelity can be evaluated without an
  unregistered contraction proxy.

`mechanism-to-observable bridge`

: The selective-instrument rule preserves both outcome probability and the
  normalized surviving branch. The fixture then maps the ordered raw outcomes
  to detectors and the logical observable by immutable absolute XOR rows.
  Consequently, exact agreement at every selective step plus an exact final
  state comparison checks one branch; enumeration over every branch checks the
  complete law. One branch is never substituted for the latter.

`predicted direction/scale`

: Increasing PEPS state bond and the independently controlled environment
  radius is expected, but not guaranteed, to improve d3 conditioned-state and
  branch-mass agreement. `F >= 0.99` is a project usefulness decision band,
  not a theorem or field threshold. No finite d5 bond is presumed sufficient.

`alternative formulations/invariants`

: Dense NumPy and Aer-MPS replays must agree on the d3 branch; the exact
  measurement operator must reproduce the Born rule and leave a measured-and-
  reset ancilla in `|0>`; raw bits must fold through the hash-frozen absolute
  rows without mutation; the same fixture and forced branch must be used by
  reference and candidate.

`possible no-go`

: Exact PEPS scalar evaluation is complete for the counting-complexity class
  in the general setting of Schuch,
  Wolf, Verstraete, and Cirac. Rudolph and Tindall additionally exhibit
  finite-dimensional tensor-network states for which perfect sequential
  terminal sampling needs exponentially large boundary MPS. These results
  forbid extrapolating a successful fixed point into a general efficient
  exact solver unless the corresponding standard complexity classes collapse;
  they do not forbid the bounded experiment.

`implementation target`

: A repository-owned adapter around the pristine Quimb clone, with an
  independently constructed Aer-MPS reference and a dense d3 reference.
  External clones remain unmodified.

## Source closure ledger

Every row was first queried against the artifact-verified local RAG/KG. The
external query column records the corresponding AnySearch disconfirmation
query; it is not a citation substitute.

| required object / load-bearing row | local evidence queried | AnySearch query | exact source / project object | status and retained boundary |
|---|---|---|---|---|
| XZZX check geometry | RAG: `XZZX bulk face local Hadamard geometry`; KG: `XZZX` | `XZZX surface code syndrome extraction ancilla measurement reset circuit detector events` | Bonilla Ataides et al., arXiv:2009.07851v3, Fig. 1, PDF p. 2; Darmawan et al., arXiv:2104.09539v2, Sec. II and Fig. 2(a), PDF p. 3 | **closed:** a bulk face has an `XZZX` check up to the stated spatial convention and local-H equivalence. Neither paper gives the complete rotated d3/d5 schedule. |
| ordered ancilla shell | RAG: `XZZX ordered ancilla circuit` | `XZZX syndrome extraction circuit ancilla reset consecutive measurement outcomes defect` | Darmawan et al., Fig. 2(b) and adjacent text, PDF p. 3 | **closed:** plus-state ancilla, ordered `CZ(A,D1), CX(A->D2), CX(A->D3), CZ(A,D4)`, then X readout. The full fixture schedule is not attributed to this figure. |
| repeated-round defect | RAG: `XZZX consecutive defect preceding outcome`; KG: `XZZX` | `surface code detector event difference consecutive stabilizer measurement outcomes` | Bonilla Ataides et al., Fig. 5, PDF p. 6; Darmawan et al., Sec. II.B, PDF p. 3 | **closed:** differing consecutive signs define a defect. First-round anchor and terminal closure remain project definitions. |
| selective probability and state | RAG: `selective measurement outcome probability normalized conditional state` | `PEPS mid circuit measurement reset quantum trajectory Born probability conditional state` | Czajkowski and Grilo, arXiv:2101.08313v2, Sec. 2.2, Eq. (1), PDF p. 5 | **closed:** `p_b=Tr(Q_b rho)` and `rho_b=A_b rho A_b^dagger/p_b`. The source does not choose the reset map or QEC schedule. |
| ordered measurement law | RAG: `ordered sequential measurement joint outcome law` | `tensor network PEPS mid-circuit measurement reset conditional quantum trajectory` | Czajkowski and Grilo, Sec. 3.1, Eq. (9), PDF p. 7 | **closed:** sequential mass depends on ordered selective operations. This is not a PEPS accuracy theorem. |
| fixed ancilla reset | RAG: `ancilla reset zero every repeated measurement cycle` | `surface code detector consecutive syndrome measurements ancilla reset temporal difference` | Ghosh et al., arXiv:1306.0925v2, Sec. I, Fig. 1 and caption, PDF p. 2 | **closed for the component:** each cycle resets the ancilla to `|0>`. Only this component transfers from the source's one-data/one-ancilla qutrit model. |
| PEPS update diagnostic | RAG: `PEPS retained gate weight final fidelity local diagnostic` | `PEPS quantum trajectories repeated syndrome measurement reset detector record` | Rudolph and Tindall, arXiv:2507.11424v2, Sec. II, Eqs. (1)-(2), PDF p. 3 | **closed:** retained weights are diagnostics, not global fidelity or historical-Record certificates. |
| terminal sampling limit | RAG: `PEPS terminal sampling probability ratio pathological boundary MPS` | `PEPS mid circuit measurement reset quantum trajectory Born probability conditional state` | Rudolph and Tindall, Sec. II, unnumbered “Sampling from Tensor Network States” subsection, Eqs. (5)-(6), PDF p. 4; pathological-cost construction, PDF p. 9 | **closed as a limitation:** terminal ratio/KL diagnostics exist and some perfect sampling needs exponential boundary dimension. Intermediate reset and a complete adaptive `Record` are absent. |
| usefulness magnitude | RAG: `PEPS global fidelity threshold bond dimension`; current metric ledger | `projected entangled pair states quantum error correction repeated syndrome measurement` | No universal source threshold is imported; Evenbly supplies the normalized overlap definition, Sec. V, Eq. (12), PDF p. 6 | **closed by epistemic classification:** `0.99/0.95` are preregistered class-(c) project bands, not physical thresholds. |
| exact-complexity boundary | RAG: `PEPS contraction #P complete`; KG: `general tensor-network contraction` | `PEPS quantum trajectories repeated syndrome measurement reset detector record` | Schuch et al., *Phys. Rev. Lett.* 98, 140506, VOR PDF pp. 2-3 | **closed:** general exact scalar primitives are complete for the paper's counting-complexity setting. It does not prove this fixed fixture must fail. |
| exact schedule and classical fold | repository scan of the d7 emitter, capability packet, and corruption tests; independent in-memory d2/d3/d5 recomputation | not a literature row; external search confirmed that the papers do not publish these exact tables | existing d7 fixture plus proposed d2/d3/d5 fixture definitions and independently recomputed hashes | **closed as a project input definition, not as implemented evidence:** d2/d3/d5 coordinates, operations, reset flags, and absolute rows are frozen in preregistration. Their emitter and corruption tests do not yet exist and are mandatory before any target run. |
| implementation surface | local pristine-clone/API audit; `PEPS_PEPO_LITERATURE_LIBRARY_LANDSCAPE_2026-07-26.md` | `tensor network PEPS mid-circuit measurement reset conditional quantum trajectory` | Quimb `CircuitPEPSSimpleUpdate`, arbitrary-graph state and public tensor update/RDM surfaces at the pinned clone | **closed for implementation selection only:** API availability is engineering evidence, never scientific ground truth. |

### Reading-note and fact bindings

| source role | current note | load-bearing fact IDs |
|---|---|---|
| XZZX geometry, local frame, defect, and source-local absences | `docs/papers/reading_notes/bonilla_ataides_xzzx_2009.07851_source_review.md` | `bonilla-xzzx-bulk-check`; `bonilla-xzzx-local-equivalence`; `bonilla-xzzx-consecutive-defect`; `bonilla-xzzx-gap-complete-schedule`; `bonilla-xzzx-gap-reset`; `bonilla-xzzx-gap-full-record` |
| ordered XZZX shell, defect, conditional re-preparation, and leakage omission | `docs/papers/reading_notes/darmawan_xzzx_circuit_2104.09539_source_review.md` | `darmawan-xzzx-check-circuit`; `darmawan-xzzx-defect`; `darmawan-xzzx-repreparation`; `darmawan-xzzx-leakage-omission`; `darmawan-xzzx-gap-complete-rotated-schedule`; `darmawan-xzzx-gap-full-record` |
| selective update and ordered law | `docs/papers/reading_notes/czajkowski_grilo_sequential_measurements_2101.08313_source_review.md` | `czajkowski-selective-update`; `czajkowski-ordered-law`; `czajkowski-gap-reset-dynamics` |
| reset-to-zero component and single-check limitation | `docs/papers/reading_notes/ghosh_leakage_paralysis_1306.0925v2.md` | `ghosh.circuit`; `ghosh.gap-surface-record` |
| PEPS diagnostics, terminal sampling, and adaptive gap | `docs/papers/reading_notes/rudolph_tindall_gpu_peps_2507.11424.md` | `fact.gate-truncation`; `fact.final-state-fidelity`; `fact.terminal-sampling-law`; `fact.pathological-sampling-cost`; `gap.adaptive-outcome-sequences`; `gap.total-variation-logical-event` |
| normalized whole-network overlap | `docs/papers/reading_notes/evenbly_closed_loop_truncation_1801.05390_source_review.md` | `evenbly-fet-objective`; `evenbly-gap-record-bridge` |
| exact-complexity boundary | `docs/papers/reading_notes/schuch_peps_complexity_prl_98_140506_source_review.md` | `schuch-peps-primitives`; `schuch-peps-completeness`; `schuch-general-tn-completeness`; `schuch-gap-pepo-qec-record` |

The two new XZZX source reviews are bound to the pinned artifacts:

- `2009.07851v3`, SHA-256
  `4b4f244f949b0d1e862ff44e6328f33abab93654cd64a7e5f1ada0467ccaafd7`;
- `2104.09539v2`, SHA-256
  `809149344e94392151a3935a4ec9615930e19d7aee414a9d022a7ac07036e5e5`.

Their independent source-only audit is
`XZZX_MEASUREMENT_RECORD_SOURCE_AUDIT_2026-07-26.md`.

### Source version and correction-status check

The experiment binds the artifact hashes above, not a floating publisher
page. On 2026-07-26, AnySearch academic exact-title searches and separate
publisher-domain correction/erratum/retraction searches recorded:

| source | bound artifact | published counterpart/status | dated disposition |
|---|---|---|---|
| Bonilla Ataides et al. | arXiv:2009.07851v3 | *Nature Communications* 12, 2172 (2021), DOI `10.1038/s41467-021-22274-1` | publisher search returned the article and no separate correction/retraction result; the VOR was identified but not substituted for the hashed v3 artifact |
| Darmawan et al. | arXiv:2104.09539v2 | *PRX Quantum* 2, 030345 (2021), DOI `10.1103/PRXQuantum.2.030345` | publisher search returned the article listing and no separate erratum/correction result; v2 remains the bound artifact |
| Ghosh et al. | arXiv:1306.0925v2 | *Physical Review A* 88, 062329 (2013), DOI `10.1103/PhysRevA.88.062329` | publisher search returned the article listing and no separate erratum/correction result; the note preserves the source's printed-date anomaly |
| Czajkowski and Grilo | arXiv:2101.08313v2 | no published counterpart was used or found by the exact-title academic query | preprint v2 only |
| Rudolph and Tindall | arXiv:2507.11424v2 | no VOR is used | preprint v2 only |
| Evenbly | arXiv:1801.05390v2 | *Physical Review B* 98, 085155 (2018), DOI `10.1103/PhysRevB.98.085155` | published counterpart identified in the source-reviewed note; v2 artifact remains bound |
| Schuch et al. | version of record | *Physical Review Letters* 98, 140506 (2007), DOI `10.1103/PhysRevLett.98.140506` | VOR itself is bound; publisher search returned no separate erratum/correction result |

The absence of a returned notice is a dated search result, not a guarantee that
no future or unindexed correction exists.

## Quimb implementation-path audit

The implementation target is pinned to pristine Quimb commit
`3c89529fe0a3487133a3928201691161e110abdf`, tree
`d81d043a27b7abf20e6c3a423f9b772682bbef40`.

- `external/baselines/quimb/quimb/tensor/circuit/peps.py`, class
  `CircuitPEPSSimpleUpdate`, defines a one-tensor-per-site arbitrary-graph
  PEPS and permits dense one- and two-site gates only on declared edges.
- `external/baselines/quimb/quimb/tensor/circuit/simple_update.py`,
  `CircuitSimpleUpdate.partial_trace` and `sample`, explicitly raise
  `NotImplementedError`; neither may be called or represented as supported.
- The audited path is
  `get_state(absorb_gauges="return")`, followed by
  `TensorNetworkGenVector.partial_trace_cluster` from
  `external/baselines/quimb/quimb/tensor/tnag/core.py` for the one-site RDM,
  then a public local rank-one reset gate on the copied network and
  reconstruction of `CircuitPEPSSimpleUpdate` for continued evolution.
- `partial_trace_cluster(max_distance=r)` contracts the selected local cluster
  exactly but approximates the global RDM whenever the cluster is not the
  complete graph. The radius is therefore a separate mass-diagnostic control,
  not a fidelity or full-law guarantee.

This custom composition was exercised only by a tiny API probe before the
freeze. Its repository-owned implementation, exact small-state comparison,
and corruption tests remain mandatory preregistered work.

## Exact operation reconstruction

For one measured ancilla in computational basis, define

```text
A_0 = I_rest tensor |0><0|
A_1 = I_rest tensor |0><1|
Q_b = A_b^dagger A_b = I_rest tensor |b><b|.
```

For premeasurement density operator `rho`,

```text
p_b   = Tr(Q_b rho)
rho_b = A_b rho A_b^dagger / p_b.
```

Thus the same selective operation both records `b` and resets the measured
ancilla to `|0>`. For a possibly unnormalized pure state, compute and separate

```text
tilde_psi_b = A_b psi
p_b = ||tilde_psi_b||^2 / ||psi||^2
psi_b = tilde_psi_b / ||tilde_psi_b||.
```

Accumulate path mass as `P_path <- P_path * p_b`; do not infer it from the
renormalized `psi_b`. For X-basis measurement, the fixture's explicit `H` or
`MX` convention is applied before the computational projector. Reset is
performed only where `measurement_order[*].reset` is true.

For an ordered raw outcome string `m=(m_0,...,m_{M-1})`, branch mass is

```text
P(m) = product_k p(m_k | m_0,...,m_{k-1}).
```

The fixture's classical map is then exact:

```text
detector_j   = XOR(m_k for k in detector_rows[j])
observable_l = XOR(m_k for k in observable_rows[l]).
```

The rows are absolute measurement-column indices. In particular, their
variable arities preserve first-round anchors and terminal data closure; they
must not be replaced by a rectangular consecutive-XOR shortcut.

## Anomaly and disconfirmation ledger

| contrary fact or ambiguity | consequence |
|---|---|
| Darmawan's hardware sequence conditionally re-prepares `|+>` or `|->` after readout, rather than erasing the branch to one fixed X eigenstate (Fig. 6, PDF p. 7). | Fixed reset is grounded separately by Ghosh and is represented as reset to `|0>` followed by the fixture's explicit preparation gates. No fixed-`|+>` claim is attributed to Darmawan. |
| Darmawan suppresses and then omits residual Kerr-cat leakage from its later code simulations (PDF p. 10), and its small exact code calculation is two-level (PDF p. 13). | The proposed run is all-qubit. It cannot answer the original retained-leakage question. |
| Bonilla's repeated-measurement numerics use a phenomenological outcome-flip model (PDF p. 6). | Its threshold numbers are not imported into this gate-level experiment. |
| Neither XZZX paper specifies the fixture's complete schedule, first detector anchor, or terminal XOR closure. | Those are independently hash-recomputed preregistration inputs. Separate d3/d5 emitter and corruption tests are still required. |
| Rudolph/Tindall's sampler is terminal, while this experiment contains intermediate selective operations. | Its terminal law is not used as the missing bridge. Stepwise Born probabilities and exact small-law enumeration are required instead. |
| PEPS state-bond truncation and environment contraction are distinct approximations. | Both controls are reported separately; neither local diagnostic can become the headline fidelity or Record distance. |
| A high conditioned-state fidelity can coexist with wrong branch mass. | Conditional fidelity and raw cumulative mass are separate mandatory outputs. |
| One sampled d5 branch can look perfect while other branches are wrong. | d5 is explicitly not a complete-law result. It yields one realized detector/observable row, not Record faithfulness. Only the tracer can own full-law TV. |
| The current registered PEPS fidelity owner accepts complete complex128 vectors only. | It applies directly to d3. For d5 it applies only if structural reset is proved and exact contraction materializes every amplitude of both 25-data vectors; otherwise fidelity is `UNAVAILABLE`. A direct scalar TN overlap would require a new owner and independent proxy-firewall tests. |

## AnySearch acquisition and disconfirmation log

Search backend: AnySearch, 2026-07-26 UTC. Routing was discovered first with
`get_sub_domains --domain academic`; the selected vertical was
`academic.search`, with `category=Physics` and relevance ordering for the
adversarial batch. Search results and snippets were used only for discovery;
every load-bearing claim above comes from a pinned full text and exact locator.

| exact query | exact candidate identifier(s) | publication/version check and disposition |
|---|---|---|
| `XZZX surface code syndrome extraction ancilla measurement reset circuit detector events` | arXiv:2104.09539v2; arXiv:2009.07851v3 | pinned and independently reviewed. Published counterparts are DOI `10.1103/PRXQuantum.2.030345` and DOI `10.1038/s41467-021-22274-1`; only the limited circuit/geometry/defect rows are admitted. |
| `tensor network PEPS mid-circuit measurement reset conditional quantum trajectory` | arXiv:2606.00433, *Learning Mid-Circuit Measurement Backaction on a Quantum Processor* | discovery only. It concerns learned MCM backaction, not a finite-bond PEPS theorem or the fixture's complete detector/observable law. |
| `surface code detector consecutive syndrome measurements ancilla reset temporal difference` | arXiv:2009.07851v3; arXiv:2104.09539v2; arXiv:1306.0925v2 | admitted sources close consecutive-defect and fixed-reset components separately; none publishes the fixture's first/last absolute rows. |
| `projected entangled pair states quantum error correction repeated syndrome measurement` | no exact candidate that combines all required objects | no abstract/snippet was promoted; exact instrument validation remains required. |
| `XZZX syndrome extraction circuit ancilla reset consecutive measurement outcomes defect` | arXiv:2104.09539v2; arXiv:2009.07851v3 | no complete rotated d3/d5 schedule found in either full text; schedule stays a project object. |
| `PEPS mid circuit measurement reset quantum trajectory Born probability conditional state` | arXiv:2507.11424v2 and adjacent monitored-circuit results | the pinned PEPS source covers terminal sampling only; no candidate displaced the selective-instrument plus exact-test bridge. |
| `surface code detector event difference consecutive stabilizer measurement outcomes` | arXiv:2009.07851v3; arXiv:2104.09539v2 | admitted for consecutive semantics only, not first-round anchor or terminal closure. |
| `PEPS quantum trajectories repeated syndrome measurement reset detector record` | no exact theorem candidate | no source-verified finite-bond full-Record theorem was imported. |
| `finite bond PEPS mid-circuit measurement reset full joint trajectory law no-go failure limitation` | arXiv:2607.00365, broad AI/quantum-information review | adversarial search returned only an off-target review; rejected because it supplies no equation-level PEPS instrument or Record bound. |
| `PEPS quantum error correction repeated syndrome measurement reset detector record null result` | arXiv:2607.00365 | same off-target result; no null theorem inferred from poor search recall. |
| `tensor network simple update conditional measurement branch probability failure counterexample` | DOI `10.1088/1361-6633/aab406` plus off-topic results | rejected as an ML/quantum-domain review unrelated to simple-update branch-mass correctness; this negative query produced no usable counterexample source. |
| `projected entangled pair state exact overlap MPS contraction limitation complexity` | DOI `10.1103/RevModPhys.93.045003`; DOI `10.1088/1367-2630/16/3/033014` | relevant adjacent reviews of PEPS concepts and approximate contraction, but not mid-circuit reset or a historical QEC Record. Current Evenbly/Rudolph/Schuch rows already close the required metric and limitations. |

This packet does **not** claim an exhaustive confirmed literature gap. It does
not need such a no-go: absence of a general theorem is handled by narrowing the
claim and requiring independent exact checks.

## Closure verdict

- `closure_status: closed`
- `closed_scope: bounded_all_qubit_two_round_instrument_experiment`
- `full_record_scope: small_enumerable_tracer_only`
- `d3_scope: selected_branch_mass_state_reset_and_record`
- `d5_scope: gated_selected_branch_only`
- `leakage_scope: excluded`
- `kraus_noise_scope: excluded`
- `decoded_ler_scope: excluded`
- `scalable_exact_peps_scope: excluded`
- `confirmed_literature_gap: not_claimed`

All mechanism, observable, bridge, limitation, and implementation rows needed
to preregister this bounded experiment are closed. The next allowed action is
to freeze its fixture identities, predictions, independent truth routes,
resource gates, and corruption falsifiers. Experiment code remains forbidden
until that preregistration is committed.
