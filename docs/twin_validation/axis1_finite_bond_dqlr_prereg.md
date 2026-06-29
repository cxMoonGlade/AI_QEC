# Axis-1 Step 7 Prereg — (A) Mixed-Dim Finite-Bond Schmidt-Tail Error Bound + (B) Leakage-Removal/DQLR Scope

Date: 2026-06-29

Status: theory-first PRE-REGISTRATION (finish-plan Step 7). **Part A** registers a
mixed-dimension finite-bond *discarded-weight certificate* + a falsifiable monotone
convergence band for the MCWF/MPS carrier. **Part B** is the leakage-removal/DQLR scope
decision: after a theory-first close-read of the cached papers, faithful DQLR is
documented as **OPEN (a cross-cycle Axis-2 protocol)**; only the *constituent*
within-substep operations are Axis-1-representable, and one of them (the multi-level
reset channel) is already in the carrier. **No DQLR removal channel is shipped in Step 7.**

This document does **not** claim Axis-1 completion, does **not** modify
`docs/METRICS.md`, introduces **no new scored quantity**, and keeps
`accepted_as_production_error_bound=false`. A prediction-band miss is a FINDING, never a
silent refit (CLAUDE.md epistemic-status discipline).

---

## Part A — Mixed-Dimension Finite-Bond Schmidt-Tail Discarded-Weight Ledger

### A.0 Current repo state (the live gap)

The MCWF/MPS carrier (`src/qec_twin/simulator/axis1_mcwf_mps_execution.py`) is
dimension-polymorphic in contract and execution (qubit / qutrit / ququart / mixed
`local_dims`) **except** that it FAILS CLOSED on a finite `max_bond` for mixed dims:

- `axis1_mcwf_mps_state_record_execution_manifest(...)` lines 176-198 return
  `blocked_reason = "mcwf_mps_multilevel_finite_bond_ledger_not_implemented"` whenever
  `max_bond is not None and any(dim != 2 for dim in local_dims)`. (a/c)
- `_apply_hamiltonian_terms_multilevel` (line 611) computes
  `all_qubit_dims = all(dim == 2 for dim in local_dims)` and passes
  `track_shadow=all_qubit_dims` into `_apply_mps_gate` (line 632), so the per-gate
  shadow Schmidt-tail event is recorded ONLY for pure-qubit schedules. (a)
- The shadow recorder `axis1_qt_mps_execution._shadow_schmidt_tail_records` (line 2196)
  reshapes the dense MPS as `state.reshape((2,) * n)` and cuts at `2**cut` — correct only
  for local dimension 2. (a)
- `_mcwf_mps_truncation_ledger` (line 1577) RAISES for mixed-dim + finite `max_bond`. (a)

A no-explicit-truncation run (`max_bond=None`) already marks
`accepted_as_exact_bond_representation: True` with an empty (zero) discarded-weight
ledger — exact-representability bookkeeping, correct as-is.

### A.1 Grounding ledger (theory-first; sources READ, not cited-from-memory)

| decision surface | source | project note / code | use here | class |
|---|---|---|---|---|
| MPS truncation discarded-weight = sum of squared discarded Schmidt coefficients; per-shot trajectory + discarded-weight monitoring | Manabe, Suzuki & Darmawan, arXiv:2308.08186 | `docs/papers/reading_notes/leakage_tensor_network_simulation_2308.08186.md`; carrier | the field-standard MPS truncation CERTIFICATE shape (the quantity recorded per cut); QEC qutrit-MPS trajectory precedent | (a/c) |
| Schmidt decomposition / bipartite-cut singular-value spectrum; bond dimension = Schmidt rank | standard TN (Schollwöck-class) via Jaschke note | `docs/papers/reading_notes/jaschke_open_quantum_tensor_networks_1804.09796.md` | the exact discarded-weight identity `sum_{k>=chi} sigma_k^2` at a bipartite cut; min-cut bond sufficiency | (a) |
| Same-substep GKSL target; the joint-generator oracle | Jaschke et al. 1804.09796 (FULL-TEXT) | reading note above; `forward.joint_lindbladian.assemble_substep_channel` | the INDEPENDENT convergence target the finite-bond runs approach | (a) |
| Process infidelity `1-F_e`, Choi trace distance, trace distance, TV | `docs/METRICS.md` | metric ledger | the standard metrics the convergence band + no-trunc cert are scored in; no new metric | (a) |
| Reuse of the qubit shadow-tail ledger pattern | this repo | `axis1_qt_mps_execution._shadow_truncation_event` / `_truncation_gate_result` / `_shadow_schmidt_tail_records` | the qubit pattern generalized to mixed leg dims; the policy gate + exact-bond bookkeeping reused unchanged | (a/c) |

**Theory-first confirmation.** The Manabe note (QEC qutrit-MPS trajectory simulation)
and the Jaschke note (FULL-TEXT, open-system TN taxonomy) are committed reading notes;
the discarded-weight = squared-Schmidt-tail identity and bond=Schmidt-rank are standard
exact TN facts read from them. The certificate is therefore literature-anchored (a-class
for the FORM and the per-cut quantity); the convergence band magnitude is b-class.

### A.2 Derivation (the discarded weight is EXACT; convergence is a band)

For a normalized MPS state `|psi>` on sites with local dims `(d_0, ..., d_{n-1})`, the
bipartite cut after site `k-1` (left = sites `0..k-1`, right = `k..n-1`) has Schmidt
decomposition `|psi> = sum_j sigma_j |L_j> |R_j>` with `sum_j sigma_j^2 = 1`. Truncating
to bond `chi` keeps the `chi` largest `sigma_j` and discards the rest; the EXACT
discarded weight at that cut is

```
w_cut(chi) = sum_{j >= chi} sigma_j^2        [a, exact Schmidt-tail identity]
```

This is the squared 2-norm of the discarded Schmidt vector — the field-standard MPS
truncation error certificate (Manabe; Schollwöck). The only thing the qubit-hardcoded
recorder got wrong is the *leg reshape*: the singular spectrum at a cut is computed from
the matricization `psi.reshape(prod(d_0..d_{k-1}), prod(d_k..d_{n-1}))`, NOT
`psi.reshape(2**k, 2**(n-k))`. **CONFIRMED quimb semantics (Step-7 probe):**
`MPS.to_dense()` fuses site indices in site order (site 0 most-significant), so flattening
to `(prod(d),)` and reshaping to `(d_0, ..., d_{n-1})` recovers the per-site legs in
ascending order and the mixed-dim cut is `reshape(prod(d[:k]), prod(d[k:]))`. For
`d_i == 2` this is bit-identical to the qubit recorder (proven by red-test T1).

Exact-bond sufficiency (min-cut identity, a-class): a state on `(d_0,...,d_{n-1})` has
Schmidt rank at any cut `<= min(prod(left), prod(right))`, so a conservative sufficient
bond is `chi* = max_cut min(prod(d[:k]), prod(d[k:]))`
(`exact_mixed_dim_bond_sufficient`; mirrors the in-tree `_exact_mixed_dim_bond_sufficient`).
At `chi >= chi*` truncation is lossless and `w_cut = 0` exactly.

The carrier's MCWF/MPS bond growth comes ONLY from multi-site (two-site) Hamiltonian
cluster gates (`_apply_mps_gate` with `contract="auto-mps"`, `max_bond` applied);
one-site jumps / projectors / one-site gates do not grow the bond (`contract=True`,
`max_bond=None`). So the per-gate shadow Schmidt-tail need only be recorded before each
two-site cluster gate — exactly the existing `_shadow_truncation_event` cadence,
generalized to mixed dims. (a)

### A.3 Anti-circular oracle (FAITHFULNESS rule I)

The convergence target and the no-truncation reference are the INDEPENDENT dense joint-L
oracle: `axis1_mcwf_dense_certification._dense_jointL_level_distribution`, which evolves
`rho0` through each dynamics substep with `assemble_substep_channel(H_list, c_list, dt)`
(sum-all -> ONE `expm(L dt)`, built from the per-term physics `_hamiltonian_matrix_for_term`
/ `_collapse_operator` — **NEVER** the carrier's `_hamiltonian_group_gates`). A wrong
carrier grouping is caught by the oracle comparison, not mirrored. The carrier cluster
gate is fed to the shadow ONLY as the state whose Schmidt spectrum is measured; the
discarded weight is an exact algebraic property of that state. (a)

### A.4 Registered prediction bands (epistemic class b unless marked)

For the compiler-generated qutrit two-site leakage-transport fixture (a `CZ` layer
carrying public `LEAK_EXCHANGE_11_02`, `local_dims=(3,3)`, `initial_levels=(1,1)`,
`gamma_phi=gamma_1=0` so the substep is pure-Hamiltonian and the carrier joint
`matrix_exp` is exact vs the oracle):

- **B1 [a] no-truncation == dense.** At `max_bond=None` (and at `max_bond >= chi* = 3`)
  the carrier level-record distribution matches the dense joint-L level-population oracle
  to TV `~ 0` (exact-branch) / within the per-bin Hoeffding finite-shot CI (sampled,
  `N=2048`, confidence 0.999). The pure-Hamiltonian substep has no finite-step error, so
  this is an EXACT match within shot noise (class a for the channel, a/b for the sampled
  estimate). A miss => the reshape / oracle wiring is broken — STOP. (red-test T2)
- **B2 [b] finite-bond monotone convergence.** As `max_bond` rises over `{1, 2, 3}`
  toward `chi* = 3`, BOTH the recorded discarded-weight sum AND the trace distance of the
  truncated state to the exact (unbounded) state DECREASE MONOTONICALLY (non-increasing,
  within `1e-9` round-off). A non-monotone miss is a FINDING (the truncation is not
  behaving as a Schmidt-tail discard) — reported, never silently re-fit. (red-test T3)
- **B3 [a] under-bond is caught (falsifying control).** At `max_bond=1 < chi*` the ledger
  records nonzero discarded weight (`> 1e-3`), marks
  `accepted_as_exact_bond_representation=False` and
  `finite_cap_below_conservative_exact_sufficient_bond`, and the truncated state is
  strictly FARTHER from the exact state than the exact-bond run
  (`trace_dist(chi=1) > trace_dist(chi=3) ~ 0`). Truncation MUST damage the state — a
  no-op / zero-discard ledger would pass falsely; this control fails it. (red-test T4)
- **B4 [a] qubit parity.** For `local_dims` all `== 2` the mixed-dim recorder is
  bit-identical (discarded weight, pre/kept rank, total Schmidt weight) to the in-tree
  qubit recorder `_shadow_schmidt_tail_records`. The generalization changes NO qubit
  numerics. (red-test T1)
- **B5 [a] exact-bond identity.** `exact_mixed_dim_bond_sufficient` equals the min-cut
  bond for `(3,3)->3`, `(2,2)->2`, `(2,3,2)->2`, `(3,3,3)->3`, `(2,4)->2`. (red-test T5)

### A.5 Acceptance policy (what the carrier ledger reports)

The mixed-dim ledger has the SAME key shape as the qubit ledger
(`_truncation_ledger`), so the existing `_truncation_gate_result` policy gate
(worst-cut / total discarded-weight tripwires, class c) and the acceptance policy consume
it unchanged, plus a `local_dims` field and
`ledger_method="cuda_shadow_state_schmidt_tail_per_two_site_hamiltonian_gate_mixed_dim"`.

```
mps_truncation (mixed-dim) = {
  "explicit_truncation_requested": true,
  "local_dims": [...],
  "max_bond": <int>,
  "exact_bond_dimension_sufficient": <chi*>,
  "exact_bond_policy": "finite_cap_{at_or_above|below}_conservative_exact_sufficient_bond",
  "accepted_as_exact_bond_representation": <max_bond >= chi*>,
  "discarded_weight_ledger_complete": true,           # the CERTIFICATE is complete
  "discarded_weight_sum": <sum of per-gate per-cut w_cut>,   # class a (exact Schmidt-tail)
  "worst_cut_discarded_weight": <max per-cut w_cut>,         # class a
  "accepted_as_production_error_bound": false,        # NON-OPTIONAL: certificate, not bound
  "comparison_outcome_is_metric": false,
  "epistemic_class": "c",
}
```

`accepted_as_production_error_bound=false` is **load-bearing**: the discarded weight is an
exact per-cut Schmidt-tail CERTIFICATE (class a) and the monotone-convergence band is
class b; neither is promoted to an a-class production error bound (which would need an
operator-norm accumulation theorem or the Werner LPTN trace-norm certificate — NOT
claimed here). The bound is a falsifiable *check*, not the *control law*.

### A.6 Anti-toy / no-laundering predictions

- **No metric invention:** discarded Schmidt-tail weight is the field-standard MPS
  truncation certificate; trace distance / TV / `1-F_e` are the existing standard metrics
  (METRICS.md). No new scored quantity. (a)
- **No silent refit:** a monotone-convergence miss (B2) or an uncaught under-bond (B3) is
  a test FAILURE / FINDING, not a constant bump. (b)
- **No Axis-2 leakage:** no source timelines, memoryful noise, `.dem`, or decoder
  semantics. (a)
- **Anti-circular oracle:** convergence checked against `assemble_substep_channel`, never
  the carrier `_hamiltonian_group_gates`. (a)
- **Compiler-generated fixtures:** the qutrit transport schedule is built from public
  Axis-1 context through the compiler (CZ + `LEAK_EXCHANGE_11_02`), not a hand-written
  schedule (prereg `axis1_leakage_transport_removal` §7). (a/c)

### A.7 Open risks / decisions

- The convergence band is registered on ONE mixed-dim fixture (qutrit `|11>`->`|02|`
  exchange). Generalizing the discarded-weight CONTROL (picking `max_bond` from a target
  tolerance) to arbitrary mixed-dim substeps is a future a-class question (LPTN/MPDO
  trace-norm certificate), not claimed here. (b/c)
- The shadow Schmidt-tail is recorded per two-site cluster gate (the only bond-growing
  op). If a future carrier slice introduces a >2-site bond-growing gate, the shadow span
  generalizes naturally (the recorder already cuts over `support`'s full span), but the
  bond-growth cadence assumption should be re-checked. (a/c)

---

## Part B — Leakage-Removal / DQLR Scope Decision (theory-first; DOCUMENTED AS OPEN)

### B.0 The decision

**A faithful SAME-SUBSTEP leakage-removal CHANNEL exists and is partly already in the
carrier; faithful DQLR as the QEC-relevant PROTOCOL is OPEN (cross-cycle, Axis-2).**
Step 7 ships **no DQLR removal primitive** — the constituent within-substep operations
that ARE Axis-1-representable are documented here, the multi-level reset one is noted as
already-present, and the protocol/effect is documented as the Axis-2 gap with precisely
what it needs. This follows the project's own preregs
(`axis1_leakage_transport_removal_prereg.md` §5/§8: "full DQLR is a schedule/protocol
feature … should get a separate prereg before implementation"; "current code must not
claim full leakage removal, full DQLR") and the completion review (DQLR "remains open").

### B.1 Grounding ledger (theory-first close-read of cached papers)

| decision surface | source | project note / PDF | finding | class |
|---|---|---|---|---|
| Multi-level reset (MLR) primitive | McEwen et al., arXiv:2102.06131 | `docs/papers/reading_notes/mcewen_removing_leakage_correlated_2102.06131.md` §3.1; PDF L172-177 | swap→hold→return pulse; "designed to **unconditionally** prepare the ground state, and thus remove all quantum data" — an unconditional reset-to-\|0> map | (a) form; (b) residual rates |
| DQLR (Data-Qubit Leakage Removal) | Miao/McEwen et al., arXiv:2211.04728 | `docs/papers/reading_notes/miao_overcoming_leakage_scalable_2211.04728.md` §3.2; PDF S2 L955-970 | a within-cycle SEQUENCE: MLR(measure) → LeakageISWAP(\|11>↔\|20>) shuttling data\|2> onto reset measure qubit → second MLR(measure); applied **every cycle** | (a) op forms; (b) rates/effect |
| LRU abstraction + indistinguishability/cadence | Fowler, arXiv:1308.6642 | `docs/papers/reading_notes/fowler_leakage_topological_codes_1308.6642.md` §2/§3 | a leaked qubit produces detection events separated by many rounds (non-local); restoring `p^{d/4}` scaling requires PER-ROUND removal — the *effect* is a cadence property | (a) LRU=L→Pauli; (b) scaling |

External identity: the cached PDFs (2102.06131, 2211.04728, 1308.6642) and their
committed reading notes were close-read on 2026-06-29; equations/passages quoted from the
notes + PDFs, not abstracts.

### B.2 What IS faithfully representable in Axis-1 (the per-application operations)

Each is a CPTP / unitary map on the declared multilevel Hilbert space — a single
within-substep operation:

1. **Multi-level reset channel (McEwen MLR), already in the carrier.** As an idealized
   channel the MLR "unconditionally prepares \|0>" (2102.06131 PDF L172-177), i.e. the
   trace-preserving reset

   ```
   E_reset(rho) = sum_{l} |0><l| rho |l><0| = Tr(rho) |0><0|        [a, definitional CPTP]
   ```

   with Kraus `{ K_l = |0><l| : l = 0..d-1 }`. This is **already implemented and
   dense-certifiable** in the carrier: `axis1_mcwf_dense_certification.py:1255-1260`
   (reset channel `sum_l |0><l|`) and the post-measurement reset L1294-1298; the carrier
   program lowers it as the `RESET_Z` / `MR*` instrument boundary. The completion review
   confirms the multilevel `MR*` boundary exists. **Step 7 adds nothing here** — it is
   noted so the Part-B picture is complete.

2. **LeakageISWAP transport Hamiltonian.** The DQLR shuttle is an ISWAP in the
   `|11>-|20>` subspace (2211.04728 PDF L963-967), i.e. the two-site Hamiltonian
   `H = omega (|20><11| + |11><20|)` evolved to `omega*t = pi/2`. This rides the
   *identical* lowering/certification path the carrier already uses for
   `LEAK_EXCHANGE_11_02 = omega(|11><02| + |02><11|)` and the other two-site exchange
   families (prereg `axis1_leakage_transport_removal` §3.1/§9, certified by
   `axis1_two_site_leakage_hamiltonian_certification_manifest`). The operator FORM is
   class a; its removal-fraction / orientation are device-calibrated (class b/c). It is
   the prereg's named-but-deferred `LEAKAGE_ISWAP_REMOVAL` (§5). **Not added in Step 7**
   (it needs its own calibration prereg per §8).

3. **One per-application DQLR** = `MLR(measure) ∘ LeakageISWAP(measure,data) ∘ MLR(measure)`
   is a legitimate single CPTP map on the measure⊗data Hilbert space (composition of CPTP
   maps is CPTP). It is representable, **provided the claim is scoped to "one DQLR
   application," NOT "DQLR steady-state removal."**

**Faithful same-substep removal-channel witnesses (if/when shipped, class a, exact,
zero-tolerance) — for the MLR reset on a qutrit (dim 3):**
- Trace preservation / population conservation:
  `|| sum_l K_l^dag K_l - I_3 || < NUMERICAL_ZERO (1e-12)` (since
  `sum_l |l><0|0><l| = sum_l |l><l| = I`).
- Output is `|0><0|` with unit trace for ANY input (feed `|2><2|`, `|1><1|`,
  `(|0>+|2>)/sqrt2`): `E(rho) == |0><0|`, `Tr == 1` exactly.
- Leakage clearance: `<2|E(rho)|2> == 0` exactly.
- Idempotence: `E∘E == E` (projector channel).

These would be checked against the dense oracle exactly as the existing reset channel in
`_dense_jointL_level_distribution` is.

### B.3 Why faithful DQLR is OPEN (the cross-cycle Axis-2 gap)

The QEC-relevant EFFECT of DQLR — leakage held FLAT at steady state ~`1e-3` over many
cycles, the non-local `p_{t,t'} > 1` leakage correlations crushed, the leakage
decomposed-weight driven to ~1, leakage ≈ Pauli (`1/Lambda ≈ 111 P_L + 0.2`, R²=0.983,
2211.04728 §4.2-§4.4) — is a property of applying the (Axis-1-representable) removal
operation **on the every-cycle cadence** against the ~`5e-3`/cycle leakage source. Three
things faithful DQLR needs that a single within-substep channel CANNOT carry, all
cross-cycle (Axis-2; class a that they are out-of-substep, b for magnitudes):

1. **The cadence IS the effect.** One within-substep channel removes one leakage
   instance; the flat steady state is the time-integral over the schedule. Fowler's
   `p^{d/4}` vs `p^{d/2}` scaling (1308.6642 §3) is a *cadence* law. "Leakage held flat
   over 30 cycles" is a multi-substep trajectory property, not a substep channel.
2. **Reset-failure → data-leakage conversion across cycles.** DQLR data removal is
   conditioned on the measure qubit being `|0>`; a `|1>` reset-residual converts to
   data-qubit leakage that PERSISTS into the next cycle (2211.04728 PDF L966-970). The
   within-substep conditional map is declarable, but its consequence (leakage seeded for
   FUTURE cycles, conditioned on this cycle's reset outcome) is a cross-cycle source term.
3. **Leakage persistence as a source process.** The ~4.4-cycle `|2>` lifetime / long
   `T1(|2>)` (2211.04728 §2/§7) carries leaked population across substeps; the cross-cycle
   carry (and the long-time `p_{t,t'}` tail) is the Axis-2 "leakage persistence as a
   source process" the prereg §2 freezes.

**Required to close (document-as-open):** a cross-cycle leakage-population source/carry
process (per-qubit latent leaked-state propagated substep-to-substep), a SCHEDULING layer
firing the (Axis-1-representable) removal channel on a cadence, and a reset-failure
stochastic branch feeding next-cycle leakage. **None of these change the within-substep
channel FORMS — they sequence and persist them.** This is an Axis-2 cross-cycle
enlargement, NOT an Axis-1 same-substep operator. It needs its own prereg
(`axis1_leakage_transport_removal` §8).

### B.4 Bounded-simplification declaration (Part B)

- The within-substep MLR reset channel (B.2.1) faithfully reproduces ONE application's
  action on the present state (exact, class a). It OMITS the cross-cycle effect (B.3);
  applied on the schedule cadence it reproduces the *removed-regime* statistics only to
  within the residual 2211.04728 itself reports (it UNDER-estimates leakage-induced error
  because intra-cycle leakage MOTION before removal is not captured — 2211.04728 §6,
  authors' explicit limitation). **Bound:** the omission is the paper's own
  removed-vs-unremoved gap; the *intra-cycle leakage dynamics* term is flagged OPEN by the
  authors and is **NOT bounded here** — therefore, per FAITHFULNESS rule III
  (unbounded ⇒ STOP), no same-substep DQLR *effect* claim is made; only the
  per-application operation forms are documented, and Step 7 ships none.
- No `L1/L2/C_L`, `p_ij`, detector-rise, or transport-fraction SCORE is added (METRICS
  ladder not invoked). (a)

---

## Epistemic-status summary (Step 7)

- **Part A discarded-weight certificate** — class **a** (exact per-cut Schmidt-tail
  identity `sum_{k>=chi} sigma_k^2`; qubit parity is a zero-tolerance identity).
- **Part A monotone-convergence band (B2)** — class **b** (registered falsifiable bet; a
  non-monotone miss is a finding).
- **Part A gate thresholds** — class **c** (go/no-go tripwires;
  `accepted_as_production_error_bound=false`).
- **Part B per-application operation forms (MLR reset, LeakageISWAP)** — class **a** for
  the CPTP/unitary forms; **b/c** for rates/fractions/orientation. **Not shipped.**
- **Part B faithful DQLR effect** — documented **OPEN** (cross-cycle Axis-2); the
  intra-cycle leakage-motion omission is UNBOUNDED ⇒ no same-substep effect claim
  (FAITHFULNESS rule III).
