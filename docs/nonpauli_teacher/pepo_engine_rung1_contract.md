# Rung-1 PEPO Engine — Build Contract (contract-first; binding for builders A1–A4)

Status: CONTRACT **v4**, 2026-07-09 — through THREE red-team rounds (blocker trajectory
3 → 1 → 1(self-inflicted by the v3 gap-rule edit) → 0; v1–v3 in git history). Governing
registration: `pepo_d5d7_carrier_prereg.md` **v2.4** (gates G1.1–G1.9, ledger C1–C10,
simplifications S1–S11, rung-0 outcomes). This document
pins IMPLEMENTATION semantics: representation, invariants, the op↔referee registry, gate
protocols, and scope fences. Committed BEFORE any implementation code. A miss at a gate is a
finding to adjudicate, never a silent tolerance bump.

**Red-team OUTCOMES (v3→v4, round 3, one fresh convergence checker):** the round-2 obs-law
closure VERIFIED leg-by-leg at the seams (incl. the off-support F₀+F₁=I marginal argument —
"3 sites only" vs "all 9 + parity over 3" are the same distribution, not two-implementable);
ONE new blocker was self-inflicted by the v3 gap-rule "total order" (k* ≫ D_cap always won ⇒
G1.3 would read ~50–566, the frozen rank_full datum) — fixed to the window-bound rule in §3;
stale "B ≤ 2" in §4 removed; F₀/F₁ pinned by formula; version strings + the prereg C3/S9/G1.9
band synced (prereg → v2.4); C3 witness re-tied to the measured G1.9 bar.

**Red-team OUTCOMES (v2→v3, round 2, two fresh breakers):** ONE residual blocker — the v2
obs-law pin was still two-implementable on the SUPPORT/BASIS axis (fixed below: parity over the
LOGICAL support only, X-flagged sites H-rotated); round-2 also independently RE-DERIVED and
confirmed the v2 fixes (TT bound tight at b=0.9; normalized Δσ the right object; the 50/50 split
correctly forbidden; A4 composition constructible from `reevolve_onto_records` — the handle IS
the post-terminal-measurement pre-readout state, terminal Y correctly skipped; det→s inversion,
raise set, H-spread seed, 50·D budget, frozen cut/margins, F6 hash all verified). Nine
amendments folded (TT parameter domain; gap-rule total order; referee chunk B=1; G1.9 bar floor;
G1.8 tile init; G1.7 floor = 1e-4; G1.2/χ_b arms pinned; prereg §6.4 synchronized to the
normalized Δσ — prereg bumped v2.3; G1.9-pre arm named + G1.4 spectra dump added).

**Red-team OUTCOMES (v1→v2, all three breakers convergent):** (B1) the v1 "TT rank ≤ 10"
assert was FALSE — the exact fused-leg TT of the weight-4 stabilizer channel at b=0.9 has bond
ranks (9, 25, 9), = (2·min(w_L,w_R)+1)² per bond (the v1 figure forgot the ket⊗bra squaring);
(B2) the v1 "Δσ ≤ 1e-3" plateau was refuted by the frozen exact spectra themselves (~4.2e-3/round
scale drift from healthy purity decay; ℓ²-normalized shape drift ~4e-5) — the gate now runs on
the NORMALIZED spectrum; (B3) the v1 G1.1 obs law was double-sided-unpinned (engine biased-b vs
referee 50/50 leaked split, divergence ~4e-3 vs a ~2e-3 band; the referee's own docstring
documents it) — the obs law is now pinned on both sides with a new A4 oracle deliverable.

## 0. Verified structural facts (Stage-0 ledger — each checked in the named seam, 2026-07-09)

| # | Fact | Verified at |
|---|---|---|
| F1 | The compiled within-cycle dynamics is ENTIRELY single-qudit: per-position token streams `H`/`X`/`LEAK` pre-M, transversal `Y` post-M (skipped on the terminal round); unknown tokens raise | `QutritDM.apply_within_cycle_premeasure` / `apply_within_cycle_postmeasure` (docstrings + code, carrier/exact/qutrit_dm.py) |
| F2 | The stabilizer measurement is the ONLY multi-site operation: X-supports Hadamard-rotated to Z (leaked levels H-inert), then the DIAGONAL syndrome-bit POVM `E_s[i,i] = ½(1+(−1)^s ∏_q d_q)` with per-site weights d_q = +1 (t=0), −1 (t=1), 1−2b (t≥2, arm A/C), applied elementwise as ρ[i,j] → √e_i √e_j ρ[i,j] (unnormalized), then rotated back | `QutritDM._povm_diag_weight` + `project_stabilizer` |
| F3 | Non-selective round = sum of the two √E_s branches per stabilizer, sequentially over the 8 stabs (the R-gate reference run's exact loop) | `outputs/nonpauli_teacher/pepo_feasibility_drho_vs_round_d3.py` main loop |
| F4 | Leak channel = per-CZ-layer single-qudit Kraus list `exp(L/4)` `(n_kraus,3,3)`, marshalled per position with the token streams | `SvSampler.build_within_cycle_leak` / `marshal_within_cycle` → `WithinCycleMarshalled.leak_kraus`, `streams_by_pos` |
| F5 | The d3 patch layout is the rotated DIAMOND; data_coords transform to an integer d×d grid under u=(x+y)/2, v=(x−y)/2 (to be ASSERTED at runtime, not assumed); stabilizer supports are 2×2 plaquettes (weight 4) + boundary weight-2 pairs; bisection n_cross = d−1 (rung-0 counted+measured); s_t = 2·n_cross at every straight cut | rung-0 `pepo_rung0_ncross_dbond_d357_result.json` + `xzzx_parser` coords |
| F6 | The NTU metric with rows = the BRA insertion satisfies ε = v†gv (the rung-0 C4-caught convention); structured Fig.-4 assembly == dense at ~5e-16 | `pepo_rung0_ntu_metric_unit.py` (fixed revision, content_hash b5f4f834…) |
| F7 | quimb 1.14.0 preserves torch-cuda-complex128 backing through PEPS contraction; PEPS/PEPO/TensorNetwork2D + `contract_boundary_from*` exist | rung-0 substrate probe (E1/E2) |
| F8 | The frozen G1.2 referee numbers (sequential-null detector marginals, ε*-cut χ=16, worst dp/bar=0.0167) live in `outputs/nonpauli_teacher/pepo_record_error_vs_eps_d3_result.json`; the sequential-null convention is DEFINED BY `pepo_record_error_vs_eps_d3.py` (reuse verbatim, cite by script name) | that script + JSON |
| F9 | Codestate oracle init = `QutritDM.set_code(...)` + `init_logical(m)`; trace==1 asserted there | qutrit_dm.py + the R-gate script |

## 1. Modules + ownership (src placement user-confirmed 2026-07-09)

```
src/error_coupling_simulator/carrier/pepo/
  __init__.py        (public API re-exports)
  layout.py     [A1] diamond→grid transform + plaquette paths + codestate PEPO builder
  dynamics.py   [A2] single-site superops, stabilizer-channel TT, NTU truncation, ledgers
  sampler.py    [A3] boundary-MPS norm cache, Tr(ρ·Π̂) caps, Born sampling + selective update
  README.md          module scope (per repo convention)
tests/test_pepo_rung1.py            [test-builder] the registered gates vs THIS contract
outputs/nonpauli_teacher/pepo_rung1_*.py  [A4] the GPU gate/cert scripts + runners
```

Builders are BANNED from GPU/pytest execution (static checks + `py_compile` +
`--collect-only` only); evidence runs are orchestrator-serialized. The test builder writes
against THIS CONTRACT, never the implementation; ambiguous signatures get ONE adapter at the
top of the test file.

## 2. Representation + invariants

- **State object `PepoState`**: a quimb `TensorNetwork` of rank≤5 site tensors, one per data
  qutrit, physical leg = the FUSED d²=9 vectorized index (ket⊗bra, ROW-MAJOR vec: fused index
  k = 3·t_ket + t_bra — pinned; every superoperator uses this convention), virtual bonds on
  the (u,v) grid edges. Tensors torch-cuda-complex128 ALWAYS (S8; assert at construction).
- **Grid (v2 fix — the raw transform gives HALF-integers on the real patch)**:
  u' = (x+y)/2 − min, v' = (x−y)/2 − min from `sched.data_coords`; integrality/uniqueness/
  d×d-ness asserted ON (u',v') ∈ {0..d−1}². Site tags `Q{pos}` keyed by ENGINE position (the
  streams/stab key space). NOTE (v2): the FROZEN referee cut A=[0,1,2] (x ≤ 5) is a STAIRCASE
  in (u',v') — {(0,0),(0,1),(1,0)} — NOT a grid column; every frozen number (16-flat, dp/bar
  table, X2b χ) is defined at THAT site list. All G1.3/G1.4/G1.6 reads use the explicit site
  list A=[0,1,2] | B=[3..8], never "a grid column".
- **d-genericity (v2)**: layout.py code is d-generic; rung-1 EVIDENCE is d3-only (the test
  builder writes d3 tests only; d5/d7 codestate checks are rung-2 scope).
- **No global gauge/canonical form is tracked** (2D has none — Kilda App. A.1); the ONLY
  tracked bond metadata is the per-bond dimension + the truncation LEDGER: per-truncation
  discarded weight (squared-σ scale — UNITS: discarded = Σ_cut σ_k² / Σσ², the same squared
  convention as the rung-0/R-gate scripts) and per-round trace shift.
- **Invariants (constraint-ledger C1–C4 bindings, checked where stated):**
  - trace: `pepo_trace(state)` == 1 within the logged trace-shift ledger after every round
    (C1); Hermiticity of the represented ρ is NOT tracked per-tensor (the fused-leg PEPO does
    not expose it locally); it is checked at gates via the d3 dense reconstruction (G1.9 path)
    and via real-nonnegative Born weights (C3 witness) — pinned here so nobody "adds" a bogus
    local Hermiticity assert that a correct fused representation would fail.
  - positivity: NEVER assumed; the C3 witness (Born weight < −1e-8 logged; cumulative
    negative mass > 1e-4 STOP) is implemented in sampler.py and is non-optional.
- **Bond caps**: D_cap per run config; rung-1 gates run the D-sweep {2,4,8,16} (rung-0
  pinned). NO silent cap: hitting the cap with discarded > the gap tail is logged as
  CAP_BINDING in the ledger.

## 3. Op ↔ referee registry (every op names its equivalence target + exact semantics)

| Op (module) | Semantics (pinned) | Referee (equivalence target) |
|---|---|---|
| `build_codestate(sched, m)` [layout] | ∏_g (I+g)/2 · logical-sector projector applied to the **H^⊗n-SPREAD seed (the oracle's `_codestate_vector` convention — v2 fix: a literal \|0…0⟩ seed can be EXACTLY annihilated in the m=1 sector; nonzero-norm ASSERTED for BOTH m)** as W-tensor chains (D-P construction: per check ONE chain, one inter-column bond, bond 2 state / 4 operator fused); qutrit-embedded (\|2⟩ row zero); built directly as the FUSED-leg PEPO of ρ = \|m⟩⟨m\| | d3: dense reconstruction == `QutritDM.init_logical(m)`.rho for **m = 0 AND m = 1**, max-abs ≤ 1e-12 (G1.0); d-generic code, d3-only evidence: structural exacts ⟨S_g⟩=+1, ⟨Z_L⟩=(−1)^m, \|2⟩-mass=0 via sampler caps (C5) |
| `apply_token_stream(state, streams, leak_kraus)` [A2] | F1 semantics VERBATIM: per position, tokens in order, stop at `M`; `H`→qutrit Hadamard superop, `X`→X superop, `LEAK`→Kraus-sum superop Σ_k (K_k ⊗ K̄_k) on the fused leg; `Y` ignored pre-M; unknown token raises. Single-site: NO bond change (assert) | `QutritDM.apply_within_cycle_premeasure` — d3 dense equality per token type on random small states (unit gate, 1e-12) |
| `apply_postmeasure(state, streams, terminal)` [A2] | F1: post-M `Y` per position; terminal skips; **raise set matches the referee EXACTLY: post-M `X`/`H`/`LEAK` raise, any OTHER unknown post-M token is silently ignored (v2 fix — the referee does NOT raise on arbitrary tokens; a raises-on-unknown killer would split engine vs referee)** | `QutritDM.apply_within_cycle_postmeasure`, same bar |
| `stab_channel_tt(paulis, outcome, b, arm)` [A2] | The EXACT NUMERIC TT of the diagonal fused-leg superoperator of √E_s·(·)·√E_s over the support: build the 3^w diagonal e_i from the F2 formula, take √, form the fused diagonal √e_i·√e_j, TT-decompose EXACTLY (SVD; candidate values with σ ≤ 1e-12·σ₁ dropped) along the plaquette path; **assert TT bond rank == the DERIVED bound (2·min(w_L,w_R)+1)² at each bond, VALID FOR arm∈{A,C} AND b∉{0, 0.5, 1} ONLY (v3 domain pin: at b=0.5 the product classes collapse — w=4 mid-bond ≤ 9; at b∈{0,1}/B1/B2 → 4; outside the domain the assert is rank ≤ the domain bound, not ==) — (9, 25, 9) for w=4, (9) for w=2 at the p1c cell b=0.9, the registered evidence point (v2 B1 fix: the v1 "≤10" forgot the ket⊗bra squaring; rank 25 verified numerically, σ₂₅≈5.8e-6)**; measured ranks logged. X-supports: sandwich with single-site H superops (F2), NOT folded into the TT | `QutritDM.project_stabilizer(..., diagonal_z=False)` — d3 dense equality of one full stabilizer update on random ρ, 1e-12; the b/arm table of `_povm_diag_weight` is the normative formula (arm A default, b from the p1c cell = 0.9) |
| `nonselective_round(state, stabs, …)` [A2] | F3 loop: per stab, branch-sum ρ → √E_0ρ√E_0 + √E_1ρ√E_1 then truncate; stabs in the SAME order as `sched.stabilizers`. **Bond budget (v2, re-derived at rank 25): the support-path transient bond reaches (r₀+r₁)·D ≤ 50·D mid-plaquette before truncation — trivial at d3 tensor sizes, but the budget line in every gate script uses 50·D, not 20·D** | R-gate reference loop semantics; gate-level: G1.2/G1.3 vs the frozen JSONs |
| `ntu_truncate(state, bond, D_cap)` [A2] | The rung-0 seed: NTU metric (rows = BRA insertion, F6) + pinv optimization loop; **per-bond truncation target = D_cap (CAP_BINDING at per-bond NTU truncations is NORMAL operation, logged not flagged — v2: the gap rule was never measured per-bond)**. The GAP RULE applies to GLOBAL spectrum reads (G1.3/G1.6) and ledger effective-rank reporting ONLY, pinned (v4 fix — the v3 "total order" let the last-nonzero index k* ≫ D_cap always win, so a correct engine read ~50–566 instead of 16 at G1.3; round-3 catch): **candidates = k ≤ D_cap with σ_k > 1e-12·σ₁ (v4.1: the σ_k guard — a rank-deficient window must not qualify via ∞/∞; if NO k in the window passes it, effective rank = the count of σ > floor) and ratio(k) = σ_k/σ_{k+1}, where ratio(k) := ∞ when σ_{k+1} ≤ 1e-12·σ₁; qualifying = ratio(k) ≥ 10; pick the LARGEST qualifying k ≤ D_cap; none qualifying ⇒ effective rank = D_cap + CAP_BINDING log** — the window k ≤ D_cap binds everything, ∞-ratios arise only inside it, both fallback clauses are live; winning ratio always logged | rung-0 unit (metric); gate-level G1.3 (gap rank == 16 at d3) |
| `norm_cache(state)` / `expect_site_caps(state, caps)` [A3] | Rudolph–Tindall reverse-pass boundary-MPS over grid columns (one-site fitting, dim R_n), cached once per state; **caps = GENERAL single-site fused operators (length-81 fused superop-diag or 3×3 site operators lifted to the fused leg) — NOT diagonal-only (v2 fix: the X-support E_s needs H-conjugated M_q, a full 3×3). E_s expectation pinned as the two-term decomposition Tr(E_s ρ) = ½Tr(ρ) + ½(−1)^s Tr(ρ·⊗_q M_q), M_q = diag(1,−1,1−2b) on Z sites and H·diag(1,−1,1−2b)·H on X sites** | d3: dense Tr(ρ·Π) equality 1e-10; convergence-in-R_n logged |
| `born_sample_round(state, stabs, rng)` [A3] | Per stab sequentially: q = Tr(E_s ρ)/Tr(ρ) via site caps; sample; SELECTIVE update √E_s branch + renormalize ledger; emit detector bits per `seam.py` d3 conventions (det(0,j)=s(0,j); det(r,j)=s(r,j)⊕s(r−1,j)). **obs law PINNED (v2 B3 + v3 support/basis fix, BOTH sides): obs = parity over the LOGICAL SUPPORT ONLY (`sched.logical` — weight-3 at d3, NEVER all data sites) of the per-site biased-b terminal readout, XOR m; each X-flagged logical site (`log_supp_isx`, the sv_sampler "the logical readout keeps its OWN X-rotation" convention) is H-CONJUGATED before the diagonal F₀/F₁ POVM, **with the per-site effects pinned BY FORMULA (v4 — reference alone allowed a coherent double-swap): F₁ = \|1⟩⟨1\| + b·\|2⟩⟨2\|, F₀ = \|0⟩⟨0\| + (1−b)·\|2⟩⟨2\| (F₀+F₁=I; F₀−F₁ = diag(1,−1,1−2b), consistent with F2)**. The engine samples exactly this; the ORACLE composes exactly this (new A4 deliverable: biased-b terminal-readout composition on the dense terminal ρ_{s\|m} — H-rotate the X-flagged logical sites, apply the per-site diagonal F₀/F₁ with b-weighted leaked rows on the logical support, take the parity marginal, XOR m; the stock `logical_sector_traces` 50/50 split is FORBIDDEN as the G1.1 referee — its divergence is documented in p7e's own docstring)** | d3 G1.1: per-sampled-record exact probability via `DMPathEvaluator.reevolve_onto_records` (defined in `qec_twin/audit/floor_backend.py`; p7e re-exports) on RAW s-records — **the det→s inversion s(r,j) = XOR_{r'≤r} det(r',j) is applied before the referee call (pinned); memory (v3 fix): chunk B = 1 ONLY — `_apply_channel_batched` holds ≥3 live (B,3⁹,3⁹) c128 copies, so B=2 peaks ≥34.6 GiB > the 32-GiB card (B=1 ≈ 17–25 GiB, measured-safe)** — plus the A4 biased-b obs composition; z ≤ 4 |
| latent conditioning [A3, G1.6 only] | Per-sample latent draw OUTSIDE the TN; per-round Pauli superop insertion per arm; χ(mix)=χ(arm) check | X2b d3 evidence pattern (`pepo_xi_correlation_length_d3.py` X2b arm) |

**Units table**: b ∈ [0,1] probability; discarded weight + ε levels are SQUARED-σ scale;
dp bar = z·√(p(1−p)/N) at N=1e6, z=4 (per-detector, the record-gate convention); NTU ε is a
squared norm (F6 quadratic form); gap-cut ratio is on UNSQUARED σ_k.

## 4. Registered gate protocols (predictions: ALL PASS; tolerances pinned)

- **G1.0 (pre-gate, A1)** dense d3 codestate == oracle for m=0 AND m=1 (1e-12 max-abs).
- **G1.1** N=1e6 sampled {det,obs} records @ d3, R=3, p1c cell; per-record exact probability
  via `DMPathEvaluator.reevolve_onto_records` (det→s inversion pinned in §3; chunk B = 1
  ONLY per §3 — v4 fix, the stale "≤ 2" here contradicted §3 and OOMs the card) +
  the A4 biased-b obs composition (§3 — the 50/50 split is FORBIDDEN as referee); multinomial
  z ≤ 4 on the top-64 record classes + tail-mass bucket. **χ_b sub-gate (v2, arms pinned v3):
  R_n = the norm-pass boundary dim, R_x = the sample-pass dim, set equal per arm; the z ≤ 4
  record bar is ASSERTED at the R=16 arm ONLY; the R=4 arm is the truncation-path exerciser —
  its deliverable is the live S2 discarded/p-q/KLD ledger + a monotone-degradation sanity read
  (a correct engine with record-faithful χ_b = 16 MAY fail the record bar at R=4; that is not
  a gate miss). An exact-χ_b-only pass does not certify S2.**
- **G1.2** sequential-null detector marginals, R=10 == frozen F8 table: engine worst
  dp/bar ≤ 0.1 (bar convention above), **evaluated at the D_cap=16 arm (v3; the D-dependence
  belongs to G1.4's monotone read).** **Engine marginals MUST come through the production
  site-cap path (A3); the d3 dense reconstruction is the cross-check, never the source (v2).**
- **G1.3** engine gap rank at the FROZEN cut (explicit site list A=[0,1,2] | B=[3..8], §2)
  == 16 at every round 1..10, **evaluated at the D_cap=16 arm via dense d3 reconstruction +
  straight-cut operator SVD + the pinned gap rule (§3), with the headroom criterion: kept
  rank < 0.5× the cut ceiling = min(bond product, physical-leg bound 9^min(|A|,|B|)) — at d3
  min(16⁴, 9³=729) = 729, satisfied (v3: the physical-leg bound binds, not the bond product;
  the rung-2 protocol reuses this min() form) — and the ≥10 gap ratio SHOWN. The
  D=2 arm's rank read is INCONCLUSIVE-BY-DESIGN (cut ceiling 2⁴ = 16 — cap-saturated) and is
  never cited as a G1.3 pass (v2 anti-vacuity fix).**
- **G1.4** Δσ on the **ℓ²-NORMALIZED (shape) spectrum σ/‖σ‖₂ (v2 B2 fix: the un-normalized
  spectrum drifts ~4.2e-3/round from healthy purity decay — arithmetically consistent with the
  frozen purity ledger; normalized drift ~4e-5; the per-round spectra get FROZEN by the
  G1.9-pre dump, v3)**, difference = the ∞-norm of the difference of ℓ²-normalized zero-padded
  spectra (v3 pin), at the frozen cut; the GATE evaluates from R=3 (Δσ(3) compares vs R=2's
  spectrum — R≤2 are excluded as gate READS, not as comparison partners, v3): plateaus ≤ 1e-3;
  discarded-weight plateau; D-sweep {2,4,8,16}: oracle distance monotone non-increasing in D
  (Kilda-pattern destabilization ⇒ STOP finding).
- **G1.5** controls DEMONSTRATED to trip: CorruptStab (wrong support) breaks G1.0/G1.2;
  Shuffle (permuted schedule) breaks G1.2; identical-arms guard in every two-arm compare;
  each C1–C10 broken-variant fires (test-builder owns the sabotage variants, K-catalog
  discipline).
- **G1.6** χ(mix) == χ(arm) per round (latent bond-free), d3 — **χ read = the gap rank of the
  dense-reconstructed ρ at the frozen §2 cut, the SAME instrument as G1.3 (v2: an engine-side
  per-bond-dim read is a different, cap-confounded quantity).**
- **G1.7** in-engine ξ re-measure (the ξ-gate instrument): ξ(Zq) ∈ [0.2,0.8] on fitted rounds;
  ξ(n2) ∈ [0.1,0.5] **on the instrument's fitted rounds R ≥ 2 (v2: the frozen instrument
  itself yields n2 NO_FIT at R=1 — zero signal before noise builds). NO_FIT policy amended
  NOW, not post-hoc: (i) the codestate boundary-stabilizer structural class (prereg P4) and
  (ii) the BELOW-FLOOR-SIGNAL class with the floor REGISTERED (v3): c_max < 1e-4 (the §1
  "all other pairs < 1e-4" figure) ⇒ that round is excluded from the fit, logged; any OTHER
  NO_FIT ⇒ STOP.**
- **G1.8** window-embedding mismatch calibration (ORACLE-side deliverable, no PEPO code):
  embedded 2×3/3×2 windows of d3 vs stand-alone tiles, both via the DENSE oracle, **tile
  DEFINITION PINNED (v2): tile sites = the window's data sites; tile stabilizers = the d3
  stabilizers whose support lies FULLY inside the window (straddling stabs DROPPED — the
  declared restriction rule); schedule = the same within-cycle streams restricted to the
  window sites; open boundary (no environment operator); p1c cell. **Tile INITIAL STATE
  pinned (v3): the G1.0 recipe restricted — H-spread seed over the tile sites, retained-stab
  projectors applied, the logical-sector projector applied ONLY when the full logical support
  lies inside the window (else that sector check is DROPPED and logged — "BOTH m sectors"
  applies only in the former case), remaining unconstrained directions declared unprojected,
  trace-normalized.** The S11 bound = the measured embedded-vs-tile sequential-null marginal
  discrepancy under exactly this declared treatment.**
- **G1.9** positivity: min-eig of the dense-reconstructed truncated ρ (d3); **bar SET BY
  MEASUREMENT, not guessed (v2: the v1 1e-6 was un-derived and ~20–500× below the Weyl scale
  of the frozen discarded weights √(2.5e-7·0.92) ≈ 4.8e-4). PRE-BUILD TASK G1.9-pre
  (orchestrator, before builders start): rerun the frozen single-cut proxy machinery — **the
  ε = 1e-3 arm of `pepo_record_error_vs_eps_d3.py` (named explicitly, v3; the three χ=16 arms
  are bit-identical per the frozen JSON)** — with one `eigvalsh` per round and RECORD
  λ_min(R); **the G1.9 bar = max(10× the worst measured \|λ_min\|, 4.8e-4) — the Weyl-scale
  floor stops the bar collapsing to ~0 if the one-cut Hermitized proxy stays ≈PSD (v3); the
  bar is class (b) (the proxy is the declared OPTIMISTIC machinery), a miss = a finding
  feeding the LPDO decision, never a silent bump. The same run ALSO dumps the per-round
  straight-cut spectra + the ℓ²-normalized Δσ series (freezing the G1.4 reference — v3;
  no committed artifact currently holds the spectra).** The sampler's negativity witness
  fires on a sign-flip sabotage (unchanged). **C3 witness re-pinned (v4 — the v3 cumulative
  Σ over 1e6 shots implied an average per-shot bar of 1e-10, inconsistent with the G1.9
  λ_min scale a correct engine carries): (i) any SINGLE raw Born weight
  q_raw < −(10× the G1.9 bar) ⇒ STOP; (ii) the MEAN over ALL BORN DRAWS of the run (per-draw, not
  per-shot-aggregated — v4.1 pin) of max(0, −q_raw)/Tr(ρ) > the G1.9 bar ⇒ STOP; both logged
  every run.**

## 5. Scope fences (rung-1)

d3 ONLY (no d5 tile — rung 2); the record-law arm (non-selective) and the sampling arm are
BOTH in scope (G1.2 vs G1.1); memory latent only as far as G1.6; NO performance targets
(correctness rung); NO d7 objects; the S10 compiled-circuit scope binds everything; src
commits wait for explicit user confirmation (one reviewed diff), docs/outputs flow normally.

## 6. Red-team + build protocol

Stage-2: ≥2 un-led adversarial passes on THIS contract (contract + referee seams; break it:
un-certifiable claims, unpinned semantics, checks a correct implementation would fail);
loop to zero blockers before any builder starts. Stage-3: A1/A2/A3 disjoint files, test
builder parallel from the contract. Stage-4: multi-lens un-led review (correctness /
numerics-GPU / devious-vacuity) + independent refute-verification of every finding, fixes
BEFORE the first GPU run. Stage-5: committed runners, sha256 + PIPESTATUS discipline.
Stage-6: KILLER variants per load-bearing assert. Stage-7: OUTCOMES backfilled here + into
the prereg; CODE_MAP regenerated; README added.
