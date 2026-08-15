# GCAPEPS exact-tree versus Quimb-native forced truncation — literature closure

Date: 2026-07-29

Status: **closed only for one bounded two-qubit bridge state-action experiment;
generic loopy-PEPS truncation, accumulated error, measurement/reset/Record
faithfulness, and efficiency remain open**

## Frozen claim

`decision/consequence`

: Test whether a Quimb-native one/two-site compilation of one Pauli rotation
  agrees with the existing exact tree-PEPO action when no singular value is
  discarded, and whether applying `max_bond=1` after every native two-site gate
  produces the independently derived transient-truncation error on one held-out
  bridge fixture.

`mechanisms`

: The existing tree lane applies

  \[
  U_P(\theta)=\cos(\theta/2)I-i\sin(\theta/2)P
  \]

  as one exact, uncompressed rank-two PEPO. The new native lane lowers the same
  Hermitian Pauli rotation to local basis changes, graph-edge CNOT/SWAP gates,
  one root \(R_Z\), and the inverse network. For the bounded \(P=Z_0Z_1\)
  fixture this reduces exactly to

  \[
  U_{ZZ}(\theta)
  =CX_{0\rightarrow1}
   \bigl(I\otimes R_Z(\theta)\bigr)
   CX_{0\rightarrow1}.
  \]

: With no truncation, the identity follows from
  \(CX^\dagger Z_1CX=Z_0Z_1\). With a finite cap, Quimb performs a two-site
  split after each CNOT. The first CNOT can therefore create a nonzero
  Schmidt tail even when the final exact target state has Schmidt rank one.

`observable objects`

: A NumPy-only dense anchor, the exact tree output, the uncapped native output,
  and capped native outputs are complete length-four `complex128` vectors in
  the frozen big-endian basis. Primary whole-state quantities are normalized
  squared fidelity, raw \(L_2\) and \(L_\infty\) vector error, and relative norm
  error. Per-split retained dimension and discarded squared singular-value
  weight establish that a real nonzero truncation occurred and identify its
  cause. They remain local diagnostics.

`mechanism-to-observable bridge`

: The only graph edge is a bridge. On this fixture the singular values obtained
  by the exact uncapped shadow split are the state Schmidt coefficients, so the
  omitted squared tail can be derived independently. This exact bridge
  interpretation is not transferred to a PEPS loop. Complete-vector comparison
  remains mandatory even here.

`prediction`

: The formal target uses a held-out input with coefficients \(12/13\) and
  \(5/13\), and angle \(\pi/5\). The cap-only native lane must discard the
  nonzero squared weight \(25/169\), finish with normalized fidelity \(144/169\)
  to the exact target, and have raw \(L_2=L_\infty=5/13\). Exact tree,
  uncapped native, high-cap native, and a direct-final-gate control must agree
  with the dense anchor at the frozen `complex128` software bands.

`possible no-go`

: Local simple-update spectra on a loopy PEPS are not generally full-state
  Schmidt spectra, and a product of retained local weights is not a generic
  whole-state certificate. Nothing in this packet supplies an accumulated
  truncation theorem, a scalable contraction certificate, or a
  measurement/reset/Record bridge.

## Coverage ledger

| Load-bearing row | Evidence/source | Exact locator | Status and implication |
|---|---|---|---|
| Exact tree Pauli rotation | Frozen GCAPEPS theorem and correspondence packet | `GCAPEPS_MATHEMATICAL_FEASIBILITY_THEOREM_2026-07-27.md`, Lemma 3 and Eqs. (9), (11), (13), (16), (17); `GCAPEPS_IMPLEMENTATION_THEOREM_CORRESPONDENCE_2026-07-28.md`, §§2–7 | Closed only for the exact untruncated representation and its bounded construction tests. |
| Native Pauli gadget | Complete finite-dimensional conjugation derivation in this packet | \(CX^\dagger Z_1CX=Z_0Z_1\), hence \(CX(I\otimes R_Z)CX=e^{-i\theta ZZ/2}\) | Closed for the two-site target. General graph routing still requires implementation tests. |
| SVD truncation rule | Paeckel et al. project-fit audit | `PAECKEL_1901_05824_PROJECT_FIT_AUDIT_2026-07-17.md`, Sec. 2.6.1, PDF p. 9 | Retain leading singular values; sequential local truncations need not be globally optimal. |
| Bridge versus loop interpretation | Evenbly source review | `docs/papers/reading_notes/evenbly_closed_loop_truncation_1801.05390_source_review.md`, Secs. III–V, Eqs. (2), (9)–(12), PDF pp. 3, 5–6 | On a bridge the weighted coefficients reduce to Schmidt coefficients; on a loop local coefficients need not be state invariants. |
| Gate truncation and discarded weight | Rudolph and Tindall source review | `docs/papers/reading_notes/rudolph_tindall_gpu_peps_2507.11424.md`, Sec. II Eqs. (1)–(2), PDF p. 3 | The discarded-tail relation is exact under the stated loop-free setting and only approximate on loopy networks; no truncation gives an exact represented update. |
| Whole-state metric | Evenbly source review | Sec. V Eq. (12), PDF p. 6 | Normalized whole-network fidelity is the state-level comparator; local tail is not its generic substitute. |
| Current native implementation semantics | Frozen Quimb fork base | base commit `6fbbf74cd36686ed30a4d8865697ce46e47056c1`, tree `ffdfdf421fbe4d9674c2c88029710042fd18ae14`; `CircuitPEPSSimpleUpdate._apply_gate` and `tensor_network_ag_gate_simple` | Single-site gates contract directly; two-site gates use split/SVD and obey explicit `max_bond`/`cutoff`. The future implementation commit must be separately bound before target execution. |

Source-note SHA-256 identities used by this closure:

```text
Rudolph/Tindall note:
dac7a8e2bb8de3ab1bf79f1cc987a8ba820f46df266b143ea3faad2349b773e8

Evenbly note:
c144aed68d7620b9d444a24e5e081de567b499f8709512ab0c545432c0587bbb

Paeckel audit:
97366fa6391b8c51f60fcf09d2812f5f15ca9981c12bc4f5cb7e63a69673289a
```

## Pilot exclusion and held-out target

A non-claim-bearing API/basis pilot using
\((4/5,3/5,\theta=\pi/3)\) was inspected before this freeze. It confirmed only
the Quimb gate order, vector coordinate, and availability of the bridge
singular spectrum. It is **excluded** from confirmatory evidence and may be
used only as a regression fixture.

The formal target changes all three numerical parameters to
\((12/13,5/13,\theta=\pi/5)\). No formal target output existed when this packet
was written. The preregistration fixes its exact predictions before the native
carrier code or target runner is implemented.

## Local search record

The artifact-verified local literature corpus was audited. The admitted
Paeckel, Evenbly, and Rudolph–Tindall primary-source reviews were read at the
locators above, and the pinned Quimb source was inspected directly. External
search was not invoked because every load-bearing row for this finite bridge
experiment is closed by admitted primary sources, pinned implementation
semantics, or a complete four-dimensional derivation. No novelty or
field-wide literature-gap claim is made.

## Closure verdict

- `closure_status:
  closed_for_bounded_held_out_bridge_transient_truncation_experiment`
- The permitted conclusion is limited to the frozen two-site bridge:
  untruncated native compilation versus exact tree action, followed by a
  deliberately lossy per-gate native cap.
- The local discarded weight is exact for this bridge construction but remains
  a diagnostic, not a generic PEPS or Record error certificate.
- A loopy \(2\times2\) extension is P1 and requires a separate dense-anchor
  preregistration; it may not reuse the bridge identity as a theorem.
- `CODE_PERMITTED` becomes effective only in the first commit that contains
  this closure, its preregistration, and the synchronized claim/metric/provenance
  entries, with no experiment implementation or target output in that commit.
