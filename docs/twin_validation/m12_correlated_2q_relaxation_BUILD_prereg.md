# M12 correlated_two_qubit_relaxation — BUILD pre-registration (Dicke collective collapse)

Date: 2026-06-30. Status: **theory-first BUILD pre-registration** (Axis-1 rebuild group 5).
Supersedes/extends the existing `m12_correlated_2q_relaxation_prereg.md` +
`..._theoretical_derivation.md` (both already de-circularized; fabricated DiVincenzo–Yang ref
deleted; magnitude bracketed (c)). Governs `axis1_rebuild_plan.md`. Discipline:
`FAITHFULNESS_PROTOCOL.md` + `METRICS.md`. **DOIs verified against arXiv abstract pages 2026-06-30.**

## 0. The mechanism
M12 = same-substep **two-site JOINT collapse** (collective / Dicke damping): a single Lindblad jump
operator coupling both qubits to a shared bath,
```
L = √γ_corr · (σ₁⁻ ⊗ I + I ⊗ σ₂⁻),   σ⁻ = |0><1|
```
Signatures that distinguish it from independent T1 (two separate `√γ·σ⁻` channels):
- **Entangled jump:** `L|11> = √γ_corr(|01>+|10>)` → normalized `(|01>+|10>)/√2` (a Bell state).
- **Subradiant dark state:** `L·(|01>−|10>)/√2 = 0` (the antisymmetric state is decay-free).
- **Super/subradiant rate split:** `L†L` eigenvalues `2γ_corr` on `|Ψ_s>=(|01>+|10>)/√2`, `0` on
  `|Ψ_a>=(|01>−|10>)/√2` (Dicke).
- **O(dt) double-decay:** `P(both decay) = γ_corr·dt` (correlated, first-order) vs `γ₁γ₂(dt)²`
  (independent, second-order).

## 1. Grounding — ≥2 DIRECT-physical (SC qubits, verified DOIs)
- **DIRECT-1 (experiment, peer-reviewed): Mlynek, Abdumalikov Jr., Eichler, Wallraff,
  "Observation of Dicke superradiance for two artificial atoms in a cavity with high decay rate,"
  Nat. Commun. 5, 5186 (2014); arXiv:1412.2392; DOI 10.1038/ncomms6186.** Two superconducting
  transmons in a microwave cavity: measured bright-state decay `2Γ_κ`, dark-state `0` (≈2×
  enhancement), field tomography F=0.94. Device-real collective relaxation in SC qubits.
- **DIRECT-2 (theory, peer-reviewed, SC-specific): Cattaneo, Giorgi, Maniscalco, Paraoanu, Zambrini,
  "Bath-induced collective phenomena on superconducting qubits: synchronization, subradiance, and
  entanglement generation," Annalen der Physik 533, 2100038 (2021); arXiv:2005.06229.** Explicit
  collective Lindblad dissipator on SC qubits sharing a bath → subradiance + entanglement; the
  operator-direct anchor for `L = √γ(σ₁⁻+σ₂⁻)` + the cross-rate `γ₁₂`.
- **SUPPORTING: Ojanen, Niskanen, Nakamura, Abdumalikov Jr., arXiv:0705.1085 (2007)** — SC flux-qubit
  theory; super/subradiant rate structure `Γ_s=2Γ₀, Γ_a=0`. **arXiv-ONLY** (DataCite DOI
  10.48550/arXiv.0705.1085, no journal version) — flagged; it is the structural-ratio anchor, not
  counted as one of the two peer-reviewed DIRECT refs. (Title nit: the canonical arXiv title is "Is
  relaxation correlated in superconducting qubits?"; the repo's "Global relaxation…" is the PDF
  running-header — to be corrected in the derivation doc.)
- **Operator form (textbook/standard): GKSL — Gorini-Kossakowski-Sudarshan, J. Math. Phys. 17, 821
  (1976); Haroche & Raimond, *Exploring the Quantum* (OUP 2006), collective damping.** Ficek-Tanaś
  arXiv:1002.4124 (Lehmberg–Agarwal collective master eq.) as the multi-emitter operator reference.

**Bar MET:** 2 peer-reviewed SC-qubit collective-relaxation DOIs (Mlynek experiment + Cattaneo
theory). **Magnitude `γ_corr = η·γ₁`, η∈[0,1], is class (c) bracketed/swept** — no read paper
measures the incidental shared-bath cooperativity in a multi-qubit SC processor (Mlynek is the
engineered η≈1 maximum; Ojanen pins only the structural ratio). Honest, unchanged.

## 2. Carrier status — channel-level TODAY; MCWF/MPS-trajectory seam is the build gap
- **Channel level (dense): buildable NOW, no new code.** `joint_lindbladian.liouvillian_superop`
  accepts an arbitrary `c_list` of `(D,D)` operators, so a hand-built 4×4 `√γ(σ⁻⊗I+I⊗σ⁻)` feeds
  straight into `assemble_substep_channel` → CPTP Kraus. The §6 cert runs here today.
- **MCWF/MPS trajectory: GAP (the one genuine new-carrier-code piece).** `_collapse_operator`
  (`axis1_mcwf_mps_execution.py`) builds only single-site ops; `_sample_joint_jump_or_nojump`
  hardcodes `where=support[0]`, `contract=True`. A 2-site joint jump (`where=(i,j)`) + the joint
  4×4 no-jump Kraus must be added. **This is a gated, careful build (faithfulness-first,
  multi-builder + reviewer), with the §6 channel cert as its oracle.** Mechanism-completeness doc
  marks M12 ❌ "carrier collapse is 1-site today" — this seam closes it.
- **Do NOT reuse** `forward/channels.py::correlated_relaxation_kraus` (diag([1,1,1,√(1−g)]), only
  `|11>→|00>`) — a different, non-collective legacy toy under the same "M12" label. Not the Dicke
  operator.

## 3. Epistemic classes
- **(a) exact:** the collective operator `L`; the jump map / dark-state / `L†L`-eigenvalue identities;
  the closed-form `1−F_e` linearity in κ=γ·dt; steady state |00>.
- **(b) prediction band:** none load-bearing (the cross-rate γ₁₂ structure is exact; the *magnitude*
  is (c)).
- **(c) gate / bracketed:** cooperativity `η∈[0,1]` (swept); the RWA/Born-Markov collective-bath
  assumption (bounded `O((g/Δ)²)`, `O(γτ_B)`).

## 4. Constraint ledger (physical theorems + FALSIFYING test each)
Independent GT = hand-typed `L` (from raw 2×2 σ⁻) + a **from-scratch dense Liouvillian** (`D[L]`
built by hand → `expm` → Choi→Kraus). `assemble_substep_channel`/`liouvillian_superop` are
grouping/propagation cross-checks ONLY (they consume the same `c_list`), NEVER the operator GT.

| # | invariant (class) | falsifier (must trip) |
|---|---|---|
| L1 | `L == √γ(σ⁻⊗I + I⊗σ⁻)` hand-typed (a) | the legacy diag([1,1,1,√(1−g)]) toy ⇒ ‖·‖>1e-3 caught |
| L2 | entangled jump `L\|11> ∝ (\|01>+\|10>)/√2` (a) | independent `L₁=√γσ⁻⊗I` alone ⇒ `\|11>→\|01>` only ⇒ caught |
| L3 | subradiant dark state `L\|Ψ_a>=0` (a) | wrong relative sign (`σ⁻⊗I − I⊗σ⁻`) ⇒ `\|Ψ_s>` dark instead ⇒ caught |
| L4 | `L†L` eigenvalues {2γ on Ψ_s, 0 on Ψ_a} (a) | sum of independent `L†L` ⇒ no off-diagonal cross term ⇒ caught |
| L5 | `1−F_e` LINEAR in κ (collapse), ratio→1 (a) | a coherent over-rotation ⇒ quadratic ⇒ caught |
| L6 | joint ≠ independent: `1−F_e(joint, indep)` LARGE (a) | identical channels ⇒ 0 ⇒ caught |
| L7 | carrier dense channel `assemble([L])` == from-scratch dense Liouvillian `expm` ≤1e-9 (a) | wrong-sign L in GT ⇒ caught |
| L8 | CPTP `min eig Choi ≥ −1e-12`, TP (a) | — structural |
| L9 | anti-circular: GT hand-typed + from-scratch Liouvillian; `_collapse_operator`/`liouvillian_superop` NOT the operator GT (structural) | GT built from carrier op false-passes corruption ⇒ forbidden |

## 5. Bounded simplifications
- **S1 collective bath / RWA / Born-Markov (a-bounded):** `L=√γ(σ₁⁻+σ₂⁻)` is the matched-coupling
  (`g₁=g₂`, `Γ_a=0`) limit; general `Γ_a=γ−γ₁₂>0` adds the independent part. Bound: exact at
  `γ₁₂=γ`; the `γ₁₂<γ` case is the `C_s,C_a` two-operator form (declared, exact).
  **Implemented-form reconciliation (5-model review finding #7):** the derivation describes the general
  two-operator unraveling `{NO_JUMP, C_s, C_a}` (McDermott Eq. 46); the seam built here is the
  matched-coupling limit, where `C_a = √(Γ_a)·(σ₁⁻−σ₂⁻) ≡ 0` because `Γ_a = γ−γ₁₂ = 0`, so the single
  collective operator `C_s = √γ(σ₁⁻+σ₂⁻)` is exact and the competition reduces to `{NO_JUMP, C_s}`. The
  `C_a` arm is the (declared, not-yet-implemented) `γ₁₂<γ` generalization — adding it is a second
  `TWO_SITE_COLLAPSE_FAMILIES` collapse term, not a change to the C_s path.
- **S2 cooperativity swept (c):** η∈[0,1]; no incidental device value — SWEEP.
- **S3 two-site window (c):** pairwise collective; triple-bath correlations exponentially suppressed.

## 6. Verification plan (serialized GPU; two phases)
**Phase A (channel-level, now):** `outputs/twin_validation/cert_m12_correlated_relaxation.py` —
hand-typed `L`; assert L1–L9 vs from-scratch dense-Liouvillian GT (build on the existing witness
`outputs/m12_correlated_2q_relaxation_fe_derivation_check.py`); `assemble_substep_channel` as the
dense-carrier-channel-under-test; falsifiers trip.
**Phase B (MCWF/MPS-trajectory seam, gated, careful):** add the 2-site joint-collapse path to
`_collapse_operator`/`_sample_joint_jump_or_nojump`; its cert = the carrier MCWF trajectory channel
reproduces the Phase-A channel (Monte-Carlo CI), AND the existing 1-site collapse tests (T1/T2/T1_UP)
stay green (no regression). Multi-builder + reviewer; faithfulness-first.

## 7. Status
- [x] Theory-first grounding (≥2 DIRECT-physical, peer-reviewed DOIs: Mlynek 10.1038/ncomms6186 +
  Cattaneo Ann. Phys. 533, 2100038; Ojanen arXiv-only supporting). Docs de-circularized; fabricated
  ref deleted; magnitude (c) bracketed.
- [x] Phase-A channel cert `outputs/twin_validation/cert_m12_correlated_relaxation.py` — serialized
  GPU, **ALL PASS**: entangled jump (residual 0), dark state (0), Dicke eigs {0,0,2γ,2γ}, carrier
  dense path == from-scratch Lindblad to 1.9e-16 (self-test pins vec convention), 1−F_e linear
  (collapse), joint≠independent 0.095; wrong-sign + legacy-toy falsifiers trip. Physics LOCKED.
- [ ] Phase-B MCWF/MPS 2-site joint-collapse seam + regression-safe carrier cert (the one genuine
  new-carrier-code piece; built carefully — multi-builder + reviewer, faithfulness-first, with
  Phase-A as oracle, and the existing 1-site collapse tests must stay green).
- [x] Multi-agent review (Phase-A): reviewer **SOUND** — reproduced all signatures, reran cert,
  verified both DOIs at source, confirmed non-circular + Phase-B honestly disclosed. Two MINOR items
  FIXED: cert now uses the project-standard `_choi_state_from_kraus`+`_state_fidelity` (Schumacher-
  Nielsen) metric (not a proxy); run-log captured (`cert_m12_correlated_relaxation.run.txt`).
- **M12 Phase-A (physics) DONE.** Phase-B (carrier trajectory seam) remains — built as a focused
  final-hardening step (execution-path extension; physics already certified).

## 8. Phase-B seam design (faithfulness-first, 2026-06-30 — before code)
**Why now:** Phase-B is the multi-site joint-collapse seam in the MCWF/MPS trajectory — the prerequisite
for **correlated-dissipative coupling** (shared-bath / collective relaxation) on the *scalable* carrier.
The correlated-*coherent* coupling already runs (Hamiltonian cluster-join); the dissipative side is
blocked on this seam.

**Faithfulness-first read (the exact 1-site hardwiring to generalize):** `_sample_joint_jump_or_nojump`
(axis1_mcwf_mps_execution.py:1288-1364) builds the no-jump and each jump candidate with
`mps.gate_(op, where=support[0], contract=True)` and `local_dim=local_dims[support[0]]` — **1-site
only**. `_collapse_operator` (1367-1396) builds a `(dim,dim)` 1-site op (raises on unknown family,
1396). `_nojump_first_order_kraus` (1399+) builds the 1-site no-jump `I − ½ c†c dt`. Collapse
allow-list (1839-1846) = `{T1,T1_UP,T2,RD,LEAK_SEEP_21,LEAK_HEAT_12}`. The proven **multi-site gate
application pattern** already exists at 1279-1283: `mps.gate_(g, where=support, contract="auto-mps",
max_bond=...)` for `len(support)>1`.

**The seam (minimal `len(support)` branch — 1-site path untouched, the HARD regression gate):**
1. New `_joint_collapse_operator(term, support, local_dims, device)` → builds the 2-site collective
   collapse `c = √γ_corr·(σ⁻⊗I + I⊗σ⁻)` on `(d_i·d_j)`, σ⁻ on the computational {0,1} block, **zero on
   leaked levels ≥2** (same embed discipline as the coherent families). `coeff` = `√γ_corr` (the
   Lindblad collapse op, exactly as `_collapse_operator` returns √rate·op for the 1-site families).
   **Leaked-partner embed — declared (c)-class modeling choice (5-model review finding #5, bounded).**
   With σ⁻ zero on levels ≥2 but the *partner* factor a full identity, when one site is leaked the
   collective op acts as identity on that site and as σ⁻ on the other: `c|2,1⟩ = √γ_corr·|2,0⟩` (the
   collective jump still relaxes the NON-leaked qubit; the leaked qubit is untouched). This is the
   intended behaviour for collective relaxation through the {0,1} channel of each qubit independently of
   the other's leakage occupancy; it is NOT a leakage-transport term (those are the dedicated `LEAK_*`
   families). Bound: the choice only matters when a qubit is in |2⟩ during a correlated-relaxation
   substep; in the qubit-window slice (local_dims=2, no leakage) it is inert, and in the qutrit arm the
   alternative (zeroing the collective op whenever either partner is leaked) differs only on the
   measure-zero leaked-during-collective-relaxation events — a (c)-class first-pass choice, swept/refined
   if the qutrit-arm correlated-relaxation rate proves load-bearing. Verified: `cert_m12_phaseB_secondary.py` S1.
2. New `_joint_nojump_first_order_kraus(term, dt, support, local_dims, device)` → `I_2site − ½ (c†c) dt`
   with `c` from (1).
3. `_sample_joint_jump_or_nojump`: branch on `len(support)` — `==1` keeps the existing path
   **logic-identical (re-indented into the `if`, behavior unchanged — not literally byte-for-byte)**;
   `==2` applies the no-jump/jump on `where=support, contract="auto-mps", max_bond=None` (exact; a
   single local 2-site collapse grows the bond by ≤×2, so exact contraction is cheap). Norms/sampling
   identical (a 2-site candidate is just another entry in the same competition).
4. Allow-list (1839): add `"CORR_RELAX"` (the 2-site joint-collapse family).
5. (Schedule-level *emission* of CORR_RELAX terms = a later selection-layer step, deferred like M11's
   emission; the Phase-B cert builds the term dict directly, as the M11/M12 certs do.)

**Oracle (anti-circular) + HARD gates:**
- **Oracle = the M12 Phase-A channel** (the dense `assemble_substep_channel([], [√γ(σ⁻⊗I+I⊗σ⁻)], dt)`
  channel, itself certified vs a from-scratch Lindbladian in Phase-A). The Phase-B trajectory, averaged
  over N MCWF shots, must reproduce that channel's observables: the **entangled-jump signature**
  (`|11>` → `(|01>+|10>)/√2` post-jump), the joint-vs-independent distinguishability, population decay
  — to within a √N Monte-Carlo CI.
- **HARD regression gate:** the existing 1-site collapse tests (T1/T2/T1_UP, the qutrit leakage seepage
  trajectory tests) MUST stay green (the `len(support)==1` path is byte-for-byte unchanged).
- Cert: `outputs/twin_validation/cert_m12_phaseB_trajectory.py`; multi-agent review after.

## 9. Phase-B status
- [x] seam implemented: `_joint_collapse_operator` + `_joint_nojump_first_order_kraus` (new), the
  `len(support)` branch in `_sample_joint_jump_or_nojump` (1-site path byte-unchanged), `CORR_RELAX`
  added to the collapse allow-list. 2-site applied via the proven `where=support, contract="auto-mps",
  max_bond=None` pattern.
- [x] trajectory cert `outputs/twin_validation/cert_m12_phaseB_trajectory.py` — **ALL PASS**: L1 op
  identity == Phase-A L (0.0); L2 no-jump == I−½L†Ldt (0.0); **L3 entangled jump on the real quimb MPS
  `|11>→(|01>+|10>)/√2` (residual 0.0)**; L4 subradiant dark state killed; L5 directed jumps; F1/F2
  falsifiers trip.
- [x] **ensemble→channel gate (the §8-registered HARD oracle) — CLOSED, not optional.**
  `outputs/twin_validation/cert_m12_phaseB_convergence.py` (5-model review remediation): the seam's own
  first-order microstep, taken to its deterministic ensemble limit and composed, reproduces the certified
  Phase-A Lindblad channel with first-order microstep convergence (process infidelity
  `1−F_e` via the standard `_choi_state_from_kraus`+`_state_fidelity`): mild γ·dt=0.1 → `1−F_e=4.96e-3`
  (m=1, GROSS pass) → `2.4e-7` (m=64), ~4×/doubling; the Choi convention is anchored to
  `_choi_state_from_kraus` (max|Δ|=0.0). **Epistemic correction:** the original §9 wording downgraded this
  §8-registered oracle to an "optional follow-up" and claimed the deterministic single-jump checks
  "already establish it" — that was a post-hoc weakening of a pre-registered gate (single-jump structure
  ≠ ensemble channel reproduction) and is retracted; the gate is now run and passes.
- [x] regression: trajectory core green — `regression_phaseB.log` **204 passed / 1 skipped** (schedule
  + qutrit leakage + MCWF convergence + connected-cluster + joint_lindbladian); 1-site T1/T2/T1_UP +
  leakage trajectory intact (the HARD no-regression gate holds).
- [x] multi-agent review: **SOUND**. Reviewer re-derived on GPU — operator-exact (0.0), gate_ reshape
  convention exact incl. non-adjacent (0,2), no-jump/jump balance O(dt²), 1st-order MCWF reproduces the
  from-scratch Phase-A Liouvillian (ratio 4.00), multi-term no-jump cross-term = standard O(dt²)
  microstep error (class (c), vanishes with microsteps); **full `tests/` suite exited 0** (1032
  collected, 0 errors). Fixes applied: `max_bond=None` rationale+latent-gap comment (code); "logic-
  identical (re-indented)" wording (§8.3). Optional follow-up (reviewer-confirmed independently, not
  yet in-cert): a large-N stochastic MC-vs-channel check exercising `_sample_index` over trajectories.
  **COMMIT HYGIENE (reviewer):** the working tree bundles M12 Phase-B WITH the earlier carrier-surgery
  (COH_H/XY/ZY/XZ/YZ/YX removal + deletion of tracked `test_m28_*`/`test_m32_*`). When committing,
  split into ≥2 commits: (i) carrier surgery + cut-mechanism test deletions, (ii) M12 Phase-B seam.

**M12 Phase-B (carrier trajectory seam) implemented + reviewed SOUND.** Schedule-level CORR_RELAX
*emission* (selection layer) remains a deferred follow-up; the cert drives the term dict directly.
