# GCAPEPS finite-memory native-path repair — literature closure

Date: 2026-07-29

Status: **CLOSED only for an engineering-path correction and a bounded
development-only thread-determinism regression.** This packet does not amend
the frozen formal bond-32 preregistration, authorize a held-out scientific
result, or establish capped-native faithfulness, performance, generic PEPS
faithfulness, efficiency, or gauge-invariant local truncation.

## Frozen claim

`decision / consequence`

: The finite-bond engineering path must stop treating
  `exact_tree_then_native_compress` as a GCAPEPS faithfulness/performance lane.
  The exact-tree construction remains an untruncated construction control.
  The already implemented `native_simple_update` Pauli gadget may be exercised
  only as the candidate implementation for exact-small, frame,
  shadow-isolation, and fresh-process thread-determinism regressions. A capped
  native result is not thereby admitted as a faithfulness or performance
  result.

`importance x attackability`

: Post-result diagnostics indicate that the current identity-compression
  strategy can map machine-precision changes of an internally gauge-equivalent
  PEPS representation to large physical differences after a finite cap. This
  is a programming-path hypothesis, not a held-out scientific observation.
  It is attackable with complete vectors at 6 and 14 qubits, two fresh
  BLAS-thread configurations, the pinned Quimb fork, and the existing
  independent dense route.

`reusable object / test`

: A branching-tree full-basis operator fixture; a nontrivial Clifford-frame
  state-action fixture; and a width-7, four-round, stop-at-operation-100
  fresh-process metamorphic test comparing one and four BLAS threads.

`alternative formulations / invariants`

: (1) exact untruncated tree-PEPO action; (2) local-gate native Pauli gadget;
  and (3) a future full-environment/variational compression. The first two must
  agree without truncation. A capped native result is not required to equal a
  capped tree-identity result. Physical complete vectors, norms, and
  normalized fidelity are invariants; raw tensor bytes, gauges, SVD vectors,
  and generated bond names are not.

`kill condition`

: The engineering repair remains blocked if the uncapped branching or frame
  fixture fails its complete-vector identity, if no-shadow and evidence replay
  change the committed physical state, or if the selected capped native path
  violates the frozen one-versus-four-thread complete-vector bands. Passing
  these conditions establishes only implementation consistency and thread
  determinism; it does not establish capped-state faithfulness or performance.

## Mechanism and exact bridge

The state invariant is

\[
|\psi\rangle=C|\phi\rangle,\qquad
Q=C^\dagger P C=s\bar Q,\qquad s\in\{-1,+1\}.
\]

For a physical Pauli rotation,

\[
C e^{-i\theta Q/2}|\phi\rangle
=e^{-i\theta P/2}C|\phi\rangle .
\]

The existing native compiler uses local basis changes \(B\), a graph-local
parity network \(V\), one signed root rotation, and exact uncomputation:

\[
B\bar Q B^\dagger=\prod_{j\in S} Z_j,\qquad
V^\dagger Z_rV=\prod_{j\in S}Z_j,
\]

\[
B^\dagger V^\dagger R_Z(s\theta)VB
=e^{-i\theta Q/2}.
\]

The compiler borrows a dirty routing vertex only through a forward SWAP,
nearest-neighbor CNOT, and reverse SWAP. It does not assume that the router is
in \(|0\rangle\). This bridge is exact only before finite-bond truncation.
Every two-site simple-update split in the capped lane remains an
approximation.

## Why the old finite-cap bridge is invalid

The exact tree lowerer extends a routed bond gauge as

\[
g'_e=g_e\otimes\mathbf 1_r .
\]

That is an exact representation rule. It is not a certificate that \(g'_e\)
is the Vidal/simple-update environment of the enlarged loopy PEPS. The old
compression path immediately supplied those representation-only gauges to
Quimb `gate_simple_`, whose local SVD weights the selected tensor pair by its
available outer gauges. Consequently the capped map was a function of the
particular PEPS representation, not only of the physical state.

Evenbly establishes the field-level limitation: a gauge transformation
\(A\mapsto AX\), \(B\mapsto X^{-1}B\) can preserve the represented state while
changing internal cyclic correlations. The source defines the full bond
environment in Sec. II Eq. (1), shows in Sec. IV Eqs. (9)--(10) that equal
states can carry different cyclic coefficients, and defines whole-network
fidelity as the full-environment truncation objective in Sec. V Eq. (12).
Appendix B further shows that cut-cycle Schmidt truncation is gauge- and
cut-dependent and need not be optimal. These formula pages were visually
checked in the versioned PDF. The mapping from that limitation to this
specific `g'_e`-to-`gate_simple_` path is **[ours]**: it is a program-level
hypothesis supported by the post-result diagnostic below, not a claim made by
Evenbly and not a held-out result.

## Coverage ledger

Each row names its source kind and version and binds the admitted note or
internal artifact used. `N/A` is explicit where the evidence object is code or
an internal contract rather than an admitted paper note.

| Load-bearing row | Source kind / version | Admitted note or internal artifact path; SHA-256 | Source PDF/artifact path; SHA-256 | Exact locator | Closure and boundary |
|---|---|---|---|---|---|
| Clifford/residual mechanism | Primary journal article plus official supplement; version of record | `docs/papers/reading_notes/masot_llima_stabilizer_tensor_networks_prl_133_230601_source_review.md`; `aeb6682c2235049a28e7175a53d7499cabb8c9191658f41fd981b698e2d145d6` | Article: `docs/papers/PhysRevLett.133.230601_version_of_record.pdf`; `7630570f2d8281ac29a99075082c7e992f8f68aa9d05bd13cf190c473f08946c`. Supplement: `docs/papers/PhysRevLett.133.230601_supplement_version_of_record.pdf`; `5d9dcbd7746b79c38678a72fb42f6b4a529ea4678de2b873b0ee85fbc276b2d1` | Article Main results items (1)--(2), Eqs. (3)--(6), PDF pp. 2--3; supplement Sec. I.B, Lemma 2, Eqs. (7)--(16), PDF pp. 2--3 | Closed for Clifford-basis invariance and the residual Pauli-axis algebra; says nothing about capped PEPS truncation. |
| Native unitary bridge | Internal bounded closure dated 2026-07-29 plus direct finite-dimensional algebra | `docs/simulator_validation/GCAPEPS_NATIVE_FORCED_TRUNCATION_LITERATURE_CLOSURE_2026-07-29.md`; `2485202db91af2ba04ad4e445960eeddec2a19a4b5f513e76ba344b9d9f28442` | N/A; internal packet binds its own primary sources | “Mechanisms”; \(CX^\dagger Z_1CX=Z_0Z_1\); pinned `native.py:1038-1223` | Closed only for the untruncated algebraic target; finite caps remain approximate. |
| Complete-state comparator | Internal metrics contract; working-tree snapshot dated 2026-07-29 | `docs/METRICS.md`; `1a01736d14c20cc7b57a0a003bc6816cd98a87858fd0da559a962355973b83f8` | N/A; internal contract | “Preregistered pending GCAPEPS differential metrics” and “Current bounded GCAPEPS bridge forced-truncation metrics” | Closed only for definitions of raw no-phase-fit symmetric complete-vector error, raw norm, and normalized squared fidelity; no accuracy theorem follows. |
| Loopy truncation limitation | Primary tensor-network methods paper; arXiv:1801.05390v2 / published PRB 98, 085155 | `docs/papers/reading_notes/evenbly_closed_loop_truncation_1801.05390_source_review.md`; `c144aed68d7620b9d444a24e5e081de567b499f8709512ab0c545432c0587bbb` | `docs/papers/1801.05390v2.pdf`; `a5578205d15a7c44a11e0508e400109393c555be243d8478c20f668f75997f40` | Sec. II Eq. (1), PDF p. 2; Sec. IV Eqs. (9)--(10), PDF p. 5; Sec. V Eq. (12), PDF p. 6; Appendix B, PDF p. 10 | [paper] Local cyclic coefficients need not be state invariants. **[ours]** Therefore representation-only gauges cannot authorize this concrete capped faithfulness path. |
| Simple-update scope | Primary methods/application preprint; arXiv:2012.03095v2 | `docs/papers/reading_notes/kilda_ipepo_stability_2012.03095.md`; `49274615199c038fadd45cc441ede16b05dd242060a91e2b1b2bda475b686448` | `outputs/papers/pepo_survey/2012.03095.pdf`; `d750982bd052408459beb0a6b1ce2655dcac236273bbd6e65ec660e79cedd25b` | Appendix A.1.1, numbered steps 1--6 and final two paragraphs, PDF pp. 10--11 | Closed limitation: simple update uses a local SVD and omits the full environment; capped native remains approximate. |
| Local-tail limitation | Primary circuit-simulation preprint; arXiv:2507.11424v2 | `docs/papers/reading_notes/rudolph_tindall_gpu_peps_2507.11424.md`; `dac7a8e2bb8de3ab1bf79f1cc987a8ba820f46df266b143ea3faad2349b773e8` | `outputs/papers/pepo_survey/2507.11424.pdf`; `780b8fad4917a9a2031aff235a699999f47b95602922d6ddf912ef946912ce00` | Sec. II Eqs. (1)--(2) and following text, PDF p. 3 | Closed limitation: a loopy local discarded tail and its product are approximate diagnostics, not a whole-state certificate. |
| Existing native implementation | Pinned implementation; fork commit `d90bb5ea210e666cbd7ecf8a8b7fa02390519baf`, tree `f7cd3496c48ec69f1800d41eabcaa8d53cab3b5b` | N/A; pinned source, not an admitted note | N/A; Git commit/tree identities replace a PDF hash | `carrier.py:733-739,942-1017`; `native.py:1038-1534` | Closed for locating the reusable compiler/executor only; implementation correctness remains subject to regressions. |
| Legacy thread-divergence input | Post-result engineering diagnostic dated 2026-07-29; explicitly non-held-out | `docs/simulator_validation/GCAPEPS_LEGACY_THREAD_DIVERGENCE_DIAGNOSTIC_2026-07-29.md`; `275264ab2e9d32cbf3615eb5ce6a652a7a06d2116ae246a0fc2085a34b7feb81` | N/A; diagnostic transcription, with no sealed raw-vector artifact | “Scope and source identity”, “Observed localization”, and “Program-level inference” | May localize the programming defect and register a regression only. It is post-result evidence and cannot qualify a faithfulness, performance, or held-out scientific claim. |

The bound legacy diagnostic was written after the divergent result was
inspected. It is therefore a post-result, non-held-out localization note. Its
numbers may select a reproducible engineering regression, but they cannot be
reused as confirmation of GCAPEPS faithfulness, accuracy, or performance.

## Anomaly ledger

| Contrary fact / ambiguity | Affected object | Implication | Status / action |
|---|---|---|---|
| The frozen formal finite-memory preregistration explicitly selects `exact_tree_then_native_compress`. | formal bond-32 experiment | Switching strategies would be a post-registration method change. | Formal route remains fail-closed; this repair creates only an engineering regression lane. |
| The native executor currently always creates an uncapped shadow for every two-site step. | engineering timing instrumentation | Current native timing includes evidence-only work. | Add an explicit no-shadow execution mode and require semantic equality to evidence replay; do not report a speedup or performance conclusion from this packet. |
| Current native full-basis fixtures do not cover a multi-terminal branching tree. | compiler completeness | Two-terminal routing does not cover a dirty branching router. | Register a 2x3, 64-column branching fixture before using the lane. |
| PEPS has no generic MPS-like canonical form and local simple update omits the full environment. | capped native path | Thread determinism is necessary for an implementation but is not a faithfulness theorem. | Use complete vectors only as bounded regression comparators and forbid faithfulness extrapolation. |

## Local search and external-acquisition ledger

The artifact-verified current corpus was queried on 2026-07-29:

```text
PEPS gauge freedom simple update truncation local SVD canonical form
Pauli string rotation CNOT parity RZ uncompute Clifford frame
concept: simple update
concept: PEPS truncation
```

The first query returned admitted, source-located Evenbly, Kilda,
Czarnik--Dziarmaga--Corboz, and Rudolph--Tindall records. The second returned
the admitted Masot-Llima record and the existing native bridge packet. The KG
concept queries had no direct graph hit, which is not treated as evidence.
`literature_rag.py audit` reported the cited records as
`artifact_verified`.

External AnySearch acquisition was not invoked: every load-bearing row for
this engineering-path correction and thread-determinism regression is closed
by an admitted primary source, a complete finite-dimensional derivation, or
the pinned implementation. No row closes a finite-cap whole-state error bound,
faithfulness claim, or performance claim. This packet makes no novelty or
field-wide absence claim.

## Operation replay

| Input | Transformation | Assumption | Output | Locator | Status |
|---|---|---|---|---|---|
| physical \(P\), frame \(C\) | compute \(Q=C^\dagger PC=s\bar Q\) | \(C\) is Clifford and \(P\) Hermitian Pauli | signed residual word | Masot-Llima Eqs. (3)--(6); pinned frame code | closed |
| \(\bar Q\) | local \(X/Y/Z\) basis changes \(B\) | \(B\bar QB^\dagger\) is a Z string | Z-parity target | direct one-qubit conjugation; `native.py:1109-1127,1170-1188` | closed |
| Z-parity target | dirty-router-safe parity compute \(V\) | every borrowed router is SWAP-restored | \(V^\dagger Z_rV=\prod Z_j\) | direct CNOT/SWAP conjugation; `native.py:1129-1168` | algebraically closed; implementation corruption test pending |
| root \(Z_r\) | apply \(R_Z(s\theta)\), reverse \(V\), reverse \(B\) | no truncation for exact identity | \(e^{-i\theta Q/2}\) | existing native bridge closure; `native.py:1161-1188` | closed |
| loopy finite-bond state | apply local simple-update caps | local gauges approximate, not a full environment | bounded candidate state | Evenbly Eq. (12) and Kilda Appendix A.1.1 | limitation closed; whole-state error remains unbounded by this packet |

## Closure verdict

```text
closure_status = closed
closure_scope = engineering_path_and_thread_determinism_only
pass_to_prereg = yes_engineering_regression_only
formal_old_prereg_amended = no
development_code_allowed_only_after_prereg = yes
legacy_capped_tree_identity_lane = post_result_diagnostic_control_only
selected_thread_determinism_candidate = native_simple_update
selected_finite_bond_faithfulness_candidate = none
selected_performance_candidate = none
finite_cap_whole_state_error_bound = unbounded_by_this_packet
capped_native_faithfulness_claim = forbidden
capped_native_performance_claim = forbidden
generic_gauge_invariant_truncation_claim = forbidden
generic_faithfulness_claim = forbidden
generic_speedup_claim = forbidden
record_or_measurement_reset_claim = forbidden
```

