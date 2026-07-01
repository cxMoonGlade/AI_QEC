# M11 spectator_crosstalk_rz_or_zz — pre-registration (theory-first, extended-support)

Date: 2026-06-30. Status: **theory-first pre-registration** (Axis-1 rebuild group 4; the
extended-support mechanism — same-substep coherent Hamiltonian on gate ∪ spectator). Governs
`docs/twin_validation/axis1_rebuild_plan.md`; companion derivation
`m11_spectator_crosstalk_theoretical_derivation.md` (already de-circularized + code-fixed).
Discipline: `FAITHFULNESS_PROTOCOL.md` + `METRICS.md`. **All cited equations text-verified against
`outputs/papers/` + committed reading notes.**

## 0. The mechanism (two forms, extended support)

When a gate acts on qubits (A,B), an idle **spectator C** picks up a parasitic coherent term in the
SAME substep, on the EXTENDED support (A,B,C):
- **ZZ form** — `H_xtalk = ζ_x · Z_B ⊗ Z_C` (conditional-phase between a gate qubit and the
  spectator). Carrier: `COH_CROSSTALK_ZZ` on `support=(B,C)` → `(coeff/4)·(Z⊗Z)`.
- **RZ form** — `H_rz = J_rz · Z_C` (a deterministic Z rotation spilled onto the spectator). Carrier:
  `COH_RZ` on `support=(C,)` → `(coeff/2)·Z`, so **`J_rz = coeff/2`** (carrier ½ convention — pin it).

The extended-support assembly `H_gate(A,B) + H_xtalk(B,C)` on `(A,B,C)` is realized by the carrier's
**connected-cluster machinery** (`_hamiltonian_group_gates` + `_lift_hamiltonian_to_cluster`): the two
terms share qubit B → one `{A,B,C}` cluster, summed → exponentiated once (cross-terms exact). This
is M11's only novel content vs the 2q mechanisms.

## 1. Grounding — ≥2 DIRECT-physical per form (text-verified; reading notes exist)

- **ZZ form:**
  - **DIRECT-1 (form): Sarovar, Proctor, Rudinger, Young, Nielsen, Blume-Kohout, "Detecting crosstalk
    errors in quantum information processors," Quantum 4, 321 (2020); arXiv:1908.09855.** §4.3
    mechanism 2 = the coherent `Z⊗Z` crosstalk example (Eq. 14, ε=2e-2); the canonical
    hardware-agnostic crosstalk taxonomy + observable. [note in-repo]
  - **DIRECT-2 (magnitude): Mundada et al., PRApplied 12, 054023 (2019); arXiv:1810.04182** —
    measured residual ZZ `ζ/2π = 2.26 MHz`. [note in-repo] (Companions: Pettersson-Fors 2408.15402,
    Kubo 2402.05361.)
- **RZ-drive form:**
  - **DIRECT-1 (form): Sarovar 1908.09855** §4.3 mechanism 1 "pulse spillover" — the gate→idle-
    spectator off-resonant drive (a coherent Z-axis spill), the exact M11-RZ mechanism.
  - **DIRECT-2 (magnitude): Song et al., "Microwave Crosstalk in Planar Superconducting Quantum
    Devices," arXiv:2606.02440 (2026)** — measured cross-drive ratio `X ≈ −10..−40 dB` ⇒ spillover
    fraction `c = √X ≈ 0.01–0.1`. [note in-repo]
- (Heinsoo 1801.07904 readout crosstalk is the *measurement* sub-form — NOT covered by the coherent
  COH_CROSSTALK_ZZ; context only, out of scope for this coherent-RZ/ZZ prereg.)

Bar **MET for both forms.**

## 2. Epistemic classes
- **(a) exact:** operator identities `H_carrier(COH_CROSSTALK_ZZ)=(coeff/4)Z⊗Z`,
  `H_carrier(COH_RZ)=(coeff/2)Z`; closed forms `1−F_e=sin²(ε/4)` (ZZ), `sin²(ε/2)` (RZ); the
  **cluster-join identity** (carrier 3q window == independent mixed-radix lift of summed generators).
- **(b) prediction band:** ZZ magnitude `ζ/2π∈[0.1,5] MHz` (Mundada 2.26 measured); RZ spillover
  `c∈[0.01,0.1]` (Song) — swept.
- **(c) gate / convention:** the `Z⊗Z` /4 and `Z` /2 carrier conventions; the **twirl/d3-gating** of
  the coherent crosstalk's *syndrome observability* — Sarovar shows coherent `Z⊗Z` under twirling
  manifests only at `O(ε²)` (needs ~10× shots), so on a d3 syndrome stream M11's coherent part is
  twirled-suppressed (a bounded gate, NOT a first-order certifiable moment).

## 3. Closed forms (independent ground truth, hand-derived)
- **ZZ** (`α=ε/4`, ε=coeff·dt): `U=diag(e^{−iα},e^{+iα},e^{+iα},e^{−iα})`; `Tr U=4cos α`;
  `1−F_e=1−cos²(ε/4)=sin²(ε/4)`, leading `ε²/16`. (Z⊗Z diagonal — the conditional phase is the
  `|·11>`-vs-`|·01>` relative phase `e^{−iε/2}`.) Scalar `1−F_e` is **axis-blind** (= M22's) ⇒ the
  **operator-identity gate is the load-bearing axis witness** (Z⊗Z diagonal vs XX/XY off-diagonal).
- **RZ** (carrier ½): `U=diag(e^{−iε/2},e^{+iε/2})`; `1−F_e=sin²(ε/2)`, leading `ε²/4`. Spectator in
  `|1>` picks up `e^{+iε/2}=e^{+iJ_rz·dt}`.
- **Cluster-join (novel):** lift `H_gate(A,B)` and `H_xtalk(B,C)` to the (A,B,C) 8×8 window via a
  **from-scratch mixed-radix lift** (NOT the carrier `_lift_hamiltonian_to_cluster`), sum,
  `U_joint=exp(−i·dt·H_window)`; assert the carrier window channel == `U_joint` to `1−F_e≤1e-6`,
  with gate-pair and spectator-pair routed from SEPARATE clusters so the W-A join is exercised.

## 4. Constraint ledger (physical theorems + FALSIFYING test each)
Independent GT = hand-typed operators + closed forms + from-scratch mixed-radix lift (NumPy).
`assemble_substep_channel` certifies grouping/propagation ONLY (Rule-I; both sides consume the same
per-term builder), NEVER the per-term physics. Cert imports only `_hamiltonian_matrix_for_term` (+
assemble + the cluster helpers as objects-under-test for the join); MUST NOT import
`_coherent_family_generator`/`_embed_coherent_generator`/`CROSSTALK_COHERENT_FAMILIES` as reference.

| # | invariant (class) | falsifier (must trip) |
|---|---|---|
| L1 | ZZ op identity `H_carrier("COH_CROSSTALK_ZZ",(B,C)) == (coeff/4)·Z⊗Z` ≤1e-12 (a) | mutate Z→X (XX) ⇒ off-diagonal ⇒ ‖·‖>1e-3 caught |
| L2 | RZ op identity `H_carrier("COH_RZ",(C,)) == (coeff/2)·Z`, J_rz=coeff/2 ≤1e-12 (a) | drop the ½ (use coeff·Z) ⇒ 2× ⇒ caught |
| L3 | closed forms `1−F_e`: ZZ sin²(ε/4), RZ sin²(ε/2) (a) | swap the two formulas ⇒ caught |
| L4 | **CLUSTER-JOIN** carrier 3q window == from-scratch mixed-radix lift of `H_gate+H_xtalk`, cross-terms retained, `1−F_e≤1e-6` (a) | old Trotter (no join) ⇒ RED (misses `[H_i,H_j]`) ⇒ caught |
| L5 | disjoint clusters factor (spectator far from gate ⇒ tensor product) (a) | force-join disjoint ⇒ spurious correlation ⇒ caught |
| L6 | anti-circular: reference hand-typed; family-generator/CROSSTALK symbols NOT imported (structural) | ref built from carrier family map false-passes corruption ⇒ forbidden |

## 5. Bounded simplifications
- **S1 single spectator (c):** one idle C per gate; multi-spectator is additive to first order. Bound:
  exact for the isolated 3q window; superposition error `O((ζt)²)` cross-spectator.
- **S2 pairwise crosstalk (c):** `Z_B⊗Z_C` pairwise (gate-qubit↔spectator); higher multi-qubit
  crosstalk exponentially suppressed by distance.
- **S3 magnitudes swept (b):** ζ/2π∈[0.1,5] MHz, c∈[0.01,0.1] — not frozen.
- **S4 coherent-crosstalk twirl-gating (c, bounded):** syndrome-level observability is `O(ε²)`
  (Sarovar) — declared; the cert tests the channel/operator level, not syndrome detectability.

## 6. Verification plan (serialized GPU)
`outputs/twin_validation/cert_m11_spectator_crosstalk.py` (scripted; asserts + printed evidence +
flushed + `__main__`): L1–L6 vs hand-typed GT; the L4 cluster-join is the load-bearing novel check
(reuse the proven pattern of `tests/test_axis1_connected_cluster_join.py`, but with an in-file
from-scratch lift as the reference). Falsifiers trip.

## 7. Status
- [x] Theory-first grounding (≥2 DIRECT-physical for ZZ + RZ; reading notes in repo).
- [x] Carrier capability confirmed: COH_CROSSTALK_ZZ + COH_RZ-on-spectator + connected-cluster join
  all implemented and tested green (`test_axis1_connected_cluster_join.py`). GAP: schedule-level
  emission onto spectators not wired (deferred — cert runs at the term-dict level, as M22/M29 do).
- [x] Derivation doc de-circularized + dimensionally-buggy illustrative code fixed (verified on-disk).
- [ ] Cert `cert_m11_spectator_crosstalk.py` (serialized GPU; L1–L6 incl. cluster-join).
- [ ] Multi-agent review.
- Carrier code: already supports M11 — re-verify (cluster join + COH families), do not rewrite.
