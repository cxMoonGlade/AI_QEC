# Restricted MPS execution mechanics

`carrier/mps` is an execution-mechanics library for restricted verification routes. It makes
no state-, Record-, or LER-faithfulness claim and is not a registered scientific Carrier.
PEPS remains the trajectory-carrier frontier, and PEPO remains the retained research Carrier.

This Module does not own Axis-1 route selection, QT/MCWF evolution laws, Record-support schemas,
sampling order, dense References, metrics, or acceptance. Those remain in the frontend Adapters and
`certify/axis1_mps.py`. In particular, the current QT sampled Adapter performs sequential conditional
single-site binary measurement and emits only lexicographically sorted observed outcomes, while QT
exact execution retains full binary support. That sparse Record Interface and its pre-CUDA resource
preflight are frontend policy, not a faithfulness property granted by these mechanics.

`uncapped_nonlocal.py` applies a bounded three-to-five-site unitary without inheriting Quimb's
nonzero dense-to-MPO split cutoff. Both dense-to-MPO construction and MPS/MPO compression name
`cutoff=0.0` explicitly. The helper builds and validates a deep candidate; callers own the final
transactional commit. Its resource ceilings are numerical-only allocation guards, not accuracy or
physical thresholds.

`probability.py` owns only law-neutral float64 mechanics: immutable validation of raw finite
nonnegative candidate mass, representability-aware multiplication, and cancellation-safe
`1-exp(-x)`. It never replaces the immutable raw values or decides that their total must equal one.
Its categorical helper normalizes only the positive sampling vector after the caller has inspected
and applied its route policy. QT Kraus/projective completeness and MCWF first-order residual policy
remain separate frontend Adapter contracts.

`controls.py` owns law-neutral Python control validation. Integer controls use the index protocol
and reject booleans, floats, and strings instead of narrowing them with `int(...)`; enumerated,
boolean, device, and finite-real controls likewise reject coercive substitutes before CUDA or a
nested execution route is entered. Scientific defaults and acceptance policy stay in the owning
frontend Adapter.

`state.py` owns route-neutral state mechanics: finite real norm evaluation, observed virtual-bond
inspection, the open-chain cut-product sufficient exact-bond cap, and transactional candidate
commit with rollback. None of these operations chooses a route, accuracy threshold, or acceptance
policy.

`capped_two_site.py` reports each retained virtual index as
`actual_kept_bond_dimension`. That is the bond index size after the split, not a numerical rank.
Any thresholded numerical-rank diagnostic must name and serialize its threshold separately. The
module also reports raw and pre-split-relative discarded weights; neither is a global state or
Record-law error bound.

`truncation.py` validates and aggregates raw split events without choosing a QT/MCWF occurrence law
or final verdict. Exact branches and sampled trajectories retain separate Adapter policies.
