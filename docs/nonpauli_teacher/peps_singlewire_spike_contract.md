# RUNG-B feasibility spike — single-wire 2D PEPS trajectory carrier (registration + design contract)

> **THEORY-FIX REOPENED, 2026-07-13.** The single-wire geometry remains live, but every bond-
> plateau/FET/WTG/ZMT-to-record GO condition in this historical contract is suspended. `b=.9` is a
> project evidence point, not a device-grounded readout value, and the registered N=8/R=40 run was
> not completed. Current authorities: ADR 0011,
> [`../NUMERICAL_PROVENANCE.md`](../NUMERICAL_PROVENANCE.md), and the long-range literature closure.

**Version: v1.0 REGISTERED (2026-07-10). Blockers = 0 after three adversarial rounds;
this document now governs the spike build. Amendments from here follow the parent
contracts' convention: findings + adjudications appended, bands never re-fit.**

**Red-team round 3 (targeted verifier — verdict READY):** the rewritten WP1 criterion
replayed against five adversarial bond sequences (monotone grower, clean/noisy
saturator, late saturator, step-after-plateau) — correct verdict on all five, NO
wrong-GO path; consistency regression sweep PASS across all round-2 edits; §7
arithmetic re-derived exact. Folded amendments: RT3-F1 (window-max test gets ±1
noise slack + declared drift-resolution limit), RT3-F2 (R=60 extension re-certifies
ALL trajectories), RT3-F3 (W_max=4·D_abort reconciled — pass-1 precut bounds every
metric leg; 23.8 GiB is the uncapped counterfactual), RT3-F4 (R-fence carve-out
covers the extension), RT3-F5/F6/F8/F9 (projected-peak formula, D_abort comparator,
floor-violation remediation family, rider arms share the horizon).**

**Red-team round 2 (3 focused lenses, 28 findings: 2 BLOCKER, 13 amendments, 13 notes —
6 of them CONFIRMED-RESOLVED verdicts on round-1 fixes; ALL adopted):** RT2-B1 the WP1
plateau criterion was boundary-broken (overlapping windows at r*=30 certified a monotone
grower — §5 criterion rewritten with disjoint detection/confirmation windows + a
registered R=60 extension); R2-1 the d5 cross-route residual had no registered floor
(§6.2 floor table added); the three-lens D_abort/VRAM convergence (D_abort 64→40,
pre-metric evaluation, VRAM tripwire, per-round flush — §6.1/§7); the SW4 staged-N
conflict ladder; the referee-budget correction to the g11 measured numbers + the
engine-freed-first sequencing pin; the reevolve raw-s input pin; the χ_b sequencing +
mid-run failure semantics; the ε_l discriminating known-answer (the product-state test
is a vacuous smoke, replaced as anchor by a hand-computable 2×2 loop); the (a)-identity
grade split (structural-exact vs caps-read floors); tag hygiene (AM5→resolvable
citation, A-lane/E2-sub declared, parent prefixes); TOL_TRACE bound to SW2;
window_binding adjudication aligned; WP2 measurement ownership pinned.

**Red-team round 1 (4 un-led lenses, 35 findings: 8 BLOCKER-class after dedup → 4 unique,
19 amendments, 8 notes — ALL adopted):** RT1-B1 stab-sampling direction contradiction
(pepo vs mps_forward convention — §2/§3 re-pinned, SW6 killer added); RT1-B2 terminal
readout site-set contradiction (all-data mps_forward law pinned; support-only kept
distribution-level only); RT1-B3 SW4 referee infeasible (record_oracle full-9q ≈50–100 GB
— re-registered to the per-record DMPathEvaluator route); RT1-B4 full_joint obs 50/50
b-blind split (FORBIDDEN verbatim, A4 biased-b composition pinned); plus the closure-
vacuity redesign (§6.2), the dynamic-ε window invariant (§6.1), the 2^multiplicity
codestate bond law (SW7), the honest Manabe-anchor restatement (WP1), the ε_l
known-answer checks (§6.3), the staged-N bench (SW4), fence pins for SW5/SW9, and the
budget/typo/floor notes (§4/§7/§8).

Governing entry point: `docs/nonpauli_teacher/HANDOFF_ancilla_explicit_rebuild_2026-07-10.md`
(§5 action #2 — the promoted crux test). Parent documents still in force where cited:
`pepo_engine_rung1_contract.md` (v4.3, "CONTRACT"), `pepo_d5d7_carrier_prereg.md`
(v2.5, "PREREG"). This document is the NEW registration the handoff §3.4 requires
(theory-first + full red-team contract-build) for the single-wire spike.

**The one question this spike answers (the crux):** does the per-edge bond of a
SINGLE-WIRE (pure-state trajectory) 2D PEPS stay bounded (saturate) under multi-round
noisy+leaky syndrome extraction on the rotated d×d XZZX patch? Everything in the d5/d7
carrier plan hinges on it. Stage (2b-i) certifies the single-wire 2D representation is
FAITHFUL at d3 against the exact referee; stage (2b-ii) runs the registered bet at d5.

**Namespace disambiguation (binding for this document):**
- "E1-tf" = the F-SEL-1 theory-fix probe registry (the 1e-15 forced-branch engine
  exoneration, CONTRACT "F-SEL-1 UPDATE"); "E1-sub" = the rung-0 substrate probe
  registry (PREREG rung-0 appendix). Bare "E1" is not used here.
- "prereg-C8" = the stim-Clifford wiring anchor (PREREG §2A C8); "ADR0010-C8" = the
  mps_forward zero-truncation bit-for-bit anchor (`mps_forward.py` module docstring).
- Spike tags: verified structural facts **SF1..SF12**, gates **SW0..SW9**, registered
  predictions **WP1..WP5**, simplification fences **SW-S1..SW-S8**, findings
  **F-SW-\<name\>**. Parent tags (F1–F9, S1–S11, C1–C10, G1.x, P1–P8, the rung-1
  builder-lane tags A1–A4 — "the A3 lesson" = production-path-is-the-source, "the A4
  composition" = the biased-b obs referee of G1.1 — and the rung-0 substrate results
  E1-sub/E2-sub/E3-sub) are cited with their document prefix where collision is
  possible (prereg-C4/C5/C8, prereg-S1/S8/S9/S10/S11); the leak tie-break registry is
  cited by its home `docs/twin_validation/batched_mps_backend_prereg.md` (the
  `_leak_sample` docstring's "TIE-BREAK REGISTRY").

---

## §0 Verified structural facts (SF — each checked in source during Stage-0 grounding, 2026-07-10)

Cited by NAMED symbol (functions/classes), never line numbers. "pepo" =
`src/error_coupling_simulator/carrier/pepo/`; "mps_forward" =
`src/qec_twin/forward/scalable/mps_forward.py`; "qutrit_dm" =
`src/error_coupling_simulator/carrier/exact/qutrit_dm.py`.

- **SF1 — the codestate ket layer is already single-wire.** `layout.build_codestate_pepo`
  builds a PURE-STATE ket PEPS in steps 1–3 (H-spread seed `(1,1,0)/√2`; stabilizer
  projectors as bond-2 W chains `_apply_chain_operator` with `W_1=[I/2, c.P_1/2]`,
  `W_mid=diag(I,P_j)`, `W_last=[I,P_w]` along `plaquette_path`, applied in
  `sched.stabilizers` order then the logical; logical projector `(I+(−1)^m Z_L)/2`);
  ket⊗bra fusion happens ONLY in step 4. `_ket_norm_sq` is the single-layer ⟨ψ|ψ⟩
  transfer contraction. The single-wire codestate builder = steps 1–3 + unit-NORM
  normalization (the existing `trace_scale = tr_m**(−1/n)` is density-matrix-specific;
  the single-wire constant is `tr_m**(−1/(2n))` per site — NEW code, small). Chain legs
  fuse MULTIPLICATIVELY into the grid-edge bond (`_fuse_pair` — no compression), so an
  edge traversed by k chains carries raw dim exactly **2^k** (RT1: not 2·k).
- **SF2 — layout geometry is d-generic.** `PepoLayout.from_sched` (diamond→grid
  `u'=(x+y)/2−min, v'=(x−y)/2−min`, asserted integral/unique/`{0..d−1}²`,
  `d=isqrt(n_data)`), `neighbors`, `grid_edges`, `plaquette_path` (min-crossing +
  lexicographic tie-break) contain no physical-leg dimension and no d3 constant in code
  logic. The only d3 pins: the FROZEN cut site list `(0,1,2)` (documentation of the rule's
  d3 output) and `dense_rho`'s `n_data ≤ 9` referee-bridge assert.
- **SF3 — the doubled-wire squaring is localized and removable.** `dynamics._fused_stab_diag`
  builds `dm = v[:,None]*v[None,:]` (the ket⊗bra square of `v = √e`); `_tt_rank_bounds`
  documents the squared bound `(2·min(w_L,w_R)+1)²`. The single-wire object is the
  UNSQUARED diagonal `v = √e` over `(3,)*w`, TT rank bound `2·min(w_L,w_R)+1` — i.e.
  **(3,5,3) for w=4, (3,) for w=2** — by the same matricization argument (the parent
  derivation's square root; RT1 re-derived independently: distinct left-product values
  of w_L factors from {+1,−1,c} = 2·w_L+1 at generic c). Moreover the doubled diagonal
  is exactly the Kronecker square of the single-wire diagonal (rank₉ = rank₃² at every
  cut), so the parent's EXECUTED in-domain equality assert at b=0.9 forces single-wire
  equality — a below-bound single-wire measurement is an implementation bug, never a
  mechanism note (RT1; carried into WP3). `_tt_svd` is generic except a literal
  local-dim 9 (parametrize 9→3); `_insert_core` and the `apply_stab_branch` skeleton
  (H sandwich, fresh-uuid TT bonds, `fuse_multibonds`) are leg-dimension-agnostic.
- **SF4 — the F2 operator form is shared and referee-mirrored.** Per-site diagonal
  `e_i = ½(1+(−1)^s ∏_q d_q)`, `d_q = +1 (t=0), −1 (t=1), d2 (t=2)` with
  `d2 = 1−2b` (arm A/C), `+1` (B1), `−1` (B2); X supports H-rotated OUTSIDE the TT.
  Identical in `dynamics._fused_stab_diag`/`_leaked_weight`, in
  `mps_forward._apply_sqrt_Es`/`_arm_d2`, and in the referee
  `qutrit_dm._povm_diag_weight`. `mps_forward` applies exactly the single-wire version
  (`sqrt_es` diagonal gate) — the standing proof the compiled √E_s is truncatable
  single-wire at d3.
- **SF5 — the E1-tf certification pattern.** Forced-outcome branches: literal outcome
  passed to the engine branch builder AND to `qutrit_dm.project_stabilizer(paulis,
  outcome, b, arm)`, BOTH sides left UNNORMALIZED; compare the dense reconstruction
  max-abs elementwise plus branch traces. Bars are three distinct numbers:
  unit-gate bar 1e-12 (`TOL_EXACT`), chain-probe registered bar 1e-8 (class (b)),
  measured outcome 1e-15/1e-16. The referee is a bare `QutritDM` from
  `SvSampler.within_cycle_dm_engine(sched)` (9 data qutrits, compiled POVM, no ancilla).
  `DMPathEvaluator` (`qec_twin/audit/floor_backend.py`) is the RECORD-level referee
  (the rung-1 G1.1 route): `reevolve_onto_records(prob, m, records)` deterministically
  re-evolves onto fixed records at chunk B=1, `path_trace` returns `P(s|m)` — the
  memory-light per-record exact-probability seam (RT1-B3: this, not `record_oracle`
  at full-9q, is the feasible record referee).
- **SF6 — a pure-state engine cannot apply nonselective channels.** The E1-tf probe drove
  LEAK as a Kraus-sum superop (`_kraus_superop`) — no single-wire analog exists;
  `nonselective_round` (branch sum) likewise. The single-wire replacements are
  trajectory Kraus SELECTION (mps_forward `_leak_sample`: branch k w.p.
  `p_k = ⟨ψ|K_k†K_k|ψ⟩`, registered tie-break "first k with `u·tot ≤ cumsum_k`
  (non-strict ≤), fallback K−1") and Born-sampled selective branches. Certification
  therefore splits into a state level (forced Kraus index + forced outcome ⇒
  deterministic pure-state chain vs referee single-Kraus DM update) and a record level
  (trajectory-ensemble statistics vs exact per-record probabilities, z-scored).
  Referee-side forced legs: `qutrit_dm.apply_within_cycle_premeasure` has NO
  forced-branch mode (it always applies the full Kraus list) — the SW2 referee driver
  is a manual per-token walk (§6.4), never the premeasure convenience method (RT1).
- **SF7 — the referee API supports everything SW needs.** `qutrit_dm.project_stabilizer`
  (unnormalized branch + probability), `apply_channel(kraus, site)` (accepts a
  single-element Kraus list — no CPTP assert — giving the unnormalized forced-branch
  DM update `K ρ K†`), `apply_gate`/`single_qudit_gate` (leaked levels untouched),
  `record_oracle` (exact record law — but its depth-`len(stabs)·R` per-level DM-clone
  recursion is INFEASIBLE at full-9q: ≈50 GB at R=1, ≈100+ GB at R=2, declared as
  routing data in `certify/anchors/dm_oracle.py`; feasible only on sub-registers
  n ≲ 7 — RT1-B3), `syndrome_distribution`, `resolve_readout_bias`, `init_logical`.
  `record_oracle.full_joint`'s obs component comes from `logical_distribution`, which
  splits leaked-support mass 50/50 INDEPENDENT of b — the parent contract FORBIDS it
  as the obs referee, and so does this one (RT1-B4). QutritDM is complex128-enforced,
  has NO internal RNG, and its chunked `apply_channel` declares reproducibility class
  ≤1e-13 vs unchunked (BLAS order) — the E1-tf 1e-15 outcome was measured, not
  guaranteed.
- **SF8 — d5 geometry exists and is execution-verified.** Google dataset
  `google_105Q_surface_code_d3_d5_d7` ships 4 d5 patches (25 data + 24 measure);
  `outputs/teacher_prereg/p9_mps_d5_forward_validate.py` already ran
  `parse_xzzx_circuit` (+ `with_within_cycle_streams`) green at `n_data=25 n_stab=24`
  on `d5_at_q6_5` (X basis, r01 + r10). `parse_xzzx_circuit` is d-generic
  (metadata-coordinate-driven); ONE d3-gated self-check (the 4-distinct-H-patterns
  assert) is silently skipped at `n_data≠9` — the spike adds a d-generic replacement
  (SW7). There is NO d5 exact referee: `(3^25)²·16 B` has no code path anywhere
  (confirmed absent), and no synthetic XZZX schedule constructor exists
  (`frontend/xzzx_code.py` is 3×3-only and produces a different type).
- **SF9 — boundary-MPS machinery is layer-count-agnostic except the caps.** The
  column-sweep/absorb/fit skeleton (`sampler._columns`, `_absorb_rows`,
  `_fit_compress_rows` with the torch-cuda-c128 initial-guess fix, `NormCache`
  reverse pass, `expect_site_caps` forward pass) never inspects leg dimension; ONLY
  `_trace_cap`/`_cap_vector`/`_capped_column_tn` encode the doubled-wire
  `Tr(ρ·Π)` semantics. The single-wire read `⟨ψ|Π|ψ⟩` is the DOUBLE-layer network
  (ket + conj-bra with per-site 3×3 ops sandwiched); the per-column tensor
  construction is the only replacement. The two-term identity
  `⟨E_s⟩ = ½⟨ψ|ψ⟩ + ½(−1)^s⟨ψ|⊗_q M_q|ψ⟩` (`stab_expectation` docstring) is an
  operator identity and transfers verbatim — with the RT1 corollary that any (q0,q1)
  derived from the same two contractions (N and M) satisfies q0+q1=N IDENTICALLY, so
  a q0+q1 "closure" is structurally vacuous; the genuine per-read accuracy
  instruments are pinned in §6.2. The boundary-MPS fit initial guess uses UNSEEDED
  `torch.randn` — a declared nondeterminism source (SW-S7).
- **SF10 — truncation + diagnostics carry over.** `svd_precut_bond`, `ntu_truncate`
  (QR-isometrize, exact-rank fast path, NTU metric + alternating pinv, v4.2
  precompression, v4.3 env bounding, greedy deterministic contraction),
  `_cluster_metric` (its two-layer ket+conj construction IS the standard pure-state
  norm metric), `gap_rank` (UNSQUARED-σ rule), and the full ledger convention
  (discarded = squared-σ tail of the LOCAL insertion spectrum — RELATIVE, gauge-local)
  operate on named bonds and never inspect the physical leg. Neither reused function
  has a dynamic-ε mode (both take fixed integer targets) — the dynamic policy wrapper
  is NEW code with its own invariant (§6.1). The loop-closed rank probe method
  (`pepo_rung1_probe_loop_rank.py`) ports to single-wire with 3-dim caps.
- **SF11 — record objects and RNG discipline are fixed by the existing arm.**
  `s_to_det`/`det_to_s` (round-major fold, `seam.py` convention), `ShotSet` +
  `pack_shots` (LSB-first, trailing obs byte), `ShotSet.to_det_obs` returns RAW
  per-round syndrome bits under the key "det" (the XOR fold lives in
  `seam.teacher_shots_to_events`) — the spike pins which meaning each consumer gets.
  RNG: per-shot `np.random.default_rng((base_seed, shot))`, Section-5 normative draw
  order (gates draw nothing; one uniform per LEAK site-op; one per stabilizer;
  n_data at terminal). Sampling maps (the SW5 anchor's conventions, binding):
  stabilizer `sbit = 0 iff u < p0` (STRICT <), `p0 = ½(1+⟨P⟩)`
  (`mps_forward._measure_stabilizer`); terminal reads ALL n_data qutrits in ENGINE
  order, one uniform each, `bit = 1 iff u < p1 = ⟨F1⟩/⟨ψ|ψ⟩`, √F_bit collapse per
  site, obs = parity(logical-support bits) XOR m (`mps_forward._terminal_readout`
  hard2). The archived pepo `born_sample_round` uses the OPPOSITE direction
  (`outcome = 1 iff u < p1`) and pepo `terminal_readout_obs` reads the SUPPORT ONLY —
  neither is the spike's sampling convention (RT1-B1/B2). `MpsTruncationLedger`
  records discarded weight but NO per-round bond profile — the saturation instrument
  is a new hook (SW8).
- **SF12 — literature anchors, exactly as strong as the sources.** (i) Manabe
  2308.08186 (original read 2026-07-10): dynamic-χ policy = "2-norm of the vector of
  truncated singular values" ≤ 1e-6 (rep code) / 1e-4 (thin surface) per truncation
  step (normalization at truncation time NOT stated — declared assumption in §2);
  Fig. 6 (1D rep code d=7..99, 99 rounds, worst cell T=100, θ=0.1π, γ=0,
  θ_spread=0.3π, no reset): bond "increase[s] linearly at initial rounds and
  saturate[s]"; χ constant in d except "finite-size effects for systems with d ≲ 50";
  per-d plateau values NOT in the text (y-axis reaches 60; the Fig.-5 whole-run
  average at that cell is 64.83, averaged over 10⁴ trajectories — an AVERAGE
  statistic, not a max); thin 3×7 surface at 7 rounds: avg χ ≈ 9.1–21.1,
  "not saturated"; saturation mechanism is stated as inference (measurement-induced
  return to low-entangled states), not a theorem. The "~20–30 rounds" onset figure
  comes from the raster-read note (figure read), not the text — cited only with that
  provenance. Noise-strength comparison to the p1c cell (RT1-corrected): Manabe's
  per-round leak generation ≈ sin²(θ/2) ≈ 2.45e-2 at θ=0.1π vs WG L1 = 5e-3 —
  **≈5× stronger**, PLUS the coherent leakage-spreading interaction (θ_spread=0.3π,
  conditional on a leaked neighbor) that our compiled semantics lacks entirely (the
  qualitatively stronger entanglement generator). NOT "orders of magnitude".
  (ii) D–P 1607.06460 (foundational): codestate/check insertions are LOCAL bond-2 W tensors;
  boundary-MPS χ_b=8 reproduces the exact 153-qubit logical channel — single-round,
  PERFECT measurement, single-LAYER trace network (our double-layer norm network is a
  declared extrapolation). (iii) Rudolph–Tindall 2507.11424 (original read
  2026-07-10): ε_l = 1−|λ^l_1|/Σ_i|λ^l_i| (Eq. 4), λ from the loop transfer matrix
  with BP messages on the loop boundary and one edge cut open, on the NORM network;
  bound 0 ≤ ε ≤ 1−1/χ²; full spectrum O(N·χ⁶); the paper does NOT specify the
  cut-edge selection rule nor the message gauge (our conventions, §6.3);
  Willow-vs-heavy-hex ε gap is "many orders of magnitude" (numeric per-depth values
  did not survive pdftotext — NOT citable); "R ∼ 75" boundary-MPS bond needed at
  L=15 Trotter layers, χ=20, Willow, for converged LOCAL expectations. ALL R–T
  numbers are for Heisenberg-quench Trotter states, NOT codestates — transfer is a
  DECLARED EXTRAPOLATION. (iv) cTJM 2607.01323 §IV.3: `a·I+b·P` has an exact bond-2
  MPO (Pauli-string scope); our biased-b √E_s is NOT of that form (the |2⟩ weight
  1−2b breaks it) — the bond-2 theorem informs the mechanism story, it is not an
  engine bound here.

---

## §1 Scope, decisions, fences

### 1.1 Decisions (each with its epistemic class)

- **D1 (c, design):** The spike stays INSIDE the S10 compiled/data-register semantics
  — the SAME compiled √E_s POVM the rung-1 engine and `mps_forward` use; NO ancilla
  qutrits. Rationale (HANDOFF §0): single-wire vs doubled-wire is the primary axis and
  `mps_forward` is the standing d3 proof compiled-√E_s works single-wire;
  ancilla-explicit is a secondary lever not shown to be required. S10/C10 stay CLOSED
  for this spike; every artifact carries the "compiled/data-register" label. If the
  spike's bet FAILS, ancilla-explicit re-enters through the adjudication menu (WP1).
- **D2 (c, design):** Arm A only (the p1c cell: `WG_L1_TARGET=5.0e-3, G_SEEP=0.09,
  G_HEAT=0.0, B_BIAS=0.9, ARM="A"` — the rung-1 test constants, kept for
  comparability with the frozen rung-1 references). Arm C (leak-flag dephase) is
  FENCED OUT (SW-S2).
- **D3 (c, design):** Representation: qutrit single-wire PEPS on the d×d data grid —
  per-site tensor rank ≤ 5 (phys dim 3 + ≤4 virtual bonds), quimb TensorNetwork with
  torch-cuda-complex128 backing (rung-0 E1-sub/E2-sub verified quimb 1.14.0 preserves
  the backing), named legs `k{pos}` (now dim 3) and bonds `B{a}_{b}` — the pepo naming
  carried over so the reused machinery works unchanged.
- **D4 (c, design):** Reuse-over-rewrite, per the Stage-0 verdict table (§3):
  layout/plaquette-path VERBATIM import; codestate = pepo steps 1–3 + norm constant;
  TT machinery ported with local-dim parametrized; boundary-MPS skeleton reused with
  double-layer column tensors; NTU/precut/gap_rank/ledger reused; `s_to_det`/`det_to_s`
  and ShotSet packing VERBATIM import; RNG discipline (base_seed, shot) + Section-5
  order VERBATIM. The engine stays referee-independent: gates/Hadamard built locally
  BY FORMULA (the dynamics/sampler discipline), NOT imported from qutrit_dm (the one
  existing layout→referee import, `qudit_hadamard` for the seed, is replaced by a
  local formula in the spike's codestate module).
- **D5 (c, design):** Module placement: NEW package
  `src/error_coupling_simulator/carrier/peps/` (state + codestate; trajectory ops;
  double-layer contraction; diagnostics), registered tests `tests/test_peps_spike.py`,
  gate/evidence scripts `outputs/nonpauli_teacher/peps_spike_*` (scripted-execution
  discipline). The pepo package stays ARCHIVED and untouched; the spike imports its
  representation-agnostic pieces rather than forking them (single source for
  layout/truncation). src/tests commits wait for explicit user confirmation; docs +
  outputs flow normally.
- **D6 (c, design):** d5 schedule route = the p9 route VERBATIM: `default_r01_paths` /
  `default_r10_paths(patch="d5_at_q6_5", basis="X")` → `parse_xzzx_circuit(verify=True)`
  → `with_within_cycle_streams(...)` (SF8). Replication patches opportunistic, not
  gating.
- **D7 (c, design):** Trajectory semantics = mps_forward's, transplanted to 2D and
  pinned VERBATIM (SF11 sampling maps): per round, PRE-measure token stream (1-site
  gates exact + LEAK Kraus-sampled, both bond-inert on a PEPS), then the n_stab
  stabilizers in schedule order (parity read via the double-layer caps →
  `sbit = 0 iff u < p0` STRICT < → √E_s TT insertion on the plaquette path →
  truncation), then POST-measure frame; terminal readout = ALL n_data qutrits in
  ENGINE order, one uniform each, `bit = 1 iff u < p1`, √F_bit collapse per site,
  X-logical-flagged sites H-rotated exactly as mps_forward's hard2 mode, obs =
  parity(logical-support bits) XOR m. The archived pepo sampling directions are NOT
  used (SF11). Draws: identical Section-5 order.

### 1.2 Stage structure

- **(2b-i) d3 correctness (gates SW0–SW6):** single-wire d3 PEPS codestate + noisy
  rounds on the real `d3_at_q6_7` patch; state-level forced-branch certification vs
  the exact QutritDM referee (E1-tf pattern, SF5/SF6); record-level trajectory-ensemble
  certification vs per-record exact probabilities (the G1.1 route, SF5); KILLER set.
  ALL gates predicted PASS (predict-before-measure; a miss is a finding).
- **(2b-ii) d5 bet (gates SW7–SW9, predictions WP1/WP2):** d5 codestate structural
  cert; the bond-saturation measurement under the registered dynamic-D policy; the
  ε_l loop-correlation cost measurement. NO record-law claim at d5 (SW-S4).

### 1.3 Scope fences (SW-S) — declared + bounded simplifications

- **SW-S1 (inherits prereg-S10/C10):** compiled/data-register semantics; no ancilla,
  no ancilla leakage/propagation/readout error; every artifact labeled. Class (c)
  fence; deviation-from-physical-circuit bounded exactly as the parent (C10).
- **SW-S2:** arm A only; arm C trajectory unraveling deferred (route named: the
  mps_forward leak-flag draws). Class (c). Bound: none needed — arm C is out of every
  SW gate's scope; no arm-C claim is made.
- **SW-S3:** boundary-MPS contraction is truncated at χ_b (norm pass R_n, sample pass
  R_x). Bound: the §6.2 per-read accuracy instruments (cross-route residual +
  χ_b-doubling deltas — RT1: the naive q0+q1 closure is vacuous and is NOT used as a
  bound) + the R-sweep convergence protocol including an EVOLVED probe state. Class
  (c) policy + (a) ledger.
- **SW-S4:** NO d5 exact referee exists (SF8). d5 claims are BOND/COST claims only;
  d5 record-law claims are OUT (rung-2 territory, gated on G1.8's S11 bound). The d5
  cross-checks (SW9 stim wiring; codestate structural cert) certify wiring and the
  codestate, never the noisy record law. Class (c) fence.
- **SW-S5:** record-level gates are Monte-Carlo (trajectory ensemble) — statistical
  bars only (per-class multinomial z ≤ 4 against exact per-record probabilities, the
  G1.1 convention); no 1e-15 claim exists at the record level. The 1e-15-grade claims
  live ONLY at the state level (forced branches). Class (c) convention.
- **SW-S6 (the S1 lesson, restated for the instrument):** the dynamic-D policy is a
  PER-TRUNCATION LOCAL rule (squared-σ tail per cut, §6.1 invariant covering BOTH
  passes), executed by non-optimal PEPS truncation (local SVD precut + NTU). The
  measured D*(ε) is instrument-relative and UPPER-bounds the representation-optimal
  bond at matched local error — valid ONLY because the §6.1 invariant bounds the
  TOTAL per-cut discard (precut included) by ε_spike (RT1: an unbounded precut window
  would invert this argument). A suboptimal truncator that still saturates is
  conservative evidence FOR feasibility; a growing D under this instrument does NOT
  prove no bounded-D representation exists (adjudication path (A') in WP1). Class (c).
- **SW-S7:** declared nondeterminism sources: (i) the boundary-MPS fit initial guess
  (unseeded `torch.randn` — SF9) — the spike seeds it per read so gate runs are
  replayable; (ii) referee chunked-apply reproducibility class 1e-13 (SF7); the SW2
  bar (1e-8) sits far above it, and the SW0/SW1 1e-12 bars sit 10× above it — the
  expected residual is ~1e-15 (E1-tf precedent); a measured residual landing in
  (1e-13, 1e-12] is EVIL-MARGINAL territory and is adjudicated as a finding against
  the referee's declared reproducibility class, never a tolerance bump (RT1). Class (c).
- **SW-S8:** GPU-only (S8 inherited: complex128, no fp32 anywhere in tails/ledgers),
  serial GPU (user's live desktop, no concurrent jobs), scripted-execution discipline
  for every run.

### 1.4 Non-goals (verbatim-level fences from the parents that stay in force)

No d7 claim; no DEM/decoder/LER in the validity chain (LER is the product); no
Pauli-twirl anywhere in the leakage path; no quantum-bath/notion-3 content; R > 10
RECORD-error claims need re-registration (prereg §9). R-fence application (RT1): the
d5 SW8 run at R=40 (and its registered R=60 extension — RT3-F4) is a
resource/entanglement measurement, not a record-error claim —
the carve-out covers SW8 ONLY; SW9 (a record-level statistical check) is pinned to its
own R ≤ 10 mechanism-off run and NEVER consumes SW8's records; SW4/SW5 run at
R ∈ {1,2}.

---

## §2 Representation + invariants (per-op pre/post-condition table)

**PepsState (new, `carrier/peps/`):** quimb TensorNetwork; per grid position `pos` one
tensor tagged `Q{pos}` with physical leg `k{pos}` of dim **3** (single-wire), virtual
bonds `B{a}_{b}` on every grid edge (dim 1 when structurally empty), rank ≤ 5;
torch-cuda-complex128 ALWAYS (raise otherwise); ledger = list of dict entries in the
pepo convention (discarded = SQUARED-σ tail; norm shifts logged); NO global
gauge/canonical form tracked. Positivity is STRUCTURAL (pure state) — the C3
negativity machinery is intentionally absent; its audit role is replaced by the §6.2
per-read accuracy instruments + the norm ledger.

| Op | Pre | Post | Bond effect | Draws |
|---|---|---|---|---|
| `build_codestate_peps(sched, m)` | real patch sched | unit-norm codestate; |2⟩-mass STRUCTURALLY exact (the k=2 slice of every site tensor is exactly 0.0 — (a) zero-tolerance on tensors, survives any contraction); ⟨S_g⟩=+1 ∀g, ⟨Z_L⟩=(−1)^m ((a) identities READ at the §4 declared caps floors — prereg-C5); per-edge raw dim == 2^(chain multiplicity through that edge) ((a) construction identity, SF1) | D=2 W-chain insertions, fused multiplicatively | 0 |
| `apply_gate_1site(U, pos)` | U 3×3 unitary (local formula table = `_qutrit_gate` convention: leaked level untouched) | ψ←U_pos ψ, norm unchanged | none (bond-inert) | 0 |
| `leak_sample(K, pos, u)` | ΣK†K=I to 1e-12 (prereg-C4) | ψ←K_k ψ/√p_k; branch k = first k with u·tot ≤ cumsum_k (non-strict ≤, fallback K−1 — the `batched_mps_backend_prereg` tie-break registry / `_leak_sample` docstring, verbatim) | none (single-site) | 1 |
| `stab_tt_singlewire(paulis, outcome, b, arm)` | X/Z-only support, outcome∈{0,1}, arm A/B1/B2 | TT of the UNSQUARED diag √e; ranks ≤ (3,5,3) w=4 / (3,) w=2 (SF3, class (a) bound; measured ranks ledgered) | builds cores only | 0 |
| `apply_stab_branch(state, tt)` | grid-adjacent path | H sandwich outside TT; unnormalized √E_s ψ | path bonds × TT ranks; NO truncation inside | 0 |
| `born_read_stab(state, stab)` | fresh NormCache | (N, M) reads via the two-term identity; `p0 = clamp((½N+½M)/N)` when s-sign is +1 on outcome 0 (i.e. p0 from e with s=0); §6.2 accuracy residuals ledgered | none | 0 |
| `sample_stab(state, stab, u)` | born_read done | **`sbit = 0 iff u < p0` (STRICT <, the mps_forward convention — SF11; the archived pepo direction is FORBIDDEN)**; branch applied; two-pass truncation under the §6.1 invariant; renormalize to unit norm, ledger entry | grown then truncated to policy | 1 |
| `truncate_bond_policy(state, bond)` | policy = dynamic-ε or D_cap arm (declared per run) | TOTAL discarded (precut + policy cut, squared-σ) ≤ ε_spike per §6.1 (dynamic arm) | ≤ policy | 0 |
| `terminal_readout(state, ...)` | — | reads ALL n_data qutrits in ENGINE order (one uniform each, `bit=1 iff u<p1`, √F_bit collapse; ALL X-logical sites H-rotated UP-FRONT before the first read, as mps_forward hard2 — value-identical to per-site rotation, disjoint sites); **obs PARITY over the logical support only** XOR m; state consumed | none (caps reads + 1-site collapses) | n_data |
| `bond_profile(state)` | — | {edge → dim} snapshot (the SW8 instrument; read per round-end) | none | 0 |
| `eps_l(state)` | norm network of current ψ | per-loop ε_l table (§6.3 conventions incl. known-answer checks) | none | 0 |

Units table (binding): discarded weight + ε_spike are SQUARED-σ scale, RELATIVE
(normalized by the local insertion spectrum's Σσ²); `gap_rank` ratios are UNSQUARED σ;
Manabe's threshold τ_M ("2-norm of truncated singular values") maps as
**ε(squared-σ) = τ_M²** — Manabe 1e-6 ↔ our 1e-12, Manabe 1e-4 ↔ our 1e-8 — under the
DECLARED ASSUMPTION that τ_M is measured on a unit-normalized canonical-form 1D
spectrum (standard TEBD; Manabe's normalization at truncation is not stated), while
our ε_spike is the relative tail of the LOCAL 2D insertion spectrum in a non-canonical
gauge: the map transfers the threshold GRADE, not an identical quantity (declared
extrapolation, same class as the χ-vs-D declaration) (RT1). All norms on
unit-normalized states unless a row says unnormalized.

---

## §3 Op registry — every new unit with its referee + tie-break/guard semantics

| New unit | Equivalent-to referee | Semantics pinned |
|---|---|---|
| codestate steps 1–3 (ported) | `QutritDM.init_logical(m)` dense ρ (via |ψ⟩⟨ψ| bridge) | projector order = `sched.stabilizers` then logical (the oracle's order); seed H|0⟩ by LOCAL formula; direct equality expected (same real projector formula, no phase quotient — a phase mismatch is a FINDING, not a tolerance bump) |
| `dense_psi(state)` (d3 bridge) | `layout.dense_rho` convention | engine position 0 = MOST-significant qutrit factor; n_data ≤ 9 assert kept |
| single-wire TT (`_tt_svd` with local-dim 3) | parent `_tt_svd` at dim 9 (structure), rank bound SF3 | per-SVD drop σ ≤ 1e-12·σ_1; assert rank ≤ bound ALWAYS; measured equality expected at (arm A, b=0.9) via the Kronecker-square identity (WP3 — below-bound = porting bug) |
| `apply_stab_branch` (ported) | `QutritDM.project_stabilizer` unnormalized | H sandwich order identical to parent; arm A only |
| `leak_sample` | mps_forward `_leak_sample` value contract | tie-break registry (`batched_mps_backend_prereg`) VERBATIM (non-strict ≤, fallback K−1); p_k from the double-layer 1-site RDM read |
| `sample_stab` | mps_forward `_measure_stabilizer` value contract | **`sbit = 0 iff u < p0` (STRICT <)** — the SW5 anchor's convention; direction-parity killer in SW6 |
| double-layer caps (`_capped_column_tn` replacement) | parent single-layer caps at matched reads | column convention (v=c columns, ROW{u} tags) identical; fit = `tensor_network_1d_compress(method="fit", bsz=1)` with the c128 guess fix, seeded (SW-S7) |
| `terminal_readout` | mps_forward `_terminal_readout` (hard2) value contract | ALL n_data sites, engine order, √F_bit collapse; `F1=|1⟩⟨1|+b|2⟩⟨2|`, `F0=|0⟩⟨0|+(1−b)|2⟩⟨2|`; obs = parity(logical support) XOR m. The pepo support-only enumeration (`terminal_readout_obs_prob` port) is retained ONLY as the distribution-level exact-P(obs) seam — valid because product-POVM outcome marginals on disjoint sites are unchanged by measuring the complement ((a), one-line theorem); NEVER a byte-level referee |
| `s_to_det`/`det_to_s`, ShotSet packing | VERBATIM imports | "det" key of `to_det_obs` = RAW s bits; XOR fold applied only via `seam.teacher_shots_to_events` (pin which meaning every consumer gets) |
| `bond_profile`, dynamic-ε truncation policy | NEW (no referee — instruments) | §6.1: per-cut invariant + window definition + binding flags |
| `eps_l` | NEW instrument WITH known-answer checks (§6.3: hand-computable 2×2-loop NONZERO anchor + independent dense-contraction cross-check at d3, no shared BP code; the product-state zero test is a smoke only — RT2) | §6.3 conventions; range + BP-residual self-checks are necessary, not sufficient (RT1) |
| loop-rank probe (ported, dim-3 caps) | parent probe method | gauge-independence argument unchanged |

Independence rule: the spike engine shares NO code path with `qutrit_dm` (gates built
by local formula); referee reads happen only in gate scripts/tests. The
representation-agnostic imports (layout, truncation, packing) are engine-side, not
referee-side — allowed.

---

## §4 Registered gates (SW0–SW9) — tolerances, inputs, predictions

Cell constants for every noisy gate: the p1c cell (D2). Patches: `d3_at_q6_7` (2b-i),
`d5_at_q6_5` (2b-ii). All gates predicted PASS; any miss is a finding to adjudicate
(never a silent tolerance bump). Bars: `TOL_EXACT=1e-12` (unit), `TOL_TRACE=1e-10`
(the SW2 branch-trace bar), `KILLER_FLOOR=1e-6`, chain-probe bar 1e-8 (class (b)).
Expected state-level residual magnitude ~1e-15 (E1-tf precedent); the (1e-13, 1e-12]
EVIL-MARGINAL band adjudication is SW-S7's. **(a)-identity grades (RT2, stated once):**
|2⟩-mass is checked STRUCTURALLY on the tensors (k=2 slices exactly 0.0 — true
zero-tolerance); every CAPS-PATH read of an (a) identity (⟨S_g⟩, ⟨Z_L⟩) carries a
declared float floor — ≤ 1e-12 at d3 (near-exact contraction), ≤ 1e-10 at d5 at the
converged χ_b — the identity stays class (a), the read is a float instrument.

- **SW0 — codestate (d3):** dense |ψ⟩⟨ψ| vs `QutritDM.init_logical(m).rho`, max-abs ≤
  1e-12, BOTH m ∈ {0,1} (chunked compare, never a full 5.77-GiB temp); PLUS the
  structural cert: |2⟩-mass exact on tensors, and ⟨S_g⟩=+1 ∀g / ⟨Z_L⟩=(−1)^m READ
  THROUGH THE PRODUCTION CAPS PATH at the d3 floor (≤ 1e-12, §4 grades) — the caps
  path is the instrument under test, the dense bridge is the cross-check, never the
  source (the rung-1 A3 lesson); PLUS per-edge raw dims == 2^(chain multiplicity),
  with the multiplicity map PRE-COMPUTED from the actual `plaquette_path` outputs and
  registered in the gate script before the run (RT1).
- **SW1 — per-op unit gates (d3):** mirrored (PepsState, QutritDM) pair through the
  SAME random token program (H/X/LEAK with leak-pump sites so b-branches are
  non-vacuous — the scrutinize-vacuous rule), per-op dense equality ≤ 1e-12:
  1-site gates; forced-Kraus LEAK (engine K_k ψ unnormalized vs referee
  `apply_channel([K_k])`); forced-outcome √E_s branch, BOTH outcomes, unnormalized.
- **SW2 — forced-branch chain probe (E1-tf mirror, d3):** ≥4 stabilizer forced-outcome-0
  branches on a leak-pumped prep state, engine at the LOSSLESS policy — defined
  STRUCTURALLY: no cut may reduce rank below the exact local rank (the σ > 1e-12·σ_1
  count, the pinned zero-drop convention; RT1: a 1e-30 weight bar is fp-junk-trippable) —
  dense equality vs referee; registered bar **≤ 1e-8 (class (b))**, expected ~1e-15;
  unnormalized branch traces agree to `TOL_TRACE=1e-10`. Referee driver = the §6.4 manual
  per-token walk (`apply_gate` + `apply_channel([K_k])` per forced LEAK token, in
  each site's stream order) — NEVER `apply_within_cycle_premeasure` (no forced mode,
  SF6). Precondition: prep mismatch < 1e-8 before the first stab (class (c),
  greppable `PRECONDITION (class c, not a gate miss):` prefix).
- **SW3 — single-wire TT ranks (d3):** measured TT bond ranks ≤ (3,5,3) / (3) on the
  real patch's w=4 / w=2 stabs at generic b=0.9 ((a) bound assert); measured values
  ledgered and compared to WP3 (equality expected; below = porting bug, SF3).
- **SW4 — record law (d3, trajectory ensemble; the G1.1 route):** engine samples N
  {det,obs} records at R ∈ {1,2}, production caps path, D7 sampling maps.
  **Referee = per-record exact probabilities via `DMPathEvaluator.reevolve_onto_records`
  (chunk B = 1 ONLY — the G1.1 §3 pin) + `path_trace` for P(s|m), with the obs law from
  the A4 biased-b composition (the `pepo_rung1_g11_sampling_cert_d3.py` referee
  machinery, reused by script name — note it hardcodes n = 9, fine for this d3-only
  gate); `record_oracle.full_joint` / `logical_distribution` / `logical_sector_traces`'
  50/50 leaked split is FORBIDDEN as the obs referee (RT1-B3/B4; full-9q record_oracle
  is memory-infeasible AND obs-b-blind). Input pin (RT2): the `records` argument of
  `reevolve_onto_records` = RAW per-round s bits, flattened round-major in stabilizer
  schedule order ((B, R·n_stab) uint8) — NEVER the XOR-folded det (the trap is
  invisible at R=1 where det ≡ s); when starting from folded records the g11 det→s
  inversion + triple-agreement check is mandatory.**
  Statistics: per-class multinomial z ≤ 4 on the top-64 record classes + tail-mass
  bucket, family-wise convention declared (64 comparisons at z=4 ⇒ family-wise false-
  positive ≈ 4e-3, class (c)). N is STAGED (RT1): a committed bench script measures
  per-shot cost at N=100 first and projects the TOTAL wall-clock — true engine arm +
  corrupt-stab engine arm + referee phase, both R values; N is then fixed to fill a
  registered TOTAL budget of ≤ 12 h serial GPU, with floor N ≥ 1e5, and the per-class
  minimum-detectable relative bias at the chosen N DECLARED in the gate script
  (class (c); at N=1e5, classes at p ~ 1e-3 detect ~40% relative bias — the G1.1
  N=1e6 convention is inherited only if the bench shows it fits). **Conflict ladder
  (RT2, registered now):** (1) if the bench projects N=1e5 > 12 h total, the budget
  rises to a pre-registered ceiling of 48 h WITH explicit user confirmation (the g11
  precedent); (2) if still infeasible, the R=2 cell is DROPPED (registered descope;
  R=1 kept); (3) N < 1e5 is FORBIDDEN — a PRECONDITION stop adjudicated as a cost
  finding, never a silent shrink ("any N change is a re-registration, never a script
  knob" — the g11 pin). Should-fail-must-fail power demonstrations AT THE SAME N
  (RT1): (i) the corrupt-stab (path-preserving letter-swap) engine arm must produce
  z > 4 on ≥ 1 top-64 class; (ii) the run-level b↔(1−b) swapped obs composition must
  trip z > 4 on ≥ 1 class while the true arm stays z ≤ 4 (the G1.1 controls,
  verbatim). Optional cross-check leg: `record_oracle` on a REGISTERED sub-register
  cell (n_data ≤ 7, where it is feasible) for the det marginal only.
- **SW5 — cross-carrier anchor (d3):** same `(base_seed, shot)` uniform stream, spike
  PEPS at the SW2 lossless policy vs `mps_forward` at `exact_chi`, R ∈ {1,2} —
  packed records byte-identical over N = 1e4 shots (WP5). Scope (RT1): certifies
  single-wire-2D vs single-wire-1D carrier equivalence GIVEN identical marshalled
  inputs; marshalling/leak-table/packing faithfulness is inherited from rung-1
  F1/C1, not re-certified here. Mismatch triage: convention first (the RT1-B1/B2
  directions), THEN fp-boundary branch flips (|u − boundary| < 1e-12, logged,
  expected count 0).
- **SW6 — KILLER set (d3, test-builder owned, K-catalog discipline):** each
  load-bearing assert ships a sabotage DEMONSTRATED to trip beyond KILLER_FLOOR, with
  non-vacuity preconditions: b↔(1−b) coherent double-swap (engine-invoking, K-5);
  wrong-outcome-sign branch (K-2); corrupt-stab letter swap path-preserving (K-2/K-8);
  **sampling-direction parity killer** (pinned point u = 0.1, p1 = 0.2: the
  mps_forward map gives s=0, the forbidden pepo-direction map gives s=1; non-vacuity
  precondition u ∉ [min(p1,1−p1), max(p1,1−p1)) — the maps AGREE on that middle band
  (RT2) — kills RT1-B1 regressions, K-8);
  **conj-layer sabotage** (double-layer caps built with the UNconjugated bra copy;
  requires an Im-carrying state precondition, K-6/K-8); det↔s fold triple-agreement vs
  `seam.teacher_shots_to_events`; ledger-image killer (deleted precut must emit
  `precut_discarded == 0.0` exactly); window-binding flag killer (a forced
  window-bound cut must emit its flag — §6.1); skips only via the registered
  allowlist.
- **SW7 — d5 codestate structural cert:** |2⟩-mass exact on tensors (§4 grades);
  through the caps path (NO dense bridge): ⟨S_g⟩ = +1 for all 24 stabs,
  ⟨Z_L⟩ = (−1)^m at the d5 converged-read floor (≤ 1e-10); PLUS per-edge raw dims
  == 2^(chain multiplicity) with the d5 multiplicity map pre-computed and registered;
  PLUS the d-generic H-pattern assertion replacing the d3-gated parser self-check
  (SF8). χ_b discipline (RT1): SW7 escalates χ_b until either the fit's exactness
  guard reports zero truncation OR consecutive-χ_b reads move < 1e-10; the bar
  (≤ 1e-10 on the (a) identities) applies at the CONVERGED read; the converged χ_b is
  ledgered AND the same identities are re-read at the SW8 production χ_b — the
  discrepancy at production χ_b is reported as data (it feeds §6.2), so the cert
  cannot be passed by cranking χ_b only for the cert.
- **SW8 — the d5 bond-saturation run (the WP1 measurement):** protocol §6.1; produces
  the per-round per-edge bond profiles, the discarded-weight + window-binding + §6.2
  accuracy ledgers, **the WP2 ε_l tables (RT2: measured on ALL 8 trajectories of the
  headline ε=1e-8 arm at the registered rounds r ∈ {0,1,2,5,10}, on the live SW8
  states — no post-hoc trajectory selection)**, and the WP1 verdict inputs. Gate
  semantics: the RUN completes within its tripwires and its ledgers close (every §6.2
  residual within its §6.2-enumerated floor; ZERO window-binding flag entries — the
  §6.1 rule; a run with ≥1 entry is adjudicated under the WP1 menu, RT2). The BET
  itself is adjudicated as WP1, not as a pass/fail gate. Registered aborts (RT1+RT2):
  **D_abort = 40** — evaluated on the per-event GROWN (instantaneous) dims BEFORE any
  NTU metric build, not only at round end ⇒ ORDERLY stop, partial bond table =
  F-SW-BOND evidence (the F-REC-1 early-stop precedent); **VRAM tripwire** — before
  each metric build, the byte estimate (§7 formulas) is checked and a projected peak
  > 24 GiB ⇒ the same ORDERLY stop; per-round FLUSH of bond profiles + ledgers to
  disk so even a hard OOM leaves the partial table; wall-clock tripwires + total
  budget per §7.
- **SW9 — d5 wiring cross-check (Clifford slice, opportunistic):** a DEDICATED
  mechanism-off run (WG off, per-round bit-flip X_ERROR(p_x=0.03) injected engine-side
  with its own runner-documented draw schedule — NOT part of the Section-5 stream),
  R = 10, N = 2e5, vs `StimCliffordAnchor(p_x=0.03, seed=4242)`; band 6/√N; NEVER
  consumes SW8's records (the prereg R-fence, §1.4). Declared blind spot inherited:
  echo-blind (the anchor cannot certify the X/Y DD echoes). Class (c) cross-check,
  non-gating for WP1.

---

## §5 Registered predictions (WP — the bets, written BEFORE any run)

- **WP1 — THE BET (class (b), the spike's reason to exist).** At d5 (`d5_at_q6_5`,
  p1c cell, arm A, compiled semantics), under the dynamic-ε truncation policy at
  ε_spike = 1e-8 (squared-σ per cut, §6.1 invariant — Manabe's thin-surface 1e-4
  grade via the §2 units map), with N_traj = 8 trajectories, R = 40 rounds (rounds
  indexed 1..40; no early stop before round 40 — RT2-B1):
  **every trajectory saturates. Per trajectory, with D_t(r) = that trajectory's
  max-over-edges bond at the end of round r: r*_t = the FIRST round r ≤ 20 such that
  (i) D_t(r') ≤ D_t(r*_t) + 2 for all r' ∈ [r*_t, 40], AND (ii) the DISJOINT-window
  max test holds: |max_{r'∈[31,40]} D_t(r') − max_{r'∈[r*_t, r*_t+10]} D_t(r')| ≤ 1
  (RT3-F1: the ±1 slack tolerates a genuinely-noisy plateau; r*_t ≤ 20 keeps the
  detection window [r*_t, r*_t+10] ⊆ [1,30] disjoint from the confirmation window
  [31,40], so a monotone drifter still cannot pass — the RT2-B1 fix; r*_t may
  precede the visual onset by one round via (i)'s slack — cosmetic, D_t(plateau) is
  a max. Declared (c) resolution limit: drift ≤ +1 bond per ~10 rounds is beneath
  ANY finite-horizon criterion — the D* ≤ 32 ceiling, the R=60 extension, and the
  ε-arm robustness rider are the guards at that scale). If ANY trajectory lacks an
  r*_t ≤ 20, ONE registered extension to R = 60 runs AUTOMATICALLY — ALL 8
  trajectories continue AND ALL 8 re-certify under the extended criterion (RT3-F2:
  never a stale-cert mix), with r*_t ≤ 40, detection window [r*_t, r*_t+10] ⊆
  [1,50], flatness window (i) over [r*_t, 60], confirmation window [51,60] (still
  disjoint); failing that ⇒ the falsification clause. The rider ε-arms extend with
  the headline arm (same horizon for the cross-arm verdict — RT3-F9). Run-level
  verdict = ALL 8 trajectories saturate; D_t(plateau) ≡ max_{r∈[r*_t, R]} D_t(r)
  with R the FINAL horizon (40 or 60, same for all); D* = max over trajectories of
  D_t(plateau), per-trajectory spread ledgered; D* ≤ 32.** Expected bracket (declared wide): **D* ∈ [2, 32]** — floor = the D-P
  bond-2 codestate; ceiling anchored on Manabe's thin-surface avg χ ≈ 9–21 at 7
  rounds (unsaturated) under ≈5× stronger per-round leak generation PLUS a coherent
  leakage-spreading interaction our compiled semantics lacks entirely (SF12 —
  the honest anchor strength), acknowledging BOTH declared mismatches: snake-MPS χ vs
  per-edge PEPS D, and Manabe's 10⁴-trajectory AVERAGE vs our max-of-8 statistic
  (RT1) — the anchor transfers entanglement-content order, not the number.
  - Robustness rider (class (c), the multiple-normalizations discipline): the
    VERDICT (saturates vs grows) must be identical across ε_spike ∈ {1e-6, 1e-8,
    1e-10} arms; the plateau VALUE may move.
  - Stability rider (class (c), RT1): if the per-trajectory plateau spread
    max_t D_t − min_t D_t > 8, escalate N_traj (8 → 24) BEFORE adjudicating —
    a max-of-8 tail estimate is not stable enough to call the verdict alone.
  - **Falsification / adjudication menu (registered):** (i) any trajectory fails the
    plateau criterion by R=40 (and the R=60 extension), or D* > 32 at ε=1e-8, or the
    D_abort=40 / VRAM tripwire fires IN THE HEADLINE ε=1e-8 ARM ⇒ **F-SW-BOND**
    finding; adjudication paths: (A') rule out the instrument (non-optimal truncation
    — SW-S6) via the loop-rank probe on the grown state + a variational/loop-update
    spot check; (B') LPDO record-law arm (Werner 1412.5746 (foundational), the
    prereg-S9 escalation); (C') accept thin-strip-only scope (mps_forward's proven
    regime); (D') geometry change. A miss is a FINDING with this menu — never a
    silent retreat, never a band re-fit. (ii) an abort firing ONLY in a rider arm
    (1e-10) is a robustness-rider verdict mismatch, adjudicated under the rider, not
    clause (i) (RT2). (iii) a run that saturates WITH ≥1 window-binding ledger entry
    is an INSTRUMENT-QUALIFIED pass: the affected trajectory re-runs at the widened
    window as a registered arm before the verdict (RT2). (iv) D* < 2 is impossible
    (codestate floor); D* ∈ [2,4] = better-than-expected, GO with a mechanism note.
  - GO semantics: WP1 pass ⇒ GO for the full 2D single-wire carrier registration
    (RUNG-C unblocks); the GO carries the SW-S6 instrument-relative qualifier and the
    max-of-8 tail-coverage qualifier.
- **WP2 — ε_l expectation (class (b), DECLARED WEAK-ANCHOR EXTRAPOLATION).** Owned by
  SW8 (RT2): measured on ALL 8 headline-arm trajectories' live states (norm network,
  §6.3 conventions incl. the known-answer checks), at rounds r ∈ {0 (codestate), 1,
  2, 5, 10}: **mean-over-loops ε_l ≤ 1e-2 at every measured round (per trajectory).** Anchor honesty: R–T's Willow numbers are for
  Heisenberg-quench Trotter states — our near-codestates under weak noise are a
  different state class; the band is wide and its miss is informative either way.
  Decision rule (class (c)): mean ε_l > 1e-1 at any r ⇒ the **boundary-cost flag** —
  the full-carrier contraction strategy (χ_b budget / geometry) must be re-adjudicated
  BEFORE the carrier build; a cost finding, not a correctness failure.
- **WP3 (class (b)):** measured single-wire TT ranks at (arm A, b=0.9) == the SF3
  bounds exactly — (3,5,3) for w=4, (3,) for w=2. Below-bound contradicts the parent's
  executed equality assert via the Kronecker-square identity ⇒ triage as an
  engine/porting bug, never a mechanism note (RT1); above-bound is impossible ((a)).
- **WP4 (class (b)):** SW2 chain dense-equality lands ≤ 1e-8 with expected magnitude
  ~1e-15 (the E1-tf precedent transfers: same referee, same forced-branch pattern,
  simpler engine side — pure vectors, no fused legs).
- **WP5 (class (b)):** SW5 cross-carrier byte-identity holds with ZERO mismatched
  records over N = 1e4 at R ∈ {1,2} (tie-break-boundary exceptions expected count 0,
  logged if any).

---

## §6 Measurement protocols (instruments pinned before the run)

### 6.1 Dynamic-ε truncation policy + bond-saturation instrument (WP1/SW8)

**Policy (the RT1 window invariant, RT2-hardened):** call order per truncation event
(verified against the reused machinery — insertion first, then cuts): apply the TT
branch, then per path bond (pass 1) `svd_precut_bond`, (pass 2) `ntu_truncate`; BOTH
passes compute the full SVD of their current pair insertion X0 = R_A R_B^T BEFORE
cutting, so the "running target" r_dyn = the smallest rank whose squared-σ tail ≤
ε_spike on the CURRENT insertion spectrum is always computable. The precut window =
min(4·r_dyn, W_max) with **W_max = 160 = 4·D_abort the metric-feasibility cap**
(RT2/RT3-F3, the reconciled resource picture: pass 1 — metric-FREE local SVD — precuts
EVERY path bond to ≤ W_max BEFORE any pass-2 NTU metric is built, so every metric leg
is ≤ W_max and the metric bytes are bounded by (W_max)⁴·16 B ≈ 9.8 GiB; the §7
(5·40)⁴ ≈ 23.8 GiB figure is the UNCAPPED counterfactual that motivated W_max and the
VRAM tripwire, kept as defense-in-depth against spec-mismatch. Without a cap the
widening branch is provably dead code because tail(4·r_dyn) ≤ tail(r_dyn) ≤
ε_spike). INVARIANT: the
TOTAL per-cut discarded weight — precut pass + NTU/policy pass, both squared-σ
(RELATIVE local-insertion tails; the NTU ledger's `discarded` is the σ-tail at kept
rank and is BLIND to variational pinv under-delivery — declared, consistent with
SW-S6's local-error-only claim), summed — must be ≤ ε_spike. If a W_max-capped precut
would exceed it: ledger a `window_binding` flag entry; retry ONCE with the kept rank
escalated; if the total still exceeds ε_spike ⇒ PRECONDITION tripwire (the orderly-
stop route), not data. The widening/flag machinery is DEFENSIVE (unreachable while
code matches spec below W_max; SW6's killer forces it) — window-plateau
discrimination rests on the window scaling with the spectrum (4·r_dyn), plus the
zero-`window_binding`-entries rule for a clean WP1 verdict (a saturating run with
entries is WP1 menu (iii)).

**Instrument:** per trajectory, after each round's last op, snapshot
`bond_profile(state)` = {edge → dim}; emit (round, edge, dim) long-form + per-round
max/mean-over-edges per trajectory, FLUSHED TO DISK EVERY ROUND (RT2: a hard OOM must
still leave the partial table). WP1 statistics per §5 (rounds 1..40; NO early stop
before round 40 — the criterion's confirmation window needs the full run; tripwires
and registered aborts are the only early exits, and their partial tables are finding
evidence per the F-REC-1 precedent). Policy arms: dynamic-ε ∈ {1e-6, 1e-8, 1e-10},
HEADLINE ε=1e-8 ARM RUNS FIRST (RT2: a budget stop still yields the primary data).
Discarded-weight ledger per cut (the Schmidt-sum bound is 1D-exact only; on PEPS it
is the LOCAL-error ledger, no global fidelity claim — SW-S6). N_traj = 8 (escalation
rider in WP1), seeds (base_seed, shot) registered in the runner. Aborts: D_abort = 40
— fires when any grown dim EXCEEDS 40 (D = 40 itself is processed; RT3-F6), checked
pre-metric — + the 24-GiB projected-peak VRAM tripwire (SW8), where the projected
peak = metric bytes (≤ (W_max)⁴·16) + live state + 3 transient copies, the runner
printing the formula's terms each check (RT3-F5). Any §6.2 floor violation without
its own pinned remediation ⇒ the orderly-stop family: run halts, ledgers flushed,
the event itself is finding evidence (RT3-F8).

### 6.2 Per-read contraction-accuracy instruments (replacing the vacuous closure — RT1)

The naive `|q0+q1−⟨ψ|ψ⟩|` closure is IDENTICALLY zero under the two-term identity
(q0,q1 both derive from the same N and M contractions — SF9) and is NOT an accuracy
bound. The registered instruments:

**Floor table (RT2 — the SW8 "ledgers close" condition checks EXACTLY these):**

| Residual | Stage | Cadence | Floor | Class |
|---|---|---|---|---|
| cross-route `|q1_caps − q1_norm|/N` | d3, every Born read | every read | ≤ 1e-10 | (c) |
| cross-route `|q1_caps − q1_norm|/N` | d5, in-run | 1 stab per 5 rounds | ≤ 1e-6 (the d5 contraction grade — RT2/R2-1; the d3 1e-10 floor is d3-ONLY) | (c) |
| χ_b-doubling `|M(χ_b) − M(2χ_b)|/N` | d5, in-run | 1 stab per round | ≤ 1e-6 | (c) |
| R-sweep p0 movement | pre-run + mid-run (r=15) | per sweep level | < 1e-8 | (c) |

- **Cross-route residual:** read `q1` twice — (i) the caps two-term route ½N − ½M
  (s=1 sign), (ii) the branch-norm route ‖√E_1 ψ‖² (apply the TT, contract the
  double-layer norm — an INDEPENDENT contraction path through a different network;
  independence confirmed vs the caps route, which never touches the TT). The
  exact-route/dense cross-check at d3 additionally compares q1 to the referee's
  `project_stabilizer` probability in SW1/SW2 contexts.
- **χ_b-doubling delta:** a CONSISTENCY estimator, not an error bound (RT2: a
  plateaued χ_b convergence can show a small delta while both reads are off) — its
  false-plateau risk is mitigated by the evolved-probe R-sweep leg. Any floor
  violation in this table ⇒ PRECONDITION event (the SW-S3 bound), not data.
- **R-sweep convergence + χ_b sequencing (RT2 pins):** (i) the PRE-run codestate
  sweep (χ_b starts 16, doubling until p0 movement < 1e-8) fixes the production
  value χ_b_prod(v0); SW7's re-read runs at v0. (ii) The MID-run re-check at r = 15
  re-runs the doubling ON THE LIVE trajectory state (a re-read, no re-sampling);
  p0 movement ≥ 1e-8 at χ_b_prod ⇒ PRECONDITION event: χ_b escalated, the event
  ledgered, and that trajectory RESTARTS from round 1 at the escalated χ_b (its
  pre-escalation rounds are discarded as tainted — they never enter WP1 statistics);
  the SW7 identities are re-read at the escalated value before any verdict.

### 6.3 ε_l instrument (WP2) — pinned conventions + known-answer checks

Network: the norm network ⟨ψ|ψ⟩ of the CURRENT trajectory state, nodes = grouped
(T, T*) per site (R–T Fig. 9 convention). Primitive loops: the (d−1)² elementary
4-site squares of the data grid. BP: messages both directions per edge, dims = the
grouped virtual pairs; update = incoming-messages × local grouped tensors; normalize
each message to unit norm; convergence tol max-message-delta ≤ 1e-10, max 500 sweeps
(non-convergence ledgered and that loop's ε_l flagged, not silently dropped).
Per loop: insert converged boundary messages, cut ONE edge, form the transfer matrix
(dimension = that edge's ket⊗bra pair, i.e. D_e² where D_e is the CUT EDGE's own
current bond dim — the self-check bound is per-edge: ε_l ∈ [0, 1−1/D_e²]), full
eigendecomposition; ε_l = 1 − |λ_1|/Σ|λ_i|. **Cut-edge rule (ours, class (c)):**
compute ε_l for EVERY edge of the loop; report MAX (conservative) + mean; cut-edge
sensitivity itself reported. **Known-answer checks (RT1+RT2, preconditions of WP2):**
(i) SMOKE only (class (a) identity with NO discriminating power — RT2: at bond dim 1
the transfer matrix is a scalar and ε_l = 0 for ANY assembly): product state ⇒ every
loop ε_l == 0 to roundoff; (ii) **the discriminating anchor:** a single 2×2 grid (one
elementary loop), all four bonds dim 2, HAND-WRITTEN loop-correlated site tensors
with a NONZERO ε_l target — per-loop transfer matrix + ε_l recomputed by an
INDEPENDENT dense eigendecomposition (no shared BP code), matched to 1e-10 (a wrong
TM assembly / message-gauge error produces a nonzero mismatch; the zero branch cannot
mask it); (iii) one evolved d3 state (d3-scoped — feasible): per-loop transfer matrix
+ ε_l recomputed by an INDEPENDENT dense contraction of the same norm network (no
shared BP code), matched to 1e-10. Codestate value reported first (r=0 baseline).

### 6.4 Dense referee protocol (d3)

State level: referee = `SvSampler(device="cuda").within_cycle_dm_engine(sched)` (bare
QutritDM, SF5). Forced-branch chains: the engine applies its token stream; the
referee is driven by a MANUAL per-token walk — H/X via
`apply_gate(single_qudit_gate(...), site)`, each forced LEAK via
`apply_channel([K_k])` with the forced index sequence, preserving each site's
within-stream token order (cross-site order immaterial: distinct-site ops commute) —
NEVER `apply_within_cycle_premeasure` (no forced-branch mode, SF6/RT1); stab outcomes
forced (engine TT branch; referee `project_stabilizer`), both unnormalized; compare
dense ψψ† vs ρ chunked. Record level: `DMPathEvaluator.reevolve_onto_records`
(B=1) + `path_trace` + the A4 biased-b obs composition (SW4); `records` input = RAW
per-round s bits, round-major in stabilizer schedule order — NEVER the XOR-folded
det (RT2; det→s inversion + triple-agreement mandatory when starting from folded
records); the 50/50 `logical_distribution` split FORBIDDEN as obs referee.
`record_oracle` appears ONLY on registered sub-register cells (n_data ≤ 7), det
marginal only.

---

## §7 Resource pre-estimates + tripwires (all class (c))

- Byte budget (single-wire, re-derived from the parent's doubled numbers): peak grown
  4-neighbor site tensor 3·(3D)·(5D)·D² complex128 ≈ 45·D⁴·16 B — at D=32: ~0.70 GiB;
  at the abort boundary D=40: ~1.7 GiB, ×3–4 transient copies ≈ 5–7 GiB (RT2: the
  budget now extends to the abort point). NTU metric cluster (5D)⁴·16 B: ≈ 9.8 GiB
  (10.5 GB) at D=32, ≈ 23.8 GiB at D=40 — the UNCAPPED counterfactual (RT3-F3: with
  the §6.1 W_max=160 precut discipline every metric leg is ≤ W_max, bounding actual
  metric bytes at ≈ 9.8 GiB; the counterfactual is WHY the guards exist) — hence
  **D_abort = 40** (fires on grown dim > 40, evaluated BEFORE any metric build) and
  the **24-GiB projected-peak VRAM tripwire** (peak = metric + live state + 3
  transients, formula printed per check): at the
  parent's measured failure mode (~20-GiB "device-not-ready" allocations, the
  `_cluster_metric` v4.3 note) a D=64 abort would OOM disorderly long before firing
  (RT2, three-lens convergence). W_max = 160 caps the metric bytes independently
  (§6.1). The v4.3 env-bounding (gauge-cut on the metric COPY) is REQUIRED equipment,
  not optional, and its ledger fields carry over. Referee-side budget (RT2, corrected
  to the g11 script's own measured numbers): the SW4 record referee at B=1 holds
  ≥ 3 live full-9q DM copies — **~17–25 GiB measured peak** — plus ≤ ~3 transient
  5.77-GiB copies in the A4 composition (freed per class); HARD PRECONDITION: the
  PEPS engine state and all engine-arm allocations are FREED before the referee phase
  starts (VRAM watermark printed between phases — the g11 sequencing pin).
  `record_oracle` full-9q is NOT budgeted because it is FORBIDDEN (SF7).
- Wall-clock: d3 STATE-level gate scripts ≤ 30 min each. SW4 has its OWN budget:
  bench first (committed script, N=100 shots, both R values, projecting the TOTAL —
  all arms + referee phase), then N set per the §4 conflict ladder (12 h → 48 h with
  user confirmation → registered R=2 descope; floor N ≥ 1e5 hard). d5 SW8: per-round
  wall-clock logged; STOP-and-profile if a round exceeds 30 min or round-time grows
  superlinearly in r (the p7e quimb-runaway lesson); **SW8 total budget (RT2): after
  trajectory 1 of each arm the runner prints the projected arm total; per-arm ceiling
  48 h serial GPU; per-trajectory checkpoint/resume (round-level flush per §6.1) so a
  budget stop preserves completed trajectories as partial evidence; headline ε=1e-8
  arm first.** A tripwire stop is `PRECONDITION (class c)`, never a WP1 verdict.
- GPU serial; every run a committed script under `outputs/nonpauli_teacher/peps_spike_*`
  with precondition asserts, printed evidence (shapes/hashes/bond tables), flushed
  output, `__main__` guard, junitxml for pytest counts, `exit ${PIPESTATUS[0]}`
  runners, sha256 of sources in logs.

---

## §8 Deliverables + closure

1. This contract at v1.0 REGISTERED (post red-team, blockers = 0), committed before
   any engine code.
2. Stage (2b-i): `carrier/peps/` modules + `tests/test_peps_spike.py` (disjoint
   builders: module vs tests, tests written against THIS contract) + gate scripts +
   the SW0–SW6 evidence run (one reviewed src diff, user-confirmed).
   **Closure requirement (RT1): `outputs/twin_validation/skip_audit_run.sh` passes
   (exit 0) on the run's junitxml** — unregistered skips or PRECONDITION-carrying
   failures fail the evidence run.
3. Stage (2b-ii): SW7–SW9 runs + the WP1/WP2 verdict — outcomes backfilled into THIS
   document (gate results with hashes; every miss a named finding with adjudication).
4. Metric audit (every number field-standard or rung-3 flagged) + rigor audit (every
   conclusion theorem-backed vs provisional) at spike close; CODE_MAP regenerated;
   memory RESUME updated.
5. RUNG-C remains GATED on WP1; RUNG-A (mps_forward verification) stays demoted to
   confirmatory and may run opportunistically; G1.8 opportunistic (GPU-idle).

---

## §9 OUTCOMES BACKFILL (Stage-7 close-the-loop, 2026-07-10)

### (2b-i) d3 STATE-LEVEL — GATE-GREEN ✅
Build: `carrier/peps/` (state / stab_tt / contraction / trajectory / sampling_maps /
diagnostics / __init__ + README) + `tests/test_peps_spike.py`. Committed (this contract
first, then src+tests engine — user-confirmed; CODE_MAP regenerated + code_status ACTIVE
entry). Built via the full contract-first pipeline (grounding → 3 red-team rounds to zero
blockers → disjoint builders → Stage-4 un-led review → gates).
- **Stage-4 un-led review** (4 lenses + adversarial verify; 8 findings, 7 confirmed 1
  refuted): **ENGINE = zero correctness defects.** The refuted finding (d5 double-layer fit
  "2 tensors per ROW tag → silently wrong") was killed via quimb 1.14.0 source
  (multi-tensor-per-site is first-class + raises loudly on malformed groups). 3 fixed
  (test-adapter reconciliation + 1 module ledger enrich): forced-Kraus adapter (dropped the
  wrong-order `apply_site_op`), `_truncate_dcap` → module `truncate_bond_dcap` + the module
  now emits `exact_rank` in the `_policy_cut` ledger, SW2 lossless dead asserts.
- **Stage-5 GPU gates**: SW0-SW6 + eps_l known-answers = **28/28 PASS, 0 failed / skipped /
  errors** on the real `d3_at_q6_7` patch (RTX 5090, ~18 s; junitxml-counted). Evidence:
  `outputs/nonpauli_teacher/peps_spike_gates_d3_run.sh` + `.junit.xml` (gitignored, local).
  First run had 4 fails, ALL test-harness (not engine): eps_l `_eps_loop_stats` didn't parse
  the `{per_loop:[...]}` dict; conj-killer's unconjugated self-overlap `n2_sab ≈ 0` degenerate
  (→ normalize by the true norm); ledger-image killer needed `exact_rank > 8` unreachable at
  single-wire low rank (→ teeth moved to `total_discarded`, `D_cap < exact_rank`). All fixed,
  re-run 28/28.
- **CERTIFIES:** SW0 codestate `|ψ⟩⟨ψ|` == `QutritDM.init_logical(m)` @ 1e-12 (both m);
  SW1 per-op mirrored equality; SW2-slice lossless; SW3 TT ranks (3,5,3)/(3) @ b=0.9
  (**WP3 confirmed**); SW5 sampling maps == mps_forward; ALL SW6 killers demonstrated to trip;
  **eps_l 2×2 vs an INDEPENDENT dense eigendecomposition @ 1e-10** (the loop-TM instrument
  validated).

### (2b-i) RECORD-LEVEL — NOT YET RUN (script-owned)
SW4 (`DMPathEvaluator.reevolve_onto_records` record-law, B=1, g11 A4 obs) + SW5 (cross-carrier
byte-identity vs `mps_forward` at `exact_chi`) — the two script-owned gates. NOT written;
**HELD** pending the YAQS-reuse decision below.

### DEFERRED d5-arm (2b-ii) items (Stage-4; NOT d3-gate blockers)
- **#1** norm-cache rebuild per read → d5 SW8 per-round perf; thread a `NormCache`.
- **#3** eps_l BP not exercised by the 2×2 pytest (all edges are loop edges) — a 3×3
  BP-into-loops smoke was added to the import-check; the full fix is the §6.3(iii) evolved-d3
  independent-dense-reference. **YAQS is a candidate independent referee here** (below).
- **#4** boundary-MPS route has no d3 validation (d3 gates use the exact route) — add a
  boundary-vs-exact agreement check at d3.

### YAQS reuse assessment (external/yaqs, MQT YAQS v0.6.0, MIT) — see
`docs/nonpauli_teacher/yaqs_reuse_assessment_2026-07-10.md`
YAQS = the reference TJM implementation (SF12's grounding). **Strictly 1D MPS/MPO — NO
2D/PEPS** (RUNG-B is unique), **NO QEC syndrome circuits** (mid-circuit measure raises),
memory subsystem single-qubit-probe + Hamiltonian-backend. BUT qutrit/leakage is real in the
analog path, and it has **an exact Lindblad ME + dense MCWF backend sharing no truncation
code** = a legitimate anti-circular independent GT. Verdicts: independent-GT for
mps_forward/RUNG-A + deferred #4 = **REUSABLE-VIA-ADAPTOR** (express √E_s as Lindblad+dt;
CPU referee); RUNG-C memory (CMI/QMI Markov-order + operational-memory-SVD) = **REFERENCE-ONLY**
(lift the formulas, not the single-qubit pipeline); digital QEC sim = **NOT-APPLICABLE**.

### ★ NEXT-SESSION DECISION POINT
Before SW4/SW5 or the d5 crux, decide the YAQS integration: (a) use YAQS exact-Lindblad/
qutrit-MCWF as the anti-circular independent GT for RUNG-A (verify `mps_forward`) + the
deferred #4 — cheap FAITHFULNESS-protocol win; (b) lift YAQS's CMI/QMI + operational-memory
metric definitions for RUNG-C rather than building from scratch. The **2D PEPS d5 crux (WP1
bond saturation) stays ours** (YAQS gives no 2D). Then: SW4/SW5 (finish 2b-i record-level) →
the deferred d5-arm prereqs → 2b-ii d5 crux (the make-or-break bet).
